#!/usr/bin/env python -tt

from psffromstack import *
import sys
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy

def main():

  args = sys.argv[1:]
  
  if not args:
    print 'Usage: fluxfromstack img_file_loc catalog_file_loc plot_loc'
    sys.exit(1)

  imgfname = args[0]
  file = fits.open(imgfname)
  img = file[0]
  catfname = args[1]
  outfname = args[2]

  cat = Table.read(catfname)

  mask_goodsrc = (cat['Detection_WISE_W1'] == 1) & (cat['PhotCase_WISE_W1'] == 1) & \
  (numpy.char.count(cat['ph_qual'], 'A') > 0)

  cat = cat[mask_goodsrc]
  cat.sort(['F_WISE_W1'])
  raunit = cat['RA'].unit
  decunit = cat['Dec'].unit

  minicat = cat[['F_WISE_W1', 'RA', 'Dec']].as_array()

  n_bins = 8
  
  split_minicat = numpy.array_split(minicat, n_bins)
  fluxes100 = numpy.zeros(n_bins)

  halfofsquarewidth = 32
  
  for i in xrange(n_bins):
  
    ras = split_minicat[i]['RA']
    decs = split_minicat[i]['Dec']

    catradec = SkyCoord(ras, decs, unit = (raunit, decunit), frame = 'icrs')

    xlocs, ylocs, numpixs, imgwcs = translatetopix(catradec, img, halfofsquarewidth)

    # I will remove sources outside the image region.  This will reduce the
    # number of sources in this bin.  If we want equal numbers of sources in
    # each bin we will have to change our approach.
    
    mask_inregion = (numpy.round(xlocs) > numpixs[1]) & \
    (numpy.round(xlocs) < img.shape[1]-numpixs[1]) & \
    (numpy.round(ylocs) < img.shape[0]-numpixs[0]) & \
    (numpy.round(ylocs) > numpixs[0])
  
    xlocs1 = xlocs[mask_inregion]
    ylocs1 = ylocs[mask_inregion]

    simple, shift, spline = getstack(xlocs1, ylocs1, numpixs, img)

    simplemed, shiftmed, splinemed = psffromstack(simple, shift, spline, 'median')
    
    shiftmedfit = fitpsf(shiftmed)

    flux = 2.*numpy.pi*shiftmedfit.amplitude_0*shiftmedfit.x_stddev_0*shiftmedfit.y_stddev_0
    flux *= numpy.abs(numpy.prod(imgwcs.wcs.cdelt))
    if 'MJy' in img.header['BUNIT']:
      flux *= 1.e6*u.Jy/u.sr*u.deg*u.deg
      flux = flux.to('mJy')
    fluxes100[i] = flux.value
    
  print fluxes100
  
if __name__ == "__main__":
  main()

