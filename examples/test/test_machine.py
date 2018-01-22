"""Virtual Machine for Testing

For now, this virtual machine is only initialized and displays its attributes.
In Ilan Moyer's original Gestalt Framework, a virtual machine was executed
directly from console, but now it can be also executed from a GUI.

Copyright (c) 2018 Daniel Marquina
"""

import machines
import interfaces
import nodes
from utilities import notice as notice
import test_node_without_GUI as TestNode


class TestVirtualMachine(machines.VirtualMachine):
    def __init__(self, *args, **kwargs):
        # Nodes should be declared here, before calling super().__init__
        self.test_node = None
        super(TestVirtualMachine,
              self).__init__(*args, **kwargs)
        self.publish_settings()

    def publish_settings(self):
        init_message = ''
        if self.use_debug_gui:
            init_message += 'Settings:' + '\n'
        else:
            init_message += '\n' + 'Settings:' + '\n'
        if self.name:
            init_message += "Name: " + self.name + '\n'
        if self.interface:
            init_message += "Provided interface: True" + '\n'
        else:
            init_message += "Provided interface: False" + '\n'
        if self.use_debug_gui:
            init_message += "GUI: " + str(self.use_debug_gui) + '\n'
        if self.persistenceFilename:
            init_message += "Persistence file: " + self.persistenceFilename + '\n'
        else:
            init_message += "Persistence file: False" + '\n'
        notice(self, init_message, self.use_debug_gui)

    def init_controllers(self):
        super(TestVirtualMachine, self).init_controllers()
        self.test_node = nodes.BaseNodeShell(self, 'Test Node')
        # self.test_node.load_vn_from_module(TestNode)
        self.test_node.load_vn_from_file('examples\\test\\test_node.py')



# If executing from console (Needed?):
if __name__ == '__main__':
    TestVirtualMachine(name='Testing Machine',
                       persistenceFile='test.vmp',
                       interface=interfaces.InterfaceShell(owner=None))
