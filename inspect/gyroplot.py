import sys
import math
import numpy
import matplotlib.pyplot as plot
import itertools
import re

def gyroplot(filename):

  data = numpy.genfromtxt(filename, names=True)

  plot.rcParams['figure.figsize'] = [7.32, 7.32]
#  plot.rcParams['font.sans-serif'] = ['Helvetica']
  plot.rcParams['axes.color_cycle'] = ['#d95f02', '#7570b3', '#1b9e77']
  markers = itertools.cycle(('o', '^', 'D'))

  data['obt'] = (data['obt']-data['obt'][0])/1.e6

  for column in data.dtype.names:
    if column != 'obt':
      plot.plot(data['obt'], data[column], marker = markers.next(), \
      linestyle = '', label = column, fillstyle = 'none')

  plot.xlabel('Time')
  plot.ylabel('Probability that fit is good')
  ymin, ymax = plot.ylim()
  plot.ylim(ymax = (ymax - ymin)*1.1+ymin)
  plot.legend(loc = 'lower right', prop = {'size': 18}, numpoints = 1)

  savename = '.'.join(filename.split('.')[:-1])+'.eps'
  
  plot.savefig(savename)

  plot.close()
  
  print 'Plot is here: '+savename

def main():

  filenames = sys.argv[1:]
  
  if not filenames:
    print 'Filename is required argument.'
    sys.exit(1)
  else:
    for filename in filenames:
      gyroplot(filename)

if __name__ == '__main__':
  main()
