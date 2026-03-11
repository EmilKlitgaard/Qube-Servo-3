"""
Controller.py — Shared control loop for the QUBE-Servo 3 Inverted Pendulum
===========================================================================
PendulumController is the single place where sensor data is turned into
a motor voltage.  It is platform-agnostic: the same instance is used
whether the qube is a Physical or Virtual device.

Usage
-----
    from controller.Controller import PendulumController

    ctrl = PendulumController()
    with qube:
        qube.reset()
        qube.enable(True)
        while running:
            state = qube.read()          # (θ, θ̇, α, α̇)
            voltage = ctrl.step(*state)
            qube.write(voltage)
"""

import math
import numpy as np
import controller.Dynamics as dyn
import controller.Design   as design


class PendulumController:
    """
    LQR state-feedback controller for the rotary inverted pendulum.

    State error:  e = [θ − θ_ref,  θ̇,  α − π,  α̇]
    Control law:  V = −K · e          (K is a 1×4 row vector)

    Parameters
    ----------
    K : array-like (1×4) or None
        Gain vector.  If None, LQR gains are computed automatically
        from Dynamics.linearize() using Design.lqr().
    theta_ref : float
        Arm angle setpoint [rad].  Default: π (180°, arm home position).
        Only meaningful when the arm position is included in the cost (K[0] ≠ 0).
    voltage_limit : float
        Symmetric saturation limit [V].  Default: 18 V (amplifier rail).
    """

    def __init__(self,
                 K:             np.ndarray | None = None,
                 theta_ref:     float             = dyn.THETA_INIT,
                 voltage_limit: float             = dyn.VOLTAGE_MAX):

        if K is None:
            self._K = design.lqr()           # shape (1, 4)
        else:
            self._K = np.atleast_2d(np.asarray(K, dtype=float))

        self._theta_ref     = theta_ref
        self._voltage_limit = abs(voltage_limit)

        print(f"[Controller] K = {self._K}")
        print(f"[Controller] θ_ref = {math.degrees(self._theta_ref):.1f}°, "
              f"V_limit = ±{self._voltage_limit} V")

    # ── main interface ─────────────────────────────────────────────────────────

    def step(self,
             theta:     float,
             theta_dot: float,
             alpha:     float,
             alpha_dot: float) -> float:
        """
        Compute the motor voltage for the current state.

        Parameters
        ----------
        theta     : float   Arm angle [rad]
        theta_dot : float   Arm angular velocity [rad/s]
        alpha     : float   Pendulum angle [rad]  (0 = down, π = upright)
        alpha_dot : float   Pendulum angular velocity [rad/s]

        Returns
        -------
        voltage : float   Motor voltage [V], saturated to ±voltage_limit
        """
        error = np.array([
            theta     - self._theta_ref,   # arm deviation from home
            theta_dot,
            alpha     - math.pi,           # pendulum deviation from upright
            alpha_dot,
        ])

        # V = -K · e   (self._K is (1,4), error is (4,) → result is (1,))
        voltage = (-(self._K @ error)).item()
        return max(-self._voltage_limit, min(self._voltage_limit, voltage))

    # ── convenience ───────────────────────────────────────────────────────────

    def set_theta_ref(self, theta_ref: float) -> None:
        """Change the arm angle setpoint at runtime."""
        self._theta_ref = theta_ref

    @property
    def K(self) -> np.ndarray:
        """The current gain vector (1×4)."""
        return self._K.copy()
