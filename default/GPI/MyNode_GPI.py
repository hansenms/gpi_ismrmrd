# GPI (v0.5.0-n1) auto-generated library file.
#
# FILE: /Users/hansenms/gpi/hansenms/default/GPI/MyNode_GPI.py
#
# For node API examples (i.e. widgets and ports) look at the
# core.interfaces.Template node.

import gpi

class ExternalNode(gpi.NodeAPI):
    '''About text goes here...
    '''

    def initUI(self):
        # Widgets
        self.addWidget('PushButton', 'MyPushButton', toggle=True)

        # IO Ports
        self.addInPort('in1', 'NPYarray')
        self.addOutPort('out1', 'NPYarray')

        return 0

    def compute(self):

        data = self.getData('in1')

        # algorithm code...

        self.setData('out1', data)

        return 0