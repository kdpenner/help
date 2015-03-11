def getpointcol(pointprod, *args):

  keys = pointprod.keySet().toArray()

  keys.pop()

  if not args:

    print 'Specify column(s) in *args. Possible values are:'
    print pointprod[keys[0]].getColumnNames()
    result = None

  else:

    result = {}

    for arg in args:

      temp = []

      for key in keys:

        temp.extend(pointprod[key][arg].data)

      result[arg] = temp

  return(result)