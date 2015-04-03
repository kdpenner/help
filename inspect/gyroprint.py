import os
from herschel.pacs.spg.common import filterOnScanSpeed

def gyroprint(poolname):

  obses = getallobscontexts(poolname)

  for obs in obses:

    strobsid = str(obs.obsid)

    try:
      probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', 'gyroAttProbY', 'gyroAttProbZ')
    except IndexError:
      print 'You must run calcAttitude on obsid '+strobsid
    else:

      frame = obs.level1.refs['HPPAVGB'].product.refs[0].product

      times = tuple(probs['obt'])

      if obs.cusMode == 'SpirePacsParallel':
        speed = obs.meta['mapScanRate'].value
        if speed == 'slow':
          lowscanspeed  = 15.
          highscanspeed = 25.
        elif speed == 'fast':
          lowscanspeed  = 54.
          highscanspeed = 66.
      elif obs.cusMode == 'PacsPhoto':
        speed = obs.meta['mapScanSpeed'].value
        if speed == 'medium':
          lowscanspeed  = 15.
          highscanspeed = 25.
        elif speed == 'high':
          lowscanspeed  = 54.
          highscanspeed = 66.
        elif speed == 'low':
          lowscanspeed  = 8.
          highscanspeed = 12.

      addscan = filterOnScanSpeed(frame, lowScanSpeed = lowscanspeed, \
      highScanSpeed = highscanspeed)

      scanmask = addscan['Mask']['ScanSpeedMask'].data[0,0,:]

#      badspeeds = scanmask.where(scanmask == False)
#      badtimes = frame['Status']['FINETIME'].data[badspeeds]

      scantimes = frame['Status']['FINETIME'].data
      start = scantimes[0]
      end = scantimes[-1]

      filename = poolname+'_'+strobsid+'gyro.dat'
      sortedkeys = sorted(probs.keys(), reverse = True)

      f = open(filename, 'wb')
      f.write(' '.join(sortedkeys) + '\n')

#      i = 0

      for j in range(len(times)):
        if (times[j] > end or times[j] < start):
#          for key in probs.keys():
#       print i
#       print j
#       print 'deleting ', j-i
#            del probs[key][j-i]
#          i = i + 1
          pass
        else:

          scantimesdiff = probs['obt'][j]-scantimes
          scantimesdiff.abs()
          scantimesindex = scantimesdiff.where(scantimesdiff == \
          min(scantimesdiff)).toInt1d()[0]

          if scanmask[scantimesindex] is True:
            pass
          else:

            writestr = ''
            for key in sortedkeys:
              writestr = writestr + ' ' + str(probs[key][j])
            f.write(writestr + '\n')

      f.close()

      print 'Wrote output file '+os.getcwd()+'/'+filename

  return

#plot = PlotXY()
#layer = LayerXY(Double1d(probs['obt']), Double1d(probs['gyroAttProbX']))
#layer.setLine(0)
#plot.addLayer(layer)