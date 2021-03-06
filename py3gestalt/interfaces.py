"""Interfaces module from Gestalt framework for Python 3.

Originally written by Ilan Moyer in 2013 and modified by Nadya Peek in 2015.

This module defines interface classes and an interface shell class, which acts
as an intermediary between the interface and nodes.

- 'InterfaceShell' class:
    A wrapper that links the real interface object to classes and methods that
    try to access it.
- 'BaseInterface' class:
    A basic example of an interface object. Every interface should be based on it.
- 'SerialInterface' class:
    Defines an interface that uses a serial port.

Copyright (c) 2018 Daniel Marquina
"""

from py3gestalt import core
from py3gestalt import packets
from py3gestalt import functions
from py3gestalt.utilities import notice, get_available_serial_ports, \
    scan_serial_ports
import threading
import itertools
import platform
import serial
import socket
import queue
import time
import sys
import os


class InterfaceShell(object):
    """Intermediary between nodes, node shells and interfaces.

    Args:
        owner: Object that initializes this interface shell. It could be a
            virtual machine, a virtual node, etc.
        interface (BaseInterface):
            Interface to be contained by this shell.

    Attributes:
        owner: Object that owns this shell. Used in the port acquisition process.
        contained_interface (BaseInterface or a child): Interface contained by
            this shell.

    """
    def __init__(self, owner, interface=None):
        self.owner = None
        self.contained_interface = None
        self.set(interface, owner)

    def set(self, interface, owner=None):
        """Update the interface contained by the shell.

        Also initializes contained (or linked) shell. Owner can be None. This
        method is called when a node is initialized.

        Args:
            interface (BaseInterface): Interface to be contained by this shell.
            owner: Object that will own this interface shell.
        """
        if owner:
            self.owner = owner
        self.contained_interface = interface
        if interface and self.owner:
            self.contained_interface.owner = self.owner
        if interface:
            self.contained_interface.init_after_set()

    def set_owner(self, owner):
        """Set owner.

         Updates owner of this shell and its contained interface.
         Useful when no owner was specified when instantiating.

         Args:
             owner: New owner of this interface shell.
        """
        self.owner = owner  # used in the port acquisition process
        if self.contained_interface:
            self.contained_interface.owner = owner

    def __getattr__(self, attribute):
        """Forward attribute calls to the contained interface.

        Args:
            attribute: Contained interface's attribute to be called.

        Returns:
            Contained interfaces's attribute.
        """
        if self.contained_interface is not None:
            if hasattr(self.contained_interface, attribute):
                return getattr(self.contained_interface, attribute)
            else:
                notice(self, "Interface does not have requested attribute.")
                raise AttributeError(attribute)
        else:
            notice(self, "Interface shell is empty.")
            raise AttributeError(attribute)


class BaseInterface(object):
    """Base class of all interfaces.

    Args:
        owner: Object that initializes this interface.

    Attributes:
        owner: Object that owns this interface.

    This class presents a basic structure of all interfaces. Currently, it only
    has an empty method which will be overridden by a child class defined
    later.
    """

    def __init__(self, owner):
        self.owner = owner

    def init_after_set(self):
        """Connect to interface after it was assigned to an interface shell."""
        pass


