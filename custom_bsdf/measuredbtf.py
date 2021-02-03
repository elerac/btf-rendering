import numpy as np
from .utils.btf_interpolator import BtfInterpolator
from .utils.coord_system_transfer import orthogonal2spherical

import enoki as ek
from mitsuba.core import Bitmap, Struct, Thread, math, Properties, Frame3f, Float, Vector3f, warp, Transform3f
from mitsuba.render import BSDF, BSDFContext, BSDFFlags, BSDFSample3f, SurfaceInteraction3f, register_bsdf, Texture

class MeasuredBTF(BSDF):
    def __init__(self, props):
        BSDF.__init__(self, props)
        
        # BTDFFのzipファイルのパス
        self.m_filename = props["filename"]
        
        # 逆ガンマ補正をかけるかどうか
        if props.has_property("apply_inv_gamma"):
            self.m_apply_inv_gamma = props["apply_inv_gamma"]
        else:
            self.m_apply_inv_gamma = True

        # 反射率
        if props.has_property("reflectance"):
            self.m_reflectance = Float(props["reflectance"])
        else:
            self.m_reflectance = Float(1.0)

        # Power parameter
        if props.has_property("power_parameter"):
            self.m_power_parameter = Float(props["power_parameter"])
        else:
            self.m_power_parameter = Float(4.0)

        # UVマップの変換
        self.m_transform = Transform3f(props["to_uv"].extract())
        
        # 読み込んだBTF
        self.btf = BtfInterpolator(self.m_filename, p=self.m_power_parameter)
        
        self.m_flags = BSDFFlags.DiffuseReflection | BSDFFlags.FrontSide
        self.m_components = [self.m_flags]

    def get_btf(self, wi, wo, uv):
        """
        BTFの生の値を取得する

        wi : enoki.scalar.Vector3f
            Incident direction
        
        wo : enoki.scalar.Vector3f
            Outgoing direction

        uv : enoki.scalar.Vector2f 
            UV surface coordinates
        """
        # カメラ側の方向
        _, tv, pv = orthogonal2spherical(*wi)
        
        # 光源側の方向
        _, tl, pl = orthogonal2spherical(*wo)
        
        # 画像中の座標位置を求める
        u, v = self.m_transform.transform_point(uv)
        
        # BTFの画素値を取得
        bgr = self.btf.angles_uv_to_pixel(tl, pl, tv, pv, u, v)
        
        # 0.0~1.0にスケーリング
        bgr = np.clip(bgr / 255.0 * self.m_reflectance, 0, 1)
        
        # 逆ガンマ補正をかける
        if self.m_apply_inv_gamma:
            bgr **= 2.2

        return Vector3f(bgr[..., ::-1])

    def sample(self, ctx, si, sample1, sample2, active):
        """
        BSDF sampling
        """
        cos_theta_i = Frame3f.cos_theta(si.wi)

        active &= cos_theta_i > 0

        bs = BSDFSample3f()
        bs.wo  = warp.square_to_cosine_hemisphere(sample2)
        bs.pdf = warp.square_to_cosine_hemisphere_pdf(bs.wo)
        bs.eta = 1.0
        bs.sampled_type = +BSDFFlags.DiffuseReflection
        bs.sampled_component = 0

        value = self.get_btf(si.wi, bs.wo, si.uv) / Frame3f.cos_theta(bs.wo)

        return ( bs, ek.select(active & (bs.pdf > 0.0), value, Vector3f(0)) )

    def eval(self, ctx, si, wo, active):
        """
        Emitter sampling
        """
        if not ctx.is_enabled(BSDFFlags.DiffuseReflection):
            return Vector3f(0)

        cos_theta_i = Frame3f.cos_theta(si.wi) 
        cos_theta_o = Frame3f.cos_theta(wo)

        value = self.get_btf(si.wi, wo, si.uv) * math.InvPi

        return ek.select((cos_theta_i > 0.0) & (cos_theta_o > 0.0), value, Vector3f(0))

    def pdf(self, ctx, si, wo, active):
        if not ctx.is_enabled(BSDFFlags.DiffuseReflection):
            return Vector3f(0)

        cos_theta_i = Frame3f.cos_theta(si.wi)
        cos_theta_o = Frame3f.cos_theta(wo)

        pdf = warp.square_to_cosine_hemisphere_pdf(wo)

        return ek.select((cos_theta_i > 0.0) & (cos_theta_o > 0.0), pdf, 0.0)
