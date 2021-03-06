"""Utilities module from Gestalt framework for Python 3.

Originally written by Ilan Moyer in 2013 and modified by Nadya Peek in 2015.

This module contains various classes and methods needed for the correct
implementation of this framework.

- 'PersistenceManager' class:
    Defines an object which is in charge of managing the creation, writing and
    reading of persistence file.
- 'Notice' method:
    Shows notifications about the execution of the framework using a logger.
- 'Scan_serial_ports' method:
    Returns a list of all serial ports in the PC.
- 'Get_available_serial_ports' method:
    Returns only available serial ports by opening and closing them.

Copyright (c) 2018 Daniel Marquina
"""

import serial, serial.tools.list_ports
import datetime
import logging
import math
import glob
import ast
import sys

# Logging configuration by default
logging.basicConfig(level=logging.DEBUG, format='%(message)s', stream=sys.stdout)
log = logging.getLogger("Virtual Machine")


class PersistenceManager(object):
    """Manager of persistence files.

    Every time a machine is configured, when addresses of physical nodes are
    assigned to virtual nodes (actually to node shells), a persistence file
    is created in order to store those addresses and load them next time the
    machine is turned on. This class manages such file, whose content is mostly
    written as a Python dictionary.

    Args:
        filename (str): Future name of persistence file.
        namespace (str): Name of machine that instantiates this class.

    Attributes:
        filename (str): Name of persistence file.
        namespace (str): Name of machine that owns this class.
    """

    def __init__(self, filename=None, namespace=None):
        self.filename = filename
        self.namespace = namespace

    def __call__(self):
        """Override '__call__()' method.

        Makes sure that a persistence file exists before trying to use it.

        Returns:
            'self', if was previously initialized, False otherwise.
        """
        if self.filename:
            return self
        else:
            return False

    def get(self, name):
        """Get a stored node's address.

        Looks up in persistence file for a node with the specified name and
        returns its address. This function is usually called when a node shell
        is being instantiated.

        Args:
            name (str): Node's name.

        Returns:
            Node's address, if found; else, None.
        """
        persistence_dict = self.read_persistence_dictionary()
        lookup = self.namespace + '.' + name
        if lookup in persistence_dict:
            return persistence_dict[self.namespace + '.' + name]
        else:
            return None

    def store(self, name, value):
        """Store a node and/or its address.

        Also updates an existing node's address. This function is usually
        called when a node shell is being instantiated.

        Args:
            name: Node's name.
            value: Node's address.
        """
        persistence_dict = self.read_persistence_dictionary()
        persistence_dict.update({self.namespace + '.' + name: value})
        self.write_persistence_dictionary(persistence_dict)

    def read_persistence_dictionary(self):
        """Copy persistence file's content into a Python dictionary."""
        try:
            file_object = open(self.filename, 'rU')
            persistence_dict = ast.literal_eval(file_object.read())
            file_object.close()
            return persistence_dict
        except IOError:
            return {}

    def write_persistence_dictionary(self, persistence_dict):
        """Write actual persistence file's content.

        Persistence file's content consists of a title and a Python dictionary.

        Args:
            persistence_dict (dict): Python dictionary containing to-be-stored
                nodes and their addresses.
        """
        file_object = open(self.filename, 'w')
        file_object.write("# This Gestalt persistence file was auto-generated @ " +
                          str(datetime.datetime.now()) + "\n")
        file_object.write("{\n")
        for key in persistence_dict:
            file_object.write("'" + key + "'" + ":" +
                              str(persistence_dict[key]) + ",\n")
        file_object.write("}")
        file_object.close()


def notice(source=None, message=""):
    """Send a notice to the user.

    Originally, this method used to inly show a notice on the console, but now
    it makes use of a logger, that means every notice can be redirected if
    specified in user-defined virtual machine.

    Args:
        source (VirtualMachine, etc.): Object that sends a notice.
        message (str): Message to display.
    """
    if hasattr(source, 'name'):
        name = getattr(source, 'name')
        if name:
            log.debug(name + ": " + str(message))
        elif hasattr(source, 'owner'):
            owner = getattr(source, 'owner')
            if owner:
                notice(source.owner, message)
            else:
                log.debug(str(source) + ": " + str(message))
        else:
            log.debug(str(source) + ": " + str(message))
    else:
        if hasattr(source, 'owner'):
            owner = getattr(source, 'owner')
            if owner:
                notice(source.owner, message)
            else:
                log.debug(str(source) + ": " + str(message))
        else:
            log.debug(str(source) + ": " + str(message))