class SerialInterface(BaseInterface):
    """Serial communication interface.

    The core of this class is a serial object. For data transmission, a queue
    stores all data to be sent whereas a thread handles transmission of every
    element in that queue.
    As data reception using a thread requires a defined
    protocol, a simple method reads a number of bytes from the input buffer.

    Args:
        owner: Object that instantiates this interface.
        baud_rate (int): Speed in baud.
        port_name (str): Name of port to connect.
        interface_type (str): Type of interface, 'ftdi' or 'arduino' for now.
        time_out (float): Time to wait for a new device to be connected, in
            seconds.

    Attributes:
        owner (VirtualMachine): Object that owns this interface.
        baudRate (int): Speed in baud.
        portName (str): Name of connected port.
        interfaceType (str): Type of interface, 'ftdi' or 'lufa' for now.
        timeOut (float): Time to wait for a new device to be connected.
        isConnected (boolean): State of connection.
        port (serial): Serial object to use.
        transmitQueue (Queue): A queue to store to-be-transmitted packets from
            different sources.
        transmitter (TransmitThread): A thread to handle data transmission.

    Note:
        Regarding the attribute 'interfaceType', a third value may be used,
        'genericSerial', but its use could potentially cause problems because of
        its generic implementation.
    """
    def __init__(self, owner, baud_rate, port_name=None, interface_type=None,
                 time_out=0.2):
        super(SerialInterface, self).__init__(owner)
        self.baudRate = baud_rate
        self.portName = port_name
        self.interfaceType = interface_type
        self.timeOut = time_out
        self.isConnected = False
        self.port = None
        # a queue is used to allow multiple threads to call transmit simultaneously.
        self.transmitQueue = queue.Queue()
        self.transmitter = None

    def init_after_set(self):
        """Initialize after setting.

        Begins connection procedure. First, it tries to connect to provided
        port name; if there is no port name, it waits for a new port to be
        created based on a provided interface type.
        """
        if self.portName:
            self.connect(self.portName)
        elif self.interfaceType:
            # if an interface type is provided, auto-acquire
            self.acquire_port_and_connect(self.interfaceType)
        else:
            notice(self, "Serial interface could not be initialized. A port name or an "
                         "interface type are required.")

    def connect(self, port_name=None):
        """Connect to serial port.

        Connects to specified port name. Tries to connect to port assigned on
        instantiation if no port is specified as argument.

        Args:
            port_name (str): Name of serial port.
        """
        if port_name:
            port = port_name
        elif self.portName:
            port = self.portName
        else:
            notice(self, 'No port name provided.')
            return

        try:
            self.port = serial.Serial(port, self.baudRate, timeout=self.timeOut)
        except serial.SerialException:
            notice(self, "Error when opening serial port " + str(port))
            return

        self.port.flushInput()
        self.port.flushOutput()
        notice(self, "Port " + str(port) + " connected successfully.")
        # Some serial ports need some time between opening and transmission
        time.sleep(2)
        self.isConnected = True
        self.start_transmitter()

    def acquire_port_and_connect(self, interface_type):
        """Acquire a serial port and connect to it.

        Tries to detect a serial port based on the provided interface type.
        If no serial port is detected, it waits some seconds (10 by default)
        for a new one to be created.

        Args:
             interface_type (str): Type of interface.

        Returns:
            Call to connect function if a port was detected. Exits, otherwise.
        """
        serial_filter = self.get_serial_filter_terms(interface_type)
        available_ports = get_available_serial_ports(serial_filter)
        if len(available_ports) == 1:
            # Connects to the only available port that matches the filter.
            self.portName = available_ports[0]
            return self.connect()
        else:
            notice(self, "Trying to acquire serial port. You have 10 seconds to "
                         "plug an interface in.")
            new_ports = self.wait_for_new_port(serial_filter)
            if new_ports:
                if len(new_ports) > 1:
                    notice(self.owner,
                           "Could not acquire. Multiple ports plugged in "
                           "simultaneously.")
                    return
                else:
                    self.portName = new_ports[0]
                    return self.connect()

    def get_serial_filter_terms(self, interface_type=None):
        """Get filter terms for serial ports.

        According to the operating system, selects a type of filter and the
        filter term.
        For example, in the case of Arduino, the type is 'manufacturer' and the
        filter term is 'Arduino'. This implementation allows the inclusion of
        new interfaces.

        Args:
            interface_type (str): Type of interface, 'ftdi' for FTDI devices,
                'Arduino' for Arduino and 'generic serial' for others.

        Returns:
            A list of filter type and filter term respectively, if found on
            the dictionary. False, otherwise.

        Note:
            Currently, the type of filter should be one attribute of
            'serial.tools.list_ports.ListPortInfo' class, supported by your
            operating system (Windows, Linux os MacOS).

        Note:
            The use of interface type 'genericSerial' should be avoided
            because many devices could share the provided filter term.
        """
        ftdi_terms = {'Windows': ['manufacturer', 'FTDI'],
                      'Linux': ['manufacturer', 'FTDI'],
                      'Darwin': ['manufacturer', 'FTDI']}
        arduino_terms = {'Windows': ['manufacturer', 'Arduino'],
                         'Linux': ['manufacturer', 'Arduino'],
                         'Darwin': ['manufacturer', 'Arduino']}
        generic_serial_terms = {'Windows': ['device', 'COM'],
                                'Linux': ['device', 'tty'],
                                'Darwin': ['device', 'tty.']}
        terms_dict = {'ftdi': ftdi_terms, 'arduino': arduino_terms,
                      'genericSerial': generic_serial_terms}
        op_sys = platform.system()  # nominally detects the system
        if interface_type in terms_dict:
            if op_sys in terms_dict[interface_type]:
                return terms_dict[interface_type][op_sys]
            else:
                notice(self,
                       "Operating system support not found for interface type '" +
                       interface_type + "'")
                return False
        else:
            notice(self,
                   "Interface support not found for interface type '" +
                   interface_type + "'")
            return False

    def wait_for_new_port(self, filter_term=None, time_limit=10):
        """Wait for a new port to be created.

        This function waits for the user to connect an interface device and
        returns its new serial port.

        Args:
            filter_term (str): Optional serial port filter, depends on
                interface type and operating system.
            time_limit (float): Maximum number of seconds to wait for a new
                port to be created.

        Returns:
            A list of new serial ports. False, otherwise.

        """
        timer_count = 0
        old_ports = scan_serial_ports(filter_term)
        num_old_ports = len(old_ports)
        while True:
            time.sleep(0.25)
            timer_count += 0.25
            if timer_count > time_limit:
                notice(self.owner, 'TIMEOUT while trying to acquire a new port.')
                return False
            new_ports = scan_serial_ports(filter_term)
            num_new_ports = len(new_ports)
            if num_new_ports < num_old_ports:
                # A device has been unplugged, update info
                old_ports = list(new_ports)
                num_old_ports = num_new_ports
            elif num_new_ports > num_old_ports:
                # Returns all ports that just appeared
                return list(set(new_ports) - set(old_ports))

    def start_transmitter(self):
        """Start the transmit thread."""
        self.transmitter = self.TransmitThread(self, self.transmitQueue, self.port)
        self.transmitter.daemon = True
        self.transmitter.start()

    def transmit(self, data):
        """Add data to transmit queue.

        As a thread handles data transmission, it continuously checks the
        transmit queue and sends data when added by this function.
        String data is converted to a list by default.
        """
        if self.isConnected:
            self.transmitQueue.put(data)
        else:
            notice(self, 'Serial interface is not connected.')

    def read_bytes(self, bytes_to_read=None):
        """Read a number of bytes from the serial port's input buffer.

        If there are less bytes available, read only the available ones.

        Args:
            bytes_to_read (int): Number of bytes to grab.

        Returns:
            Read bytes, if received. None, otherwise.
        """
        if self.port:
            available_bytes = self.port.in_waiting
            if bytes_to_read:
                return self.port.read(min(bytes_to_read, available_bytes))
            else:
                return self.port.read(available_bytes)
        else:
            return None

    class TransmitThread(threading.Thread):
        """A thread to handle data transmission data over a serial port.

        Args:
            owner (SerialInterface): Interface that instantiates this thread.
            transmit_queue (Queue): Queue that stores to-be-transmitted packets.
            port (Serial): Serial port to be used.

        Attributes:
            owner (SerialInterface): Interface that owns this thread.
            transmitQueue (Queue): Queue that stores to-be-transmitted packets.
            port (Serial): Serial port to be used.
        """
        def __init__(self, owner, transmit_queue, port):
            super(SerialInterface.TransmitThread, self).__init__()
            self.owner = owner
            self.transmitQueue = transmit_queue
            self.port = port

        def run(self):
            """Define code to be ran by the transmit thread.

            Gets a packet from transmit queue, converts it into a string and
            transmits it.
            """
            while True:
                transmit_state, transmit_packet = self.get_transmit_packet()
                if transmit_state:
                    if self.port:
                        self.port.write(self.serialize(transmit_packet).encode('utf-8'))
                    else:
                        notice(self, "Cannot transmit. No serial port "
                                     "initialized.")
                time.sleep(0.0005)
            pass

        def get_transmit_packet(self):
            """Get a to-be-transmitted packet from the transmit queue.

            Returns:
                True and first packet from transmit queue, if it was not empty.
                False and None, otherwise.
            """
            try:
                return True, self.transmitQueue.get()
            except queue.Empty:
                return False, None
            pass

        def serialize(self, packet):
            """Convert packet into a string for transmission over a serial port.

            Uses ASCII characters.

            Returns:
                Packet as string if it was a list or a string. False, otherwise.
            """
            if type(packet) == list:
                return ''.join([chr(byte) for byte in packet])
            elif type(packet) == str:
                return packet
            else:
                notice(self,
                       "Error: Packet must be either a list or a string.")
                return False

