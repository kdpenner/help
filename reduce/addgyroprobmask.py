from herschel.ia.numeric.toolbox.basic import GammaP
from herschel.ia.numeric.toolbox.basic import Log
from herschel.ia.numeric import Bool3d
from herschel.ia.numeric import Double1d
from herschel.ia.numeric import String1d
from herschel.pacs.spg.pipeline.SaveProductToObservationContext import *
from help.inspect import getpointcol
from herschel.ia.toolbox.util.jython import saveObservation
from bisect import bisect_left

def addgyroprobmask(obs, camera, probthresh = 1.e-4):

  poolname = obs.level0.getCamera(camera).averaged.product.refs[0].urn.split(':')[1]

  level1 = PacsContext(obs.level1)

  frames = level1.averaged.getCamera(camera).product.getScience(0)

  if not frames.containsMask('badprobs'):
  
    scantimes = frames['Status']['FINETIME'].data

    numscans = len(scantimes)

    startscan = scantimes[0]
    stopscan = scantimes[-1]

    probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', \
                        'gyroAttProbY', 'gyroAttProbZ')

    numtimes = len(probs['obt'])

    # masked pixels have a mask value of True
    onlygoodprobs = Bool3d(32, 64, numscans, False)

    for i in xrange(numtimes-1):
      for key in probs.iterkeys():
        # if the probabilities are equal to 0.0 the log below returns Infinity
        if key is not 'obt':
          if probs[key][i] == 0.:
            probs[key][i] = 1e-16
          if probs[key][i+1] == 0.:
            probs[key][i+1] = 1e-16
      teststats = [-1.*Log.PROCEDURE(probs['gyroAttProbX'][i]*\
                                     probs['gyroAttProbY'][i]*\
                                     probs['gyroAttProbZ'][i]),\
                   -1.*Log.PROCEDURE(probs['gyroAttProbX'][i+1]*\
                                     probs['gyroAttProbY'][i+1]*\
                                     probs['gyroAttProbZ'][i+1])]
      fullprobs = 1.-GammaP(3.)(teststats)
      if sum(fullprobs < probthresh) != 0 and probs['obt'][i+1] >= startscan and \
      probs['obt'][i] <= stopscan:
        index_low = bisect_left(scantimes, probs['obt'][i])
        index_high = bisect_left(scantimes, probs['obt'][i+1])
        onlygoodprobs[:,:,index_low:index_high] = True

    frames.addMaskType('badprobs', 'mask is true if prob is bad')
    frames.setMask('badprobs', onlygoodprobs)

    level1.averaged.getCamera(camera).product.replace(0, frames)
  
    obs.level1 = level1

    saveObservation(obs, poolName = poolname)
    
  else:
  
    print 'This observation contains a gyro prob mask'
  
  return