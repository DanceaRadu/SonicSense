import threading
import os
import json

class UserSettings:
    def __init__(self, settings_path):
        self.settings_path = settings_path
        self._settings = None
        self._lock = threading.Lock()
        self.load_user_settings_from_file()

    def get(self, key, default=None):
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key, value):
        with self._lock:
            self._settings[key] = value

    def update(self, new_settings: dict):
        with self._lock:
            if self._settings is None:
                self._settings = {}
            self._settings.update(new_settings)
            try:
                with open(self.settings_path, "w") as f:
                    json.dump(new_settings, f, indent=4)
            except IOError as e:
                print(f"Failed to save user settings: {e}")

    def to_dict(self):
        with self._lock:
            return self._settings.copy()
        
    def load_user_settings_from_file(self):
        default_config = {
            "sound_threshold": 1.0,
            "frequency": 1000,
            "bandwidth": 1,
            "event_sound_threshold": 2.0,
        }

        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    user_config = json.load(f)
            else:
                user_config = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading user settings: {e}")
            user_config = {}

        merged_config = {
            "sound_threshold": user_config.get("sound_threshold", default_config["sound_threshold"]),
            "frequency": user_config.get("frequency", default_config["frequency"]),
            "bandwidth": user_config.get("bandwidth", default_config["bandwidth"]),
            "event_sound_threshold": user_config.get("event_sound_threshold", default_config["event_sound_threshold"]),
        }
        self.update(merged_config)
