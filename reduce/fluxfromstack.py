#!/usr/bin/env python -tt

from psffromstack import *
import sys
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy
import matplotlib.pyplot as plt
import math

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

  raunit = cat['RA'].unit
  decunit = cat['Dec'].unit
  fluxunitstr = cat['Flux_density'].unit.to_string()

  cat = cat.as_array()

  n_bins = 14
  
  split_cat = numpy.array_split(cat, n_bins)
  fluxes_herschel = numpy.zeros(n_bins)
  fluxes_stack = numpy.zeros(n_bins)

  halfofsquarewidth = 32
  
  plt.rcParams['figure.figsize'] = [18., 18.]

  for i in xrange(n_bins):
  
    ras = split_cat[i]['RA']
    decs = split_cat[i]['Dec']

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
    fluxes_herschel[i] = flux.value
    fluxes_stack[i] = numpy.median(split_cat[i]['Flux_density'])
    
    numyplots = numpy.int(numpy.ceil(n_bins/4.)+1)
    
    plt.subplot(numyplots, 4, i+1)
    plt.imshow(shiftmed, origin = 'lower')
    plt.colorbar()

#  print fluxes100

  fig = plt.gcf()
  
  ax = fig.add_subplot(numyplots, 1, numyplots)
  
  ax.plot(fluxes_stack, fluxes_herschel, marker = 'o')

  ax.set_xlabel('Median flux density of priors ('+fluxunitstr+')')
  ax.set_ylabel('Stacked flux density (mJy, unimap)')

  ax.set_xscale('log')
  ax.set_yscale('log')

  plt.savefig(outfname)

  plt.close()

  
if __name__ == "__main__":
  main()

