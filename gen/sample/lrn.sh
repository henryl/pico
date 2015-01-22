#!/bin/bash

#
# prepare face samples (from the GENKI dataset)
#

# mkdir -p faces

python preparefacesamplesfromgenki.py $1 faces

#
# prepare non-face samples (background)
#

# mkdir -p nonfaces

python preparebackground.py $2 nonfaces

#
# start the learning process
#

# create an object detector
./picolrn 1 1 6 $1

# append stages
./picolrn $1 $2 $3 1 1e-6 0.980 0.5 1 $1
./picolrn $1 $2 $3 1 1e-6 0.985 0.5 1 $1
./picolrn $1 $2 $3 1 1e-6 0.990 0.5 2 $1
./picolrn $1 $2 $3 1 1e-6 0.995 0.5 3 $1
./picolrn $1 $2 $3 6 1e-6 0.997 0.5 10 $1
./picolrn $1 $2 $3 10 1e-6 0.999 0.5 20 $1
