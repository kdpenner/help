from herschel.ia.pal import ProductStorage
from herschel.ia.pal import PoolManager
from herschel.ia.pal.query import MetaQuery
from herschel.ia.obs import ObservationContext

def getallobscontexts(poolname):

  query = ProductStorage([PoolManager.getPool(poolname)]).select(MetaQuery(ObservationContext, "p", "1"))

  obscontexts = []

  for result in query:

    obscontexts.append(result.product)

  def getallobsids(context):

    return(context.meta['obsid'].long)

  obscontexts = sorted(obscontexts, key = getallobsids)

  return(obscontexts)