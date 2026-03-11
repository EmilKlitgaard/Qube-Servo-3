"""
Dynamics.py — QUBE-Servo 3 Rotary Inverted Pendulum
=====================================================
Single source of truth for all physical parameters.
Used by both Virtual.py (simulation) and the controller.

State vector  x = [θ,  θ̇,  δα,  δ̇α]
  θ   – arm angle [rad]
  δα  – pendulum deviation from upright: δα = α − π
        (so δα = 0 is perfectly balanced)

Input u = V  (motor voltage [V])
"""

import math
import numpy as np

# ── Motor / Electrical ────────────────────────────────────────────────────────
Rm = 8.4        # Ω      terminal resistance
Km = 0.042      # V·s    back-EMF constant
Kt = 0.042      # Nm/A   torque constant  (Km = Kt in SI)

# ── Rotary arm ────────────────────────────────────────────────────────────────
Lr = 0.085      # m      arm length (pivot to pivot)
Mr = 0.095      # kg     arm mass
Jm = 4.0e-6     # kg·m²  motor rotor inertia
Ja = Jm + Mr * Lr**2 / 3.0   # kg·m²  arm + rotor about motor axis

# ── Pendulum ──────────────────────────────────────────────────────────────────
Lp = 0.129      # m      full rod length
lp = Lp / 2.0  # m      pivot → CoM
Mp = 0.024      # kg
Jp = Mp * Lp**2 / 3.0   # kg·m²  about pivot (thin rod, end)

# ── Damping (nominally zero) ──────────────────────────────────────────────────
Br = 0.0        # Nm·s   arm viscous damping
Bp = 0.0        # Nm·s   pendulum viscous damping

# ── Gravity ───────────────────────────────────────────────────────────────────
g = 9.81        # m/s²

# ── Arm travel limits ─────────────────────────────────────────────────────────
THETA_INIT = math.pi              # 180° — arm home position (facing −X)
THETA_MIN  = math.pi / 2.0        #  90° — left  hard stop
THETA_MAX  = 3.0 * math.pi / 2.0  # 270° — right hard stop
VOLTAGE_MAX = 18.0                # V — amplifier rail


def linearize() -> tuple[np.ndarray, np.ndarray]:
    """
    Linearize the equations of motion about the upright equilibrium
    (θ arbitrary, θ̇=0, α=π, α̇=0, V=0).

    Evaluated mass matrix at α = π  (sin π = 0, cos π = −1):
        M11 = Ja + Mp·Lr²
        M12 = Mp·Lr·lp·cos(π) = −Mp·Lr·lp    → nM12 = −M12 = Mp·Lr·lp
        M22 = Jp
        det = M11·M22 − M12²

    Linearised RHS at α = π + δα (first order):
        F1 ≈ (Kt/Rm)·V  −  Dr·θ̇                  Dr = Kt·Km/Rm + Br
        F2 ≈  Mp·g·lp·δα  −  Bp·δ̇α               (sin(π+δα) ≈ −δα)

    Equations of motion:
        θ̈  = ( M22·F1 + nM12·F2 ) / det
        δ̈α = ( nM12·F1 +  M11·F2 ) / det

    State x = [θ, θ̇, δα, δ̇α],  input u = V.

    Returns
    -------
    A : ndarray (4, 4)   state matrix
    B : ndarray (4, 1)   input matrix
    """
    M11  = Ja + Mp * Lr**2
    nM12 = Mp * Lr * lp          # −M12, positive value
    M22  = Jp
    det  = M11 * M22 - nM12**2   # M12² = nM12²

    Dr   = Kt * Km / Rm + Br     # effective arm damping (back-EMF + viscous)

    A = np.array([
        [0,               1,                      0,               0            ],
        [0, -M22  * Dr / det,   nM12 * Mp*g*lp / det,  -nM12 * Bp / det],
        [0,               0,                      0,               1            ],
        [0,  nM12 * Dr / det,    M11 * Mp*g*lp / det,   -M11 * Bp / det],
    ], dtype=float)

    B = np.array([
        [0                      ],
        [M22  * Kt / (Rm * det) ],
        [0                      ],
        [nM12 * Kt / (Rm * det) ],
    ], dtype=float)

    return A, B