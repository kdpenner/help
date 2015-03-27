#!/usr/bin/env python -tt

import sys
import math
import numpy
import itertools
from bokeh.plotting import figure, output_file, show

def gyroplotbk(filename):

  data = numpy.genfromtxt(filename, names=True)
  
  savename = '.'.join(filename.split('.')[:-1])+'.html'
  
  output_file(savename)

  colors = itertools.cycle(('#d95f02', '#7570b3', '#1b9e77'))
  markers = itertools.cycle(('o', 'triangle', 'diamond'))

  data['obt'] = (data['obt']-data['obt'][0])/1.e6/60.

  p = figure(tools = 'wheel_zoom, box_zoom, box_select, reset, save', \
  x_axis_label = 'Time (minutes)', \
  y_axis_label = 'Probability that fit is good', \
  title = 'calcAttitude probabilities')

  for column in data.dtype.names:
    if column != 'obt':
      p.scatter(data['obt'], data[column], \
      legend = column, marker = markers.next(), line_color = colors.next(), \
      fill_color = None)

  show(p)

def main():

  filenames = sys.argv[1:]
  
  if not filenames:
    print 'Filename is required argument.'
    sys.exit(1)
  else:
    for filename in filenames:
      gyroplotbk(filename)

if __name__ == '__main__':
  main()
