"""Float64 geometry and display math for the independent offline oracle."""
import numpy as np


def unit(vector):
    return vector / np.linalg.norm(vector, axis=-1, keepdims=True)


def dot(a, b):
    return np.sum(a * b, axis=-1)


def pinhole(eye, target, up, fov_y_degrees, width, height, rows):
    forward = unit(np.asarray(target) - eye)
    right = unit(np.cross(forward, up))
    camera_up = np.cross(right, forward)
    half_height = np.tan(np.deg2rad(fov_y_degrees) / 2)
    x = (2 * (np.arange(width) + 0.5) - width) / height
    y = 1 - 2 * (np.asarray(rows) + 0.5) / height
    return unit(forward + half_height * (x[None, :, None] * right
                                         + y[:, None, None] * camera_up))


def sphere_distance(origin, direction, center, radius, epsilon):
    offset = origin - center
    b = dot(offset, direction)
    discriminant = b*b - (dot(offset, offset) - radius*radius)
    root = np.sqrt(np.maximum(0, discriminant))
    near, far = -b - root, -b + root
    t = np.where(near > epsilon, near, far)
    return np.where((discriminant >= 0) & (t > epsilon), t, np.inf)


def quad_distance(origin, direction, corner, u, v, epsilon):
    normal = np.cross(u, v)
    denominator = dot(direction, normal)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = dot(corner - origin, normal) / denominator
        local = origin - corner + t[..., None] * direction
        # Dual basis supports any non-degenerate parallelogram.
        uu = dot(local, np.cross(v, normal)) / dot(normal, normal)
        vv = dot(local, np.cross(normal, u)) / dot(normal, normal)
    inside = (uu >= 0) & (uu <= 1) & (vv >= 0) & (vv <= 1)
    return np.where(inside & (t > epsilon) & np.isfinite(t), t, np.inf)


def display_rgb(radiance, exposure):
    linear = np.clip(radiance * exposure, 0, 1)
    encoded = np.where(linear <= 0.0031308, 12.92 * linear,
                       1.055 * linear ** (1 / 2.4) - 0.055)
    return np.rint(255 * encoded).astype(np.uint8)
