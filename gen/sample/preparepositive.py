#!/usr/bin/env python

import os
import sys

import argparse
import math
import struct
import random
import numpy
from PIL import Image
from PIL import ImageOps

try:
    import matplotlib.pyplot
    import matplotlib.image
    import matplotlib.cm
except ImportError:
    pass

PLOT = False # To plot or not to plot images via matplotlib (debugging)

MAXWSIZE = 192.0 # Maximum image "window" size

NRANDS = 14 # Number of samples to generate

MININPUTSIZE = 15

if PLOT:
    fig = matplotlib.pyplot.figure()
    matplotlib.pyplot.show(block=False)

    
def saveasrid(im, path):
    # Raw Intensity Data
    # File format:
    #       - a 32-bit signed integer w (image width)
    #       - a 32-bit signed integer h (image height)
    #       - an array of w*h unsigned bytes representing pixel intensities

    h = im.shape[0]
    w = im.shape[1]

    #
    f = open(path, 'wb')

    #
    data = struct.pack('ii', w, h)
    f.write(data)

    tmp = [None]*w*h
    for y in range(0, h):
        for x in range(0, w):
            tmp[y*w + x] = im[y, x]

    #
    data = struct.pack('%sB' % w*h, *tmp)
    f.write(data)

    #
    f.close()

#
def export(im, r, c, s, folder, id, ofile):
    nrows = im.shape[0]
    ncols = im.shape[1]

    # crop a slightly larger area because we will be generating
    # multiple samples from a base image by perturbing pos / scale
    r0 = max(int(r - 0.75*s), 0); r1 = min(r + 0.75*s, nrows)
    c0 = max(int(c - 0.75*s), 0); c1 = min(c + 0.75*s, ncols)

    im = im[r0:r1, c0:c1]

    nrows = im.shape[0]
    ncols = im.shape[1]

    r = r - r0
    c = c - c0

    maxwsize = MAXWSIZE
    wsize = max(nrows, ncols)

    ratio = maxwsize/wsize

    if ratio<1.0:
        # window size is larger than maximum. resize down.
        im = numpy.asarray( Image.fromarray(im).resize((int(ratio*ncols), int(ratio*nrows))) )

        r = ratio*r
        c = ratio*c
        s = ratio*s

    # Output list file format per object is
    # L1: [filename].rid
    # L2:     [numofsamples]
    # L3+:    [rows] [cols] [size]
    
    # Number of samples to generate
    nrands = NRANDS
    
    # L1
    ofile.write(id + '.rid\n')
    
    # L2
    ofile.write('\t%d\n' % nrands)
    
    for i in range(0, nrands):
        stmp = s*random.uniform(0.9, 1.1)

        rtmp = r + s*random.uniform(-0.05, 0.05)
        ctmp = c + s*random.uniform(-0.05, 0.05)

        if PLOT:
            matplotlib.pyplot.cla()

            matplotlib.pyplot.plot([ctmp-stmp/2, ctmp+stmp/2], [rtmp-stmp/2, rtmp-stmp/2], 'b', linewidth=3)
            matplotlib.pyplot.plot([ctmp+stmp/2, ctmp+stmp/2], [rtmp-stmp/2, rtmp+stmp/2], 'b', linewidth=3)
            matplotlib.pyplot.plot([ctmp+stmp/2, ctmp-stmp/2], [rtmp+stmp/2, rtmp+stmp/2], 'b', linewidth=3)
            matplotlib.pyplot.plot([ctmp-stmp/2, ctmp-stmp/2], [rtmp+stmp/2, rtmp-stmp/2], 'b', linewidth=3)

            matplotlib.pyplot.imshow(im, cmap=matplotlib.cm.Greys_r)

            matplotlib.pyplot.draw()

            response = raw_input('Press Enter to continue...')
        # L3+
        ofile.write('\t%d %d %d\n' % (int(rtmp), int(ctmp), int(stmp)))
        
    ofile.write('\n')
    ofile.flush()

    saveasrid(im, os.path.join(folder, id + '.rid'))


