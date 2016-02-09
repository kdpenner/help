#!/usr/bin/env python -tt

import sys
from astropy.table import Table
import numpy
from astropy import units as u

def cleanwisecat(infname, outfname):

  cat = Table.read(infname)

  mask_goodsrc = (cat['Detection_WISE_W1'] == 1) & \
                 (cat['PhotCase_WISE_W1'] == 1) & \
                 (numpy.char.count(cat['ph_qual'], 'A') > 0)

  cat = cat[mask_goodsrc]
  cat.sort(['F_WISE_W1'])

  minicat = cat[['F_WISE_W1', 'RA', 'Dec']]

  minicat['F_WISE_W1'].unit = u.mJy
  
  minicat['F_WISE_W1'].name = 'Flux_density'

  try:
    minicat.write(outfname)
  except IOError as error:
    print error
  
  return

def main():

  args = sys.argv[1:]
  
  if not args:
    print 'Usage: cleanwisecat catalog_file_loc output_file_loc'
    sys.exit(1)

  catfname = args[0]
  outfname = args[1]

  cleanwisecat(catfname, outfname)
  
if __name__ == "__main__":
  main()
