from acoular import RectGrid
import math
import os
import subprocess

class HelperService:
    def __init__(self):
        pass

    @staticmethod
    def getRectGridBasedOnCameraFOV(horizontal_fov, vertical_fov, z, increment = 0.01):
        horizontal_fov_radians = math.radians(horizontal_fov)
        vertical_fov_radians = math.radians(vertical_fov)

        horizontal_angle_tangent = math.tan(horizontal_fov_radians / 2)
        vertical_angle_tangent = math.tan(vertical_fov_radians / 2)

        horizontal_distance = z * horizontal_angle_tangent
        vertical_distance = z * vertical_angle_tangent
        print(f"Horizontal distance: {horizontal_distance}, Vertical distance: {vertical_distance}")

        return RectGrid(
            x_min=-horizontal_distance, 
            x_max=horizontal_distance, 
            y_min=-vertical_distance, 
            y_max=vertical_distance,
            z=-z, increment=increment
        )
    
    @staticmethod
    def ensure_v4l2loopback_device(device="/dev/video10", label="PiCam"):
        if not os.path.exists(device):
            print(f"Creating {device} using v4l2loopback...")
            try:
                subprocess.run([
                    "sudo", "modprobe", "v4l2loopback",
                    "devices=1",
                    f"video_nr={device[-2:]}",
                    f"card_label={label}",
                    "exclusive_caps=1"
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to load v4l2loopback: {e}")
                exit(1)