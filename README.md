# BTF Rendering
Custom plugin in Python to render measured BTF (Bidirectional Texture Function)  with Mitsuba 2.

![](documents/cloth_wool.jpg)

## Usage
1. Clone and compile [Mitsuba 2](https://github.com/mitsuba-renderer/mitsuba2). Check whether you can `import mitsuba` in python.
2. Clone this repository and move it there.
```bash
git clone https://github.com/elerac/btf-rendering.git
cd btf-rendering
```
3. Download [UBO2003 BTF Dataset](https://cg.cs.uni-bonn.de/en/projects/btfdbb/download/ubo2003/). Make directory named `UBO2003/` and save the data under there. OR, you can run [download_large_data.py](https://github.com/elerac/btf-rendering/blob/master/download_large_data.py) and the data will download automatically.  
Have you placed BTF Dataset as shown below?
```
.
├── UBO2003
│   ├── UBO_IMPALLA256.zip
│   ├── ...
├── custom_bsdf
├── download_large_data.py
├── rendering.py
├── scenes
├── ...
```
4. Run [rendering.py](https://github.com/elerac/btf-rendering/blob/master/rendering.py) and get [rendered image using BTF](https://github.com/elerac/btf-rendering/blob/master/documents/simple_sphere.jpg).

## Measured BTF (*measuredbtf*)
| Parameter | Type | Description | 
| :-- | :-- | :-- |
| filename | string | Filename of the ZIP file to be loaded. |
| reflectance| rgb | Adjust the reflectance of the BTF. (Default: 1.0) |
| apply_inv_gamma | boolean | Whether to apply inverse gamma correction. If the input is the gamma-corrected image, this process should be applied. (Default: *true*) | 
| power_parameter | float | Determine the smoothness of the interpolation. The smaller the value, the smoother it is. (Default: 2.0) |
| to_uv | transform | Specifies an optional 3x3 UV transformation matrix. A 4x4 matrix can also be provided, in which case the extra row and column are ignored. (Default: none) |

| | | 
| :-: | :-: |
| ![](documents/matpreview_impalla.jpg)| ![](documents/matpreview_corduroy.jpg) |
| UBO2003 IMPALLA | UBO2003 CORDUROY |

This custom plugin implements a BTF for rendering reflections of textures taken in a real scene. The BTF is a set of images with different illumination and viewing directions.

`filename` is the name of the image zip file. This zip file should follow the format of the BTF dataset of University of Bonn. It is a set of image files with the naming composition like *WoolPKNT256_00084_tl015_pl000_tv015_pv120.jpg*.
Download the [UBO2003](https://cg.cs.uni-bonn.de/en/projects/btfdbb/download/ubo2003/) or [ATRIUM](https://cg.cs.uni-bonn.de/en/projects/btfdbb/download/atrium/) dataset for rendering.

```xml
<bsdf type="measuredbtf">
    <string name="filename" value="UBO_IMPALLA256.zip"/>
    <transform name="to_uv">
        <scale value="5"/>
    </transform>
</bsdf>
```

### Warning
In the `scalar_rgb` variant, the execution of this plugin is **extremely slow**. Thus, using the `gpu_rgb` variant is recommended.