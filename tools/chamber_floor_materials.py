"""Chamber-only floor siblings; all preserved source texture inputs are read-only."""
from chamber_common import *
import apply_parity_combined as combined
import apply_parity_look as look
def floor(name,factor=1.,profile=None):
    s={**P['floor'],**(profile or {})};m=newmat('Floor'+name)
    world=node(m,u.MaterialExpressionWorldPosition)
    xy=node(m,u.MaterialExpressionComponentMask,r=True,g=True,b=False,a=False);link(world,xy,'Input')
    uv=mul(m,xy,1/s['tile_cm'])
    soft=look.sample(m,'T_AI_Floor_Color',u.MaterialSamplerType.SAMPLERTYPE_COLOR,uv)
    detailed=look.texture_sample(m,look.parity_texture(),uv)
    color=blend(m,soft,detailed,scalar(m,s['detail_weight']))
    d=node(m,u.MaterialExpressionDesaturation);link(color,d,'');link(scalar(m,.70),d,'Fraction')
    dry=combined.data_sample(m,'T_Comfy_Floor_Dry',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE,mul(m,xy,1/1350.))
    wear=blend(m,scalar(m,.50),scalar(m,1.),dry)
    x=channel(m,world,'R');gradient=mul(m,add(m,mul(m,x,-1),scalar(m,-250)),1/650.)
    weight=node(m,u.MaterialExpressionClamp,min_default=0.,max_default=1.);link(gradient,weight,'')
    damp=blend(m,scalar(m,s['foreground_damp']),scalar(m,s['foreground_dry']),dry)
    wear=blend(m,wear,damp,weight)
    bind(mul(m,mul(m,d,s['value_scale']*factor),wear),u.MaterialProperty.MP_BASE_COLOR)
    nr=look.floor_bump(m,look.parity_texture(),uv)
    old=look.sample(m,'T_AI_Floor_Normal',u.MaterialSamplerType.SAMPLERTYPE_NORMAL,uv)
    bind(blend(m,old,nr,scalar(m,s.get('normal_mix',.55))),u.MaterialProperty.MP_NORMAL)
    if name=='Aggregate':
        rough=scalar(m,.98);spec=scalar(m,.07)
    else:rough=blend(m,scalar(m,.46),scalar(m,.92),dry);spec=scalar(m,.22)
    bind(rough,u.MaterialProperty.MP_ROUGHNESS);bind(spec,u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(m);save(m);return m
