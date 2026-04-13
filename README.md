# Quanser QUBE-Servo 3: Inverted Pendulum Control
<img src="Images/Qube_servo_3.png" width="100%">

## Overview
Real-time swing-up and stabilization control system for the Quanser QUBE-Servo 3 inverted pendulum. Combines embedded firmware (TM4C123 ARM Cortex-M4) with Python host control, supporting both physical hardware and MuJoCo simulation.

---

## Quick Start

### Installation
```bash
git clone <repo-url>
cd Qube-Servo-3/Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run
```bash
python main.py
```

Configure simulation vs. physical hardware in `Config.yaml`.

---

## Documentation
- **[Project Structure](Guides/PROJECT-STRUCTURE.md)** — System architecture and all modules
- **[Virtual Environment Setup](Guides/VIRTUAL-ENVIRONMENT.md)** — Python dependency management  
- **[Git Setup](Guides/GIT-SETUP.md)** — Version control workflow
- **[QUBE-Servo 3 Setup](Guides/QUBE-SERVO-3-SETUP.md)** — Hardware integration
- **[TO-DO List](Guides/TO-DO.md)** — Known issues and planned work

---

## References
- Quanser QUBE-Servo 3: https://www.quanser.com/products/qube-servo-3
- Quanser Resources: https://github.com/quanser/Quanser_Academic_Resources
- MuJoCo: https://mujoco.org/
