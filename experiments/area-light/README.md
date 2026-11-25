# Direct irradiance of a rectangular light

Frozen criteria and scope are in [issue 5](https://github.com/SamG-Coder/WebGPURealism/issues/5). This CPU control evaluates the irradiance at a point from a uniform, unoccluded, one-sided light. It uses unit emitted radiance. For a diffuse material multiply the resulting irradiance by linear albedo / π to obtain outgoing radiance.

## Independent analytic check

Place a square of half-width a at unit separation, centred on the receiver and facing it. Rescale lengths by the separation for other distances. The two cosine factors and inverse-square falloff give the integrand 1/(1+x²+y²)². This equals the 2D divergence of (x,y)/(2(1+x²+y²)). Integrating the outward flux over the four edges gives 4t atan(t), with t = a/sqrt(1+a²). It tends to π as the light fills the hemisphere.

The numerical routine instead samples emitter positions in world space and integrates the projected solid angle with a tensor Gauss–Legendre rule. Order 1 is the common single centre sample times area. Order 64 evaluates 4096 points.

## Reproduction and interpretation

On Windows with Python 3.14.7 and NumPy 2.5.3 run:

    python -B reference/check_area_light.py

The command prints all 21 scalar estimates, signed relative errors and orientation checks, and exits nonzero on failed criteria. Raw results from the initial run are in results.json. With half-width equal to separation the centre rule gives 4 versus approximately 1.741 for the integral, overestimating irradiance by approximately 130%. All three order-64 results satisfy the frozen relative tolerance of 1e-8.

The error is measured in linear lighting before exposure. A clamped PNG can conceal it. This motivates a linear-radiance control for a future browser area-light experiment. These data cover direct illumination at an unoccluded point. No GPU frames, temporal samples, browser memory or CPU submission timings are involved.
