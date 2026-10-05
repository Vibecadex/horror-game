"""Darken only the owned V2 thread material after the independent crown review."""
import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import existing,save,M
from apply_parity_look import rgb,scalar,bind,OUT
R={'passed':False,'base_color':[.06,.055,.045],'scene_writes':False}
try:
    material=existing('/Game/TeddyEncounter/Parity/Materials/M_Parity_ThreadV2');assert material
    M.delete_all_material_expressions(material)
    bind(rgb(material,R['base_color']),u.MaterialProperty.MP_BASE_COLOR)
    bind(scalar(material,.9),u.MaterialProperty.MP_ROUGHNESS)
    bind(scalar(material,.1),u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(material);save(material);R['material']=material.get_path_name();R['passed']=True
except Exception:R['error']=traceback.format_exc();raise
finally:(OUT/'thread-15-authoring.json').write_text(json.dumps(R,indent=2))
