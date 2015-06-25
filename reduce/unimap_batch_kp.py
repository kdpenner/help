### To exec the task you can set directly the parameters as in the following example: 
# uniHipe(obsidList=obsList, tag='test2_obsids', execUniHipe = True, execUnimap=True, batchExec=True, outDir='/data/test/new_2obsid',\
#    type='spire', instrument='SPIRE', store='HSA', mcrDir='/home/hipe/MATLAB/v78', unimapDir='/home/hipe/gabri', \
#    spireArray='PLW', filterSize=20.0)

# or set here each parameters and then excute the task as did in the following lines: 

from help import getallobscontexts
from datetime import datetime
import os
import sys
import shutil
from herschel.ia.pal.pool.lstore import LocalStoreContext

from herschel.ia.gui.apps.plugin import PluginRegistry

reg = PluginRegistry.getInstance()

name = 'UniHipePlugin' # fill in the name of the plug-in here
plugin = reg.get(name)
basedir = plugin.pluginDir.absolutePath
sys.path.append(basedir)

from plugin import UniHipeTask

uniHipe = UniHipeTask()

def unimap_batch_kp(poolname, camera):

  obses = getallobscontexts(poolname)

  for obs in obses:

######### PARAMETER SETTING ##########

### GENERAL PARAMETERS
# 1. obsidList (MANDATORY) : a list of obsids

    obsidList = [obs.obsid]

# 2. tag: the name to associate to the unihipe run (e.g "run_april_15", if not set the default is obsid1_obsid2)

    runtime = str(datetime.now().date())

    tag = runtime+'-'+poolname

# 3. inOutDir (MANDATORY): the output directory where the unihipe and unimap products will be saved 

    c1 = LocalStoreContext()
    c1_pre = c1.getStoreDir().toString()

    dir_pre = c1_pre.split('.hcss/')[0]

    inOutDir = dir_pre+'unimap'

    if not os.path.exists(inOutDir):
      try:
        os.makedirs(inOutDir)
      except OSError:
        print 'Could not make directory', inOutDir
        sys.exit(1)

# 4. instrument (MANDATORY): select between SPIRE and PACS

    instrument = "PACS"

# 5. batchExec (default False): select it to exec the task in batch mode. If is set and store is set to 
#    Local Directory you have to provide a list of directory where the level1 fits files are stored using
#    location parameter

    batchExec = True

# 6. execUniHipe (default True): select it to execute the preprocess of level1 data for unimap. 
#     If set, you have to provide also values for the specific UniHipe parameters.

    execUniHipe = True 

# 7. execUnimap (default False): select it to execute also the UNIMAP process and the maps are generated.
#    If set, you have to provide also values for the specific UNIMAP parameters.

    execUnimap = False

### UNIHIPE PARAMETERS
## UniHipe converts standard SPIRE and PACS data to values valid as input for UniMap mapmaking.

# 8. type: select the type of process. Possible values are: 
#    - spire: convert directly the level1 (not recommended if data are taken directly from HSA)
#    - spire_lev0: generate new SPIRE level1 starting from level0 (eng conversion included) and then covert them
#    - spire_lev05: generate new SPIRE level1 starting from level0_5 and then covert them
#    - pacs_red: convert level1 PACS red band
#    - pacs_blue convert level1 PACS blue band

    type = "pacs_"+camera

# 9. store: where the data to convert are stored. Possible values are:
#    - Local Store: the products are stored in the HIPE Local Store
#    - HSA: the data should be downloaded from the Herschel Science Archive
#    - Local Directory: the products are stored in a local directory outside the HIPE local store
#      If the parameter is set to Local Directory you have to provide a list of directory (one for each obsid in obsidList)
#      If the task is executed in interactive way (i.e.  batchExec is set to false) a popup window will be open and you will
#      select the directories using the GUI interface. Otherwise you have to provide a list of directories using the 
#      "location" parameter (see below).

    store = "Local Store"

# 10.  location: if store is set to Local Store you can use this parameter to provide the name of the local store. If
#      store is set to Local Directory, you have to provide a list of directory (separated by a comma; where the level1 data are stored.
#location="~/1342198246/level1/herschel.spire.ia.dataset.PointedPhotTimeline, ~/1342198247/level1/herschel.spire.ia.dataset.PointedPhotTimeline"

# 11. updateCal: only for SPIRE. If set, the calibration tree attached to the observations is update using the last available locally (i.e. 
#     the last tree stored on your machine) and it will be used when the data are reprocessed from level0 or level0_5.

#  updateCal = True

### UNIMAP PARAMETERS
## UniMap generates the maps for SPIRE and PACS data.


# 12. mcrDir: where the MATLAB runtime is stored
# mcrDir= "/Applications/MATLAB/v716"

#13. unimapDir: where unimap is installed
# unimapDir="/Users/Gabri/hcss/unimap"

#14. spireArray: the SPIRE band to process with UNIMAP. If select ALL, all the three bands are processed. 
# spireArray="ALL"
 
#15. pacsArray: the PACS band to process with UNIMAP. If select ALL, all the two bands are processed. 
#pacsArray="red"

#16. filterSize: pgls high pass filter size in arcsec
# filterSize=10.0


#17. noiseFilterType: possible values are
#     0 raw unit power,
#     1 fit unit power,
#     2 raw estimated power (suggested for SPIRE observations)
#     3 fit estimated power
#     4 raw avefilt, 
#     5 fit avefilt
# noiseFilterType=2 

#18. startImage: Starting image for the gls (default 1): 0 zero image, 1 rebin, 2 highpass.
# startImage=0

# 19. wglsDThreshold: Threshold to detect an artifact (lower = more artifacts)
# wglsDThreshold=3.0

# 20. wglsGThreshold: Threshold to grow an artifact  (lower = wider artifacts)
# wglsGThreshold=1.5

#21. loadWglsImage: Select it to load final WGLS image generated by UNIMAP
# loadWglsImage=False



########TASK Execution #############

    uniHipe(obsidList = obsidList, execUniHipe = execUniHipe, \
    execUniMap = execUnimap, batchExec = batchExec, inOutDir = inOutDir, \
    type = type, instrument = instrument, store = store, tag = tag)
    
    shutil.move(inOutDir+'/'+tag+'/'+camera+'/unimap_meta_'+camera+'.dat', \
    inOutDir+'/'+tag+'/'+camera+'/unimap_meta_'+camera+str(obsidList[0])+'.dat')