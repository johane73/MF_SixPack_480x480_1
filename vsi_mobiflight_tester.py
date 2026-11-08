#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None


MIN_SPEED = -3800
MAX_SPEED = 3800

RAMP_RATE = 100          # FPM per second
RAMP_INTERVAL = 100      # milliseconds
SLIDER_DEBOUNCE = 60     # milliseconds


class VSIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VSI - MobiFlight Serial Tester")
        self.root.resizable(True, False)

        self.ser = None
        self.last_sent = None
        self.current_value = 0

        self.pending_send = None
        self.ramp_job = None
        self.ramp_active = False
        self.ramp_target = 0
        self.ramp_position = 0.0
        self.ramp_last_time = 0.0

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value="115200")
        self.device_var = tk.StringVar(value="0")
        self.message_var = tk.StringVar(value="0")

        self.value_var = tk.IntVar(value=0)
        self.value_label_var = tk.StringVar(value="0 FPM")

        self.status_var = tk.StringVar(value="Disconnected")
        self.last_command_var = tk.StringVar(
            value="Select a serial port and connect."
        )
        self.ramp_status_var = tk.StringVar(value="Ramp stopped")

        self.build_ui()
        self.refresh_ports()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------------------------------------------------
    # User interface
    # ---------------------------------------------------------

    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")

        # Serial connection
        connection = ttk.LabelFrame(
            main, text="Serial connection", padding=8
        )
        connection.grid(row=0, column=0, sticky="ew")

        ttk.Label(connection, text="Port:").grid(
            row=0, column=0, padx=4, pady=4
        )

        self.port_combo = ttk.Combobox(
            connection,
            textvariable=self.port_var,
            width=24,
            state="readonly"
        )
        self.port_combo.grid(row=0, column=1, padx=4, pady=4)

        ttk.Button(
            connection,
            text="Refresh",
            command=self.refresh_ports
        ).grid(row=0, column=2, padx=4, pady=4)

        ttk.Label(connection, text="Baud:").grid(
            row=0, column=3, padx=4, pady=4
        )

        ttk.Entry(
            connection,
            textvariable=self.baud_var,
            width=9
        ).grid(row=0, column=4, padx=4, pady=4)

        self.connect_button = ttk.Button(
            connection,
            text="Connect",
            command=self.connect
        )
        self.connect_button.grid(row=0, column=5, padx=4, pady=4)

        self.status_label = ttk.Label(
            connection,
            textvariable=self.status_var
        )
        self.status_label.grid(
            row=1, column=0, columnspan=6,
            sticky="w", padx=4, pady=(5, 0)
        )

        # MobiFlight addressing
        addressing = ttk.LabelFrame(
            main, text="MobiFlight addressing", padding=8
        )
        addressing.grid(
            row=1, column=0, sticky="ew", pady=(8, 0)
        )

        ttk.Label(addressing, text="Device index:").grid(
            row=0, column=0, padx=4, pady=4
        )

        ttk.Entry(
            addressing,
            textvariable=self.device_var,
            width=8
        ).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(addressing, text="Message ID:").grid(
            row=0, column=2, padx=4, pady=4
        )

        ttk.Entry(
            addressing,
            textvariable=self.message_var,
            width=8
        ).grid(row=0, column=3, padx=4, pady=4)

        # Current value
        value_frame = ttk.LabelFrame(
            main, text="Vertical speed", padding=10
        )
        value_frame.grid(
            row=2, column=0, sticky="ew", pady=(8, 0)
        )

        ttk.Label(
            value_frame,
            textvariable=self.value_label_var,
            font=("Helvetica", 22, "bold")
        ).grid(row=0, column=0, pady=(0, 5))

        self.slider = tk.Scale(
            value_frame,
            from_=MAX_SPEED,
            to=MIN_SPEED,
            orient=tk.HORIZONTAL,
            resolution=1,
            showvalue=False,
            variable=self.value_var,
            command=self.on_slider_change,
            length=650
        )
        self.slider.grid(
            row=1, column=0, sticky="ew", padx=5
        )

        value_frame.columnconfigure(0, weight=1)

        # Instant preset buttons
        instant_frame = ttk.LabelFrame(
            main, text="Send immediately", padding=8
        )
        instant_frame.grid(
            row=3, column=0, sticky="ew", pady=(8, 0)
        )

        instant_values = self.get_preset_values()

        for column, value in enumerate(instant_values):
            ttk.Button(
                instant_frame,
                text=f"{value:+d}",
                width=7,
                command=lambda v=value: self.set_value(v)
            ).grid(
                row=0, column=column,
                padx=2, pady=3, sticky="ew"
            )

        for column in range(len(instant_values)):
            instant_frame.columnconfigure(column, weight=1)

        # Gradual movement buttons
        ramp_frame = ttk.LabelFrame(
            main,
            text=f"Gradual movement ({RAMP_RATE} FPM/second)",
            padding=8
        )
        ramp_frame.grid(
            row=4, column=0, sticky="ew", pady=(8, 0)
        )

        for column, value in enumerate(instant_values):
            ttk.Button(
                ramp_frame,
                text=f"{value:+d}",
                width=7,
                command=lambda v=value: self.start_ramp(v)
            ).grid(
                row=0, column=column,
                padx=2, pady=3, sticky="ew"
            )

        for column in range(len(instant_values)):
            ramp_frame.columnconfigure(column, weight=1)

        ramp_controls = ttk.Frame(ramp_frame)
        ramp_controls.grid(
            row=1, column=0, columnspan=len(instant_values),
            sticky="ew", pady=(8, 0)
        )

        ttk.Button(
            ramp_controls,
            text="Ramp to slider value",
            command=self.start_ramp_to_slider
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            ramp_controls,
            text="STOP",
            command=self.stop_ramp
        ).pack(side=tk.LEFT, padx=4)

        ttk.Label(
            ramp_controls,
            textvariable=self.ramp_status_var
        ).pack(side=tk.LEFT, padx=12)

        # Transmission information
        transmission = ttk.LabelFrame(
            main, text="Transmission", padding=8
        )
        transmission.grid(
            row=5, column=0, sticky="ew", pady=(8, 0)
        )

        ttk.Label(
            transmission,
            textvariable=self.last_command_var
        ).grid(row=0, column=0, sticky="w")

        self.log = tk.Text(
            transmission,
            height=7,
            width=85,
            state="disabled",
            font=("Menlo", 10)
        )
        self.log.grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )

        transmission.columnconfigure(0, weight=1)

    # ---------------------------------------------------------
    # Presets
    # ---------------------------------------------------------

    @staticmethod
    def get_preset_values():
        # Include both endpoints as well as 500-FPM increments.
        values = list(range(-3500, 3501, 500))
        values.extend([MIN_SPEED, MAX_SPEED])
        return sorted(set(values))

    # ---------------------------------------------------------
    # Serial ports
    # ---------------------------------------------------------

    def refresh_ports(self):
        if list_ports is None:
            self.port_combo["values"] = []
            self.status_var.set(
                "pyserial is not installed in this Python environment."
            )
            return

        ports = list(list_ports.comports())
        port_names = [port.device for port in ports]

        self.port_combo["values"] = port_names

        if self.port_var.get() not in port_names:
            preferred = next(
                (
                    port for port in port_names
                    if "usbmodem" in port.lower()
                ),
                None
            )

            if preferred:
                self.port_var.set(preferred)
            elif port_names:
                self.port_var.set(port_names[0])
            else:
                self.port_var.set("")

    def connect(self):
        if serial is None:
            messagebox.showerror(
                "Missing dependency",
                "pyserial is not installed.\n\n"
                "Install it using:\n"
                ".venv-vsi/bin/python -m pip install pyserial"
            )
            return

        if self.ser and self.ser.is_open:
            self.disconnect()
            return

        port = self.port_var.get().strip()

        if not port:
            messagebox.showwarning(
                "No serial port",
                "Please select a serial port."
            )
            return

        try:
            baud = int(self.baud_var.get())

            self.ser = serial.Serial(
                port=port,
                baudrate=baud,
                timeout=0.1,
                write_timeout=1
            )

            # Avoid resetting the ESP32 when opening the port.
            self.ser.dtr = False
            self.ser.rts = False

            self.status_var.set(f"Connected: {port}")
            self.connect_button.configure(text="Disconnect")
            self.log_line(f"Connected to {port} at {baud} baud")

            self.last_sent = None

        except Exception as exc:
            self.ser = None
            self.status_var.set("Connection failed")
            messagebox.showerror(
                "Serial connection error",
                str(exc)
            )

    def disconnect(self):
        self.stop_ramp()

        if self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception:
                pass

        self.ser = None
        self.connect_button.configure(text="Connect")
        self.status_var.set("Disconnected")
        self.log_line("Disconnected")

    # ---------------------------------------------------------
    # Value selection
    # ---------------------------------------------------------

    def on_slider_change(self, value):
        self.stop_ramp()

        selected = int(float(value))
        self.current_value = selected
        self.value_label_var.set(f"{selected:+d} FPM")

        if self.pending_send is not None:
            self.root.after_cancel(self.pending_send)

        self.pending_send = self.root.after(
            SLIDER_DEBOUNCE,
            self.send_slider_value
        )

    def send_slider_value(self):
        self.pending_send = None
        self.send_value(self.current_value)

    def set_value(self, value):
        self.stop_ramp()

        value = max(MIN_SPEED, min(MAX_SPEED, int(value)))

        self.current_value = value
        self.value_var.set(value)
        self.value_label_var.set(f"{value:+d} FPM")

        if self.pending_send is not None:
            self.root.after_cancel(self.pending_send)
            self.pending_send = None

        self.send_value(value)

    # ---------------------------------------------------------
    # Gradual movement
    # ---------------------------------------------------------

    def start_ramp_to_slider(self):
        self.start_ramp(int(self.value_var.get()))

    def start_ramp(self, target):
        target = max(MIN_SPEED, min(MAX_SPEED, int(target)))

        self.stop_ramp()

        if self.pending_send is not None:
            self.root.after_cancel(self.pending_send)
            self.pending_send = None

        self.ramp_target = target
        self.ramp_position = float(self.current_value)
        self.ramp_last_time = time.monotonic()
        self.ramp_active = True

        self.ramp_status_var.set(
            f"Moving to {target:+d} FPM..."
        )

        if int(round(self.ramp_position)) == target:
            self.set_value(target)
            self.ramp_status_var.set("Already at target")
            return

        self.ramp_job = self.root.after(
            RAMP_INTERVAL,
            self.ramp_tick
        )

    def ramp_tick(self):
        self.ramp_job = None

        if not self.ramp_active:
            return

        now = time.monotonic()
        elapsed = now - self.ramp_last_time
        self.ramp_last_time = now

        distance = self.ramp_target - self.ramp_position
        max_step = RAMP_RATE * elapsed

        if abs(distance) <= max_step:
            self.ramp_position = float(self.ramp_target)
        elif distance > 0:
            self.ramp_position += max_step
        else:
            self.ramp_position -= max_step

        value = int(round(self.ramp_position))

        self.current_value = value
        self.value_var.set(value)
        self.value_label_var.set(f"{value:+d} FPM")

        self.send_value(value)

        if value == self.ramp_target:
            self.ramp_active = False
            self.ramp_status_var.set(
                f"Reached {self.ramp_target:+d} FPM"
            )
            return

        self.ramp_job = self.root.after(
            RAMP_INTERVAL,
            self.ramp_tick
        )

    def stop_ramp(self):
        if self.ramp_job is not None:
            try:
                self.root.after_cancel(self.ramp_job)
            except tk.TclError:
                pass

            self.ramp_job = None

        was_active = self.ramp_active
        self.ramp_active = False

        if was_active:
            self.ramp_status_var.set(
                f"Stopped at {self.current_value:+d} FPM"
            )

    # ---------------------------------------------------------
    # CmdMessenger transmission
    # ---------------------------------------------------------

    def send_value(self, value):
        if not self.ser or not self.ser.is_open:
            self.last_command_var.set(
                "Not connected - value selected but not transmitted."
            )
            return False

        try:
            device = int(self.device_var.get())
            message = int(self.message_var.get())

            # MobiFlight SetCustomDevice command:
            # 32, device index, message ID, value;
            command = f"32,{device},{message},{value};"

            self.ser.write(command.encode("ascii"))
            self.ser.flush()

            self.last_command_var.set(
                f"Sent: {command.strip()}"
            )

            if value != self.last_sent:
                self.log_line(command.strip())
                self.last_sent = value

            return True

        except Exception as exc:
            self.log_line(f"Serial write error: {exc}")
            self.status_var.set("Serial error")
            return False

    # ---------------------------------------------------------
    # Log
    # ---------------------------------------------------------

    def log_line(self, text):
        timestamp = time.strftime("%H:%M:%S")

        self.log.configure(state="normal")
        self.log.insert(
            tk.END,
            f"[{timestamp}] {text}\n"
        )
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------

    def close(self):
        if self.pending_send is not None:
            try:
                self.root.after_cancel(self.pending_send)
            except tk.TclError:
                pass

            self.pending_send = None

        self.stop_ramp()
        self.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    VSIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
