from herschel.ia.numeric import Bool3d
from herschel.ia.toolbox.util import SimpleFitsWriterTask
from herschel.ia.toolbox.image import ImageSubtractTask
from herschel.pacs.spg.phot import PhotProjectTask
from herschel.pacs.cal.all import getCalTree
from getpointcol import getpointcol
from findprobsforscantimes import findprobsforscantimes
simpleFitsWriter = SimpleFitsWriterTask()
imageSubtract = ImageSubtractTask()
photProject = PhotProjectTask()

def makelowpmap(obs, probthresh):

  """Makes 3 very simple maps

  Use this routine to inspect maps from a division of the data by pointing
  probability.  Three maps are made: one for data with a pointing prob >
  probthresh; one for data with a pointing prob < probthresh; and a difference
  map (> probthresh minus < probthresh).  Dark spots in the difference map are
  sources which appear only in the bad prob map.

  Inputs:
  obs -- an observation context
  probthresh -- the probability threshold.  Applied to gyroAttProbY and
  gyroAttProbZ with 'or' logic.

  Outputs:
  3 maps in the working directory.
  """


  frame = obs.level1.refs['HPPAVGB'].product.refs[0].product
  
  caltree = getCalTree(obs = obs)

  scantimes = frame['Status']['FINETIME'].data

  probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', \
                      'gyroAttProbY', 'gyroAttProbZ')

  scandict = findprobsforscantimes(scantimes, probs)

  numtimesteps = len(scandict['obt'])

  # masked pixels have a mask value of True
  onlybadprobs = Bool3d(32, 64, numtimesteps, True)
  onlygoodprobs = Bool3d(32, 64, numtimesteps, False)

  for i in xrange(numtimesteps):
    if scandict['gyroAttProbY'][i] < probthresh or \
    scandict['gyroAttProbZ'][i] < probthresh:
      onlybadprobs[:,:,i] = False
      onlygoodprobs[:,:,i] = True

  frame.addMaskType('badprobs', 'only the bad pointing probs')
  frame.setMask('badprobs', onlybadprobs)
  
  for eachmask in frame.activeMaskNames:
    if eachmask != 'badprobs':
      frame.mask.setActive(eachmask, False)

  print 'Making a map with only the following masks:', frame.activeMaskNames

  mapbadprobs, mi = photProject(frame, copy = 1, calTree = caltree)

  frame.addMaskType('goodprobs', 'only the good pointing probs')
  frame.setMask('goodprobs', onlygoodprobs)
  
  for eachmask in frame.activeMaskNames:
    if eachmask != 'goodprobs':
      frame.mask.setActive(eachmask, False)

  print 'Making a map with only the following masks:', frame.activeMaskNames

  mapgoodprobs, mi = photProject(frame, copy = 1, calTree = caltree)

  diffmap = imageSubtract(image1 = mapgoodprobs, image2 = mapbadprobs, ref = 1)

  strobsid = str(obs.obsid)

  simpleFitsWriter(product = mapbadprobs, \
                   file = 'badprobmap'+strobsid+'.fits')
  print 'Wrote output file badprobmap'+strobsid+'.fits'
  simpleFitsWriter(product = mapgoodprobs, \
                   file = 'goodprobmap'+strobsid+'.fits')
  print 'Wrote output file goodprobmap'+strobsid+'.fits'
  simpleFitsWriter(product = diffmap, \
                   file = 'good-minus-bad-map'+strobsid+'.fits')
  print 'Wrote output file good-minus-bad-map'+strobsid+'.fits'

  return