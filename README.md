# Detective Eye

**A Computer-Vision-Driven Robotic Eye System**

Detective Eye is a robotics project that combines computer vision, embedded systems, and servo motor control to produce physical eye movements in response to visual input.

The system uses a Raspberry Pi to run Python-based vision processing and communicate commands to an Arduino. The Arduino processes these commands and controls the servos responsible for moving the robot's eyes.

## System Architecture

The system is divided into two main components:

### 1. Raspberry Pi: Vision Processing
- Runs the Python program.
- Processes visual input and performs the implemented vision tasks.
- Sends movement commands to the Arduino.

### 2. Arduino: Servo Control
- Receives commands from the Raspberry Pi.
- Controls the servo motors.
- Produces the corresponding eye movements.

### Control Flow

Camera → Python Vision Processing → Arduino Communication → Servo Control → Eye Movement

## Hardware Components

- Raspberry Pi
- Arduino microcontroller
- Camera or visual input device
- Servo motors
- Robotic eye assembly
- Supporting wiring and power supply

## Software and Technologies

- Python
- Arduino C/C++
- Computer vision
- Serial or other communication interface, as implemented in the original code
- Arduino IDE

## Repository Structure

```text
detective-eye/
├── README.md
├── eye_brain.py
└── updated_Detective_Eye_Robot_Code.ino
```

- `README.md`: Project overview, system architecture, and demonstration link.
- `eye_brain.py`: Python code for the Raspberry Pi's vision-processing and control workflow.
- `updated_Detective_Eye_Robot_Code.ino`: Arduino sketch for the robotic eye's servo-control system.

## Demonstration

Watch the robot demonstration:

https://youtube.com/shorts/JDT0XNlPn4k

## Project Objectives

- Integrate computer vision with embedded systems.
- Translate visual-processing outputs into physical robotic movement.
- Explore communication between a Raspberry Pi and an Arduino.
- Develop practical experience in robotics and hardware-software integration.

## Author

**Samuel Kenneth Silva-Eboagwu**

Physics (Electronics) | Computer Vision | Robotics | Embedded Systems
