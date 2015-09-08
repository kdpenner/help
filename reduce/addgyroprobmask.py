from herschel.ia.numeric.toolbox.basic import GammaP
from herschel.ia.numeric.toolbox.basic import Log
from herschel.ia.numeric import Bool3d
from herschel.ia.numeric import Double1d
from herschel.ia.numeric import String1d
from herschel.pacs.spg.pipeline.SaveProductToObservationContext import *
from help.inspect import getpointcol
from help.inspect import findprobsforscantimes
from herschel.ia.toolbox.util.jython import saveObservation


def addgyroprobmask(obs, camera, probthresh = 1.e-4):

  poolname = obs.level0.getCamera(camera).averaged.product.refs[0].urn.split(':')[1]

  level1 = PacsContext(obs.level1)

  frames = level1.averaged.getCamera(camera).product.getScience(0)
  
  scantimes = frames['Status']['FINETIME'].data

  probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', \
                      'gyroAttProbY', 'gyroAttProbZ')

  scandict = findprobsforscantimes(scantimes, probs)

  teststat = -1.*Log.PROCEDURE(Double1d(scandict['gyroAttProbX'])*\
                  Double1d(scandict['gyroAttProbY'])*\
                  Double1d(scandict['gyroAttProbZ']))

  scandict['fullprob'] = 1.-GammaP(3.)(teststat)

  numtimesteps = len(scandict['obt'])

  # masked pixels have a mask value of True
  onlygoodprobs = Bool3d(32, 64, numtimesteps, False)

  for i in xrange(numtimesteps):
    if scandict['fullprob'][i] < probthresh:
      onlygoodprobs[:,:,i] = True

  frames.addMaskType('goodprobs', 'only the good pointing probs')
  frames.setMask('goodprobs', onlygoodprobs)

  frames.mergeMasks(String1d(["SATURATION", "goodprobs"]), 'forunihipe')
  
  level1.averaged.getCamera(camera).product.replace(0, frames)
  
  obs.level1 = level1

  saveObservation(obs, poolName = poolname)
  
  return