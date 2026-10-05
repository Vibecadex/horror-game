"""Bounded cloth colour correction; preserve geometry, camera and material slots."""
import sys,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import apply_parity_combined as combined
R={'passed':False,'scene_writes':False,'cloth_tint':combined.P['cloth_tint'],'base_scale':combined.P['cloth_base_scale']}
try:
    R['materials']=[combined.cloth(name,value).get_path_name() for name,value in [('M_Parity_CombinedCloth',1.),('M_Parity_CombinedStitchling',.70)]]
    R['passed']=True
except Exception:R['error']=traceback.format_exc();raise
finally:(combined.OUT/'cloth-tint-14-authoring.json').write_text(json.dumps(R,indent=2))
