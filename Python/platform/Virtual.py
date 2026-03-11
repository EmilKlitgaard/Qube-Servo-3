import math
import os
import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .QubeInterface import QubeInterface

# ── Published QUBE-Servo 3 parameters (Quanser Student Workbook) ─────────────
#
#   Motor / Electrical
#     Rm  = 8.4      Ω           Motor terminal resistance
#     Km  = 0.042    V·s/rad     Back-EMF constant
#     Kt  = 0.042    Nm/A        Motor torque constant  (Km = Kt in SI)
#
#   Rotary arm
#     Lr  = 0.085    m           Arm length (pivot to pivot)
#     Mr  = 0.095    kg          Arm mass
#     Ja  = Jm + Mr·Lr²/3        Total arm+rotor inertia about motor axis
#
#   Pendulum
#     Lp   = 0.129   m           Full rod length
#     lp   = Lp/2    m           Distance from pivot to CoM
#     Mp   = 0.024   kg
#     Jp   = Mp·Lp²/3            Pendulum inertia about pivot (thin rod)
#
#   Damping (nominally zero in workbook)
#     Br  = 0.0    Nm·s/rad      Arm viscous damping
#     Bp  = 0.0    Nm·s/rad      Pendulum viscous damping
#
#   Gravity
#     g   = 9.81   m/s²

_Rm = 8.4
_Km = 0.042
_Kt = 0.042
_g  = 9.81

_Lr = 0.085
_Mr = 0.095
_Jm = 4.0e-6
_Ja = _Jm + _Mr * _Lr**2 / 3.0      # arm + rotor about motor axis

_Lp = 0.129
_lp = _Lp / 2.0
_Mp = 0.024
_Jp = _Mp * _Lp**2 / 3.0            # pendulum about pivot (thin rod, end)

_Br = 0.0
_Bp = 0.0

# ── Arm travel limits ────────────────────────────────────────────────────────
# Physical stop at ±90° from the centre (180°): cable/stop prevents full rotation.
_THETA_INIT = math.pi           # 180° — arm home position
_THETA_MIN  = math.pi / 2.0     #  90° — left  hard stop
_THETA_MAX  = 3.0 * math.pi / 2.0  # 270° — right hard stop


# ── Virtual implementation ────────────────────────────────────────────────────

