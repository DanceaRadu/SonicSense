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
        
        self.option_buttons = {}
        self.options_config = {
            "frequency": ["250", "500", "1000", "2000", "4000"],
            "sound_threshold": ["0.5", "1.0", "2.0", "5.0", "10.0"],
            "event_sound_threshold": ["0.5", "1.0", "2.0", "5.0", "10.0"],
            "bandwidth": ["0", "1", "2", "3"]
        }

        self.build_settings_grid()

        save_btn = ctk.CTkButton(
            self, text="Save", font=("Arial", 20),
            command=self.save, height=50, width=200
        )
        save_btn.grid(row=len(self.options_config)+1, column=0, columnspan=10, pady=30)

    def build_settings_grid(self):
        for row_idx, (setting_key, values) in enumerate(self.options_config.items()):
            label = ctk.CTkLabel(self, text=setting_key.replace("_", " ").title(), font=("Arial", 20))
            label.grid(row=row_idx, column=0, padx=10, pady=10, sticky="w")

            self.option_buttons[setting_key] = []

            for col_idx, value in enumerate(values):
                btn = ctk.CTkButton(
                    self,
                    text=value,
                    width=80,
                    height=40,
                    font=("Arial", 18),
                    command=lambda k=setting_key, v=value: self.select_option(k, v)
                )
                btn.grid(row=row_idx, column=col_idx + 1, padx=5, pady=5)

                self.option_buttons[setting_key].append((value, btn))

                if str(self.changed_settings[setting_key]) == value:
                    btn.configure(fg_color="dodgerblue", text_color="white")
                else:
                    btn.configure(fg_color="gray20", text_color="white")

    def select_option(self, key, value):
        self.changed_settings[key] = float(value) if "." in value else int(value)

        for val, btn in self.option_buttons[key]:
            if val == value:
                btn.configure(fg_color="dodgerblue")
            else:
                btn.configure(fg_color="gray20")

    def save(self):
        self.settings.update(self.changed_settings)
        self.destroy()
