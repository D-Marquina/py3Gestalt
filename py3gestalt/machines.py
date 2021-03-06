"""Machines module from Gestalt framework for Python 3.

Originally written by Ilan Moyer in 2013 and modified by Nadya Peek in 2015.

This module contains classes needed to define a virtual machine and its
components according to user's real physical machine.

- 'Virtual Machine' class:
    The main class, all user-defined virtual machines should be its children. It
    includes some methods in order to show a basic structure of virtual
    machines. Those methods are supposed to be overridden.

Copyright (c) 2018 Daniel Marquina
"""

from py3gestalt import interfaces
from py3gestalt.utilities import PersistenceManager, notice
import threading
import inspect
import math
import copy


class VirtualMachine(object):
    """Base class for all virtual machines.

    A virtual machine is basically made of an interface, nodes and machine
    elements, all of them are virtual too because they represent the real,
    physical machine. Besides, some functions have to be defined in order to
    interact with the real machine.

    Three basic main attributes are needed: name, interface and persistence
    file. If no name is specified, user's virtual machine's file path is
    assigned as name by default. The interface must be defined on 'interfaces'
    module. The persistence file is always created when a name is specified and
    is saved where the user-defined virtual machine's file is located.

    All 'init...' methods are empty but are called on initialization because
    the user should override them according to the real machine's requirements.
    While many machines won't need every pre-built initializer, they are
    provided to introduce some structure to the format of virtual machines.

    Keyword Args:
        name (str): Virtual machine's to-be name.
        interface(InterfaceShell, BaseInterface or a child): Virtual machine's
            to-be interface.
        persistenceFile (str): Persistence file's to-be name.

    Attributes:
        name (str): Virtual machine's name.
        interface(InterfaceShell, BaseInterface or a child): Virtual machine's
            interface.
        persistence (PersistenceManager): Persistence file's manager.
        node_file_counter (int): Counter of virtual nodes' file copies. Used
            when initializing nodes.
    """
    def __init__(self, *args, **kwargs):
        self.name = None
        self.interface = None
        self.persistence = None
        self.node_file_counter = 0

        notice(self, "Initializing virtual machine...")
        self.set_name(kwargs['name'] if 'name' in kwargs else None)
        self.set_interface(kwargs['interface'] if 'interface' in kwargs else None)
        self.set_persistence(kwargs['persistenceFile'] if 'persistenceFile'
                                                          in kwargs else None)
        if 'persistenceFile' in kwargs and 'name' not in kwargs:
                # If no name is provided, and multiple machines share the
                # persistence file, this could result in a namespace conflict.
                notice(self,
                       'Warning: setting persistence without providing a name '
                       'to the virtual machine can result in a conflict in '
                       'multi-machine persistence files.')

        # Run user initialization
        self.init(*args, **kwargs)
        self.init_interfaces()
        self.init_controllers()
        self.init_coordinates()
        self.init_kinematics()
        self.init_functions()
        self.init_last()

    def set_name(self, name=None):
        """Set name of virtual machine.

        If this function is called without passing an argument, virtual machine's
        file's location is assigned as name.

        Args:
            name (str): Virtual machine's new name
        """
        if name is None:
            self.name = inspect.getfile(self.__class__)
        elif isinstance(name, str):
            self.name = name
            notice(self, "Name successfully assigned.")
        else:
            notice(self, "Assignation of ill defined name was refused. "
                         "Previous name remains.")

    def set_interface(self, interface=None):
        """Set interface of virtual machine.

        When no interface is specified, an empty interface shell is assigned as
        machine's interface.

        Args:
            interface: Virtual machine's interface, must be defined in
                interfaces module.
        """
        if interface is None:
            self.interface = interfaces.InterfaceShell(self)
            notice(self, "An empty interface has been assigned.")
        elif any(cls in str(interface.__class__.__mro__)
                 for cls in ("InterfaceShell", "BaseInterface")):
            self.interface = interface
            notice(self, "Interface successfully assigned.")
        else:
            notice(self, "Assignation of ill defined interface was refused. "
                         "Previous interface remains")

    def set_persistence(self, filename=None):
        """Set persistence file of virtual machine.

        'Filename' can be None because the implementation of PersistenceManager
        class foresees a case when no file name was assigned.

        Args:
            filename (str): Virtual machine's persistence file's name.
        """
        if filename is None:
            self.persistence = PersistenceManager(namespace=self.name)
            notice(self, "No persistence manager has been assigned.")
        elif isinstance(filename, str):
            self.persistence = PersistenceManager(filename=filename,
                                                  namespace=self.name)
            notice(self, "Persistence manager successfully initialized.")
        else:
            notice(self, "Assignation of ill defined persistence manager was "
                         "refused. Previous one remains.")

    def init_interfaces(self):
        """Initialization of interfaces.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        Machine interface can be specified either on instantiation, using
        "set_interface()" method or here.
        """
        pass

    def init_controllers(self):
        """Initialization of controllers or nodes.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        Every node should be defined here. However, they should first be declared
        on "__init__" function of user-defined virtual machine, before calling
        its parent class' "__init__" function.
        """
        pass

    def init_coordinates(self):
        """Initialization of coordinates.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        Used units are defined here.
        """
        pass

    def init_kinematics(self):
        """Initialization of kinematics.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        Mechanical machine elements and kinematics are defined here.
        """
        pass

    def init_functions(self):
        """Initialization of functions.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        Functions needed for machine interaction should be defined here.
        """
        pass

    def init(self, *args, **kwargs):
        """User-defined initialization.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        This initialization method can be called any time, should be carefully
        written.
        """
        pass

    def init_last(self):
        """Initialization of last.

        This method is called on instantiation of virtual machine and should
        be overridden by user.

        This methods purpose is still obscure.
        """
        pass


