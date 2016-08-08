import help
from herschel.ia.toolbox.util.jython import saveObservation
from herschel.ia.numeric import String1d
from herschel.pacs.spg.common import ActivateMasksTask
from herschel.pacs.spg.pipeline import UpdatePacsObservationTask
activateMasks = ActivateMasksTask()
updatePacsObservation = UpdatePacsObservationTask()

def deactivatemask(poolname, camera):

  obses = help.getallobscontexts(poolname)

  for obs in obses:

    level1 = PacsContext(obs.level1)
    frames = level1.averaged.getCamera(camera).product
      
    frames.removeMask('badprobs')
      
    obs = updatePacsObservation(obs, 1.0, frames)
      
    saveObservation(obs, poolName = poolname)

  return
