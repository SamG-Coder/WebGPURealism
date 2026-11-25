"""Compare opaque, display-encoded RGB8 calibration PNGs (no resampling)."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def read_rgb(path):
    # Pillow can silently downconvert RGB16 PNGs when decoding into RGB mode.
    with open(path, "rb") as stream:
        header = stream.read(29)
    if (header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR"
            or header[24:26] not in (bytes([8, 2]), bytes([8, 6]))):
        raise ValueError(f"{path}: expected truecolour RGB8 or RGBA8 PNG")
    with Image.open(path) as image:
        if image.format != "PNG" or image.mode not in ("RGB", "RGBA"):
            raise ValueError(f"{path}: expected RGB or RGBA PNG")
        if image.mode == "RGBA" and image.getextrema()[3] != (255, 255):
            raise ValueError(f"{path}: expected fully opaque alpha")
        return np.array(image.convert("RGB"))


def compare(reference, capture, spec):
    width, height = spec["size"]
    if reference.shape != (height, width, 3) or reference.shape != capture.shape:
        raise ValueError("Image dimensions must match the frozen profile")
    delta = np.abs(reference.astype(np.int16) - capture.astype(np.int16))
    if not spec["patches"] or not spec["landmarks"]:
        raise ValueError("At least one patch and landmark are required")
    patches = []
    for x, y, w, h in spec["patches"]:
        if not (0 <= x < x+w <= width and 0 <= y < y+h <= height):
            raise ValueError("Patch outside image")
        patches.append(int(delta[y:y+h, x:x+w].max()))

    # Search a short horizontal interval containing a single silhouette edge.
    # Compare its strongest RGB step, rejecting ambiguous or weak matches.
    def edge(image, x0, x1, y):
        if not (0 <= x0 < x1 < width and 0 <= y < height):
            raise ValueError("Landmark outside image")
        steps = np.abs(np.diff(image[y, x0:x1+1].astype(np.int16), axis=0)).max(axis=1)
        hits = np.flatnonzero(steps == steps.max())
        return int(x0 + hits[0] + 1) if len(hits) == 1 and steps.max() >= 16 else None

    edges = []
    for x0, x1, y in spec["landmarks"]:
        expected = edge(reference, x0, x1, y)
        if expected is None:
            raise ValueError("Reference landmark is ambiguous or weak")
        edges.append([expected, edge(capture, x0, x1, y)])

    mae = float(delta.mean())
    result = {"mean_abs_rgb8": mae, "max_abs_rgb8": int(delta.max()),
              "patch_max_abs_rgb8": patches, "landmarks_reference_capture_x": edges,
              "reference_rgb_sha256": hashlib.sha256(reference.tobytes()).hexdigest(),
              "capture_rgb_sha256": hashlib.sha256(capture.tobytes()).hexdigest(),
              "pass": mae <= 0.5 and max(patches) <= 1 and all(a == b for a, b in edges)}
    return result, np.minimum(delta * 8, 255).astype(np.uint8)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("reference", "capture", "profile", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    result, diff = compare(read_rgb(args.reference), read_rgb(args.capture),
                           json.loads(args.profile.read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(diff).save(args.output / "abs-diff-8x.png")
    (args.output / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
