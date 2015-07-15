import os
import shutil
import sys
import subprocess
from string import rfind
from string import replace
from string import split
from org.python.core import PyList
from javax.swing import *
from herschel.ia.numeric import *
from herschel.ia.io.fits import *
from herschel.ia.io.fits import FitsArchive
from herschel.ia.dataset import *
from herschel.ia.toolbox.util import *
from herschel.ia.gui.plot import *
from herschel.pacs.cal import *
from herschel.pacs.toolboxes.all import *
from java.util import Date
from java.lang import Runtime
from herschel.ia.task import *
from java.lang import Boolean
from herschel.ia.pal import *
from herschel.ia.obs import ObservationContext
from herschel.ia.pal.query import MetaQuery
from herschel.ia.pal.pool.lstore import LocalStoreFactory
from herschel.ia.pal.browser.v2.table.model import * 
from herschel.ia.pal.util import StorageResult
from herschel.ia.pal.pool.hsa import HsaReadPool
from herschel.ia.numeric.toolbox import *
from herschel.ia.numeric.toolbox.basic import MAX
from herschel.ia.toolbox.util import SimpleFitsReaderTask
from herschel.ia.gui.apps.modifier import JOptionModifier, JFilePathModifier
from herschel.ia.gui.kernel.util.field import FileSelectionMode
from herschel.spire.all import *
from herschel.spire.util import *
from herschel.ia.all import *
from herschel.ia.task.mode import *
from herschel.ia.pg import ProductSink
from java.lang import *
from java.util import *
from java.util import List
from java.io import *
from herschel.ia.obs.util import ObsParameter
from herschel.ia.pal.pool.lstore.util import TemporalPool
from herschel.spire.ia.pipeline.scripts.PARALLEL.PARALLEL_tasks import *

from herschel.ia.gui.kernel import ParameterValidatorAdapter
from herschel.ia.gui.kernel import ParameterValidationException
from herschel.ia.gui.kernel.Tool import Category
from herschel.ia.task.views import TaskToolRegistry
from herschel.ia.gui.kernel.parts import ExternalHelp
from herschel.ia.task import ParameterGroups, Group 
from herschel.pacs.signal.context import PacsContext
from herschel.ia.toolbox.util import AsciiTableWriterTask

asciiTableWriter = AsciiTableWriterTask()

from herschel.ia.gui.apps.plugin import PluginRegistry

reg = PluginRegistry.getInstance()

name = 'UniHipePlugin' # fill in the name of the plug-in here
plugin = reg.get(name)
basedir = plugin.pluginDir.absolutePath
sys.path.append(basedir)
del(reg, plugin, basedir, name)
import convert_binary
import unimap_spire
import unimap_pacs
#import unimap_spire_lev0

from unimap_spire import *
#from unimap_spire_lev0 import *
from unimap_pacs import *


