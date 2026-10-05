"""Recompile only the three owned combined floor materials, preserving the scene."""
import json,sys,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import apply_parity_combined as combined
R={'passed':False,'scene_writes':False,'settings':combined.P.get('foreground_wear')}
try:
    R['materials']=[combined.floor(name,value).get_path_name() for name,value in [('M_Parity_CombinedFloor',1.),('M_Parity_CombinedFloorLight',1.18),('M_Parity_CombinedFloorDark',.82)]]
    R['passed']=True
except Exception:R['error']=traceback.format_exc();raise
finally:(combined.OUT/'floor-wear-12-authoring.json').write_text(json.dumps(R,indent=2))
