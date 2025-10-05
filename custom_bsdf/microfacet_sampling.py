import mitsuba as mi
import drjit as dr

# Magic:
# Prevent RuntimeError: drjit.custom(<mitsuba.python.util._RenderOp>): error while performing a custom differentiable operation.
# https://github.com/mitsuba-renderer/mitsuba3/discussions/586#discussioncomment-5300468
dr.set_flag(dr.JitFlag.LoopRecord, False)
dr.set_flag(dr.JitFlag.VCallRecord, False)


class MicrofacetSampling(mi.BSDF):
    """Custom BSDF plugin to apply a sampling routine from the GGX Microfacet model.

    This class is designed to be used by inheriting it and overriding the `eval()` method.
    By default, `eval()` is implemented as a diffuse reflection, but can be changed as needed.

    This class is implemented based on measured_polarized plugin in Mitsuba3.
    """

    def __init__(self, props: mi.Properties) -> None:
        super().__init__(props)

        self.m_flags = mi.BSDFFlags.GlossyReflection | mi.BSDFFlags.FrontSide
        self.m_components = [self.m_flags]

        self.m_alpha_sample = props.get("alpha_sample", 0.1)

        # Set the weight for cosine hemisphere sampling in relation to GGX sampling.
        # Set to 1.0 in order to fully fall back to cosine sampling.
        self.COSINE_HEMISPHERE_PDF_WEIGHT = 0.1

    def sample(self, ctx: mi.BSDFContext, si: mi.SurfaceInteraction3f, sample1: mi.Float, sample2: mi.Point2f, active: mi.Mask) -> tuple[mi.BSDFSample3f, mi.Spectrum]:
        cos_theta_i = mi.Frame3f.cos_theta(si.wi)
        active &= cos_theta_i > 0.0

        bs = dr.zeros(mi.BSDFSample3f)
        if dr.none(active) | (not ctx.is_enabled(mi.BSDFFlags.GlossyReflection)):
            return bs, 0.0

        distr = mi.MicrofacetDistribution(mi.MicrofacetType.GGX, self.m_alpha_sample, self.m_alpha_sample, True)

        lobe_pdf_diffuse = self.COSINE_HEMISPHERE_PDF_WEIGHT
        sample_diffuse = active & (sample1 < lobe_pdf_diffuse)
        sample_microfacet = active & (~sample_diffuse)

        wo_diffuse = mi.warp.square_to_cosine_hemisphere(sample2)
        m, unused = distr.sample(si.wi, sample2)
        wo_microfacet = mi.reflect(si.wi, m)

        bs.wo[sample_diffuse] = wo_diffuse
        bs.wo[sample_microfacet] = wo_microfacet

        bs.pdf = self.pdf(ctx, si, bs.wo, active)

        bs.sampled_component = 0
        bs.sampled_type = +mi.BSDFFlags.GlossyReflection
        bs.eta = 1.0

        value = self.eval(ctx, si, bs.wo, active)
        return bs, dr.select(active & (bs.pdf > 0.0), value / bs.pdf, 0.0)

    def eval(self, ctx: mi.BSDFContext, si: mi.SurfaceInteraction3f, wo: mi.Vector3f, active: mi.Mask) -> mi.Spectrum:
        cos_theta_i = mi.Frame3f.cos_theta(si.wi)
        cos_theta_o = mi.Frame3f.cos_theta(wo)
        active &= (cos_theta_i > 0.0) & (cos_theta_o > 0.0)

        if (dr.none(active)) or (not ctx.is_enabled(mi.BSDFFlags.GlossyReflection)):
            return 0.0

        value = mi.Color3f(0.2, 0.25, 0.7) * dr.inv_pi * cos_theta_o

        return mi.depolarizer(value) & active

    def pdf(self, ctx: mi.BSDFContext, si: mi.SurfaceInteraction3f, wo: mi.Vector3f, active: mi.Mask) -> mi.Float:
        if dr.none(active) or (not ctx.is_enabled(mi.BSDFFlags.GlossyReflection)):
            return 0.0

        cos_theta_i = mi.Frame3f.cos_theta(si.wi)
        cos_theta_o = mi.Frame3f.cos_theta(wo)

        distr = mi.MicrofacetDistribution(mi.MicrofacetType.GGX, self.m_alpha_sample, self.m_alpha_sample, True)
        H = dr.normalize(wo + si.wi)

        pdf_diffuse = mi.warp.square_to_cosine_hemisphere_pdf(wo)
        pdf_microfacet = distr.pdf(si.wi, H) / (4.0 * dr.dot(wo, H))

        pdf = 0
        pdf += pdf_diffuse * self.COSINE_HEMISPHERE_PDF_WEIGHT
        pdf += pdf_microfacet * (1.0 - self.COSINE_HEMISPHERE_PDF_WEIGHT)

        return dr.select((cos_theta_i > 0.0) & (cos_theta_o > 0.0), pdf, 0.0)

    def eval_pdf(self, ctx: mi.BSDFContext, si: mi.SurfaceInteraction3f, wo: mi.Vector3f, active: mi.Mask) -> tuple[mi.Spectrum, mi.Float]:
        return self.eval(ctx, si, wo, active), self.pdf(ctx, si, wo, active)

    def to_string(self) -> str:
        return f"MicrofacetSampling[\n  alpha_sample = {self.m_alpha_sample},\n]"
