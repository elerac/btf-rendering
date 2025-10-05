import numpy as np
import numpy.typing as npt
from scipy.spatial import KDTree


def sph_to_dir(theta, phi):
    st = np.sin(theta)
    x = st * np.cos(phi)
    y = st * np.sin(phi)
    z = np.cos(theta)
    return np.stack([x, y, z], axis=-1)


class BtfInterpolator:
    """Angle-space interpolator for a measured BTF.

    Inputs
    ------
    images : ndarray (N, H, W, C)
        BTF sample images (must all be same resolution & dtype).
    angles : ndarray (N, 4)
        (tl, pl, tv, pv) in degrees for each image.
          tl, pl : light polar / azimuth (theta_l, phi_l)
          tv, pv : view  polar / azimuth (theta_v, phi_v)
    k : int
        Number of nearest angular samples used for interpolation.
    p : float
        Inverse distance weighting power. p=2 typical. k=1 disables weighting.
    """

    def __init__(self, images: npt.ArrayLike, angles: npt.ArrayLike, k: int = 4, p: float = 4.0):
        # images and angles validation
        images = np.asarray(images)
        angles = np.asarray(angles)
        if images.ndim != 4:
            raise ValueError("images must have shape (N,H,W,C).")
        if angles.ndim != 2 or angles.shape[1] != 4:
            raise ValueError("angles must have shape (N,4).")
        if images.shape[0] != angles.shape[0]:
            raise ValueError("images and angles batch dimension mismatch.")
        self.images = images
        self.angles = angles.astype(np.float32)
        self._N, self._H, self._W, self._C = images.shape

        # Precompute 6D points (xl, yl, zl, xv, yv, zv)
        self._points6 = np.empty((self._N, 6), dtype=np.float32)
        for i, (tl, pl, tv, pv) in enumerate(self.angles):
            wl = sph_to_dir(np.radians(tl), np.radians(pl))
            wv = sph_to_dir(np.radians(tv), np.radians(pv))
            self._points6[i] = np.concatenate([wl, wv], axis=-1)

        self._tree = KDTree(self._points6)

        self.k = max(1, int(k))
        self.p = float(p)

    def __call__(self, wi, wr, uv):
        # wi (..., 3) light directions
        # wr (..., 3) view directions
        # uv (..., 2) texture coordinates
        wi = np.asarray(wi, dtype=np.float32)
        wr = np.asarray(wr, dtype=np.float32)
        uv = np.asarray(uv, dtype=np.float32)

        # k-NN search for each (wi, wr) pair
        point = np.concatenate([wi, wr], axis=-1)
        distance, index = self._tree.query(point, k=self.k, p=2, workers=-1)
        distance = distance.astype(np.float32)

        if self.k == 1:  # keep dims
            distance = distance[..., np.newaxis]
            index = index[..., np.newaxis]

        # uv to xy
        u, v = uv[..., 0], uv[..., 1]
        x = np.clip(np.mod(u * (self._W - 1), (self._W)).astype(np.uint32), 0, self._W - 1)[..., np.newaxis]
        y = np.clip(np.mod(v * (self._H - 1), (self._H)).astype(np.uint32), 0, self._H - 1)[..., np.newaxis]

        # Gather pixel values
        values = self.images[index, y, x].astype(np.float32)

        # Weighted average with inverse distance weights
        weights = 1 / (distance + 1e-16) ** self.p
        weights = weights[..., np.newaxis]
        pixel = np.sum(values * weights, axis=-2) / np.sum(weights, axis=-2)

        return pixel
