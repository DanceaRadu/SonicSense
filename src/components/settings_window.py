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
        self.label_font = ("Arial", 22)
        self.combobox_font = ("Arial", 24)
        self.width = 300
        self.height = 50

        # Frequency
        freq_label = ctk.CTkLabel(self, text="Frequency (Hz)", font=self.label_font)
        freq_label.pack(pady=(20, 0))
        combobox_frequency = ctk.CTkComboBox(
            self, 
            values=["250", "500", "1000", "2000", "4000"],
            command=self.set_frequency,
            height=50,
            width=self.width,
            font=self.combobox_font,
            dropdown_font=self.combobox_font
        )
        combobox_frequency.set(self.changed_settings["frequency"])
        combobox_frequency.pack(pady=10)

        # Sound threshold
        threshold_label = ctk.CTkLabel(self, text="Sound Threshold", font=self.label_font)
        threshold_label.pack(pady=(20, 0))
        combobox_threshold = ctk.CTkComboBox(
            self, 
            values=["0.5", "1.0", "2.0", "5.0", "10.0"],
            command=self.set_threshold,
            height=self.height,
            width=self.width,
            font=self.combobox_font,
            dropdown_font=self.combobox_font
        )
        combobox_threshold.set(self.changed_settings["sound_threshold"])
        combobox_threshold.pack(pady=10)

        # Event sound threshold
        event_threshold_label = ctk.CTkLabel(self, text="Event Threshold", font=self.label_font)
        event_threshold_label.pack(pady=(20, 0))
        combobox_event_threshold = ctk.CTkComboBox(
            self, 
            values=["0.5", "1.0", "2.0", "5.0", "10.0"],
            command=self.set_event_sound_threshold,
            height=self.height,
            width=self.width,
            font=self.combobox_font,
            dropdown_font=self.combobox_font
        )
        combobox_event_threshold.set(self.changed_settings["event_sound_threshold"])
        combobox_event_threshold.pack(pady=10)

        # Bandwith channels
        bandwidth_label = ctk.CTkLabel(self, text="Bandwidth channels", font=self.label_font)
        bandwidth_label.pack(pady=(20, 0))
        combobox_bandwidth = ctk.CTkComboBox(
            self, 
            values=["0", "1", "2", "3"],
            command=self.set_bandwidth,
            height=self.height,
            width=self.width,
            font=self.combobox_font,
            dropdown_font=self.combobox_font
        )
        combobox_bandwidth.set(self.changed_settings["bandwidth"])
        combobox_bandwidth.pack(pady=10)

        close_btn = ctk.CTkButton(
            self, 
            text="Save", 
            command=self.save, 
            font=("Arial", 24),
            border_spacing=10,
            width=self.width,
        )
        close_btn.pack(pady=40)

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
