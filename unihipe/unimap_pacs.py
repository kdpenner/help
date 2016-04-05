def unimap_pacs(frames,calTree,camera=''):
    from herschel.ia.toolbox.util import SimpleFitsReaderTask
    from herschel.ia.numeric import Int1d
    from herschel.ia.numeric import Float1d
    from herschel.ia.numeric import Float2d
    from herschel.ia.numeric import Bool2d
    from herschel.ia.numeric import Int2d
    from herschel.ia.numeric import Range
    from herschel.ia.numeric import Selection
    from herschel.pacs.spg.phot import photAssignRaDec
    from herschel.pacs.signal.context import PacsContext
    from herschel.pacs.cal import PacsCal
    from herschel.pacs.spg.phot import ConvertToFixedPixelSizeTask

#-the standard level1 product has not the coordinetes assigned (AssignRaDecTask)

    convertToFixedPixelSize=ConvertToFixedPixelSizeTask()
    if camera == 'blue':
        bol = 2048
        pix_size = 3.2
        n_row = 32
    else:
        bol = 512
        pix_size = 6.4
        n_row = 16

    frames = frames.refs[0].product

    if 'badprobs' in frames.activeMaskNames:
    
      gyroprob = frames.getMask('badprobs')[0,0,:]

    # when the gyro probability is bad for one bolometer it is bad for all
    # bolometers. we find the bad pointing times only once.

      goodprobs = gyroprob.where(gyroprob == False)
      goodprobssize = goodprobs.toInt1d().size
      
    else:

      goodprobssize = frames['Signal'].data.dimensions[2]
      goodprobs = Selection(Int1d.range(goodprobssize))



    scanning_flag = Int1d(frames.dimensions[2])

######Select the telescope scanning    

    start_ind = frames['BlockTable']['StartIdx'].data
    end_ind = frames['BlockTable']['EndIdx'].data
    id = frames['BlockTable']['Id'].data
    start_scan = start_ind.where(id == "PHOT_SCANMODE").toInt1d()
    end_scan = end_ind.where(id == "PHOT_SCANMODE").toInt1d()
    is_scan = Range(start_ind[start_scan[0]], end_ind[end_scan[0]])
    scanning_flag[is_scan] = 1
    index = 2
    for i in range(len(start_scan)-1):
        is_scan = Range(start_ind[start_scan[i+1]], end_ind[end_scan[i+1]])
        scanning_flag[is_scan] = index
        index = index + 1
        
    scanning_flag = scanning_flag[goodprobs]
        
    frames = convertToFixedPixelSize(frames, calTree=calTree)[0]
    frames = photAssignRaDec(frames, calTree=calTree)

####################################### 
    px = (pix_size / 3600.)**2
    sr = 57.2957795131**2
    f = (sr/px) * 1e-6
    signal = (frames['Signal'].data * f)[:,:,goodprobs]
    ra = frames['Ra'].data[:,:,goodprobs]
    dec = frames['Dec'].data[:,:,goodprobs]
    sat = frames.getMask("SATURATION")[:,:,goodprobs]

    bad = frames.getMask("BADPIXELS")[:,:,0]

    s = Float2d() #signal
    r = Float2d()
    d = Float2d()
    f = Int2d()
    gb = Int1d()
    index = 1

    for i_column in range(signal.dimensions[1]):
        print 'PACS frames: column', i_column
        for i_row in range(signal.dimensions[0]):
             if bad[i_row,i_column] == False:
                 gb.append(index)
                 pixel_I = Float1d(signal[i_row,i_column,:])
                 s.append(pixel_I,1)
                 pixel_Ra = Float1d(ra[i_row,i_column,:])
                 r.append(pixel_Ra,1)
                 pixel_Dec = Float1d(dec[i_row,i_column,:])
                 d.append(pixel_Dec,1)
                 ind = sat[i_row,i_column,:].where(sat[i_row,i_column,:] == True)
                 pixel_Flag = Int1d(goodprobssize)
                 pixel_Flag[ind] = 1
                 f.append(pixel_Flag,1)
             else:
                 print 'PACS frames: pixel', i_column, i_row, 'is a bad detector!!'
             index = index + 1

    sample = Int1d(len(gb))
    sample[:] = goodprobssize
    return s,r,d,f,gb,Int1d().append(bol),Int1d().append(scanning_flag), sample
