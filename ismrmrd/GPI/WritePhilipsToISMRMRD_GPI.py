# Node for Writing the data produced by the ReadPhilips node to
# the ISMRMRD format
#

#
# Author: Michael S. Hansen (michael.hansen@nih.gov)
# Date: 2015 Apr 12

import gpi
import numpy as np
import ismrmrd
import ismrmrd.xsd
import os

class ExternalNode(gpi.NodeAPI):
    '''About text goes here...
    '''

    def execType(self):
        # skip execType recursion by getting val from widget directly
        op = self.getWidget('Execution Type').get_val()
        if op == 0:
            return gpi.GPI_THREAD
        if op == 1:
            return gpi.GPI_PROCESS
        if op == 2:
            return gpi.GPI_APPLOOP
                                                                        
    def initUI(self):
        self.procType = gpi.GPI_PROCESS

        self.addWidget('ExclusiveRadioButtons', 'Execution Type',
                       buttons=['Thread', 'Process', 'Main Loop'],
                       val=1, collapsed=True)

        # IO Ports
        self.addInPort('data', 'NPYarray')
        self.addInPort('noise', 'NPYarray')
        #self.addInPort('pfc', 'NPYarray')
        self.addInPort('header', 'DICT')
        self.addInPort('filename', 'STRING')

        #self.addOutPort('out1', 'NPYarray')

        return 0

    def compute(self):

        data = self.getData('data')
        noise = self.getData('noise')
        header = self.getData('header')
        filename = self.getData('filename')
        
        #We will delete the file if it exists
        try:
            os.remove(filename)
        except OSError:
            pass
        
        #Expected dimension order"
        #nr_measured_channels
        #nr_dynamic_scans
        #nr_cardiac_phases
        #nr_echoes
        #nr_locations
        #nr_rows
        #nr_extra_attr_values
        #nr_measurements 
        #nr_e3_profiles
        #nr_e2_profiles
        #nr_e1_profiles
        #nr_samples

        dimension_keys = ['nr_measured_channels',
                          'nr_mixes',
                          'nr_dynamic_scans',
                          'nr_echoes',
                          'nr_cardiac_phases',
                          'nr_locations',
                          'nr_rows',
                          'nr_extra_attr_values',
                          'nr_measurements',
                          'nr_e3_profiles',
                          'nr_e2_profiles',
                          'nr_e1_profiles',
                          'nr_samples']
        
        sin = header['sin']
        lab = header['lab']
        
        data_dimensions = np.concatenate([[int(sin[x][0][0]) for x in dimension_keys[0:9]],[sin[x] for x in dimension_keys[9:]]])
        data = data.reshape(data_dimensions)

        # Open the dataset
        dset = ismrmrd.Dataset(filename, "dataset", create_if_needed=True)
    
        # Create the XML header and write it to the file
        header = ismrmrd.xsd.ismrmrdHeader()
    
        # Experimental Conditions
        exp = ismrmrd.xsd.experimentalConditionsType()
        exp.H1resonanceFrequency_Hz = 128000000
        header.experimentalConditions = exp
    
        # Acquisition System Information
        sys = ismrmrd.xsd.acquisitionSystemInformationType()
        sys.receiverChannels = data.shape[0]
        header.acquisitionSystemInformation = sys

        # Encoding
        encoding = ismrmrd.xsd.encoding()
        encoding.trajectory = ismrmrd.xsd.trajectoryType.cartesian
    
        # encoded and recon spaces
        ematrix = ismrmrd.xsd.matrixSize()
        ematrix.x = data.shape[-1]
        ematrix.y = data.shape[-2]
        ematrix.z = data.shape[-3]
        rmatrix = ismrmrd.xsd.matrixSize()
        rmatrix.x = int(sin['output_resolutions'][0][0])
        rmatrix.y = int(sin['output_resolutions'][0][1])
        rmatrix.z = int(sin['output_resolutions'][0][2])
        efov = ismrmrd.xsd.fieldOfView_mm()
        efov.x = ematrix.x * float(sin['voxel_sizes'][0][0])
        efov.y = rmatrix.y * float(sin['voxel_sizes'][0][1])
        efov.z = rmatrix.z * float(sin['voxel_sizes'][0][2])
        rfov = ismrmrd.xsd.fieldOfView_mm()
        rfov.x = rmatrix.x * float(sin['voxel_sizes'][0][0])
        rfov.y = rmatrix.y * float(sin['voxel_sizes'][0][1])
        rfov.z = rmatrix.y * float(sin['voxel_sizes'][0][2])
    

        espace = ismrmrd.xsd.encodingSpaceType()
        espace.matrixSize = ematrix
        espace.fieldOfView_mm = efov
        rspace = ismrmrd.xsd.encodingSpaceType()
        rspace.matrixSize = rmatrix
        rspace.fieldOfView_mm = rfov
    
        # Set encoded and recon spaces
        encoding.encodedSpace = espace
        encoding.reconSpace = rspace
    
        # Encoding limits
        limits = ismrmrd.xsd.encodingLimitsType()
    
        limits1 = ismrmrd.xsd.limitType()
        limits1.minimum = 0
        limits1.center = data.shape[-2]/2
        limits1.maximum = data.shape[-2]-1
        limits.kspace_encoding_step_1 = limits1
    
        limits2 = ismrmrd.xsd.limitType()
        limits2.minimum = 0
        limits2.center = data.shape[-3]/2
        limits2.maximum = data.shape[-3]-1
        limits.kspace_encoding_step_2 = limits2

        #limits3 = ismrmrd.xsd.limitType()
        #limits3.minimum = 0
        #limits3.center = data.shape[-4]/2
        #limits3.maximum = data.shape[-4]
        #limits.kspace_encoding_step_3 = limits3

        limits_average = ismrmrd.xsd.limitType()
        limits_average.minimum = 0
        limits_average.center = data.shape[-5]/2
        limits_average.maximum = data.shape[-5]-1
        limits.average = limits_average

        limits_slice = ismrmrd.xsd.limitType()
        limits_slice.minimum = 0
        limits_slice.center = data.shape[-8]/2
        limits_slice.maximum = data.shape[-8]-1
        limits.slice = limits_slice

        limits_contrast = ismrmrd.xsd.limitType()
        limits_contrast.minimum = 0
        limits_contrast.center = data.shape[-9]/2
        limits_contrast.maximum = data.shape[-9]-1
        limits.contrast = limits_contrast

        limits_phase = ismrmrd.xsd.limitType()
        limits_phase.minimum = 0
        limits_phase.center = data.shape[-10]/2
        limits_phase.maximum = data.shape[-10]-1
        limits.phase = limits_phase

        limits_rep = ismrmrd.xsd.limitType()
        limits_rep.minimum = 0
        limits_rep.center = data.shape[-11]/2
        limits_rep.maximum = data.shape[-11]-1
        limits.repetition = limits_rep
    
        limits_rest = ismrmrd.xsd.limitType()
        limits_rest.minimum = 0
        limits_rest.center = 0
        limits_rest.maximum = 0
        limits.segment = limits_rest
        limits.set = limits_rest
    
        encoding.encodingLimits = limits
        header.encoding.append(encoding)

        dset.write_xml_header(header.toxml('utf-8'))           
        
        # # Write out a few noise scans
        # for n in range(32):
        #     noise = noise_level * (np.random.randn(coils, nkx) + 1j * np.random.randn(coils, nkx))
        #     # here's where we would make the noise correlated
        #     acq.scan_counter = counter
        #     acq.clearAllFlags()
        #     acq.setFlag(ismrmrd.ACQ_IS_NOISE_MEASUREMENT)
        #     acq.data[:] = noise
        #     dset.append_acquisition(acq)
        #     counter += 1 # increment the scan counter

        acq = ismrmrd.Acquisition()
        acq.clearAllFlags()
        acq.version = 1
        acq.setFlag(ismrmrd.ACQ_IS_NOISE_MEASUREMENT)
        acq.available_channels = noise.shape[0]
        acq.resize(noise.shape[1],noise.shape[0])
        acq.data[:] = noise[:]
        dset.append_acquisition(acq)
        
        counter = 0
        for l in range(len(lab['control'])):
            if lab['label_type'][l] == 'LABEL_TYPE_STANDARD':
                if lab['control'][l] == 'CTRL_NORMAL_DATA':
                    counter += 1
                    acq = ismrmrd.Acquisition()
                    acq.clearAllFlags()
                    
                    acq.resize(data.shape[-1], data.shape[0])
                    acq.version = 1
                    acq.available_channels = data.shape[0]
                    acq.center_sample = data.shape[-1]/2
                    acq.read_dir[0] = 1.0
                    acq.phase_dir[1] = 1.0
                    acq.slice_dir[2] = 1.0

                    
                    e1 = int(lab['e1_profile_nr'][l])
                    e2 = int(lab['e2_profile_nr'][l])
                    e3 = int(lab['e3_profile_nr'][l])
                    meas = int(lab['measurement_nr'][l])
                    location = int(lab['location_nr'][l])
                    echo = int(lab['echo_nr'][l])
                    phase = int(lab['cardiac_phase_nr'][l])
                    dyn = int(lab['dynamic_scan_nr'][l])
                    mix = int(lab['mix_nr'][l])
                    row = int(lab['mix_nr'][l])
                    extra = int(lab['extra_attr_nr'][l])
                    acq.idx.kspace_encode_step_1 = e1
                    acq.idx.kspace_encode_step_2 = e2
                    acq.idx.contrast = echo
                    acq.idx.average = meas
                    acq.idx.repetition = dyn
                    acq.idx.slice = location
                    acq.idx.phase = phase
                    acq.data[:] = np.squeeze(data[:,mix,dyn,echo,phase,location,row,extra,meas,e3,e2,e1,:])

                    #TODO:
                    #Set some flags
                    #deal with ignored dimensions
                    #add some noise sample
                    #deal with orientation

                    dset.append_acquisition(acq)                
        return 0

    
