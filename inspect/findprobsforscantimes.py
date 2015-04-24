from bisect import bisect_left

def findprobsforscantimes(scantimes, probsdict):

  """Finds the prob times, which are coarsely sampled, for the scan times,
  which are finely sampled, and returns the corresponding probs data

  The inputs must be sorted such that the times increase with increasing index.

  (You can use this for the reverse task, finding the scan times for the prob
  times, as well.  Throw away the prob times before the first scan time and
  after the last scan time.  Input your prob times to the parameter scantimes
  and be sure that the scan times are in a dict with the data you want matched.)

  This routine does not always return the *closest* times.  Use with caution.

  Inputs:
  scantimes -- a list from the level 1 frame of all scan times.
  probsdict -- a dictionary from getpointcol. It must contain a key named
  'obt.'  The data must be a list of all prob times.

  Output:
  scantimesdict -- a dictionary with the format of probsdict and the length of
  scantimes.
  """

  scantimesdict = {}

  for time in scantimes:
    scantimesindex = bisect_left(probsdict['obt'], time)
    for key in probsdict.iterkeys():
      try:
        scantimesdict[key].append(probsdict[key][scantimesindex])
      except KeyError:
        scantimesdict[key] = [probsdict[key][scantimesindex]]
      except IndexError:
        # bisect_left returns the index of insertion.  This is sometimes out of
        # bounds because the scan times exceed the prob times.
        scantimesindex = scantimesindex - 1
        scantimesdict[key].append(probsdict[key][scantimesindex])

  return(scantimesdict)
