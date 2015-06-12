#!/usr/bin/env python -tt

import numpy
import psffromstack
from scipy.ndimage.interpolation import shift


def gen2dgaussian(amplitude, x_stddev, y_stddev, x_center, y_center, x_size, y_size):
  
  x = numpy.arange(0, x_size, 1)
  y = x[:,numpy.newaxis]
  
  xoff = ((x-x_center)/x_stddev)**2./2.
  yoff = ((y-y_center)/y_stddev)**2./2.
  
  return(amplitude*numpy.exp(-(xoff + yoff)))
  

def testpsfstack():

  amplitude = 1.
  x_stddev = 1.6
  y_stddev = 1.6
  x_center = 8.7
  y_center = 8.7
  x_size = 18
  y_size = 18
  

  kernel = gen2dgaussian(amplitude, x_stddev, y_stddev, x_center, y_center, \
  x_size, y_size)
  
  xlocs = numpy.atleast_1d(8.7)
  ylocs = numpy.atleast_1d(8.7)
  numpixs = numpy.array([9.,9.])

  simple, shift, spline = psffromstack.getstack(xlocs, ylocs, numpixs, kernel)
  
  psffromstack.plotpsffit(shift[:,:,0])

  secondshift = shift(kernel, [1., 1.], mode = 'nearest')

  psffromstack.plotpsffit(secondshift)
