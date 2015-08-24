import csv
import os

filename = raw_input('Working dir is '+os.getcwd()+'. Enter file name to read:')

f = open(filename, 'rb')

reader = csv.reader(f)

obsids = []

for row in reader:
  obsids.append(row[0])

f.close()

obsids = obsids[1:]

pool_name = raw_input('Enter a pool name:')

query = ProductStorage([PoolManager.getPool(pool_name)]).select(herschel.ia.pal.query.MetaQuery(herschel.ia.obs.ObservationContext, "p", "1"))

listofobsids = []

for result in query:
  listofobsids.append(result.product.obsid)

for obsid in obsids:
  if long(obsid) in listofobsids:
    print 'Obsid already exists in pool. Skipping download.'
  else:
    print 'Getting '+obsid+' and storing in '+pool_name
    obs = getObservation(obsid, instrument = 'PACS', useHsa = True)
    saveObservation(obs, poolName = pool_name, saveCalTree = True)
