"""
Design.py — Controller gain design for the QUBE-Servo 3 Inverted Pendulum
==========================================================================
Computes the LQR gain matrix K (1×4) for the linearised system:

    ẋ = A·x + B·u       x = [θ, θ̇, δα, δ̇α]   u = V
    V = -K · x_err      x_err = [θ−θ_ref, θ̇, α−π, α̇]

Requires scipy (pip install scipy).
Falls back to hand-tuned gains if scipy is unavailable.
"""

import numpy as np
import controller.Dynamics as dyn

# ── Default LQR weights ───────────────────────────────────────────────────────
#   Q penalises state deviation, R penalises control effort.
#   Increase Q[2,2] to make the pendulum angle tighter.
#   Increase R to use less voltage (smoother, but slower response).
DEFAULT_Q = np.diag([0.1, 0.0, 10.0, 0.0])  # [θ, θ̇, δα, δ̇α]
DEFAULT_R = np.array([[1.0]])

# ── Fallback gains (approximate LQR solution, hand-tuned) ────────────────────
# V = -K · [θ−θ_ref, θ̇, α−π, α̇]
FALLBACK_K = np.array([[-1.0, -0.5, 25.0, 2.5]])


def lqr(Q: np.ndarray = DEFAULT_Q,
        R: np.ndarray = DEFAULT_R) -> np.ndarray:
    """
    Solve the continuous-time LQR problem for the linearised pendulum system.

    min  ∫ (x'Qx + u'Ru) dt
    s.t. ẋ = Ax + Bu

    Solves the algebraic Riccati equation:
        A'P + PA − PBR⁻¹B'P + Q = 0

    Parameters
    ----------
    Q : ndarray (4, 4)   state cost matrix  (default: diagonal, pendulum-angle heavy)
    R : ndarray (1, 1)   input cost matrix  (default: 1.0)

    Returns
    -------
    K : ndarray (1, 4)   gain matrix  →  V = -K · [θ−θ_ref, θ̇, α−π, α̇]
    """
    try:
        from scipy.linalg import solve_continuous_are
    except ImportError:
        print("[Design] scipy not found — using fallback gains. "
              "Install with: pip install scipy")
        return FALLBACK_K.copy()

    A, B = dyn.linearize()

    try:
        P = solve_continuous_are(A, B, Q, R)
        K = np.linalg.solve(R, B.T @ P)   # K = R⁻¹ B' P
        return K                            # shape (1, 4)
    except Exception as e:
        print(f"[Design] Riccati solver failed ({e}) — using fallback gains.")
        return FALLBACK_K.copy()


def print_system_info() -> None:
    """Print linearised A, B matrices and resulting LQR gains."""
    A, B = dyn.linearize()
    K = lqr()
    print("── Linearised system (about α = π upright) ──────────────")
    print(f"A =\n{A}")
    print(f"B =\n{B}")
    print(f"\n── LQR gain K = {K}")
    print(f"   V = -K·[θ−θ_ref, θ̇, α−π, α̇]")
    print(f"   K[θ]={K[0,0]:.3f}  K[θ̇]={K[0,1]:.3f}  "
          f"K[δα]={K[0,2]:.3f}  K[δ̇α]={K[0,3]:.3f}")
