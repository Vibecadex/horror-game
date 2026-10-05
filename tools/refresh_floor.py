import sys,json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
for name in ['T_Concrete_Color','T_Concrete_Normal','T_Concrete_Roughness']:
    obj=existing(NS+'/Arena/'+name);task=u.AssetImportTask();task.filename=str(ROOT/'Assets/Adapted/Arena'/(name+'.png'));task.destination_path=NS+'/Arena';task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
    obj=own(A.load_asset(task.imported_object_paths[0]))
    if name.endswith('Normal'):obj.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);obj.set_editor_property('srgb',False)
    if name.endswith('Roughness'):obj.set_editor_property('srgb',False)
    save(obj)
mat=existing(NS+'/Materials/M_WornConcrete');count=0
for node in u.ObjectIterator(u.MaterialExpressionTextureCoordinate):
    if node.get_outer()==mat:node.set_editor_property('u_tiling',7.);node.set_editor_property('v_tiling',7.);count+=1
assert count==1;M.recompile_material(mat);save(mat)
(ROOT/'evidence/implementation/floor-refinement.json').write_text(json.dumps({'passed':True,'tiling':7,'changes':'Smaller concrete slabs, continuous hairline fractures instead of isolated dots, quieter slab seam contrast.'},indent=2))
