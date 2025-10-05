from pathlib import Path
import mitsuba as mi

parent = Path(__file__).parent


scene_dict = {
    "type": "scene",
    "integrator": {"type": "path"},
    "sensor": {
        "type": "perspective",
        "id": "camera",
        "fov_axis": "smaller",
        "focus_distance": 6.0,
        "fov": 28.8415,
        "to_world": mi.ScalarTransform4f.look_at(
            target=[3.04072, -2.85176, 2.80939],
            origin=[3.69558, -3.46243, 3.25463],
            up=[-0.317366, 0.312466, 0.895346],
        ),
        "sampler": {"type": "independent", "sample_count": 1},
        "film": {
            "type": "hdrfilm",
            "id": "film",
            "width": 960,
            "height": 720,
            "pixel_format": "rgb",
            "rfilter": {"type": "gaussian"},
        },
    },
    "emitter-envmap": {
        "type": "envmap",
        "id": "emitter-envmap",
        "filename": f"{parent}/envmap.exr",
        "to_world": (
            mi.ScalarTransform4f(
                [
                    [-0.224951, -0.000001, -0.974370, 0.0],
                    [-0.974370, 0.000000, 0.224951, 0.0],
                    [0.000000, 1.000000, -0.000001, 8.870000],
                    [0.000000, 0.000000, 0.000000, 1.000000],
                ]
            )
            @ mi.ScalarTransform4f.rotate([0, 1, 0], -180)
        ),
        "scale": 3.0,
    },
    "bsdf-diffuse": {
        "type": "diffuse",
        "id": "bsdf-diffuse",
        "reflectance": {"type": "rgb", "value": [0.18, 0.18, 0.18]},
    },
    "texture-checkerboard": {
        "type": "checkerboard",
        "id": "texture-checkerboard",
        "color0": {"type": "rgb", "value": [0.4, 0.4, 0.4]},
        "color1": {"type": "rgb", "value": [0.2, 0.2, 0.2]},
        "to_uv": mi.ScalarTransform4f.scale([8.0, 8.0, 1.0]),
    },
    "bsdf-plane": {
        "type": "diffuse",
        "id": "bsdf-plane",
        "reflectance": {"type": "ref", "id": "texture-checkerboard"},
    },
    "bsdf-matpreview": {
        "type": "measuredbtf",
        "id": "bsdf-matpreview",
        "filename": "UBO2003/UBO_IMPALLA256.zip",
        "to_uv": mi.ScalarTransform4f.scale(5.0),
    },
    "shape-plane": {
        "type": "serialized",
        "id": "shape-plane",
        "filename": f"{parent}/matpreview.serialized",
        "shape_index": 0,
        "to_world": (
            mi.ScalarTransform4f(
                [
                    [3.38818, -4.06354, 0.0, -1.74958],
                    [4.06354, 3.38818, 0.0, 1.43683],
                    [0.0, 0.0, 5.29076, -0.0120714],
                    [0.0, 0.0, 0.0, 1.0],
                ]
            )
            @ mi.ScalarTransform4f.rotate([0, 0, 1], -4.3)
        ),
        "bsdf": {"type": "ref", "id": "bsdf-plane"},
    },
    "shape-matpreview-interior": {
        "type": "serialized",
        "id": "shape-matpreview-interior",
        "filename": f"{parent}/matpreview.serialized",
        "shape_index": 1,
        "to_world": mi.ScalarTransform4f(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0252155],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
        "bsdf": {"type": "ref", "id": "bsdf-diffuse"},
    },
    "shape-matpreview-exterior": {
        "type": "serialized",
        "id": "shape-matpreview-exterior",
        "filename": f"{parent}/matpreview.serialized",
        "shape_index": 2,
        "to_world": (
            mi.ScalarTransform4f.translate([0, 0, 0.01])
            @ mi.ScalarTransform4f(
                [
                    [0.614046, 0.614047, 0.0, -1.78814e-07],
                    [-0.614047, 0.614046, 0.0, 2.08616e-07],
                    [0.0, 0.0, 0.868393, 1.02569],
                    [0.0, 0.0, 0.0, 1.0],
                ]
            )
        ),
        "bsdf": {"type": "ref", "id": "bsdf-matpreview"},
    },
}
