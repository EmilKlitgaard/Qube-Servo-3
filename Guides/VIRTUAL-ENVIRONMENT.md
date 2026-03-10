# Virtual Environment Setup Guide

## 1. Create the virtual environment

Run once from the **repo root**:

```bash
python3 -m venv venv
```

This creates `Qube-Servo-3/venv/`.

---

## 2. Activate the virtual environment

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

## 3. Install dependencies

With the venv active, install all packages from `requirements.txt`:

```bash
pip install -r Python/requirements.txt
```

> **Note:** The `quanser` package must be installed separately via the
> [Quanser Python SDK / QUARC installer](https://www.quanser.com) — it is
> not available on PyPI and is therefore excluded from `requirements.txt`.

---

## 4. Run the project

```bash
cd Python
python main.py
```

---

## 5. Save / update requirements

After installing or upgrading any package, update `requirements.txt` with:

```bash
pip freeze > Python/requirements.txt
```

> Re-open `Python/requirements.txt` afterwards and remove the `quanser`
> line if it was captured, to keep it out of the file.

---

## 6. Deactivate the virtual environment

```bash
deactivate
```

Your prompt returns to normal.