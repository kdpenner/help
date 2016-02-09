#!/usr/bin/env python -tt

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
import matplotlib.pyplot as plt
import numpy
import sys

def main():

  args = sys.argv[1:]
  
  if not args:
    print 'Usage: positionvalidation prior_catalog_loc blind_catalog_loc sep_arcsec plot_loc'
    sys.exit(1)

  priorfname = args[0]
  blindfname = args[1]
  separation = numpy.int(args[2])
  outfname = args[3]

  prior = Table.read(priorfname)

  blind = Table.read(blindfname, comment = '#', format = 'ascii')

  blindcoords = SkyCoord(ra = blind['ra'], dec = blind['dec'], frame = 'icrs', \
                         unit = 'deg')
  priorcoords = SkyCoord(ra = prior['RA'], dec = prior['Dec'], frame = 'icrs', \
                         unit = 'deg')

  idprior, idblind, dist2, dist3 = blindcoords.search_around_sky(priorcoords, \
                                                            separation*u.arcsec)
  dist2 = dist2.to('arcsec')
  angle_eastofnorth = priorcoords[idprior].position_angle(blindcoords[idblind])

  plt.rcParams['figure.figsize'] = [18.1, 18.1/2.**0.5]

  fig, ax = plt.subplots()

  posscat = ax.quiver(priorcoords[idprior].ra.value, \
                      priorcoords[idprior].dec.value, \
                dist2.value*numpy.cos(numpy.pi/2.-angle_eastofnorth.value), \
                dist2.value*numpy.sin(numpy.pi/2.-angle_eastofnorth.value), \
                dist2.value, angles = 'uv')

  ax.set_xlabel('RA')
  ax.set_ylabel('Dec')
  cbar = plt.colorbar(posscat)

  cbar.set_label('Separation between blind and prior source (arcsec)')

  plt.savefig(outfname)
  plt.close()
  
if __name__ == "__main__":
  main()
