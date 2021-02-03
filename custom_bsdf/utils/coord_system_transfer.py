import numpy as np

def spherical2orthogonal(r, theta, phi):
    """
    球面座標から直交座標へ変換する．
    thetaとphiの単位は度．
    """
    theta = np.deg2rad(theta)
    phi = np.deg2rad(phi)
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z

def orthogonal2spherical(x, y, z):
    """
    直交座標から球面座標へ変換する．
    thetaとphiの単位は度．
    """
    r = np.sqrt(x*x+y*y+z*z)
    theta = np.arccos(z/r)
    x_for_arccos = x / (np.sqrt(x*x+y*y) + 10**-32)
    phi = np.sign(y) * np.arccos( np.clip(x_for_arccos, -1, 1) )
    return r, np.rad2deg(theta), np.rad2deg(phi)

def mirror_uv(uv):
    """
    UV座標の境界が反転するように変換

    Parameters
    ----------
    uv : np.ndarray
      変換前のUV座標
    
    Returns
    -------
    uv_mirror : np.ndarray
      変換後のUV座標

    Notes
    -----
    変換前 -> 変換後
    0.0 -> 0.0
    0.1 -> 0.1
    0.9 -> 0.9
    1.1 -> 1.9
    1.9 -> 1.1
    2.1 -> 2.1
    2.9 -> 2.9
    3.1 -> 3.9
    3.9 -> 3.1
    4.1 -> 4.1
    """
    uv_int = np.floor(uv)
    mask_to_mirror = np.mod(uv_int, 2)
    uv_mirror = np.where(mask_to_mirror, 1 - uv + 2*uv_int, uv)
    return uv_mirror
