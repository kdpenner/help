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
from pdb import set_trace

def translatetopix(catradec, imgfile, extent_arcsec):

  file = fits.open(imgfile)
  
  try:
    img = file['image']
  except KeyError:
    try:
      img = file['wrapped']
    except KeyError:
      img = file[0]

  try:
    imgwcs = WCS(img.header)
  except AttributeError:
    raise

  xlocs, ylocs = catradec.to_pixel(imgwcs, origin = 0)
  
  xlocs, ylocs = numpy.atleast_1d(xlocs, ylocs)

  pixsizes = abs(imgwcs.wcs.cdelt)*3600.

  numpixs = numpy.ceil(extent_arcsec/pixsizes)
  
  return xlocs, ylocs, numpixs, img


def getstack(xlocs, ylocs, numpixs, img):
  
  xlocs = numpy.atleast_1d(xlocs)
  ylocs = numpy.atleast_1d(ylocs)
  
  xgrids = numpy.round(xlocs)
  ygrids = numpy.round(ylocs)

#  xlocs += 0.5
#  ylocs += 0.5

  dimstack = numpy.append(2*numpixs, xlocs.size)

  extracts = numpy.zeros(dimstack)
  extracts_shift = numpy.zeros(dimstack)
  extracts_bispline = numpy.zeros(dimstack)

  for i in xrange(xlocs.size):
  
    try:

      extract = img.data[ygrids[i]-numpixs[0]:ygrids[i]+numpixs[0], \
      xgrids[i]-numpixs[1]:xgrids[i]+numpixs[1]]
      
      if not numpy.isnan(extract.sum()):
        

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
      
        extracts[:,:,i] = numpy.nan
        extracts_shift[:,:,i] = numpy.nan
        extracts_bispline[:,:,i] = numpy.nan
      
    except:
    
      print 'Error'
      raise

  return extracts, extracts_shift, extracts_bispline

def psffromstack(simple, shift, spline, method):

  if method == 'mean':
    psfsimple = numpy.nanmean(simple, axis = 2)
    psfshift = numpy.nanmean(shift, axis = 2)
    psfspline = numpy.nanmean(spline, axis = 2)
  elif method == 'median':
    psfsimple = numpy.nanmedian(simple, axis = 2)
    psfshift = numpy.nanmedian(shift, axis = 2)
    psfspline = numpy.nanmedian(spline, axis = 2)
    
  return psfsimple, psfshift, psfspline
  
def plotpsf(*psfs):
  
  numpsfs = len(psfs)
  
  psfmax = numpy.max(psfs[0])
  psfmin = numpy.min(psfs[0])
  
  ndim = numpy.int(numpy.ceil(numpy.sqrt(numpsfs)))
  
  if numpsfs % ndim == 0:
    ndims = [numpsfs/ndim, ndim]
  else:
    ndims = [ndim, ndim]
  
  for i in xrange(0, numpsfs):
    plt.subplot(ndims[0], ndims[1], i+1)
    plt.imshow(psfs[i], vmin = psfmin, vmax = psfmax, origin = 'lower')
    plt.colorbar()

  plt.gcf().set_size_inches(ndims[0]*8.5, ndims[1]*8.5)
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
  
  p_const_init = models.Const2D(amplitude = 0.)
  
  fit_p = fitting.LevMarLSQFitter()
  
  gridy, gridx = numpy.mgrid[0:psf.shape[0]:1, 0:psf.shape[1]:1]
  
  p = fit_p(p_init+p_const_init, gridx, gridy, psf)
  
  if not numpy.any(fit_p.fit_info['param_cov']):
    p = None
  
  return p
  
def plotpsffit(psf, fit = None):

  gridy, gridx = numpy.mgrid[0:psf.shape[0]:1, 0:psf.shape[1]:1]

  if not fit:
    p = fitpsf(psf)
  else:
    p = fit
  
  try:

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
    
  except:
    pass

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

#  cat = Table.read(home+'/Documents/validatemap/xmmlss/mymap/run1/hipe_daophot_buildpsf', \
#  comment = '#', format = 'ascii')
  
  ra = cat['RA']
  dec = cat['Dec']

#  ra = cat['ra']
#  dec = cat['dec']
  
  catradec = SkyCoord(ra, dec, unit = (ra.unit, dec.unit), frame = 'icrs')

#  catradec = SkyCoord(ra, dec, unit = 'deg', frame = 'icrs')
  
#  catradec = catradec[20026]

#  imgfname = home+'/Documents/validatemap/xmmlss/'+\
#  'mymap/run1/img_gls.fits'

#  imgfname = home+'/Documents/validatemap/xmmlss/'+\
#  'HerMES_PACS_level4_UDS_100um_EdoIbar_Unimap_img_wgls.fits'

  imgfname = home+'/Documents/removetest/gls_gooddata_gyro.fits'

#  imgfname = home+'/Documents/psffromstacktest/simimg.fits'

#  imgfname = home+'/Documents/correctscans/scan1.fits'

  xlocs, ylocs, numpixs, img = translatetopix(catradec, imgfname, 32)
  
  mask = (numpy.round(xlocs) > numpixs[1]) & \
  (numpy.round(xlocs) < img.shape[1]-numpixs[1]) & \
  (numpy.round(ylocs) < img.shape[0]-numpixs[0]) & \
  (numpy.round(ylocs) > numpixs[0])
  
  xlocs1 = xlocs[mask]
  ylocs1 = ylocs[mask]

  simple, shift, spline = getstack(xlocs1, ylocs1, numpixs, img)

  simplemed, shiftmed, splinemed = psffromstack(simple, shift, spline, 'median')
  simpleavg, shiftavg, splineavg = psffromstack(simple, shift, spline, 'mean')
  plotpsf(simplemed, shiftmed, splinemed, simpleavg, shiftavg, splineavg)
  print 'PSF fit: simplemed'
  plotpsffit(simplemed)
  print 'PSF fit: shiftmed'
  shiftmedfit = fitpsf(shiftmed)
  
#  shiftmedfit.amplitude_0 = 1./2./numpy.pi/shiftmedfit.x_stddev_0/shiftmedfit.y_stddev_0
#  gridy, gridx = numpy.mgrid[0:19:1, 0:19:1]
#  shiftmedfit.x_mean_0 = 9.
#  shiftmedfit.y_mean_0 = 9.
#  shiftmedfit.amplitude_1 = 0.
#  writepsf = shiftmedfit(gridx, gridy)
#  hdu = fits.PrimaryHDU(writepsf)
#  hdu.writeto('shiftmedpsf.fits')
  
  plotpsffit(shiftmed, fit = shiftmedfit)
  print 'PSF fit: splinemed'
  plotpsffit(splinemed)
  print 'PSF fit: simpleavg'
  plotpsffit(simpleavg)

#  set_trace()

if __name__ == "__main__":
  main()