# # --COORDINATES-----
# class coordinates():
#     '''Components pertinent to storing and manipulating position information.'''
#
#     class uFloat(float):
#         '''A floating-point number which also has units.'''
#
#         def __new__(self, value, units=None):
#             return float.__new__(self, value)
#
#         def __init__(self, value, units=None):
#             self.units = units
#             self.conversionDictionary = ''
#             if units == 'mm': self.conversionDictionary = {'in': 1.0 / 25.4}
#             if units == 'in': self.conversionDictionary = {'mm': 25.4}
#             if units == 'deg': self.conversionDictionary = {'rad': 2 * math.pi / 360.0}
#             if units == 'rad': self.conversionDictionary = {'deg': 360.0 / (2.0 * math.pi)}
#
#         def convertUnits(self, targetUnits):
#             if targetUnits in self.conversionDictionary:
#                 return coordinates.uFloat(self * self.conversionDictionary[targetUnits], targetUnits)
#             else:
#                 return False
#
#     def uFloatSubtract(self, term1, term2):
#         '''Returns a list containing term1 - term2 with units.'''
#         return [uFloat(x - y, x.units) for (x, y) in zip(term1, term2)]
#
#     class baseCoordinate(object):
#         '''A set of ordinates which can be used to define positions of various machine elements.'''
#
#         def __init__(self, inputList):
#             self.baseList = [coordinates.uFloat(0, elementUnit) for elementUnit in inputList]
#
#         def __call__(self):
#             return self.baseList
#
#         def get(self):
#             return self.baseList
#
#         def set(self, valueArray):
#             if len(valueArray) != len(self.baseList):
#                 notice(self, 'input array length must match coordinate length.')
#                 return False
#             else:
#                 for index, item in enumerate(valueArray):
#                     # any None input will not modify value
#                     self.baseList[index] = coordinates.uFloat(item, self.baseList[index].units) if item != None else \
#                     self.baseList[index]
#                 return True
#
#
# # --MACHINE STATE-----
# class state():
#     '''Elements which help keep track of machine state.'''
#
#     class coordinate(object):
#         '''A collection of coordinates which stores both actual (real-time) and future (buffered) machine positions.'''
#
#         def __init__(self, inputList):
#             self.actual = coordinates.baseCoordinate(inputList)
#             self.future = coordinates.baseCoordinate(inputList)
#
#         def update(self, inputList):
#             '''Updates last known real-time coordinate of machine.'''
#             return self.actual.set(inputList)
#
#         def commit(self, inputList):
#             '''Updates most recent change to machine position used for calculating future moves.'''
#             return self.future.set(inputList)
#
#
# # --ELEMENTS-----
# class elements():
#     class element(object):
#         '''Base class for mechanical elements.
#         In essence, elements scale and/or convert between units.'''
#
#         @classmethod
#         def forward(thisClass, inputParameter):
#             newInstance = thisClass(inputParameter)  # instantiates a new class with the specified input parameter
#             setattr(newInstance, 'forward',
#                     newInstance.transformForward)  # replaces reference to forward for future function calls
#             setattr(newInstance, 'reverse',
#                     newInstance.transformReverse)  # replaces reference to reverse for future function calls
#             return newInstance
#
#         @classmethod
#         def reverse(thisClass, inputParameter):
#             newInstance = thisClass(inputParameter)  # instantiates a new class with the specified input parameter
#             setattr(newInstance, 'forward',
#                     newInstance.transformForward)  # replaces reference to forward for future function calls
#             setattr(newInstance, 'reverse',
#                     newInstance.transformReverse)  # replaces reference to reverse for future function calls
#             if type(newInstance.transformation) == int or type(
#                     newInstance.transformation) == float:  # make sure not to reverse a list of elements
#                 newInstance.transformation = 1.0 / float(newInstance.transformation)  # invert transformation
#                 newInstance.inputUnits, newInstance.outputUnits = newInstance.outputUnits, newInstance.inputUnits  # flip units
#             if type(newInstance.transformation) == list: newInstance.transformation.reverse()  # flip element list
#             return newInstance
#
#         def init(self, inputUnits=None, outputUnits=None, transformation=None):
#             self.inputUnits = inputUnits
#             self.outputUnits = outputUnits
#             self.transformation = transformation
#
#         def transformForward(self,
#                              value):  # NOTE: THIS GETS REASSIGNED TO THE NAME "forward" ON INSTANTIATION BY CLASSMETHOD "forward"
#             if type(self.transformation) == list:  # transformation is a list of elements
#                 for element in self.transformation:  # transform value thru elements in forwards direction
#                     value = element.forward(value)
#                 return value
#
#             elif type(value) == coordinates.uFloat:  # input value is a uFloat, transform directly
#                 if value.units == self.inputUnits:  # input units match
#                     return coordinates.uFloat(value * self.transformation,
#                                               self.outputUnits)  # return a transformed uFloat in output units
#                 elif self.inputUnits:  # input units are specified for this element, enforce match
#                     newValue = value.convertUnits(self.inputUnits)  # try to convert to input units. i.e. mm to inch
#                     if newValue:
#                         return coordinates.uFloat(newValue * self.transformation,
#                                                   self.outputUnits)  # conversion successful, return a transformed uFloat in output units
#                     else:
#                         notice(self,
#                                'provided units ' + str(value.units) + ' but this element works in units of ' + str(
#                                    self.inputUnits) + ' in the forward direction.')
#                         return False
#                 else:  # no input units specified, transform anyways
#                     return coordinates.uFloat(value * self.transformation,
#                                               value.units)  # return a transformed uFloat in same units as input value
#
#             else:
#                 notice(self, 'expected an input of type uFloat but instead got ' + str(type(value)))
#                 return False
#
#         def transformReverse(self,
#                              value):  # NOTE: THIS GETS REASSIGNED TO THE NAME "reverse" ON INSTANTIATION BY CLASSMETHOD "reverse"
#             if type(self.transformation) == list:  # transformation is a list of elements
#                 reverseTransformation = copy.copy(self.transformation)
#                 reverseTransformation.reverse()
#                 for element in reverseTransformation:  # transform value thru elements in forwards direction
#                     value = element.reverse(value)
#                 return value
#
#             elif type(value) == coordinates.uFloat:  # input value is a uFloat, transform directly
#                 if value.units == self.outputUnits:  # output units match (going in reverse!)
#                     return coordinates.uFloat(value / float(self.transformation),
#                                               self.inputUnits)  # return a transformed uFloat in input units
#                 elif self.inputUnits:  # input units are specified for this element, enforce match
#                     newValue = value.convertUnits(self.outputUnits)  # try to convert to input units. i.e. mm to inch
#                     if newValue:
#                         return coordinates.uFloat(newValue / float(self.transformation),
#                                                   self.inputUnits)  # conversion successful, return a transformed uFloat in output units
#                     else:
#                         notice(self,
#                                'provided units ' + str(value.units) + ' but this element works in units of ' + str(
#                                    self.outputUnits) + ' in the reverse direction.')
#                         return False
#                 else:  # no input units specified, transform anyways
#                     return coordinates.uFloat(value / float(self.transformation),
#                                               value.units)  # return a transformed uFloat in same units as input value
#             else:
#                 notice(self, 'expected an input of type uFloat but instead got ' + str(type(value)))
#                 return False
#
#     class elementChain(element):
#         def __init__(self, elements):
#             if type(elements) == list:
#                 self.init(transformation=elements)
#             else:
#                 notice(self, 'expected input of type list but instead got ' + str(type(elements)))
#                 return None
#
#     class microstep(element):
#         def __init__(self, microstepCount):
#             self.init(inputUnits='usteps', outputUnits='steps',
#                       transformation=1 / float(microstepCount))  # microsteps -> 1/microstepCount -> steps
#             self.steps = self.transformForward
#             self.usteps = self.transformReverse
#
#     class stepper(element):
#         def __init__(self, stepAngle):
#             self.init(inputUnits='steps', outputUnits='rev',
#                       transformation=stepAngle / 360.0)  # steps -> stepAngle/360 -> revolutions
#             self.revolutions = self.transformForward  # (steps)
#             self.steps = self.transformReverse  # (revolutions)
#
#     class leadscrew(element):
#         def __init__(self, lead):
#             self.init(inputUnits='rev', outputUnits='mm', transformation=float(lead))  # revolutions -> lead -> travel
#             self.travel = self.transformForward  # (revolutions)
#             self.revolutions = self.transformReverse  # (travel)
#
#     class pulley(element):
#         def __init__(self, pitchDiameter):
#             self.init(inputUnits='rev', outputUnits='mm',
#                       transformation=float(math.pi * pitchDiameter))  # revolutions -> pitch circumference -> travel
#             self.travel = self.transformForward  # (revolutions)
#             self.revolutions = self.transformReverse  # (travel)
#
#     class invert(element):
#         def __init__(self, invert=False):
#             if not invert:
#                 self.init(transformation=1.0)
#             else:
#                 self.init(transformation=-1.0)
#
#
# # ---KINEMATICS-----
# class kinematics():
#     class matrix(object):
#         '''A base class for defining transformation matrices.'''
#
#         def __init__(self, array):
#             self.array = array
#             self.length = len(array[0])  # the number of columns of the array
#
#         def __call__(self, inputVector):
#             return self.transform(inputVector)
#
#         def transform(self, inputVector):
#             if len(inputVector) != len(self.array[0]):  # check to make sure that vectors match
#                 notice(self, 'vector length mismatch')
#                 return False
#             return [self.dot(row, inputVector) for row in self.array]
#
#         def dot(self, array1, array2):
#             # array1 is a dimensionless vector
#             # array2 has dimensions
#             dotProduct = 0.0
#             units = None
#             for index, value in enumerate(array1):
#                 dotProduct += float(array1[index]) * float(array2[index])
#                 if value != 0: units = array2[
#                     index].units  # takes on the units of the last vector whose value has contributed to the dot product
#             return coordinates.uFloat(dotProduct, units)
#
#     class identityMatrix(matrix):
#         '''A square matrix of size = order with 1's on the diagonal and zeros elsewhere.'''
#
#         def __init__(self, order):
#             self.array = [[1 if i == j else 0 for j in range(order)] for i in range(order)]
#             self.length = order
#
#     class routeForwardMatrix(matrix):
#         '''A square matrix which routes according to the provided routing list.'''
#
#         def __init__(self, routingList):
#             self.array = [[1 if index == value else 0 for index in range(len(routingList))] for value in routingList]
#             self.length = len(routingList)
#
#     class routeReverseMatrix(matrix):
#         '''A square matrix which routes according to the inverse of the provided routing list.'''
#
#         def __init__(self, routingList):
#             self.array = [[1 if index == value else 0 for value in routingList] for index in range(len(routingList))]
#             self.length = len(routingList)
#
#     class compoundMatrix(matrix):
#         '''A matrix which is composed of several matrices arranged along the diagonal.'''
#
#         def __init__(self, inputMatrices):
#             if type(inputMatrices) != list:  # make sure that input is a list
#                 notice(self, 'expected input of type list but instead got type ' + str(list))
#                 return False
#             self.arrays = inputMatrices
#             self.lengths = [array.length for array in inputMatrices]  # stores lengths of each array
#             self.length = sum(self.lengths)
#
#         def transform(self, inputVector):
#             splitInput = []
#             originPosition = 0
#             # split input vector into sections corresponding to transform array
#             for sectionLength in self.lengths:
#                 splitInput += [inputVector[originPosition:originPosition + sectionLength]]
#                 originPosition += sectionLength
#             # transform each section separately
#             transformedOutput = []
#             for index, input in enumerate(splitInput):
#                 transformedOutput += self.arrays[index].transform(input)
#             return transformedOutput
#
#     class transform(object):
#         '''Contains methods for transforming in the forwards and reverse directions.'''
#
#         def __init__(self, forwardMatrix, reverseMatrix):
#             self.forwardMatrix = forwardMatrix
#             self.reverseMatrix = reverseMatrix
#
#         def forward(self, inputVector):
#             return self.forwardMatrix.transform(inputVector)
#
#         def reverse(self, inputVector):
#             return self.reverseMatrix.transform(inputVector)
#
#     class direct(transform):
#         def __init__(self, order):
#             self.forwardMatrix = kinematics.identityMatrix(order)
#             self.reverseMatrix = kinematics.identityMatrix(order)
#
#     class route(transform):
#         def __init__(self, routingList):
#             self.forwardMatrix = kinematics.routeForwardMatrix(routingList)
#             self.reverseMatrix = kinematics.routeReverseMatrix(routingList)
#
#     class compound(transform):
#         def __init__(self, inputTransforms):
#             self.forwardMatrix = kinematics.compoundMatrix([transform.forwardMatrix for transform in inputTransforms])
#             self.reverseMatrix = kinematics.compoundMatrix([transform.reverseMatrix for transform in inputTransforms])
#
#     class hbot(transform):
#         def __init__(self, invertX=False, invertY=False):
#             invertX = {True: -1, False: 1}[invertX]
#             invertY = {True: -1, False: 1}[invertY]
#
#             self.forwardMatrix = kinematics.matrix([[0.5 * invertX, 0.5 * invertX], [0.5 * invertY, -0.5 * invertY]])
#             self.reverseMatrix = kinematics.matrix([[1 * invertX, 1 * invertY], [1 * invertX, -1 * invertY]])
#
#     class chain(transform):
#         '''Allows a series of kinematics to be chained together.'''
#
#         def __init__(self, forwardChain):
#             self.forwardChain = forwardChain
#             self.reverseChain = copy.copy(forwardChain)  # makes a shallow copy
#             self.reverseChain.reverse()  # reverses inputChain
#
#         def forward(self, inputVector):
#             for transform in self.forwardChain:
#                 inputVector = transform.forward(inputVector)
#             return inputVector
#
#         def reverse(self, inputVector):
#             for transform in self.reverseChain:
#                 inputVector = transform.reverse(inputVector)
#             return inputVector
#
#
