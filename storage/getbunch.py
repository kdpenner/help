import csv
import os

filename = raw_input('Working dir is '+os.getcwd()+'. Enter file name to read:')

f = open(filename, 'rb')

reader = csv.reader(f)

obsids = []

for row in reader:
  obsids.append(row[0])

f.close()

obsids = obsids[1:2]

pool_name = raw_input('Enter a pool name:')

for obsid in obsids:
  print 'Getting '+obsid+' and storing in '+pool_name
  obs = getObservation(obsid, useHsa = True)
  saveObservation(obs, poolName = pool_name, saveCalTree = True)