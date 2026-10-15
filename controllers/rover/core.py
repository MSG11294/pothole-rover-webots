"""Simulator-independent mission logic. Units: metres, radians, seconds."""
from dataclasses import dataclass, field
import math

def wrap(a): return (a+math.pi)%(2*math.pi)-math.pi
def distance(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
@dataclass
class Observation:
    time: float
    pose: tuple
    obstacles: dict
    pothole: tuple | None = None
    sensors_ok: bool = True
    bumper: bool = False
    motor_ok: bool = True
    ack: str | None = None
    battery_override: float | None = None

@dataclass
class Output:
    v: float = 0
    w: float = 0
    dispense: dict | None = None

class Mission:
    def __init__(self,c):
        self.c=c; self.route=c['route']; self.index=0; self.state='ROUTE'
        self.battery=100.; self.last_time=None; self.records=[]; self.repairs=[]
        self.target=None; self.repair_start=0; self.sent=False; self.reason=''
        self.returning=False; self.fault=None; self.blocked_since=None
    def drive(self,pose,target,speed=None):
        d=distance(pose,target); a=wrap(math.atan2(target[1]-pose[1],target[0]-pose[0])-pose[2])
        return Output(min(self.c['speed'] if speed is None else speed,d*.8)*max(0,math.cos(a)) if abs(a)<.55 else 0,max(-1,min(1,2*a)))
    def tick(self,o):
        dt=0 if self.last_time is None else max(0,o.time-self.last_time); self.last_time=o.time
        self.battery=max(0,self.battery-dt*100/self.c['battery_seconds'])
        if o.battery_override is not None: self.battery=o.battery_override
        if not o.sensors_ok: self.fault='sensor invalid or stale'
        if not o.motor_ok: self.fault='wheel encoder mismatch'
        if o.bumper: self.fault='bumper contact'
        if self.battery<=1: self.fault='battery depleted'
        if self.fault:
            self.state='FAULT'; self.reason=self.fault; return Output()
        if o.pothole and all(distance(o.pothole,r['position'])>.18 for r in self.records):
            self.records.append({'id':f'P{len(self.records)+1}','position':list(o.pothole),'time':o.time,'status':'detected'})
        # Holes identified from depth, not scene coordinates. Selection is discovery order.
        if not self.returning and self.battery<self.c['return_battery'] and self.state not in ('DISPENSE','WAIT_ACK','DOCKED'):
            self.returning=True; self.state='RETURN'; self.target=None
        if self.state=='DOCKED':
            self.battery=min(100,self.battery+dt*3); return Output()
        if not self.returning and self.state=='ROUTE':
            candidates=[r for r in self.records if r['status']=='detected' and r['id'] in self.c['selected_potholes']]
            if candidates:
                self.target=candidates[0]; self.state='ALIGN_REPAIR'
        if self.state=='ALIGN_REPAIR':
            if distance(o.pose,self.target['position'])<.025:
                self.state='DISPENSE'; self.repair_start=o.time; return Output()
            command=self.drive(o.pose,self.target['position'],.045)
        elif self.state=='DISPENSE':
            if o.time-self.repair_start>=self.c['repair_seconds']:
                self.state='WAIT_ACK'; self.repair_start=o.time
                return Output(dispense={'id':self.target['id'],'position':self.target['position']})
            command=Output()
        elif self.state=='WAIT_ACK':
            if o.ack=='ok':
                self.target['status']='repaired'; self.repairs.append(dict(self.target,repair_time=o.time)); self.state='ROUTE'; self.target=None
            elif o.ack=='rejected' or o.time-self.repair_start>2:
                self.fault='dispense acknowledgement failed'
            return Output()
        elif self.state in ('RETURN','DOCK_ALIGN'):
            dock=self.c['dock']
            if distance(o.pose,dock)<.04 or (self.state=='DOCK_ALIGN' and distance(o.pose,dock)<.10):
                self.state='DOCK_ALIGN'; e=wrap(dock[2]-o.pose[2])
                if abs(e)<.06: self.state='DOCKED'; return Output()
                command=Output(0,max(-.4,min(.4,2*e)))
            else: command=self.drive(o.pose,dock,.08)
        else:
            if self.index>=len(self.route): self.returning=True; self.state='RETURN'; return Output()
            if distance(o.pose,self.route[self.index])<.045: self.index+=1; return Output()
            command=self.drive(o.pose,self.route[self.index])
        # Stopping envelope includes body extent, reaction interval and braking.
        needed=.23+abs(command.v)*.256+command.v**2/(2*.4)+.08
        relevant=list(o.obstacles.values()) if abs(command.w)>.12 else [o.obstacles.get('front',math.inf)]
        if min(relevant,default=math.inf)<needed:
            self.reason='obstacle: protective stop'
            if self.blocked_since is None: self.blocked_since=o.time
            if o.time-self.blocked_since>30: self.fault='route blocked timeout'
            return Output()
        self.blocked_since=None; self.reason=''; return command
    def status(self,pose):
        return {'state':self.state,'reason':self.fault or self.reason,'battery':round(self.battery,1),'pose':pose,'route_index':self.index,'potholes':self.records,'repairs':self.repairs}
