"""Virtual Node for Testing

This modules does nothing, for now.
"""

import py3gestalt.nodes as nodes
from py3gestalt.utilities import notice


class TestNode(nodes.BaseVirtualNode):
    def do(self):
        notice(self, "It does work.")

# This class can be uncommented in order to debug
# 'nodes.BaseNodeShell.is_vn_ill_defined()'
# class AnotherTestNode(nodes.BaseVirtualNode):
#     def do(self):
#         print('It does.')
