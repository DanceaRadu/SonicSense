import customtkinter as ctk

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, initial_settings, settings_callback):
        super().__init__(parent)

        self.title("Settings")
        self.geometry("250x320")
        self.after(10, self.grab_set)
        self.settings_callback = settings_callback
        self.changed_settings = {
            "frequency": initial_settings["frequency"],
            "sound_threshold": initial_settings["sound_threshold"],
            "bandwidth": initial_settings["bandwidth"]
        }

        freq_label = ctk.CTkLabel(self, text="Frequency (Hz)")
        freq_label.pack(pady=(10, 0))
        combobox_frequency = ctk.CTkComboBox(
            self, 
            values=["250", "500", "1000", "2000", "4000"],
            command=self.set_frequency
        )
        combobox_frequency.set(initial_settings["frequency"])
        combobox_frequency.pack(pady=10)


        threshold_label = ctk.CTkLabel(self, text="Sound Threshold")
        threshold_label.pack(pady=(0, 0))
        combobox_threshold = ctk.CTkComboBox(
            self, 
            values=["0.2", "0.5", "1.0", "2.0"],
            command=self.set_threshold
        )
        combobox_threshold.set(initial_settings["sound_threshold"])
        combobox_threshold.pack(pady=10)


        bandwidth_label = ctk.CTkLabel(self, text="Bandwidth channels")
        bandwidth_label.pack(pady=(0, 0))
        combobox_bandwidth = ctk.CTkComboBox(
            self, 
            values=["1", "2", "3"],
            command=self.set_bandwidth
        )
        combobox_bandwidth.set(initial_settings["bandwidth"])
        combobox_bandwidth.pack(pady=10)

        close_btn = ctk.CTkButton(self, text="Save", command=self.save)
        close_btn.pack(pady=10)

    def set_frequency(self, value):
        self.changed_settings["frequency"] = int(value)

    def set_threshold(self, value):
        self.changed_settings["sound_threshold"] = float(value)

    def set_bandwidth(self, value):
        self.changed_settings["bandwidth"] = int(value)

    def save(self):
        self.settings_callback(self.changed_settings)
        self.destroy()
