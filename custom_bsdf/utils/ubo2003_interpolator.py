"""
BTFDBBを元に．任意角度のBTF画像を補間して返すためのライブラリ．
任意の角度(tl, pl, tv, pv)から，補間したndarray形式の画像を取得．

BTFDBBの読み込みについては，ubo2003_extractor.pyを参照．
"""
import numpy as np
from scipy.spatial import cKDTree

from .ubo2003_extractor import BtfFromZip
from .coord_system_transfer import spherical2orthogonal

class BtfInterpolator:
    """
    BTFDBBを元に，任意角度のBTF画像を補間して返す．
    """
    def __init__(self, zip_filepath: str, linear_interp=False):
        """
        BTFDBBを読み込み，補間器を生成する．
        （読み込みには少し時間がかかる）

        zip_filepath : str
            BTFDBBのzipファイルのパス

        linear_interp : bool
            線形補間を行うかどうか．デフォルトはFalse．
            Falseの場合，最近傍補間(nearest neighbor)．
            True の場合，線形補間(linear)．
            
            NOTE: 線形補間の場合，計算量・メモリの使用が多い．また，指定の角度が入力データの範囲外だと，nanが返ってくるので使いにくい．詳しくは，scipyのドキュメント参照．
        """
        # すべてのファイルの実態と角度情報を読み込みリストを生成．
        btf_extractor = BtfFromZip(zip_filepath)
        filepath_set = btf_extractor.get_filepath_set()
        Xy = [ btf_extractor.filepath_to_X_y(filepath) for filepath in filepath_set ]
        
        # 読み込んだリストから，画像と角度のリストに分離．
        image_list = [None] * len(Xy)
        xyz_list   = [None] * len(Xy)
        for i, (im, angles) in enumerate(Xy):
            img_bgr = (im[...,::-1]).copy()
            image_list[i]  = img_bgr
            
            # 角度は球面座標から直交座標へ変換する．
            xyz_l = spherical2orthogonal(1.0, angles[0], angles[1])
            xyz_v = spherical2orthogonal(1.0, angles[2], angles[3])
            xyz_list[i] = np.array(xyz_l+xyz_v)
        del Xy
        
        # 補間器を生成
        self.__values = np.array(image_list)
        num, self.__height, self.__width, channel = self.__values.shape
        del image_list
        
        points = np.array(xyz_list)
        del xyz_list
        self.__kd_tree = cKDTree(points)
    
    def __uv_to_xy(self, u, v):
        """uv座標(float)を，BTF画像に対応するxy座標(int)に変換する
        """
        xf = np.mod(u * (self.__width-1), self.__width)
        yf = np.mod(v * (self.__height-1), self.__height)
        x = np.array(xf).astype(np.uint32)
        y = np.array(yf).astype(np.uint32)
        return x, y
        
    def angles_xy_to_pixel(self, tl, pl, tv, pv, x, y):
        """
        `tl`, `pl`, `tv`, `pv`の角度条件で`x`，`y`の座標の画像値を補間して返す．

        tl, pl : float
            光源の方向(tl:theta, pl:phi)

        tv, pv : float
            カメラの方向(tv:theta, pv:phi)

        x, y : float
            BTFのxy画像座標
        """ 
        # 角度は球面座標から直交座標へ変換する．
        xyz_l = spherical2orthogonal(1.0, tl, pl)
        xyz_v = spherical2orthogonal(1.0, tv, pv)
        point = np.array(xyz_l+xyz_v)
        
        # 角度に対応する画像を取得
        k = 4
        distance, index = self.__kd_tree.query(point, k=k)
        
        values = self.__values[index, y, x] # (k, height, width, channel)
        if k==1:
            img_btf = values
        else:
            # Inverse Distance Weighting interpolation
            p = 2.0
            w = 1/(distance+1e-32)**p
            img_btf = np.average(values, axis=0, weights=w)

        return img_btf
    
    def angles_uv_to_pixel(self, tl, pl, tv, pv, u, v):
        """
        `tl`, `pl`, `tv`, `pv`の角度条件で`u`，`v`の座標の画像値を補間して返す．

        tl, pl : float
            光源の方向(tl:theta, pl:phi)

        tv, pv : float
            カメラの方向(tv:theta, pv:phi)

        u, v : float
            BTFのuv画像座標
        """ 
        x, y = self.__uv_to_xy(u, v)
        return self.angles_xy_to_pixel(tl, pl, tv, pv, x, y)

    def angles_to_image(self, tl, pl, tv, pv):
        """
        `tl`, `pl`, `tv`, `pv`の角度条件の画像値を補間して返す．

        tl, pl : float
            光源の方向(tl:theta, pl:phi)

        tv, pv : float
            カメラの方向(tv:theta, pv:phi)
        """
        x = np.arange(self.__width)
        y = np.arange(self.__height)
        return self.angles_xy_to_pixel(tl, pl, tv, pv, x, y)
