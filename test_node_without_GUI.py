"""Virtual Node for Testing

This modules does nothing, for now.
"""
import nodes
from utilities import notice


class TestNode(nodes.BaseVirtualNode):
    def do(self):
        notice(self, "It does work.", self.use_debug_gui)

# class AnotherTestNode(nodes.BaseVirtualNode):
#     def do(self):
#         print('It does.')
