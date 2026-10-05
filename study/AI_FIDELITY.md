# Doing the fidelity pass with AI

5 October 2026. How to use current AI tools on the gaps in [VISUAL_FIDELITY.md](VISUAL_FIDELITY.md), checked against official Unreal 5.8 notes and public texture tools. No encounter asset was changed. Nothing was purchased or installed.

The shot in the plates is mostly light, fog, and scale. AI does not author that shot. AI is useful for the surfaces the plates are missing: a broken floor, a fuzz and seam response on the existing teddy, and a few stain decals. The rig, the clips, the camera, and the Blueprint combat stay as they are.

## What each kind of tool is for

| Job | Tool class | Fits this encounter |
| --- | --- | --- |
| See the target grade before touching the level | Image edit of our own gameplay still | Already done: `visuals/direction-wide.jpg`, `visuals/direction-close.jpg` |
| A tileable floor and a plush micro-texture | Text or photo to a PBR map set | Yes. This is the pass with the most return |
| Crack, mud, and oil decals with a real alpha | Image generation, then a mask | Yes, a handful of decals, not a library |
| A new creature mesh | Image-to-3D (Hunyuan3D, TRELLIS.2, Tripo, Rodin, Meshy) | No. A new mesh throws away the weighted skeleton and the six clips |
| Fog, the contact shadow, the flashlight pool, crushed corners | Unreal lights, exponential height fog, a Local Fog Volume, cloth shading | Not an AI step. The settings are in the fidelity note |
| Driving the editor | Unreal 5.8’s own MCP server | Optional later. It places actors and edits materials. It does not invent the look |

