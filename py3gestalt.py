"""
TO-DO
- Add set_name, set_interface, etc to machines.VirtualMachine class
- Verify what happens when no persistence file is passed.
- Put important code into a folder called py3Gestalt in order to normalize
    importing lines in examples with and without GUI (run independently,
    from console).
- gui.Py3GestaltGUI.check_status():
    Define empty method
- examples/test/test_machine.py:
    Add description normalize code
"""

from machines import VirtualMachine
from gui import Py3GestaltGUIApp

# VirtualMachine(name='de')
Py3GestaltGUIApp().run()
