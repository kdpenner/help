import commands
import re

c1 = LocalStoreContext()
c1_pre = c1.getStoreDir().toString()

dir_pre = c1_pre.split('.hcss/')[0]

out = commands.getstatusoutput('ls '+dir_pre)
dirs = out[1].split()

common_dirname = raw_input('Enter a string common to all downloaded dirs:')
pool_name = raw_input('Enter a pool name:')

for dir in dirs[7:]:
  if common_dirname in dir:
    get_obsids = commands.getstatusoutput('ls '+dir_pre+dir)[1]
    obsids = re.findall(r'(\d+)-', get_obsids)

    for obsid in obsids:
      print 'Getting', obsid, 'from', dir_pre + dir
      t = getObservation(obsid, path = dir_pre + dir)
      saveObservation(t, poolName = pool_name, saveCalTree = True)