def exportmirrored(im, r, c, s, folder, id, list):
    #
    # exploit mirror symmetry of the face
    #

    # flip image
    im = numpy.asarray(ImageOps.mirror(Image.fromarray(im)))

    # flip column coordinate of the object
    c = im.shape[1] - c

    # export
    export(im, r, c, s, folder, id, list)


def prepare():
    parser = argparse.ArgumentParser()
    parser.add_argument('imagesfile', help='input image list')
    parser.add_argument('srcfolder', help='input folder')
    parser.add_argument('dstfolder', help='output folder, destination')
    parser.add_argument('--minroll', help='min roll', type=float, default=-22.0)
    parser.add_argument('--maxroll', help='max roll', type=float, default=22.0)
    parser.add_argument('--minpitch', help='min pitch', type=float, default=-22.0)
    parser.add_argument('--maxpitch', help='max pitch', type=float, default=22.0)
    parser.add_argument('--minyaw', help='min yaw', type=float, default=-22.0)
    parser.add_argument('--maxyaw', help='max yaw', type=float, default=22.0)
    parser.add_argument('--flipyaw', help='flip yaw', action='store_true')
    args = parser.parse_args()
    
    imagesfile = args.imagesfile
    srcfolder = args.srcfolder
    dstfolder = args.dstfolder
    
    minrollrads = args.minroll / 180 * math.pi
    maxrollrads = args.maxroll / 180 * math.pi
    minpitchrads = args.minpitch / 180 * math.pi
    maxpitchrads = args.maxpitch / 180 * math.pi
    minyawrads = args.minyaw / 180 * math.pi
    maxyawrads = args.maxyaw / 180 * math.pi

    flipyaw = args.flipyaw

    if flipyaw:
        assert minyawrads >= 0 and maxyawrads >= 0

    # images file is a tab delimited file with the following format:
    #     <filepath, x, y, w, h, roll, pitch, yaw>
    # where roll, pitch, yaw are in radians.

    # IMPORTANT: This script only works if w == h

    # create destination folder, if needed
    if not os.path.exists(dstfolder):
       os.makedirs(dstfolder)

    imlist = open(imagesfile, 'r').readlines()
    imlist_len = len(imlist)
    n = 0

    ofile = open(os.path.join(dstfolder, 'list.txt'), 'w')
    
    for i in range(0, imlist_len):
        filepath, x, y, w, h, rollrads, pitchrads, yawrads = imlist[i].split('\t')
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        rollrads = float(rollrads)
        pitchrads = float(pitchrads)
        yawrads = float(yawrads)
        nyawrads = abs(yawrads) if flipyaw else yawrads
        
        assert w == h
        
        if (w > MININPUTSIZE and h > MININPUTSIZE
                and minrollrads < rollrads < maxrollrads
                and minpitchrads < pitchrads < maxpitchrads
                and minyawrads < nyawrads < maxyawrads):

            try:
                im = Image.open(os.path.join(srcfolder, filepath)).convert('L')
            except:
                print("ERROR: Could not open %s" % filepath)
                continue

            im = numpy.asarray(im)

            imh = im.shape[0]
            imw = im.shape[1]
            
            if flipyaw and yawrads < 0:
                didflip = True
                im = numpy.asarray(ImageOps.mirror(Image.fromarray(im)))
                c = imw - (x + 0.5 * w)
            else:
                didflip = False
                c = x + 0.5 * w
                
            r = y + 0.5 * h
            s = w
            
            oid = 'face%d' % n
            export(im, r, c, s, dstfolder, oid, ofile)
            n += 1

            if not flipyaw:
                oid = 'face%d' % n
                exportmirrored(im, r, c, s, dstfolder, oid, ofile)
                n += 1

            if flipyaw:
                manip = "flipyaw" if didflip else "I"
            else:
                manip = "mirror"
                
            sys.stdout.write("%d of %d - %s (%s) \r" % (i + 1, imlist_len, filepath, manip))
            sys.stdout.flush()

    print "DONE"
    ofile.flush()
    ofile.close()

if __name__ == "__main__":
    prepare()
    
            
    

    

    
