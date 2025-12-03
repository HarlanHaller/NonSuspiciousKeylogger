from datetime import datetime
import threading
import time
from time import sleep
from typing import List, cast

from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import tkinter as tk

outputFile = "output.txt"

gameInputs = ["left", "right", "up", "down", "jump", "dash", "attack", "superdash", "dreamnail", "cast", "focus"]
bindings: List[Key | KeyCode] = [Key.left, Key.right, Key.down, Key.up, Key.space, KeyCode(char='c'), KeyCode(char='x'), KeyCode(char='s'), KeyCode(char='d'), KeyCode(char='f'), KeyCode(char='a')]
key_status = [False, False, False, False, False, False, False, False, False, False, False]

logging = False
rate = 5 # Hz

def get_key_name(key: Key | KeyCode) -> str:
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

    def set_binding(self, ind: int):
        #user pynput to get a new key binding
        def on_press(key):
            global bindings
            if key == Key.esc:
                return False
            bindings[ind] = key
            self.master.after(0, lambda: self._on_binding_set(ind, key, listener))
            return None

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def _on_binding_set(self, ind: int, key: Key | KeyCode, listener: keyboard.Listener):
        print(f"Binding for {gameInputs[ind]} set to {get_key_name(key)}")
        self.update_bindings_display(bindings)
        listener.stop()



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


def main():
    root = tk.Tk()
    app = InputLoggerApp(root, bindings)

    hotkey_thread = threading.Thread(target=start_pynput_listener, args=[app.toggle_logging], daemon=True)
    output_thread = threading.Thread(target=output_to_file, args=[rate], daemon=True)

    hotkey_thread.start()
    output_thread.start()

    def on_press(key):
        # print(key.name)
        if logging:
            try:
                i = bindings.index(key)
                key_status[i] = True
            except ValueError:
                pass

    def on_release(key):
        if logging:
            try:
                i = bindings.index(key)
                key_status[i] = False
            except ValueError:
                pass

    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)
    listener.start()


    root.geometry("325x425")
    root.mainloop()

    listener.stop()

if __name__ == "__main__":
    main()