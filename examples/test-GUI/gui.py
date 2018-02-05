"""A Gestalt framework for Python 3's GUI.

This module extends Gestalt Framework for Python 3's usability by creating a
GUI that allows the user to select a defined virtual machine, available
interface and test communication status.

-'Py3GestaltGUIApp':
    Main app.
- 'Py3GestaltGUI':
    Main box layout.
- 'VirtualMachineBrowser':
    A browser that filters out non-Python files
- 'DebugGUIHandler':
    Custom handler that prints logging messages in debugger label.

Note:
    This GUI requires Kivy.

Copyright (c) 2018 Daniel Marquina
"""

from py3gestalt import interfaces
from py3gestalt.utilities import get_available_serial_ports
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
import importlib
import logging
import inspect
import pyclbr
import serial
import shutil
import time
import glob
import sys
import os

# Kivy requirements
kivy.require('1.0.1')

# Logging configuration
log = logging.getLogger("Virtual Machine")
log.level = logging.DEBUG


class Py3GestaltGUIApp(App):
    """Gestalt framework for Python 3's GUI application class.

    Builds a Py3GestaltGUI object. Visual settings are located in 'gui.kv'.
    """
    title = StringProperty("Gestalt Framework for Python 3")

    def build(self):
        """Overrides default build method.

        Returns:
            Py3GestaltGUI: Kivy's box layout, main widget of this app.
        """
        self.load_kv('gui.kv')
        return Py3GestaltGUI()


class Py3GestaltGUI(BoxLayout):
    """ Gestalt framework for Python 3's GUI's main layout class.

    This layout contains 4 sections:
        - Virtual machine selection,
        - Interface selection,
        - Machine recognition,
        - Debugger output.

    Attributes:
        vm_bt_search (Button): Virtual machine section's 'Search' button.
        vm_bt_import (Button): Virtual machine section's 'Import' button.
        vm_fb (VirtualMachineBrowser): Virtual machine section's file browser.
        vm_source_file (str): Virtual machine's definition file's direction.
        vm_class (class): User defined virtual machine class.
        vm(vm_class): Instantiation of user defined virtual machine.
        int_sp (Spinner): Interface section's spinner.
        int_bt_connect (Button): Interface section's 'Connect' button.
        debugger_lb (Label): Debugger output.
    """
    vm_bt_search = ObjectProperty(Button())
    vm_bt_import = ObjectProperty(Button())
    int_sp = ObjectProperty(Spinner())
    int_bt_connect = ObjectProperty(Button())
    debugger_lb = ObjectProperty(Label())

    def __init__(self):
        super(Py3GestaltGUI, self).__init__()
        self.vm_fb = VirtualMachineBrowser()
        self.vm_source_file = None
        self.vm_class = None
        self.vm = None
        self.import_counter = 0
        log.addHandler(DebugGUIHandler(self.debugger_lb, logging.DEBUG))

    def open_file_browser(self):
        """Open a file browser including a reference to this GUI."""
        self.vm_fb.open(self)

    def import_virtual_machine(self):
        """Import virtual machine definition.

        Makes a copy of the user's virtual machine into a folder called 'tmp',
        imports it as a module inside a package and creates a reference to
        its user-defined virtual machine class.
        Besides, virtual machine section's buttons are disabled.

        Returns:
            None if virtual machine is ill defined.
        """
        self.import_counter += 1

        vm_module = self.create_vm_module()

        if self.is_vm_ill_defined(vm_module):
            self.int_bt_connect.disabled = True
            return

        vm_imported_module = importlib.import_module(vm_module)
        for name in dir(vm_imported_module):
            cls = getattr(vm_imported_module, name)
            if inspect.isclass(cls):
                if "VirtualMachine" in str(cls.__mro__[-2]):
                    self.vm_class = cls

        package = 'tmpVM'
        if os.path.exists(package):
            shutil.rmtree(package, ignore_errors=True)

        with open(self.vm_source_file, 'r') as vm_definition:
            self.write_debugger(vm_definition.read())

        self.vm_bt_search.disabled = True
        self.vm_bt_import.disabled = True
        self.int_bt_connect.disabled = False

    def create_vm_module(self):
        """Create user-defined virtual machine module.

        Makes a temporal package (directory with an '__init__.py' file) called
        'tmp' with a temporal module (file) which is a copy of the user-defined
        virtual machine.
        They are assessed as 'temporal' because they are deleted every time an
        import action is attempted.

        Note:
        The module's name is 'temp_virtual_machine_X.py', where 'X' is the
        number of import attempts. Such change of name is necessary in order
        to avoid problems next, when analyzing module's classes using 'pyclbr'.

        Returns:
            module_object: Temporal module's name.
        """
        package = 'tmpVM'
        if os.path.exists(package):
            shutil.rmtree(package, ignore_errors=True)
        os.makedirs(package)
        open(os.path.join(package, '__init__.py'), 'w').close()

        module_name = 'temp_virtual_machine_' + str(self.import_counter)
        module_location = os.path.join(package, module_name + '.py')
        open(module_location, 'w').close()
        shutil.copyfile(self.vm_source_file, module_location)
        module_object = package + '.' + module_name

        return module_object

    def is_vm_ill_defined(self, vm_module):
        """Check whether a virtual machine is well or ill defined.

        Makes sure that selected virtual machine contains one and only one
        user-defined virtual machine class, child of py3Gestalt's
        'machines.VirtualMachine' class.

        Args:
            vm_module: Virtual Machine module to be analyzed

        Returns:
            True when selected module contains none or more than a unique
            virtual machine. False otherwise.
        """
        num_of_vm_cls = 0
        for name, class_data in sorted(pyclbr.readmodule(vm_module).items(),
                                       key=lambda x: x[1].lineno):
            if class_data.super[0] == 'machines.VirtualMachine':
                num_of_vm_cls += 1

        if num_of_vm_cls == 0:
            self.write_debugger("Error: No virtual machine defined." + '\n' +
                                "Select a new file.")
            return True
        elif num_of_vm_cls > 1:
            self.write_debugger("Error: More than a unique virtual " +
                                "machine defined in a single file." + '\n' +
                                "Select a new file.")
            return True

        self.write_debugger("Virtual machine correctly defined.")

        return False

    def load_ports(self):
        """Loads available ports into interface section's spinner.

        Calls utilities.get_available_ports().
        """
        self.int_sp.values = get_available_serial_ports()

    def connect_to_machine(self):
        """Connect to virtual machine.

        Instantiate a user-defined virtual machine and changes the current
        working directory to where its original virtual machine's file is
        located.
        Besides, interface section's buttons are disabled.
        """
        self.vm = self.vm_class(name='Testing Machine', persistenceFile='test.txt')
        self.vm.set_interface(interfaces.InterfaceShell(owner=self.vm))
        self.vm.interface.set(interfaces.SerialInterface(owner=self.vm,
                                                         baud_rate=9600,
                                                         port_name=self.int_sp.text,
                                                         interface_type='arduino'))
        os.chdir(os.path.dirname(self.vm_source_file))
        self.int_sp.disabled = True
        self.int_bt_connect.disabled = True

    def check_status(self):
        """Check status of real machine.

        In this stage of Py3Gestalt's development, this function just sends an
        'a' and shows what was the answer from an Arduino that was programmed
        to re-send every incoming character and to toggle built-in led when
        an 'a' was received.
        """
        # self.vm.interface.transmit('a')
        time.sleep(0.05)
        # self.write_debugger('Message: ' +
                            # self.vm.interface.read_bytes(30).decode('utf-8'))
        # log.warning("It does print.")
        self.vm.test_node.do()

    def write_debugger(self, message):
        """Print in debugging section."""
        self.debugger_lb.text += message + '\n\n'


