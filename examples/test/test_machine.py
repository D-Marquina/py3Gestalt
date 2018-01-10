"""Virtual Machine for Testing

This modules does nothing, for now.
"""

import machines
# import test_vn


class TestVirtualMachine(machines.VirtualMachine):
    def __init__(self, gui):
        super(TestVirtualMachine, self).__init__()
        self.gui = gui
        self.gui.debugger_lb.text += 'Loaded'

class AnotherTestVirtualMachine(machines.VirtualMachine):
    def __init__(self, gui):
        super(TestVirtualMachine, self).__init__()
        self.gui = gui
        self.gui.debugger_lb.text += 'Loaded'
