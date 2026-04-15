from datetime import datetime
import threading
from time import sleep
from typing import List, cast

from inputs import get_gamepad
from pynput import keyboard
from pynput import mouse
from pynput.mouse import Button
from pynput.keyboard import Key, KeyCode
import tkinter as tk

# This is the file the data is output to. It never overwrites this file and instead adds a new set of headers every time.
outputFile = "output.txt"

# These are all the action sin the game I wanted to track. There are a few others but this is everything I care about.
gameInputs = ["left", "right", "up", "down", "jump", "dash", "attack", "superdash", "dreamnail", "cast", "focus"]
# The bindings store which key press corresponds to each action. The default is my keybinds, but they can be adjusted for other people.
bindings: List[Key | KeyCode | Button] = [Key.left, Key.right, Key.down, Key.up, Key.space, KeyCode(char='c'), KeyCode(char='x'), KeyCode(char='s'), KeyCode(char='d'), KeyCode(char='f'), KeyCode(char='a')]
# This list will store which buttons on a controller are used for which action if set. Each button is addressed by an int.
controller_bindings = [0]
# This list stores which buttons are currently pressed. It is indexed by action.
key_status = [False, False, False, False, False, False, False, False, False, False, False]
# Is a controller being used? Set by user
controllerMode = False
# Set to true while logging inputs/
logging = False
# Sets the rate of data recording. Is not perfect as it does not change rate depending on the time it takes the code to execute
rate = 10 # Hz

# Returns the name of the key pressed. Needed to account for meta keys like shift or space and mouse clicks.
def get_key_name(key: Key | KeyCode) -> str:
    if type(key) is Button:
        if key == Button.left:
            return "left click"
        else:
            return "right click"
    else:
        try:
            return key.char
        except AttributeError:
            return key.name

