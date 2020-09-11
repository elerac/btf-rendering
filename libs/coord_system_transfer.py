import numpy as np

def spherical2orthogonal(r, theta, phi):
    """
    球面座標から直交座標へ変換する．
    thetaとphiの単位は度．
    """
    theta = theta*np.pi/180.0
    phi = phi*np.pi/180.0
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z

def orthogonal2spherical(x, y, z):
    """
    直交座標から球面座標へ変換する．
    thetaとphiの単位は度．
    """
    r = (x**2+y**2+z**2)**0.5
    theta = np.arccos(z/r)
    phi = np.sign(y) * np.arccos(x/(x**2+y**2)**0.5)
    return r, theta*180.0/np.pi, phi*180.0/np.pi
