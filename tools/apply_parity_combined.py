"""Combine reviewed art inputs after the shared Unreal writer has handed over.

Uses owned sibling materials so both prior material graphs remain available.
The input colour texture, ComfyUI maps and original rig/animation are retained.
"""
import json,sys,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import apply_parity_look as look
from apply_parity_look import node,link,bind,scalar,rgb,mul,blend,channel,texture_sample
from encounter_authoring import NS,asset,existing,save,M,components,compile
look.P=json.loads((ROOT/'study/parity-combined-settings.json').read_text());P=look.P
OUT=look.OUT
R=look.R;R['settings']=P;R['prior_material_graphs_preserved']=True
def surface(name):return existing(NS+'/Parity/Surfaces/'+name)
def newmat(name):
    m=asset('Parity/Materials/'+name,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
    R['new_materials'].append(m.get_path_name());return m
def data_sample(m,name,kind,uv):
    n=node(m,u.MaterialExpressionTextureSample,texture=surface(name),sampler_type=kind);link(uv,n,'UVs');return n
def floor(name='M_Parity_CombinedFloor',value_scale=1.):
    m=newmat(name)
    world=node(m,u.MaterialExpressionWorldPosition)
    xy=node(m,u.MaterialExpressionComponentMask,r=True,g=True,b=False,a=False);link(world,xy,'Input')
    uv=mul(m,xy,1/P['floor_tile_cm'])
    soft=look.sample(m,'T_AI_Floor_Color',u.MaterialSamplerType.SAMPLERTYPE_COLOR,uv)
    detailed=texture_sample(m,look.parity_texture(),uv)
    color=blend(m,soft,detailed,scalar(m,.35))
    desat=node(m,u.MaterialExpressionDesaturation);link(color,desat,'');link(scalar(m,.70),desat,'Fraction')
    damp_uv=mul(m,xy,1/1350.)
    dry=data_sample(m,'T_Comfy_Floor_Dry',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE,damp_uv)
    wear=blend(m,scalar(m,.50),scalar(m,1.0),dry)
    if 'foreground_wear' in P:
        # A fixed damp zone near the foreground drains, shared by slab/base
        # world coordinates. It never follows the camera or player.
        spec=P['foreground_wear'];x=channel(m,world,'R')
        gradient=mul(m,look.add(m,mul(m,x,-1),scalar(m,-spec['start_cm'])),1/spec['fade_cm'])
        weight=node(m,u.MaterialExpressionClamp,min_default=0.,max_default=1.);link(gradient,weight,'')
        damp=blend(m,scalar(m,spec['damp_min']),scalar(m,spec['dry_max']),dry)
        wear=blend(m,wear,damp,weight)
    base=mul(m,mul(m,desat,P['floor_scale']*value_scale),wear)
    bind(base,u.MaterialProperty.MP_BASE_COLOR)
    new_normal=look.floor_bump(m,look.parity_texture(),uv)
    old_normal=look.sample(m,'T_AI_Floor_Normal',u.MaterialSamplerType.SAMPLERTYPE_NORMAL,uv)
    bind(blend(m,old_normal,new_normal,scalar(m,.55)),u.MaterialProperty.MP_NORMAL)
    bind(blend(m,scalar(m,.46),scalar(m,.92),dry),u.MaterialProperty.MP_ROUGHNESS)
    bind(scalar(m,.22),u.MaterialProperty.MP_SPECULAR);M.recompile_material(m);save(m);return m
def cloth(name='M_Parity_CombinedCloth',darken=1.):
    m=newmat(name);m.set_editor_property('used_with_skeletal_mesh',True)
    m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_CLOTH);m.set_editor_property('use_material_attributes',True)
    attr=node(m,u.MaterialExpressionMakeMaterialAttributes)
    original=node(m,u.MaterialExpressionTextureSample,texture=existing(NS+'/Teddy/T_Teddy_BaseColor'))
    d=node(m,u.MaterialExpressionDesaturation);link(original,d,'','RGB');link(scalar(m,P['cloth_desaturation']),d,'Fraction')
    uv=node(m,u.MaterialExpressionTextureCoordinate,u_tiling=P['cloth_uv'][0],v_tiling=P['cloth_uv'][1])
    weave=data_sample(m,'T_Comfy_Cloth_Weave',u.MaterialSamplerType.SAMPLERTYPE_COLOR,uv)
    weave_value=channel(m,weave,'G')
    base=mul(m,mul(m,mul(m,d,P['cloth_base_scale']*darken),rgb(m,P.get('cloth_tint',(1.,.94,.80)))),blend(m,scalar(m,.78),scalar(m,1.32),weave_value))
    link(base,attr,'BaseColor')
    normal=data_sample(m,'T_Comfy_Cloth_Normal',u.MaterialSamplerType.SAMPLERTYPE_NORMAL,uv)
    normal=blend(m,rgb(m,(0,0,1)),normal,scalar(m,P['cloth_normal']))
    normalized=node(m,u.MaterialExpressionNormalize);link(normal,normalized,'VectorInput');link(normalized,attr,'Normal')
    rough=data_sample(m,'T_Comfy_Cloth_Roughness',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE,uv)
    link(blend(m,scalar(m,.84),scalar(m,.97),rough),attr,'Roughness')
    link(scalar(m,.10),attr,'Specular');link(rgb(m,(.09,.07,.04)),attr,'SubsurfaceColor');link(scalar(m,P['cloth_amount']),attr,'ClearCoat')
    bind(attr,u.MaterialProperty.MP_MATERIAL_ATTRIBUTES);M.recompile_material(m);save(m);return m
def main():
    look.floor_mat=floor;look.cloth_mat=cloth;look.main()
    # Keep imported slab tops continuous with the new base floor; preserve side slots.
    kit=json.loads((ROOT/'Assets/Adapted/Parity/Floor/manifest.json').read_text())
    fm=existing(NS+'/Parity/Materials/M_Parity_CombinedFloor')
    for entry in kit['assets']:
        model=existing(NS+'/Parity/Floor/'+entry['name'])
        for i,slot in enumerate(model.get_editor_property('static_materials')):
            if str(slot.get_editor_property('material_slot_name'))=='Concrete':model.set_material(i,fm)
        save(model)
    dark=cloth('M_Parity_CombinedStitchling',.70)
    bp=existing(NS+'/Blueprints/BP_Stitchling')
    for _,(_,c) in components(bp).items():
        if isinstance(c,u.SkeletalMeshComponent):c.set_editor_property('override_materials',[dark,*list(c.get_editor_property('override_materials'))[1:]])
    compile(bp)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem);lev=u.get_editor_subsystem(u.LevelEditorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label()=='TE_Parity_Floor_000':
            a.set_actor_location(u.Vector(-480,-100,-5),False,False)
        if a.get_actor_label().startswith('TE_Stitchling'):
            for c in a.get_components_by_class(u.SkeletalMeshComponent):c.set_editor_property('override_materials',[dark,*list(c.get_editor_property('override_materials'))[1:]])
    # Lens-only adjustment: no added light or spill on the arena.
    warning=existing(NS+'/Parity/Materials/M_Parity_Warning')
    M.delete_all_material_expressions(warning);bind(rgb(warning,(.28,.004,.002)),u.MaterialProperty.MP_BASE_COLOR)
    bind(rgb(warning,(8,.09,.04)),u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(warning);save(warning)
    assert lev.save_current_level();assert lev.load_level('/Game/Maps/TeddyEncounter')
    R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['passed']=False;R['error']=traceback.format_exc();raise
    finally:(OUT/(P['revision']+'-authoring.json')).write_text(json.dumps(R,indent=2))
