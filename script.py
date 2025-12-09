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

outputFile = "output.txt"

gameInputs = ["left", "right", "up", "down", "jump", "dash", "attack", "superdash", "dreamnail", "cast", "focus"]
bindings: List[Key | KeyCode | Button] = [Key.left, Key.right, Key.down, Key.up, Key.space, KeyCode(char='c'), KeyCode(char='x'), KeyCode(char='s'), KeyCode(char='d'), KeyCode(char='f'), KeyCode(char='a')]
controller_bindings = [0]
key_status = [False, False, False, False, False, False, False, False, False, False, False]
controllerMode = False
logging = False
rate = 10 # Hz

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

class InputLoggerApp:
    def __init__(self, master, init_bindings):
        self.master = master
        master.title("Input Logger")

        self.status_label = tk.Label(master, text="Status: Not Logging")
        self.status_label.pack()

        self.mode_label = tk.Label(master, text="Keyboard/Mouse mode")
        self.mode_label.pack()

        self.info_box = tk.Frame(self.master)

        lb1 = tk.Label(self.info_box, text="Name")
        lb1.grid(row=0, column=0, padx=5, pady=5)

        self.name_field = tk.Text(self.info_box, height=1, width=30)
        self.name_field.grid(row=0, column=1, padx=5, pady=5)

        lb2 = tk.Label(self.info_box, text="Boss")
        lb2.grid(row=1, column=0, padx=5, pady=5)

        self.boss_field = tk.Text(self.info_box, height=1, width=30)
        self.boss_field.grid(row=1, column=1, padx=5, pady=5)

        self.info_box.pack(pady=10)

        self.controller_button = tk.Button(master, text="Toggle Controller Mode", command=self.toggle_controller_mode)
        self.controller_button.pack()

        self.start_button = tk.Button(master, text="Start Logging", command=self.start_logging)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop Logging", command=self.stop_logging)
        self.stop_button.pack()

        self.bindings_container = tk.Frame(master)
        self.create_bindings_display(init_bindings)


    def create_bindings_display(self, bindings: List[Key | KeyCode]):
        global gameInputs
        for i in range(len(gameInputs)):
            button_in_game = gameInputs[i]
            button_binding = bindings[i]
            button_binding_name = get_key_name(button_binding)
            key_label = tk.Label(self.bindings_container, text=button_in_game)
            value_label = tk.Label(self.bindings_container, text=button_binding_name)
            set_button = tk.Button(self.bindings_container, text="Set", command=lambda i=i: self.set_binding(i))
            if i < 6:
                key_label.grid(row=i, column=0, padx=5, pady=5)
                value_label.grid(row=i, column=1, padx=5, pady=5)
                set_button.grid(row=i, column=2, padx=5, pady=5)
            else:
                key_label.grid(row=i-6, column=3, padx=5, pady=5)
                value_label.grid(row=i-6, column=4, padx=5, pady=5)
                set_button.grid(row=i-6, column=5, padx=5, pady=5)
        self.bindings_container.pack(pady=10)

    def update_bindings_display(self, bindings: List[Key | KeyCode]):
        for i, child in enumerate(self.bindings_container.winfo_children()):
            if i % 3 == 1:
                binding_index = i // 3
                new_binding_name = get_key_name(bindings[binding_index])
                cast(tk.Label, child).config(text=new_binding_name)


    def start_logging(self):
        global logging
        self.status_label.config(text="Status: Logging")
        name = self.name_field.get("1.0", tk.END)
        boss = self.boss_field.get("1.0", tk.END)
        header(name, boss)
        logging = True
        print("Logging started.")

    def stop_logging(self):
        global logging
        self.status_label.config(text="Status: Not Logging")
        logging = False
        print("Logging stopped.")

    def toggle_logging(self):
        print("Toggling Logging.")
        global logging
        if logging:
            self.stop_logging()
        else:
            self.start_logging()

    def toggle_controller_mode(self):
        global controllerMode
        if controllerMode:
            controllerMode = False
            self.mode_label.config(text="Keyboard/Mouse mode")
        else:
            controllerMode = True
            self.mode_label.config(text="Controller mode")

    def set_binding(self, ind: int):
        #user pynput to get a new key binding
        def on_press(key):
            global bindings
            if key == Key.esc:
                return False
            bindings[ind] = key
            self.master.after(0, lambda: self._on_binding_set(ind, key, listener, listener_mouse))
            return None

        def on_click(x, y, button: Button, pressed):
            if pressed:
                global bindings
                bindings[ind] = button
                self.master.after(0, lambda: self._on_binding_set(ind, button, listener, listener_mouse))

        listener = keyboard.Listener(on_press=on_press)
        listener_mouse = mouse.Listener(on_click=on_click)
        listener.start()
        listener_mouse.start()

    def _on_binding_set(self, ind: int, key: Key | KeyCode | Button, listener: keyboard.Listener, listener_mouse: mouse.Listener):
        print(f"Binding for {gameInputs[ind]} set to {get_key_name(key)}")
        self.update_bindings_display(bindings)
        listener.stop()
        listener_mouse.stop()