# class gestaltInterface(baseInterface):
#     '''Interface to Gestalt nodes based on the Gestalt protocol.'''
#
#     def __init__(self, name=None, interface=None, owner=None):
#         self.name = name  # name becomes important for networked gestalt
#         self.owner = owner
#         self.interface = interfaceShell(interface,
#                                         self)  # uses the interfaceShell object for connecting to sub-interface
#
#         self.receiveQueue = Queue.Queue()
#         self.CRC = CRC()
#         self.nodeManager = self.nodeManager()  # used to map network addresses (physical devices) to nodes
#
#         self.startInterfaceThreads()  # this will start the receiver, packetRouter, channelPriority, and channelAccess threads.
#
#         # define standard gestalt packet
#         self.gestaltPacket = packets.packet(template=[packets.pInteger('startByte', 1),
#                                                       packets.pList('address', 2),
#                                                       packets.pInteger('port', 1),
#                                                       packets.pLength(),
#                                                       packets.pList('payload')])
#
#     def validateIP(self, IP):
#         '''Makes sure that an IP address isn't already in use on the interface.'''
#         if str(IP) in self.nodeManager.address_node:
#             return False
#         else:
#             return True
#
#     class nodeManager(object):
#         '''Manages all nodes under the control of this interface.'''
#
#         def __init__(self):
#             self.node_address = {}  # node : address
#             self.address_node = {}  # address: node
#
#         def updateNodesAddresses(self, node, address):
#             oldNode = None
#             oldAddress = None
#
#             if str(address) in self.address_node: oldNode = self.address_node[str(address)]
#             if node in self.node_address: oldAddress = self.node_address[node]
#
#             if str(oldAddress) in self.address_node: self.address_node.pop(str(oldAddress))
#             if oldNode in self.node_address: self.node_address.pop(oldNode)
#
#             self.address_node.update({str(address): node})
#             self.node_address.update({node: address})
#
#         def getIP(self, node):
#             '''Returns IP address for a given node.'''
#             if node in self.node_address:
#                 return self.node_address[node]
#             else:
#                 return False
#
#         def getNode(self, IP):
#             IP = str(IP)
#             if IP in self.address_node:
#                 return self.address_node[IP]
#             else:
#                 return False
#
#     def assignNode(self, node, address):
#         '''Assigns a given node to the interface on a particular address.'''
#         self.nodeManager.updateNodesAddresses(node, address)
#
#     def transmit(self, virtualNode, port, packetSet, mode):
#         '''Transmits a packet set over the interface immediately.'''
#         # --BUILD START BYTE TABLE--
#         startByteTable = {'unicast': 72,
#                           'multicast': 138}  # unicast transmits to addressed node, multicast to all nodes on network
#         if mode in startByteTable:
#             startByte = startByteTable[mode]
#         else:
#             startByte = startByteTable['unicast']
#
#         # --TRANSMIT PACKETS--
#         address = self.nodeManager.getIP(virtualNode)
#         for packet in packetSet:
#             packetRoutable = self.gestaltPacket(
#                 {'startByte': startByte, 'address': address, 'port': port, 'payload': packet})  # build packet
#             packetWChecksum = self.CRC(packetRoutable)  # generate CRC
#             self.interface.transmit(packetWChecksum)  # transmit packet thru interface
#
#     def commit(self, actionObject):
#         '''Puts actionObjects or actionSets into the channelPriority queue.'''
#         self.channelPriority.putActionObject(actionObject)
#
#     def startInterfaceThreads(self):
#         '''Initiates the receiver thread.'''
#         # START RECEIVE THREAD
#         self.receiver = self.receiveThread(self)
#         self.receiver.daemon = True
#         self.receiver.start()
#         # START ROUTER THREAD
#         self.packetRouter = self.packetRouterThread(self)
#         self.packetRouter.daemon = True
#         self.packetRouter.start()
#         # START CHANNEL PRIORITY THREAD
#         self.channelPriority = self.channelPriorityThread(self)
#         self.channelPriority.daemon = True
#         self.channelPriority.start()
#         # START CHANNEL ACCESS THREAD
#         self.channelAccess = self.channelAccessThread(self)
#         self.channelAccess.daemon = True
#         self.channelAccess.start()
#
#     class receiveThread(threading.Thread):
#         '''Gets packets from the network interface, interpreting them, and pushing them to the router queue.'''
#
#         def __init__(self, interface):
#             threading.Thread.__init__(self)
#             self.interface = interface
#
#         #			print "GESTALT INTERFACE RECEIVE THREAD INITIALIZED"
#
#         def run(self):
#             packet = []
#             inPacket = False
#             packetPosition = 0
#             packetLength = 5
#
#             while True:
#                 byte = self.interface.interface.receive()  # get byte
#                 if byte:
#                     byte = ord(byte)  # converts char to byte
#                     if not inPacket:
#                         if byte == 72 or byte == 138:  # waits for start byte
#                             inPacket = True
#                             packet += [byte]  # adds start byte to packet
#                             packetPosition += 1  # increment packet position
#                             continue  # otherwise rejects packet
#                     else:  # in a packet
#                         packet += [byte]  # append byte to packet
#
#                         if packetPosition == 4:  # byte 2 contains the packet position
#                             packetLength = byte
#                             packetPosition += 1  # increment packet position
#                             continue
#
#                         if packetPosition < packetLength:
#                             packetPosition += 1  # increment packet position
#                             continue
#
#                         if packetPosition == packetLength:
#                             if self.interface.CRC.validate(packet): self.interface.packetRouter.routerQueue.put(
#                                 packet[:len(packet) - 1])  # check CRC, then send to router (minus CRC)
#
#                 # initialize packet
#                 packet = []
#                 inPacket = False
#                 packetPosition = 0
#                 packetLength = 5
#
#                 time.sleep(0.0005)
#
#     class packetRouterThread(threading.Thread):
#         '''Routes packets to their matching service routines, and executes the service routine within this thread.'''
#
#         def __init__(self, interface):
#             threading.Thread.__init__(self)
#             self.interface = interface
#             self.routerQueue = Queue.Queue()
#
#         def run(self):
#             while True:
#                 routerState, routerPacket = self.getRouterPacket()
#                 if routerState:
#                     parsedPacket = self.interface.gestaltPacket.decode(routerPacket)
#                     address = parsedPacket['address']
#                     port = parsedPacket['port']
#                     data = parsedPacket['payload']
#                     destinationNode = self.interface.nodeManager.getNode(address)
#                     if not destinationNode:
#                         print
#                         "PACEKT RECEIVED FOR UNKNOWN ADDRESS " + str(address)
#                         continue
#                     destinationNode.route(port, data)
#
#                 time.sleep(0.0005)
#
#         def getRouterPacket(self):
#             try:
#                 return True, self.routerQueue.get()
#             except:
#                 return False, None
#
#     class channelAccessThread(threading.Thread):
#         '''Controls when action objects have access to the interface.
#
#             channelAccessQueue contains a serialized list of actionObjects which have been cleared for transmission and
#             are waiting for access to the channel.'''
#
#         def __init__(self, interface):
#             threading.Thread.__init__(self)
#             self.interface = interface
#             self.channelAccessQueue = Queue.Queue()
#
#         # might add another queue here for when actionObjects need to be transmitted immediately.
#
#         def run(self):
#             while True:
#                 accessQueueState, actionObject = self.getActionObject()  # get the next action object from the queue.
#                 if accessQueueState:
#                     actionObject.grantAccess()  # actionObject now has control of the channel.
#                 time.sleep(0.0005)
#
#         def getActionObject(self):
#             try:
#                 return True, self.channelAccessQueue.get()
#             except:
#                 return False, None
#
#         def putActionObject(self, actionObject):
#             self.channelAccessQueue.put(actionObject)
#             return True
#
#     class channelPriorityThread(threading.Thread):
#         '''Releases actionObjects to the channelAccessQueue, and when necessary first serializes actionSets into a series of action objects.'''
#
#         def __init__(self, interface):
#             threading.Thread.__init__(self)
#             self.interface = interface
#             self.channelPriorityQueue = Queue.Queue()
#
#         def run(self):
#             while True:
#                 priorityQueueState, actionObject = self.getActionObject()  # get the next actionObject or actionSet from the queue.
#                 if priorityQueueState:
#                     while not actionObject.isReleased():  # wait for actionObject or actionSet to be released
#                         time.sleep(0.0005)
#                     for thisActionObject in self.serialize(actionObject):
#                         self.interface.channelAccess.putActionObject(
#                             thisActionObject)  # transfer action object to the channel access thread.
#                 time.sleep(0.0005)
#
#         def serialize(self, actionObject):
#             '''serializes actionSets into actionObjects.'''
#             if actionObject._type_ == 'actionObject': return [
#                 actionObject]  # note _type_ is defined in the actionObject class
#             if actionObject._type_ == 'actionSet':
#                 if actionObject.actionObjects[0]._type_ == 'actionObject':
#                     # actionSet contains actionObjects rather than actionSequences
#                     actionObjectStream = [thisActionObject for thisActionObject in actionObject.actionObjects]
#                     actionObjectStream += [
#                         actionObject.actionObjects[0].virtualNode.syncRequest()]  # generates a syncRequest.
#                     return actionObjectStream
#                 if actionObject.actionObjects[0]._type_ == 'actionSequence':
#                     actionObjectStream = []
#                     actionSequences = [actionSequence.actionObjects for actionSequence in actionObject.actionObjects]
#                     syncLists = zip(
#                         *actionSequences)  # takes parallel slices of actionObjects in the provided actionSequences.
#                     for syncList in syncLists:
#                         actionObjectStream += syncList
#                         actionObjectStream += [syncList[0].virtualNode.syncRequest()]
#                     return actionObjectStream
#             return []
#
#         def getActionObject(self):
#             try:
#                 return True, self.channelPriorityQueue.get()
#             except:
#                 return False, None
#
#         def putActionObject(self, actionObject):
#             self.channelPriorityQueue.put(actionObject)
#             return True
#
#
# class socketInterface(baseInterface):
#     def __init__(self, IPAddress='', IPPort=27272):  # all avaliable interfaces, port 27272
#         self.receiveIPAddress = IPAddress
#         self.receiveIPPort = IPPort
#
#
# class socketUDPServer(socketInterface):
#
#     def initAfterSet(self):  # gets called once interface is set into shell.
#         self.receiveSocket = socket.socket(socket.AF_INET,
#                                            socket.SOCK_DGRAM)  # UDP, would be socket.SOCK_STREAM for TCP
#         self.receiveSocket.bind((self.receiveIPAddress, self.receiveIPPort))  # bind to socket
#         notice(self, "opened socket on " + str(self.receiveIPAddress) + " port " + str(self.receiveIPPort))
#         self.transmitSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
#     def receive(self):
#         data, addr = self.receiveSocket.recvfrom(1024)
#         notice(self, "'" + str(data) + "' from " + str(addr))
#         return (data, addr)
#
#     def transmit(self, remoteIPAddress, remoteIPPort, data):
#         #		self.transmitSocket.sendto(data, (remoteIPAddress, remoteIPPort))
#         self.receiveSocket.sendto(data, (remoteIPAddress, remoteIPPort))
#
#
# # ----UTILITY CLASSES---------------
# class CRC():
#     '''Generates CRC bytes and checks CRC validated packets.'''
#
#     def __init__(self):
#         self.polynomial = 7  # CRC-8: ATM=7, Dallas-Maxim = 49
#         self.crcTableGen()
#
#     def calculateByteCRC(self, byteValue):
#         '''Calculates Bytes in the CRC Table.'''
#         for i in range(8):
#             byteValue = byteValue << 1
#             if (byteValue // 256) == 1:
#                 byteValue = byteValue - 256
#                 byteValue = byteValue ^ self.polynomial
#         return byteValue
#
#     def crcTableGen(self):
#         '''Generates a CRC table to make CRC generation faster.'''
#         self.crcTable = []
#         for i in range(256):
#             self.crcTable += [self.calculateByteCRC(i)]
#
#     def __call__(self, packet):
#         '''Generates CRC for an input packet.'''
#         # INITIALIZE CRC ALGORITHM
#         crc = 0
#         crcByte = 0
#
#         # CALCULATE CRC AND CONVERT preOutput BYTES TO CHR
#         output = []
#         for byte in packet:
#             crcByte = byte ^ crc
#             crc = self.crcTable[crcByte]
#             output += [byte]
#         output += [crc]  # write crc to output
#         return output  # NOTE: OUTPUT HAS BEEN CONVERTED TO A STRING
#
#     def validate(self, packet):  # NOTE: ASSUMES INPUT IS A LIST OF NUMBERS
#         '''Checks CRC byte against packet.'''
#         crc = 0
#         crcByte = 0
#         packetLength = len(packet)
#
#         for char in packet[0:packetLength]:
#             crcByte = char ^ crc
#             crc = self.crcTable[crcByte]
#
#         if crc != 0:
#             return False  # CRC doesn't match
#         else:
#             return True  # CRC matches
#
#
# ----METHODS-----------------------




