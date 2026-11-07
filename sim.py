import tkinter as tk
from tkinter import ttk
import time
from threading import Thread

class MobiFlightSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("MobiFlight Python Simulator & Connector")
        self.root.geometry("850x550")
        self.root.resizable(False, False)
        
        # Simulation State
        self.is_running = False
        self.sim_variables = {
            "PARKING_BRAKE_INDICATOR": 0,
            "GEAR_HANDLE_POSITION": 1, # 1 = Down, 0 = Up
            "AUTOPILOT_HEADING_LOCK_DIR": 360
        }
        
        self.create_styles()
        self.build_ui()
        self.log_message("MobiFlight Simulator initialized. Click 'START' to connect to Sim.")

    def create_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#2b2b2b")
        self.style.configure("TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#00ff00")
        self.style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#007acc")
        self.style.configure("Stop.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#cc0000")

    def build_ui(self):
        # Main container split into Left (Hardware) and Right (MobiFlight UI)
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ------------------ LEFT: HARDWARE PANEL SIMULATION ------------------
        hw_frame = ttk.LabelFrame(main_frame, text=" Cockpit Hardware (Simulated Arduino/HID) ", padding=15)
        hw_frame.place(x=20, y=20, width=380, height=500)
        
        # 1. Parking Brake Switch (Input)
        ttk.Label(hw_frame, text="Parking Brake Switch (Pin 4):").grid(row=0, column=0, sticky="w", pady=10)
        self.brake_var = tk.IntVar(value=0)
        self.brake_chk = tk.Checkbutton(
            hw_frame, text="ENGAGED", variable=self.brake_var, onvalue=1, offvalue=0,
            command=self.on_parking_brake_toggle, bg="#2b2b2b", fg="#ffffff", selectcolor="#444444", activebackground="#2b2b2b", activeforeground="#ffffff"
        )
        self.brake_chk.grid(row=0, column=1, sticky="w", padx=10)

        # 2. Landing Gear Switch (Input)
        ttk.Label(hw_frame, text="Landing Gear Switch (Pin 5):").grid(row=1, column=0, sticky="w", pady=10)
        self.gear_var = tk.StringVar(value="DOWN")
        self.gear_btn = ttk.Button(hw_frame, textvariable=self.gear_var, command=self.on_gear_toggle)
        self.gear_btn.grid(row=1, column=1, sticky="w", padx=10)

        # 3. Heading Rotary Encoder (Input)
        ttk.Label(hw_frame, text="HDG Encoder (Pins 6/7):").grid(row=2, column=0, sticky="w", pady=15)
        enc_frame = ttk.Frame(hw_frame)
        enc_frame.grid(row=2, column=1, sticky="w", padx=10)
        ttk.Button(enc_frame, text="◀ Dec", width=6, command=lambda: self.on_encoder_turn(-1)).pack(side=tk.LEFT)
        ttk.Button(enc_frame, text="Inc ▶", width=6, command=lambda: self.on_encoder_turn(1)).pack(side=tk.LEFT, padx=5)

        # 4. Parking Brake LED (Output)
        ttk.Label(hw_frame, text="Brake Indicator LED (Pin 13):").grid(row=3, column=0, sticky="w", pady=20)
        self.led_canvas = tk.Canvas(hw_frame, width=30, height=30, bg="#2b2b2b", bd=0, highlightthickness=0)
        self.led_canvas.grid(row=3, column=1, sticky="w", padx=10)
        self.led_light = self.led_canvas.create_oval(5, 5, 25, 25, fill="#440000")

        # 5. Heading 7-Segment Display (Output)
        ttk.Label(hw_frame, text="HDG 7-Segment Display:").grid(row=4, column=0, sticky="w", pady=15)
        self.hdg_display_val = tk.StringVar(value="360")
        self.hdg_display = tk.Label(hw_frame, textvariable=self.hdg_display_val, font=("Consolas", 24, "bold"), fg="#ff3333", bg="#111111", width=5, relief="sunken")
        self.hdg_display.grid(row=4, column=1, sticky="w", padx=10)

        # ------------------ RIGHT: MOBIFLIGHT CONNECTOR UI ------------------
        mf_frame = ttk.LabelFrame(main_frame, text=" MobiFlight Connector Settings ", padding=15)
        mf_frame.place(x=420, y=20, width=410, height=500)

        # Controls Toolbar
        btn_frame = ttk.Frame(mf_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.run_btn = tk.Button(btn_frame, text="▶ START", bg="#007acc", fg="white", font=("Segoe UI", 10, "bold"), command=self.start_mobiflight, width=10, bd=0)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="■ STOP", bg="#cc0000", fg="white", font=("Segoe UI", 10, "bold"), command=self.stop_mobiflight, width=10, bd=0, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Config Grid Table Header
        cfg_label = ttk.Label(mf_frame, text="Active Mappings (Inputs & Outputs)", style="Header.TLabel")
        cfg_label.pack(anchor="w", pady=(15, 5))

        # Config Treeview / Table
        columns = ("type", "device", "sim_variable")
        self.tree = ttk.Treeview(mf_frame, columns=columns, show="headings", height=5)
        self.tree.heading("type", text="Direction")
        self.tree.heading("device", text="Hardware Module")
        self.tree.heading("sim_variable", text="Sim Variable / Event ID")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("device", width=120)
        self.tree.column("sim_variable", width=180)
        self.tree.pack(fill=tk.X, pady=5)

        # Populate Mock Mapping Configurations
        self.tree.insert("", tk.END, values=("Input ◀", "Pin 4 Switch", "PARKING_BRAKE_SET"))
        self.tree.insert("", tk.END, values=("Input ◀", "Pin 5 Switch", "GEAR_TOGGLE"))
        self.tree.insert("", tk.END, values=("Input ◀", "Pins 6/7 Encoder", "HEADING_BUG_INC/DEC"))
        self.tree.insert("", tk.END, values=("Output ▶", "Pin 13 LED", "PARKING_BRAKE_INDICATOR"))
        self.tree.insert("", tk.END, values=("Output ▶", "MAX7219 Display", "AUTOPILOT_HEADING_LOCK_DIR"))

        # Log Window
        ttk.Label(mf_frame, text="MobiFlight Log Execution Output:").pack(anchor="w", pady=(15, 2))
        self.log_txt = tk.Text(mf_frame, height=10, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9), wrap=tk.WORD)
        self.log_txt.pack(fill=tk.BOTH, expand=True)

    # ------------------ EVENT HANDLERS / SIMULATED HARDWARE FUNCTIONS ------------------
    def on_parking_brake_toggle(self):
        if not self.is_running:
            self.log_message("[HW Warning] Switch flipped on Pin 4, but MobiFlight is STOPPED. No data sent.")
            return
        val = self.brake_var.get()
        self.log_message(f"[Input Event] Hardware Pin 4 (Switch) -> State: {val}")
        # Map input event to change flight simulator value
        self.sim_variables["PARKING_BRAKE_INDICATOR"] = val
        self.log_message(f"[MobiFlight] Executed Event Mapping: Send 'PARKING_BRAKE_SET' with value {val}")

    def on_gear_toggle(self):
        if not self.is_running:
            self.log_message("[HW Warning] Button pressed on Pin 5, but MobiFlight is STOPPED.")
            return
        current = self.gear_var.get()
        new_state = "UP" if current == "DOWN" else "DOWN"
        self.gear_var.set(new_state)
        
        self.log_message(f"[Input Event] Hardware Pin 5 (Button) -> Pressed")
        self.sim_variables["GEAR_HANDLE_POSITION"] = 0 if new_state == "UP" else "1"
        self.log_message(f"[MobiFlight] Executed Event Mapping: Trigger Sim Event 'GEAR_TOGGLE'")

    def on_encoder_turn(self, direction):
        if not self.is_running:
            return
        action = "INC" if direction > 0 else "DEC"
        self.log_message(f"[Input Event] Hardware Pins 6/7 (Encoder) -> Turned {action}")
        
        # Modify the local sim register
        self.sim_variables["AUTOPILOT_HEADING_LOCK_DIR"] = (self.sim_variables["AUTOPILOT_HEADING_LOCK_DIR"] + direction) % 360
        if self.sim_variables["AUTOPILOT_HEADING_LOCK_DIR"] == 0:
            self.sim_variables["AUTOPILOT_HEADING_LOCK_DIR"] = 360
            
        self.log_message(f"[MobiFlight] Executed Event Mapping: Trigger SimEvent 'HEADING_BUG_{action}'")

    # ------------------ MOBIFLIGHT EXECUTION ENGINE ------------------
    def start_mobiflight(self):
        self.is_running = True
        self.run_btn.config(state=tk.DISABLED, bg="#555555")
        self.stop_btn.config(state=tk.NORMAL)
        self.log_message("[System] MobiFlight Execution loop started. SimConnect Hook Active.")
        
        # Start background update cycle thread for outputs (LED & Displays)
        self.loop_thread = Thread(target=self.output_sync_loop, daemon=True)
        self.loop_thread.start()

    def stop_mobiflight(self):
        self.is_running = False
        self.run_btn.config(state=tk.NORMAL, bg="#007acc")
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("[System] MobiFlight Execution loop stopped. Hardware link dormant.")
        # Turn off LED visually because hardware execution stops
        self.led_canvas.itemconfig(self.led_light, fill="#440000")

    def output_sync_loop(self):
        """Simulates MobiFlight querying SimConnect offsets and updating the registers."""
        while self.is_running:
            # 1. Sync simulated LED to 'PARKING_BRAKE_INDICATOR' data value
            brake_val = self.sim_variables["PARKING_BRAKE_INDICATOR"]
            led_color = "#ff0000" if brake_val == 1 else "#440000"
            self.led_canvas.itemconfig(self.led_light, fill=led_color)
            
            # 2. Sync Heading variable to the 7-Segment display output register
            hdg_val = f"{self.sim_variables['AUTOPILOT_HEADING_LOCK_DIR']:03d}"
            self.hdg_display_val.set(hdg_val)
            

