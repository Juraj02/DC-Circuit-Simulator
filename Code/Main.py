import pygame
from pygame.locals import *
from tkinter import *
from tkinter import messagebox
import numpy
import os
from MNA import circuit_component, CSC, MNA


# Initialise pygame
pygame.init()

# Define constants
# Get screen width and screen height
infoObject = pygame.display.Info()
# Width of the screen
WIDTH = infoObject.current_w - 380
# Height of the screen
HEIGHT = infoObject.current_h - 280
# Define colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
# Frames per second
fps = 60
# Coordinates on the screen where component's value and unit prefix are displayed
value_box = pygame.Rect(20, 520, 150, 40)
unit_prefix_box = pygame.Rect(20, 560, 60, 40)

# Define variables
# Counts independent voltage sources in the main tab
independent_voltage_source_count = 0
# Counts independent current sources in the main tab
independent_current_source_count = 0
# Counts resistors in the main tab
resistor_count = 0
# Booleans controlling when component's value or unit prefix can be changed
value_box_active = False
unit_prefix_box_active = False
# Program will run until 'done' becomes True
done = False

# Used to manage how fast the screen updates
clock = pygame.time.Clock()
# Opening the program's window
screen = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)
# Title of the program's window
pygame.display.set_caption('DC Circuit Simulator')

# Load component's images
independent_voltage_source = pygame.image.load("images/independent_voltage_source.png").convert_alpha()
independent_voltage_source_selected = pygame.image.load(
    "images/independent_voltage_source_selected.png").convert_alpha()
independent_voltage_source_left_side = pygame.image.load(
    "images/independent_voltage_source_left_side.png").convert_alpha()
independent_voltage_source_right_side = pygame.image.load(
    "images/independent_voltage_source_right_side.png").convert_alpha()
independent_current_source = pygame.image.load("images/independent_current_source.png").convert_alpha()
independent_current_source_selected = pygame.image.load(
    "images/independent_current_source_selected.png").convert_alpha()
independent_current_source_left_side = pygame.image.load(
    "images/independent_current_source_left_side.png").convert_alpha()
independent_current_source_right_side = pygame.image.load(
    "images/independent_current_source_right_side.png").convert_alpha()
resistor = pygame.image.load("images/resistor.png").convert_alpha()
resistor_selected = pygame.image.load("images/resistor_selected.png").convert_alpha()
resistor_left_side = pygame.image.load("images/resistor_left_side.png").convert_alpha()
resistor_right_side = pygame.image.load("images/resistor_right_side.png").convert_alpha()


