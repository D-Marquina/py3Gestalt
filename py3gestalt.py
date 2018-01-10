"""
TO-DO
- gui.Py3GestaltGUI:
    DO NOT IMPORT before checking everything is correct.
    As completely unloading a module is almost impossible (too hard),
    virtual machine's temporal file should not be loaded that easily.
    Also, a new GUI should be executed in order to change virtual machine file
    or a new approach should be used.
- gui.Py3GestaltGUI:
    Renew documentation
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
