# Hand Tracking Thingy

A Windows 11 webcam hand-tracking experiment using MediaPipe and OpenCV. The project is being developed toward a Kinect-inspired interactive dashboard and Toybox.

## Current features

- Hand landmark tracking
- Finger-state detection
- Pinch detection
- Palm-controlled Windows mouse
- Cursor smoothing
- Pinch = left click
- Index-only gesture = right click
- Two fingers = scroll
- Fist = pause mouse control
- Open palm = activate mouse control
- Swipe controls intentionally removed

## Requirements

- Windows 11
- Python 3.14.x
- A working webcam

Tested with:

- MediaPipe 1.2.0
- OpenCV 5.0.0

## Installation

1. Clone the repository:

```text
git clone https://github.com/Labokid11/hand-tracking-thingy.git
cd hand-tracking-thingy
```

2. Install the Python dependencies:

```text
python -m pip install -r requirements.txt
```

3. Put the MediaPipe Hand Landmarker model at:

```text
models/hand_landmarker.task
```

The model is kept out of the repository for now. If you already have the model from the development setup, copy that file into the `models` folder.

4. Run the hand tracker:

```text
python hand_test.py
```

5. Press `ESC` in the camera window to quit.

## Camera test

To test whether OpenCV can access the webcam:

```text
python camera_test.py
```

## Project roadmap

- Improve tracking responsiveness
- Separate hand tracking from the UI
- Build a Kinect-era Xbox 360 dashboard-inspired interface
- Add dashboard navigation using the hand controller
- Add a Toybox section with small experimental hand-controlled toys

## Notes

This project is currently Windows-specific because mouse control uses the Windows `user32` API.

The `.venv` directory is intentionally not part of the repository. Create your own environment if you want one.
