from pathlib import Path
import mitsuba as mi

parent = Path(__file__).parent


scene_dict = {
    "type": "scene",
    "integrator": {"type": "path"},
    "sensor": {
        "type": "perspective",
        "to_world": mi.ScalarTransform4f.look_at(
            origin=[-3.5, 2, 3.5],
            target=[0, 0, 0],
            up=[0, 1, 0],
        ),
        "film": {
            "type": "hdrfilm",
            "width": 512,
            "height": 512,
        },
    },
    "constant_emitter": {
        "type": "constant",
        "radiance": {"type": "rgb", "value": 0.5},
    },
    "point_emitter": {
        "type": "point",
        "position": [-2, 2, 0],
        "intensity": {"type": "rgb", "value": [10, 10, 10]},
    },
    "sphere": {
        "type": "sphere",
        "to_world": mi.ScalarTransform4f.rotate([1, 0, 0], 90),
        "bsdf": {
            "type": "measuredbtf",
            "filename": "UBO2003/UBO_IMPALLA256.zip",
            "to_uv": mi.ScalarTransform4f.scale(5.0),
        },
    },
    "floor": {
        "type": "rectangle",
        "to_world": (mi.ScalarTransform4f.translate([0, -1, 0]) @ mi.ScalarTransform4f.rotate([1, 0, 0], -90) @ mi.ScalarTransform4f.scale(2)),
        "bsdf": {
            "type": "diffuse",
            "reflectance": {
                "type": "checkerboard",
                "to_uv": mi.ScalarTransform4f.scale(5),
            },
        },
    },
}
