## Overview

This is the main software component of the SonicSense project. This python app runs on the acoustic camera and handles beamforming, communication with the backend and event detection. The app also uses CustomTkinter in order to create the user interface shown on the LCD display. 

## Prerequisites

Make sure **libcamera**, **FFmpeg** and **v4l2loopback** are installed on the machine.

## Starting the app

```bash
pip install -r requirements.txt
python src/main.py