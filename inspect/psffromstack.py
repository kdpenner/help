#!/usr/bin/env python -tt

from astropy.table import Table
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import numpy
from matplotlib import pyplot as plt
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage.interpolation import shift
from astropy.modeling import models, fitting
from os.path import expanduser

def translatetopix(catradec, imgfile, extent_arcsec):

  file = fits.open(imgfile)
  
  img = file[0]

  imgwcs = WCS(img.header)

  xlocs, ylocs = catradec.to_pixel(imgwcs, origin = 0)
  
  xlocs, ylocs = numpy.atleast_1d(xlocs, ylocs)

  pixsizes = abs(imgwcs.wcs.cdelt)*3600.

  numpixs = numpy.ceil(extent_arcsec/pixsizes)
  
  return xlocs, ylocs, numpixs, img


def getstack(xlocs, ylocs, numpixs, img):
  
  xgrids = numpy.round(xlocs)
  ygrids = numpy.round(ylocs)

#  xlocs += 0.5
#  ylocs += 0.5

  dimstack = numpy.append(2*numpixs, xlocs.size)

  extracts = numpy.zeros(dimstack)
  extracts_shift = numpy.zeros(dimstack)
  extracts_bispline = numpy.zeros(dimstack)

  for i in xrange(xlocs.size):
  
    if img.data[ylocs[i]+.5, xlocs[i]+.5] == img.data[ygrids[i], xgrids[i]]:

      extract = img.data[ygrids[i]-numpixs[0]:ygrids[i]+numpixs[0], \
      xgrids[i]-numpixs[1]:xgrids[i]+numpixs[1]]

      x = numpy.arange(2*numpixs[0])
      y = numpy.arange(2*numpixs[1])

      f = RectBivariateSpline(x, y, extract)

      ynew = numpy.arange(ylocs[i]-ygrids[i], ylocs[i]-ygrids[i]+2*numpixs[0], 1)
      xnew = numpy.arange(xlocs[i]-xgrids[i], xlocs[i]-xgrids[i]+2*numpixs[1], 1)

#    obsgrid = numpy.mgrid[0:2*numpixs[0]:1, 0:2*numpixs[1]:1]

#    wantgrid = numpy.mgrid[ylocs[i]-ygrids[i]:(ylocs[i]-ygrids[i]+2*numpixs[0]):1, \
#    xlocs[i]-xgrids[i]:(xlocs[i]-xgrids[i]+2*numpixs[1]):1]

      result1 = shift(extract, [ygrids[i]-ylocs[i], xgrids[i]-xlocs[i]], \
      mode = 'nearest')
      result2 = f(ynew, xnew)
      
      extracts[:,:,i] = extract
      extracts_shift[:,:,i] = result1
      extracts_bispline[:,:,i] = result2
      
    else:
    
      print 'Error'
      raise

  return extracts, extracts_shift, extracts_bispline

def psffromstack(catradec, imgfile, extent_arcsec):

  xlocs, ylocs, numpixs, img = translatetopix(catradec, imgfile, extent_arcsec)

  simple, shift, spline = getstack(xlocs, ylocs, numpixs, img)
  
  psfsimpleavg = numpy.average(simple, axis = 2)
  psfsimplemed = numpy.median(simple, axis = 2)
  psfshiftmed = numpy.median(shift, axis = 2)
  psfsplinemed = numpy.median(spline, axis = 2)
  
  return psfsimpleavg, psfsimplemed, psfshiftmed, psfsplinemed
  
