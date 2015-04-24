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
  PACS Photometer Level 1 generation for scan maps with PhotProject (used for automatic pipeline processing)

Description :
- This script takes your data from Level 0.5 to 1, starting from a Frames class product.
  After this script you should run :   L2_scanMapPhotProject.py
- This script is written so that you can run it entirely in one go, or line-by-line....
    - ...however, you need to set up the camera *before* you run the script (see the line SETUP1) 
- Comments are included in this script, but for a full explanation see the PACS Data Reduction Guide (PDRG) 
    - Help Menu -> Show Contents -> PACS Data Reduction Guide
- Note that this is the script that HSC runs as the automatic pipeline, hence there are some things included 
   that are for that automatic pipeline rather than for the user. These are marked with FOR HSC PIPELINE. 
   You do not  need to run these commands if you are reducing the data yourself, but it does not harm them if you do


Inputs :    
- obs : ObservationContext
    - Products needed to run the pipeline are extracted from it
- camera : camera
    - "red" or "blue"
- calTree : Calibration Tree from the observation, or generated within your HIPE session 

Author :
  Ekkehard Wieprecht <ewieprec@mpe.mpg.de>


"""
from herschel.pacs.spg.pipeline   import *
from herschel.pacs.spg.phot       import *
from herschel.pacs.spg.all        import *
from herschel.ia.pal              import ProductRef
from herschel.pacs.share.util     import PacsProductSinkWrapper
from herschel.pacs.spg.common     import correctRaDec4Sso
from herschel.pacs.spg.pipeline.SaveProductToObservationContext import *
from herschel.pacs.cal.all import getCalTree

def L10_scanMap_kp(obs, camera):

# ------------------------------------------------------------------------------------
# Extract out the level0 from the ObservationContext
  level0 = PacsContext(obs.level0)
  level0_5 = PacsContext(obs.level0_5)
  frames = level0_5.averaged.getCamera(camera).product.copy()
  photHk = level0.hk.product.refs[0].product["HPPHKS"]
#
  poolname = obs.level0.getCamera(camera).averaged.product.refs[0].urn.split(':')[1]
#
  timeCorr = obs.auxiliary.timeCorrelation
  pp = obs.auxiliary.pointing
  orbitEphem = obs.auxiliary.orbitEphemeris
  horizonsProduct = obs.auxiliary.horizons
  sso = isSolarSystemObject(obs)
#
# ------------------------------------------------------------------------------------
# Extract the calibration tree 
  calTree = getCalTree(obs=obs)
#
# interactive user: you may apply following e.g. to get the most recent calibration
#calTree = getCalTree(obs=obs)
#
#
# ***********************************************************************************
#         Processing
# ***********************************************************************************
#
# Filter the slew to target from the data
  frames = filterSlew(frames)
#
# Find the major blockjs of this observation and organize it in the block table attached to the Frames
#frames = findBlocks(frames, calTree=calTree)
#
#
#frames = detectCalibrationBlock(frames)
#
#
#frames = removeCalBlocks(frames,useBbid=1)
#
# 
# Flag the pixel which are flagged as "bad" in a Mask : BADPIXELS
# Bad pixel are specified in a calibration file : PCalPhotometer_BadPixelMask_FM_vx.fits (for x set the version number)
# During this step also the calibration block is removed by setting Task parameter : scical="sci",keepall=False
  frames = photFlagBadPixels(frames, calTree=calTree, scical="sci", keepall=0, copy=1)
#
# The phenomenon of electronic crosstalk was identified, in particular in the
# red bolometer (column 0 of any bolometer) subarray, during the testing phase 
# and it is still present in in-flight data. We reccommend to flag those pixels
# in order to remove artifacts  from your map.
  frames = photMaskCrosstalk(frames)

#  Flag saturated pixel in a Mask : SATURATION_HIGH and SATURATION_LOW (SATURATION just contains both merged)
  frames = photFlagSaturation(frames, calTree=calTree, hkdata=photHk)
#
#
# Convert digital units to Volts
  frames = photConvDigit2Volts(frames, calTree=calTree)
# 
#
# Add the Utc column to the status table (not used in further processing)
  frames = addUtc(frames, timeCorr)
#
#
# Calculates the chopper position angle with respect to the optical axis of the focal plane unit 
# in degrees and add the Status parameter CHOPFPUANGLE 
  frames = convertChopper2Angle(frames, calTree=calTree)
#
# Converts Volt signal to Jansky and applies flat correction
# PCalPhotometer_Responsivity_FM_vx.fits and PCalPhotometer_FlatField_FM_vx.fits (for x set the version number)
  frames = photRespFlatfieldCorrection(frames, calTree=calTree)
#
# Apply the non linearity correction to take care of 
# flux deviations in the measurement of bright sources 
  frames = photOffsetCorr(frames)
  frames = photNonLinearityCorrection(frames, calTree=calTree)
#
# Add the pointing information to the status word of the frames class
# The frames finetime (status entry) is used to find the related information in the PointingProduct 
# Central focal plane coordinates  : RaArray, DecArray, PaArray 
#frames = photAddInstantPointing(frames, pp, calTree = calTree, orbitEphem = orbitEphem)   
#
# Move SSO target to a fixed position in sky. This is needed for mapping.
#
  if (sso):
    frames = correctRaDec4Sso(frames, timeOffset=0, orbitEphem=orbitEphem, horizonsProduct=horizonsProduct, linear=0)
#
# Assign RA and Dec position for every individual pixel
# Use PCalPhotometer_SubArrayArray_FM_vx.fits (for x set the version number)
# PCalPhotometer_ArrayInstrument_FM_vx.fits(for x set the version number)
# PhotProject is using this calls again internally, therefore it is not needed to executed it now
# only in case of e.g. coordinate checks
# frames = photAssignRaDec(frames, calTree=calTree)
#
#if (sso) :
#  timeOffset         = frames.startDate
#  horizonsProduct = obs.auxiliary.horizons
#  frames          = correctFramesRaDec4SsoDirections(frames, orbitEphem=orbitEphem, horizonsProduct=horizonsProduct, timeOffset=timeOffset)
#
# Save the slicedFrames to ObservationContext (overwrite !)
#
#
# Apply the Phot evaporator temperature correction
  frames = photTevCorrection(frames, calTree=calTree, hk=photHk)
#
#
  obs = savePhotProductToObsContextL1(obs, "HPPT" , camera, frames)

  saveObservation(obs, poolName = poolname)

# Remove some variables
  del level0, level0_5, frames, photHk, timeCorr, pp, orbitEphem, horizonsProduct, sso
