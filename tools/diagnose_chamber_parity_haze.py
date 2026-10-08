"""Transient local-volume calibration. No saved map or asset writes."""
import sys
from pathlib import Path
import unreal as u
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture_chamber_views as g

g.VIEWS = [dict(g.VIEWS[0], name=f'{i:02d}-emission-{power}', power=power)
           for i,power in enumerate([.02,.07,.20,.60])]
g.report['method'] = 'Diagnostic PIE-only local fog emission sweep; native full-room camera, no map or asset writes.'
original = g.stage

def stage(world, player, pc):
    original(world, player, pc)
    fog = next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.LocalFogVolume)
               if a.get_actor_label()=='TE_Parity20261007_UpperHaze')
    c = fog.get_component_by_class(u.LocalFogVolumeComponent)
    # UE 5.8 combines radial and height coverage multiplicatively. Zero height
    # extinction cancels this radial volume as well (verified installed shader).
    c.set_height_fog_extinction(.24)
    c.set_height_fog_falloff(1.)
    power = g.VIEWS[g.state['index']]['power']
    c.set_fog_emissive(u.LinearColor(.001,.004,.0036,1))
    for light in u.GameplayStatics.get_all_actors_of_class(world, u.Light):
        lc=light.get_component_by_class(u.LightComponent)
        if light.get_actor_label()=='TE_Parity20261007_OverheadShaft':
            lc.set_editor_property('volumetric_scattering_intensity',power)
        elif light.get_actor_label()=='TE_Parity_Key':
            lc.set_editor_property('volumetric_scattering_intensity',.04)
        elif light.get_actor_label()=='TE_Parity_FarFog_Light':
            lc.set_editor_property('volumetric_scattering_intensity',.02)
    g.report.setdefault('sweep', []).append({'power':power,'hidden':fog.get_editor_property('hidden'),
        'active':c.is_active(),'visible':c.is_visible(),'emissive':str(c.get_editor_property('fog_emissive')),
        'cvars':{k:u.SystemLibrary.get_console_variable_int_value(k) for k in
                 ['r.VolumetricFog','r.LocalFogVolume','r.LocalFogVolume.RenderIntoVolumetricFog','r.Fog','sg.ShadowQuality']}})

g.report['method']='Diagnostic PIE-only shaft scattering sweep with key scattering .04 and fog rect .02. No map or asset writes.'
g.stage = stage
