import os

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

from pathlib import Path
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from zipfile import ZipFile
from tqdm import tqdm
import numpy as np
import cv2


def parse_keyed_number(text: str, key: str) -> float:
    """Extract a float value following a given key from a text string.

    Parameters
    ----------
    text : str
        The input string to search.
    key : str
        The key to look for.

    Returns
    -------
    float
        The extracted numeric value as a float.

    Examples
    --------
    Extracting a single keyed number:
    >>> parse_keyed_number("user_id123 file_val45 temp10", "id")
    123.0

    Another key:
    >>> parse_keyed_number("user_id123 file_val45 temp10", "val")
    45.0

    Key not present:
    >>> parse_keyed_number("user_id123 file_val45 temp10", "score")
    Traceback (most recent call last):
        ...
    ValueError: No value found for key 'score' in text.

    Multiple matches:
    >>> parse_keyed_number("id123 id456", "id")
    Traceback (most recent call last):
        ...
    ValueError: Multiple values found for key 'id' in text: ['123', '456']
    """
    pattern = rf"{key}(\d+)"
    matches = re.findall(pattern, str(text))
    if len(matches) == 0:
        raise ValueError(f"No value found for key '{key}' in `{text}`.")
    elif len(matches) > 1:
        raise ValueError(f"Multiple values found for key '{key}' in '{text}': {matches}")
    return float(matches[0])


class Ubo2003:
    """Load BTF images and angles from a UBO2003 zip file.

    The zip file is expected to contain images named in the format:
        "UBO2003/MANYFILES/tv030_pv030/00008 tl000 pl000 tv030 pv030.jpg"
    where tl, pl, tv, pv are angles. The images files are recursively searched in the zip.

    The angle values are parsed from the filenames and stored as a list of tuples.

    Examples:
    ---------
    Basic usage.

    >>> btf_data = Ubo2003("UBO2003/UBO_IMPALLA256.zip")
    >>> angles = btf_data.angles
    >>> len(angles)
    6561
    >>> tl, pl, tv, pv = angles[0]
    >>> tl, pl, tv, pv
    (0.0, 0.0, 30.0, 30.0)
    >>> img = btf_data.angle_to_image(tl, pl, tv, pv)
    >>> img.shape
    (256, 256, 3)
    >>> img.dtype
    uint8

    Iterate over all angles, loading images on demand.

    >>> for angle in btf_data.angles:
    ...     img = btf_data.angle_to_image(*angle)
    ...     # process img ang angle...

    Preload all images into memory for faster access.

    >>> btf_data.preload()  # or accessing btf_data.images implicitly triggers preload
    >>> for angle, img in zip(btf_data.angles, btf_data.images):
    ...     # process img ang angle...
    """

    def __init__(self, file_zip: str | Path, preload: bool = False) -> None:
        self.zfile = ZipFile(file_zip)
        self._zip_lock = threading.Lock()  # Lock ensures ZipFile.read is thread-safe during parallel preload

        self.angle_file_dict: dict[tuple[float, float, float, float], str] = {}
        for name in self.zfile.namelist():
            basename = os.path.basename(name)
            ext = os.path.splitext(basename)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".exr", ".hdr"]:
                continue
            tl = parse_keyed_number(basename, "tl")
            pl = parse_keyed_number(basename, "pl")
            tv = parse_keyed_number(basename, "tv")
            pv = parse_keyed_number(basename, "pv")
            angle = (tl, pl, tv, pv)
            self.angle_file_dict[angle] = name

        self._images: Optional[np.ndarray] = None
        if preload:
            self.preload()

    @property
    def angles(self) -> list[tuple[float, float, float, float]]:
        return list(self.angle_file_dict.keys())

    @property
    def files(self) -> list[str]:
        return list(self.angle_file_dict.values())

    @property
    def images(self) -> np.ndarray:
        if self._images is None:
            self.preload()
            return self.images  # recursive call
        else:
            return self._images

    def _read_image(self, filepath: str) -> np.ndarray:
        with self._zip_lock:
            data = self.zfile.read(filepath)  # bytes
        arr = np.frombuffer(data, dtype=np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED | cv2.IMREAD_COLOR_BGR)
        if img_bgr is None:
            raise ValueError(f"Failed to decode image: {filepath}")
        return img_bgr

    def get_image(self, filepath: str) -> np.ndarray:
        if self._images is not None:
            index = self.files.index(filepath)
            return self._images[index]
        else:
            return self._read_image(filepath)

    def angle_to_image(self, tl: float, pl: float, tv: float, pv: float) -> np.ndarray:
        key = (tl, pl, tv, pv)
        file = self.angle_file_dict[key]
        return self.get_image(file)

    def angles_to_image(self, tl: float, pl: float, tv: float, pv: float) -> np.ndarray:
        """Alias for angle_to_image"""
        return self.angle_to_image(tl, pl, tv, pv)

    def preload(self, max_workers: int | None = None, show_progress: bool = False):
        files = list(self.angle_file_dict.values())

        sample_img = self._read_image(files[0])
        h, w, c = sample_img.shape
        self._images = np.empty((len(files), h, w, c), dtype=sample_img.dtype)

        pbar = tqdm(total=len(files), disable=not show_progress, desc="Ubo2003.preload")
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(self._read_image, f): i for i, f in enumerate(files)}
            for fut in as_completed(futures):
                i = futures[fut]
                self._images[i] = fut.result()
                pbar.update(1)
        pbar.close()
