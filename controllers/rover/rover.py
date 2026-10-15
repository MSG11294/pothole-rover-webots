from pathlib import Path
import json,traceback
from controller import Robot
from hardware import WebotsHardware
from core import Mission
from dashboard import Dashboard
ROOT=Path(__file__).resolve().parents[2]
def main():
    c=json.loads((ROOT/'config.json').read_text()); r=Robot(); hw=WebotsHardware(r,c); mission=Mission(c)
    dash=Dashboard(ROOT/'logs'); last_save=-2
    keyboard=r.getKeyboard(); keyboard.enable(hw.dt)
    print('Dashboard http://127.0.0.1:8765 · scenario',c['scenario'])
    try:
        while r.step(hw.dt)!=-1:
            if r.getTime()<.3: continue # first sensor frames and settling
            obs=hw.read()
            key=keyboard.getKey()
            if key in (32,ord('E')): mission.fault='operator emergency stop'
            if key==ord('R') and not mission.fault and mission.state not in ('DISPENSE','WAIT_ACK'):
                mission.returning=True; mission.state='RETURN'; mission.target=None
            out=mission.tick(obs); hw.apply(out)
            if r.getTime()-last_save>=1:
                last_save=r.getTime(); status=mission.status(obs.pose); status['sim_time']=round(obs.time,2)
                status['clearance_m']={k:round(v,3) if v!=float('inf') else None for k,v in obs.obstacles.items()}
                status["camera_detections"]=hw.detections
                dash.update(status)
                with (ROOT/"logs/telemetry.jsonl").open("a") as log: log.write(json.dumps(status)+"\n")
                for name,cam in hw.cams.items(): cam.saveImage(str(ROOT/'logs'/f'{name}.jpg'),70)
    except Exception:
        hw.stop(); traceback.print_exc()
        # Keep motor stop in effect rather than silently continuing a broken mission.
        while r.step(hw.dt)!=-1: hw.stop()
    finally: hw.stop()
if __name__=='__main__': main()
