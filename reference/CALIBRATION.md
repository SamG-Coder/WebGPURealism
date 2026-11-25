# Camera and colour calibration

Render the version 1 calibration scene using pixel-centre rays. Each diffuse surface returns its linear albedo, the emitter returns its radiance on its emitting side, and misses return environment radiance. Apply the scene exposure and sRGB encoding. This diagnostic isolates primary visibility and colour encoding from stochastic light transport. Identical albedos can hide an intersection error where objects overlap.

From the repository root, with the packages in reference/requirements.txt, run the following for each of primary and held-out:

    python -B reference/calibration.py scenes/calibration-diffuse-v1.json output/primary --view primary
    python -B reference/compare.py output/primary/reference.png browser-primary.png reference/profiles/primary.json output/check-primary

The renderer records the exact scene-byte digest, resolved camera and decoded RGB digest. Both images must be opaque 1920 × 1080 PNGs. The profiles were selected using only the CPU reference, before inspecting browser captures. Their validity depends on unchanged scene semantics. If the fixture changes, record the change and freeze new profiles before testing. The held-out profile assesses cross-implementation agreement on a second preselected camera of the same scene.
