"""
TO-DO
- gui.Py3GestaltGUI:
    add print debugger method
- gui.VirtualMachineBrowser.select_virtual_machine():
    Evaluate whether file's extension is '.py' or not
- gui.Py3GestaltGUI.check_status():
    Define empty method
- examples/test/test_machine.py:
    Add description normalize code
"""

from machines import VirtualMachine
from gui import Py3GestaltGUIApp

VirtualMachine(name='de')
Py3GestaltGUIApp().run()
