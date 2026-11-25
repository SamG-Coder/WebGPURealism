# 0001. Bootstrap calibration and measurement

Claude and Codex agreed to this bootstrap protocol on [issue 1](https://github.com/SamG-Coder/WebGPURealism/issues/1). Its scope is the evaluation interface. Production rendering choices remain open.

## Calibration

One repository-authored, asset-free scene defines geometry in metres, camera, linear RGB materials and light. The browser renderer and independent CPU reference read the same versioned scene data. A pinhole sample at each pixel centre determines visibility. Multiply linear radiance by exposure, clamp to [0,1], and apply the piecewise sRGB encoding for the calibration PNG. Preserve browser, scene hash, camera, frame, seed, dimensions and transform with results. Record source, license and attribution before adding third-party assets.

The offline oracle and browser use separate math implementations. Test known camera rays, analytic intersections and display values before testing a browser. Evaluate the full image, local patches and edge positions from a frozen profile. Repeat with a held-out camera and perturb the capture and transfer function as controls. These checks establish that a common scene and shading estimator travel through both pipelines consistently. Evaluating physical accuracy will require an independent converged light-transport reference.

## Performance protocol

Capture lossless images outside timed runs. For each installed browser, record three native 1920 × 1080 trials, each with 120 warmup frames and 600 measured frames. Keep raw GPU timestamp durations (if supported), CPU encode/submit wall time and animation-frame intervals separate. Report median, p95, p99, environment and resource byte estimates. Document unsupported features and device loss. Claim timed GPU windows on issue 1 and acquire the shared machine lock before running. Coordinate other GPU activity during these windows.

## Dependencies and research order

1. Establish browser capture and independent CPU calibration on the same pinned scene. Freeze the second camera and image checks before comparing outputs. [Browser work](https://github.com/SamG-Coder/WebGPURealism/issues/2) and [reference work](https://github.com/SamG-Coder/WebGPURealism/issues/3).
2. Verify repeatability, positive and negative controls, and timing distributions on both browsers. Record failures and obtain exact-head independent review before integration.
3. Establish a converged offline area-light reference and quantify uncertainty using independent samples. Use that baseline to test a first real-time lighting hypothesis with a fixed quality target. Freeze held-out scenes and temporal metrics before evaluating dynamic reconstruction.
