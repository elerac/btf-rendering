# BTF Rendering

![](documents/cloth_wool.jpg)

## Measured BTF (measuredbtf)
| Parameter | Type | Description | 
| --- | --- | --- |
| filename | string | Filename of the ZIP file to be loaded. |
| apply_inv_gamma | boolean | Whether to apply inverse gamma correction. If the input is the gamma-corrected image, this process should be applied. (Default: true) | 
| to_uv | transform | Specifies an optional 3x3 UV transformation matrix. A 4x4 matrix can also be provided, in which case the extra row and column are ignored. (Default: none) |

| | | 
| :-: | :-: |
| ![](documents/matpreview_impalla.jpg)| ![](documents/matpreview_impalla.jpg) |
| UBO2003 IMPALLA | description |

This custom plugin implements a BTF (Bidirectional Texture Function) for rendering reflections of textures taken in a real scene. The BTF is a set of images with different illumination and viewing directions.

`filename` is the name of the image zip file. This zip file should follow the format of the BTF dataset of University of Bonn.
You can download the [UBO2003](https://cg.cs.uni-bonn.de/en/projects/btfdbb/download/ubo2003/) or [ATRIUM](https://cg.cs.uni-bonn.de/en/projects/btfdbb/download/atrium/) dataset for rendering.

```xml
<bsdf type="measuredbtf">
    <string name="filename" value="UBO_IMPALLA256.zip"/>
    <transform name="to_uv">
        <scale value="5"/>
    </transform>
</bsdf>
```