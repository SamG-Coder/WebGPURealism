# Independent offline lighting reference

This experiment imports the authored v1 room into Mitsuba 3. It measures steady-state RGB radiance with an independent sampler, an emitter-sampling path integrator, a box-filtered pinhole camera, unlimited path depth and Russian roulette starting at depth five. It is an offline CPU evaluation dependency. The browser renderer continues to use standard WebGPU.

## Reproduce

Use a separate Python 3.12 environment. Install reference/mitsuba/requirements.txt. Reserve a window before running on the browser benchmark machine. From the repository root run:

    python reference/mitsuba/render.py scenes/calibration-diffuse-v1.json results/mitsuba-s16

The frozen input and controls are documented in [issue 8](https://github.com/SamG-Coder/WebGPURealism/issues/8). The script uses fixed seeds 17 and 31. Pass a different output directory when changing the sample count with --spp. The scalar_rgb variant traces on the CPU with two render workers. No LLVM or GPU backend is needed.

Both seed images are retained as unclamped float32 RGB NumPy arrays. The PNG shows their arithmetic mean after the scene exposure, clamp and sRGB transfer. Measure disagreement in the linear arrays before this display transform. Relative RMS divides the RMS difference of the two images by the RMS of their mean. Evaluate both the entire frame and a fixed diffuse region because the bright visible lamp can mask noise elsewhere. A failed convergence threshold is a valid experiment outcome; inspect result.json for the convergence flag. A failed camera or radiance control invalidates the trial.

Quads use the supplied edge winding, two-sided diffuse reflectance and a one-sided emitter. The box uses half extents and rotation about world Y. Three camera probes check the projected left wall, right wall and light against Mitsuba intersections before tracing. CPU render wall time includes camera sampling and light transport; it does not represent a browser timing. [Mitsuba sensor conventions](https://mitsuba.readthedocs.io/en/stable/src/generated/plugins_sensors.html) and [shape definitions](https://mitsuba.readthedocs.io/en/stable/src/generated/plugins_shapes.html).
