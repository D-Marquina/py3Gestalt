"""Gestalt framework for Python 3's GUI

This module extends Gestalt Framework for Python 3's usability by creating a
GUI that allows the user to select a defined virtual machine, available
interface and test communication status.

Copyright (c) 2018 Daniel Marquina
"""

import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
import serial
import shutil
import glob
import sys
import os

kivy.require('1.0.1')


class Py3GestaltGUIApp(App):
    """Gestalt framework for Python 3's GUI application class

    Personalized class based on kivy.app class.
    """
    title = StringProperty("Gestalt Framework for Python 3")

    def build(self):
        """Overrides default build method.

        Returns:
            Py3GestaltGUI: Kivy's box layout, root widget of this app.
        """
        self.load_kv('gui.kv')
        return Py3GestaltGUI()


class Py3GestaltGUI(BoxLayout):
    """ Gestalt framework for Python 3's GUI's main layout class

    This layout contains 4 sections:
        - Virtual machine selection
        - Interface selection
        - Machine recognition
        - Debugger output

    Attributes:
        vm_bt_load (Button): Virtual machine section's 'Load' button
        vm_fb (VirtualMachineBrowser): Virtual machine section's file browser
        vm_vm_source_file (str): Virtual machine's definition file's direction
        inf_sp (Spinner): Interface section's spinner
        inf_bt_connect (Button): Interface section's 'Connect' button
        debugger_lb (Label): Debugger output
    """
    vm_bt_load = ObjectProperty(Button())
    inf_sp = ObjectProperty(Spinner())
    inf_bt_connect = ObjectProperty(Button())
    debugger_lb = ObjectProperty(Label())

    def __init__(self):
        super(Py3GestaltGUI, self).__init__()
        self.vm_fb = VirtualMachineBrowser()
        self.vm_source_file = None

    def open_file_browser(self):
        """Open a file browser including a reference to this GUI"""
        self.vm_fb.open(self)

    def load_virtual_machine(self):
        """Load virtual machine definition

        Makes a directory called 'tmp', copies the virtual machine's
        definition into a file called 'temp_virtual_machine' and imports such
        file.
        """
        temp_vm_location = os.path.join('tmp', 'temp_virtual_machine.py')
        if os.path.exists('tmp'):
            shutil.rmtree('tmp', ignore_errors=True)
        os.makedirs('tmp')
        init_file = open(os.path.join('tmp', '__init__.py'), 'w')
        init_file.close()
        temp_vm_file = open(temp_vm_location, 'w')
        shutil.copyfile(self.vm_source_file, temp_vm_location)
        temp_vm_file.close()
        __import__('tmp.temp_virtual_machine')
        with open(self.vm_source_file, 'r') as stream:
            self.debugger_lb.text += stream.read()
        self.inf_bt_connect.disabled = False

    def load_ports(self):
        """Loads available ports into interface section's spinner.

        Note: When using glob, your current terminal "/dev/tty" is excluded.
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        available_ports = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                available_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        self.inf_sp.values = available_ports

    def connect_to_machine(self):
        """initialize virtual machine."""
        print(self.inf_sp.text)

    def check_status(self):
        """Checks status of real machine."""
        pass


class VirtualMachineBrowser(Popup):
    """File browser class

    Definition of a file browser based on kivy's FileChooserListView.
    """
    title = StringProperty('Select your virtual machine definition')

    def __init__(self):
        super(VirtualMachineBrowser, self).__init__()
        self.parent_gui = None

    def open(self, gui):
        """Overrides open() function

        This function pops up the file browser and defines parent GUI.

        Arguments:
            gui: GUI that instantiated this class, aka parent GUI.
        """
        super(VirtualMachineBrowser, self).open()
        self.parent_gui = gui

    def select_virtual_machine(self, path, filename):
        """Select virtual machine's definition file

        Gives parent GUI the path and filename of virtual machine's definition
        file. Also, writes file's name and content in parent GUI's debugger.
        Last, enables parent GUI's 'Load' button.

        Arguments:
            path (str): Current working directory, more information on Kivy's
                        FileChooser's reference.
            filename (str): Name of selected file.
        """
        self.parent_gui.vm_source_file = os.path.join(path, filename)
        self.parent_gui.debugger_lb.text += filename + '\n' + '\n'
        self.parent_gui.vm_bt_load.disabled = False
        self.dismiss()


if __name__ == '__main__':
    Py3GestaltGUIApp().run()
