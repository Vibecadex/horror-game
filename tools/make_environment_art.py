"""Deterministic local material maps and an original simple service rifle."""
import bpy,numpy as np,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Assets/Adapted/Arena';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
N=1024; rng=np.random.default_rng(47);yy,xx=np.mgrid[:N,:N];field=np.zeros((N,N),np.float32)
for size,weight in [(4,.12),(12,.08),(38,.06),(128,.03),(512,.02)]:
    grid=rng.random((size+1,size+1));grid[-1,:]=grid[0,:];grid[:,-1]=grid[:,0];gx=xx/N*size;gy=yy/N*size;ix=gx.astype(int);iy=gy.astype(int);fx=gx-ix;fy=gy-iy;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    val=(1-fy)*((1-fx)*grid[iy,ix]+fx*grid[iy,ix+1])+fy*((1-fx)*grid[iy+1,ix]+fx*grid[iy+1,ix+1]);field+=(val-.5)*weight
grain=rng.normal(0,.014,(N,N));base=np.clip(.22+field+grain,.08,.4)
# Irregular old concrete slab seams, hairline branching fractures, damp patches.
seams=np.zeros_like(base)
for a in [205,511,802]:
    line=a+2*np.sin(yy*.031)+np.sin(yy*.15);seams+=np.exp(-((xx-line)/1.4)**2)
for a in [278,652]:seams+=np.exp(-((yy-(a+2*np.sin(xx*.023)))/1.5)**2)
for j in range(19):
    x,y=rng.uniform(0,N,2);theta=rng.uniform(0,math.tau)
    for k in range(rng.integers(14,45)):
        theta+=rng.normal(0,.24);previous_x,previous_y=x,y;x+=math.cos(theta)*8;y+=math.sin(theta)*8
        for q in range(9):
            px=previous_x+(x-previous_x)*q/8;py=previous_y+(y-previous_y)*q/8
            if 0<px<N and 0<py<N:
                xi,yi=int(px),int(py);seams[yi,xi]=max(seams[yi,xi],.45)
base=np.clip(base-.08*seams,.045,.6);height=base*.045-seams*.008
dy,dx=np.gradient(height);normal=np.stack([-dx*22,dy*22,np.ones_like(base)],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
def image(name,rgb,noncolor=False):
    im=bpy.data.images.new(name,width=N,height=N);rgba=np.ones((N,N,4),np.float32);rgba[:,:,:3]=rgb
    if noncolor:im.colorspace_settings.name='Non-Color'
    im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save()
image('T_Concrete_Color',np.stack([base*.83,base*.94,base],-1))
image('T_Concrete_Normal',normal*.5+.5,True)
rough=np.clip(.67+field*.6+seams*.15,.35,.96);image('T_Concrete_Roughness',np.stack([rough]*3,-1),True)
# Weapon axis X forward, origin at grip. Distinct receiver, stock, magazine, barrel and sights.
parts=[]
def box(name,loc,scale):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);parts.append(o)
box('Receiver',(.16,0,.055),(.38,.07,.12));box('Stock',(-.17,0,.07),(.28,.065,.095));box('Butt',(-.3,0,.045),(.04,.095,.18))
box('Grip',(.025,0,-.06),(.065,.055,.16));box('Magazine',(.16,0,-.09),(.07,.055,.20));box('Barrel',(.50,0,.08),(.37,.028,.028));box('Muzzle',(.7,0,.08),(.07,.05,.05));box('Rail',(.21,0,.127),(.32,.045,.02));box('Sight',(.13,0,.16),(.09,.055,.055))
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='SM_ServiceRifle';bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bev=o.modifiers.new('Machined edges','BEVEL');bev.width=.004;bev.segments=2;bpy.ops.object.modifier_apply(modifier=bev.name)
bpy.ops.export_scene.fbx(filepath=str(OUT/'ServiceRifle.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Arena_Art.blend'))
(OUT/'provenance.json').write_text(json.dumps({'author':'Original procedural local authoring for this encounter','seed':47,'texture_size':N,'source_assets':[]},indent=2))
