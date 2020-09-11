"""BTFDBBのzipファイルを展開せずに使用するためのライブラリ。
BTFDBB UBO2003(*)形式, ATRIUM(**)形式のzipファイルを参照し、
・zipファイルに含まれるファイルと角度情報の取得
・「角度のタプル(tl, pl, tv, pv)」から「画像の実体(pillow/PIL形式)」を取得
する関数を提供する。
(*) http://cg.cs.uni-bonn.de/en/projects/btfdbb/download/ubo2003/
(**) http://cg.cs.uni-bonn.de/en/projects/btfdbb/download/atrium/
"""
from typing import Set, Tuple
from zipfile import ZipFile

from PIL import Image

AnglesTuple = Tuple[int, int, int, int]


class BtfFromZip:
    """BTFDBBのzipファイルから角度や画像を取り出す。"""

    def __init__(self, zip_filepath: str) -> None:
        """使用するzipファイルを指定する。"""
        self.zip_filepath = zip_filepath
        self.z = ZipFile(zip_filepath)
        self.filepath_set = self.get_filepath_set()

    def get_filepath_set(self) -> Set[str]:
        """zip内の"jpg"ファイルのファイルパスの集合を取得する。"""
        return {path for path in self.z.namelist()
                if path.endswith(".jpg")}

    def get_angles_set(self) -> Set[AnglesTuple]:
        """zip内の"jpg"ファイル名から角度情報を取得し、intのタプルの集合で返す。"""
        return {self.filename_to_angles(path)
                for path in self.get_filepath_set()}

    def filename_to_angles(self, filename: str) -> AnglesTuple:
        """ファイル名(orパス)から角度(int)のタプル(tl, pl, tv, pv)を取得する。"""
        # ファイルパスの長さの影響を受けないように後ろから数えている
        tl = (int(filename[-25:-22]))
        pl = (int(filename[-19:-16]))
        tv = (int(filename[-13:-10]))
        pv = (int(filename[-7:-4]))
        return (tl, pl, tv, pv)

    def filename_to_image(self, filename: str) -> Image:
        """`filename`が含まれるファイルを探し、その実体をpillow形式で返す。
        `filename`が含まれるファイルが存在しない場合は`ValueError`。
        `filename`が含まれるファイルが複数ある場合は`print`で警告を表示。
        """
        # filepath_listからfilenameが含まれるものを探し、filepathに入れる
        filepaths = [t for t in self.filepath_set
                     if filename in t]
        found_files = len(filepaths)
        if found_files == 0:
            raise ValueError(
                f"'{filename}' does not exist in '{self.zip_filepath}'.")
        elif found_files > 1:
            print("WARN:",
                  f"'{self.zip_filepath}' has {found_files} '{filename}'.")

        return Image.open(self.z.open(filepaths[0]))

    def angles_to_image(self, tl: int, pl: int, tv: int, pv: int) -> Image:
        """`tl`, `pl`, `tv`, `pv`の角度を持つ画像の実体をpillow形式で返す。"""
        filename = f"tl{tl:03} pl{pl:03} tv{tv:03} pv{pv:03}.jpg"
        return self.filename_to_image(filename)

    def filepath_to_X_y(self, filepath: str) -> Tuple[Image, AnglesTuple]:
        """`filepath`にあるファイルの実体(*)と角度情報(**)を返す。
        (*) pillow形式
        (**) それぞれがintの(tl, pl, tv, pv)のタプル
        """
        X = Image.open(self.z.open(filepath))
        y = self.filename_to_angles(filepath)
        return X, y
