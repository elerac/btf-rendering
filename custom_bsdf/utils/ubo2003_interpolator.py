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
    補間は，k近傍のデータから，逆距離加重法(Inverse Distance Weighting)を用いている．
    """
    def __init__(self, zip_filepath, k=4, p=2.0):
        """
        BTFDBBを読み込み，補間器を生成する．
        （読み込みには少し時間がかかります）
        
        Parameters
        ----------
        zip_filepath : str
            BTFDBBのzipファイルのパス
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
        
        # zipファイルからのBTFDBBの読み込み
        btf_extractor = BtfFromZip(zip_filepath)
        
        # すべてのファイルの実態と角度情報を読み込みリストを生成
        image_list = []
        point_list   = []
        for filepath in btf_extractor.get_filepath_set():
            # 画像と角度を読み込み
            img_rgb, angles = btf_extractor.filepath_to_X_y(filepath)
            
            # 画像をRGBからBGRに変換
            img_bgr = img_rgb[...,::-1].copy()
            
            # 角度を球面座標から直交座標へ変換
            tl, pl, tv, pv = angles
            xl, yl, zl = spherical2orthogonal(1.0, tl, pl)
            xv, yv, zv = spherical2orthogonal(1.0, tv, pv)
            point = np.array([xl, yl, zl, xv, yv, zv])
            
            # 画像と角度をリストに保存
            image_list.append(img_bgr)
            point_list.append(point)
        
        # BTF全画像
        self.__images = np.array(image_list)

        # 画像のサイズを取得
        num, height, width, channel = self.__images.shape
        self.__height = height
        self.__width = width
        
        # 角度の情報からKDTreeを構築
        points = np.array(point_list)
        self.__kd_tree = cKDTree(points)
        
        del image_list, point_list
    
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
        point = np.array([xl, yl, zl, xv, yv, zv])
        
        # k近傍探索を実行
        # 距離はl2ノルム
        distance, index = self.__kd_tree.query(point, k=self.k, p=2)
        
        # 対応する角度・xy座標のBTF画像の値を取得
        btf_values = self.__images[index, y, x] # (k, height, width, channel)
        
        if self.k==1:
            # 補間なし
            pixel = btf_values
        else:
            # 逆距離加重法による補間
            weights = 1/(distance+1e-32)**self.p
            pixel = np.average(btf_values, axis=0, weights=weights)

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