def scan_serial_ports(serial_filter_terms=None):
    """Scan serial ports.

    It can filter out ports that do not match given filter terms.

    Args:
        serial_filter_terms (str): Serial device's information used to filter.

    Returns:
        A list containing the names of all serial ports.

    Note:
        When using glob, your current terminal "/dev/tty" is excluded.
    """
    if sys.platform.startswith('win') or \
            sys.platform.startswith('linux') or \
            sys.platform.startswith('darwin'):
        ports = []
        for port in serial.tools.list_ports.comports():
            if serial_filter_terms:
                filter_type = serial_filter_terms[0]
                filter_term = serial_filter_terms[1]
                if filter_type == 'manufacturer':
                    if filter_term in port.manufacturer:
                        ports.append(port.device)
                elif filter_type == 'device':
                    if filter_term in port.device:
                        ports.append(port.device)
                continue
            else:
                ports.append(port.device)
    else:
        raise EnvironmentError('Unsupported platform')

    return ports


def get_available_serial_ports(filter_term=None):
    """Get available serial ports.

    Tries to open PC's serial ports and filters the available ones.

    Args:
        filter_term (str): Serial device's information used to filter.

    Returns:
        A list containing the names of available serial ports.
    """
    ports = scan_serial_ports(filter_term)
    available_ports = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            available_ports.append(port)
        except (OSError, serial.SerialException):
            pass

    return available_ports


