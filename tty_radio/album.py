from __future__ import print_function
import platform
PY3 = False
if platform.python_version().startswith('3'):
    PY3 = True
from bisect import bisect
from io import BytesIO
from random import choice
if PY3:
    from urllib.request import urlopen, URLError
else:
    from urllib2 import urlopen, URLError
PYPILLOW = True
try:
    from PIL import Image
except ImportError:
    PYPILLOW = False
    print("Hey-o, you don't have image manipulation libs installed:")
    print("  pip install pillow")


def gen_art(url, term_w, term_h):
    # Creates an ascii art image from an arbitrary image
    # orig author: Steven Kay 7 Sep 2009
    # mod by x0rion Feb 2014
    # print("Printing ASCII Art for " + url)
    if not PYPILLOW:
        return

    # greyscale.. the following strings represent
    # 7 tonal ranges, from lighter to darker.
    # for a given pixel tonal level, choose a character
    # at random from that range.
    greyscale = [" ",
                 " ",
                 "-",      # ".,-",
                 "=~+*",   # "_ivc=!/|\\~",
                 "[]()",   # "gjez2]/(YL)t[+T7Vf",
                 "mdbwz",  # "mdK4ZGbNDXY5P*Q",
                 "WKMA",
                 "#@$&"    # "#%$"
                 ]

    # using the bisect class to put luminosity values
    # in various ranges.
    # these are the luminosity cut-off points for each
    # of the 7 tonal levels. At the moment, these are 7 bands
    # of even width, but they could be changed to boost
    # contrast or change gamma, for example.

    zonebounds = [36, 72, 108, 144, 180, 216, 252]

    # open image and resize
    try:
        image = urlopen(url).read()
    except URLError:
        print("Warning: couldn't retrieve file" + url)
        return

    im = Image.open(BytesIO(image))
    w, h = im.size

    im_height = term_h//2
    im_width = 2 * int((w / h) * im_height)
    # factor 2 is due to the fact that ascii characters are roughtly twice as
    # high as they are wide
    if im_width > term_w - 2:
        im_height = int(im_height * (term_w - 2) / im_width)
        im_width = int(im_width * (term_w - 2) / im_width)
    if im_width < 20 or im_height < 20:
        # tiny images look bad, so we just skip them
        return ''

    # experiment with aspect ratios according to font
    #   w , h
    # im=im.resize((160, 75),Image.BILINEAR)
    im = im.resize((im_width, im_height), Image.BILINEAR)
    im = im.convert("L")  # convert to mono

    # now, work our way over the pixels
    # build up str
    str_ = ""
    for y in range(0, im.size[1]):
        for x in range(0, im.size[0]):
            lum = 255 - im.getpixel((x, y))
            row = bisect(zonebounds, lum)
            str_ = str_ + choice(greyscale[row])
        if y != (im.size[1] - 1):
            str_ = str_ + "\n"
    return str_
