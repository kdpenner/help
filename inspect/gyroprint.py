import os

def gyroprint(poolname):

  obses = getallobscontexts(poolname)

  for obs in obses:

    strobsid = str(obs.obsid)

    try:
      probs = getpointcol(obs.auxiliary.pointing, 'obt', 'gyroAttProbX', 'gyroAttProbY', 'gyroAttProbZ')
    except IndexError:
      print 'You must run calcAttitude on obsid '+strobsid
    else:
      start = obs.level1.refs['HPPAVGB'].product.refs[0].product['Status']['FINETIME'].data[0]
      end = obs.level1.refs['HPPAVGB'].product.refs[0].product['Status']['FINETIME'].data[-1]

      times = tuple(probs['obt'])

      filename = poolname+'_'+strobsid+'gyro.dat'
      sortedkeys = sorted(probs.keys(), reverse = True)

      f = open(filename, 'wb')
      f.write(' '.join(sortedkeys) + '\n')

      i = 0

      for j in range(len(times)):
        if (times[j] > end or times[j] < start):
          for key in probs.keys():
#       print i
#       print j
#       print 'deleting ', j-i
            del probs[key][j-i]
          i = i + 1
        else:
          writestr = ''
          for key in sortedkeys:
            writestr = writestr + ' ' + str(probs[key][j-i])
          f.write(writestr + '\n')

      f.close()

      print 'Wrote output file '+os.getcwd()+'/'+filename

  return

#plot = PlotXY()
#layer = LayerXY(Double1d(probs['obt']), Double1d(probs['gyroAttProbX']))
#layer.setLine(0)
#plot.addLayer(layer)