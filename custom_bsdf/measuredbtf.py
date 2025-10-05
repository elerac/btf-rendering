import numpy as np
import mitsuba as mi
import drjit as dr

from .microfacet_sampling import MicrofacetSampling

from .btf_interpolator import BtfInterpolator
from .ubo2003 import Ubo2003


class MeasuredBTF(MicrofacetSampling):
    def __init__(self, props: mi.Properties) -> None:
        super().__init__(props)

        self.m_filename: str = props["filename"]  # Path to the BTF file
        self.m_scale: float = props.get("scale", 1.0)  # Scale factor for reflectance
        self.m_p: float = props.get("p", 4.0)  # Power parameter
        self.m_k: int = props.get("k", 4)  # Number of nearest neighbors
        self.m_gamma: float = props.get("gamma", 2.2)  # Gamma correction

        to_uv = props.get("to_uv", mi.ScalarTransform4f())
        self.m_transform = mi.Transform3f(to_uv.extract().matrix)

        ubo = Ubo2003(self.m_filename)
        images = ubo.images
        angles = ubo.angles
        self.btf_interp = BtfInterpolator(images, angles)

    def eval(self, ctx: mi.BSDFContext, si: mi.SurfaceInteraction3f, wo: mi.Vector3f, active: mi.Mask) -> mi.Spectrum:
        cos_theta_i = mi.Frame3f.cos_theta(si.wi)
        cos_theta_o = mi.Frame3f.cos_theta(wo)
        active &= (cos_theta_i > 0.0) & (cos_theta_o > 0.0)

        if (dr.none(active)) or (not ctx.is_enabled(mi.BSDFFlags.GlossyReflection)):
            return 0.0

        uv = self.m_transform.transform_affine(si.uv)

        # Convert to numpy arrays for BTF lookup
        wl = np.asarray(wo).T  # (N, 3)
        wv = np.asarray(si.wi).T  # (N, 3)
        uv = np.asarray(uv).T  # (N, 2)
        bgr = self.btf_interp(wl, wv, uv)

        bgr *= self.m_scale / 255.0  # scale
        bgr **= self.m_gamma  # inverse gamma correction
        rgb = bgr[..., ::-1]  # BGR -> RGB

        value = mi.Color3f(rgb.T) * dr.inv_pi

        return mi.depolarizer(value) & active