def plotpsf(psfsimpleavg, psfsimplemed, psfshiftmed, psfsplinemed):
  
  psfmax = numpy.max(psfsimpleavg)
  psfmin = numpy.min(psfsimpleavg)
  
  plt.subplot(221)
  plt.imshow(psfsimpleavg, vmin = psfmin, vmax = psfmax, origin = 'lower')
  plt.colorbar()
  plt.subplot(222)
  plt.imshow(psfsimplemed, vmin = psfmin, vmax = psfmax, origin = 'lower')
  plt.colorbar()
  plt.subplot(223)
  plt.imshow(psfshiftmed, vmin = psfmin, vmax = psfmax, origin = 'lower')
  plt.colorbar()
  plt.subplot(224)
  plt.imshow(psfsplinemed, vmin = psfmin, vmax = psfmax, origin = 'lower')
  plt.colorbar()
  plt.gcf().set_size_inches(17, 17)
  plt.show()
  
  return
  
def fitpsf(psf, *center):

  fixed = {}
  bounds = {}

  if not center:
  
    amplitude = psf.max()
    y_center, x_center = numpy.unravel_index(psf.argmax(), psf.shape)
    fixed['x_mean'] = False
    fixed['y_mean'] = False
    bounds['x_stddev'] = [0., psf.shape[1]]
    bounds['y_stddev'] = [0., psf.shape[0]]
    
  else:
  
    amplitude = psf[center[1], center[0]]
    x_center = center[0]
    y_center = center[1]
    fixed['x_mean'] = True
    fixed['y_mean'] = True
    bounds['x_stddev'] = [0., psf.shape[1]]
    bounds['y_stddev'] = [0., psf.shape[0]]


  x_stddev = 3./2.35
  y_stddev = 3./2.35
  theta = 0
  
  p_init = models.Gaussian2D(amplitude = amplitude, x_mean = x_center, \
  y_mean = y_center, x_stddev = x_stddev, y_stddev = y_stddev, \
  theta = theta, fixed = fixed, bounds = bounds)
  
  fit_p = fitting.LevMarLSQFitter()
  
  gridy, gridx = numpy.mgrid[0:psf.shape[0]:1, 0:psf.shape[1]:1]
  
  p = fit_p(p_init, gridx, gridy, psf)
  
  return p
  
def plotpsffit(psf, fit = None):

  gridy, gridx = numpy.mgrid[0:psf.shape[0]:1, 0:psf.shape[1]:1]

  if not fit:
    p = fitpsf(psf)
  else:
    p = fit
  
  for outparam in p.param_names:
    print outparam, '{0:.4f}'.format(getattr(p, outparam).value)

  psfmin = psf.min()
  psfmax = psf.max()

  plt.subplot(221)
  plt.imshow(psf, vmin = psfmin, vmax = psfmax, origin = 'lower')
  plt.colorbar()
  plt.subplot(222)
  plt.imshow(p(gridx, gridy), vmin = psfmin, vmax = psfmax, origin = 'lower')
  plt.colorbar()
  plt.subplot(223)
  plt.imshow(psf - p(gridx, gridy), origin = 'lower')
  plt.colorbar()
  plt.show()
  
#  plt.plot(psf[9, :], 'ro')
#  plt.plot(p(gridx, gridy)[9, :], 'k--')
#  plt.show()
  
#  plt.plot(psf[9, :] - p(gridx, gridy)[9, :], 'ro')
#  plt.show()
  
  return
  
def main():

  home = expanduser('~')

  catfname = home+'/Documents/validatemap/xmmlss/xmmlss_wp4_mips24_may2015.fits'
  
  cat = Table.read(catfname)
  
  ra = cat['RA']
  dec = cat['Dec']
  
  catradec = SkyCoord(ra, dec, unit = (ra.unit, dec.unit), frame = 'icrs')
  
#  catradec = catradec[20026]

  imgfname = home+'/Documents/validatemap/xmmlss/'+\
  'HerMES_PACS_level6_XMM_LSS_SWIRE_100um_EdoIbar_Unimap_img_wgls.fits'

  simpleavg, simplemed, shiftmed, splinemed = psffromstack(catradec, imgfname, 18)
  plotpsf(simpleavg, simplemed, shiftmed, splinemed)
  plotpsffit(simplemed)
  plotpsffit(shiftmed)
  plotpsffit(splinemed)

if __name__ == "__main__":
  main()
