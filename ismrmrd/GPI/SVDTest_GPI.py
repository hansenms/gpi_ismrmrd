# Toy example to illustrate crashing when running nodes as process on Mac
#

# Author: Michael S. Hansen
# Date: April 10, 2015

import gpi
import numpy as np

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

        # Widgets
        self.addWidget('PushButton', 'MyPushButton', toggle=True)

        self.addWidget('ExclusiveRadioButtons', 'Execution Type',
                       buttons=['Thread', 'Process', 'Main Loop'],
                       val=1, collapsed=True)
        # IO Ports
        self.addInPort('in1', 'NPYarray')
        self.addOutPort('out1', 'NPYarray')

        return 0

    def compute(self):

        data = self.getData('in1')

        print "Testing SVD"
        a = np.random.randn(1000, 400) + 1j*np.random.randn(1000, 400)
        s= np.linalg.svd(a, compute_uv=False)
        print "Done testing SVD"

        # algorithm code...

        self.setData('out1', data)

        return 0
