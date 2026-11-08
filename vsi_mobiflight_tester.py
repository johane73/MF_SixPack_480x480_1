
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


class VsiSerialTester:

    def __init__(self, root):
        self.root = root
        self.root.title("VSI - MobiFlight Serial Tester")
        self.root.resizable(False, False)

        self.ser = None
        self.pending_send = None
        self.last_sent = None

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value="115200")
        self.device_var = tk.StringVar(value="0")
        self.message_var = tk.StringVar(value="0")
        self.value_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Disconnected")
        self.last_command_var = tk.StringVar(
            value="No command sent"
        )

        self._build_ui()
        self.refresh_ports()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

        if serial is None:
            self.root.after(100, self.show_missing_dependency)

    def show_missing_dependency(self):
        messagebox.showerror(
            "Missing dependency",
            "pyserial is not installed.\n\n"
            "Install it with:\n"
            "python3 -m pip install pyserial"
        )

    def _build_ui(self):

        outer = ttk.Frame(self.root, padding=14)
        outer.grid(row=0, column=0, sticky="nsew")

        # Serial connection
        connection = ttk.LabelFrame(
            outer, text="Serial connection", padding=10
        )
        connection.grid(row=0, column=0, sticky="ew")

        ttk.Label(connection, text="Port").grid(
            row=0, column=0, sticky="w"
        )

        self.port_box = ttk.Combobox(
            connection,
            textvariable=self.port_var,
            width=28,
            state="readonly"
        )
        self.port_box.grid(
            row=0, column=1, padx=6, pady=3
        )

        ttk.Button(
            connection,
            text="Refresh",
            command=self.refresh_ports
        ).grid(row=0, column=2)

        ttk.Label(connection, text="Baud").grid(
            row=1, column=0, sticky="w"
        )

        ttk.Entry(
            connection,
            textvariable=self.baud_var,
            width=10
        ).grid(row=1, column=1, sticky="w", padx=6)

        ttk.Label(connection, text="Device index").grid(
            row=2, column=0, sticky="w"
        )

        ttk.Entry(
            connection,
            textvariable=self.device_var,
            width=10
        ).grid(row=2, column=1, sticky="w", padx=6)

        ttk.Label(connection, text="Message ID").grid(
            row=3, column=0, sticky="w"
        )

        ttk.Entry(
            connection,
            textvariable=self.message_var,
            width=10
        ).grid(row=3, column=1, sticky="w", padx=6)

        self.connect_button = ttk.Button(
            connection,
            text="Connect",
            command=self.toggle_connection
        )
        self.connect_button.grid(
            row=0, column=3, rowspan=2,
            padx=(12, 0), sticky="ns"
        )

        ttk.Label(
            connection,
            textvariable=self.status_var
        ).grid(row=2, column=3, rowspan=2, padx=12)

        # Vertical speed controls
        control = ttk.LabelFrame(
            outer, text="Vertical speed", padding=12
        )
        control.grid(
            row=1, column=0, sticky="ew", pady=(12, 0)
        )

        value_row = ttk.Frame(control)
        value_row.grid(row=0, column=0, sticky="ew")

        self.value_label = ttk.Label(
            value_row,
            text="0",
            font=("TkDefaultFont", 28, "bold")
        )
        self.value_label.grid(row=0, column=0)

        ttk.Label(
            value_row,
            text="ft/min",
            font=("TkDefaultFont", 11)
        ).grid(row=0, column=1, padx=8, sticky="s")

        self.scale = ttk.Scale(
            control,
            from_=-1500,
            to=1500,
            orient="horizontal",
            command=self.on_slider
        )
        self.scale.grid(
            row=1, column=0, sticky="ew", pady=12
        )

        ends = ttk.Frame(control)
        ends.grid(row=2, column=0, sticky="ew")

        ttk.Label(ends, text="-1500 DN").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(ends, text="0").grid(row=0, column=1)
        ttk.Label(ends, text="UP +1500").grid(
            row=0, column=2, sticky="e"
        )

        buttons = ttk.Frame(control)
        buttons.grid(
            row=3, column=0, sticky="ew", pady=(12, 0)
        )

        for col in range(5):
            buttons.columnconfigure(col, weight=1)

        for col, value in enumerate(
            (-1500, -1000, 0, 1000, 1500)
        ):
            label = f"{value:+d}" if value else "ZERO"

            ttk.Button(
                buttons,
                text=label,
                command=lambda v=value: self.set_value(v)
            ).grid(row=0, column=col, padx=3, sticky="ew")

        ttk.Label(
            outer,
            textvariable=self.last_command_var,
            wraplength=520
        ).grid(row=2, column=0, sticky="w", pady=10)

        # Activity log
        log_frame = ttk.LabelFrame(
            outer, text="Activity", padding=8
        )
        log_frame.grid(row=3, column=0, sticky="ew")

        self.log = tk.Text(
            log_frame,
            width=68,
            height=6,
            state="disabled"
        )
        self.log.grid(row=0, column=0, sticky="ew")

    def log_line(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def refresh_ports(self):
        if list_ports is None:
            return

        ports = [
            p.device for p in list_ports.comports()
        ]

        self.port_box["values"] = ports

        if self.port_var.get() not in ports:
            preferred = next(
                (
                    p for p in ports
                    if "usbmodem" in p or "usbserial" in p
                ),
                ports[0] if ports else ""
            )
            self.port_var.set(preferred)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):

        if serial is None:
            self.show_missing_dependency()
            return

        port = self.port_var.get().strip()

        if not port:
            messagebox.showwarning(
                "Select a port",
                "Choose the ESP32 serial port."
            )
            return

        try:
            baud = int(self.baud_var.get())
            device = int(self.device_var.get())
            message = int(self.message_var.get())

            if baud <= 0 or device < 0 or message < 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid settings",
                "Check baud rate, device index and message ID."
            )
            return

        try:
            self.ser = serial.Serial()
            self.ser.port = port
            self.ser.baudrate = baud
            self.ser.timeout = 0.1
            self.ser.write_timeout = 1

            # Avoid deliberately asserting control lines.
            self.ser.dtr = False
            self.ser.rts = False

            self.ser.open()

            time.sleep(0.15)
            self.ser.reset_input_buffer()

            self.status_var.set(f"Connected: {port}")
            self.connect_button.configure(text="Disconnect")

            self.log_line(
                f"Connected to {port} at {baud} baud."
            )

            self.last_sent = None

        except Exception as exc:
            self.ser = None
            messagebox.showerror(
                "Serial connection failed", str(exc)
            )
            self.status_var.set("Disconnected")

    def disconnect(self):
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass

        self.ser = None
        self.status_var.set("Disconnected")
        self.connect_button.configure(text="Connect")
        self.log_line("Disconnected.")

    def on_slider(self, raw_value):

        value = int(round(float(raw_value)))

        self.value_var.set(value)

        self.value_label.configure(
            text=f"{value:+d}" if value else "0"
        )

        # Coalesce rapid slider events.
        if self.pending_send is not None:
            self.root.after_cancel(self.pending_send)

        self.pending_send = self.root.after(
            60, self.send_current_value
        )

    def set_value(self, value):

        self.scale.set(value)
        self.value_var.set(value)

        self.value_label.configure(
            text=f"{value:+d}" if value else "0"
        )

        if self.pending_send is not None:
            self.root.after_cancel(self.pending_send)
            self.pending_send = None

        self.send_value(value)

    def send_current_value(self):
        self.pending_send = None
        self.send_value(self.value_var.get())

    def send_value(self, value):

        if not self.ser or not self.ser.is_open:
            self.last_command_var.set(
                "Not connected - value selected but not transmitted."
            )
            return

        try:
            device = int(self.device_var.get())
            message = int(self.message_var.get())

            # MobiFlight SetCustomDevice command format.
            # command = (
            #     f"SetCustomDevice <32,{device},{message},"
            #     f"{value:+d};>\n"
            # )
            command = f"32,{device},{message},{value};"

            self.ser.write(command.encode("ascii"))
            self.ser.flush()

            self.last_command_var.set(
                f"Sent: {command.strip()}"
            )

            if value != self.last_sent:
                self.log_line(command.strip())
                self.last_sent = value

        except Exception as exc:
            self.log_line(f"Serial write error: {exc}")
            self.status_var.set("Serial error")

    def close(self):

        if self.pending_send is not None:
            self.root.after_cancel(self.pending_send)

        self.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    VsiSerialTester(root)
    root.mainloop()


if __name__ == "__main__":
    main()

