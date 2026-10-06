"""Repair owned material connections and provide a continuous cool combat light pool."""
import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
historical_builder(__file__)
r={'passed':False};lev=u.get_editor_subsystem(u.LevelEditorSubsystem)
try:
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    mat=existing(NS+'/Materials/M_TeddyCloth');M.delete_all_material_expressions(mat)
    tex=existing(NS+'/Teddy/T_Teddy_BaseColor')
    sample=M.create_material_expression(mat,u.MaterialExpressionTextureSample);sample.set_editor_property('texture',tex)
    des=M.create_material_expression(mat,u.MaterialExpressionDesaturation);assert M.connect_material_expressions(sample,'RGB',des,'')
    fraction=M.create_material_expression(mat,u.MaterialExpressionConstant);fraction.set_editor_property('r',.5);assert M.connect_material_expressions(fraction,'',des,'Fraction')
    mul=M.create_material_expression(mat,u.MaterialExpressionMultiply);mul.set_editor_property('const_b',1.15);assert M.connect_material_expressions(des,'',mul,'A');assert M.connect_material_property(mul,'',u.MaterialProperty.MP_BASE_COLOR)
    rough=M.create_material_expression(mat,u.MaterialExpressionConstant);rough.set_editor_property('r',.9);assert M.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    M.recompile_material(mat);save(mat)
    boss=existing(NS+'/Blueprints/BP_TeddyBoss')
    r['before']={}
    for name,(_,c) in components(boss).items():
        if isinstance(c,u.SkeletalMeshComponent):
            r['before'][name]={'materials':[str(x) for x in c.get_materials()],'mesh':str(c.skeletal_mesh_asset)};c.set_material(0,mat)
    compile(boss)
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        name=a.get_actor_label()
        light=a.get_component_by_class(u.LightComponent)
        if light:light.set_editor_property('mobility',u.ComponentMobility.MOVABLE)
        if name=='TE_AmbientFill':
            c=a.get_component_by_class(u.DirectionalLightComponent);c.set_intensity(13.);c.set_light_color(u.LinearColor(.20,.32,.38,1));c.set_editor_property('light_source_angle',12.)
        if isinstance(a,u.PointLight) and name in ['TE_Key','TE_Rim','TE_PlayerFill']:
            c=a.point_light_component
            if name=='TE_Key':a.set_actor_location(u.Vector(0,-360,1700),False,False);c.set_editor_property('intensity',40000.)
            if name=='TE_Rim':a.set_actor_location(u.Vector(780,720,1400),False,False);c.set_editor_property('intensity',18000.)
            if name=='TE_PlayerFill':a.set_actor_location(u.Vector(-750,300,1200),False,False);c.set_editor_property('intensity',12000.)
            c.set_editor_property('attenuation_radius',3300.);c.set_editor_property('source_radius',250.)
        if name=='TE_MainTeddy':
            a.get_component_by_class(u.SkeletalMeshComponent).set_material(0,mat);a.set_actor_rotation(u.Rotator(yaw=121),False)
        if name=='TE_Exposure':
            pp=a.settings;pp.set_editor_property('vignette_intensity',.38);a.set_editor_property('settings',pp)
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/scene-lighting-refinement.json').write_text(json.dumps(r,indent=2))