# Sprite class which creates components in the main tab
class Component(pygame.sprite.Sprite):
    # Netlist of the circuit
    netlist = []
    # Class attributes used for validating value and unit prefix from user input
    # Value can consist of only numbers and a decimal point
    allowed_values = '1234567890.'
    # Unit prefix letters allowed in the metric system
    allowed_unit_prefixes = 'fpnumkMGT'

    def __init__(self, x_component_pos, y_component_pos, id):
        # Component instances which will be different for every component
        super(Component, self).__init__()
        # Component's image
        self.image = image
        # Variables which hold component's current position
        self.rect = self.image.get_rect()
        self.rect.y = y_component_pos
        self.rect.x = x_component_pos
        # Unique number for every component
        self.id = id
        # Boolean showing if component is clicked
        # Variable used for changing component's position
        self.clicked = False
        # Boolean showing if component is selected
        # Variable is used for displaying components characteristics
        self.selected = False
        # Boolean showing if component is ready for connecting
        # Variable used for connecting two components together
        self.ready = False
        # Boolean showing if component's right side is selected
        self.RightSide = False
        # Boolean showing if component's left side is selected
        self.LeftSide = False
        # List of connections to the right side of a component
        self.right_links = []
        # List of connections to the left side of a component
        self.left_links = []
        # Variable counting number of times a component was clicked.
        # This variable will be used to determine whether a component is selected or not.
        # Component is only selected when it is clicked odd number of times.
        self.clicked_count = 0
        # Type of component (voltage source, current source or resistor)
        self.type = component_type
        # Unique name made from component's type and number of same type components in the main tab
        self.name_id = name_id
        # Component's value
        self.value = value
        # Component's unit prefix
        self.unit_prefix = unit_prefix
        # Component's unit
        self.unit = unit
        # Nodes a component is connected to
        self.high_node = ''
        self.low_node = ''

    #  When a component is selected, its characteristics get displayed in the component tab
    def display_characteristics(self):
        # Define fonts
        name_font = pygame.font.SysFont('Calibre', 100)
        font = pygame.font.SysFont('Calibre', 45)
        description_font = pygame.font.SysFont('Calibre', 24)

        # Name label
        text_name = name_font.render(self.type + str(self.name_id), 1, BLACK)
        # Label's position is such that no matter it's width, it will always be centered
        text_name_rect = text_name.get_rect(center=(95, 487))

        # Value label
        text_value = font.render(self.value, 1, BLACK)
        # Unit prefix label
        text_unit_prefix = font.render(self.unit_prefix, 1, BLACK)
        # Unit label
        text_unit = font.render(self.unit, 1, BLACK)

        # Add labels to the screen
        screen.blit(text_name, text_name_rect)
        screen.blit(text_value, (30, 530))
        screen.blit(text_unit_prefix, (30, 560))
        screen.blit(text_unit, (57, 560))

        # Draw lines to separate name, value and description labels
        pygame.draw.line(screen, BLACK, (17, 520), (166, 520), 7)
        pygame.draw.line(screen, BLACK, (17, 595), (166, 595), 7)

        # If clicked, value box or unit prefix box become active
        # This means that a user can now change the value or unit prefix
        # A vertical line is drawn to indicate a box is active
        if value_box_active:
            pygame.draw.line(screen, BLACK, (30 + text_value.get_width(), 530), (30 + text_value.get_width(), 555), 3)
        elif unit_prefix_box_active:
            pygame.draw.line(screen, BLACK, (30 + text_unit_prefix.get_width(), 560),
                             (30 + text_unit_prefix.get_width(), 585), 3)

        # Description labels
        # Each component type has different description label
        if self.type == 'V':
            description1 = description_font.render('A component', 1, BLACK)
            description2 = description_font.render('with two distinct', 1, BLACK)
            description3 = description_font.render('terminals that', 1, BLACK)
            description4 = description_font.render('provides', 1, BLACK)
            description5 = description_font.render('constant voltage', 1, BLACK)
            description6 = description_font.render('independent of', 1, BLACK)
            description7 = description_font.render('current drawn', 1, BLACK)
            description8 = description_font.render('from it.', 1, BLACK)

            screen.blit(description1, (28, 602))
            screen.blit(description2, (28, 621))
            screen.blit(description3, (28, 640))
            screen.blit(description4, (28, 659))
            screen.blit(description5, (27, 678))
            screen.blit(description6, (28, 697))
            screen.blit(description7, (28, 716))
            screen.blit(description8, (28, 735))

        if self.type == 'I':
            description1 = description_font.render('A component', 1, BLACK)
            description2 = description_font.render('with two distinct', 1, BLACK)
            description3 = description_font.render('terminals that', 1, BLACK)
            description4 = description_font.render('supplies the', 1, BLACK)
            description5 = description_font.render('same current to', 1, BLACK)
            description6 = description_font.render('any load', 1, BLACK)
            description7 = description_font.render('connected', 1, BLACK)
            description8 = description_font.render('across', 1, BLACK)
            description9 = description_font.render('its terminals.', 1, BLACK)

            screen.blit(description1, (28, 602))
            screen.blit(description2, (28, 621))
            screen.blit(description3, (28, 640))
            screen.blit(description4, (28, 659))
            screen.blit(description5, (28, 678))
            screen.blit(description6, (28, 697))
            screen.blit(description7, (28, 716))
            screen.blit(description8, (28, 735))
            screen.blit(description9, (28, 754))

        if self.type == 'R':
            description1 = description_font.render('A component', 1, BLACK)
            description2 = description_font.render('used to reduce', 1, BLACK)
            description3 = description_font.render('current flow and', 1, BLACK)
            description4 = description_font.render('drop voltage', 1, BLACK)
            description5 = description_font.render('potentials by', 1, BLACK)
            description6 = description_font.render('absorbing', 1, BLACK)
            description7 = description_font.render('electric energy.', 1, BLACK)

            screen.blit(description1, (28, 602))
            screen.blit(description2, (28, 621))
            screen.blit(description3, (28, 640))
            screen.blit(description4, (28, 659))
            screen.blit(description5, (28, 678))
            screen.blit(description6, (28, 697))
            screen.blit(description7, (28, 716))


