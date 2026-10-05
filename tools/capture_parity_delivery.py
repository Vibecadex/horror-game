"""Saved close/wide gameplay and four architectural views for delivery review."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_parity_room as comparison
g=comparison.g
g.VIEWS.extend([
    {'name':'04-rear-bulkhead','kind':'architecture','caption':'Architectural rear-bulkhead view; saved art with temporary camera.','location':(650,-300,600),'target':(1650,180,320),'fov':62},
    {'name':'05-side-services','kind':'architecture','caption':'Architectural pipework and wall dressing; saved art with temporary camera.','location':(-950,100,600),'target':(450,-1680,310),'fov':60},
    {'name':'06-electrical-bay','kind':'architecture','caption':'Architectural electrical bay; saved art with temporary camera.','location':(-1100,550,430),'target':(-420,1640,250),'fov':64}
])
