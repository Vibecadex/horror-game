"""Read-only saved actor/material/light inventory for the isolated room pass."""
import unreal as u

def vec(v):
    return [v.x, v.y, v.z]

def snapshot_level():
    rows = []
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith('TE_'):
            continue
        r = a.get_actor_rotation()
        row = {'label': label, 'class': a.get_class().get_path_name(),
               'location': vec(a.get_actor_location()), 'rotation': [r.pitch, r.yaw, r.roll],
               'scale': vec(a.get_actor_scale3d()), 'hidden': bool(a.get_editor_property('hidden')),
               'tags': [str(t) for t in a.tags], 'meshes': [], 'lights': []}
        for c in a.get_components_by_class(u.StaticMeshComponent):
            b, e, _ = u.SystemLibrary.get_component_bounds(c)
            row['meshes'].append({'name': c.get_name(), 'mesh': c.static_mesh.get_path_name() if c.static_mesh else None,
                'materials': [c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
                'bounds_origin': vec(b), 'bounds_extent': vec(e), 'visible': c.is_visible(),
                'collision': str(c.get_collision_enabled())})
        for c in a.get_components_by_class(u.LightComponent):
            item = {'name': c.get_name(), 'class': c.get_class().get_name()}
            for k in ['intensity', 'attenuation_radius', 'source_radius', 'source_width', 'source_height',
                      'inner_cone_angle', 'outer_cone_angle', 'diffuse_scale', 'specular_scale',
                      'volumetric_scattering_intensity', 'indirect_lighting_intensity', 'cast_shadows']:
                try:
                    item[k] = c.get_editor_property(k)
                except Exception:
                    pass
            row['lights'].append(item)
        for c in a.get_components_by_class(u.LocalFogVolumeComponent):
            row['local_fog'] = {k: c.get_editor_property(k) for k in ['radial_fog_extinction', 'height_fog_extinction', 'fog_phase_g']}
        for c in a.get_components_by_class(u.ExponentialHeightFogComponent):
            row['height_fog'] = {k: c.get_editor_property(k) for k in ['fog_density', 'fog_height_falloff', 'enable_volumetric_fog', 'volumetric_fog_extinction_scale', 'volumetric_fog_distance']}
        rows.append(row)
    return rows
