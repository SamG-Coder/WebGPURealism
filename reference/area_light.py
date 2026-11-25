"""Direct irradiance from a uniform, unoccluded, one-sided parallelogram."""
import math

import numpy as np
from numpy.polynomial.legendre import leggauss


def irradiance(point, normal, corner, edge_u, edge_v, order):
    """Return E / Le. Edge winding points toward the light's emitting side."""
    point, normal, corner, u, v = (
        np.asarray(value, dtype=np.float64) for value in (point, normal, corner, edge_u, edge_v)
    )
    area_vector = np.cross(u, v)
    area = np.linalg.norm(area_vector)
    if area == 0 or not np.isclose(np.linalg.norm(normal), 1.0, atol=1e-12, rtol=0):
        raise ValueError("Expected a nondegenerate emitter and a unit receiver normal")
    nodes, weights = leggauss(order)
    s = (nodes + 1) / 2
    ray = corner - point + s[:, None, None] * u + s[None, :, None] * v
    distance_squared = np.sum(ray * ray, axis=-1)
    if np.any(distance_squared == 0):
        raise ValueError("Receiver coincides with emitter sample")
    # Both cosine numerators use an unnormalised direction. The area vector
    # includes the patch Jacobian, leaving squared distance squared below.
    integrand = (np.maximum(ray @ normal, 0) * np.maximum(ray @ -area_vector, 0)
                 / distance_squared**2)
    return float(weights @ integrand @ weights / 4)


def centred_square_exact(half_width_over_height):
    """Parallel receiver facing a centred square, with unit emitted radiance."""
    a = half_width_over_height
    t = a / math.hypot(1, a)
    return 4 * t * math.atan(t)