active_times = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def get_controller_state():
    global active_times
    events = get_gamepad()
    #    0        1      2     3        4       5        6         7             8         9        10
    # ["left", "right", "up", "down", "jump", "dash", "attack", "superdash", "dreamnail", "cast", "focus"]
    state = [False, False, False, False, False, False, False, False, False, False, False]
    controller_mappings = {"BTN_NORTH": 8, "BTN_SOUTH": 4, "BTN_WEST":6, "BTN_EAST":10, "BTN_TR":9, "ABS_Z":7, "ABS_RZ":5, "ABS_X":1, "ABS_X_LOW": 0, "ABS_Y":2, "ABS_Y_LOW": 3}

    def set_state(ind, key_state):
        if key_state:
            active_times[ind] = 2

    for event in events:
        if event.ev_type == "Sync":
            continue
        if event.state == 0:
            continue
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

    for i in range(11):
        if active_times[i]>0:
            active_times[i] -= 1
            state[i]=True

    return state

def controller_input_listener():
    global controller_bindings
    global controllerMode
    global logging
    global key_status
    while True:
        while logging & controllerMode:
            key_status = get_controller_state()
            sleep(1/rate)
        sleep(1/3)

def start_pynput_listener(func):
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<f4>'),
        func
    )

    with keyboard.Listener(
            on_press=lambda k: hotkey.press(listener.canonical(k)),
            on_release=lambda k: hotkey.release(listener.canonical(k))) as listener:
        listener.join()


def header(name, boss):
    with open(outputFile, "a") as f:
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# {name}")
        f.write(f"# {boss}")
        for i in range(len(gameInputs)):
            f.write(gameInputs[i])
            if i<10:
                f.write(", ")
            else:
                f.write("\n")


def output_to_file(rate_hz):
    global logging
    global key_status
    while True:
        if logging:
            with open(outputFile, "a") as f:
                for i in range(len(key_status)):
                    f.write("1 " if key_status[i] else "0 ")
                    if i < 10:
                        f.write(", ")
                f.write("\n")
        sleep(1 / rate_hz)

def on_press(key):

    if logging and not controllerMode:
        try:
            i = bindings.index(key)
            key_status[i] = True
        except ValueError:
            pass

def on_release(key):
    if logging and not controllerMode:
        try:
            i = bindings.index(key)
            key_status[i] = False
        except ValueError:
            pass

def on_click(x, y, button, pressed):
    if logging and not controllerMode:
        try:
            i = bindings.index(button)
            key_status[i] = pressed
        except ValueError:
            pass

main_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
    )

mouse_listener = mouse.Listener(
    on_click=on_click
    )

controller_listener = threading.Thread(target=controller_input_listener, daemon=True)

def main():
    global main_listener
    root = tk.Tk()
    app = InputLoggerApp(root, bindings)

    hotkey_thread = threading.Thread(target=start_pynput_listener, args=[app.toggle_logging], daemon=True)
    output_thread = threading.Thread(target=output_to_file, args=[rate], daemon=True)

    hotkey_thread.start()
    output_thread.start()

    main_listener.start()
    mouse_listener.start()

    controller_listener.start()

    root.geometry("325x425")
    root.mainloop()

    if not controllerMode:
        main_listener.stop()

if __name__ == "__main__":
    main()