# This defines the main GUI of the application.
class InputLoggerApp:
    # This constructor is used to initialize the Tkinter GUI
    def __init__(self, master, init_bindings):
        # The master is the tk root.
        self.master = master
        master.title("Input Logger")

        # Creates a label that shows the logging status of the application
        self.status_label = tk.Label(master, text="Status: Not Logging")
        self.status_label.pack()

        # Creates a label that shows if the application is in keyboard or controller mode.
        self.mode_label = tk.Label(master, text="Keyboard/Mouse mode")
        self.mode_label.pack()

        # Creates a box (like a div) within the application. Used for formating
        self.info_box = tk.Frame(self.master)

        # This label is for an input field indicating where the user's name should be entered.
        lb1 = tk.Label(self.info_box, text="Name")
        lb1.grid(row=0, column=0, padx=5, pady=5)

        # The input field for the name
        self.name_field = tk.Text(self.info_box, height=1, width=30)
        self.name_field.grid(row=0, column=1, padx=5, pady=5)

        # This label is for an input field indicating where the boss the user is fighting should be entered.
        lb2 = tk.Label(self.info_box, text="Boss")
        lb2.grid(row=1, column=0, padx=5, pady=5)

        # The input field for the boss
        self.boss_field = tk.Text(self.info_box, height=1, width=30)
        self.boss_field.grid(row=1, column=1, padx=5, pady=5)

        # Adds the box to the GUI
        self.info_box.pack(pady=10)

        # Adds a button to toggle controller. Mode activates the set function when pressed.
        self.controller_button = tk.Button(master, text="Toggle Controller Mode", command=self.toggle_controller_mode)
        self.controller_button.pack()

        # Adds a button to start loggin. Mode activates the set function when pressed.
        self.start_button = tk.Button(master, text="Start Logging", command=self.start_logging)
        self.start_button.pack()

        # Adds a button to stop logging. Mode activates the set function when pressed.
        self.stop_button = tk.Button(master, text="Stop Logging", command=self.stop_logging)
        self.stop_button.pack()

        self.bindings_container = tk.Frame(master)
        # calls a function to programmatically generate a display to show and allow button binding to be changed.
        self.create_bindings_display(init_bindings)


    # Takes in a list of bindings and creates a display to show them.
    def create_bindings_display(self, bindings: List[Key | KeyCode]):
        global gameInputs
        # Loops for every game action
        for i in range(len(gameInputs)):
            # Gets the name of the action
            button_in_game = gameInputs[i]
            # Gets the key bound to that binding
            button_binding = bindings[i]
            # Gets the human-readable name for that key
            button_binding_name = get_key_name(button_binding)
            # Creates a label with the name of the action in game
            key_label = tk.Label(self.bindings_container, text=button_in_game)
            # Creates a label showing the current button bound to that action
            value_label = tk.Label(self.bindings_container, text=button_binding_name)
            # Creates a button that will set the binding for this action. Lambda functions are used to encode the index
            # of the action the binding must be set for
            set_button = tk.Button(self.bindings_container, text="Set", command=lambda i=i: self.set_binding(i))
            # This code places the buttons in a grid. The first 6 are on the left and the second 6 on the right.
            if i < 6:
                key_label.grid(row=i, column=0, padx=5, pady=5)
                value_label.grid(row=i, column=1, padx=5, pady=5)
                set_button.grid(row=i, column=2, padx=5, pady=5)
            else:
                key_label.grid(row=i-6, column=3, padx=5, pady=5)
                value_label.grid(row=i-6, column=4, padx=5, pady=5)
                set_button.grid(row=i-6, column=5, padx=5, pady=5)
        # Adds the button container to the GUI
        self.bindings_container.pack(pady=10)

    # Updates the bound button or key for a given action. For simplicity if any binding is updated all labels are iterated through
    def update_bindings_display(self, bindings: List[Key | KeyCode]):
        # This loops through all children of the bindings container (the two labels and button for each action)
        for i, child in enumerate(self.bindings_container.winfo_children()):
            # This selects each binding label
            if i % 3 == 1:
                binding_index = i // 3 # this divides by three and floors the result. This gets me the index of the label to change
                new_binding_name = get_key_name(bindings[binding_index]) # updates the GUI display to show the new bound button
                cast(tk.Label, child).config(text=new_binding_name) # Uses cast so the linter doesn't get mad. This sets the text to the new value

    # Function to start logging
    def start_logging(self):
        global logging
        # Pulls in the global variable tracking logging
        # updates the status on the gui
        self.status_label.config(text="Status: Logging")
        # records data for the header in the output file
        name = self.name_field.get("1.0", tk.END)
        boss = self.boss_field.get("1.0", tk.END)
        # Creates a header in the output file
        header(name, boss)
        # Internally records that logging should start
        logging = True
        # Debugging
        print("Logging started.")

    # Function that stops logging
    def stop_logging(self):
        global logging
        # Pulls in the global variable tracking logging
        # updates the status on the gui
        self.status_label.config(text="Status: Not Logging")
        # Internally records that logging should stop
        logging = False
        # Debugging
        print("Logging stopped.")

    def toggle_logging(self):
        # Helper function to toggle logging. Simply calls the applicable function depending on the value of logging
        print("Toggling Logging.")
        global logging
        if logging:
            self.stop_logging()
        else:
            self.start_logging()

    # Toggles the controller mode.
    def toggle_controller_mode(self):
        global controllerMode
        # Pulls in the global variable that tracks if controller mode is enabled
        if controllerMode:
            # Internally tracks that controller mode should not be used
            controllerMode = False
            # Updates GUI accordingly
            self.mode_label.config(text="Keyboard/Mouse mode")
        else:
            # Internally tracks that controller mode should  be used
            controllerMode = True
            # Updates GUI accordingly
            self.mode_label.config(text="Controller mode")

    # Sets a new key bind for a game action
    def set_binding(self, ind: int):
        # listener callback for key press
        def on_press(key):
            global bindings
            # Cancels if the escape key is pressed
            if key == Key.esc:
                return False
            # Otherwise updates the binding to the pressed key
            bindings[ind] = key
            # This code runs outside the main GUI loop in a listener so when the listener is activated
            # we need to move this execution to the main loop to ensure it works properly
            self.master.after(0, lambda: self._on_binding_set(ind, key, listener, listener_mouse))
            return None

        # Listener callback for mouse click
        def on_click(x, y, button: Button, pressed):
            # This has the same general function as the on_press callback
            if pressed:
                global bindings
                bindings[ind] = button
                self.master.after(0, lambda: self._on_binding_set(ind, button, listener, listener_mouse))

        # creates listeners for the keyboard and mouse
        listener = keyboard.Listener(on_press=on_press)
        listener_mouse = mouse.Listener(on_click=on_click)
        # Listeners are not started by default so that is handled here
        listener.start()
        listener_mouse.start()

    # This function will be called after bindings have been set. It will update the GUI and stop the listeners.
    # To stop the listener it needs to take a reference to both as an input.
    def _on_binding_set(self, ind: int, key: Key | KeyCode | Button, listener: keyboard.Listener, listener_mouse: mouse.Listener):
        print(f"Binding for {gameInputs[ind]} set to {get_key_name(key)}")
        self.update_bindings_display(bindings)
        listener.stop()
        listener_mouse.stop()

