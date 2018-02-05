"""Nodes module from Gestalt framework for Python 3.

Originally written by Ilan Moyer in 2013 and modified by Nadya Peek in 2015.

This module defines virtual node and node shell classes, the latter act
as an intermediary between the former and the virtual machine.

- 'BaseNodeShell' class:
    Basic node shell, its function is to provide a mean to load a virtual node
    that is not defined in the same file as the virtual machine.
- 'BaseVirtualNode' class:
    Basic virtual node definition.

Copyright (c) 2018 Daniel Marquina
"""

from py3gestalt import core
from py3gestalt import packets
from py3gestalt import functions
from py3gestalt import utilities
from py3gestalt import interfaces
from py3gestalt.utilities import notice
import importlib
import threading
import requests
import inspect
import shutil
import random
import urllib
import pyclbr
import time
import math
import os


# ----NODE SHELLS------------
class BaseNodeShell(object):
    """The basic container for all nodes.

    Like a room in a hotel, that has different occupants and offers certain
    amenities to its guests, 'BaseNodeShell' gets subclassed by more specific
    shells for one of the four types of gestalt nodes:

    - Solo/Independent: arbitrary interface/ arbitrary protocol
    - Solo/Gestalt: arbitrary interface/ gestalt protocol
    - Networked/Gestalt: networked gestalt interface/ gestalt protocol
    - Managed/Gestalt: hardware synchronized gestalt network/ gestalt protocol

    Args:
        owner (VirtualMachine or a child): Virtual machine that instantiates
            this node shell.
        name (str): Name of this node shell.

    Attributes:
        owner (VirtualMachine or a child): Virtual machine that owns this node
            shell.
        name (str): Name of this node shell.
        interface (InterfaceShell): Shell to contain owner's interface.
        vn_class (Class): Virtual node's class. The contained node will be an
            instance of this class.
        node (BaseVirtualNode or a child): Contained or linked node.
    """
    def __init__(self, owner, name):
        self.owner = owner
        self.name = name
        self.interface = interfaces.InterfaceShell(self)
        self.vn_class = None
        self.node = None

    def __getattr__(self, attribute):
        """Forward any unsupported call to the shell onto the node."""
        if self.node is not None:  # Shell contains a node.
            if hasattr(self.node, attribute):  # node contains requested attribute
                return getattr(self.node, attribute)
            else:
                notice(self, "Node does not have requested attribute.")
                raise AttributeError(attribute)
        else:
            notice(self, "Node has not been initialized.")
            raise AttributeError(attribute)

    def load_vn_from_file(self, filename, **kwargs):
        """Load virtual node from a file.

        This function gets the text from a file, imports it as a module and
        loads its defined virtual node'.

        Note:
            If a file path is being passed, it is recommended to use
            'os.path.join()' as it creates a path according to the operating
            system.

        Args:
             filename (str): Name or path to file containing virtual node's
                definition.
        """
        file_object = open(filename, 'r')
        vn_imported_module = self.import_vn_module(file_object.read())
        file_object.close()
        self.load_vn_from_module(vn_imported_module, checked=True, **kwargs)

    def load_vn_from_url(self, url, **kwargs):
        """Load virtual node from a url.

        This functions gets the text from a provided URL, imports it as a
        module and loads the defined virtual node.

        Args:
             url (str): URL directing to virtual node's definition.
        """
        resp = requests.get(url)
        notice(self, resp.text)
        vn_imported_module = self.import_vn_module(resp.text)
        self.load_vn_from_module(vn_imported_module, checked=True, **kwargs)

    def import_vn_module(self, module_content):
        """Import a user-defined virtual node module.

        Makes a temporal package (directory with an '__init__.py' file) called
        'tmpVN' with a temporal module (file) which contains a defined virtual
        node and imports it.
        They are assessed as 'temporal' because they are deleted every time an
        import action is attempted or finished.

        Note:
            The module's name is 'temp_virtual_node_X.py', where 'X' is the
            number of import attempts. Such change of name is necessary in
            order to avoid problems next, when analyzing module's classes
            using 'pyclbr'.

        Returns:
            vn_module: Imported virtual node.
        """
        self.owner.node_file_counter += 1

        package = 'tmpVN'
        if os.path.exists(package):
            shutil.rmtree(package, ignore_errors=True)
        os.makedirs(package)

        open(os.path.join(package, '__init__.py'), 'w').close()

        module_name = 'temp_virtual_node_' + str(self.owner.node_file_counter)
        module_location = os.path.join(package, module_name + '.py')
        module_file = open(module_location, 'w')
        module_file.write(module_content)
        module_file.close()
        module = package + '.' + module_name

        if self.is_vn_ill_defined(module):
            return

        vn_module = importlib.import_module(module)

        if os.path.exists(package):
            shutil.rmtree(package, ignore_errors=True)

        return vn_module

    def load_vn_from_module(self, module, checked=False, **kwargs):
        """Load virtual node from an imported module.

        Instantiates a virtual node from a class defined in provided module.
        Such module must have been already imported and should contain only one
        virtual node class that is a child of 'nodes.BaseVirtualNode'. That
        last feature can be checked passing an argument 'checked' as False.

        Args:
            module: Module containing virtual node's definition.
            checked (boolean): A flag indicating whether module's content (only
                one BaseVirtualNode's child class) has been checked or not.
        """
        if not checked:
            if self.is_vn_ill_defined(module.__name__):
                notice(self, "Provided module '"
                       + module.__name__ +
                       ".py' was ill defined and could not be loaded.")
                return

        for name in dir(module):
            cls = getattr(module, name)
            if inspect.isclass(cls):
                if "BaseVirtualNode" in str(cls.__mro__[-2]):
                    self.vn_class = cls
                else:
                    notice(self, "Error - Virtual node class ill defined.")
                    return

        self.set_node(self.vn_class, **kwargs)

    def is_vn_ill_defined(self, vn_module):
        """Check whether a virtual node is ill defined or not.

        Makes sure that selected virtual node contains one and only one
        user-defined virtual machine class, child of 'nodes.BaseVirtualNode'
        class.

        Args:
            vn_module: Virtual node module to be analyzed.

        Returns:
            True when selected module contains none or more than a unique
            virtual node. False otherwise.
        """
        num_of_vn_cls = 0
        for name, class_data in sorted(pyclbr.readmodule(vn_module).items(),
                                       key=lambda x: x[1].lineno):
            supers_list = []
            if hasattr(class_data, 'super'):
                class_super = class_data.super[0]
                if hasattr(class_super, 'name'):
                    while class_super != 'object':
                        supers_list.append(class_super.name)
                        class_super = class_super.super[0]
                    supers_list.append('object')
                else:
                    supers_list.append(class_super)
            if any('BaseVirtualNode' in super_ for super_ in supers_list):
                num_of_vn_cls += 1

        if num_of_vn_cls == 0:
            notice(self, "Error: No virtual node defined.")
            return True
        elif num_of_vn_cls > 1:
            notice(self, "Error: More than a unique virtual node defined in a "
                         "single file.")
            return True

        return False

    def set_node(self, vn_class, **kwargs):
        """Sets contained or linked node.

        Creates an instance of selected virtual node class and executes its
        'init()' method.
        Owner, name and interface from this shell are passed to contained node.

        Args:
            vn_class (Class): Virtual node class to be instantiated.
            kwargs: Arguments to be passed onto the virtual node's initialization.
        """
        self.node = vn_class(self.owner, **kwargs)
        notice(self, "Node assigned to '" + self.name + "' node shell.")
        self.node.shell = self
        self.node.name = self.name
        self.node.interface = self.interface
        self.node.init(**self.node.initKwargs)