# Class for creating buttons
class button:
    def __init__(self, x_button_pos, y_button_pos, width, height, colour, surface):
        # Button position
        self.x = x_button_pos
        self.y = y_button_pos
        # Button width
        self.width = width
        # Button Height
        self.height = height
        # Button colour
        self.color = colour
        #   
        self.surface = surface

    # Draw a button
    def draw_button(self):
        pygame.draw.rect(self.surface, self.color, (self.x, self.y, self.width, self.height))

    # Check if button is pressed
    def is_pressed(self):
        # Get mouse position
        mouse_position = pygame.mouse.get_pos()
        mouse_x = mouse_position[0]
        mouse_y = mouse_position[1]

        # If button's and mouse's positions are same, a button is pressed
        if self.x < mouse_x < self.x + self.width:
            if self.y < mouse_y < self.y + self.height:
                mouse_click = pygame.mouse.get_pressed()
                left_click = mouse_click[0]
                if left_click:
                    return True
        return False


# Tinker's message box for giving the user feedback based on their input
def message_box():
    # Window's title
    title = "DC Circuit Simulator Message"
    # Initialise tkinter
    root = Tk()

    # Warn the user about an error they made
    if message_type == 'warning':
        # Hide the main Tkinter window
        root.withdraw()
        # Display only Tkinter message box with appropriate text
        messagebox.showwarning(title, text)

    # Show information to the user
    elif message_type == 'info':
        root.withdraw()
        messagebox.showinfo(title, text)

    # Ask user a question with yes and no answer options
    elif message_type == 'yesno':
        root.withdraw()
        response = messagebox.askyesno(title, text)
        return response

    # Instructions for using the simulator
    elif message_type == 'instructions':
        root.withdraw()
        messagebox.showinfo(title, text)


# Draw GUI
# Draw main tab
# Place on the screen for building a circuit
def main_tab():
    # First draw a white rectangle, then add black lines to create grid like structure
    pygame.draw.rect(screen, WHITE, (0, 60, WIDTH, HEIGHT))

    # Dimensions of each grid
    width = 185
    height = 60
    # While loop for drawing black lines
    while width < WIDTH or height < HEIGHT:
        width += 150
        height += 150
        pygame.draw.line(screen, BLACK, (width, 60), (width, HEIGHT), 2)
        pygame.draw.line(screen, BLACK, (185, height), (WIDTH, height), 2)


