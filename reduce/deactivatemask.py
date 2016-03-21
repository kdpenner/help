import help

def deactivatemask(poolname, camera):

  obses = help.getallobscontexts(poolname)

  for obs in obses:
    if obs.obsid in [1342186610, 1342186611, 1342186625, 1342186626, \
    1342186627, 1342186628, 1342187058, 1342187059, 1342187060, 1342187061, \
    1342188073, 1342188074]:

      level1 = PacsContext(obs.level1)
      frames = level1.averaged.getCamera(camera).product.getScience(0)
      
      frames = activateMasks(frames, String1d(['badprobs']), activate = False)
      
      level1.averaged.getCamera(camera).product.replace(0, frames)
      
      obs = updatePacsObservation(obs, 1.0, frames)
      
      saveObservation(obs, poolName = poolname)

  return
