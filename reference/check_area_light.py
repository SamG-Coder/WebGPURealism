"""Reproduce issue #5 (run as python reference/check_area_light.py)."""
import json

import numpy as np

from area_light import centred_square_exact, irradiance


def run():
    origin = np.zeros(3)
    up = np.array([0., 0., 1.])
    rows = []
    passed = True
    for a in (0.25, 1., 2.):
        corner = np.array([-a, a, 1.])
        u = np.array([2*a, 0., 0.])
        v = np.array([0., -2*a, 0.])
        exact = centred_square_exact(a)
        for order in (1, 2, 4, 8, 16, 32, 64):
            estimate = irradiance(origin, up, corner, u, v, order)
            error = (estimate - exact) / exact
            rows.append(dict(half_width_over_height=a, order=order, irradiance=estimate,
                             analytic=exact, relative_error=error))
            if order == 64:
                passed &= abs(error) < 1e-8
            if a == 1 and order == 1:
                passed &= error > 0.10
    # A smaller square remains entirely above the tilted receiver's horizon.
    # Odd x contributions cancel by symmetry, leaving cos(theta) times E.
    a = 0.25
    c, u, v = np.array([[-a, a, 1.], [2*a, 0., 0.], [0., -2*a, 0.]])
    exact = centred_square_exact(a)
    tilt = np.array([0.6, 0, 0.8])
    rot = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    offset = np.array([5., -3., 11.])
    checks = {
        "rigid_transform_abs_error": abs(irradiance(offset, rot@up, offset+rot@c,
                                                    rot@u, rot@v, 64) - exact),
        "tilted_receiver_abs_error": abs(irradiance(origin, tilt, c, u, v, 64) - 0.8*exact),
        "back_facing_emitter": irradiance(origin, up, c, v, u, 64),
        "back_facing_receiver": irradiance(origin, -up, c, u, v, 64),
    }
    passed &= max(checks.values()) < 1e-12
    return dict(rows=rows, checks=checks, passed=bool(passed))


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
