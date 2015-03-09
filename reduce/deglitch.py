from herschel.pacs.signal import MapIndex
from herschel.pacs.spg.phot import MapIndexTask
from herschel.pacs.spg.phot import IIndLevelDeglitchTask

obsid = 1342223836
o = getObservation(obsid)
f = o.level1.refs['HPPAVGB'].product.refs[0].product
mit = MapIndexTask()
mi = mit(f)

s = Sigclip(nsigma = 5, outliers = 'both', behavior = 'filter', env = 10)


map = IIndLevelDeglitch(mi, f, deglitchvector = 'timeordered', algo = s)

# MapIndexViewer(mi, f)

# t = f['Mask']['2nd level glitchmask']