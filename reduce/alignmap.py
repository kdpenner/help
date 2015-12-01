#!/usr/bin/env python -tt

from verify.psffromstack import *
import sys
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord

def main():

  args = sys.argv[1:]
  
  if not args:
    print 'Usage: alignmap [--hipe] img_file_name catalog_file_name output_file_name'
    sys.exit(1)
    
  if args[0] == '--hipe':
    imgfname = args[1]
    file = fits.open(imgfname)
    img = file['wrapped']
    catfname = args[2]
    outfname = args[3]
  else:
    imgfname = args[0]
    file = fits.open(imgfname)
    img = file[0]
    catfname = args[1]
    outfname = args[2]

  cat = Table.read(catfname)

  ra = cat['RA']
  dec = cat['Dec']

  halfofsquarewidth = 32
  
  catradec = SkyCoord(ra, dec, unit = (ra.unit, dec.unit), frame = 'icrs')

  xlocs, ylocs, numpixs, imgwcs = translatetopix(catradec, img, halfofsquarewidth)
  
  mask = (numpy.round(xlocs) > numpixs[1]) & \
  (numpy.round(xlocs) < img.shape[1]-numpixs[1]) & \
  (numpy.round(ylocs) < img.shape[0]-numpixs[0]) & \
  (numpy.round(ylocs) > numpixs[0])
  
  xlocs1 = xlocs[mask]
  ylocs1 = ylocs[mask]

  simple, shift, spline = getstack(xlocs1, ylocs1, numpixs, img)

  simplemed, shiftmed, splinemed = psffromstack(simple, shift, spline, 'median')

  shiftmedfit = fitpsf(shiftmed)

  pixsizes = imgwcs.wcs.cdelt
  if shiftmedfit:
    shifts = (numpixs - numpy.array([shiftmedfit.x_mean_0.value, shiftmedfit.y_mean_0.value]))*pixsizes
  else:
    shifts = numpy.zeros(2)
  pixtypes = imgwcs.wcs.ctype
  pixvals = imgwcs.wcs.crval
  decind = numpy.where(numpy.char.find(pixtypes, 'DEC') != -1)
  raind = numpy.where(numpy.char.find(pixtypes, 'RA') != -1)
  shifts[raind] = shifts[raind]/numpy.cos(pixvals[decind]/180.*numpy.pi)
  numpy.savetxt(outfname, numpy.atleast_2d(shifts), fmt = '%e', \
  header = ' '.join(pixtypes))

if __name__ == "__main__":
  main()
