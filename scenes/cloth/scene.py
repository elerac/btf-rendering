from pathlib import Path
import mitsuba as mi

parent = Path(__file__).parent


scene_dict = {
    "type": "scene",
    "integrator": {"type": "path"},
    "sensor": {
        "type": "perspective",
        "sampler": {"type": "independent", "sample_count": 1},
        "to_world": mi.ScalarTransform4f.look_at(
            origin=[5.3, 3.0, 5.6],
            target=[0.0, 0.2, 1.2],
            up=[0, 1, 0],
        ),
        "film": {
            "type": "hdrfilm",
            "width": 480,
            "height": 270,
        },
    },
    "envmap": {
        "type": "envmap",
        "filename": f"{parent}/skylit_garage_1k.hdr",
    },
    "cloth": {
        "type": "obj",
        "filename": f"{parent}/cloth.obj",
        "bsdf": {
            "type": "twosided",
            "bsdf": {
                "type": "measuredbtf",
                "filename": "UBO2003/UBO_WOOL256.zip",
                "to_uv": mi.ScalarTransform4f.scale(5.0),
            },
        },
    },
    "ground": {
        "type": "rectangle",
        "to_world": (mi.ScalarTransform4f.rotate([1, 0, 0], -90) @ mi.ScalarTransform4f.scale(5)),
    },
}
