# Windows Nuitka Build Plan

This repository is being prepared for a **Windows-only physical release** built with **Nuitka**. The goal is not to simulate the QUBE-Servo 3 in the binary, but to package the Python control application into a native Windows executable with the smallest practical runtime surface.

## Scope

- Target OS: Windows 10/11
- Target mode: physical hardware only
- Simulation: disabled for the release build
- Viewer / MuJoCo: excluded from the release build
- GUI / plotting: optional, but not required for the physical release

## Why Nuitka

Nuitka compiles Python modules into C/C++ and then produces a native executable. In this project, the speedup will mostly come from:

- lower Python interpreter overhead at startup
- fewer runtime imports
- less dependency churn from avoiding simulation modules
- better packaging for deployment on a Windows control PC

It will not remove the cost of hardware I/O or the Quanser SDK calls, and it will not make already-native libraries like `numpy` or `serial` dramatically faster on their own.

## Current Repository Constraints

The current configuration in `Python/Config.yaml` is already aligned with the physical release:

- `QUBE.SIMULATION: false`
- `QUBE.VISUALIZE: false`
- `GUI.ENABLED: false`
- `DATA.LOGGING: false`
- `DATA.PLOTTING: false`

The main release risk was the import chain, not the control logic itself. Package-level imports previously pulled simulation and plotting modules into the load path. The codebase was adjusted so the physical entry point imports the hardware path directly.

## Build Strategy

### 1. Keep the physical entry point minimal

The executable should start from `Python/main.py`, but the import graph must stay physical-only:

- import `Physical` directly, not through package-level `__init__.py`
- import `run_controller` directly from `controller/ControlLoop.py`
- import `Logger` directly from `data/Logging.py` if logging is enabled
- do not import `Virtual` unless a separate simulation build is needed

### 2. Build from Windows

Build on the same OS that will run the executable. For this project, that means Windows with:

- Quanser SDK installed
- Python venv activated
- the same runtime dependencies that the script uses

### 3. Freeze only what the physical build needs

For the current config, the release should exclude:

- MuJoCo
- simulation XML/assets
- customtkinter GUI stack
- matplotlib plotting stack

If later you enable GUI or logging, add those back deliberately rather than bundling them by default.

## Recommended Nuitka Command

### Install Nuitka on Windows

Use the Windows Python launcher if it is available:

```powershell
py -m pip install --upgrade pip
py -m pip install nuitka
```

If you are using an activated virtual environment, this also works:

```powershell
python -m pip install --upgrade pip
python -m pip install nuitka
```

### Important: Windows line continuation

The backslash character `\` is **not** a line-continuation character in PowerShell or `cmd.exe`. That is why `--standalone \` produces the error about a missing expression after `--`.

Use one of these instead:

- PowerShell continuation: backtick `` ` ``
- `cmd.exe` continuation: caret `^`
- Easiest option: keep the command on one line

### Minimal physical build

Use this if you want the smallest deployment surface and you are keeping the current config values:

PowerShell:

```powershell
py -m nuitka `
  --standalone `
  --onefile `
  --assume-yes-for-downloads `
  --output-dir=build `
  Python/main.py
```

cmd.exe:

```bat
py -m nuitka ^
  --standalone ^
  --onefile ^
  --assume-yes-for-downloads ^
  --output-dir=build ^
  Python/main.py
```

Single line:

```bash
py -m nuitka --standalone --onefile --assume-yes-for-downloads --output-dir=build Python/main.py
```

### If you want to pin the config file explicitly

PowerShell:

```powershell
py -m nuitka `
  --standalone `
  --onefile `
  --assume-yes-for-downloads `
  --output-dir=build `
  --include-data-file=Python/Config.yaml=Config.yaml `
  Python/main.py
```

Single line:

```bash
py -m nuitka --standalone --onefile --assume-yes-for-downloads --output-dir=build --include-data-file=Python/Config.yaml=Config.yaml Python/main.py
```

## Recommended Packaging Rules

### Include

- `Python/main.py`
- `Python/Config.py`
- `Python/Config.yaml`
- `Python/controller/`
- `Python/control_platform/Physical.py`
- `Python/control_platform/QubeInterface.py`
- `Python/tiva_microcontroller/UART.py`
- any Quanser runtime libraries required by the SDK on Windows

### Exclude from the release build

- `Python/control_platform/Virtual.py`
- `Virtual_model/`
- `Python/interface/`
- `Python/data/Plot.py`
- MuJoCo viewer assets

## Validation Checklist

After building the executable, validate these in order:

1. Launch the binary on Windows with the Quanser hardware attached.
2. Confirm `Config.yaml` is read correctly and matches the current physical settings.
3. Verify the UART thread starts and can receive commands.
4. Confirm the control loop runs and the motor enable path works.
5. Confirm shutdown is clean and the motor output is zeroed.
6. Measure startup time and control-loop rate against the Python version.

## Known Caveats

- Nuitka will not improve the Quanser SDK itself; hardware calls remain the dominant cost.
- If `Config.yaml` or the working directory is not packaged correctly, the binary will fail at startup because `Config.py` reads the config from disk.
- If any code path imports `Virtual.py` indirectly, the build may start pulling in MuJoCo again. Keep release imports direct and physical-only.
- If you later re-enable GUI or logging, that should be a separate build profile so the release binary stays small and stable.

## Practical Recommendation

For this project, maintain two build profiles:

- **Physical Windows release**: current `Config.yaml`, no simulation, no GUI, no plotting
- **Optional simulation build**: separate artifact for development only

That split keeps the release binary smaller, reduces dependency risk, and makes the control PC easier to deploy.