class Virtual(QubeInterface):
    """
    QUBE-Servo 3 Rotary Inverted Pendulum — full nonlinear 2-DOF simulator.

    State:
        θ  (theta)  – arm angle [rad], driven by motor
        α  (alpha)  – pendulum angle [rad], 0 = hanging down, π = upright

    Physics precision and wall-clock speed are fully decoupled:

        ctrl_freq  – rate at which read() is called [Hz]             (default 500)
        substeps   – RK4 steps per control step                      (default 40)
                     → effective physics dt = 1 / (ctrl_freq × substeps)
                     → 500 Hz × 40 = 20 000 Hz internal integration rate
        viz_rate   – visualisation refresh rate [Hz], wall-clock     (default 60)
        speed      – wall-clock speed factor
                     1.0 = real time, 0.1 = 10× slower (good for watching)

    read() returns (theta, theta_dot, alpha, alpha_dot).
    """

    def __init__(self,
                 ctrl_freq: float = 500.0,
                 substeps:  int   = 40,
                 viz_rate:  float = 60.0,
                 speed:     float = 1.0):

        self._ctrl_freq    = ctrl_freq
        self._ctrl_dt      = 1.0 / ctrl_freq
        self._substeps     = max(1, substeps)
        self._phys_dt      = self._ctrl_dt / self._substeps
        self._speed        = max(speed, 1e-3)
        self._viz_interval = 1.0 / max(viz_rate, 1.0)
        self._last_viz_t   = 0.0

        # ── Physics state ─────────────────────────────────────────────────────
        self._theta     = _THETA_INIT  # arm starts at 180°
        self._theta_dot = 0.0
        self._alpha     = 0.0   # pendulum angle [rad], 0 = hanging down
        self._alpha_dot = 0.0
        self._voltage   = 0.0
        self._enabled   = False

        # ── Circular history buffers (5 s at ctrl_freq) ───────────────────────
        self._hist_len = int(ctrl_freq * 5)
        self._hist_t   = np.zeros(self._hist_len)
        self._hist_th  = np.zeros(self._hist_len)
        self._hist_al  = np.zeros(self._hist_len)
        self._hist_v   = np.zeros(self._hist_len)
        self._step     = 0

        # ── Matplotlib handles (created in open()) ────────────────────────────
        self._fig            = None
        self._ax_top         = None   # bird's-eye view  (shows θ)
        self._ax_side        = None   # end-on view      (shows α)
        self._ax_plot        = None   # time series
        self._arm_line       = None
        self._pend_line      = None
        self._pend_tip       = None
        self._th_line        = None
        self._al_line        = None
        self._v_line         = None
        self._led_patch      = None
        self._alpha_text     = None
        self._theta_text     = None

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def open(self) -> None:
        plt.ion()
        self._fig = plt.figure(figsize=(14, 5))
        self._fig.suptitle("QUBE-Servo 3  —  Rotary Inverted Pendulum  (Virtual)",
                           fontsize=12, fontweight="bold")
        # Three panels
        self._ax_top  = self._fig.add_subplot(1, 3, 1)
        self._ax_side = self._fig.add_subplot(1, 3, 2)
        self._ax_plot = self._fig.add_subplot(1, 3, 3)
        self._setup_top_view()
        self._setup_side_view()
        self._setup_plot_view()
        self._fig.tight_layout(rect=[0, 0, 1, 0.94])
        self._fig.canvas.flush_events()
        print(
            f"[Virtual] Opened  (ctrl {self._ctrl_freq:.0f} Hz × {self._substeps} "
            f"RK4 substeps = {self._ctrl_freq * self._substeps:.0f} Hz physics, "
            f"speed={self._speed}×)"
        )

    def close(self) -> None:
        self.write(0.0)
        self.enable(False)
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
        print("[Virtual] Closed.")

    # ── helpers ────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        self._theta     = _THETA_INIT  # 180° — arm home
        self._theta_dot = 0.0
        self._alpha     = 0.0
        self._alpha_dot = 0.0
        self._voltage   = 0.0
        self._step      = 0
        self._hist_t[:]  = 0.0
        self._hist_th[:] = 0.0
        self._hist_al[:] = 0.0
        self._hist_v[:]  = 0.0

    def set_led(self, r: float, g: float, b: float) -> None:
        if self._led_patch is not None:
            self._led_patch.set_facecolor((
                max(0.0, min(1.0, r)),
                max(0.0, min(1.0, g)),
                max(0.0, min(1.0, b)),
            ))

    def enable(self, on: bool) -> None:
        self._enabled = on
        if not on:
            self._voltage = 0.0
        self.set_led(0.0, 1.0 if on else 0.0, 0.0)

    # ── control loop ───────────────────────────────────────────────────────────

    def read(self) -> tuple[float, float, float, float]:
        """
        Advance the simulation by one control step and return the full state.

        Returns
        -------
        theta     : float   Arm angle                      [rad]
        theta_dot : float   Arm angular velocity           [rad/s]
        alpha     : float   Pendulum angle (0=down, π=up)  [rad]
        alpha_dot : float   Pendulum angular velocity      [rad/s]
        """
        # ── Physics (RK4, many substeps) ──────────────────────────────────────
        if self._enabled:
            for _ in range(self._substeps):
                self._rk4_step(self._phys_dt)

        # ── History ───────────────────────────────────────────────────────────
        idx = self._step % self._hist_len
        self._hist_t[idx]  = self._step * self._ctrl_dt
        self._hist_th[idx] = self._theta
        self._hist_al[idx] = self._alpha
        self._hist_v[idx]  = self._voltage
        self._step += 1

        # ── Pace to wall-clock speed ──────────────────────────────────────────
        time.sleep(self._ctrl_dt / self._speed)

        # ── Visualisation at viz_rate Hz (wall-clock driven) ──────────────────
        now = time.monotonic()
        if now - self._last_viz_t >= self._viz_interval:
            self._update_viz()
            self._last_viz_t = now

        return self._theta, self._theta_dot, self._alpha, self._alpha_dot

    def write(self, voltage: float) -> None:
        self._voltage = max(min(voltage, 18.0), -18.0)

    # ── physics ────────────────────────────────────────────────────────────────

    def _derivatives(self, th: float, thd: float,
                     al: float, ald: float) -> tuple[float, float, float, float]:
        """
        Full nonlinear EOM for the rotary pendulum (Lagrangian).

        pendulum_joint axis = arm-frame +X  (along the arm)
        Pendulum swings in the arm-YZ plane (perpendicular to arm, vertical).

        Variable mass matrix:
          M11 = Ja + Mp*Lr^2 + Mp*lp^2*sin^2(a)   <- angle-dependent!
          M12 = Mp*Lr*lp*cos(a)
          M22 = Jp   (about pivot)

        RHS  (correct signs: a=0 at bottom, a=pi upright):
          F1 = t - Br*td - Mp*lp^2*sin(2a)*ad*td + Mp*Lr*lp*sin(a)*ad^2
          F2 = -Mp*g*lp*sin(a) - Bp*ad + 0.5*Mp*lp^2*sin(2a)*td^2
        """
        tau = (_Kt / _Rm) * (self._voltage - _Km * thd)

        sa  = math.sin(al)
        ca  = math.cos(al)
        s2a = math.sin(2.0 * al)

        M11 = _Ja + _Mp * _Lr**2 + _Mp * _lp**2 * sa**2
        M12 = _Mp * _Lr * _lp * ca
        M22 = _Jp
        det = M11 * M22 - M12 * M12

        F1  = (tau
               - _Br * thd
               - _Mp * _lp**2 * s2a * ald * thd
               + _Mp * _Lr * _lp * sa * ald**2)
        F2  = (- _Mp * _g * _lp * sa
               - _Bp * ald
               + 0.5 * _Mp * _lp**2 * s2a * thd**2)

        thdd = ( M22 * F1 - M12 * F2) / det
        aldd = (-M12 * F1 + M11 * F2) / det

        return thd, thdd, ald, aldd

    def _rk4_step(self, dt: float) -> None:
        """Classic 4th-order Runge-Kutta step."""
        th, thd, al, ald = self._theta, self._theta_dot, self._alpha, self._alpha_dot

        k1 = self._derivatives(th,              thd,              al,              ald)
        k2 = self._derivatives(th + dt/2*k1[0], thd + dt/2*k1[1], al + dt/2*k1[2], ald + dt/2*k1[3])
        k3 = self._derivatives(th + dt/2*k2[0], thd + dt/2*k2[1], al + dt/2*k2[2], ald + dt/2*k2[3])
        k4 = self._derivatives(th + dt  *k3[0], thd + dt  *k3[1], al + dt  *k3[2], ald + dt  *k3[3])

        self._theta     += dt / 6 * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
        self._theta_dot += dt / 6 * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
        self._alpha     += dt / 6 * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
        self._alpha_dot += dt / 6 * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])

        # ── Hard stops for arm travel ─────────────────────────────────────────
        if self._theta < _THETA_MIN:
            self._theta     = _THETA_MIN
            self._theta_dot = max(0.0, self._theta_dot)  # only allow outward velocity
        elif self._theta > _THETA_MAX:
            self._theta     = _THETA_MAX
            self._theta_dot = min(0.0, self._theta_dot)  # only allow outward velocity

    # ── visualisation setup ────────────────────────────────────────────────────

    def _setup_top_view(self) -> None:
        """Bird's-eye (XY) view — shows the rotating arm angle θ."""
        ax = self._ax_top
        margin = (_Lr + _lp) * 1.25
        ax.set_aspect("equal")
        ax.set_xlim(-margin, margin)
        ax.set_ylim(-margin, margin)
        ax.set_title("Top view  (arm angle θ)", fontsize=9)
        ax.set_xlabel("x [m]", fontsize=8)
        ax.set_ylabel("y [m]", fontsize=8)
        ax.grid(True, alpha=0.25)
        ax.tick_params(labelsize=7)

        # Housing (square, 90 mm)
        hs = 0.045
        body = plt.Rectangle((-hs, -hs), 2*hs, 2*hs,
                              linewidth=1.5, edgecolor="dimgrey",
                              facecolor="#2e2e2e", zorder=1)
        ax.add_patch(body)

        # Motor shaft dot
        ax.plot(0, 0, "o", color="silver", markersize=5, zorder=3)

        # Allowed travel arc (90° – 270°, shaded)
        arc_angles = np.linspace(_THETA_MIN, _THETA_MAX, 120)
        arc_r = (_Lr + _lp) * 1.15
        ax.fill(
            np.append([0], arc_r * np.cos(arc_angles)),
            np.append([0], arc_r * np.sin(arc_angles)),
            color="#3a5a3a", alpha=0.12, zorder=0, label="allowed range"
        )
        # Hard-stop lines
        for ang in (_THETA_MIN, _THETA_MAX):
            ax.plot([0, arc_r * math.cos(ang)],
                    [0, arc_r * math.sin(ang)],
                    color="#cc4444", linewidth=1.2, linestyle="--", alpha=0.7, zorder=1)

        # LED indicator
        self._led_patch = plt.Circle((hs*0.75, hs*0.75), hs*0.12,
                                     facecolor="grey", edgecolor="black",
                                     linewidth=0.8, zorder=4)
        ax.add_patch(self._led_patch)

        # Arm line (updated live)
        self._arm_line, = ax.plot([0, _Lr], [0, 0],
                                  color="#e0a020", linewidth=3, solid_capstyle="round",
                                  zorder=2, label="arm")

        # Pendulum tip projected onto XY plane (circle)
        self._pend_tip, = ax.plot([_Lr], [0], "o",
                                  color="#5599ff", markersize=7, zorder=5,
                                  label="pendulum tip (proj.)")
        ax.legend(fontsize=7, loc="upper right")

        self._theta_text = ax.text(0.03, 0.97, "", transform=ax.transAxes,
                                   fontsize=8, va="top",
                                   bbox=dict(boxstyle="round,pad=0.2",
                                             facecolor="white", alpha=0.7))

    def _setup_side_view(self) -> None:
        """
        End-on view looking along the arm toward the pivot — shows pendulum
        angle α in the vertical plane through the arm.
        """
        ax = self._ax_side
        margin = _lp * 1.5
        ax.set_aspect("equal")
        ax.set_xlim(-margin, margin)
        ax.set_ylim(-_lp * 1.6, _lp * 1.1)
        ax.set_title("Side view  (pendulum angle α)", fontsize=9)
        ax.set_xlabel("← ⊥ arm  (arm-Y dir)  [m] →", fontsize=8)
        ax.set_ylabel("vertical  Z  [m]", fontsize=8)
        ax.grid(True, alpha=0.25)
        ax.tick_params(labelsize=7)

        # Pivot point marker
        ax.plot(0, 0, "s", color="#e0a020", markersize=8, zorder=3,
                label="pivot (arm tip)")

        # Downward reference (al=0, stable)
        ax.plot([0, 0], [0, -_lp], color="grey", linewidth=0.8,
                linestyle="--", alpha=0.6)
        ax.text(0.003, -_lp * 0.5, "\u03b1=0\n(down)", fontsize=7,
                color="grey", va="center")

        # Upward reference (al=pi, unstable)
        ax.plot([0, 0], [0, +_lp], color="green", linewidth=0.8,
                linestyle=":", alpha=0.7)
        ax.text(0.003, _lp * 0.65, "\u03b1=\u03c0\n(up)", fontsize=7,
                color="green", va="center")

        # Pendulum rod (updated live)
        # α=0  → tip at (0, -lp)
        # α=π  → tip at (0, +lp)
        # In this view: x = lp·sin(α), z = -lp·cos(α)
        self._pend_line, = ax.plot([0, 0], [0, -_lp],
                                   color="#5599ff", linewidth=4,
                                   solid_capstyle="round", zorder=4,
                                   label="pendulum")
        ax.legend(fontsize=7, loc="upper right")

        self._alpha_text = ax.text(0.03, 0.97, "", transform=ax.transAxes,
                                   fontsize=8, va="top",
                                   bbox=dict(boxstyle="round,pad=0.2",
                                             facecolor="white", alpha=0.7))

    def _setup_plot_view(self) -> None:
        ax = self._ax_plot
        ax.set_title("State history  (5 s rolling window)", fontsize=9)
        ax.set_xlabel("time [s]", fontsize=8)
        ax.grid(True, alpha=0.25)
        ax.tick_params(labelsize=7)
        ax.set_xlim(0.0, 5.0)
        ax.set_ylim(-20.0, 20.0)
        self._th_line, = ax.plot([], [], color="steelblue",  linewidth=1.2,
                                 label="θ [rad]")
        self._al_line, = ax.plot([], [], color="#e07020",    linewidth=1.2,
                                 label="α [rad]")
        self._v_line,  = ax.plot([], [], color="tomato",     linewidth=0.9,
                                 linestyle="--", label="V [V]")
        ax.legend(fontsize=7, loc="upper right")

    # ── visualisation update ───────────────────────────────────────────────────

    def _update_viz(self) -> None:
        if self._fig is None:
            return

        th = self._theta
        al = self._alpha

        # ── Top view: arm + projected pendulum tip ────────────────────────────
        tip_x = _Lr * math.cos(th)
        tip_y = _Lr * math.sin(th)
        self._arm_line.set_data([0, tip_x], [0, tip_y])

        # Joint axis = arm-X  => pendulum swings in arm-YZ plane.
        # arm-Y direction in world = (-sin(th), cos(th), 0)  [90 deg CCW from arm]
        # XY projection of tip relative to pivot: lp*sin(al) * arm-Y_world
        pend_proj_x = tip_x - _lp * math.sin(al) * math.sin(th)   # -sin(th)
        pend_proj_y = tip_y + _lp * math.sin(al) * math.cos(th)   # +cos(th)
        self._pend_tip.set_data([pend_proj_x], [pend_proj_y])

        deg_th = math.degrees(th) % 360
        self._theta_text.set_text(f"θ = {deg_th:6.1f}°\n   {th:+.3f} rad")

        # ── Side view: pendulum rod in arm-YZ plane ───────────────────────────
        # View direction: looking from arm tip toward motor (along -arm-X).
        # Plot-x = arm-Y (right = +arm-Y), Plot-y = world-Z (up = +Z).
        # Rotating rest tip (0,0,-Lp) about arm-X by al (RH rule):
        #   arm-Y:  +lp*sin(al)     arm-Z: -lp*cos(al)
        # al=0   => (0,  -lp)  => hanging straight down  ✓
        # al=pi  => (0,  +lp)  => straight up             ✓
        # al=pi/2=> (+lp, 0)   => horizontal to the right ✓
        px = +_lp * math.sin(al)
        pz = -_lp * math.cos(al)
        self._pend_line.set_data([0, px], [0, pz])

        deg_al = math.degrees(al) % 360
        upright_err = math.degrees(abs(math.pi - abs(al % (2 * math.pi) - math.pi)))
        self._alpha_text.set_text(
            f"α = {deg_al:6.1f}°\n   {al:+.3f} rad\n"
            f"Δ from up: {upright_err:.1f}°"
        )

        # ── Time series ───────────────────────────────────────────────────────
        n = min(self._step, self._hist_len)
        if n > 0:
            if self._step <= self._hist_len:
                ts  = self._hist_t[:n]
                ths = self._hist_th[:n]
                als = self._hist_al[:n]
                vs  = self._hist_v[:n]
            else:
                roll = self._step % self._hist_len
                ts   = np.roll(self._hist_t,  -roll)
                ths  = np.roll(self._hist_th, -roll)
                als  = np.roll(self._hist_al, -roll)
                vs   = np.roll(self._hist_v,  -roll)
                ts   = ts - ts[0]

            self._th_line.set_data(ts, ths)
            self._al_line.set_data(ts, als)
            self._v_line.set_data(ts, vs)
            t_end = float(ts[-1])
            self._ax_plot.set_xlim(max(0.0, t_end - 5.0), max(5.0, t_end))

        self._fig.canvas.flush_events()
        plt.pause(0.001)
