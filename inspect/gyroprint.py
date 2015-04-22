import os
from bisect import bisect_left
from herschel.pacs.spg.common import filterOnScanSpeed

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

def findprobsforscantimes(scantimes, probsdict):

  """Finds the prob times, which are coarsely sampled, for the scan times,
  which are finely sampled, and returns the corresponding probs data

  The inputs must be sorted such that the times increase with increasing index.

  (You can use this for the reverse task, finding the scan times for the prob
  times, as well.  Throw away the prob times before the first scan time and
  after the last scan time.  Input your prob times to the parameter scantimes
  and be sure that the scan times are in a dict with the data you want matched.)

  This routine does not always return the *closest* times.  Use with caution.

  Inputs:
  scantimes -- a list from the level 1 frame of all scan times.
  probsdict -- a dictionary from getpointcol. It must contain a key named
  'obt.'  The data must be a list of all prob times.

  Output:
  scantimesdict -- a dictionary with the format of probsdict and the length of
  scantimes.
  """

  scantimesdict = {}

  for time in scantimes:
    scantimesindex = bisect_left(probsdict['obt'], time)
    for key in probsdict.iterkeys():
      try:
        scantimesdict[key].append(probsdict[key][scantimesindex])
      except KeyError:
        scantimesdict[key] = [probsdict[key][scantimesindex]]
      except IndexError:
        # bisect_left returns the index of insertion.  This is sometimes out of
        # bounds because the scan times exceed the prob times.
        scantimesindex = scantimesindex - 1
        scantimesdict[key].append(probsdict[key][scantimesindex])

  return(scantimesdict)

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
