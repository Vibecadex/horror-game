# DefeatGrounded animation

Separate 2.367 second collapse for the preserved Teddy skeleton. Import `Teddy_DefeatGrounded.fbx` as animation only onto the existing skeleton, with the same `force_front_x_axis=True` convention as the six original clips. A 60 Hz import sample rate retains the contact bake. Do not update the skeleton reference pose or replace the V2 skeletal mesh.

The original Defeat was already height corrected, but its final pose balanced on the head: torso-core minimum height was 1.395 m. Lowering the root alone would bury the head. This approved revision rotates the root toward a broad side/back support plane, with gentle head and limb settling. The source skin, UVs, weights, bones, and six original actions are preserved. The character's original stylized anatomy remains.

`manifest.json` contains all 285 deformation checks at 120 samples/second. Lowest skinned surface stays 1.185–1.247 cm above local ground; the final torso minimum is 1.2 cm. The first pose is exactly the original Defeat start. All 18 source-clip pose comparisons have zero error. The animated FBX round trip preserves 16 bone names/parents and checked poses within 1.26 micrometers at the bone heads. Blender import validation uses `anim_offset=0`; its default otherwise adds a frame.

Preview evidence: `source-defeat-contact-side.png`, `corrected-mid-side.png`, `corrected-end-side.png`, `corrected-end-game-angle.png`. These are neutral Blender studio views with source materials, not claims of Unreal visual acceptance. Existing runtime mesh offset adds about 2.15 cm to local surface clearance. Root's Unreal capture must verify the imported clip and gameplay transition.

Editable source: `Teddy_DefeatGrounded.blend`. Generator: `tools/make_parity_defeat.py`. All outputs are owned by the parity defeat task; original assets and V1/V2 exports were not overwritten. Diagnostic trial scripts/images remain separate from the delivered clip.
