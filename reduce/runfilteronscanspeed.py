from herschel.pacs.spg.common import FilterOnScanSpeedTask
filterOnScanSpeed = FilterOnScanSpeedTask()

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
