"""Virtual Machine for Testing without a GUI

This virtual machine is intended to be run from console, its purpose is to find
problems or incongruities between the use of GUI or console. After all, this
framework was originally intended to be run from console.

Eventually, this file wil be moved to examples.

Copyright (c) 2018 Daniel Marquina
"""

import py3gestalt.machines as machines
import py3gestalt.interfaces as interfaces
import py3gestalt.nodes as nodes
from py3gestalt.utilities import notice as notice
import time
import os

# import test_node_without_GUI as TestNode


class TestVirtualMachine(machines.VirtualMachine):
    def __init__(self, *args, **kwargs):
        # All nodes should be declared here
        self.test_node = None
        super(TestVirtualMachine,
              self).__init__(*args, **kwargs,)
        self.publish_settings()

    def publish_settings(self):
        init_message = ''
        init_message += '\n' + 'Settings:' + '\n'
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

    def init_interfaces(self):
        """Initializes a serial interface."""
        self.set_interface(interfaces.InterfaceShell(owner=self))
        self.interface.set(interfaces.SerialInterface(owner=self,
                                                      baud_rate=9600,
                                                      port_name='COM7',
                                                      interface_type='arduino'))

    def init_controllers(self):
        self.test_node = nodes.BaseNodeShell(self, 'Test Node')
        # self.test_node.is_vn_ill_defined('test_node_without_GUI')
        # self.test_node.load_vn_from_module(TestNode)
        self.test_node.load_vn_from_file('test_node_without_GUI.py')
        # self.test_node.load_vn_from_file('examples\\test\\test_node.py')
        # self.test_node.load_vn_from_url(
            #'https://raw.githubusercontent.com/d-marquina/py3gestalt/master/test_node_without_GUI.py')
        pass


# When executing from console:
if __name__ == '__main__':
    my_machine = TestVirtualMachine(name='Testing Machine',
                                    persistenceFile='test.vmp')
    time.sleep(1)
    # my_machine.interface.do()
    my_machine.test_node.do()
