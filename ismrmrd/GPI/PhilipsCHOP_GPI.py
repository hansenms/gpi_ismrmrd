# GPI (v0.5.0-n1) auto-generated library file.
#
# FILE: /Users/hansenms/gpi/hansenms/default/GPI/MyNode_GPI.py
#
# For node API examples (i.e. widgets and ports) look at the
# core.interfaces.Template node.

import gpi
import numpy as np

class ExternalNode(gpi.NodeAPI):
    '''About text goes here...
    '''

    def initUI(self):

        # IO Ports
        self.addInPort('in', 'NPYarray')
	self.addOutPort('out', 'NPYarray')

        return 0

    def compute(self):

        data = self.getData('in')

        mask = np.ones((data.shape[-2],data.shape[-1]))-2*(np.asarray(range(0,data.shape[-2])).reshape(data.shape[-2],1)%2)
	self.setData('out',data*mask)
	
        return 0
