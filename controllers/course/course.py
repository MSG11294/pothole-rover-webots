"""Environment supervisor: animated actors and acknowledged fill placement.
Ground truth stays here; rover cannot query world nodes.
"""
from controller import Supervisor
import math,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TEST_SECONDS=float(os.environ.get('ROVER_TEST_SECONDS','0'))
recorded=False
recording=False
r=Supervisor(); dt=int(r.getBasicTimeStep()); rx=r.getDevice('repair_rx'); rx.enable(dt); tx=r.getDevice('ack_tx')
actors=[r.getFromDef('PEDESTRIAN'),r.getFromDef('VEHICLE')]; holes=[r.getFromDef('P1'),r.getFromDef('P2')]; filled=set()
robot=None
for i in range(r.getRoot().getField('children').getCount()):
    node=r.getRoot().getField('children').getMFNode(i)
    if node.getTypeName()=='Rover': robot=node
# getFromDef is more robust for PROTO instances; world generator adds DEF ROVER.
robot=r.getFromDef('ROVER') or robot
while r.step(dt)!=-1:
    t=r.getTime()
    if TEST_SECONDS and not recording and not recorded:
        recording=r.animationStartRecording(str(ROOT/'logs/replay.html'))
    status_file=ROOT/'logs/status.json'
    if TEST_SECONDS and status_file.exists() and t>6:
        try: data=json.loads(status_file.read_text())
        except (OSError,json.JSONDecodeError): data={}
        if data.get('state') in ('FAULT','DOCKED') or t>TEST_SECONDS:
            (ROOT/'logs/result.json').write_text(json.dumps(data,indent=2))
            r.exportImage(str(ROOT/'logs/scene.jpg'),85)
            if recording: r.animationStopRecording(); recorded=True
            r.simulationQuit(0); break
    actors[0].getField('translation').setSFVec3f([1.2,.8+1.05*math.sin(t*.22),.8])
    actors[1].getField('translation').setSFVec3f([2.8+1.2*math.sin(t*.16),1.65,.18])
    while rx.getQueueLength():
        try:
            req=json.loads(rx.getString()); xy=req['position']; pose=robot.getPosition()
            hole=min(holes,key=lambda h: math.hypot(h.getPosition()[0]-xy[0],h.getPosition()[1]-xy[1]))
            hp=hole.getPosition(); key=hole.getDef()
            stopped=sum(v*v for v in robot.getVelocity()[:3])<.0004
            if math.hypot(pose[0]-hp[0],pose[1]-hp[1])<.06 and math.hypot(xy[0]-hp[0],xy[1]-hp[1])<.08 and stopped and key not in filled:
                r.getRoot().getField('children').importMFNodeFromString(-1,f'Solid {{ translation {hp[0]} {hp[1]} -.02 children [ Shape {{ appearance PBRAppearance {{ baseColor .55 .38 .18 roughness 1 }} geometry Box {{ size .245 .245 .04 }} }} ] boundingObject Box {{ size .245 .245 .04 }} }}')
                filled.add(key); tx.send(b'ok')
            else: tx.send(b'rejected')
        except Exception as e:
            print('Repair rejected:',e); tx.send(b'rejected')
        finally: rx.nextPacket()
