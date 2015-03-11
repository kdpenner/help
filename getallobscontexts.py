def getallobscontexts(poolname):

  query = ProductStorage([PoolManager.getPool(poolname)]).select(herschel.ia.pal.query.MetaQuery(herschel.ia.obs.ObservationContext, "p", "1"))

  obscontexts = []

  for result in query:

    obscontexts.append(result.product)

  def getallobsids(context):

    return(context.meta['obsid'].long)

  obscontexts = sorted(obscontexts, key = getallobsids)

  return(obscontexts)