Unreal Engine 5.8 did not ship a material generator. Epic’s 5.8 rendering notes make [MegaLights](https://dev.epicgames.com/documentation/en-us/unreal-engine/megalights-in-unreal-engine) production-ready, including volumetric fog, and add an experimental [Unreal MCP](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) plugin so an agent can call editor tools. Unity’s May 2026 material generator is the editor-native version of “prompt to PBR,” and it is not in this engine. Third-party C++ bridges that drop a plugin into the project are outside this Blueprint project.

## The pass that matches the plates

Do these in order. Stop when a recaptured still hits the check at the bottom.

**1. Generate surfaces, not a new level.**

Make three originals. Do not feed the Husk Cluster frames into the model. Those frames are the measuring stick. Using them as an image prompt copies a commercial character and a commercial room.

- Floor albedo, seamless, 2K or 4K: “dark stained concrete floor, damp, hairline cracks, mottled teal-gray, no tile grid, no text, top-down, even lighting.”
- Plush albedo or a close photo of worn cloth: “matted off-white plush, dirty seams, compressed pile, no face, even lighting.” The teddy’s identity stays the mesh and the existing base color. This map is the fuzz and the dirt.
- Four decals on black: one crack, one damp stain, one scuff, one small debris scatter. Each needs an alpha. A generated RGB picture with no alpha is not a decal yet.

Browser tools that publish this job in 2026 include [3DTexel](https://3dtexel.com/pbr-material-generator/) (prompt to seamless albedo, normal, roughness, height), [PLAYTEX](https://www.playtex.ai/pbr-map-generator) (image to the map stack, with an Unreal ORM packing option), and Material Forge. Free tiers move. Read the listing before a run. A paid credit pack needs a separate yes.

The local tool with a real Unreal export is [ArmorLab](https://armorlab.org). Its photo-to-PBR node estimates base color, occlusion, roughness, normal, and height from one image, and the Unreal preset writes a packed occlusion-roughness-metallic texture. The source tree is [armory3d/armortools](https://github.com/armory3d/armortools/tree/main/armorlab). The prebuilt app is a paid download, so it waits for a yes. ArmorLab’s own model-license folder is worth reading before a commercial ship: the photo-to-PBR nets are one thing, and any Stable Diffusion node inside the app is another.

[Materialize](https://boundingboxsoftware.com/materialize/) is the older free desktop step. It does not invent a texture. Given an albedo or a height, it derives a normal, an occlusion, and a roughness. That is the right second step when a generator only returned a color map.

**2. Reject bad maps before they enter Unreal.**

A usable floor set has all of these:

- The albedo tiles. Offset it by half in both axes and look at the seam.
- The albedo has no baked spotlight, no baked shadow, and no perspective. A top-down photo of a lit room will fight the encounter key light.
- Roughness is a texture, not a constant. Seams and damp patches go rougher or smoother than the field. The current teddy material is a constant roughness of 0.9, which is why the cloth reads as clay.
- The normal is DirectX (Unreal), not OpenGL (Blender). Green channel flipped is the usual fix. 3DTexel and PLAYTEX both expose that switch.
- Metallic stays black on concrete and on plush.
- Height is gentle. A strong height map on a flat floor plane will sparkle and swim under the elevated camera.

A usable plush map is the same test, plus one more: at the encounter camera distance the base color still reads as the teddy. Epic’s skin guide makes the same point about subsurface. Fuzz and cavity detail show. A new face painted by a model does not.

**3. Put the maps on the assets that already exist.**

Floor: replace the tile albedo on the existing floor material. Lay the four decals as deferred decals, different scales and rotations, so the grout lines die. One Local Fog Volume still has to eat the far wall. A perfect floor texture will not hide that corner.

Teddy: keep `M_TeddyCloth` on the existing skeletal mesh. Switch the shading model to Cloth. Plug the fuzz color and a varying roughness. Leave the skeleton, the clips, and the Blueprint alone. A Hunyuan or TRELLIS mesh is a different object. Public 2026 writeups put TRELLIS.2 around a 24 GB card and describe Hunyuan3D as a GLB you retopologize afterward ([Fuser’s Hunyuan3D guide](https://fuser.studio/articles/hunyuan3d-guide), [image-to-3dlab](https://github.com/Bingeljell/image-to-3dlab)). That path is for a prop, a rubble chunk, or a new character. It is the wrong path for a mesh that already deforms.

Image-to-3D is reasonable for one or two debris meshes in the fog, if the license of that generator allows a game. Read it. Tencent’s Hunyuan community license and Stability’s revenue cap are not the same as CC0.

**4. Then do the non-AI lighting pass.**

One cool key, two small red practicals, a short player flashlight with volumetric scattering at 0, teal fog, manual exposure left where the delivery still sits. MegaLights can carry many shadowed area lights and it does affect volumetric fog, and it wants hardware ray tracing. This room does not need dozens of lights. Turn it on only if a later pass adds a field of practicals and the old deferred path gets noisy.

The experimental Unreal MCP server can spawn the fog actor and instance the material once the textures exist. Enabling Epic’s own engine plugin is a separate choice. Do not add a third-party project plugin to get there. The Python authoring scripts already used on this encounter can import the textures and wire the material without one.

## A concrete run, with no new install

This environment can already generate the color maps. The derive step is the part that needs a chosen tool.

1. Generate the floor albedo and the four decal pictures. Keep them under `Assets/Adapted/Arena/` with a provenance note: prompt, tool, date, and “original, not taken from the reference clip.” The finished maps are also in `study/assets/`.
2. Run the albedo through Materialize, ArmorLab, or a browser derive step that is actually free that day. Export Unreal-oriented normal, roughness, and a packed ORM if the tool offers it.
3. Import with the existing editor-script path: `python tools/astra_setup.py editor-script tools/<script>.py`. Point the floor material and `M_TeddyCloth` at the new textures. Do not overwrite the original teddy GLB.
4. Recapture a 1280×720 held plate and sample it the same way as the fidelity note.

## Check

The plate matches the fidelity note’s band when the far corner is gone, the teddy throws a contact shadow, the player stands in a small cool pool, the floor is no longer a tile grid, and the sampled grade sits nearer mean G and B in the mid-20s to low-30s with roughly 8–16% of pixels above luminance 40. The corners stay near black.

If the new textures are in and the grade is still flat, the maps are not the remaining problem. The four wide cool fills are. Go back to the lighting pass.

## Sources

- [Unreal Engine 5.8 announcement](https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available), 23 June 2026. MegaLights production-ready. No first-party text-to-material tool in that note.
- [MegaLights](https://dev.epicgames.com/documentation/en-us/unreal-engine/megalights-in-unreal-engine). Many dynamic area lights, volumetric fog supported, hardware ray tracing recommended.
- [Unreal MCP](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor). Experimental editor server. It drives tools. It does not generate textures.
- [Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine) and [Local Fog Volumes](https://dev.epicgames.com/documentation/en-us/unreal-engine/local-fog-volumes-in-unreal-engine). Still the way the far wall leaves the frame.
- [ArmorLab manual](https://github.com/armory3d/armorlab_web/blob/main/manual.md). Photo to PBR, Unreal ORM preset. Prebuilt builds are paid.
- [Materialize](https://boundingboxsoftware.com/materialize/). Free derive-from-image maps.
- [3DTexel PBR generator](https://3dtexel.com/pbr-material-generator/) and [PLAYTEX PBR map generator](https://www.playtex.ai/pbr-map-generator). Browser map stacks. Confirm the free tier before use.
- [Unity material generator](https://unity.com/blog/unity-ai-material-generator), 14 May 2026. The comparable in-editor feature, in the other engine.
- [Fuser, best AI 3D generators](https://fuser.studio/articles/best-ai-3d-model-generators), 28 September 2026, and [Hunyuan3D guide](https://fuser.studio/articles/hunyuan3d-guide). Image-to-3D returns a GLB you still retopologize. Use it for props, not for the rigged teddy.
