import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, default="scenes/simple_sphere/simple_sphere.xml", help="Input scene filepath (.xml)")
parser.add_argument("-o", "--output", type=str, default="rendered.jpg", help="Output image filepath (.jpg, .png)")
parser.add_argument("-m", "--mode", type=str, default="scalar_rgb", help="Rendering mode (scalar_rgb or gpu_rgb)")
args = parser.parse_args()

import mitsuba
mitsuba.set_variant(args.mode)
from mitsuba.core import Bitmap, Struct, Thread
from mitsuba.core.xml import load_file
from mitsuba.render import register_bsdf

from custom_bsdf.measuredbtf import MeasuredBTF

def main():
    # Register MeasuredBTF
    register_bsdf('measuredbtf', lambda props: MeasuredBTF(props))
    
    # Filename
    filename_src = args.input
    filename_dst = args.output

    # Load an XML file
    Thread.thread().file_resolver().append(os.path.dirname(filename_src))
    scene = load_file(filename_src)

    # Rendering
    scene.integrator().render(scene, scene.sensors()[0])

    # Save image
    film = scene.sensors()[0].film()
    bmp = film.bitmap(raw=True)
    bmp.convert(Bitmap.PixelFormat.RGB, Struct.Type.UInt8, srgb_gamma=True).write(filename_dst)

if __name__=="__main__":
    main()