# This is the start of the non directly GUI connected code
# stores the time each button has been held for. Used to make sure each button press is recorded by a write operation.
# This is needed because writes occur at a different lower frequency then reads and because a press and release event can be picked up in the same window
active_times = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# This function returns the controller state. Specifically used for controller mode. This corresponds to a bool list with a value for each action.
# If the button for an action is pressed it is Ture
def get_controller_state():
    global active_times
    # Pulls in the global variable to track how long buttons have been active for. Needed to store the times between function calls
    #Easier than returning it and passing it in every time.
    # Gets all button press events since the last time this funciton was called
    events = get_gamepad()
    #    0        1      2     3        4       5        6         7             8         9        10
    # ["left", "right", "up", "down", "jump", "dash", "attack", "superdash", "dreamnail", "cast", "focus"]
    state = [False, False, False, False, False, False, False, False, False, False, False]
    # These mappings are hard coded to the defaults for controllers. Basically no one uses anything else. Definitely not my teammate
    # Represents the correlation between button name and the index of the action they map to
    controller_mappings = {"BTN_NORTH": 8, "BTN_SOUTH": 4, "BTN_WEST":6, "BTN_EAST":10, "BTN_TR":9, "ABS_Z":7, "ABS_RZ":5, "ABS_X":1, "ABS_X_LOW": 0, "ABS_Y":2, "ABS_Y_LOW": 3}

    # Takes in an action index and a true or false for corresponding to if the button is pressed.
    # This is just compresses a bunch of if statements. When a button is pressed it is set to active for two iterations of this function
    def set_state(ind, key_state):
        if key_state:
            active_times[ind] = 2

    # Loops through all the events
    for event in events:
        # Events can be of type "Sync" with metadata or of type "Key" which refrenses button presses
        # Sync events are passesd over
        if event.ev_type == "Sync":
            continue
        # a state of 1 indicates a button was pressed. Release events are discarded
        if event.state == 0:
            continue
        # This matches the event code to the buttons we care about. For each button it calls set state with an appropriate condition.
        # The controller_mapping dictionary is used for human readability and maintainability.
        match event.code:
            case "BTN_NORTH":
                set_state(controller_mappings["BTN_NORTH"], event.state == 1)
            case "BTN_EAST":
                set_state(controller_mappings["BTN_EAST"], event.state == 1)
                print(event.state)
            case "BTN_SOUTH":
                set_state(controller_mappings["BTN_SOUTH"], event.state == 1)
            case "BTN_WEST":
                set_state(controller_mappings["BTN_WEST"], event.state == 1)
            case "BTN_TR":
                set_state(controller_mappings["BTN_TR"], event.state == 1)
            case "ABS_Z":
                set_state(controller_mappings["ABS_Z"], event.state >= 125)
            case "ABS_RZ":
                set_state(controller_mappings["ABS_RZ"], event.state >= 125)
            case "ABS_X":
                set_state(controller_mappings["ABS_X"], event.state >= 10000)
                set_state(controller_mappings["ABS_X_LOW"], event.state <= -10000)
            case "ABS_Y":
                set_state(controller_mappings["ABS_Y"], event.state >= 10000)
                set_state(controller_mappings["ABS_Y_LOW"], event.state <= -10000)

    # Decreases the active time for each button. The button will be set to true if it has a value above 0 by the time it gets to this loop.
    # Without this style of tracking if a press and release action were given in the same window of collected events it would never register as pressed outside of this function
    for i in range(11):
        if active_times[i]>0:
            active_times[i] -= 1
            state[i]=True

    # Returns the bool list
    return state

# Lister function that reads controller inputs
def controller_input_listener():
    global controller_bindings
    global controllerMode
    global logging
    global key_status
    # This listener keeps running until forced stopped.
    while True:
        # Only while applicable the state of the controller will be tracked
        while logging & controllerMode:
            # The key status is saved to a global variable so it can be written in a different thread.
            key_status = get_controller_state()
            # sleeps so that the code will run at ~rate Hz
            sleep(1/rate)
        # While the tracking is not active the sleep is longer to not do unnecessary processing.
        sleep(1/3)

# This function creates hotkeys to handle the start/stop logging functionally
# This function takes in the function to run when the hotkey is pressed
# This is adapted from documentation
def start_pynput_listener(func):
    # We first use the built-in hotkey object. It takes in the button to trigger on and the function to call when it is pressed.
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<f4>'),
        func
    )

    # This creates a new listener in the manner outlined in the documentation. Should sit in the background and monitor all inputs
    # triggering on the specific key supplied.
    with keyboard.Listener(
            on_press=lambda k: hotkey.press(listener.canonical(k)),
            on_release=lambda k: hotkey.release(listener.canonical(k))) as listener:
        # Complex thread things are happening here. This function is called in a thread. The listener also creates a thread.
        # Calling listener.join is necessary and stops execution of the outside thread while the listener is active. In this case .join binds
        # the listener to the thread this function is called in. The end result is this runs in the background like I want it to.
        listener.join()