# class soloIndependentNode(baseNodeShell):
#     ''' A container shell for Solo/Independent nodes.
#
#         Solo/Independent nodes are non-networked and may use an arbitrary communications protocol.
#         For example, they could be a third-party device with a python plug-in, etc...
#     '''
#
#     def __init__(self, name=None, interface=None, filename=None, URL=None, module=None, **kwargs):
#         '''	Initialization procedure for Solo/Independent Node Shell.
#
#             name:		a unique name assigned by the user. This is used by the persistence algorithm to re-acquire the node.
#             interface: 	the object thru which the virtual node communicates with its physical counterpart.
#             **kwargs:	any additional arguments to be passed to the node during initialization
#
#             Methods of Loading Virtual Node:
#                 filename: an import-able module containing the virtual node.
#                 URL: a URL pointing to a module as a resource containing the virtual node.
#                 module: a python module name containing the virtual node.
#         '''
#
#         # call base class __init__ method
#         super(soloIndependentNode, self).__init__()
#
#         # assign parameters to variables
#         self.name = name
#         self.filename = filename
#         self.URL = URL
#         self.module = module
#         self.interface.set(interface, self)  # interface isn't shared with other nodes, so owner is self.
#
#         # acquire node. For an SI node, some method of acquisition MUST be provided, as it has no protocol for auto-loading.
#         # load via filename
#         if filename:
#             self.loadNodeFromFile(filename, **kwargs)
#         # load via URL
#         elif URL:
#             self.loadNodeFromURL(URL, **kwargs)
#         # load via module
#         elif module:
#             self.loadNodeFromModule(module, **kwargs)
#         else:
#             notice(self, "no node source was provided.")
#             notice(self, "please provide a filename, URL, or class")
#
#
# class gestaltNodeShell(baseNodeShell):
#     '''Base class for all nodes which communicate using the gestalt protocol.'''
#
#     def __init__(self, name=None, interface=None, filename=None, URL=None, module=None, persistence=lambda: None,
#                  **kwargs):
#         '''	Initialization procedure for Gestalt Node Shell.
#
#             name:		a unique name assigned by the user. This is used by the persistence algorithm to re-acquire the node.
#             interface: 	the object thru which the virtual node communicates with its physical counterpart.
#             **kwargs:	any additional arguments to be passed to the node during initialization
#
#             Methods of Loading Virtual Node:
#                 filename: an import-able module containing the virtual node.
#                 URL: a URL pointing to a module as a resource containing the virtual node.
#                 module: a python module name containing the virtual node.
#
#             Networked/Gestalt virtual nodes initialize by associating with their counterparts over the network. A URL pointing to their driver is
#             returned upon association. This driver is then loaded into the shell as the virtual node.
#         '''
#
#         # call base class __init__ method
#         super(gestaltNodeShell, self).__init__()  # call init on baseNodeShell
#
#         # assign parameters to variables
#         self.name = name
#         self.filename = filename
#         self.URL = URL
#         self.module = module
#         self.persistence = persistence
#
#         # connect to interface
#         if interface:
#             # make sure that node has a gestalt interface
#             if type(interface) != interfaces.gestaltInterface:
#                 # wrap a gestalt interface around the provided interface
#                 self.interface.set(interfaces.gestaltInterface(interface=interface, owner=self), self)
#             else:
#                 self.interface.set(interface, self)  # interface isn't shared with other nodes, so owner is self.
#
#             # import base node
#             self.setNode(baseStandardGestaltNode())
#
#             if self.persistence():
#                 address = self.persistence.get(self.name)
#             else:
#                 address = None
#
#             if address:  # an IP address was found
#                 self.interface.assignNode(self.node, address)  # assign node to interface with IP address
#                 nodeURL = self.node.urlRequest()  # get node URL
#             else:  # acquire node
#                 # set node IP address	-- this will be changed later once persistence is added
#                 address = self.generateIPAddress()  # generate random IP address
#                 self.interface.assignNode(self.node, address)  # assign node to interface with IP address
#                 if type(self) == networkedGestaltNode: notice(self, "please identify me on the network.")
#                 nodeURL = self.node.setIPRequest(address)  # set real node's IP address, and retrieve URL.
#                 if self.persistence(): self.persistence.store(self.name, address)
#
#             notice(self, nodeURL)
#
#             # try to start node in application mode
#             nodeStatus, appValid = self.statusRequest()
#             if nodeStatus == 'B' and appValid:  # node is in bootloader mode and application is valid
#                 if self.runApplication():  # need to reinitialize
#                     nodeURL = self.urlRequest()
#                     notice(self, " NOW RUNNING IN APPLICATION MODE")
#                     notice(self, nodeURL)  # remove
#                 else:
#                     notice(self, "ERROR STARTING APPLICATION MODE")
#             elif nodeStatus == 'A':
#                 notice(self, "RUNNING IN APPLICATION MODE")
#             else:
#                 notice(self, " RUNNING IN BOOTLOADER MODE")
#
#         else:
#             # No interface, this can be intentional to allow debugging offline
#             notice(self, 'Error - please provide an interface.')
#
#         # acquire virtual node.
#         # if a virtual node source is provided, use that. Otherwise acquire from URL provided by node.
#         if filename:
#             if not self.loadNodeFromFile(filename, **kwargs): return
#         # load via URL
#         elif URL:
#             if not self.loadNodeFromURL(URL, **kwargs): return
#         # load via module
#         elif module:
#             if not self.loadNodeFromModule(module, **kwargs): return
#         # get URL from node
#         else:
#             if not self.loadNodeFromURL(nodeURL): return
#
#         if interface:
#             # assign new node with old IP address to interface. This replaces the default node with the imported node.
#             self.interface.assignNode(self.node, address)
#
#     def generateIPAddress(self):
#         '''Generates a random IP address.'''
#         while True:
#             IP = [random.randint(0, 255), random.randint(0, 255)]
#             if self.interface.validateIP(IP): break  # checks with interface to make sure IP address isn't taken.
#         return IP
#
#
# class soloGestaltNode(gestaltNodeShell):
#     '''	A container shell for Solo/Gestalt nodes.
#
#         Solo/Gestalt nodes are non-networked and use the gestalt communications protocol.
#         For example they might make use of the gsArduino library.'''
#     pass
#
#
# class networkedGestaltNode(gestaltNodeShell):
#     '''	A container shell for Networked/Gestalt nodes.
#
#         Networked/Gestalt nodes are networked and use the gestalt communications protocol.
#         Both the older Fabnet hardware as well as boards based on Units of Fab are supported.'''
#     pass
#
#
# # ----VIRTUAL NODES------------


