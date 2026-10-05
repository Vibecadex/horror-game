"""Fit retained service props to a flush drain edge and add wall practicals."""
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
from import_chamber_kit import collision_off
R={'passed':False,'changes':[],'gameplay_collision_unchanged':True}
def main():
    begin();actors={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    def move(label,loc=None,scale=None,hide=False):
        a=actors[label];assert 'TeddyEncounterOwned' in [str(t) for t in a.tags]
        before=a.get_actor_location();oldscale=a.get_actor_scale3d()
        if loc:a.set_actor_location(u.Vector(*loc),False,False)
        if scale:a.set_actor_scale3d(u.Vector(*scale))
        if hide:
            a.set_actor_hidden_in_game(True)
            for c in a.get_components_by_class(u.PrimitiveComponent):c.set_editor_property('visible',False);c.set_editor_property('cast_shadow',False)
        R['changes'].append({'label':label,'before':[before.x,before.y,before.z],'before_scale':[oldscale.x,oldscale.y,oldscale.z],'location':loc,'scale':scale,'concealed':hide})
    # Decorative foundations had formed a 61cm raised stage; retain narrow low
    # plinths instead. The four original collision walls are never touched.
    for sign in [-1,1]:
        move('TE_Room_SideFoundation_'+str(sign),(90,sign*1625,1),(31.8,1.1,.12))
        move('TE_Room_SideGutter_'+str(sign),(90,sign*1548,-4.2),(31.8,1.08,.04))
        for i,x in enumerate([-1070,-550,-10,550,1090]):
            move('TE_Room_DrainGrate_'+str(sign)+'_'+str(i),(x,sign*1548,-7.6))
    move('TE_Room_FarFoundation',(1620,0,1),(1.2,33.5,.12))
    for label,z in [('RearTank',-5),('RightCabinetA',-5),('RightCabinetB',-5),('RightTank',-5),('LeftCrate',-2),('RightSpool',-2),('RearCrate',-2)]:
        a=actors['TE_Room_'+label];p=a.get_actor_location();move('TE_Room_'+label,(p.x,p.y,z))
    for label in ['TE_Chamber_RightServiceDrums','TE_Chamber_LeftServiceDrums','TE_Chamber_RearDrum']:
        p=actors[label].get_actor_location();move(label,(p.x,p.y,-5))
    move('TE_Room_RearFan',(1612,1130,445),(.90,.90,.90))
    # Rear body grows coherently in both its width and height, while its threshold
    # meets the floor. Pivot and wheel stay aligned; sources remain immutable.
    move('TE_Chamber_RearBulkhead',(1630,180,7),(1.15,1.,1.12))
    move('TE_Chamber_RearBulkheadWheel',(1549,180,291),(1.06,1.06,1.06))
    move('TE_Room_RearPilaster_780',(1635,850,-5))
    # Matched small warning indicators sit on either side of the pressure frame.
    cube=u.load_asset('/Engine/BasicShapes/Cube')
    for side,y in [('L',-460),('R',820)]:
        for key,loc,size,material in [('Housing',(1540,y,330),(18,23,44),'Dark'),('Lens',(1529,y,330),(3,9,24),'Emissive')]:
            label='BulkheadBeacon'+side+key;a=actors.get('TE_Chamber_'+label)
            if a:assert 'ChamberOwned' in [str(t) for t in a.tags]
            else:a=spawn(u.StaticMeshActor,label,loc)
            a.set_actor_location(u.Vector(*loc),False,False);a.set_actor_scale3d(u.Vector(*(s/100 for s in size)));a.set_actor_enable_collision(False)
            c=a.static_mesh_component;c.set_static_mesh(cube);collision_off(c);c.set_material(0,existing(DEST+'/Materials/M_Chamber_'+material));c.set_lighting_channels(True,False,True)
    # Suppress sharp pale chip sides that read like reflective threads in reverse.
    edge=existing(DEST+'/Materials/M_Chamber_FloorAggregate');crack=existing(DEST+'/Materials/M_Chamber_FloorCrack')
    for a in ACTORS.get_all_level_actors():
        if a.get_actor_label().startswith('TE_Parity_Floor_'):
            c=a.static_mesh_component
            for i,slot in enumerate(c.static_mesh.get_editor_property('static_materials')):
                key=str(slot.get_editor_property('material_slot_name'))
                if key=='Aggregate':c.set_material(i,edge)
                elif key=='Dark':c.set_material(i,crack)
    # Header fixture makes the overhead pool physically motivated, with an actual
    # soft downward light that affects only the architecture.
    move('TE_Room_RearFixture_0',(1590,180,655),(1.35,1.,1.))
    move('TE_Room_RearFixture_1',hide=True)
    lens=newmat('PracticalLens');bind(rgb(lens,(.25,.40,.38)),u.MaterialProperty.MP_BASE_COLOR);bind(rgb(lens,(25,50,46)),u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(lens);save(lens)
    fixture=actors['TE_Room_RearFixture_0'].static_mesh_component
    for i,slot in enumerate(fixture.static_mesh.get_editor_property('static_materials')):
        if 'emissive' in str(slot.get_editor_property('material_slot_name')).lower():fixture.set_material(i,lens)
    # Modeled front structural returns replace only the five flat cube piers.
    bp=existing(DEST+'/Blueprints/BP_ChamberCutaway');pillar=existing(NS+'/Room/Meshes/SM_RoomPilaster');assert pillar
    for i,y in enumerate([-1660,-1130,0,1130,1660]):
        c=component(bp,'FrontPier_'+str(i),u.StaticMeshComponent,parent='ChamberRoot');c.set_static_mesh(pillar)
        c.set_editor_property('relative_location',u.Vector(-1585,y,-5));c.set_editor_property('relative_rotation',u.Rotator(yaw=-90));c.set_editor_property('relative_scale3d',u.Vector(1.15,1.,1.26));collision_off(c)
        for j,slot in enumerate(pillar.get_editor_property('static_materials')):
            key=str(slot.get_editor_property('material_slot_name'));material=existing(DEST+'/Materials/M_Chamber_'+key)
            if material:c.set_material(j,material)
        c.set_lighting_channels(True,False,True)
    # Both bay indicators brighten as material overrides; no detached floating light.
    indicator=newmat('ServiceIndicator');bind(rgb(indicator,(.3,.006,.002)),u.MaterialProperty.MP_BASE_COLOR);bind(rgb(indicator,(32,.2,.04)),u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(indicator);save(indicator)
    for name in ['ReverseDoorL','ReverseDoorR']:
        c=component(bp,name,u.StaticMeshComponent,parent='ChamberRoot')
        for j,slot in enumerate(c.static_mesh.get_editor_property('static_materials')):
            if str(slot.get_editor_property('material_slot_name'))=='Emissive':c.set_material(j,indicator)
    pool=component(bp,'ReverseOverheadPool',u.SpotLightComponent,parent='ChamberRoot')
    pool.set_editor_property('relative_location',u.Vector(-1370,0,620));pool.set_editor_property('relative_rotation',u.MathLibrary.find_look_at_rotation(u.Vector(-1370,0,620),u.Vector(-1610,0,290)))
    for k,v in {'intensity_units':u.LightUnits.CANDELAS,'intensity':3500.,'attenuation_radius':1100.,'inner_cone_angle':15.,'outer_cone_angle':52.,'source_radius':35.,'volumetric_scattering_intensity':2.,'indirect_lighting_intensity':0.}.items():pool.set_editor_property(k,v)
    pool.set_light_color(u.LinearColor(.34,.70,.69,1));pool.set_lighting_channels(False,False,True);pool.set_cast_shadows(True);compile(bp)
    # Earlier surface passes created placed-instance material overrides. Rebind
    # the managed component instances explicitly, then verify them after reload.
    for c in actors['TE_Chamber_FrontCutaway'].get_components_by_class(u.StaticMeshComponent):
        name=c.get_name()
        if name.startswith('FrontPier_'):
            i=int(name.rsplit('_',1)[1]);c.set_static_mesh(pillar)
            c.set_editor_property('relative_location',u.Vector(-1585,[-1660,-1130,0,1130,1660][i],-5))
            c.set_editor_property('relative_rotation',u.Rotator(yaw=-90));c.set_editor_property('relative_scale3d',u.Vector(1.15,1.,1.26));collision_off(c)
            for j,slot in enumerate(pillar.get_editor_property('static_materials')):
                material=existing(DEST+'/Materials/M_Chamber_'+str(slot.get_editor_property('material_slot_name')))
                if material:c.set_material(j,material)
        if name in ['ReverseDoorL','ReverseDoorR']:
            for j,slot in enumerate(c.static_mesh.get_editor_property('static_materials')):
                if str(slot.get_editor_property('material_slot_name'))=='Emissive':c.set_material(j,indicator)
    name='TE_Chamber_HeaderPractical'
    if name in actors:assert 'ChamberOwned' in [str(t) for t in actors[name].tags];assert ACTORS.destroy_actor(actors[name])
    a=spawn(u.SpotLight,'HeaderPractical',(1390,180,625),u.MathLibrary.find_look_at_rotation(u.Vector(1390,180,625),u.Vector(1640,180,390)))
    c=a.get_component_by_class(u.SpotLightComponent)
    for k,v in {'mobility':u.ComponentMobility.MOVABLE,'intensity_units':u.LightUnits.CANDELAS,'intensity':5000.,'attenuation_radius':1100.,'inner_cone_angle':20.,'outer_cone_angle':48.,'source_radius':45.,'volumetric_scattering_intensity':1.5,'indirect_lighting_intensity':0.}.items():c.set_editor_property(k,v)
    c.set_light_color(u.LinearColor(.40,.80,.81,1));c.set_lighting_channels(False,False,True);c.set_cast_shadows(True)
    finish();R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/'chamber-details.json').write_text(json.dumps(R,indent=2))
