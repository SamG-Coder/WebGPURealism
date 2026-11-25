"""Render a deterministic v1 geometry and colour calibration image on the CPU."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from optics import display_rgb, dot, pinhole, quad_distance, sphere_distance


HELD_OUT = {"position": [0.22, 1.14, 3.75], "target": [-0.06, 0.94, 0.]}


def box_distance(origin, direction, obj):
    angle = np.deg2rad(obj["rotateYDeg"])
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, 0., s], [0., 1., 0.], [-s, 0., c]])
    local_origin = (origin - obj["center"]) @ rotation
    local_direction = direction @ rotation
    extent = np.asarray(obj["halfExtents"])
    parallel = local_direction == 0
    divisor = np.where(parallel, 1., local_direction)
    lo, hi = (-extent-local_origin)/divisor, (extent-local_origin)/divisor
    entry = np.max(np.where(parallel, -np.inf, np.minimum(lo, hi)), axis=-1)
    exit_t = np.min(np.where(parallel, np.inf, np.maximum(lo, hi)), axis=-1)
    outside = np.any(parallel & (np.abs(local_origin) > extent), axis=-1)
    t = np.where(entry > 0, entry, exit_t)
    return np.where((exit_t >= entry) & ~outside & (t > 0), t, np.inf)


def render(scene, view, width, height):
    if (scene["format"], scene["formatVersion"], scene["colorSpace"]) != (
            "webgpurealism-scene", 1, "linear-rec709"):
        raise ValueError("Expected a v1 linear Rec.709 scene")
    cam = dict(scene["camera"])
    if view == "held-out":
        cam.update(HELD_OUT)
    if cam["model"] != "pinhole" or cam["outputTransform"] != "exposure-clamp-srgb-oetf":
        raise ValueError("Unsupported camera or output transform")
    eye = np.array(cam["position"])
    rgb = np.empty((height, width, 3), dtype=np.uint8)
    for start in range(0, height, 32):
        end = min(height, start+32)
        rays = pinhole(eye, cam["target"], cam["up"], cam["verticalFovDeg"],
                       width, height, range(start, end))
        nearest = np.full(rays.shape[:2], np.inf)
        linear = np.empty_like(rays)
        linear[:] = scene["environment"]["radiance"]
        for obj in scene["objects"]:
            mat = scene["materials"][obj["material"]]
            if obj["type"] == "quad":
                corner, u, v = (np.array(obj[k]) for k in ("origin", "edgeU", "edgeV"))
                t = quad_distance(eye, rays, corner, u, v, 0.)
            elif obj["type"] == "sphere":
                t = sphere_distance(eye, rays, np.array(obj["center"]), obj["radius"], 0.)
            elif obj["type"] == "box":
                t = box_distance(eye, rays, obj)
            else:
                raise ValueError(f"Unsupported primitive {obj['type']}")
            wins = t < nearest
            if mat["type"] == "lambert":
                linear[wins] = mat["albedo"]
            elif mat["type"] == "emitter" and obj["type"] == "quad":
                front = dot(rays, np.cross(u, v)) < 0
                linear[wins] = 0.
                linear[wins & front] = mat["radiance"]
            else:
                raise ValueError(f"Unsupported material on {obj['name']}")
            nearest[wins] = t[wins]
        rgb[start:end] = display_rgb(linear, cam["exposure"])
    return rgb, cam


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--view", choices=["primary", "held-out"], default="primary")
    args = parser.parse_args()
    raw = args.scene.read_bytes()
    rgb, camera = render(json.loads(raw), args.view, 1920, 1080)
    args.output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(args.output / "reference.png")
    meta = dict(scene_sha256=hashlib.sha256(raw).hexdigest(), camera=camera,
                size=[1920, 1080], view=args.view, sample="pixel-centre",
                mode="unlit-material-calibration", rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest())
    (args.output / "reference.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