class BaseVirtualNode(object):
    """Base class for virtual nodes.

    Initialization occurs in three steps:

    1) BaseVirtualNode gets initialized when instantiated.
    2) Node shell loads references into node through 'set_node()' method.
    3) 'init()' is called by 'set_node()' method.

    The purpose of this routine is to initialize the nodes once they already
    have references to their shell.

    Args:
        owner (VirtualMachine or a child): Virtual machine that instantiates
            this node.

    Attributes:
        owner (VirtualMachine or a child): Virtual machine that owns this node.
        shell (BaseNodeShell or a child): Node shell that contains this node.
        name (str): Name of this node shell.
        interface (InterfaceShell): Shell to contained owner's interface.
        initKwargs: Keyword arguments used on instantiation.
    """

    def __init__(self, owner, **kwargs):
        self.owner = owner
        self.shell = None
        self.name = None
        self.interface = None
        self.initKwargs = kwargs

    def _init(self, **kwargs):
        """Dummy initializer for child class."""
        pass

    def init(self, **kwargs):
        """Dummy initializer for terminal child class."""
        pass

#
#
# class baseSoloIndependentNode(baseVirtualNode):
#     '''base class for solo/independent virtual nodes'''
#     pass
#
#
# class baseGestaltNode(baseVirtualNode):
#     '''base class for all gestalt nodes'''
#
#     def _init(self, **kwargs):
#         self.bindPort = self.bindPort(self)  # create binder function for node
#
#         self._initParameters()
#         self.initParameters()
#         self._initFunctions()
#         self.initFunctions()
#         self._initPackets()
#         self.initPackets()
#         self._initPorts()
#         self.initPorts()
#         # //FIX// need to make response flags specific to ports, otherwise packets can be recognized cross-port
#         self.responseFlag = threading.Event()  # this object is used for nodes to wait for a response
#
#     def _initParameters(self):
#         return
#
#     def initParameters(self):
#         return
#
#     def _initFunctions(self):
#         return
#
#     def initFunctions(self):
#         return
#
#     def _initPorts(self):
#         return
#
#     def initPorts(self):
#         return
#
#     def _initPackets(self):
#         return
#
#     def initPackets(self):
#         return
#
#     def _initLast(self):
#         return
#
#     def initLast(self):
#         return
#
#     def transmit(self, nodeSet, mode='unicast'):
#         self.interface.transmit(nodeSet, mode)
#
#     def route(self, port, packet=None):
#         if packet == None: packet = []
#         if port in self.bindPort.inPorts:
#             destinationFunction = self.bindPort.inPorts[port]
#         else:
#             print
#             str(self) + " RECEIVED A PACKET TO UNKOWN PORT " + str(port)
#             return
#         destinationFunction.receiver(packet)
#         return
#
#     class bindPort():
#         def __init__(self, virtualNode):
#             self.virtualNode = virtualNode
#             self.outPorts = {}  # ports for outbound packets {function:port#}
#             self.inPorts = {}  # functions for inbound packets {port#:function}
#
#         def __call__(self, port, outboundFunction=None, outboundPacket=None, inboundFunction=None, inboundPacket=None):
#             newResponseFlag = threading.Event()
#             packetHolder = packets.packetHolder()
#
#             # ---CREATE FUNCTION INSTANCES AND UPDATE ROUTE DICTIONARIES---
#             if outboundFunction != None:
#                 if outboundPacket != None:
#                     packetSet = packets.packetSet(
#                         outboundPacket)  # gives the outbound function a packetSet initialized with the provided packet as a template
#                 else:
#                     packetSet = packets.packetSet(packets.packet(
#                         template=[]))  # gives the outbound function a packetSet initialized with a blank packet as a template
#                 if type(outboundFunction) == type: setattr(self.virtualNode, outboundFunction.__name__,
#                                                            outboundFunction(virtualNode=self.virtualNode,
#                                                                             # create function instance
#                                                                             packetSet=packetSet,  # define packet format
#                                                                             responseFlag=newResponseFlag,
#                                                                             # creates a common response flag for outbound and inbound functions
#                                                                             packetHolder=packetHolder))  # creates a common packet holder for outbound and inbound functions
#                 outboundFunction = getattr(self.virtualNode,
#                                            outboundFunction.__name__)  # update outboundFuncton pointer in event that new instance was created
#                 self.outPorts.update({outboundFunction: port})  # bind port to outbound instance
#
#             if inboundFunction != None:
#                 if inboundPacket != None:
#                     packetSet = packets.packetSet(
#                         inboundPacket)  # gives the inbound function a packetSet initialized with the provided packet as a template
#                 else:
#                     packetSet = packets.packetSet(packets.packet(
#                         template=[]))  # gives the inbound function a packetSet initialized with a blank packet as a template
#                 if type(inboundFunction) == type: setattr(self.virtualNode, inboundFunction.__name__,
#                                                           inboundFunction(virtualNode=self.virtualNode,
#                                                                           # create function instance
#                                                                           packetSet=packetSet,  # define packet format
#                                                                           responseFlag=newResponseFlag,
#                                                                           # creates a common response flag for outbound and inbound functions
#                                                                           packetHolder=packetHolder))  # creates a common packet holder for outbound and inbound functions
#                 inboundFunction = getattr(self.virtualNode, inboundFunction.__name__)
#                 self.inPorts.update({port: inboundFunction})  # bind port to inbound instance
#             else:  # create a default inbound function which will handle incoming packets.
#                 if inboundPacket != None:
#                     packetSet = packets.packetSet(inboundPacket)  # use provided inbound packet
#                 else:
#                     packetSet = packets.packetSet(packets.packet(template=[]))  # create default blank packet
#                 inboundFunction = functions.serviceRoutine(virtualNode=self.virtualNode, packetSet=packetSet,
#                                                            responseFlag=newResponseFlag, packetHolder=packetHolder)
#                 self.inPorts.update({port: inboundFunction})
#
#
# class baseStandardGestaltNode(baseGestaltNode):
#
#     def _initParameters(self):
#         self.bootPageSize = 128
#
#     def _initPackets(self):
#         # status
#         self.statusResponsePacket = packets.packet(
#             template=[packets.pString('status', 1),  # status is encoded as 'b' for bootloader, 'a' for app.
#                       packets.pInteger('appValidity', 1)])  # app validity byte, gets set to 170 if app is valid
#
#         # bootloader command
#         self.bootCommandRequestPacket = packets.packet(template=[packets.pInteger('commandCode', 1)])
#         self.bootCommandResponsePacket = packets.packet(template=[packets.pInteger('responseCode', 1),
#                                                                   packets.pInteger('pageNumber', 2)])
#         # bootloader write
#         self.bootWriteRequestPacket = packets.packet(template=[packets.pInteger('commandCode', 1),
#                                                                packets.pInteger('pageNumber', 2),
#                                                                packets.pList('writeData', self.bootPageSize)])
#         self.bootWriteResponsePacket = packets.packet(self.bootCommandResponsePacket)
#
#         # bootloader read
#         self.bootReadRequestPacket = packets.packet(template=[packets.pInteger('pageNumber', 2)])
#         self.bootReadResponsePacket = packets.packet(template=[packets.pList('readData', self.bootPageSize)])
#
#         # request URL
#         self.urlResponsePacket = packets.packet(template=[packets.pString('URL')])
#
#         # set IP address
#         self.setIPRequestPacket = packets.packet(template=[packets.pList('setAddress', 2)])
#         self.setIPResponsePacket = packets.packet(self.urlResponsePacket)
#
#     # identify node
#     # no packet format
#
#     # reset node
#     # no packet format
#
#     def _initPorts(self):
#         # status
#         self.bindPort(port=1, outboundFunction=self.statusRequest, inboundPacket=self.statusResponsePacket)
#         # bootloader command
#         self.bindPort(port=2, outboundFunction=self.bootCommandRequest, outboundPacket=self.bootCommandRequestPacket,
#                       inboundPacket=self.bootCommandResponsePacket)
#         # bootloader write
#         self.bindPort(port=3, outboundFunction=self.bootWriteRequest, outboundPacket=self.bootWriteRequestPacket,
#                       inboundPacket=self.bootWriteResponsePacket)
#         # bootloader read
#         self.bindPort(port=4, outboundFunction=self.bootReadRequest, outboundPacket=self.bootReadRequestPacket,
#                       inboundPacket=self.bootReadResponsePacket)
#         # request url
#         self.bindPort(port=5, outboundFunction=self.urlRequest, inboundPacket=self.urlResponsePacket)
#         # set IP address
#         self.bindPort(port=6, outboundFunction=self.setIPRequest, outboundPacket=self.setIPRequestPacket,
#                       inboundPacket=self.setIPResponsePacket)
#         # identify node
#         self.bindPort(port=7, outboundFunction=self.identifyRequest)
#
#         # reset node
#         self.bindPort(port=255, outboundFunction=self.resetRequest)
#
#     def loadProgram(self, filename):
#         '''Loads a program into a Gestalt Node via the built-in Gestalt bootloader.'''
#         # initialize hex parser
#         parser = utilities.intelHexParser()  # Intel Hex Format Parser Object
#         parser.openHexFile(filename)
#         parser.loadHexFile()
#         pages = parser.returnPages(self.bootPageSize)
#         # reset node if necessary to switch to bootloader mode
#         nodeStatus, appValid = self.statusRequest()
#         if nodeStatus == 'A':  # currently in application, need to go to bootloader
#             self.resetRequest()  # attempt to reset node
#             nodeStatus, appValid = self.statusRequest()
#             if nodeStatus != 'B':
#                 notice(self, "ERROR IN BOOTLOADER: CANNOT RESET NODE")
#                 return False
#         # initialize bootloader
#         if self.initBootload(): notice(self, "BOOTLOADER INITIALIZED!")
#         # write hex file to node
#         for page in pages:
#             pageData = [addressBytePair[1] for addressBytePair in page]
#             pageNumber = self.bootWriteRequest(0, pageData)  # send page to bootloader
#             if pageNumber != page[0][0]:
#                 notice(self, "Error in Bootloader: PAGE MISMATCH: SENT PAGE " + str(
#                     page[0][0]) + " AND NODE REPORTED PAGE " + str(pageNumber))
#                 notice(self, "ABORTING PROGRAM LOAD")
#                 return False
#             notice(self, "WROTE PAGE " + str(pageNumber))  # + ": " + str(pageData)
#         # verify hex file from node
#         for page in pages:
#             pageData = [addressBytePair[1] for addressBytePair in page]
#             currentPageNumber = page[0][0]
#             verifyData = self.bootReadRequest(currentPageNumber)
#             for index, item in enumerate(verifyData):
#                 if item != pageData[index]:
#                     notice(self, "VERIFY ERROR IN PAGE: " + str(currentPageNumber) + " BYTE: " + str(index))
#                     notice(self, "VERIFY FAILED")
#                     return False
#             notice(self, "PAGE " + str(currentPageNumber) + " VERIFIED!")
#         notice(self, "VERIFY PASSED")
#         # start application
#         if not self.runApplication():
#             notice(self, "COULD NOT START APPLICATION")
#             return FALSE
#         # register new node with gestalt interface
#         # self.target.nodeManager.assignNode(self)	#registers node with target
#         # need something here to import a new node into self.shell based on URL from node
#         return True
#
#     def initBootload(self):
#         return self.bootCommandRequest('startBootload')
#
#     def runApplication(self):
#         return self.bootCommandRequest('startApplication')
#
#     class statusRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self):
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess()  # wait for channel access
#                 if self.transmitPersistent():
#                     return self.getPacket()['status'], (
#                             self.getPacket()['appValidity'] == 170)  # magic number for app validity
#
#     class bootCommandRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self, command):
#                 commandSet = {'startBootload': 0, 'startApplication': 1}
#                 responseSet = {'bootloadStarted': 5,
#                                'applicationStarted': 9}  # these numbers are arbitrary and defined in the firmware.
#                 if command in commandSet:
#                     self.setPacket({'commandCode': commandSet[command]})
#                     self.commitAndRelease()  # commit self immediately
#                     self.waitForChannelAccess()
#                     if self.transmitPersistent():
#                         responseCode = self.getPacket()['responseCode']
#                         if command == 'startBootload' and responseCode == responseSet['bootloadStarted']: return True
#                         if command == 'startAplication' and responseCode == responseSet[
#                             'applicationStarted']: return True
#                     else:
#                         print
#                         "NO RESPONSE TO BOOTLOADER COMMAND " + command
#                         return False
#                 else:
#                     print
#                     "BOOTLOADER COMMAND " + command + " NOT RECOGNIZED."
#                     return False
#
#     class bootWriteRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self, pageNumber, data):
#                 self.setPacket({'commandCode': 2, 'pageNumber': pageNumber, 'writeData': data})
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess()
#                 if self.transmitPersistent():
#                     returnPacket = self.getPacket()
#                     if returnPacket['responseCode'] == 1:  # page write OK
#                         return returnPacket['pageNumber']
#                     else:
#                         print
#                         "PAGE WRITE NOT SUCCESSFUL ON NODE END"
#                         return False
#                 else:
#                     print
#                     "NO RESPONSE RECEIVED TO PAGE WRITE REQUEST"
#                     return False
#
#     class bootReadRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self, pageNumber):
#                 self.setPacket({'pageNumber': pageNumber})
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess()
#                 if self.transmitPersistent():
#                     return self.getPacket()['readData']
#                 else:
#                     print
#                     "NO RESPONSE RECEIVED TO PAGE WRITE REQUEST"
#                     return False
#
#     class urlRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self):
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess()
#                 if self.transmitPersistent():
#                     return self.getPacket()['URL']
#                 else:
#                     notice(self.virtualNode, 'NO URL RECEIVED')
#                     return False
#
#     class setIPRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self, IP):
#                 self.setPacket({'setAddress': IP}, mode='multicast')
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess(5)
#                 if self.transmitPersistent(timeout=15):
#                     time.sleep(1)  # debounce for button press
#                     return self.getPacket()['URL']
#                 else:
#                     notice(self.virtualNode, 'TIMEOUT WAITING FOR BUTTON PRESS')
#
#     class identifyRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self):
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess()
#                 self.transmit()
#                 time.sleep(4)  # roughly the time that the LED is on.
#
#     class resetRequest(functions.serviceRoutine):
#         class actionObject(core.actionObject):
#             def init(self):
#                 self.commitAndRelease()  # commit self immediately
#                 self.waitForChannelAccess()
#                 self.transmit()
#                 time.sleep(0.1)  # give time for watchdog timer to reset
#
#
# class compoundNode(object):
#     '''A compound node helps distribute and synchronize function calls across multiple nodes.'''
#
#     def __init__(self, *nodes):
#         self.nodes = nodes
#         self.nodeCount = len(self.nodes)
#         self.name = "[" + ''.join([str(node.name) + "," for node in nodes])[:-1] + "]"
#         interfaces = [node.interface.Interface for node in nodes]  # nodes have an interface shell
#         if all(interface == interfaces[0] for interface in interfaces):
#             self.commonInterface = True
#         else:
#             self.commonInterface = False
#             notice(self, "warning: not all members of compound node share a common interface!")
#
#     def __getattr__(self, attribute):
#         '''	Forwards all unsupported function calls to a distributor'''
#         return self.distributor(self, attribute)
#
#     class distributor(object):
#         '''The distributor is responsible for forwarding function calls made on the compound node to its constituents.
#
#         Arguments provided as tuples will be distributed individually. Non-tuple arguments will be duplicated to all
#         nodes.'''
#
#         def __init__(self, compoundNode, attribute):
#             self.attribute = attribute
#             self.compoundNode = compoundNode
#             self.sync = False  # indicates whether function call is synchronized. This gets set true if any arguments are tuples.
#
#         def __call__(self, *compoundArguments, **compoundKWarguments):
#             nodeArguments = [[] for i in range(self.compoundNode.nodeCount)]  # a list of arguments for each node
#             nodeKWarguments = [{} for i in range(self.compoundNode.nodeCount)]  # a list of kwarguments for each node
#
#             # If a tuple is provided, the items are distributed to respective arguments out lists. Otherwise, the item is copied to all lists.
#
#             # compile arguments
#             for argument in compoundArguments:
#                 if type(argument) == tuple:  # tuple provided, should distribute
#                     if len(
#                             argument) != self.compoundNode.nodeCount:  # check to make sure that tuple length matches the number of nodes.
#                         alert(self.compoundNode, self.attribute + ": not enough arguments provided in tuple.")
#                         return False
#                     else:
#                         self.sync = True  # tuple provided, this will be a synchronized call.
#                         for nodeArgPair in zip(nodeArguments,
#                                                list(argument)):  # iterate thru (targetArgumentList, argument)
#                             currentNodeArguments = nodeArgPair[0]
#                             currentNodeArguments += [nodeArgPair[1]]
#                 else:
#                     for node in nodeArguments:
#                         node += [argument]
#
#             # compile keyword arguments
#             for key, value in compoundKWarguments.iteritems():
#                 if type(value) == tuple:  # tuple provided, should distribute
#                     if len(value) != self.compoundNode.nodeCount:
#                         alert(self.compoundNode, self.attribute + ": not enough arguments provided in tuple.")
#                         return False
#                     else:
#                         self.sync = True
#                         for nodeArgPair in zip(nodeKWarguments, list(value)):
#                             currentNodeArguments = nodeArgPair[0]
#                             currentNodeArguments.update({key: nodeArgPair[1]})
#                 else:
#                     for node in nodeKWarguments:
#                         node.update({key: value})
#
#             #			if sync, provide a sync token
#             if self.sync:
#                 syncToken = core.syncToken()  # pull a new sync token
#                 for node in nodeKWarguments:
#                     node.update({'sync': syncToken})
#
#             #			make function calls
#             returnValues = [self.nodeFunctionCall(node, self.attribute, args, kwargs) for node, args, kwargs in
#                             zip(self.compoundNode.nodes, nodeArguments, nodeKWarguments)]
#
#             if self.sync:
#                 return core.actionSet(returnValues)
#             else:
#                 return returnValues
#
#         def nodeFunctionCall(self, node, attribute, args, kwargs):
#             if hasattr(node, attribute):
#                 return getattr(node, attribute)(*list(args), **kwargs)
#             else:
#                 notice(self.compoundNode, "NODE DOESN'T HAVE REQUESTED ATTRIBUTE")
#                 raise AttributeError(attribute)
