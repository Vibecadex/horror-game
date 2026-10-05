"""Three held views of saved parity art; staging is restricted to transforms/camera."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_parity_look as comparison
g=comparison.gallery
g.VIEWS=[
    {'name':'01-matched-gameplay','kind':'gameplay','caption':'Saved gameplay camera, spawns, exposure, lighting and surfaces; movement held and player yaw staged toward boss.'},
    {'name':'02-gameplay-wide','kind':'gameplay-staged','caption':'Saved adaptive gameplay camera and art at opposite-corner separation; actors held for room coverage.'},
    {'name':'03-room-overview','kind':'architecture','caption':'Architectural cutaway with temporary camera; saved room lighting/surfaces.','location':(-4300,-2300,4100),'target':(0,0,180),'fov':53}
]
