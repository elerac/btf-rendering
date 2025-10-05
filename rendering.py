import time
from tqdm import tqdm
import numpy as np
import mitsuba as mi

mi.set_variant("llvm_ad_rgb")

from custom_bsdf.measuredbtf import MeasuredBTF

mi.register_bsdf("measuredbtf", lambda props: MeasuredBTF(props))


# Scene to render

# from scenes.cloth.scene import scene_dict
# from scenes.matpreview.scene import scene_dict
from scenes.simple_sphere.scene import scene_dict

# Edit here to change the scene or the BTF dataset
# scene_dict["sphere"]["bsdf"]["filename"] = "UBO2003/UBO_IMPALLA256.zip"
# scene_dict["bsdf-matpreview"]["filename"] = "ATRIUM/CEILING.zip"
# scene_dict["bsdf-matpreview"]["scale"] = 0.6


def main():
    spp = 16
    sample_per_pass = 16
    if spp % sample_per_pass != 0:
        raise ValueError("spp must be a multiple of sample_per_pass")

    print("Loading scene...")
    scene = mi.load_dict(scene_dict)

    print(f"Starting rendering with {spp} spp...")
    start_time = time.time()
    if sample_per_pass > spp:
        img = mi.render(scene, spp=spp)
    else:
        # Rendering with the measured BTF tends to use a lot of memory,
        # so splitting the rendering into several passes and averaging the results.
        images = []
        for i in tqdm(range(spp // sample_per_pass)):
            img = mi.render(scene, seed=i, spp=sample_per_pass)
            images.append(img)
        img = mi.Bitmap(np.mean(images, axis=0))

    print(f"Rendering finished in {(time.time() - start_time) / 60:.2f} min.")

    mi.util.write_bitmap("output.jpg", img)


if __name__ == "__main__":
    main()
