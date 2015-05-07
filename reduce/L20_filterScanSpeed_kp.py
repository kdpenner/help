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
  Generates masks in the level 2 script

Description :
- This script runs a number of routines found in the level 2 script.  I want
  only the masks and other changes made to the level 1 products.

Inputs :
- obs : ObservationContext
    - Products needed to run the pipeline are extracted from it
- camera : camera
    - "red" or "blue"
- calTree : Calibration Tree from the observation, or generated within your HIPE
  session

Author :
  Ekkehard Wieprecht <ewieprec@mpe.mpg.de>
  Bruno Altieri <bruno.altieri@sciops.esa.int>
"""
from herschel.pacs.spg.pipeline   import *
from herschel.pacs.signal.context import *
from herschel.pacs.spg.all        import *
from herschel.pacs.spg            import *
from herschel.ia.pg               import ProductSink
from herschel.pacs.share.util     import PacsProductSinkWrapper
from herschel.ia.pal              import ProductRef
from herschel.ia.all              import *
from java.lang                    import System
from herschel.pacs.spg.phot.deglitching.map import MapDeglitchTask
from herschel.pacs.spg.phot.scanam import *
from herschel.pacs.spg.phot import PhotHelper
from herschel.pacs.spg.common     import *
from herschel.ia.dataset import StringParameter
from herschel.ia.dataset import DoubleParameter
from herschel.share.unit import Angle
from runfilteronscanspeed import runfilteronscanspeed

def L20_filterScanSpeed_kp(obs, camera):

  poolname = obs.level0.getCamera(camera).averaged.product.refs[0].urn.split(':')[1]
# ------------------------------------------------------------------------------
# Extract the calibration tree 
  calTree = obs.calibration
#
# interactive user: you may apply following e.g. to get the most recent
# calibration
#calTree = getCalTree(obs=obs)
#
# ------------------------------------------------------------------------------
#
#
# Extract out the level1 from the ObservationContext
  level1 = PacsContext(obs.level1)
  frames = level1.averaged.getCamera(camera).product.getScience(0)
# ******************************************************************************
#         Processing
# ******************************************************************************
# Flag jump/module drop outs
#
  frames = scanamorphosMaskLongTermGlitches(frames, stepAfter=20)
#
# Flag calibration block decays
#
  frames = scanamorphosBaselinePreprocessing(frames)

  System.gc()
#
# Filter on scan speed (parameter at the top)
  frames = runfilteronscanspeed(frames)
#
# spatial deglitching now after just before photProject SPRs PACS-3522 &
# PACS-3906
#s = Sigclip(10, 20)
#s.behavior = Sigclip.CLIP
#s.outliers = Sigclip.BOTH_OUTLIERS
#s.mode = Sigclip.MEDIAN
#
#mdt = MapDeglitchTask()
#mdt(frames, algo = s, deglitchvector="timeordered", calTree=calTree)
#
# save the new glitch mask to be casted back to L1 frames
#if frames.meta.containsKey('Glitchmask') :
#  glitchmaskdata = frames.meta["Glitchmask"]
#  mask   = frames.getMask(glitchmaskdata.value)
#
# Masking the "no scan data" (using BBID 215131301) - Mask name : NoScanData
#frames = photMaskFrames(frames, noScanData = 1, remove=1)   #PACS-4008
#
#frames  = filterOnScanSpeed(frames,lowScanSpeed=lowscanspeed,highScanSpeed=highscanspeed)
#
#System.gc()
#
# 
# Add some Quality information to the frames 
  frames = addQualityInformation(frames)
#
# Post processing
# cast the glitch mask back into level 1
#if frames.meta.containsKey('Glitchmask') :
#  del(frames)
#  frames = level1.averaged.getCamera(camera).product.getScience(0)
#  frames.removeMask(glitchmaskdata.value)
#  frames.addMaskType(glitchmaskdata.value,glitchmaskdata.description)
#  frames.setMask(glitchmaskdata.value,mask)
#  frames.meta["Glitchmask"] = glitchmaskdata
#  level1.averaged.getCamera(camera).product.replace(0, frames)
#  obs.level1 = level1
#  del(glitchmaskdata, mask)
#
# delete some variables
#del level1, frames, hpfradius1, hpfradius2, outputPixelSize
#del lowscanspeed, highscanspeed, speed, ref, med, index
#del signal_stdev, cutlevel, threshold, HPFmask, s, mdt, image, ad, mi, historyCopy

  level1.averaged.getCamera(camera).product.replace(0, frames)

  obs.level1 = level1

  saveObservation(obs, poolName = poolname)