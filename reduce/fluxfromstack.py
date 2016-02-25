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

def goodindices(img, catradec, halfofsquarewidth):

  xlocs, ylocs, numpixs, imgwcs = translatetopix(catradec, img, halfofsquarewidth)

  mask_inregion = (numpy.round(xlocs) > numpixs[1]) & \
  (numpy.round(xlocs) < img.shape[1]-numpixs[1]) & \
  (numpy.round(ylocs) < img.shape[0]-numpixs[0]) & \
  (numpy.round(ylocs) > numpixs[0])

  return mask_inregion, xlocs, ylocs, numpixs, imgwcs


def getfluxes(xpos, ypos, fluxval, n_bins, numpixs, img, imgwcs):

  split_x = numpy.array_split(xpos, n_bins)
  split_y = numpy.array_split(ypos, n_bins)
  split_flux = numpy.array_split(fluxval, n_bins)

  fluxes_stack = numpy.zeros(n_bins)
  fluxes_catalog = numpy.zeros(n_bins)
  psfs_stack = numpy.zeros((numpixs[0]*2., numpixs[1]*2., n_bins))

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
    fluxes_stack[i] = flux.value
    fluxes_catalog[i] = numpy.median(split_flux[i])
    psfs_stack[:,:,i] = shiftmed

  return fluxes_stack, fluxes_catalog, psfs_stack, mapstr

def plotfluxflux(flux_xaxis, flux_yaxis, img_stacks, n_bins, mapstr, fluxunitstr, outfname):

  plt.rcParams['figure.figsize'] = [18., 18.]

  numyplots = numpy.int(numpy.ceil(n_bins/4.)+1)

  for i in xrange(n_bins):

    plt.subplot(numyplots, 4, i+1)
    plt.imshow(img_stacks[:,:,i], origin = 'lower')
    plt.colorbar()

  fig = plt.gcf()
  
  ax = fig.add_subplot(numyplots, 1, numyplots)
  
  ax.plot(flux_xaxis, flux_yaxis, marker = 'o')

  ax.set_xlabel('Median flux density of priors ('+fluxunitstr+')')
  ax.set_ylabel('Stacked flux density (mJy, '+mapstr+')')

  ax.set_xscale('log')
  ax.set_yscale('log')

  plt.savefig(outfname)

  plt.close()

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

  fluxs = cat['Flux_density'].data

  catradec = SkyCoord(cat['RA'], cat['Dec'], unit = (raunit, decunit), frame = 'icrs')

  halfofsquarewidth = 32

  indices, xs, ys, numpixarr, wcs = goodindices(img, catradec, halfofsquarewidth)

  goodxs = xs[indices]
  goodys = ys[indices]
  goodfluxs = fluxs[indices]

  n_bins = 14
  
  stacked_fluxes, catalog_fluxes, stacks, label = getfluxes(goodxs, goodys, goodfluxs, n_bins, numpixarr, img, wcs)

  plotfluxflux(catalog_fluxes, stacked_fluxes, stacks, n_bins, label, fluxunitstr, outfname)

if __name__ == "__main__":
  main()

