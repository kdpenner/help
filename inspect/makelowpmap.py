from herschel.ia.toolbox.util import SimpleFitsWriterTask
simpleFitsWriter = SimpleFitsWriterTask()

def makelowpmap(obs, probthresh):

  """Makes 3 very simple maps

  Use this routine to inspect maps from a division of the data by pointing
  probability.  Three maps are made: one for data with a pointing prob >
  probthresh; one for data with a pointing prob < probthres; and a difference
  map (> probthresh minus < probthresh).

  Inputs:
  obs -- an observation context
  probthresh -- the probability threshold.  Applied to gyroAttProbY and
  gyroAttProbZ with 'or' logic.

  Outputs:
  3 maps in the working directory.
  """


  frame = obs.level1.refs['HPPAVGB'].product.refs[0].product

  scantimes = frame['Status']['FINETIME'].data

  probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', \
                      'gyroAttProbY', 'gyroAttProbZ')

  scandict = findprobsforscantimes(scantimes, probs)

  # masked pixels have a mask value of True
  onlybadprobs = Bool3d(32, 64, len(scandict['obt']), True)
  onlygoodprobs = Bool3d(32, 64, len(scandict['obt']), False)

  for i in xrange(len(scandict['obt'])):
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

  mapbadprobs, mi = photProject(frame, copy = 1)

  frame.addMaskType('goodprobs', 'only the good pointing probs')
  frame.setMask('goodprobs', onlygoodprobs)
  
  for eachmask in frame.activeMaskNames:
    if eachmask != 'goodprobs':
      frame.mask.setActive(eachmask, False)

  print 'Making a map with only the following masks:', frame.activeMaskNames

  mapgoodprobs, mi = photProject(frame, copy = 1)

  diffmap = imageSubtract(image1 = mapbadprobs, image2 = mapgoodprobs, ref = 1)

  strobsid = str(obs.obsid)

  simpleFitsWriter(product = mapbadprobs, \
                   file = 'badprobmap'+strobsid+'.fits')
  print 'Wrote output file badprobmap'+strobsid+'.fits'
  simpleFitsWriter(product = mapgoodprobs, \
                   file = 'goodprobmap'+strobsid+'.fits')
  print 'Wrote output file goodprobmap'+strobsid+'.fits'
  simpleFitsWriter(product = diffmap, \
                   file = 'bad-minus-good-map'+strobsid+'.fits')
  print 'Wrote output file bad-minus-good-map'+strobsid+'.fits'

  return