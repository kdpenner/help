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

def goodlocations(img, catradec, fluxarr, halfofsquarewidth):

  xlocs, ylocs, numpixs, imgwcs = translatetopix(catradec, img, halfofsquarewidth)

  mask_inregion = (numpy.round(xlocs) > numpixs[1]) & \
  (numpy.round(xlocs) < img.shape[1]-numpixs[1]) & \
  (numpy.round(ylocs) < img.shape[0]-numpixs[0]) & \
  (numpy.round(ylocs) > numpixs[0])

  xlocs1 = xlocs[mask_inregion]
  ylocs1 = ylocs[mask_inregion]
  fluxarr1 = fluxarr[mask_inregion]

  return xlocs1, ylocs1, fluxarr1, numpixs, imgwcs


def getfluxes(x, y, flux, n_bins, numpixs, img, imgwcs):

  split_x = numpy.array_split(x, n_bins)
  split_y = numpy.array_split(y, n_bins)
  split_flux = numpy.array_split(flux, n_bins)

  fluxes_herschel = numpy.zeros(n_bins)
  fluxes_stack = numpy.zeros(n_bins)

  for i in xrange(n_bins):

    simple, shift, spline = getstack(split_x[i], split_y[i], numpixs, img)

    simplemed, shiftmed, splinemed = psffromstack(simple, shift, spline, 'median')
    
    shiftmedfit = fitpsf(shiftmed)

    try:
      if 'MJy' in img.header['BUNIT']:
        flux = 2.*numpy.pi*shiftmedfit.amplitude_0*shiftmedfit.x_stddev_0*shiftmedfit.y_stddev_0
        flux *= numpy.abs(numpy.prod(imgwcs.wcs.cdelt))
        flux *= 1.e6*u.Jy/u.sr*u.deg*u.deg
        flux = flux.to('mJy')
        mapstr = 'unimap'
    except KeyError:
      flux = 2.*numpy.pi*shiftmedfit.amplitude_0*shiftmedfit.x_stddev_0*shiftmedfit.y_stddev_0
      flux *= u.Jy
      flux = flux.to('mJy')
      mapstr = 'jscan'
    fluxes_herschel[i] = flux.value
    fluxes_stack[i] = numpy.median(split_flux[i])

  return fluxes_herschel, fluxes_stack


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

  flux = cat['Flux_density'].to_array()

  catradec = SkyCoord(cat['RA'], cat['Dec'], unit = (raunit, decunit), frame = 'icrs')

  halfofsquarewidth = 32

  x, y, unmaskflux, numpixs, imgwcs = goodlocations(img, catradec, flux, halfofsquarewidth)

  n_bins = 14
  


  getfluxes(x, y, unmaskflux, n_bins, numpixs, img, imgwcs)
  


  
  plt.rcParams['figure.figsize'] = [18., 18.]






    
    numyplots = numpy.int(numpy.ceil(n_bins/4.)+1)
    
    plt.subplot(numyplots, 4, i+1)
    plt.imshow(shiftmed, origin = 'lower')
    plt.colorbar()

#  print fluxes100

  fig = plt.gcf()
  
  ax = fig.add_subplot(numyplots, 1, numyplots)
  
  ax.plot(fluxes_stack, fluxes_herschel, marker = 'o')

  ax.set_xlabel('Median flux density of priors ('+fluxunitstr+')')
  ax.set_ylabel('Stacked flux density (mJy, '+mapstr+')')

  ax.set_xscale('log')
  ax.set_yscale('log')

  plt.savefig(outfname)

  plt.close()

  
if __name__ == "__main__":
  main()

