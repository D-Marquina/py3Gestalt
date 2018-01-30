"""
TO-DO list:
- Resolve issue with owner concept: what objects can own other objects?
    Should I define only one owner, the virtual machine?
- The use of a GUI as a debugger must be normalized: make it more general without
    knowledge of the GUI methods.
- Organize modules as a framework, relocate gui.py module.
- Install this framework and use it as the original, importing it.
- Develop GUI as a separate project.
"""

from machines import VirtualMachine
from gui import Py3GestaltGUIApp

# VirtualMachine(name='de')
Py3GestaltGUIApp().run()
