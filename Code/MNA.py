import numpy
import scipy.sparse as sparse
from scipy.sparse.linalg.dsolve import linsolve
from tkinter import *
from tkinter import messagebox
import time


# Parent class
class circuit_component:  # circuit component structure
    def __init__(self, comp_type, high_str, low_str, value):
        # component type as list
        self.comp_type = comp_type
        # nodes as strings
        self.high_str = high_str
        self.low_str = low_str
        # mapped nodes as integers
        self.high = -1
        self.low = -1
        # component's value
        self.value = value


class CSC:
    def __init__(self):
        self.rows = []
        self.columns = []
        self.data = []

    def insert(self, row, column, data):
        self.data.append(data)
        self.rows.append(row)
        self.columns.append(column)


# Main class
class MNA:
    def __init__(self, file_name, optimised):
        # Netlist text file
        self.file_name = file_name
        # Choose whether to use optimisation technique or not
        self.optimised = optimised
        # List of components
        self.components = []
        # Table for hashed nodes
        self.hash_table = {}
        # Number of voltages sources
        self.voltage_count = 0
        # Number of nodes
        self.node_count = 0
        # Size of the matrices
        self.matrix_size = 0
        # Dictionary of unit prefixes
        self.unit_prefixes = {'f': 'e-15', 'p': 'e-12', 'n': 'e-9', 'u': 'e-6', 'm': 'e-3', 'k': 'e3',
                              'M': 'e6', 'G': 'e9', 'T': 'e12'}

    def Parse_netlist(self):
        nodes = []
        lines = []

        # Open a netlist text file
        f = open(self.file_name, 'r')
        # Cycle through each netlist lines
        for line in f:
            # Add each line to a list
            lines.append(line.split())
        # Close the file
        f.close()

        # Cycle through component list
        for line in lines:
            # Add component's nodes
            nodes.append(line[1:3])
            # Convert component's unit prefix into a float value
            for prefix, prefix_value in self.unit_prefixes.items():
                # Find component's unit prefix in unit prefix dictionary
                if prefix in line[3]:
                    # Replace string with float value
                    line[3] = line[3].replace(prefix, prefix_value)
                    break

            # Create components
            self.components.append(circuit_component(line[0][0].upper(), line[1], line[2], float(line[3])))

            # Count number of independent voltage sources
            if line[0][0] == 'V':
                self.voltage_count += 1

        # Map string nodes to integer nodes
        self.Nodes()

    def Nodes(self):
        # Add zero to the hash table
        self.hash_table['0'] = self.node_count
        # Count number of nodes in the hash table
        self.node_count += 1

        # Loop through components
        for component in self.components:
            # If string node is not yet mapped
            if component.high_str not in self.hash_table:
                # String node gets mapped to integer node
                self.hash_table[component.high_str] = self.node_count
                # Count nodes
                self.node_count += 1
            # Repeat for low string nodes
            if component.low_str not in self.hash_table:
                self.hash_table[component.low_str] = self.node_count
                self.node_count += 1

            # Add high and low integer nodes to instance attributes
            component.high = self.hash_table[component.high_str]
            component.low = self.hash_table[component.low_str]

    def A_matrix(self):
        # Calculate matrix size
        self.matrix_size = self.node_count + self.voltage_count - 1
        # Get voltage index
        voltage_index = self.matrix_size - self.voltage_count
        # Create two dimensional A  matrix filled with zeros
        A = numpy.zeros((self.matrix_size, self.matrix_size))

        # Loop though components and fill the matrix accordingly
        for component in self.components:
            # Only independent voltage sources and resistors affect A matrix
            # A matrix is made up of four sub-matrices: G, B, C and D
            # D matrix consists entirely of zero values so it does not need to be filled

            # Independent voltage source
            if component.comp_type == 'V':
                # Affects B and C matrices
                # Rules for B matrix:
                #  - each column corresponds to a independent voltage source
                #  - 1 is written when node is connected to positive terminal
                #  - negative 1 is written when node is connected to negative terminal
                #  - 0 is written when it is not incident
                # C matrix is a transpose of B
                if component.high != 0:
                    # B matrix
                    A[component.high - 1][voltage_index] = A[component.high - 1][voltage_index] + 1
                    # C matrix
                    A[voltage_index][component.high - 1] = A[voltage_index][component.high - 1] + 1
                if component.low != 0:
                    # B matrix
                    A[component.low - 1][voltage_index] = A[component.low - 1][voltage_index] - 1
                    # C matrix
                    A[voltage_index][component.low - 1] = A[voltage_index][component.low - 1] - 1

                # Increase index
                voltage_index += 1

            # Resistor
            elif component.comp_type == 'R':
                # Affects G matrix
                # G matrix rules:
                #  - each line and row corresponds to a specific node
                #  - diagonal is positive and contains total self conductance of each node
                #  - non-diagonal are negative and containing the mutual conductance between nodes

                # Diagonal self-conductance of node
                if component.high != 0:
                    A[component.high - 1][component.high - 1] = A[component.high - 1][
                                                                    component.high - 1] + 1 / component.value
                if component.low != 0:
                    A[component.low - 1][component.low - 1] = A[component.low - 1][
                                                                  component.low - 1] + 1 / component.value

                # Mutual conductance between nodes
                if component.high != 0 and component.low != 0:
                    A[component.high - 1][component.low - 1] = A[component.high - 1][
                                                                   component.low - 1] - 1 / component.value
                    A[component.low - 1][component.high - 1] = A[component.low - 1][
                                                                   component.high - 1] - 1 / component.value

        return A

    def z_matrix(self):
        # Calculate matrix size
        self.matrix_size = self.node_count + self.voltage_count - 1

        # Get voltage index
        if self.optimised:
            if self.voltage_count > 0:
                voltage_index = self.matrix_size - self.voltage_count
            else:
                voltage_index = 0
        else:
            voltage_index = self.matrix_size - self.voltage_count

        # Create one dimensional z matrix filled with zeros
        z = numpy.zeros(self.matrix_size)

        # Loop though components and fill the matrix accordingly
        for component in self.components:
            # z matrix holds values of independent voltage and current sources
            # It consists of i and e sub-matrices

            # Independent voltage source
            if component.comp_type == 'V':
                # Affects e matrix
                # Rules for e matrix:
                #  - its size corresponds to number of independent voltage sources
                #  - holds the values of corresponding independent voltage sources

                # Voltage vale gets added to matrix
                z[voltage_index] = component.value

                # Increase index
                voltage_index += 1

            # Independent current source
            elif component.comp_type == 'I':
                # Affects i matrix
                # Rules for i matrix:
                #  - each element in the matrix corresponds to a particular node
                #  - consists of the sum of the currents flowing through the passive components
                #  - if there are no current sources connected to the node, the current value is 0
                if component.high != 0:
                    # Negative current value gets added to matrix
                    z[component.high - 1] = z[component.high - 1] - component.value
                if component.low != 0:
                    # Positive current value gets added to matrix
                    z[component.low - 1] = z[component.low - 1] + component.value

        return z

    def Optimised_A_matrix(self):
        # Calculate matrix size
        self.matrix_size = self.node_count + self.voltage_count - 1

        # Create lists for constructing CSC
        Sparse = CSC()

        # Get voltage index
        if self.voltage_count > 0:
            voltage_index = self.matrix_size - self.voltage_count
        else:
            voltage_index = 0

        # loop through all components
        for component in self.components:

            if component.comp_type == 'R':
                # affects G matrix
                # diagonal self-conductance of node
                if component.high != 0:
                    Sparse.insert(component.high - 1, component.high - 1, 1 / component.value)
                if component.low != 0:
                    Sparse.insert(component.low - 1, component.low - 1, 1 / component.value)

                # mutual conductance between nodes
                if component.high != 0 and component.low != 0:
                    Sparse.insert(component.high - 1, component.low - 1, 1 / component.value)
                    Sparse.insert(component.low - 1, component.high - 1, 1 / component.value)

            elif component.comp_type == 'V':
                # affects the B and C
                if component.high != 0:
                    Sparse.insert(component.high - 1, voltage_index, 1)
                    Sparse.insert(voltage_index, component.high - 1, 1)
                if component.low != 0:
                    Sparse.insert(component.low - 1, voltage_index, 1)
                    Sparse.insert(voltage_index, component.low - 1, 1)

                # Increase index
                voltage_index = voltage_index + 1

        # Setup sparse A matrix
        matrix = sparse.coo_matrix((Sparse.data, (Sparse.rows, Sparse.columns)),
                                   shape=(self.matrix_size, self.matrix_size))

        # convert to CSC matrix format
        A = matrix.tocsc()

        return A

    def x_matrix(self):
        # Get z matrix
        z = self.z_matrix()
        # Get A
        # Choose whether to use sparse optimisation or not
        if self.optimised:
            A = self.Optimised_A_matrix()
            # Solve linear matrix equation
            x = linsolve.spsolve(A, z)
        else:
            A = self.A_matrix()
            # Solve linear matrix equation
            x = numpy.linalg.solve(A, z)

        return x

    def print_results(self, x):
        # Create text with calculated values which gets displayed to the user
        node_voltages_text = 'Voltage potential on each node:\n'
        # Count x matrix index
        count = 0

        # Loop through nodes to allocate appropriate nodal voltages
        for node in self.hash_table:
            if node != '0':
                node_voltages_text += 'node' + str(self.hash_table[node]) + ': '

                #  Display calculated nodal voltages
                if x[count] > 0:
                    # Format value to three decimal places
                    node_voltages_text += str('{:.3f}'.format(x[count])) + ' V\n'

                # If the value is negative, multiply by -1 to get positive value
                else:
                    node_voltages_text += str(float('{:.3f}'.format(x[count])) * (-1)) + ' V\n'

                # Count x matrix index
                count += 1

        # Check how many voltages sources there in the circuit
        if self.voltage_count > 1:
            current_of_voltage_source_text = '\nCurrents flowing through independent voltage sources:\n'
        else:
            current_of_voltage_source_text = '\nCurrent flowing through independent voltage source:\n'

        # Loop through independent nodal voltages to allocate appropriate current values
        for v in range(self.voltage_count):
            current_of_voltage_source_text += 'Current through V' + str(v + 1) + ': '

            # Display currents flowing through independent voltage sources
            if x[count] > 0:
                # Format value to three decimal places
                current_of_voltage_source_text += str('{:.3f}'.format(x[count])) + ' A\n'

            # If the value is negative, multiply by -1 to get positive value
            else:
                current_of_voltage_source_text += str('{:.3f}'.format(x[count] * (-1))) + ' A\n'

            # Count x matrix index
            count += 1

        # Create the final message
        text = node_voltages_text + current_of_voltage_source_text

        # Display the message using tkinter message box
        title = "MNA results"
        root = Tk()
        root.withdraw()
        messagebox.showinfo(title, text)
