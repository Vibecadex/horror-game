import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=u.EditorAssetLibrary;L=u.BlueprintEditorLibrary
r={}
bs=A.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run');r['samples']=[str(x) for x in bs.get_editor_property('sample_data')]
bp=A.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed');r['graphs']={}
for gr in L.list_graphs(bp):
    data=[]
    for n in u.BlueprintGraphEditor.get_graph_editor(gr).list_all_nodes():
        info={'name':n.get_name(),'class':n.get_class().get_name(),'title':str(L.get_node_title(n))}
        for k in ['node','blend_space','animation']:
            try:info[k]=str(n.get_editor_property(k))
            except Exception:pass
        data.append(info)
    r['graphs'][gr.get_name()]=data
mat=A.load_asset('/Game/TeddyEncounter/Materials/M_TeddyCloth');r['material_inputs']={}
for o in u.ObjectIterator(u.MaterialExpression):
    if o.get_outer()==mat:
        r['material_inputs'][o.get_name()]={'class':o.get_class().get_name(),'inputs':str(u.MaterialEditingLibrary.get_material_expression_input_names(o))}
r['hud_api']=u.HUD.__doc__
(R/'evidence/implementation/animation-api.json').write_text(json.dumps(r,indent=2))