class VirtualMachineBrowser(Popup):
    """Virtual machine browser class.

    Definition of a file browser based on Kivy's FileChooserListView.

    Attributes:
        parent_gui (Py3GestaltGUI): GUI that initializes this browser.
    """
    title = StringProperty('Select your virtual machine definition')

    def __init__(self):
        super(VirtualMachineBrowser, self).__init__()
        self.parent_gui = None

    def open(self, parent_gui):
        """Overrides 'open()' function.

        This function pops up the file browser and defines parent GUI.

        Arguments:
            parent_gui: GUI that instantiated this class, aka parent GUI.
        """
        super(VirtualMachineBrowser, self).open()
        self.parent_gui = parent_gui

    def select_virtual_machine(self, path, filename):
        """Select virtual machine's definition file.

        Gives parent GUI the path and filename of virtual machine's definition
        file. Also, writes file's name and content in parent GUI's debugger.
        Last, enables parent GUI's 'Load' button.

        Arguments:
            path (str): Current working directory, more information on Kivy's
                        FileChooser's reference.
            filename (str): Name of selected file.
        """
        self.parent_gui.vm_source_file = ''
        self.parent_gui.vm_source_file = os.path.join(path, filename)
        self.parent_gui.write_debugger(filename)
        self.parent_gui.vm_bt_import.disabled = False
        self.dismiss()


class DebugGUIHandler(logging.Handler):
    """A handler for logging.

    This handler shows notices in GUI's debugging section' label. It must be
    assigned to the Logger.

    Args:
        label (Label): Label where notices will be displayed.
        level: Logging level setting.
    """

    def __init__(self, label, level=logging.NOTSET):
        logging.Handler.__init__(self, level=level)
        self.label = label

    def emit(self, record):
        """Overrides default 'emit' method.

        It uses the Clock module for thread safety with Kivy's main loop.
        """
        def f(dt=None):
            self.label.text += self.format(record) + '\n\n'
        Clock.schedule_once(f)


if __name__ == '__main__':
    Py3GestaltGUIApp().run()