class UniHipeTask(Task, ExternalHelp): 
	storeOptions=ArrayList()
	storeOptions.add("Local Store")
	storeOptions.add("HSA")
	storeOptions.add("Local Directory")
	
	cameraOptions=ArrayList()
	cameraOptions.add("pacs_blue")
	cameraOptions.add("pacs_red")
	cameraOptions.add("spire_lev0")
	cameraOptions.add("spire_lev05")
	cameraOptions.add("spire_lev1")

	instrumentOptions=ArrayList()
	instrumentOptions.add("PACS")
	instrumentOptions.add("SPIRE")

	arrayOptions=ArrayList()
	arrayOptions.add("ALL")
	arrayOptions.add("PSW")
	arrayOptions.add("PMW")
	arrayOptions.add("PLW")

	arrayPacsOptions=ArrayList()
	arrayPacsOptions.add("red")
	arrayPacsOptions.add("blue")
	
	def __init__(self, name="uniHipe"):
		self.setDescription("Task used to produce inputs for unimap mapmaker")
		p = TaskParameter('obsidList',valueType = List, type = IN, \
			mandatory = True, description = "Obsid 1 to process.")
		self.addTaskParameter(p)

   		p = TaskParameter('poolName',valueType = String, type = IN, \
			mandatory = True, description = "name of pool with obsIDs")
		self.addTaskParameter(p)
		
		p = TaskParameter('tag',valueType = String,type = IN, \
			mandatory = False, description = "Name identifies the run.")
		self.addTaskParameter(p)

		p = TaskParameter('execUniHipe',valueType = Boolean,type = IN, \
		mandatory = False, defaultValue= True, description = "Select it to generate the input for UniMap")
		self.addTaskParameter(p)


		p = TaskParameter('execUniMap',valueType = Boolean,type = IN, \
		mandatory = False, defaultValue= False, description = "Select it to execute also unimap to generate the final maps")
		self.addTaskParameter(p)

		p = TaskParameter('inOutDir',valueType = String,type = IN, \
			mandatory = True, description = "Output directory for UniHipe process, input directory for UniMap.")
		self.addTaskParameter(p)
		
		p = TaskParameter('type',valueType = String,type = IN, \
			mandatory = False, description = "Name indentifies the level of process.")
		self.addTaskParameter(p)

		p = TaskParameter('instrument',valueType = String,type = IN, \
		mandatory = True, description = "Name indentifies the instrument.")
		self.addTaskParameter(p)
		
		p = TaskParameter('store',valueType = String,type = IN, \
		mandatory = False, defaultValue= self.storeOptions[0], description = "Name indentifies the store to use.")
		self.addTaskParameter(p)

		p = TaskParameter('updateCal',valueType = Boolean,type = IN, \
		mandatory = False, defaultValue= False, description = "Select it to update the calibration tree attached to the observation (only for SPIRE data)")
		self.addTaskParameter(p)

		p = TaskParameter('batchExec',valueType = Boolean,type = IN, \
		mandatory = False, defaultValue= False, description = "Select it to execute the task in batch mode")
		self.addTaskParameter(p)

		p = TaskParameter('location',valueType = String,type = IN, \
		mandatory = False, defaultValue=None, description = "Name of the store or, if store is set to Local Directory, the list of directories where the level1 are locally stored")
		self.addTaskParameter(p)
		
		p = TaskParameter('mcrDir',valueType = String,type = IN, \
			mandatory = False, description = "The directory where the Matlab Compiler Runtime is installed.")
		self.addTaskParameter(p)
		
		p = TaskParameter('unimapDir',valueType = String,type = IN, \
		mandatory = False, description ="The directory where Unimap is installed", )
		self.addTaskParameter(p)
		
		p = TaskParameter('spireArray',valueType = String,type = IN, \
		mandatory = False, description = "Select the SPIRE array to be processed via UniMap")
		self.addTaskParameter(p)
		
		p = TaskParameter('pacsArray',valueType = String,type = IN, \
		mandatory = False, description = "Select the PACS array to be processed via UniMap")
		self.addTaskParameter(p)

		p = TaskParameter('filterSize',valueType = Double,type = IN, \
		mandatory = False, description = "The pgls high pass filter size in arcseconds")
		self.addTaskParameter(p)
		
		p = TaskParameter('startImage',valueType = Integer,type = IN, \
		mandatory = False, defaultValue=1, description = "Starting image for the gls (default 1): 0 zero image, 1 rebin, 2 highpass.")
		self.addTaskParameter(p)		
		
		p = TaskParameter('wglsDThreshold',valueType = Double,type = IN, \
		mandatory = False, defaultValue= 3.0, description = "Threshold to detect an artifact (lower = more artifacts)")
		self.addTaskParameter(p)
		
		p = TaskParameter('wglsGThreshold',valueType = Double,type = IN, \
		mandatory = False, defaultValue= 1.5, description = "Threshold to grow an artifact  (lower = wider artifacts)")
		self.addTaskParameter(p)

		p = TaskParameter('noiseFilterType',valueType = Integer,type = IN, \
		mandatory = False, defaultValue=2, description = "Noise filter type: 0 raw unit power, 1 fit unit power, 2 raw estimated power, 3 fit estimated power, 4 raw avefilt, 5 fit avefilt")
		self.addTaskParameter(p)

		p = TaskParameter('loadWglsImage',valueType = Boolean,type = IN, \
		mandatory = False, defaultValue= True, description = "Select it to load final WGLS image generated by UNIMAP")
		self.addTaskParameter(p)
		
		p = TaskParameter('maps',valueType = Object,type = OUT, \
		mandatory = False, description = "Array with maps")
		self.addTaskParameter(p)
		
	def getCustomModifiers(self): 
		map = LinkedHashMap()
		map.put("inOutDir", JFilePathModifier(FileSelectionMode.DIRECTORY, []))
		map.put("instrument", JOptionModifier(self.instrumentOptions.toArray()))
		map.put("type", JOptionModifier(self.cameraOptions.toArray()))
		map.put("store",JOptionModifier(self.storeOptions.toArray()))
		map.put("mcrDir", JFilePathModifier(FileSelectionMode.DIRECTORY, []))
		map.put("unimapDir", JFilePathModifier(FileSelectionMode.DIRECTORY, []))
		map.put("spireArray", JOptionModifier(self.arrayOptions.toArray()))
		map.put("pacsArray", JOptionModifier(self.arrayPacsOptions.toArray()))
		return map
	
	def getGroups(self):
		return ParameterGroups(self, [
		Group("Main", "Main parameters", ["obsidList",  "poolName", "tag","inOutDir", "instrument", "batchExec", "execUniHipe", "execUniMap"]),
		Group("UniHipe", "Options for UniHIpe inputs", [ "type",  "store", "location", "updateCal"]),
		Group("Unimap", "Unimap's options", ["mcrDir", "unimapDir", "spireArray", "pacsArray", "filterSize","noiseFilterType", "startImage", "wglsDThreshold", "wglsGThreshold", "loadWglsImage" ])
		])

	def getHelpURL(self):
		return "http://herschel.asdc.asi.it/index.php?page=unimap.html"
	
	def runUnimap(self, command):
		javaexec = getattr(Runtime.getRuntime(), "exec")
		javaexec(command)
		

		
	def execute(self):
		isBatch=self.batchExec
		useHsa = False
		if self.store == "HSA": useHsa=True
		localPool = None
		if self.store == "Local" and not self.location==None: localPool= self.location
		inOutDir= self.inOutDir
		instrument = self.instrument
		channel = self.type
		#indx=rfind(field, "/")
		tag=None
		if (self.tag is not None):
			tag = self.tag
		else:
			for obss in self.obsidList:
				if tag == None: 
					tag = str(obss)
				else:
					tag = tag+"_"+str(obss)
		workingDir=inOutDir+File.separator+tag
		exists_mainDir =  os.path.exists(inOutDir)
		if exists_mainDir == 0:
			os.mkdir(inOutDir)
		if os.path.exists(workingDir) == 0:
			print "Making "+workingDir
			os.mkdir(workingDir)
		
		if (channel == 'pacs_blue'):
			camera = 'blue'
		if (channel == 'pacs_red'):
			camera = 'red'
		if (self.execUniMap): 
			listArray = self.getArray(instrument) 
		obsids = self.obsidList
		poolname = self.poolName
		n_obsids=len(obsids)
		database=self.store
		
		if (self.execUniHipe):
			if database == 'Local Directory':
				if instrument == 'PACS':
					question = 'PACS: Choose the level 1 FITS files from your database'
					choosertitle = 'PACS'
				else:
					question = 'SPIRE: Choose the directory where level 1 files are saved'
					choosertitle = 'SPIRE'
				if isBatch:
					file = String1d(n_obsids)
					dirList=self.location
					dirList.replace(" ", "")
					file=String1d(dirList.split(","))
					for i in range(n_obsids):
						obsids[i]=str(i)
					
				else:
					file = String1d(n_obsids)
					for i in range(n_obsids):
						JOptionPane.showMessageDialog(None, question +" ( "+str(i)+" Selected )")
						fc =  JFileChooser()
						fc.setDialogTitle(choosertitle)
						if instrument == 'SPIRE': fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
						val = fc.showOpenDialog(None)
						if val == fc.APPROVE_OPTION:
							file[i] = str(fc.getSelectedFile())
						obsids[i] = str(i)
			results_list = PyList()
			dim_samples = Int1d()
			key = ['DATE-OBS','SPG','INSTRUME','BUNIT','WAVELNTH']
			comment = ['average JD','standard product generator','instrument','unit','wavelength in micron']
			julianDate = Double1d()
			spg_vect = String1d()
			wave_vect = String1d()
			
			for obsid in obsids:
				if (database == 'HSA' or database == "Local Store"):
					obs=getObservation(int(obsid), useHsa=useHsa, instrument=instrument,poolName = poolname)
					startDate = obs.meta['startDate'].time
					spg = obs.meta['creator'].string[4:len(obs.meta['creator'].string)]
					if instrument == 'SPIRE':
						if (self.updateCal):
							print "Updating the calibration tree attached to the obs" 
							cal = spireCal()
							obs.calibration.update(cal)
						if (channel == 'spire_lev0' or channel=='spire_lev05'):
							logger=TaskModeManager.getMode().getLogger()
							try:
								scandirect=obs.refs["auxiliary"].product.refs["UplinkProduct"].product["ObsRequestData"]["stringParameter"]['stringParamVal'].data[10]
							except IndexError:
								scandirect=obs.refs["auxiliary"].product.refs["UplinkProduct"].product["observationRequest"]["stringParameter"]['stringParamVal'].data[10]
							level1, scanle = self.spire_pipeline(obs, channel)
							obs.level1=level1
							#results = unimap_spire_lev0(obs,scanle)
							results = unimap_spire(obs)
							dim_samples.append(results[0][0].dimensions[0])
						else:
							print "Load and process SPIRE data"
							results = unimap_spire(obs)
							dim_samples.append(results[0][0].dimensions[0])
					else:
						########################
						frames = PacsContext(obs.level1).averaged.getCamera(camera).product.selectAll()
						calTree=getCalTree()
						if (database == 'HSA' or database == "Local Store"): calTree = getCalTree(obs=obs)
						results = unimap_pacs(frames,calTree,camera)
				if database == 'Local Directory':
					if instrument == 'SPIRE':
						obs = []
						list = os.listdir(file[i])
						img = simpleFitsReader(file[i]+'/'+list[0])
						startDate = img.meta['startDate'].time
						spg = img.meta['creator'].string[4:len(img.meta['creator'].string)]
						results = unimap_spire(obs,file[i])
					else:
						frames = simpleFitsReader(file[i])
						startDate = frames.meta['startDate'].time
						spg = frames.meta['creator'].string[4:len(frames.meta['creator'].string)]
						dimension = frames.dimensions[0]
						if camera == 'red':
							if dimension != 16:
								print 'Loaded frames are not red frames --STOP--'
								sys.exit()
						if camera == 'blue':
							if dimension != 32:
								print 'Loaded frames are not blue frames --STOP--'
								sys.exit()
						calTree = getCalTree()
						results = unimap_pacs(frames,calTree,camera)
						dim_samples.append(results[0].dimensions[0])			
				#computing JD    
				date = str(startDate)[0:10]
				time = str(startDate)[11:19]   
				date=date.split("-")
				dd=int(date[2])
				mm=int(date[1])
				yyyy=int(date[0])
				time=time.split(":")
				hh=float(time[0])
				min=float(time[1]) 
				sec=float(time[2])
				UT=hh+min/60+sec/3600
				if (100*yyyy+mm-190002.5)>0:
					sig=1
				else:
					sig=-1
				JD = 367*yyyy - int(7*(yyyy+int((mm+9)/12))/4) + int(275*mm/9) + dd + 1721013.5 + UT/24 - 0.5*sig +0.5
				julianDate.append(JD)
	
				spg_vect.append(spg)
	
				if instrument == 'PACS':
					if camera == 'red':
							wave = '160'
					else:
						blue = frames.meta['blue'].string
						if blue == 'blue1':
							wave = '70'
						else:
							wave = '100'
					wave_vect.append(wave)
		
				results_list.append(results)    
			JD_avg = str(MEAN(julianDate))
			ind = spg_vect.where(spg_vect == spg_vect[0])
			if (len(ind.toInt1d()) != n_obsids):
				print 'WARNING!! you are combinining observations with different SPG! EXIT'
			#    sys.exit()
			if instrument == 'PACS':
				ind = wave_vect.where(wave_vect == wave_vect[0])
				if (len(ind.toInt1d()) != n_obsids):
					print 'WARNING!! you are mixing blue and green observations! EXIT'
					sys.exit()
			if instrument == 'SPIRE':
				camera=['PSW','PMW','PLW']
				waves = ['250','350','500']
				for jspire in range(3):        
					self.readSpireFits(results_list, workingDir, camera[jspire], jspire, obsids, tag)
					m = TableDataset()
					meta_value = String1d([JD_avg,spg,instrument,'MJy/sr',waves[jspire]])
					m['meta'] = Column(meta_value)
					meta_name = workingDir+'/'+camera[jspire]+'/unimap_meta_'+camera[jspire]+'.dat'
					asciiTableWriter(m,meta_name,writeHeader=False)
			else:
				#n_bolo = results[0].dimensions[1]
				for i in range(n_obsids):
					self.readPacsFits(results_list, workingDir, camera, obsids, tag)
				m = TableDataset()
				meta_value = String1d([JD_avg,spg,instrument,'MJy/sr',wave])
				m['meta'] = Column(meta_value)
				meta_name = workingDir+'/'+camera+'/unimap_meta_'+camera+'.dat'
				asciiTableWriter(m,meta_name,writeHeader=False)


		if (self.execUniMap):
			if len(listArray) > 1:
				 maps=ArrayList()
			for array in listArray:
				print "Processing "+ array +" using Unimap"
				self.updateUnimapPar(array, workingDir)
				self.executeUnimap(workingDir)
				print "Saving final map for "+instrument+" "+array
				path=self.getWglsLocation(array, workingDir)
				finalMap=self.loadImage(path, array)
				if len(listArray) > 1: 
					maps.add(finalMap)
				else:
					maps=finalMap
				self.saveImage(finalMap, path, array)
				if (self.loadWglsImage): Display(finalMap, title="UniMap map for "+array)
			self.maps=maps

	def getCommandLine(self):
		print "loading command"
		return ["sh", self.unimapDir+"/run_unimap.sh", self.mcrDir]
	
	def getWglsLocation(self, array, workingDir):
		return workingDir + File.separator +array
		
	def loadImage(self, workingDirCam, array):
		map      = fitsReader(workingDirCam + '/img_wgls.fits')
		pgls     = fitsReader(workingDirCam + '/img_pgls.fits')
		gls      = fitsReader(workingDirCam + '/img_gls.fits')
		naive    = fitsReader(workingDirCam + '/img_rebin.fits')
		coverage = fitsReader(workingDirCam + '/cove_full.fits')
		noise    = fitsReader(workingDirCam + '/img_noise.fits')

		# Create the final map combining all the individual maps
		finalMap = SimpleImage()
		finalMap.setWcs(map.wcs)
		finalMap.setImage(map.image, SurfaceBrightness.JANSKYS_PER_PIXEL)
		finalMap.setError(noise.image)
		finalMap.setCoverage(coverage.image)
		finalMap["gls"] = ArrayDataset(gls.image, SurfaceBrightness.JANSKYS_PER_PIXEL,'gls')
		finalMap["pgls"] = ArrayDataset(pgls.image, SurfaceBrightness.JANSKYS_PER_PIXEL,'pgls')
		finalMap["naive"] = ArrayDataset(naive.image, SurfaceBrightness.JANSKYS_PER_PIXEL,'naive')
		finalMap = self.setMapMeta(finalMap)
		return finalMap
	
	def setMapMeta(self, map):
		map.meta["type"]=StringParameter(self.instrument + " Map", "Product Type Identification")
		map.meta["modelName"]=StringParameter("FLIGHT", "Model name attached to this product")
		map.meta["instrument"]=StringParameter( self.instrument,"Instrument attached to this product")
		map.meta["creator"]=StringParameter( "UniMap", "Generator of this product")
		return map
		
	def saveImage(self, finalMap, workingDirCam, array):
		simpleFitsWriter(finalMap, workingDirCam + '/unimap_'+array+'.fits')
	
	def executeUnimap(self, workingDir):
		command=self.getCommandLine()
		os.chdir(workingDir)
		print os.getcwd()
		process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
		output = process.communicate()[0]
		while True:
			nextline = process.stdout.readline()
			if nextline == '' and process.poll() != None:
				 break
			print nextline
			sys.stdout.flush() 
		print output
		exitCode = process.returncode

		if (exitCode == 0):
			return output
		else:
			raise Exception("Error")
		
	def updateUnimapPar(self, array, workingDir):
		path=self.unimapDir+"/unimap_par.txt"
		file_par = File(path)
		fileReader = FileReader(file_par)
		bufReader = BufferedReader(fileReader)
		i=0
		list=ArrayList()

		while (i < 50):
			line=bufReader.readLine()
			list.add(line)
			i=i+1
		list.set(1, workingDir + File.separator +array+File.separator+ "   % data_path - working directory")
		list.set(36, str(self.noiseFilterType) + "  % noise_filter_type - 0 raw unit power, 1 fit unit power, 2 raw estimated power, 3 fit estimated power, 4 raw avefilt, 5 fit avefilt ")
		list.set(40, str(self.startImage) + "  % gls_start_image - 0 zero img, 1 rebin, 2 highpass.")
		list.set(45, str(self.filterSize / 2) + "   % pgls_hfwin - positive integer - half len of the pgls highpass filter (samples) e.g. 20")
		list.set(48, str(self.wglsDThreshold)  + "  % wgls_gthresh - positve real - threshold to grow an artifact  (lower = wider artifacts)")
		list.set(49, str(self.wglsGThreshold)  + "  % wgls_gthresh - positve real - threshold to grow an artifact  (lower = wider artifacts)")

		pathWrite=workingDir+File.separator+"unimap_par.txt"
		unimapParametersFile = File(pathWrite);
		fileWirter=FileWriter(unimapParametersFile)
		bw = BufferedWriter(fileWirter)
		for line in list:
			bw.write(line + " \n")
		bw.close()
				
	def getArray(self, instrument):
		if instrument == "SPIRE": 
			if self.spireArray == "ALL": 
				return ["PSW", "PMW", "PLW"]
			else:
				return [self.spireArray]
		if instrument == "PACS":
			if self.pacsArray == "ALL": 
				return ["blue", "red"]
			else:
				return [self.pacsArray]

	def readPacsFits(self,results_list, workingDir, camera, obsids, tag):
		n_obsids=len(obsids)
		for i in range(n_obsids):
			exists_path =  os.path.exists(workingDir+'/'+camera)
			if exists_path == 0:
				os.mkdir(workingDir+'/'+camera)
			s = results_list[i][0].copy()
			r = results_list[i][1].copy()
			d = results_list[i][2].copy()
			f = results_list[i][3].copy()
			gb = results_list[i][4].copy()
			sc = results_list[i][6].copy()
			sp = results_list[i][7].copy()    
			print 'Saving PACS '+camera+' outputs'
			array = [s,r,d,f,gb,results_list[0][5],sc,sp]
			description = ['Signal','Ra','Dec','Flag','Good bolometers','Number bolometers'\
				,'Scanning flag ', 'Number of samples']
			c=CompositeDataset()
			for j in range(len(array)):
				dataset = ArrayDataset(description=description[j])
				dataset.data = array[j]
				c[description[j]] = dataset
			p = Product(description='Unimap input')
			p[str(obsids[i])] = c
			fits = FitsArchive(reader=FitsArchive.STANDARD_READER)
			fits.save(workingDir+'/'+camera+'/unimap_obsid_'+tag+'_'+camera+'_'+str(obsids[i])+'.fits',p)
			del array,p
			System.gc()

	def readSpireFits(self, results_list, workingDir, camera, jspire, obsids, tag):
		exists_path =  os.path.exists(workingDir+'/'+camera)
		if exists_path == 0:
			os.mkdir(workingDir+'/'+camera)
		n_obsids=len(obsids)
		for i in range(n_obsids):
			s = results_list[i][0][jspire].copy()
			r = results_list[i][1][jspire].copy()
			d = results_list[i][2][jspire].copy()
			f = results_list[i][3][jspire].copy()
			gb = results_list[i][4][jspire].copy()
			sc = results_list[i][6][jspire].copy()
			sp = results_list[i][7][jspire].copy()
			print 'Saving SPIRE '+camera+' outputs'
			array = [s,r,d,f,gb,Int1d().append(results_list[0][5][jspire]),sc,sp]
			description = ['Signal','Ra','Dec','Flag','Good bolometers','Number bolometers'\
				,'Scanning flag ', 'Number of samples']
			c=CompositeDataset()
			for j in range(len(array)):
				dataset = ArrayDataset(description=description[j])
				dataset.data = array[j]
				c[description[j]] = dataset
			p = Product(description='Unimap input')
			p[str(obsids[i])] = c
			fits = FitsArchive(reader=FitsArchive.STANDARD_READER)
			fits.save(workingDir+'/'+camera+'/unimap_obsid_'+tag+'_'+camera+'_'+str(obsids[i])+'.fits',p)
			del array,p
			System.gc()

	def spire_pipeline(self, obs, startLevel):
		start_level=startLevel
		obsid = obs.obsid
		print "processing OBSID=", obsid,"("+hex(obsid)+")"
		bsmPos=obs.calibration.phot.bsmPos
		lpfPar=obs.calibration.phot.lpfPar
		detAngOff=obs.calibration.phot.detAngOff
		elecCross=obs.calibration.phot.elecCross
		optCross=obs.calibration.phot.optCross
		chanTimeConst=obs.calibration.phot.chanTimeConst
		chanNum=obs.calibration.phot.chanNum
		fluxConvList=obs.calibration.phot.fluxConvList
		tempDriftCorrList=obs.calibration.phot.tempDriftCorrList
		hpp=obs.auxiliary.pointing
		siam=obs.auxiliary.siam
		tempStorage=Boolean.TRUE
		if TaskModeManager.getType().toString() == "INTERACTIVE" and tempStorage:
			pname="tmp"+hex(System.currentTimeMillis())[2:-1]
			tmppool=TemporalPool.createTmpPool(pname,TemporalPool.CloseMode.DELETE_ON_CLOSE)
			ProductSink.getInstance().productStorage=ProductStorage(tmppool)
		else: 
			tmppool=None
		pass
		# From Level 0 to Level 0.5
		if start_level=="spire_lev0":
			print "Executing eng conversion" 
			level0_5= engConversion(obs.level0,cal=obs.calibration, tempStorage=tempStorage)
			obs.level0_5=level0_5
		else:
			level0_5=obs.level0_5
		pass
		# set the progress
		start_progress=20
		# counter for computing progress	
		count=0
		# From Level 0.5 to Level 1
		level1=Level1Context(obsid)
		bbids=level0_5.getBbids(0xa103)
		nlines=len(bbids)
		scanle= Int1d(nlines)
		print "number of scan lines:",nlines
		ilen=0
		for bbid in bbids:
			block=level0_5.get(bbid)
			print "processing BBID="+hex(bbid)
			pdt  = block.pdt
			nhkt = block.nhkt
			if pdt == None:
				logger.severe("Building block "+hex(bbid)+" doesn't contain a PDT. Cannot process this building block.")
				print "Building block "+hex(bbid)+" doesn't contain a PDT. Cannot process this building block."
				continue
			if nhkt == None:
				logger.severe("Building block "+hex(bbid)+" doesn't contain a NHKT. Cannot process this building block.")
				print "Building block "+hex(bbid)+" doesn't contain a NHKT. Cannot process this building block."
				continue
			bbCount=bbid & 0xFFFF
			pdtLead=None
			nhktLead=None
			pdtTrail=None
			nhktTrail=None
			if bbCount >1:
				blockLead=level0_5.get(0xaf000000L+bbCount-1)
				pdtLead=blockLead.pdt
				nhktLead=blockLead.nhkt
			if pdtLead != None and pdtLead.sampleTime[-1] < pdt.sampleTime[0]-3.0:
				pdtLead=None
				nhktLead=None
			if bbid < MAX(Long1d(bbids)):
				blockTrail=level0_5.get(0xaf000000L+bbCount)
				pdtTrail=blockTrail.pdt
				nhktTrail=blockTrail.nhkt
			if pdtTrail != None and pdtTrail.sampleTime[0] > pdt.sampleTime[-1]+3.0:
				pdtTrail=None
				nhktTrail=None
			pdt=joinPhotDetTimelines(pdt,pdtLead,pdtTrail)
			nhkt=joinNhkTimelines(nhkt,nhktLead,nhktTrail)
			bat=calcBsmAngles(nhkt,bsmPos=bsmPos)
			spp=createSpirePointing(detAngOff=detAngOff,bat=bat,hpp=hpp,siam=siam)
			pdt=elecCrossCorrection(pdt,elecCross=elecCross)
			processingVersion = pdt['History']['HistoryTasks']['BuildVersion'].data[0]
			processingDescription = pdt['History']['HistoryTasks']['BuildVersion'].description
			productDescription = pdt.meta['creator'].description
			productVersion = pdt.meta['creator'].string[24:40]
			fluxConv=fluxConvList.getProduct(pdt.meta["biasMode"].value,pdt.startDate)
			pdt=photFluxConversion(pdt,fluxConv=fluxConv)
			tempDriftCorr=tempDriftCorrList.getProduct(pdt.meta["biasMode"].value,pdt.startDate)
			pdt=temperatureDriftCorrection(pdt,tempDriftCorr=tempDriftCorr)
			pdt=photOptCrossCorrection(pdt,optCross=optCross)
			psp=associateSkyPosition(pdt,spp=spp)
			psp2=cutPhotDetTimelines(psp)
			len_notur=len(psp2.getSignal("PSWE4"))
			psp=cutPhotDetTimelines(psp,extend=True)
			len_tur=len(psp.getSignal("PSWE4"))
			scanle[ilen]=(len_tur-len_notur)
			ilen=ilen+1
			if tempStorage:
				ref=ProductSink.getInstance().save(psp)
				level1.addRef(ref)
			else:
				level1.addProduct(psp)
				print "Completed BBID=0x%x (%i/%i)"%(bbid,count+1,nlines)
				count=count+1
				start_progress = 20+(60*count)/nlines
				#
			if level1.count == 0:
				logger.severe("No scan line processed due to missing data. This observation CANNOT be processed!")
				print "No scan line processed due to missing data. This observation CANNOT be processed!"
				raise MissingDataException("No scan line processed due to missing data. This observation CANNOT be processed!")
						#
		return level1, scanle

uniHipe=UniHipeTask()
toolRegistry = TaskToolRegistry.getInstance()
toolRegistry.register(uniHipe, [Category.SPIRE, Category.PACS]) # 2
del(toolRegistry)