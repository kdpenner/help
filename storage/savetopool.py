import commands
import re

c1 = LocalStoreContext()
c1_pre = c1.getStoreDir().toString()

dir_pre = c1_pre.split('.hcss/')[0]

append_dir = raw_input('Your local store is in '+dir_pre+'. Enter the \
remaining directory structure:')

dir_pre = dir_pre + append_dir

out = commands.getstatusoutput('ls '+dir_pre)
dirs = out[1].split()

common_dirname = raw_input('Enter a string common and exclusive \
to all downloaded dirs:')
pool_name = raw_input('Enter a pool name:')

print 'Searching for '+common_dirname+' in '+str(dirs)

for direct in dirs:
  if common_dirname in direct:
    get_obsids = commands.getstatusoutput('ls '+dir_pre+direct)[1]
    obsids = re.findall(r'(\d+)-', get_obsids)

    for obsid in obsids:
      print 'Getting', obsid, 'from', dir_pre + direct
      t = getObservation(obsid, path = dir_pre + direct)
      saveObservation(t, poolName = pool_name, saveCalTree = True)
