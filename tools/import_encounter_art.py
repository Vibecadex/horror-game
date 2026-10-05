import sys,json,traceback,os
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'assets':[]}
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    sk=None
    for clip in ['Idle','Walk','Crawl','Attack','Hit','Defeat']:
        dest=NS+'/Teddy/'+clip
        if A.does_directory_exist(dest) and not os.environ.get('TEDDY_REIMPORT_OWNED'):
            for p in A.list_assets(dest):
                o=A.load_asset(p);assert A.get_metadata_tag(o,TAG)==OWNER
                if isinstance(o,u.Skeleton):sk=o
                r['assets'].append({'path':p,'type':o.get_class().get_name()})
            continue
        opt=u.FbxImportUI();opt.set_editor_property('automated_import_should_detect_type',False)
        if clip!='Idle' and sk is None:sk=A.load_asset(NS+'/Teddy/Idle/SK_Teddy_Skeleton')
        opt.set_editor_property('import_as_skeletal',True);opt.set_editor_property('import_mesh',clip=='Idle')
        opt.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_SKELETAL_MESH if clip=='Idle' else u.FBXImportType.FBXIT_ANIMATION)
        opt.set_editor_property('import_animations',True);opt.set_editor_property('import_materials',False);opt.set_editor_property('import_textures',False)
        opt.set_editor_property('create_physics_asset',False)
        if sk:opt.set_editor_property('skeleton',sk)
        opt.set_editor_property('override_animation_name','A_Teddy_'+clip)
        for data in [opt.skeletal_mesh_import_data,opt.anim_sequence_import_data]:
            data.set_editor_property('convert_scene',True);data.set_editor_property('convert_scene_unit',True);data.set_editor_property('force_front_x_axis',True)
        task=u.AssetImportTask();task.filename=str(ROOT/'Assets/Adapted/Teddy'/('Teddy_'+clip+'.fbx'));task.destination_path=dest;task.destination_name='SK_Teddy' if clip=='Idle' else 'A_Teddy_'+clip;task.automated=True;task.save=True;task.options=opt
        if os.environ.get('TEDDY_REIMPORT_OWNED'):
            for p in A.list_assets(dest):assert A.get_metadata_tag(A.load_asset(p),TAG)==OWNER
            task.replace_existing=True;task.replace_existing_settings=True
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
        for p in A.list_assets(dest):
            o=own(A.load_asset(p));save(o)
            if isinstance(o,u.Skeleton):sk=o
            r['assets'].append({'path':p,'type':o.get_class().get_name()})
    task=u.AssetImportTask();task.filename=str(ROOT/'Assets/Adapted/Teddy/Teddy_BaseColor.png');task.destination_path=NS+'/Teddy';task.destination_name='T_Teddy_BaseColor';task.automated=True;task.save=True
    if not A.does_asset_exist(NS+'/Teddy/T_Teddy_BaseColor'):
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=own(A.load_asset(task.imported_object_paths[0]));save(tex)
    else:tex=existing(NS+'/Teddy/T_Teddy_BaseColor')
    mat=asset('Materials/M_TeddyCloth',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(mat)
    sample=M.create_material_expression(mat,u.MaterialExpressionTextureSample);sample.texture=tex
    # Keep recognisable source texture but pale and desaturated in cool lighting.
    des=M.create_material_expression(mat,u.MaterialExpressionDesaturation);assert M.connect_material_expressions(sample,'RGB',des,'')
    fraction=M.create_material_expression(mat,u.MaterialExpressionConstant);fraction.r=.65;M.connect_material_expressions(fraction,'',des,'Fraction')
    mul=M.create_material_expression(mat,u.MaterialExpressionMultiply);mul.set_editor_property('const_b',1.15);M.connect_material_expressions(des,'',mul,'A');M.connect_material_property(mul,'',u.MaterialProperty.MP_BASE_COLOR)
    rough=M.create_material_expression(mat,u.MaterialExpressionConstant);rough.r=.87;M.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    mat.set_editor_property('two_sided',True);M.recompile_material(mat);save(mat)
    skmesh=next(A.load_asset(x['path']) for x in r['assets'] if x['type']=='SkeletalMesh')
    materials=skmesh.get_editor_property('materials')
    for entry in materials:entry.set_editor_property('material_interface',mat)
    skmesh.set_editor_property('materials',materials);save(skmesh)
    r['bounds']=str(skmesh.get_bounds());r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/art-import.json').write_text(json.dumps(r,indent=2))
