import sys,unittest,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'controllers/rover'))
from core import Mission,Observation,distance
C=json.loads((ROOT/'config.json').read_text())
def obs(t=1,pose=(0,0,0),**kw): return Observation(t,pose,kw.pop('obstacles',{'front':math.inf,'left':math.inf,'rear':math.inf,'right':math.inf}),**kw)
class Tests(unittest.TestCase):
 def test_move(self):
  m=Mission(C); m.tick(obs()); self.assertGreater(m.tick(obs(2)).v,0)
 def test_obstacle(self):
  m=Mission(C); m.tick(obs()); self.assertEqual(m.tick(obs(2,obstacles={'front':.2})).v,0)
 def test_sensor_fault_latches(self):
  m=Mission(C); m.tick(obs(sensors_ok=False)); self.assertEqual(m.tick(obs(2)).v,0); self.assertEqual(m.state,'FAULT')
 def test_motor_fault(self):
  m=Mission(C); m.tick(obs(motor_ok=False)); self.assertEqual(m.state,'FAULT')
 def test_low_battery_return(self):
  m=Mission(C); m.tick(obs(pose=(2,0,0),battery_override=20)); self.assertEqual(m.state,'RETURN')
 def test_low_battery_preserves_dock_alignment(self):
  m=Mission(C)
  m.tick(obs(pose=(.03,0,1),battery_override=20))
  self.assertEqual(m.state,'DOCK_ALIGN')
  m.tick(obs(2,pose=(.05,0,.5),battery_override=20))
  self.assertEqual(m.state,'DOCK_ALIGN')
  m.tick(obs(3,pose=(.05,0,.01),battery_override=20))
  self.assertEqual(m.state,'DOCKED')
 def test_bumper(self):
  m=Mission(C); m.tick(obs(bumper=True)); self.assertEqual(m.state,'FAULT')
 def test_repair_ack(self):
  m=Mission(C); m.tick(obs(pose=(2,0,0),pothole=(2,0))); self.assertEqual(m.state,'DISPENSE')
  o=m.tick(obs(5,pose=(2,0,0))); self.assertIsNotNone(o.dispense)
  self.assertEqual(len(m.repairs),0); m.tick(obs(5.1,pose=(2,0,0),ack='ok')); self.assertEqual(len(m.repairs),1)
 def test_repair_timeout(self):
  m=Mission(C); m.tick(obs(pose=(2,0,0),pothole=(2,0))); m.tick(obs(5,pose=(2,0,0))); m.tick(obs(8)); m.tick(obs(9)); self.assertEqual(m.state,'FAULT')
 def test_duplicates(self):
  m=Mission(C); m.tick(obs(pothole=(2,0))); m.tick(obs(2,pothole=(2.01,0))); self.assertEqual(len(m.records),1)
 def test_docking_heading(self):
  m=Mission(C); m.returning=True; m.state='RETURN'; m.tick(obs(pose=(0,0,.5))); self.assertEqual(m.state,'DOCK_ALIGN'); m.tick(obs(2)); self.assertEqual(m.state,'DOCKED')
 def test_kinematic_route_and_repairs(self):
  m=Mission(C); x=y=a=0.; filled=set()
  for k in range(14000):
   t=k*.032; hole=None
   for h in [(2,0),(3.5,1)]:
    if h not in filled and distance((x+.12*math.cos(a),y+.12*math.sin(a)),h)<.09: hole=h
   o=obs(t,(x,y,a),pothole=hole,ack='ok' if filled and m.state=='WAIT_ACK' else None)
   out=m.tick(o)
   if out.dispense: filled.add(tuple(out.dispense['position']))
   x+=out.v*math.cos(a)*.032; y+=out.v*math.sin(a)*.032; a+=out.w*.032
   if m.state=='DOCKED': break
  self.assertEqual(m.state,'DOCKED'); self.assertEqual(len(m.repairs),2)
if __name__=='__main__': unittest.main(verbosity=2)
