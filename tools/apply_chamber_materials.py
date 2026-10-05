"""World-sized worn wall surfaces, using preserved local source maps."""
import traceback,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from apply_parity_look import noise
R={'passed':False,'preserved_old_materials':True,'character_and_floor_changes':False,'materials':[],'actors':[],'function_inputs':{}}
def texture(family,kind):
    patina=P.get('wall_patina') if kind=='Color' and family in ['Concrete','Steel'] else None
    name='T_Chamber_WallPatinaColor' if patina else 'T_Chamber_'+family+'_'+kind
    path=DEST+'/Textures/'+name;obj=existing(path)
    if patina:
        source=ROOT/patina['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==patina['sha256'];R['wall_patina']=patina
    if not obj:
        if not patina:source=ROOT/'Assets/Adapted/RoomShell/Surfaces'/('T_Shell_'+family+'_'+kind+'.png')
        assert source.is_file()
        task=u.AssetImportTask();task.filename=str(source);task.destination_path=DEST+'/Textures';task.destination_name=name;task.automated=True;task.save=True
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
        obj=own(A.load_asset(task.imported_object_paths[0]))
    obj.set_editor_property('srgb',kind=='Color')
    obj.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if kind=='Normal' else u.TextureCompressionSettings.TC_GRAYSCALE if kind=='Roughness' else u.TextureCompressionSettings.TC_DEFAULT)
    save(obj);return obj
def aligned(m,tex,size,normal=False):
    function=u.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/'+('WorldAlignedNormal' if normal else 'WorldAlignedTexture'));assert function
    call=node(m,u.MaterialExpressionMaterialFunctionCall);assert call.set_material_function(function)
    inputs=list(M.get_material_expression_input_names(call));R['function_inputs'][function.get_name()]=inputs
    obj=node(m,u.MaterialExpressionTextureObject,texture=tex)
    if normal:obj.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif tex.get_name().endswith('Roughness'):obj.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    link(obj,call,'TextureObject');link(rgb(m,(size,size,size)),call,'TextureSize')
    # Route the documented named output into a small adapter for common helpers.
    result=node(m,u.MaterialExpressionMultiply,const_b=1.);link(call,result,'A','XYZ Texture');return result
def materials():
    out={}
    for name,spec in P['material_families'].items():
        m=newmat(name);m.set_editor_property('tangent_space_normal',False)
        textures={k:texture(spec['source'],k) for k in ['Color','Normal','Roughness']}
        color=aligned(m,textures['Color'],spec['tile_cm'])
        world=node(m,u.MaterialExpressionWorldPosition);height=mul(m,channel(m,world,'B'),1/170.)
        clean=node(m,u.MaterialExpressionClamp,min_default=0.,max_default=1.);link(height,clean,'')
        grime=blend(m,scalar(m,.38),scalar(m,1.),clean)
        color=mul(m,color,spec['color_scale'])
        if 'base_color' in spec:
            color=blend(m,rgb(m,spec['base_color']),color,scalar(m,spec.get('texture_weight',.18)))
        # World-fixed vertical runoff breaks broad wall bays without a mottled grid.
        streaks=noise(m,mul(m,world,rgb(m,(1.,1.,.085))),.016)
        streaks=blend(m,scalar(m,.90),scalar(m,1.03),streaks)
        color=mul(m,color,streaks)
        bind(mul(m,color,grime),u.MaterialProperty.MP_BASE_COLOR)
        normal=aligned(m,textures['Normal'],spec['tile_cm'],True)
        geometric=node(m,u.MaterialExpressionVertexNormalWS)
        normal=blend(m,geometric,normal,scalar(m,spec['normal_strength']))
        normalized=node(m,u.MaterialExpressionNormalize);link(normal,normalized,'VectorInput');bind(normalized,u.MaterialProperty.MP_NORMAL)
        bind(channel(m,aligned(m,textures['Roughness'],spec['tile_cm']),'R'),u.MaterialProperty.MP_ROUGHNESS)
        bind(scalar(m,spec['metallic']),u.MaterialProperty.MP_METALLIC);bind(scalar(m,.25),u.MaterialProperty.MP_SPECULAR)
        M.recompile_material(m);save(m);out[name]=m;R['materials'].append(m.get_path_name())
    for name,color,emission in [('Stencil',(.26,.29,.25),0),('Emissive',(.40,.008,.003),24.)]:
        m=newmat(name);bind(rgb(m,color),u.MaterialProperty.MP_BASE_COLOR);bind(scalar(m,.8),u.MaterialProperty.MP_ROUGHNESS)
        if emission:bind(mul(m,rgb(m,color),emission),u.MaterialProperty.MP_EMISSIVE_COLOR)
        M.recompile_material(m);save(m);out[name]=m
    return out
def main():
    begin();mats=materials()
    old={'M_Room_Concrete':'Concrete','M_Room_PaintedSteel':'Metal','M_Room_Oxide':'Rust','M_Room_Recess':'Dark','M_Room_EdgeSteel':'Metal'}
    for a in ACTORS.get_all_level_actors():
        if not a.get_actor_label().startswith(('TE_Room_','TE_Parity_RoomExt_','TE_Chamber_')):continue
        if {'ChamberFloorOwned','ChamberSlabsOwned','ChamberCrustOwned'} & {str(t) for t in a.tags}:continue
        changed=[]
        for c in a.get_components_by_class(u.StaticMeshComponent):
            if not c.static_mesh:continue
            slots=c.static_mesh.get_editor_property('static_materials')
            for i in range(c.get_num_materials()):
                current=c.get_material(i);current_name=current.get_name() if current else ''
                key=old.get(current_name)
                if current_name.startswith('M_Chamber_'):key=current_name.removeprefix('M_Chamber_')
                if not key and not current_name.startswith('M_Room_') and i<len(slots):key=str(slots[i].get_editor_property('material_slot_name'))
                if key in mats and key!='Emissive':c.set_material(i,mats[key]);changed.append([c.get_name(),i,key])
        if changed:R['actors'].append({'label':a.get_actor_label(),'overrides':changed})
    finish();R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/(P['revision']+'-materials.json')).write_text(json.dumps(R,indent=2))
