"""Gestalt framework for Python 3's GUI

This module extends Gestalt Framework for Python 3's usability by creating a
GUI that allows the user to select a defined virtual machine, available
interface and test communication status.
"""

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, ObjectProperty
import serial
import sys


kivy.require('1.0.1')
#Config.set('graphics', 'width', '750')
#Config.set('graphics', 'height', '600')
#Config.write()


class Py3GestaltGUIApp(App):
    """Gestalt framework for Python 3's GUI application class

    Personalized class based on kivy.app class.

    Attributes:
        title (str): Title displayed
    """

    title = StringProperty("Gestalt Framework for Python 3")

    class Py3GestaltGUI(BoxLayout):
        """GUI's basic Layout

        This layout contains 4 sections:
            - Virtual machine selection
            - Interface selection
            - Machine recognition
            - Debugger output
        """

        virtual_machine_lt = ObjectProperty(BoxLayout())
        virtual_machine_lt_lb = ObjectProperty(Label())
        virtual_machine_lt_fbb = ObjectProperty(Button())
        virtual_machine_lt_bt = ObjectProperty(Button())

        interface_lt = ObjectProperty(BoxLayout())
        interface_lt_lb = ObjectProperty(Label())
        interface_lt_sp = ObjectProperty(Spinner())
        interface_lt_bt = ObjectProperty(Button())
        #btn2 = ObjectProperty(Button())

        class FileBrowser(Popup):
            title = StringProperty('Select your virtual machine definition')
            filebrowser_lt = ObjectProperty(BoxLayout())
            filebrowser_fc = ObjectProperty(FileChooserListView())
            filebrowser_bt_lt = ObjectProperty(Button())
            filebrowser_bt_load = ObjectProperty(Button())
            filebrowser_bt_cancel = ObjectProperty(Button())

            load = ObjectProperty(None)

            #def load_virtual_machine(self):
             #   print('Yahoo!')

        def select_virtual_machine(self):
            self.virtual_machine_fb = self.FileBrowser(load = self.load_virtual_machine).open()
            pass

        def load_virtual_machine(self, path, filename):
            pass

        def load_ports(self):
            """Loads available ports into interface section's spinner"""

            if sys.platform.startswith('win'):
                ports = ['COM%s' % (i + 1) for i in range(256)]
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                # this excludes your current terminal "/dev/tty"
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
            self.interface_lt_sp.values = available_ports

        def connect_to_machine(self):
            """Open specified serial port"""

            print(self.interface_lt_sp.text)

    def build(self):
        """Overrides default build method.

        Returns:
            Py3GestaltGUI: Kivy's box layout, root widget of this app.
        """

        self.load_kv('gui.kv')
        return self.Py3GestaltGUI()


if __name__ == '__main__':
    Py3GestaltGUIApp().run()
