"""Small checked helpers for owned encounter assets and saved Blueprint graphs."""
import unreal as u
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; NS='/Game/TeddyEncounter'; TAG='TeddyEncounter.Owner'; OWNER='encounter-20261004'
A=u.EditorAssetLibrary; L=u.BlueprintEditorLibrary; M=u.MaterialEditingLibrary
def historical_builder(script):
    # These builders recreate early encounter state wholesale. On the saved project
    # they erase later chamber, camera, boss and feedback work, then save over it.
    import os
    if A.does_asset_exist('/Game/Maps/TeddyEncounter') and os.environ.get('TEDDY_ALLOW_HISTORICAL_REBUILD')!='1':
        raise RuntimeError(Path(script).name+' is a historical builder: on the saved project it would erase later '
                           'chamber/camera/boss work. Continue the saved project instead (study/TEAM_CONTINUATION.md). '
                           'Only a person may decide to rebuild a scratch copy of the project, by setting '
                           'TEDDY_ALLOW_HISTORICAL_REBUILD=1 for that run; agents must not set it.')
def own(obj): A.set_metadata_tag(obj,TAG,OWNER);return obj
def existing(path):
    if A.does_asset_exist(path):
        obj=A.load_asset(path);assert A.get_metadata_tag(obj,TAG)==OWNER, 'Unowned asset: '+path
        return obj
def asset(name,cls,factory):
    path=NS+'/'+name;obj=existing(path)
    if obj:return obj
    return own(u.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit('/',1)[1],path.rsplit('/',1)[0],cls,factory))
def duplicate(src,name):
    path=NS+'/'+name;obj=existing(path)
    return obj or own(A.duplicate_asset(src,path))
def blueprint(name,parent=u.Actor):
    path=NS+'/Blueprints/'+name
    return existing(path) or own(L.create_blueprint_asset_with_parent(path,parent.static_class()))
def save(obj):assert A.save_loaded_asset(obj,False),obj.get_path_name()
def components(bp):
    s=u.get_engine_subsystem(u.SubobjectDataSubsystem);out={}
    for h in s.k2_gather_subobject_data_for_blueprint(bp):
        d=u.SubobjectDataBlueprintFunctionLibrary.get_data(h);o=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
        if o:out[o.get_name()]=(h,o)
    return out
def component(bp,name,cls,parent=None):
    s=u.get_engine_subsystem(u.SubobjectDataSubsystem);cs=components(bp)
    key=name+'_GEN_VARIABLE'
    if key in cs:return cs[key][1]
    handles=s.k2_gather_subobject_data_for_blueprint(bp)
    ph=next((h for n,(h,o) in cs.items() if n==parent or n==str(parent)+'_GEN_VARIABLE'),handles[0])
    h,why=s.add_new_subobject(u.AddNewSubobjectParams(parent_handle=ph,new_class=cls,blueprint_context=bp))
    assert not str(why),str(why)
    assert s.rename_subobject(h,name)
    d=u.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    return u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
def compile(bp):
    assert L.compile_blueprint(bp),bp.get_path_name()
    for gr in L.list_graphs(bp):
        errors=u.BlueprintGraphEditor.get_graph_editor(gr).list_nodes_with_errors()
        assert not errors,[(n.get_name(),L.get_node_title(n)) for n in errors]
    save(bp)
class Graph:
    def __init__(self,bp,function=None):
        self.bp=bp;self.g=u.BlueprintGraphEditor.create_and_edit_function_graph(bp,function) if function else u.BlueprintGraphEditor.get_graph_editor(L.find_event_graph(bp));self.count=0
    def node(self,n):
        assert n
        n.set_node_pos(u.IntPoint((self.count%7)*320,(self.count//7)*240));self.count+=1;return n
    def call(self,path,/,**values):
        if not path.startswith('/'):path='/Script/Engine.'+path
        n=self.node(self.g.add_call_function_node(path))
        for k,v in values.items():self.val(n,k,v)
        return n
    def val(self,n,k,v):
        p=n.find_input_pin(k);assert p.is_valid(),(L.get_node_title(n),k,[str(x.get_pin_name()) for x in n.list_input_pins()])
        if isinstance(v,u.BlueprintGraphPin):assert v.try_create_connection(p),(k,v)
        elif isinstance(v,tuple):self.link(v[0],v[1],n,k)
        else:assert p.set_pin_value(str(v)),(L.get_node_title(n),k,v)
    def link(self,a,pa,b,pb):
        x=a.find_output_pin(pa);y=b.find_input_pin(pb)
        assert x.is_valid() and y.is_valid(),(L.get_node_title(a),pa,L.get_node_title(b),pb)
        assert x.try_create_connection(y),(L.get_node_title(a),pa,L.get_node_title(b),pb)
    def chain(self,*nodes):
        for a,b in zip(nodes,nodes[1:]):self.link(a,'then',b,'execute')
    def get(self,name,cls=''):return self.node(self.g.add_get_member_variable_node(name,cls))
    def set(self,name,value,cls=''):
        n=self.node(self.g.add_set_member_variable_node(name,cls));self.val(n,name,value);return n
    def var(self,name,type='real',value='0'):
        if L.get_member_variable_type(self.bp,name) is None:
            assert self.g.add_member_variable(name,L.get_basic_type_by_name(type),str(value))
    def event(self,name):return self.node(L.add_event_override(self.bp,name,u.IntPoint(0,0)))
    def custom(self,name):return self.node(self.g.add_custom_event_node(name))
    def branch(self,condition):
        n=self.node(self.g.add_branch_node());self.val(n,'Condition',condition);return n
    def math(self,name,**kwargs):return self.call('KismetMathLibrary.'+name,**kwargs)
    def ret(self,n,pin='ReturnValue'):return(n,pin)
def constmat(name,color,rough=.8,emission=0):
    mat=asset('Materials/'+name,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(mat)
    c=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector);c.set_editor_property('constant',u.LinearColor(*color,1))
    M.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    r=M.create_material_expression(mat,u.MaterialExpressionConstant);r.set_editor_property('r',rough);M.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
    if emission:
        mul=M.create_material_expression(mat,u.MaterialExpressionMultiply);mul.set_editor_property('const_b',emission);M.connect_material_expressions(c,'',mul,'A');M.connect_material_property(mul,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat);save(mat);return mat
