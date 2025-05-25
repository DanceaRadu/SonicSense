import customtkinter as ctk

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)

        self.title("Settings")
        self.geometry("250x370")
        self.after(10, self.grab_set)
        self.changed_settings = {
            "frequency": settings.get("frequency"),
            "sound_threshold": settings.get("sound_threshold"),
            "bandwidth": settings.get("bandwidth"),
            "event_sound_threshold": settings.get("event_sound_threshold")
        }
        self.settings = settings

        # Frequency
        freq_label = ctk.CTkLabel(self, text="Frequency (Hz)")
        freq_label.pack(pady=(10, 0))
        combobox_frequency = ctk.CTkComboBox(
            self, 
            values=["250", "500", "1000", "2000", "4000"],
            command=self.set_frequency
        )
        combobox_frequency.set(self.changed_settings["frequency"])
        combobox_frequency.pack(pady=10)

        # Sound threshold
        threshold_label = ctk.CTkLabel(self, text="Sound Threshold")
        threshold_label.pack(pady=(0, 0))
        combobox_threshold = ctk.CTkComboBox(
            self, 
            values=["0.2", "0.5", "1.0", "2.0", "10.0"],
            command=self.set_threshold
        )
        combobox_threshold.set(self.changed_settings["sound_threshold"])
        combobox_threshold.pack(pady=10)

        # Event sound threshold
        event_threshold_label = ctk.CTkLabel(self, text="Event Threshold")
        event_threshold_label.pack(pady=(0, 0))
        combobox_event_threshold = ctk.CTkComboBox(
            self, 
            values=["2.0", "3.0", "5.0", "7.0", "10.0"],
            command=self.set_event_sound_threshold
        )
        combobox_event_threshold.set(self.changed_settings["event_sound_threshold"])
        combobox_event_threshold.pack(pady=10)

        # Bandwith channels
        bandwidth_label = ctk.CTkLabel(self, text="Bandwidth channels")
        bandwidth_label.pack(pady=(0, 0))
        combobox_bandwidth = ctk.CTkComboBox(
            self, 
            values=["1", "2", "3"],
            command=self.set_bandwidth
        )
        combobox_bandwidth.set(self.changed_settings["bandwidth"])
        combobox_bandwidth.pack(pady=10)

        close_btn = ctk.CTkButton(self, text="Save", command=self.save)
        close_btn.pack(pady=10)

    def set_frequency(self, value):
        self.changed_settings["frequency"] = int(value)

    def set_threshold(self, value):
        self.changed_settings["sound_threshold"] = float(value)

    def set_bandwidth(self, value):
        self.changed_settings["bandwidth"] = int(value)

    def set_event_sound_threshold(self, value):
        self.changed_settings["event_sound_threshold"] = float(value)

    def save(self):
        self.settings.update(self.changed_settings)
        self.destroy()
