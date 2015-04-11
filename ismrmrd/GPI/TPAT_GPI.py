#
# 
# Example of using ismrmrd-python-tools to do TPAT (TSENSE or TGRAPPA) in GPI
#

# Author: Michael S. Hansen (michael.hansen@nih.gov)
# Date: 2015 Apr 07

import gpi
import ismrmrd.xsd
from ismrmrdtools import coils,  sense, transform, grappa
import numpy as np

class ExternalNode(gpi.NodeAPI):
    '''Simple Node for doing TSENSE or TGRAPPA
    '''

    def initUI(self):
        # Widgets
        self.addWidget('ExclusiveRadioButtons', 'Parallel Imaging Method', buttons=['GRAPPA', 'SENSE'], val=0)

        # IO Ports
        self.addInPort('data', 'NPYarray')
        self.addInPort('ISMRMRDHeader', 'STRING')
        
        self.addOutPort('recon', 'NPYarray')
        self.addOutPort('gmap', 'NPYarray')
        
        return 0

    def compute(self):
        
        all_data = self.getData('data')
        xml_header = self.getData('ISMRMRDHeader')

        header = ismrmrd.xsd.CreateFromDocument(xml_header)
        enc = header.encoding[0]

        #Parallel imaging factor
        acc_factor = 1
        if enc.parallelImaging:
            acc_factor = enc.parallelImaging.accelerationFactor.kspace_encoding_step_1
        
        # Coil combination
        print "Calculating coil images and CSM"
        coil_images = transform.transform_kspace_to_image(np.squeeze(np.mean(all_data,0)),(1,2))
        (csm,rho) = coils.calculate_csm_walsh(coil_images)
        csm_ss = np.sum(csm * np.conj(csm),0)
        csm_ss = csm_ss + 1.0*(csm_ss < np.spacing(1)).astype('float32')
        
        if acc_factor > 1:
            coil_data = np.squeeze(np.mean(all_data,0))
            
            if self.getVal('Parallel Imaging Method') == 0:
                (unmix,gmap) = grappa.calculate_grappa_unmixing(coil_data, acc_factor,csm=csm)
            elif self.getVal('Parallel Imaging Method') == 1:
                (unmix,gmap) = sense.calculate_sense_unmixing(acc_factor,csm)
            else:
                raise Exception('Unknown parallel imaging method')

        recon = np.zeros((all_data.shape[-4],all_data.shape[-2],all_data.shape[-1]), dtype=np.complex64)
        
        for r in range(0,all_data.shape[-4]):
            recon_data = transform.transform_kspace_to_image(np.squeeze(all_data[r,:,:,:]),(1,2))*np.sqrt(acc_factor)
            if acc_factor > 1:
                recon[r,:,:] = np.sum(unmix * recon_data,0)
            else:
                recon[r,:,:] = np.sum(np.conj(csm) * recon_data,0)

        print "Reconstruction done"
        
        self.setData('recon', recon)
        
        if acc_factor == 1:
            gmap = np.ones((all_data.shape[-2],all_data.shape[-1]),dtype=np.float32)
            
        self.setData('gmap',gmap)

        return 0
