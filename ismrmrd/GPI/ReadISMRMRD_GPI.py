#
# Node for reading the ISMRMRD (http://ismrmrd.github.io) format
#

#
# Author: Michael S. Hansen (michael.hansen@nih.gov)
# Date: 2015 Apr 07

import os
import gpi
import numpy as np
import ismrmrd
import ismrmrd.xsd
from ismrmrdtools import transform, coils

class ExternalNode(gpi.NodeAPI):
    '''This node is used to read ISMRMRD format and convert to a simple NPY array
    '''

    def initUI(self):
        # Widgets
        self.addWidget('OpenFileBrowser', 'File Browser',
                       button_title='Browse', caption='Open File', directory='~/',
                       filter='ismrmrd (*.h5)')

        self.addWidget('PushButton', 'Squeeze', button_title='Squeeze', toggle=True,val=True)
        self.addWidget('PushButton', 'Remove Oversampling', button_title='Remove oversampling', toggle=True, val=True)
        self.addWidget('PushButton', 'Zeropad', button_title='Zeropad (partial Fourier)', toggle=True, val=True)
        self.addWidget('PushButton', 'Noise Adjust', button_title='Noise Adjust (prewhitening)', toggle=True, val=True)
        self.addWidget('DoubleSpinBox', 'Receiver Noise BW Ratio', val=0.79, decimals=3, label='Receiver Noise BW Ratio')

        # IO Ports

        self.addOutPort('data', 'NPYarray')
        self.addOutPort('noise', 'NPYarray')
        self.addOutPort('ISMRMRDHeader','STRING')
        
        return 0
    def compute(self):

        do_squeeze = self.getVal('Squeeze')
        do_remos = self.getVal('Remove Oversampling')
        do_zeropad = self.getVal('Zeropad')
        do_noiseadj = self.getVal('Noise Adjust')
        receiver_noise_bw = self.getVal('Receiver Noise BW Ratio')

        #Get the file name use the file browser widget
        fname = gpi.TranslateFileURI(self.getVal('File Browser'))

        #Check if the file exists
        if not os.path.exists(fname):
            self.log.node("Path does not exist: "+str(fname))
            return 0
        
        dset = ismrmrd.Dataset(fname, 'dataset', create_if_needed=False)

        xml_header = dset.read_xml_header()
        header = ismrmrd.xsd.CreateFromDocument(xml_header)
        self.setData('ISMRMRDHeader', str(xml_header))

        enc = header.encoding[0]

        # Matrix size
        eNx = enc.encodedSpace.matrixSize.x
        eNy = enc.encodedSpace.matrixSize.y
        eNz = enc.encodedSpace.matrixSize.z
        rNx = enc.reconSpace.matrixSize.x
        rNy = enc.reconSpace.matrixSize.y
        rNz = enc.reconSpace.matrixSize.z

        # Field of View
        eFOVx = enc.encodedSpace.fieldOfView_mm.x
        eFOVy = enc.encodedSpace.fieldOfView_mm.y
        eFOVz = enc.encodedSpace.fieldOfView_mm.z
        rFOVx = enc.reconSpace.fieldOfView_mm.x
        rFOVy = enc.reconSpace.fieldOfView_mm.y
        rFOVz = enc.reconSpace.fieldOfView_mm.z

        # Number of Slices, Reps, Contrasts, etc.
        ncoils = header.acquisitionSystemInformation.receiverChannels
        if enc.encodingLimits.slice != None:
            nslices = enc.encodingLimits.slice.maximum + 1
        else:
            nslices = 1
            
        if enc.encodingLimits.repetition != None:
            nreps = enc.encodingLimits.repetition.maximum + 1
        else:
            nreps = 1
        
        if enc.encodingLimits.contrast != None:
            ncontrasts = enc.encodingLimits.contrast.maximum + 1
        else:
            ncontrasts = 1


        # In case there are noise scans in the actual dataset, we will skip them.
        noise_data = list()
        noise_dmtx = None
        
        firstacq=0
        for acqnum in range(dset.number_of_acquisitions()):
            acq = dset.read_acquisition(acqnum)
            
            if acq.isFlagSet(ismrmrd.ACQ_IS_NOISE_MEASUREMENT):
                noise_data.append((acq.getHead(),acq.data))
                continue
            else:
                firstacq = acqnum
                break    

        if len(noise_data):
            profiles = len(noise_data)
            channels = noise_data[0][1].shape[0]
            samples_per_profile = noise_data[0][1].shape[1]
            noise = np.zeros((channels,profiles*samples_per_profile),dtype=np.complex64)
            counter = 0
            for p in noise_data:
                noise[:,counter*samples_per_profile:(counter*samples_per_profile+samples_per_profile)] = p[1]
                counter = counter + 1
                
            self.setData('noise',noise)
            
            scale = (acq.sample_time_us/noise_data[0][0].sample_time_us)*receiver_noise_bw
            noise_dmtx = coils.calculate_prewhitening(noise,scale_factor=scale)
            noise_data = list()
            
        # Empty array for the output data
        acq = dset.read_acquisition(firstacq)
        ro_length = acq.number_of_samples
        padded_ro_length = (acq.number_of_samples-acq.center_sample)*2

        
        size_nx = 0
        if do_remos:
            size_nx = rNx
            do_zeropad = True
        elif do_zeropad:
            size_nx = padded_ro_length
        else:
            size_nx = ro_length
            
        all_data = np.zeros((nreps, ncontrasts, nslices, ncoils, eNz, eNy, size_nx), dtype=np.complex64)

        # Loop through the rest of the acquisitions and stuff
        for acqnum in range(firstacq,dset.number_of_acquisitions()):
            acq = dset.read_acquisition(acqnum)

            acq_data_prw = np.zeros(acq.data.shape,dtype=np.complex64)
            acq_data_prw[:] = acq.data[:]
            
            if do_noiseadj and (noise_dmtx is not None):
                acq_data_prw = coils.apply_prewhitening(acq_data_prw, noise_dmtx)
 
            data2 = None
            
            if (padded_ro_length != ro_length) and do_zeropad: #partial fourier
                data2 = np.zeros((acq_data_prw.shape[0], padded_ro_length),dtype=np.complex64)
                offset = (padded_ro_length>>1)  - acq.center_sample
                data2[:,0+offset:offset+ro_length] = acq_data_prw
            else:
                data2 = acq_data_prw

            if do_remos:
                data2=transform.transform_kspace_to_image(data2,dim=(1,))
                data2=data2[:,(padded_ro_length>>2):(padded_ro_length>>2)+(padded_ro_length>>1)]
                data2=transform.transform_image_to_kspace(data2,dim=(1,)) * np.sqrt(float(padded_ro_length)/ro_length)
                
            # Stuff into the buffer
            rep = acq.idx.repetition
            contrast = acq.idx.contrast
            slice = acq.idx.slice
            y = acq.idx.kspace_encode_step_1
            z = acq.idx.kspace_encode_step_2
            
            all_data[rep, contrast, slice, :, z, y, :] = data2
                
        all_data = all_data.astype('complex64')

        if do_squeeze:
            all_data = np.squeeze(all_data)

        
        self.setData('data',all_data)
        
        return 0
