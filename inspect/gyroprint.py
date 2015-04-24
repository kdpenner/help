import os
from bisect import bisect_left
from herschel.pacs.spg.common import filterOnScanSpeed
from findprobsforscantimes import findprobsforscantimes

def runfilteronscanspeed(frame):

  """Runs filterOnScanSpeed

  Input:
  frame -- a level 1 frame.

  Output:
  The level 1 frame.  It should have a Mask dataset named 'ScanSpeedMask'.
  """

  try:
    speed = frame.meta['mapScanRate'].value
  except IndexError:
    speed = frame.meta['mapScanSpeed'].value

#  print speed

  if speed == 'slow' or speed == 'medium':
    lowscanspeed  = 15.
    highscanspeed = 25.
  elif speed == 'fast' or speed == 'high':
    lowscanspeed  = 54.
    highscanspeed = 66.
  elif speed == 'low':
    lowscanspeed  = 8.
    highscanspeed = 12.

#  print lowscanspeed, highscanspeed

#  print 'Running filterOnScanSpeed'

  addscanframe = filterOnScanSpeed(frame, lowScanSpeed = lowscanspeed, \
                                   highScanSpeed = highscanspeed)

#  print 'Finished with filter'

  return(addscanframe)

def gyroprint(poolname):

  """Prints gyro probabilities in pointing products to text files

  Gyro probabilities are removed at times when Herschel is turning around.
  Probabilities are in the level 0.5 product but the turn-around mask is placed
  in the level 1 product.  So the level 1 frame must already exist; do not run
  this routine on an observation context missing the level 1 frame.  An
  unfortunate dependency.

  Input:
  poolname -- the pool name.

  Output:
  Text files in the working directory.  There should be one text file for each
  observation ID.
  """

  obses = getallobscontexts(poolname)

  for obs in obses:

    strobsid = str(obs.obsid)

    try:

      # X = direction of motion, Y and Z = the important probs for the map
      probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', 'gyroAttProbY', 'gyroAttProbZ')

    except IndexError:

      print 'You must run calcAttitude on obsid '+strobsid

    else:

      frame = obs.level1.refs['HPPAVGB'].product.refs[0].product

      addscan = runfilteronscanspeed(frame)
      
      scanmask = addscan['Mask']['ScanSpeedMask'].data[0,0,:]

      scantimes = frame['Status']['FINETIME'].data

      filename = poolname+'_'+strobsid+'gyro.dat'

      sortedkeys = sorted(probs.keys(), reverse = True)

      f = open(filename, 'wb')
      f.write(' '.join(sortedkeys) + '\n')

      # prepare to run findprobsforscantimes in opposite sense

      obsstart = scantimes[0]
      obsend = scantimes[-1]

      probstartindex = bisect_left(probs['obt'], obsstart)
#      print probstartindex
      probendindex = bisect_left(probs['obt'], obsend)
#      print probendindex

      for key in probs.iterkeys():
        probs[key] = probs[key][probstartindex:probendindex]

      probtimes = probs['obt']

      scandict = {'obt': scantimes, 'scanmask': scanmask}

      matchedprobs = findprobsforscantimes(probtimes, scandict)

      for k, scanstatus in enumerate(matchedprobs['scanmask']):
        if scanstatus is False:
          writestr = ''
          for key in sortedkeys:
            writestr = writestr + ' ' + str(probs[key][k])
          f.write(writestr + '\n')

      f.close()

      print 'Wrote output file '+os.getcwd()+'/'+filename
