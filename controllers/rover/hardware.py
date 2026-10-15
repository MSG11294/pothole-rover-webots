"""Webots adapter only. Real board transports are intentionally not implemented."""
import math,random
from core import Observation
class WebotsHardware:
    def __init__(self,robot,c):
        self.r=robot; self.c=c; self.dt=int(robot.getBasicTimeStep()); self.rng=random.Random(7)
        self.motors=[robot.getDevice(n) for n in ('fl','rl','fr','rr')]
        self.enc=[robot.getDevice(n+'_encoder') for n in ('fl','rl','fr','rr')]
        for m,e in zip(self.motors,self.enc): m.setPosition(float('inf')); m.setVelocity(0); e.enable(self.dt)
        self.gps=robot.getDevice('gps'); self.imu=robot.getDevice('imu'); self.bump=robot.getDevice('bumper')
        for s in (self.gps,self.imu,self.bump): s.enable(self.dt)
        self.cams={n:robot.getDevice(n) for n in ('front','rear','left','right')}
        for cam in self.cams.values(): cam.enable(c['camera_period_ms']); cam.recognitionEnable(c['camera_period_ms'])
        self.safety={n:robot.getDevice('safety_'+n) for n in self.cams}
        for sensor in self.safety.values(): sensor.enable(c['camera_period_ms'])
        self.down=robot.getDevice('down_camera'); self.down.enable(c['camera_period_ms'])
        self.depth=robot.getDevice('down_depth'); self.depth.enable(c['depth_period_ms'])
        self.tx=robot.getDevice('repair_tx'); self.rx=robot.getDevice('repair_ack'); self.rx.enable(self.dt)
        self.hole_start=None; self.hole_end=None; self.last_depth_tick=-1
        self.previous=None; self.last_t=0; self.stall=[0]*4; self.command=[0]*4
    def read(self):
        t=self.r.getTime(); xyz=self.gps.getValues(); roll,pitch,yaw=self.imu.getRollPitchYaw(); pose=(xyz[0],xyz[1],yaw)
        self.detections=[]; distances={}; good=all(math.isfinite(x) for x in (*pose,))
        for name,cam in self.cams.items():
            frame=cam.getImage(); good=good and frame is not None
            ranges=[]
            for obj in cam.getRecognitionObjects():
                if obj.getModel() in ('dock','barrier'): continue
                q=obj.getPosition(); size=obj.getSize()
                self.detections.append({"camera":name,"model":obj.getModel(),"position":list(q),"size":list(size)})
                ranges.append(max(0,math.sqrt(sum(v*v for v in q))-min(size)/2))
            safety_frame=self.safety[name].getRangeImage()
            good=good and bool(safety_frame)
            if safety_frame: ranges.extend(v for v in safety_frame if math.isfinite(v))
            distances[name]=min(ranges,default=math.inf)
        depth=self.depth.getRangeImage(); hole=None
        if depth:
            # Median center patch rejects isolated noisy pixels. Vertical optical ray.
            w=self.depth.getWidth(); h=self.depth.getHeight()
            samples=[depth[y*w+x] for y in range(h//2-2,h//2+2) for x in range(w//2-2,w//2+2)]
            valid=sorted(v for v in samples if math.isfinite(v))
            good=good and len(valid)>=12
            depth_tick=int(t/(self.c['depth_period_ms']/1000))
            if depth_tick!=self.last_depth_tick:
                self.last_depth_tick=depth_tick
                projection=math.cos(roll)*math.cos(pitch)
                flat_depth=(xyz[2]-.12*math.sin(pitch)-.047*projection)/max(.5,projection)
                stable=abs(roll)<.15 and abs(pitch)<.15 and abs(self.command[0]-self.command[2])*.065/.29<.25
                if not stable:
                    self.hole_start=None; self.hole_end=None
                if stable and valid and .025<valid[len(valid)//2]-flat_depth<.08:
                    point=(pose[0]+.12*math.cos(yaw),pose[1]+.12*math.sin(yaw))
                    if self.hole_start is None: self.hole_start=point
                    self.hole_end=point
                elif stable and valid and self.hole_start is not None:
                    # Record midpoint of observed leading/trailing depth edges.
                    span=math.dist(self.hole_start,self.hole_end)
                    if .10<span<.40: hole=tuple((a+b)/2 for a,b in zip(self.hole_start,self.hole_end))
                    self.hole_start=None; self.hole_end=None
        else: good=False
        values=[e.getValue() for e in self.enc]; motor_ok=True
        if self.previous is not None:
            dt=t-self.last_t
            for i,(v,old,cmd) in enumerate(zip(values,self.previous,self.command)):
                self.stall[i]=self.stall[i]+dt if abs(cmd)>.7 and abs(v-old)/max(dt,.001)<.15 else 0
            motor_ok=max(self.stall)<1.2
        self.previous=values; self.last_t=t
        scenario=self.c['scenario']; active=t>self.c['fault_at']
        if scenario=='camera_dropout' and active: good=False
        ack=None
        while self.rx.getQueueLength(): ack=self.rx.getString(); self.rx.nextPacket()
        return Observation(t,pose,distances,hole,good,bool(self.bump.getValue()),motor_ok,ack,20 if scenario=='low_battery' and active else None)
    def apply(self,out):
        left=(out.v-out.w*.29/2)/.065; right=(out.v+out.w*.29/2)/.065
        self.command=[left,left,right,right]
        for i,(m,v) in enumerate(zip(self.motors,self.command)):
            failed=self.c['scenario']=='motor_failure' and self.r.getTime()>self.c['fault_at'] and i==0
            m.setVelocity(0 if failed else max(-8,min(8,v)))
        if out.dispense:
            import json
            self.tx.send(json.dumps(out.dispense).encode())
    def stop(self):
        for m in self.motors: m.setVelocity(0)