# This function writes data to a new header in the output file
# The inputs are the name of the person playing and the boss they are fighting
def header(name, boss):
    # The header contains the time of the fight, the person fighting, the boss they are fighting as metadata, and the colum headers for the differnt actions.
    # Opens this file
    with open(outputFile, "a") as f:
        # Gets the date and writes it as metadata before the csv headers
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        # Writes the name of the player
        f.write(f"# {name}")
        # Writes the name of the boss
        f.write(f"# {boss}")
        # for each of the game inputs writes the input with a ", " delimiter. on the last item adds a newline.
        for i in range(len(gameInputs)):
            f.write(gameInputs[i])
            if i<10:
                f.write(", ")
            else:
                f.write("\n")

# This function runs in a thread and while the key logging is active it records rows of 1s or 0s to indicate if a given action is triggered
def output_to_file(rate_hz):
    global logging
    global key_status
    # Keeps the thread constantly going
    while True:
        # If the program is actively logging
        if logging:
            # opens the file in append mode so we add to the end of the file
            with open(outputFile, "a") as f:
                # For each action
                for i in range(len(key_status)):
                    # Write a 1 if the corresponding entry for each action in key_status is true.
                    f.write("1 " if key_status[i] else "0 ")
                    if i < 10:
                        f.write(", ") # Uses a ", " delimiter
                # ends with a new line
                f.write("\n")
        # Sleeps so this runs at rate Hz
        sleep(1 / rate_hz)

# Handler for key presses in keyboard mode.
def on_press(key):
    # Runs if logging is active and controller mode is not
    if logging and not controllerMode:
        # Try catch is used in case the key press is not in a binding.
        try:
            # Gets the index for the game action corresponding to the pressed button
            i = bindings.index(key)
            # Sets the entry in key_status corresponding to the given game action to true
            key_status[i] = True
        except ValueError:
            pass

# Handles key releases for keyboard mode.
def on_release(key):
    # Runs if logging is active and controller mode is not
    if logging and not controllerMode:
        # Try catch is used in case the key press is not in a binding.
        try:
            # Gets the index for the game action corresponding to the pressed button
            i = bindings.index(key)
            # Sets the entry in key_status corresponding to the given game action to False
            key_status[i] = False
        except ValueError:
            pass

# Handles mouse clicks in keyboard mode
def on_click(x, y, button, pressed):
    # Runs if logging is active and controller mode is not
    if logging and not controllerMode:
        # Try catch is used in case the key press is not in a binding.
        try:
            # Gets the index for the game action corresponding to the pressed button
            i = bindings.index(button)
            # Sets the entry in key_status corresponding to the given game action to true or false depending on the boolean pressed
            key_status[i] = pressed
        except ValueError:
            pass

# This listener handles key events
# The on press is the above on press event; the on release is the above on release event.
# The effect of this is that while a key is pressed the entry in key_status corresponding to the action triggered by the key pressed is set to True.
# Additionally, that entry is set back to false when the key is released
main_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
    )

# This listener works in much the same way as the keyboard listener just for the mouse.
# The one difference is on_click is triggered for presses and release
mouse_listener = mouse.Listener(
    on_click=on_click
    )

# This listener tracks controller inputs. It is set to daemon=True so it will close when the program ends
controller_listener = threading.Thread(target=controller_input_listener, daemon=True)

# This initializes the logging setup
def main():
    global main_listener
    # Creates the base Tk GUI element
    root = tk.Tk()
    # Initializes the GUI handler class and sets up GUI elements
    app = InputLoggerApp(root, bindings)

    # Creates the hotkey thread for watching hotkeys and the output thread for writing to the output file.
    # Both area daemons so the threads will close when the program ends
    hotkey_thread = threading.Thread(target=start_pynput_listener, args=[app.toggle_logging], daemon=True)
    output_thread = threading.Thread(target=output_to_file, args=[rate], daemon=True)

    # Starts the threads
    hotkey_thread.start()
    output_thread.start()

    main_listener.start()
    mouse_listener.start()

    controller_listener.start()

    # Sets the window size
    root.geometry("325x425")
    # Runs the main loop (handles button presses keyboard input registering etc...)
    # Program will pass this call when the GUI is closed
    root.mainloop()

    # makes sure the keyboard listener is stopped properly
    if not controllerMode:
        main_listener.stop()

# Standard py file starting code
if __name__ == "__main__":
    main()