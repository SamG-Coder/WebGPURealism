"""Independent offline path reference for the v1 diffuse room."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import drjit as dr
import mitsuba as mi
import numpy as np
from PIL import Image

mi.set_variant("scalar_rgb")
dr.set_thread_count(2)


def spectrum(values):
    return {"type": "rgb", "value": values}


def shape(obj, material):
    transform = mi.ScalarTransform4f
    if obj["type"] == "quad":
        p, u, v = (np.array(obj[k]) for k in ("origin", "edgeU", "edgeV"))
        n = np.cross(u, v)
        matrix = np.eye(4)
        matrix[:3] = np.column_stack((u/2, v/2, n/np.linalg.norm(n), p+(u+v)/2))
        result = {"type": "rectangle", "to_world": transform(matrix)}
    elif obj["type"] == "sphere":
        result = {"type": "sphere", "center": obj["center"], "radius": obj["radius"]}
    elif obj["type"] == "box":
        result = {"type": "cube", "to_world": transform.translate(obj["center"])
                  @ transform.rotate([0, 1, 0], obj["rotateYDeg"])
                  @ transform.scale(obj["halfExtents"])}
    else:
        raise ValueError(obj["type"])
    if material["type"] == "lambert":
        result["bsdf"] = {"type": "twosided", "material": {
            "type": "diffuse", "reflectance": spectrum(material["albedo"])}}
    elif material["type"] == "emitter":
        result["emitter"] = {"type": "area", "radiance": spectrum(material["radiance"])}
        result["bsdf"] = {"type": "diffuse", "reflectance": spectrum([0, 0, 0])}
    else:
        raise ValueError(material["type"])
    return result


def load(data):
    cam = data["camera"]
    if (data["formatVersion"], data["colorSpace"], data["units"], cam["model"],
        cam["pixelFilter"], cam["outputTransform"]) != (
            1, "linear-rec709", "metres", "pinhole", "box", "exposure-clamp-srgb-oetf"):
        raise ValueError("Unsupported scene or camera specification")
    scene = {"type": "scene", "integrator": {"type": "path", "max_depth": -1, "rr_depth": 5},
             "sensor": {"type": "perspective", "fov_axis": "y", "fov": cam["verticalFovDeg"],
                        "to_world": mi.ScalarTransform4f.look_at(origin=cam["position"],
                            target=cam["target"], up=cam["up"]),
                        "sampler": {"type": "independent"},
                        "film": {"type": "hdrfilm", "width": 1920, "height": 1080,
                                 "rfilter": {"type": "box"}}}}
    if any(data["environment"]["radiance"]):
        scene["environment"] = {"type": "constant", "radiance": spectrum(data["environment"]["radiance"])}
    for obj in data["objects"]:
        scene[obj["name"]] = shape(obj, data["materials"][obj["material"]])
    return mi.load_dict(scene)


def relative_rms(a, b):
    a, b = a.astype(np.float64), b.astype(np.float64)
    return float(np.sqrt(np.mean((a-b)**2) / np.mean(((a+b)/2)**2)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--spp", type=int, default=16)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = args.scene.read_bytes()
    data = json.loads(raw)
    scene = load(data)
    sensor = scene.sensors()[0]
    for x, expected in [(515, "left"), (1380, "right"), (960, "lamp")]:
        y = 150 if expected == "lamp" else 535
        ray, _ = sensor.sample_ray(0., 0., [(x+.5)/1920, (y+.5)/1080], [0., 0.])
        hit = scene.ray_intersect(ray).shape
        if hit is None or hit.id() != expected:
            raise ValueError(f"Pixel {x},{y} missed expected {expected}")
    images, trials = [], []
    for seed in (17, 31):
        start = time.perf_counter()
        image = np.array(mi.render(scene, spp=args.spp, seed=seed))
        elapsed = time.perf_counter()-start
        if not np.isfinite(image).all() or image.min() < 0:
            raise ValueError("Invalid radiance")
        np.save(args.output / f"seed-{seed}.npy", image)
        trials.append(dict(seed=seed, wall_seconds=elapsed, rgb_f32_sha256=hashlib.sha256(
            image.tobytes()).hexdigest(), lamp=image[150,960].tolist(), exterior=image[500,50].tolist()))
        images.append(image)
    avg = (images[0]+images[1])/2
    full = relative_rms(*images)
    region = relative_rms(*(im[400:650,750:1150] for im in images))
    controls = all(max(abs(v-12) for v in t["lamp"]) <= .12 and t["exterior"] == [0,0,0]
                   for t in trials)
    lin = np.clip(avg * data["camera"]["exposure"], 0, 1)
    enc = np.where(lin <= .0031308, 12.92*lin, 1.055*lin**(1/2.4)-.055)
    Image.fromarray(np.rint(enc*255).astype(np.uint8)).save(args.output / "mean.png")
    report = dict(scene_sha256=hashlib.sha256(raw).hexdigest(), camera=data["camera"],
                  resolution=[1920,1080], spp_per_seed=args.spp, trials=trials, max_depth=-1,
                  rr_depth=5, threads=2, variant=mi.variant(), mitsuba=mi.__version__,
                  python=platform.python_version(), numpy=np.__version__, relative_rms=full,
                  diffuse_region_relative_rms=region, controls_pass=controls,
                  converged=bool(controls and max(full,region)<.02))
    (args.output / "result.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report), flush=True)
    return 0 if controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