# Draw toolbar
# Top part of the screen where all the buttons are placed
def toolbar():
    # Dimensions of the buttons
    width = 120
    height = 50
    # Coordinates of buttons
    clear_x = 0
    clear_y = 5
    undo_x = width + 5
    undo_y = 5
    help_x = 2 * (width + 5)
    help_y = 5
    build_x = 3 * (width + 5)
    build_y = 5

    # Font for every button
    button_font = pygame.font.SysFont('Calibre', 50)

    # Button labels
    clear_text = button_font.render('Clear', 1, BLACK)
    undo_text = button_font.render('Undo', 1, BLACK)
    help_text = button_font.render('Help', 1, BLACK)
    build_text = button_font.render('Build', 1, BLACK)

    # Each label is centered in their button
    clear_text_rect = clear_text.get_rect(center=(clear_x + width // 2, clear_y + height // 2))
    undo_text_rect = undo_text.get_rect(center=(undo_x + width // 2, undo_y + height // 2))
    help_text_rect = help_text.get_rect(center=(help_x + width // 2, help_y + height // 2))
    build_text_rect = build_text.get_rect(center=(build_x + width // 2, build_y + height // 2))

    # Draw each button using Button class methode
    clear_button.draw_button()
    undo_button.draw_button()
    help_button.draw_button()
    build_button.draw_button()

    # Add labels to the screen
    screen.blit(clear_text, clear_text_rect)
    screen.blit(undo_text, undo_text_rect)
    screen.blit(help_text, help_text_rect)
    screen.blit(build_text, build_text_rect)


# Draw component tab
# A grey area on the left side of the screen
# A place where user can add component's to main tab and check their their characteristics
def component_tab():
    # Draw a grey 3 rectangles
    # Draw the big grey rectangle which covers whole component tab
    pygame.draw.rect(screen, GREY, (0, 60, 185, 750))
    # Draw a smaller black rectangle and a grey rectangle for displaying component's characteristics
    pygame.draw.rect(screen, BLACK, (17, 440, 150, 345))
    pygame.draw.rect(screen, GREY, (26, 450, 132, 325))

    # Add component images to the screen
    screen.blit(independent_voltage_source_selected, (17, 70))
    screen.blit(independent_current_source_selected, (17, 190))
    screen.blit(resistor_selected, (17, 310))


# Create buttons in the toolbar
clear_button = button(0, 5, 120, 50, WHITE, screen)
undo_button = button(125, 5, 120, 50, WHITE, screen)
help_button = button(250, 5, 120, 50, WHITE, screen)
build_button = button(375, 5, 120, 50, WHITE, screen)

# List containing all components which are currently in the main tab
component_list = pygame.sprite.Group()

# Main program loop
while not done:
    # Main event loop
    for event in pygame.event.get():
        # If the user presses down a key on the keyboard
        if event.type == pygame.KEYDOWN:
            # Escape key
            if event.key == pygame.K_ESCAPE:
                # Exit the loop
                done = True

            # Loop through components to check for value or unit prefix  input from the user
            for component in component_list:
                # Check for only selected component (component whose characteristics are displayed)
                if component.selected:
                    # Value ready for input
                    if value_box_active:

                        # Return key
                        if event.key == pygame.K_RETURN:
                            # Validation
                            # Presence check
                            if len(component.value) == 0 or component.value == '.':
                                # Display warning message to the user with tkinter messagebox
                                text = "No value entered. Please enter component's value."
                                message_type = 'warning'
                                message_box()
                            # Range check
                            elif float(component.value) == 0:
                                # Display warning tkinter message
                                text = "Component's value cannot be zero. Please enter a valid value."
                                message_type = 'warning'
                                message_box()
                            # Value is valid
                            else:
                                # Close value box for user input
                                value_box_active = False
                                # Format value to 3 decimal places and store it
                                component.value = str('{:.3f}'.format(float(component.value)))

                        # Backspace key
                        elif event.key == pygame.K_BACKSPACE:
                            # Delete last digit
                            component.value = component.value[:-1]

                        # Any other key
                        else:
                            # Validation
                            valid = False
                            # Cross-reference check
                            for key in component.allowed_values:
                                # Compare user's input to allowed values
                                if key == event.unicode:
                                    valid = True
                            # User input is valid
                            if valid:
                                # Add user input to component's value
                                component.value += event.unicode
                            else:
                                # Display warning tkinter message
                                text = "Only numbers can be entered as a component's value."
                                message_type = 'warning'
                                message_box()

                    # Unit prefix ready for input
                    elif unit_prefix_box_active:

                        # Return key
                        if event.key == pygame.K_RETURN:
                            # Close unit prefix box for user input
                            unit_prefix_box_active = False

                        # Backspace key
                        elif event.key == pygame.K_BACKSPACE:
                            # Delete last digit
                            component.unit_prefix = component.unit_prefix[:-1]

                        # Any other key
                        else:
                            # Validation
                            valid_length = False
                            valid_prefix = False
                            # Cross-reference check
                            for key in component.allowed_unit_prefixes:
                                # Compare user input to allowed unit prefixes
                                if key == event.unicode:
                                    valid_prefix = True

                            # Length check
                            if len(component.unit_prefix) < 1:
                                # Unit prefix can be made up of only one letter
                                # Or component does not need to have a unit prefix
                                valid_length = True

                            # User input is valid
                            if valid_length and valid_prefix:
                                # Add user input
                                component.unit_prefix += event.unicode

                            # Invalid user input
                            elif not valid_prefix:
                                # Display warning tkinter message
                                text = "Unknown unit prefix entered. Please enter a valid unit prefix.\n" \
                                       "Valid unit prefixes: 'f', 'p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T'."
                                message_type = 'warning'
                                message_box()

                            # Invalid length
                            elif not valid_length:
                                # Display warning tkinter message
                                text = "Unit prefix can be only one character."
                                message_type = 'warning'
                                message_box()

        # Quit button
        if event.type == pygame.QUIT:
            # Exit the loop
            done = True

        # 'Clear' button gets pressed
        if clear_button.is_pressed():
            # Check is there are any components in the main tab
            if len(component_list) != 0:
                # Delete all components
                component_list.empty()
                # Set component type counts to 0
                independent_voltage_source_count = 0
                independent_current_source_count = 0
                resistor_count = 0

        # 'Undo' button gets pressed
        if undo_button.is_pressed():
            for component in component_list:
                # Find last component added to the main tab
                if len(component_list) == component.id:
                    # Loop through all components again
                    for component2 in component_list:
                        # Check if deleted component id is in any links lists
                        if component.id in component2.right_links:
                            # Delete component id from every links list
                            component2.right_links.remove(component.id)
                        if component.id in component2.left_links:
                            component2.left_links.remove(component.id)
                    # Delete the component
                    component.kill()

        # 'Help' button gets pressed
        if help_button.is_pressed():
            # Display program's instructions
            message_type = 'instructions'
            text = "Add components to the main tab:\n" \
                   "   - left mouse click on component's image\n\n" \
                   "Connect two components together:\n" \
                   "   - right mouse click on left or right side of first the component\n" \
                   "   - another right mouse click on left or right side of the second component\n\n" \
                   "Change component's value:\n" \
                   "   - left mouse click on the component\n" \
                   "   - left mouse click on component's value\n" \
                   "   - type in new value\n" \
                   "   - click the 'ENTER' key to save the new value\n\n" \
                   "Change component's unit prefix:\n" \
                   "   - left mouse click on the component\n" \
                   "   - left mouse click on component's unit prefix (in front of component's unit)\n" \
                   "   - type in the new unit prefix\n" \
                   "   - click the 'ENTER' key to save the new unit prefix\n\n" \
                   "Clear button:\n" \
                   "   - deletes all components in the main tab\n\n" \
                   "Undo button:\n" \
                   "   - deletes the last component added to the main tab\n\n" \
                   "Build button:\n" \
                   "   - initialize MNA to calculate the results\n\n" \
                   "'Esc' key or 'x' symbol:\n" \
                   "   - press to close the simulator"

            message_box()

        # 'Build'  button gets pressed
        if build_button.is_pressed():
            # Variable which will contain all lists of links
            nodes = []
            # Variable indicating whether to initialise MNA or not
            error = False

            # Validation
            # Only one component is in the main tab
            if len(component_list) < 2:
                # Error detected so MNA won't be initialised
                error = True
                # Display warning tkinter message
                message_type = 'warning'
                text = "Not enough components to construct a circuit.\nPlease add more components."
                message_box()
                break

            for component in component_list:
                # Not all components are connected in a circuit
                if len(component.right_links) == 0 or len(component.left_links) == 0:
                    # Error detected so MNA won't be initialised
                    error = True
                    # Display warning tkinter message
                    message_type = 'warning'
                    text = "Not all components are connected in a circuit.\nPlease connect all components."
                    message_box()
                    break

            if not error:
                # Try creating a netlist
                try:
                    # Loop through components
                    for component in component_list:
                        # Add all links lists to nodes
                        nodes.append(component.right_links)
                        nodes.append(component.left_links)

                    # Remove any redundant nodes
                    for node in nodes:
                        while nodes.count(node) != 1:
                            nodes.remove(node)

                    # Remove nodes which can be made from other nodes
                    # Example: nodes = [[1,2], [1,2,3]]
                    # Node [1,2] can be made from node [1,2,3], but Node [1,2,3] can be made from node [1,2]
                    # Therefore, node [1,2] needs to be removed from the nodes list
                    nodes_to_remove = []  # List of nodes which need to be removed
                    # Loop through modes
                    for node1 in nodes:
                        # Loop through nodes again
                        for node2 in nodes:
                            # Variable which will temporarily hold component ids
                            node_hold = []
                            # Makes sure two nodes are not the same node
                            if node1 != node2:
                                # Loop though ids in the first node
                                for link1 in node1:
                                    # Loop through ids in the second node
                                    for link2 in node2:
                                        # Compare two ids
                                        if link1 == link2:
                                            # Append to the hold variable and eventually create a new node
                                            node_hold.append(link1)
                            # Compare second node to newly created node
                            if node2 == node_hold:
                                # If two nodes are the same, second node needs to be removed from the nodes list
                                nodes_to_remove.append(node2)

                    # After loop through nodes list, remove unwanted nodes
                    for node in nodes_to_remove:
                        nodes.remove(node)

                    # Determine which nodes each component is connected to
                    # Determine which node is high component's node and which is low component's node
                    for component in component_list:
                        # Loop through components and nodes
                        for node in nodes:
                            # Variable which will hold component ids
                            node_hold = []
                            # Loop through ids in nodes
                            for link1 in node:
                                # Loop through ids in component's right links list
                                for link2 in component.right_links:
                                    # Compare two component ids
                                    if link1 == link2:
                                        # Two ids are same, so id gets added to the hold variable to create a new node
                                        node_hold.append(link1)
                            # Compare component's right links list to newly created node
                            if component.right_links == node_hold:
                                # Two nodes are same so node becomes component's low node
                                component.low_node = nodes.index(node)
                            # Repeat the procedure for components left links list
                            # This will create component's high node
                            node_hold = []
                            for link1 in node:
                                for link2 in component.left_links:
                                    if link1 == link2:
                                        node_hold.append(link1)
                            if component.left_links == node_hold:
                                component.high_node = nodes.index(node)


                # Components are connected in such way that a short circuit was created
                except ValueError:
                    # Display warning tkinter message
                    message_type = 'warning'
                    text = "Circuit was not built properly.\nPlease try again."
                    message_box()
                    break

                # Create a netlist text file
                f = open('dc_circuit.txt', 'w')
                # Loop through components
                for component in component_list:
                    # Add needed information of every component to the file
                    component.netlist = [str(component.type) + str(component.name_id) + ' ',
                                         str(component.high_node) + ' ',
                                         str(component.low_node) + ' ',
                                         str(component.value) + str(component.unit_prefix)]
                    # In each line write information of one component
                    f.writelines(component.netlist)
                    f.write('\n')
                # Close the file
                f.close()

                # MNA
                netlist_file = 'dc_circuit.txt'
                # Initialise MNA

                circuit = MNA(netlist_file, False)
                # Parse file
                circuit.Parse_netlist()

                # Try filling the matrices and solving the matrix equation
                try:
                    # Solve matrix equation for unknown nodal voltages and current going through voltage sources
                    x_matrix = circuit.x_matrix()
                    # Print results of the MNA equation
                    circuit.print_results(x_matrix)


                # There is an error in the circuit so it cannot results cannot be calculated properly
                except numpy.linalg.LinAlgError:
                    # Display warning tkinter message
                    message_type = 'warning'
                    text = "Circuit was not built properly.\nPlease try again"
                    message_box()
                    break

                # Ask the user if they would like to save the netlist file
                message_type = 'yesno'
                text = "Would you like to save the netlist to a text file?"
                save = message_box()

                # User wants to save the file
                if save:
                    # Create file name
                    number = 1
                    path = 'dc_circuit' + str(number) + '.txt'
                    # Check if a file with that name exists
                    file_exists = os.path.isfile(path)
                    if file_exists:
                        # Create new file name
                        while file_exists:
                            number += 1
                            path = 'dc_circuit' + str(number) + '.txt'
                            file_exists = os.path.isfile(path)
                    else:
                        pass

                    # Open new file and netlist file
                    with open('dc_circuit.txt', 'r') as first_file, open(path, 'a') as second_file:
                        # Read content from netlist file
                        for line in first_file:
                            # Append content to new file
                            second_file.write(line)
                    # Close both files
                    first_file.close()
                    second_file.close()

                    # Inform the user that the file is saved
                    message_type = 'info'
                    text = "File is saved under the name '" + str(path) + "'"
                    message_box()

                #  Pass if user does not want to save the file
                else:
                    pass


        # When the user presses a button a mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Get mouse position
            pos = pygame.mouse.get_pos()
            x = pos[0]
            y = pos[1]

            # Left mouse click
            if event.button == 1:
                # Boxes for displaying component values
                if value_box.collidepoint(event.pos):
                    # Ready for user input
                    value_box_active = True
                else:
                    value_box_active = False

                #  Boxes for displaying unit prefixes
                if unit_prefix_box.collidepoint(event.pos):
                    # Ready for user input
                    unit_prefix_box_active = True
                else:
                    unit_prefix_box_active = False

                # When image of a component in the component tab gets clicked, a new component is added to the main tab.
                # Position of independent voltage source image
                if 10 < x < 160 and 70 < y < 180:
                    # Define component's characteristics specific for each component
                    independent_voltage_source_count += 1
                    name_id = independent_voltage_source_count
                    # Define component's characteristics specific for component's type
                    image = independent_voltage_source
                    component_type = 'V'
                    # Value and unit prefix are predefined but they can be changed later
                    value = '9.00'
                    unit_prefix = ''
                    unit = 'V'
                    # Create a component using Component class
                    # Component appears in the fixed position in the main tab
                    # Create new id
                    component_list.add(Component(200, 70, len(component_list) + 1))

                # Same procedure is repeated for adding independent current sources and resistors
                # Position of independent current source image
                elif 10 < x < 160 and 190 < y < 300:
                    independent_current_source_count += 1
                    name_id = independent_current_source_count
                    image = independent_current_source
                    component_type = 'I'
                    value = '1.00'
                    unit_prefix = ''
                    unit = 'A'
                    component_list.add(Component(200, 190, len(component_list) + 1))

                # Position of resistor image
                elif 10 < x < 160 and 310 < y < 420:
                    resistor_count += 1
                    name_id = resistor_count
                    image = resistor
                    component_type = 'R'
                    value = '10.00'
                    unit_prefix = ''
                    unit = 'Ω'
                    component_list.add(Component(200, 310, len(component_list) + 1))

                # Loop through all component to check if a component was clicked
                for component in component_list:
                    # Compare component's position to mouse position.
                    # If collision detected
                    if component.rect.collidepoint(pos):
                        # Component gets clicked
                        component.clicked = True
                        component.clicked_count += 1
                        # If component was clicked odd number of times
                        if component.clicked_count % 2 != 0:
                            # Component gets selected and its characteristics get displayed in component tab
                            component.selected = True
                        # If component is clicked on again (now even number of times)
                        else:
                            # Component is no longer selected and its characteristics are no longer displayed
                            component.selected = False
                    # If there is no collision
                    else:
                        # User clicks anywhere in the main tab
                        if 185 < x < WIDTH and 60 < y < HEIGHT:
                            # # Component is no longer selected and its characteristics are no longer displayed
                            component.selected = False

            # Right mouse click
            elif event.button == 3:

                # Loop through components to check if any were clicked
                for component in component_list:
                    # If mouse position collides with component's position
                    if component.rect.collidepoint(pos):
                        # Component is ready for connecting
                        component.ready = True
                        # Define variables
                        # Count components which are ready
                        count = 0
                        # List of component's ids which are ready
                        links = []

                        # Check which side of the component has been clicked
                        if component.rect.x < x < (component.rect.x + component.rect.width // 2):
                            if component.rect.y < y < (component.rect.y + component.rect.height):
                                # Left side is ready for connecting
                                component.LeftSide = True
                        elif (component.rect.x + component.rect.width // 2) < x \
                                < component.rect.x + component.rect.width:
                            if component.rect.y < y < (component.rect.y + component.rect.height):
                                # Right side is ready for connecting
                                component.RightSide = True

                        # Change image of the component to display which side of the component is ready for connecting
                        if component.image == independent_voltage_source and component.LeftSide:
                            component.image = independent_voltage_source_left_side
                        elif component.image == independent_voltage_source and component.RightSide:
                            component.image = independent_voltage_source_right_side
                        if component.image == independent_current_source and component.LeftSide:
                            component.image = independent_current_source_left_side
                        elif component.image == independent_current_source and component.RightSide:
                            component.image = independent_current_source_right_side
                        if component.image == resistor and component.LeftSide:
                            component.image = resistor_left_side
                        elif component.image == resistor and component.RightSide:
                            component.image = resistor_right_side

                        # Loop through components
                        for component in component_list:
                            if component.ready:
                                count += 1
                                links.append(component.id)

                            # Connect two components which are ready for connecting
                            if count == 2:
                                for component in component_list:
                                    if component.ready:
                                        # Component is no longer ready for connecting
                                        component.ready = False
                                        # Component's right side was clicked
                                        if component.RightSide:
                                            # Add components id to the links list
                                            component.right_links += links
                                            # Right side is no longer ready for connecting
                                            component.RightSide = False
                                        # Component's left side was clicked
                                        elif component.LeftSide:
                                            # Add components id to the links list
                                            component.left_links += links
                                            # Left side is no longer ready for connecting
                                            component.LeftSide = False

                                        # Two new component ids are now added to the links lists.
                                        # A components id might be stored in its own links lists more than once.
                                        # Remove any redundant component ids in links lists.
                                        # Loop through right links list
                                        for link_id in component.right_links:
                                            # Loop until there is no more than one same component id in the list
                                            while component.right_links.count(link_id) != 1:
                                                # Delete redundant id
                                                component.right_links.remove(link_id)
                                        # Repeat for left links list
                                        for link_id in component.left_links:
                                            while component.left_links.count(link_id) != 1:
                                                component.left_links.remove(link_id)

                                        # Sort the link list containing component ids in ascending order
                                        component.right_links = sorted(component.right_links)
                                        component.left_links = sorted(component.left_links)

                                        # Change component's image back to normal
                                        if component.image == independent_voltage_source_right_side \
                                                or component.image == independent_voltage_source_left_side:
                                            component.image = independent_voltage_source
                                        elif component.image == independent_current_source_right_side \
                                                or component.image == independent_current_source_left_side:
                                            component.image = independent_current_source
                                        elif component.image == resistor_right_side \
                                                or component.image == resistor_left_side:
                                            component.image = resistor

        #  Mouse button is no longer pressed
        if event.type == pygame.MOUSEBUTTONUP:
            for component in component_list:
                # Every component is no longer clicked
                component.clicked = False

    # Drawing code
    # Draw all parts of GUI
    toolbar()
    main_tab()
    component_tab()
    # Draw components
    component_list.draw(screen)

    # Program logic
    for component in component_list:
        # Line position variables which will connect two components  together
        start_pos = (0, 0)
        end_pos = (0, 0)

        # Create circuit network
        # Check if link lists are not empty
        if len(component.right_links) != 0 or len(component.left_links) != 0:
            # Another loop going through all components
            for component2 in component_list:
                # Check if component id is in other components links lists
                # Right - Right link
                if component2.id in component.right_links and component.id in component2.right_links:
                    # Define line's start and end positions
                    start_pos = (
                        component.rect.x + component.rect.width, component.rect.y + (component.rect.height // 2))
                    end_pos = (component2.rect.x + component2.rect.width, component2.rect.y
                               + (component2.rect.height // 2))
                # Repeat for all possible link sides combinations
                # Left - Left link
                elif component2.id in component.left_links and component.id in component2.left_links:
                    start_pos = (component.rect.x, component.rect.y + (component.rect.height // 2))
                    end_pos = (component2.rect.x, component2.rect.y + (component2.rect.height // 2))
                # Right - Left link
                elif component2.id in component.right_links and component.id in component2.left_links:
                    start_pos = (
                        component.rect.x + component.rect.width, component.rect.y + (component.rect.height // 2))
                    end_pos = (component2.rect.x, component2.rect.y + (component2.rect.height // 2))
                # Left - Right link
                elif component2.id in component.left_links and component.id in component2.right_links:
                    start_pos = (component.rect.x, component.rect.y + (component.rect.height // 2))
                    end_pos = (component2.rect.x + component2.rect.width, component2.rect.y
                               + (component2.rect.height // 2))

                # Dray a line connecting two components
                pygame.draw.line(screen, BLACK, start_pos, end_pos, 7)

        # Drag and drop system
        # Check if component is clicked
        if component.clicked:
            # Get mouse position
            pos = pygame.mouse.get_pos()
            # While users moves a mouse inside the main tab
            if (185 + (component.rect.width // 2)) < pos[0] < (WIDTH + (component.rect.width // 2)) \
                    and (60 + (component.rect.height // 2)) < pos[1] < (HEIGHT + (component.rect.height // 2)):
                # Change component position based on mouse's position
                # Mouse is always positioned in the center of component
                component.rect.x = pos[0] - (component.rect.width // 2)
                component.rect.y = pos[1] - (component.rect.height // 2)

        # Selected components
        if component.selected:
            # Display component's name, value, unit, unit prefix and short description
            component.display_characteristics()

            # Change component's image that tells the user which component is selected
            if component.image == independent_voltage_source:
                component.image = independent_voltage_source_selected
            elif component.image == independent_current_source:
                component.image = independent_current_source_selected
            elif component.image == resistor:
                component.image = resistor_selected
        # If component is not selected
        else:
            # Display normal component image
            if component.image == independent_voltage_source_selected:
                component.image = independent_voltage_source
            elif component.image == independent_current_source_selected:
                component.image = independent_current_source
            elif component.image == resistor_selected:
                component.image = resistor

    # Update the screen
    pygame.display.update()
    # Repeat update 60 times each second
    clock.tick(fps)

# Close pygame
pygame.quit()