# def intToBytes(integer, numbytes):
#     bytes = range(numbytes)
#     for i in bytes:
#         bytes[i] = integer % 256
#         integer -= integer % 256
#         integer = integer // 256
#
#     if integer > 0: print
#     "ERROR in PACKET COMPOSER: BYTE OVERFLOW"
#     return bytes
#
#
# def bytesToInt(bytes):
#     integer = 0
#     order = 0
#     for i in bytes:
#         integer += i * (256 ** order)
#         order += 1
#     return integer
#
#
# def listToString(numList):
#     strList = [chr(x) for x in numList]
#     return ''.join(strList)
#
#
# def vectorAbs(vector):
#     output = range(len(vector))
#     for i in output:
#         output[i] = abs(vector[i])
#     return output
#
#
# def vectorInt(vector):
#     output = range(len(vector))
#     for i in output:
#         output[i] = int(vector[i])
#     return output
#
#
# def vectorMultiply(vector1, vector2):
#     if len(vector1) != len(vector2):
#         print
#         "ERROR in vectorMultiply: vectors have dissimilar lengths"
#     output = range(len(vector1))
#     for i in output:
#         output[i] = vector1[i] * vector2[i]
#     return output
#
#
# def vectorDivide(vector1, vector2):
#     if len(vector1) != len(vector2):
#         print
#         "ERROR in vectorDivide: vectors have dissimilar lengths"
#     output = range(len(vector1))
#     for i in output:
#         output[i] = vector1[i] / float(vector2[i])
#     return output
#
#
# def vectorSign(vector):
#     output = range(len(vector))
#     for i in output:
#         if vector[i] > 0: output[i] = 1
#         if vector[i] < 0: output[i] = -1
#         if vector[i] == 0: output[i] = 0
#     return output
#
#
# def vectorMCUSign(vector):
#     output = range(len(vector))
#     for i in output:
#         if vector[i] > 0: output[i] = 1
#         if vector[i] <= 0: output[i] = 0
#     return output
#
#
# def vectorLength(vector):
#     sum = 0.0
#     for i in vector:
#         sum += i ** 2  # squares power
#     return math.sqrt(sum)
#
#
# def vectorMax(vector):
#     vMax = 0.0
#     for i in vector:
#         if i > vMax: vMax = i
#     return vMax
#
#
# class intelHexParser(object):
#     '''Parses Intel Hex Files for Bootloading and Memory Programming.'''
#
#     def __init__(self):
#         self.filename = None
#         self.hexFile = None
#         self.resetParser()
#
#     def openHexFile(self, filename=None):
#         if filename != None:
#             self.hexFile = open(filename, 'r')
#             return self.hexFile
#         else:
#             print
#             "intelHexParser: please provide a filename!"
#             return False
#
#     def resetParser(self):
#         self.baseByteLocation = 0  # always initialize at location 0, this can be changed by the hex file during reading
#         self.parsedFile = []
#         self.codeStart = 0
#         self.terminated = False  # gets set when end of file record is reached
#
#     def loadHexFile(self):
#         parseVectors = {0: self.processDataRecord, 1: self.processEndOfFileRecord,
#                         2: self.processExtendedSegmentAddressRecord,
#                         3: self.processStartSegmentAddressRecord, 4: self.processExtendedLinearAddressRecord,
#                         5: self.processStartLinearAddressRecord}
#
#         for index, record in enumerate(self.hexFile):  # enumerate over lines in hex file
#             integerRecord = self.integerRecord(self.recordParser(record))
#             parseVectors[integerRecord['RECTYP']](integerRecord)
#         #		print self.parsedFile
#         self.checkAddressContinuity()
#
#     def returnPages(self, pageSize):
#         numPages = int(math.ceil(len(self.parsedFile) / float(pageSize)))  # number of pages
#         pages = [self.parsedFile[i * pageSize:(i + 1) * pageSize] for i in
#                  range(numPages)]  # slice parsed data into pages of size pageSize
#
#         # fill in last page
#         lastPage = pages[-1]
#         delta = pageSize - len(lastPage)
#         lastAddress = lastPage[-1][0]  # address of last entry in last page
#         makeUp = [[lastAddress + i + 1, 0] for i in range(delta)]
#         pages[-1] += makeUp  # fill last page
#
#         return pages
#
#     def recordParser(self, record):
#         record = record.rstrip()
#         length = len(record)
#         return {'RECLEN': record[1:3], 'OFFSET': record[3:7], 'RECTYP': record[7:9], 'DATA': record[9:length - 2],
#                 'CHECKSUM': record[length - 2: length]}
#
#     def integerRecord(self, record):
#         return {'RECLEN': int(record['RECLEN'], 16), 'OFFSET': int(record['OFFSET'], 16),
#                 'RECTYP': int(record['RECTYP'], 16),
#                 'CHECKSUM': int(record['CHECKSUM'], 16), 'DATA': self.dataList(record['DATA'])}
#
#     def dataList(self, data):
#         return [int(data[i:i + 2], 16) for i in range(0, len(data), 2)]
#
#     def processDataRecord(self, record):
#         codeLocation = record['OFFSET'] + self.baseByteLocation
#         for index, byte in enumerate(record['DATA']):
#             self.parsedFile += [[codeLocation + index, byte]]
#
#     def processEndOfFileRecord(self, record):
#         self.terminated = True
#
#     def processExtendedSegmentAddressRecord(self, record):
#         self.baseByteLocation = (record['DATA'][0] * 256 + record['DATA'][1]) * 16  # value is shifted by four bits
#
#     def processStartSegmentAddressRecord(self, record):
#         print
#         "Start Segment Address Record Encountered and Ignored"
#
#     def processExtendedLinearAddressRecord(self, record):
#         print
#         "Extended Linear Address Record Encountered and Ignored"
#
#     def processStartLinearAddressRecord(self, record):
#         print
#         "Start Linear Address Record Encountered and Ignored"
#
#     def checkAddressContinuity(self):
#         baseAddress = self.parsedFile[0][0]  # inital address entry
#         for byte in self.parsedFile[1::]:
#             if byte[0] == baseAddress + 1:
#                 baseAddress += 1
#                 continue
#             else:
#                 print
#                 "CONTINUITY CHECK FAILED"
#                 return False
#
#         print
#         "CONTINUITY CHECK PASSED"