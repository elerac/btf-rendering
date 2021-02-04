"""
BTFDBBを元に．任意角度のBTF画像を補間して返すためのライブラリ．
任意の角度(tl, pl, tv, pv)から，補間したndarray形式の画像を取得．

BTFDBBの読み込みについては，btf-extractor(https://github.com/2-propanol/BTF_extractor)を参照．
"""
import os
import numpy as np
from scipy.spatial import cKDTree
from btf_extractor import Ubo2003, Ubo2014
from .coord_system_transfer import spherical2orthogonal


class BtfInterpolator:
    """
    BTFDBBを元に，任意角度のBTF画像を補間して返す．
    補間は，k近傍のデータから，逆距離加重法(Inverse Distance Weighting)を用いている．
    """
    def __init__(self, filepath, k=4, p=4.0):
        """
        BTFDBBを読み込み，補間器を生成する．
        （読み込みには少し時間がかかります）
        
        Parameters
        ----------
        filepath : str
            BTFDBBのファイルのパス
            拡張子が".zip"の場合は"Ubo2003"
            拡張子が".btf"の場合は"Ubo2014"
        k : int
            補間に用いる近傍点の数
        p : float
            逆距離加重補間の近傍点の影響の強さを決定する
            pは小さいほど近傍点の値の影響が大きくなる

        Methods
        -------
        angles_xy_to_pixel(tl, pl, tv, pv, x, y)
            `tl`, `pl`, `tv`, `pv`の角度条件で`x`，`y`の座標の画像値を補間して返す
        angles_uv_to_pixel(tl, pl, tv, pv, u, v)
            `tl`, `pl`, `tv`, `pv`の角度条件で`u`，`v`の座標の画像値を補間して返す
        angles_to_image(tl, pl, tv, pv)
            `tl`, `pl`, `tv`, `pv`の角度条件の画像値を補間して返す

        Notes
        -----
        光源側の角度は`tl`，`pl`
        観測側の角度は`tv`，`pv`
        """
        self.k = k
        self.p = p
        
        # BTFDBBの読み込み
        root, ext = os.path.splitext(filepath)
        if ext==".zip":
            btf = Ubo2003(filepath)
        elif ext==".btf":
            btf = Ubo2014(filepath)
        else:
            raise Exception("The filepath must have a .zip or .btf extension.")
        
        # 画像のサイズを取得
        angles_list = list(btf.angles_set)
        num = len(angles_list)
        img_dummy = btf.angles_to_image(*angles_list[0])
        height, width, channel = img_dummy.shape
        dtype = img_dummy.dtype
        self.__num = num
        self.__height = height
        self.__width = width

        # すべてのファイルの実態と角度情報を読み込みリストを生成
        self.__images = np.empty((num, height, width, channel), dtype=dtype)
        points = np.empty((num, 6), dtype=np.float32)
        for i, (tl, pl, tv, pv) in enumerate(angles_list):
            # 画像と角度を読み込み
            img_bgr = btf.angles_to_image(tl, pl, tv, pv)
            
            # 角度を球面座標から直交座標へ変換
            xl, yl, zl = spherical2orthogonal(1.0, tl, pl)
            xv, yv, zv = spherical2orthogonal(1.0, tv, pv)
            point = np.array([xl, yl, zl, xv, yv, zv])
            
            # 画像と角度をリストに保存
            self.__images[i] = img_bgr
            points[i] = point
        
        # 角度の情報からKDTreeを構築
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
        `tl`, `pl`, `tv`, `pv`の角度条件で`x`，`y`の座標の画像値を補間して返す
        
        Parameters
        ----------
        tl, pl : array of floats
            光源の方向(tl:theta, pl:phi)
        tv, pv : array of floats
            カメラの方向(tv:theta, pv:phi)
        x, y : array of floatss
            BTFのxy画像座標

        Returns
        -------
        pixel : array of floats
            BTFの画素値
        """ 
        # 角度は球面座標から直交座標へ変換する．
        xl, yl, zl = spherical2orthogonal(1.0, tl, pl)
        xv, yv, zv = spherical2orthogonal(1.0, tv, pv)
        point = np.array([xl, yl, zl, xv, yv, zv]).T
        
        # k近傍探索を実行
        # 距離はl2ノルム
        distance, index = self.__kd_tree.query(point, k=self.k, p=2, workers=-1)
        
        # 対応する角度・xy座標のBTF画像の値を取得
        index = np.clip(index, 0, self.__num-1)
        x = np.expand_dims(np.clip(x, 0, self.__width-1), axis=-1)
        y = np.expand_dims(np.clip(y, 0, self.__height-1), axis=-1)
        btf_values = self.__images[index, y, x]
        
        if self.k==1:
            # 補間なし
            pixel = btf_values
        else:
            # 逆距離加重法による補間
            weights = np.expand_dims( 1/(distance+10**-32)**self.p, axis=-1)
            pixel = np.sum(btf_values * weights, axis=-2) / np.sum(weights, axis=-2)

        return pixel
    
    def angles_uv_to_pixel(self, tl, pl, tv, pv, u, v):
        """
        `tl`, `pl`, `tv`, `pv`の角度条件で`u`，`v`の座標の画像値を補間して返す．

        Parameters
        ----------
        tl, pl : array of floats
            光源の方向(tl:theta, pl:phi)
        tv, pv : array of floats
            カメラの方向(tv:theta, pv:phi)
        u, v : array of floatss
            BTFのuv画像座標

        Returns
        -------
        pixel : array of floats
            BTFの画素値
        """ 
        x, y = self.__uv_to_xy(u, v)
        return self.angles_xy_to_pixel(tl, pl, tv, pv, x, y)

    def angles_to_image(self, tl, pl, tv, pv):
        """
        `tl`, `pl`, `tv`, `pv`の角度条件の画像を補間して返す．

        Parameters
        ----------
        tl, pl : array of floats
            光源の方向(tl:theta, pl:phi)
        tv, pv : array of floats
            カメラの方向(tv:theta, pv:phi)

        Returns
        -------
        image : array of floats
            BTFの画像
        """
        x = np.arange(self.__width)
        y = np.arange(self.__height)
        return self.angles_xy_to_pixel(tl, pl, tv, pv, x, y)
