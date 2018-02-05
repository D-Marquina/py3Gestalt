"""Virtual Machine for Testing

For now, this virtual machine is only initialized and displays its attributes.
In Ilan Moyer's original Gestalt Framework, a virtual machine was executed
directly from console, but now it can be also executed from a GUI.

Copyright (c) 2018 Daniel Marquina
"""

import py3gestalt.machines as machines
import py3gestalt.interfaces as interfaces
import py3gestalt.nodes as nodes
from py3gestalt.utilities import notice as notice

import test_node as TestNode


class TestVirtualMachine(machines.VirtualMachine):
    def __init__(self, *args, **kwargs):
        # Nodes should be declared here, before calling super().__init__
        self.test_node = None
        super(TestVirtualMachine,
              self).__init__(*args, **kwargs)
        self.publish_settings()

    def publish_settings(self):
        init_message = ''
        if self.name:
            init_message += "Name: " + self.name + '\n'
        if self.interface:
            init_message += "Provided interface: True" + '\n'
        else:
            init_message += "Provided interface: False" + '\n'
        if self.persistenceFilename:
            init_message += "Persistence file: " + self.persistenceFilename + '\n'
        else:
            init_message += "Persistence file: False" + '\n'
        notice(self, init_message)

    def init_controllers(self):
        super(TestVirtualMachine, self).init_controllers()
        self.test_node = nodes.BaseNodeShell(self, 'Test Node')
        # Any of this lines should work, one at a time
        self.test_node.load_vn_from_module(TestNode)
        # self.test_node.load_vn_from_file('examples\\test\\test_node.py')
        # Provided URL would change in time, it redirects to the actual version
        # of 'test_node_without_GUI.py'
        # self.test_node.load_vn_from_url(
            # 'https://raw.githubusercontent.com/D-Marquina/py3Gestalt/master/test_node_without_GUI.py')


# If executing from console (Needed?):
if __name__ == '__main__':
    TestVirtualMachine(name='Testing Machine',
                       persistenceFile='test.vmp',
                       interface=interfaces.InterfaceShell(owner=None))
