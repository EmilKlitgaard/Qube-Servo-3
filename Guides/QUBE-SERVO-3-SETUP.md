# QUBE-Servo 3 — Windows Setup Guide

This guide walks you through installing the required software and drivers to communicate with the **Quanser QUBE-Servo 3** on a native Windows machine. Two software stacks are available; this guide focuses on the **real-time driver** (Quanser QUARC with MATLAB/Simulink) but also covers the **non-real-time Python SDK** for standalone Python use.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Hardware Overview](#2-hardware-overview)
3. [Software Options: QUARC vs. Python SDK](#3-software-options-quarc-vs-python-sdk)
4. [Option A — QUARC (Real-Time)](#4-option-a--quarc-real-time)
   - [4.1 Install MATLAB & Simulink](#41-install-matlab--simulink)
   - [4.2 Install QUARC](#42-install-quarc)
   - [4.3 Install the USB HIL Driver](#43-install-the-usb-hil-driver)
5. [Option B — Quanser Python SDK (Non-Real-Time)](#5-option-b--quanser-python-sdk-non-real-time)
   - [5.1 Download & Install the SDK](#51-download--install-the-sdk)
   - [5.2 Install the Python Package](#52-install-the-python-package)
6. [Connecting the Hardware](#6-connecting-the-hardware)
7. [Verifying the Connection](#7-verifying-the-connection)
8. [Python Project Setup (this repository)](#8-python-project-setup-this-repository)
9. [Configuration Reference](#9-configuration-reference)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Requirements

| Requirement | Details |
|---|---|
| **Operating System** | Windows 10 or Windows 11 (64-bit only) |
| **USB port** | USB-A or USB-C with USB 2.0 or later |
| **Python** (for Python SDK) | 3.10 – 3.12, 64-bit |
| **MATLAB** (for QUARC only) | R2021a or later (with Simulink) |
| **RAM** | 8 GB minimum, 16 GB recommended |
| **Disk space** | ~4 GB for QUARC, ~200 MB for Python SDK |

> **Important:** Only the 64-bit (x64) architecture is supported. Do not use a 32-bit Python interpreter or a 32-bit Windows installation.

---

## 2. Hardware Overview

The **QUBE-Servo 3** is a USB-powered rotary servo module. Key hardware details relevant to driver setup:

| Component | Details |
|---|---|
| **USB device** | Identified as `qube_servo3_usb` in the HIL API |
| **Board index** | `"0"` (first connected unit) |
| **Encoder resolution** | 512 PPR × 4× quadrature = **2048 counts/rev** |
| **Motor voltage range** | ±18 V (amplifier hard limit) |
| **Encoder channels** | Ch 0 = arm (θ), Ch 1 = pendulum (α) |
| **Analog output channel** | Ch 0 = motor voltage |
| **Power** | Bus-powered over USB (no external PSU needed) |

The device exposes a **HIL (Hardware Interface Layer)** abstraction. All communication — encoder reads, voltage writes, LED control — goes through the HIL API, which is provided by either QUARC or the Python SDK.

---

## 3. Software Options: QUARC vs. Python SDK

| Feature | QUARC (Real-Time) | Python SDK (Non-Real-Time) |
|---|---|---|
| **Real-time execution** | Yes (deterministic, kernel-level) | No (best-effort, OS-scheduled) |
| **MATLAB/Simulink required** | Yes | No |
| **Python `quanser` package** | Included | Included |
| **HIL API access from Python** | Yes | Yes |
| **Typical use case** | Control experiments, hardware-in-the-loop | Rapid prototyping, data logging, research |
| **Cost** | Commercial licence required | Free (open-source installer) |
| **Installer source** | quanser.com (licence required) | GitHub Releases |

For most student and research projects where MATLAB is available, **QUARC is the recommended path** because it installs both the MATLAB toolchain and the USB HIL drivers in one step. If you only need Python without MATLAB, use the Python SDK.

---

## 4. Option A — QUARC (Real-Time)

### 4.1 Install MATLAB & Simulink

1. Download and install **MATLAB** from [mathworks.com](https://www.mathworks.com/downloads/).
2. During installation, make sure the following toolboxes are selected:
   - **Simulink**
   - **Simulink Real-Time** *(optional but recommended for HIL experiments)*
   - **Control System Toolbox** *(recommended)*
3. After installation, open MATLAB and confirm it launches without errors.

> QUARC is compatible with MATLAB R2021a and later. Check Quanser's release notes for the exact compatibility matrix of your QUARC version.

---

### 4.2 Install QUARC

1. Visit [quanser.com](https://www.quanser.com) and log in to your Quanser account. If your institution provides a licence, use that portal.
2. Navigate to **Downloads → QUARC** and download the latest installer for Windows 64-bit.
3. Run the installer **as Administrator** (right-click → *Run as administrator*).
4. Follow the setup wizard:
   - Accept the licence agreement.
   - Keep the default installation path (`C:\Program Files\Quanser\QUARC`).
   - When prompted, select **Install USB HIL Drivers** — this installs the low-level Windows driver that the QUBE uses.
5. The installer will integrate with your MATLAB installation automatically. If MATLAB is not detected, verify it is on the system `PATH`.
6. Restart Windows when prompted.

After rebooting, launch MATLAB. You should see a **QUARC** menu in the MATLAB toolbar and a `quarc_win64` target available in Simulink.

---

### 4.3 Install the USB HIL Driver

The USB driver is normally installed automatically by the QUARC installer (step 4.2). You can verify this:

1. Plug the QUBE-Servo 3 into a USB port.
2. Open **Device Manager** (press `Win + X` → *Device Manager*).
3. Expand the **Quanser Devices** category. You should see:
   ```
   Quanser Devices
   └── QUBE-Servo 3
   ```
4. If the device shows a yellow warning icon, right-click it and select **Update driver** → **Search automatically for drivers**.

If the driver is missing entirely, re-run the QUARC installer and make sure **Install USB HIL Drivers** is checked.

---

## 5. Option B — Quanser Python SDK (Non-Real-Time)

Use this path if you do **not** have a QUARC licence but still want to control the hardware from Python.

### 5.1 Download & Install the SDK

1. Go to the **Quanser SDK for Windows** releases page:
   ```
   https://github.com/quanser/quanser_sdk_win64/releases
   ```
2. Download the latest `.exe` installer (e.g. `quanser_sdk_win64_<version>_setup.exe`).
3. Run the installer **as Administrator**.
4. Follow the wizard and keep the default paths.
5. The installer:
   - Installs the **USB HIL driver** for the QUBE-Servo 3.
   - Installs the Quanser runtime libraries.
   - Places the `quanser` Python wheel in a known location (typically `C:\Program Files\Quanser\Python`).
6. Restart Windows when prompted.

### 5.2 Install the Python Package

After the SDK installer has finished, install the `quanser` Python package into your environment:

```powershell
# Find the wheel bundled with the SDK installer:
# Default path: C:\Program Files\Quanser\Python\quanser-<version>-cp3xx-cp3xx-win_amd64.whl

pip install "C:\Program Files\Quanser\Python\quanser-<version>-cp3xx-cp3xx-win_amd64.whl"
```

> Replace `<version>` and `cp3xx` with the actual version and Python version in the filename (e.g. `cp312` for Python 3.12).

Verify the installation:

```powershell
python -c "from quanser.hardware import HIL; print('Quanser SDK OK')"
```

If this line prints `Quanser SDK OK` without errors, the package is correctly installed.

---

## 6. Connecting the Hardware

1. Locate the **USB cable** that came with the QUBE-Servo 3 (USB-A to USB-B or USB-C, depending on your unit).
2. Connect the QUBE to any USB 2.0 or higher port on your PC.
3. The RGB LED on the QUBE will briefly flash, indicating it has received power.
4. Wait for Windows to finish driver enumeration (5–10 seconds after the first connection; instant on subsequent connections).
5. Open **Device Manager** and confirm the device appears under **Quanser Devices** without a warning icon.

> If you are connecting multiple QUBE units simultaneously, each is assigned a sequential board index starting at `"0"`. The first unit is always `"0"`.

---

## 7. Verifying the Connection

The quickest way to verify end-to-end communication is a minimal Python script using the HIL API:

```python
import numpy as np
from quanser.hardware import HIL

card = HIL("qube_servo3_usb", "0")

# Read both encoder channels (arm and pendulum)
enc_channels = np.array([0, 1], dtype=np.uint32)
counts        = np.zeros(2, dtype=np.int32)
card.read_encoder_counts(enc_channels, len(enc_channels), counts)

print(f"Encoder counts — arm: {counts[0]}, pendulum: {counts[1]}")

card.close()
```

Expected output (with the pendulum at rest):
```
Encoder counts — arm: 0, pendulum: 0
```

If a `HILError` is raised, see the [Troubleshooting](#10-troubleshooting) section below.

---

## 8. Python Project Setup (this repository)

This section walks through setting up the project's Python environment on Windows. For a full virtual-environment guide see [`VIRTUAL-ENVIRONMENT.md`](VIRTUAL-ENVIRONMENT.md).

### 8.1 Create and activate a virtual environment

Open a terminal (PowerShell or Command Prompt) in the project root:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 8.2 Install project dependencies

```powershell
pip install -r Python\requirements.txt
```

> The `requirements.txt` intentionally omits `quanser` because it must be installed from the SDK installer's bundled wheel (see [Section 5.2](#52-install-the-python-package)). Install it separately after activating your virtual environment.

### 8.3 Install the Quanser package into the venv

```powershell
pip install "C:\Program Files\Quanser\Python\quanser-<version>-cp3xx-cp3xx-win_amd64.whl"
```

### 8.4 Edit `Config.yaml`

Open `Python\Config.yaml` and adjust the settings for your machine:

```yaml
DEBUG: false          # Set to true for verbose startup output

UART:
  PORT: COM5          # Windows COM port of your Tiva microcontroller (if used)
  BAUDRATE: 19200

QUBE:
  SIMULATION: false   # false = real hardware, true = virtual simulation
  KP: 0.5
  KD: 0.1
  SIMULATION_SPEED: 1
```

To find the correct COM port for the Tiva (if applicable), open **Device Manager** → **Ports (COM & LPT)** and look for the *Stellaris Virtual Serial Port* or *XDS110 Class Application/User UART* entry.

### 8.5 Run the project

```powershell
cd Python
python main.py
```

---

## 9. Configuration Reference

The project's runtime behaviour is controlled entirely by `Python\Config.yaml`. The `Config.py` singleton loads this file once at startup and exposes all values as flat attributes (e.g. `config.QUBE_SIMULATION`).

| Key | Type | Description |
|---|---|---|
| `DEBUG` | bool | Print all config values at startup |
| `UART.PORT` | string | Serial port for the Tiva MCU (Windows: `COMx`) |
| `UART.BAUDRATE` | int | Baud rate (default `19200`) |
| `QUBE.SIMULATION` | bool | `false` = use real hardware via HIL; `true` = use `Virtual()` |
| `QUBE.KP` | float | Proportional gain for the PD controller |
| `QUBE.KD` | float | Derivative gain for the PD controller |
| `QUBE.SIMULATION_SPEED` | float | Simulation speed multiplier (`1.0` = real time) |

The HIL board is always opened with:

```python
HIL("qube_servo3_usb", "0")
#        ↑ board type      ↑ board index (0 = first unit)
```

---

## 10. Troubleshooting

### Device not found in Device Manager

- Try a different USB port (prefer a port directly on the motherboard, not a hub).
- Re-run the QUARC or SDK installer and ensure the driver installation step is included.
- Run `pnputil /enum-devices /class "Quanser"` in an elevated PowerShell to list all Quanser device nodes.

### `HILError: -1073 Device not found`

- Confirm the USB cable is firmly seated at both ends.
- Confirm the device appears in Device Manager **without** a warning icon.
- Make sure no other process (e.g. QUARC Workbench, another Python script) has already opened the card.
- Only one `HIL` handle per physical device is allowed at a time. Close any other sessions first.

### `ModuleNotFoundError: No module named 'quanser'`

- The `quanser` wheel was not installed into the active environment.
- Re-run: `pip install "C:\Program Files\Quanser\Python\quanser-<version>-...whl"` inside your activated venv.
- Ensure you are using the 64-bit Python interpreter: `python -c "import struct; print(struct.calcsize('P')*8)"` should print `64`.

### USB driver shows a yellow warning icon

- Right-click the device in Device Manager → **Update driver** → **Browse my computer** → navigate to `C:\Program Files\Quanser\Drivers`.
- If the folder does not exist, re-install QUARC or the SDK.

### Encoder reads zero after the pendulum was moved

- Confirm `card.set_encoder_counts(channels, len(channels), zeros)` has not been called inadvertently at startup, which resets the counts.
- The QUBE does not retain encoder state across power cycles; always call `reset()` before your control loop to establish a known reference.

### Motor does not respond but no error is raised

- Confirm `enable(True)` has been called on the card before writing voltages.
- Verify the voltage command is within ±18 V; the amplifier silently clamps out-of-range values.
- Check the LED colour: red = disabled/fault, green = enabled.
