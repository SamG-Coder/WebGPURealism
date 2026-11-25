# Mission

Achieve the highest practical visual realism in real-time rendering using standard browser WebGPU. Approach offline path-traced reference quality while maintaining interactive performance. Discover the architecture through experiments; do not prescribe existing engine techniques or copy an existing engine.

## Targets
- Native 1920×1080, 60 FPS (16.67 ms frame budget) on RTX 5080 initially; report actual internal resolution and any reconstruction separately.
- Chrome and Edge, standard WebGPU/WGSL, no native backend or proprietary extensions.
- Dynamic lighting and GI, physically plausible materials, shadows, reflections, vegetation, water and atmosphere. These are research goals, not claims of existing capabilities.
- Build an original modular renderer; choose language, tooling and techniques jointly. Licensed assets and focused libraries are permitted with attribution.
- Eventually evaluate other GPUs and browsers; never silently fall back to a different rendering API.

## Evidence
Establish a reproducible browser harness with deterministic camera paths, fixed seeds, pinned assets and reference images with matched cameras, lighting, exposure and materials. Include indoor, outdoor, foliage, reflective and moving-light scenes. Measure GPU timing where timestamp queries are supported, CPU time, end-to-end frame time, median and tail latency, memory estimates and temporal stability. Record browser, driver, hardware, warmup and sample count. Distinguish measured from estimated quantities. Use image metrics and independent visual review; neither alone establishes realism. Preserve raw results and negative experiments. Freeze acceptance criteria before test runs; do not tune on held-out scenes. Never claim speedups from undisclosed quality reductions. Do not assume a specific architecture will win.
