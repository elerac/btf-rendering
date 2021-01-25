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
