# Virtual Environment Setup Guide

## Introduction

Select the guide for your operating system below. This project uses a **root virtual environment** approach, where the venv is created in your home directory for better organization.

- **[macOS](#macos)** — Using Homebrew
- **[Windows](#windows)** — Using Python installer
- **[General (Not used for this project)](#general-not-used-for-this-project)** — Legacy approach *(deprecated)*

> **Note:** The `quanser` package must be installed separately via the [Quanser Python SDK / QUARC installer](https://www.quanser.com) — it is not available on PyPI and is therefore excluded from `requirements.txt`.

---

## macOS

### Prerequisites

- Homebrew installed on your Mac

### Step 1: Install Python 3.12

```bash
brew install python@3.12
```

### Step 2: Verify Python Installation

```bash
which python3.12
```

You should see: `/opt/homebrew/bin/python3.12`

### Step 3: Create Virtual Environment

```bash
python3.12 -m venv ~/qube_venv
```

### Step 4: Activate Virtual Environment

```bash
source ~/qube_venv/bin/activate
```

Your terminal prompt should now show `(qube_venv)` at the beginning.

### Step 5: Navigate to Python Directory

```bash
cd Python
```

Make sure you're in the `Python` folder of the Qube-Servo-3 project.

### Step 6: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 7: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 8: Run the Application

```bash
python main.py
```

### Troubleshooting

**Module not found error:**
- Make sure you're in the virtual environment (check for `(qube_venv)` in your prompt)
- Verify you're in the `Python` directory
- Try reinstalling Python: `brew reinstall python@3.12`

---

## Windows

### Prerequisites

- Python 3.12 installed on your Windows machine ([Download here](https://www.python.org/downloads/))

### Step 1: Verify Python Installation

Open Command Prompt or PowerShell and run:

```bash
python --version
```

Ensure it shows `Python 3.12.x`

### Step 2: Create Virtual Environment

```bash
python -m venv qube_venv
```

### Step 3: Activate Virtual Environment

```bash
qube_venv\Scripts\activate
```

Your command prompt should now show `(qube_venv)` at the beginning.

### Step 4: Navigate to Python Directory

```bash
cd Python
```

Make sure you're in the `Python` folder of the Qube-Servo-3 project.

### Step 5: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Run the Application

```bash
python main.py
```

### Troubleshooting

**Module not found error:**
- Verify virtual environment is activated (should see `(qube_venv)` in prompt)
- Verify you're in the `Python` directory
- Delete `qube_venv` folder and recreate it from Step 2

**Dependencies won't install:**
- Ensure pip is up to date by running the upgrade step again
- Try installing one package at a time to identify which one fails
- Check your internet connection

---

## General (Not used for this project)

> **Note:** This approach is deprecated. Use the macOS or Windows guide above instead.

### 1. Create the virtual environment

Run once from the **repo root**:

```bash
python3 -m venv venv
```

This creates `Qube-Servo-3/venv/`.

---

### 2. Activate the virtual environment

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

Your prompt will change to show `(venv)` when active.

---

### 3. Install dependencies

With the venv active, install all packages from `requirements.txt`:

```bash
pip install -r Python/requirements.txt
```

---

### 4. Run the project

```bash
cd Python
python main.py
```

---

### 5. Save / update requirements

After installing or upgrading any package, update `requirements.txt` with:

```bash
pip freeze > Python/requirements.txt
```

> Re-open `Python/requirements.txt` afterwards and remove the `quanser`
> line if it was captured, to keep it out of the file.

---

### 6. Deactivate the virtual environment

```bash
deactivate
```

Your prompt returns to normal.