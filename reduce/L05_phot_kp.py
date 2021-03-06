# 
#  This file is part of Herschel Common Science System (HCSS).
#  Copyright 2001-2011 Herschel Science Ground Segment Consortium
# 
#  HCSS is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation, either version 3 of
#  the License, or (at your option) any later version.
# 
#  HCSS is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
# 
#  You should have received a copy of the GNU Lesser General
#  Public License along with HCSS.
#  If not, see <http://www.gnu.org/licenses/>.
# 
"""
Purpose :
  PACS Photometer Level 0.5 generation

Description :
- This script takes your data from Level 0 to 0.5, starting from a Frames class product.
  After this script you should run one of the level 1 generation scripts : L1_* 
- This script is written so that you can run it entirely in one go, or line-by-line....
    - ...however, you need to set up the camera *before* you run the script (see the line SETUP1) 
- Comments are included in this script, but for a full explanation see the PACS Data Reduction Guide (PDRG) 
    - Help Menu -> Show Contents -> PACS Data Reduction Guide
- Note that this is the script that HSC runs as the automatic pipeline, hence there are some things included 
   that are for that automatic pipeline rather than for the user. These are marked with FOR HSC PIPELINE. 
   You do not  need to run these commands if you are reducing the data yourself, but it does not harm them if you do
- This script runs on sliced products, that is data sliced according to an astronomical logic. 
   - See the PDRG for more information on slicing 
   - Help Menu -> Show Contents -> PACS Data Reduction Guide

Inputs :    
- obs : ObservationContext
    - Products needed to run the pipeline are extracted from it
- camera : camera
    - "red" or "blue"
- calTree : Calibration Tree from the observation, or generated within your HIPE session 

Author :
  Ekkehard wieprecht <ewieprec@mpe.mpg.de>

History : 
  2009-03-13 EkW Initial version 
  2009-09-24 EkW Operational version

"""
from herschel.pacs.spg import *
from herschel.pacs.spg.common import *
from herschel.pacs.spg.phot import *
from herschel.pacs.spg.pipeline import *
from herschel.pacs.signal.context import *
from herschel.pacs.signal import SlicedFrames
from herschel.pacs.cal import GetPacsCalDataTask
from herschel.ia.dataset import LongParameter
from herschel.pacs.spg.all import *
from herschel.ia.toolbox.util import SimpleFitsWriterTask
from herschel.ia.toolbox.pointing import CalcAttitudeTask
import os
from herschel.pacs.cal.all import getCalTree
simpleFitsWriter = SimpleFitsWriterTask()
calcAttitude = CalcAttitudeTask()

def L05_phot_kp(obs, camera):

  pp = obs.auxiliary.pointing
  
#  try:
#    pphist = pp.history.getTaskNames().toString()
#  except:
#    pphist = [None]

#  if 'calcAttitude' in pphist:

#    print 'You must not run calcAttitude twice on an observation.'
    
#    poolname = obs.level0.getCamera(camera).averaged.product.refs[0].urn.split(':')[1]

#  else:

#    c1 = LocalStoreContext()
#    c1_pre = c1.getStoreDir().toString()

#    dir_pre = c1_pre.split('.hcss/')[0]+'oldpoint/'

#    if not os.path.exists(dir_pre):
#      print 'Creating directory:'
#      print dir_pre
#      print 'for old pointing products'
#      os.mkdir(dir_pre)
#      print 'Saving old pointing product to:'
#      print dir_pre+str(obs.obsid)+'oldpp.fits'
#      simpleFitsWriter(product = pp, file = dir_pre+str(obs.obsid)+'oldpp.fits')
#    else:
#      print 'Saving old pointing product to:'
#      print dir_pre+str(obs.obsid)+'oldpp.fits'
#      simpleFitsWriter(product = pp, file = dir_pre+str(obs.obsid)+'oldpp.fits')

  poolname = obs.level0.getCamera(camera).averaged.product.refs[0].urn.split(':')[1]

# add extra meta data 
  pacsEnhanceMetaData(obs)

# copy meta keywords to level-0 products
  pacsPropagateMetaKeywords(obs,'0',obs.level0)

#
# Extract Time Correlation which is used to convert in addUtc
#  timeCorr = obs.auxiliary.timeCorrelation
#
# Extract the PointingProduct
#  acms = obs.auxiliary.acms
#  tchist = obs.auxiliary.teleCommHistory
#  newpp = calcAttitude(pp, acms, tchist)
#  obs.auxiliary.pointing = newpp
#
# ------------------------------------------------------------------------------------
# Extract out the level0 from the ObservationContext
  level0 = PacsContext(obs.level0)
#
# ------------------------------------------------------------------------------------
# Extract Horizons product which is need by SSO observations
# This product is available since bulk re processing with HCSS4.1
  horizonsProduct = obs.auxiliary.horizons
#
  orbitEphem = obs.auxiliary.orbitEphemeris
#
# ------------------------------------------------------------------------------------
# Extract the calibration tree 
  calTree = obs.calibration
#
# interactive user: apply following:
#calTree = getCalTree(obs=obs)
#
#
# ------------------------------------------------------------------------------------
  slicedFrames = SlicedFrames(level0.getCamera(camera).averaged.product)
#
# ***********************************************************************************
# Processing 
# Level 0.5 Products are just the sliced version of the Level 0 Products
# The intermediate processing steps are only used to identify the slices proper
# ***********************************************************************************
#
# ------------------------------------------------------------------------------------
# Add the pointing information to the status word of the frames class
# The frames finetime (status entry) is used to find the related information in the PointingProduct 
# Central focal plane coordinates  : RaArray, DecArray, PaArray 
#
# !!! Attention copy =1 is needed not to work straight on level 0 data !!!

  slicedFrames = photAddInstantPointing(slicedFrames, pp, calTree=calTree, orbitEphem=orbitEphem, horizonsProduct=horizonsProduct, copy=1)
#
# Identify the calibration blocks and fills the CALSOURCE status entry. 
# This task has been introduced because only the labels are no longer a reliable source of information. 
# Here also the chopper position and BBTYPE are taken into account.
  slicedFrames = detectCalibrationBlock(slicedFrames)
#
#
# Remove calibration blocks 
# We remove the calibration blocks, because due to commanding error very early scans are interrupted
# by calibratyion blocks. Before and after is considered a separate slice then.
# This is deactivated this way and the whole data appear in one slice
  slicedFrames = removeCalBlocks(slicedFrames,useBbid=1,skipAfter=300)
#
#
# FindBlocks need to run to make the block table which is used by pacsSliceContext then
  slicedFrames = findBlocks(slicedFrames, calTree=calTree)
#
#
# The meta keyward repFactor is needed as this is a slice criteria for PointSource observations
  if (not slicedFrames.meta.containsKey("repFactor")):
    slicedFrames.meta["repFactor"] = LongParameter(1)
#
#
# Re-slice the data to level-0.5 conventions
  slicedFrames, other = pacsSliceContext(slicedFrames, level='0.5')
#
# Save the slicedFrames to ObservationContext (overwrite !)
  obs = savePhotProductToObsContextL05(obs, "HPPT" , camera, slicedFrames)

  saveObservation(obs, poolName = poolname, saveCalTree = True)

#
# delete some variables
  del level0, pp, horizonsProduct, orbitEphem, slicedFrames, other
