import math
import os
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .QubeInterface import QubeInterface


# ── Published QUBE-Servo 3 parameters (Quanser Student Workbook) ─────────────
#
#   Electrical
#     Rm  = 8.4     Ω           Motor terminal resistance
#     Km  = 0.042   V·s/rad     Back-EMF constant
#     Kt  = 0.042   Nm/A        Motor torque constant
#
#   Mechanical
#     Jm  = 4.0e-6  kg·m²       Motor rotor moment of inertia
#     Jd  = 6.4e-6  kg·m²       Aluminium disc moment of inertia
#     Jeq = Jm + Jd = 10.4e-6   Total (Kg = 1, direct drive)
#     Beq = 0.0     Nm·s/rad    Viscous damping (nominally zero)

_Rm  = 8.4
_Km  = 0.042
_Kt  = 0.042
_Jeq = 10.4e-6
_Beq = 0.0

_URDF_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Virtual_model", "Qube_Servo_3.urdf")
)


# ── URDF helpers ──────────────────────────────────────────────────────────────

def _parse_disc_radius(urdf_path: str) -> float:
    """Read the rotor cylinder radius from the URDF.  Falls back to the
    datasheet-derived value if the file is missing or malformed."""
    try:
        root = ET.parse(urdf_path).getroot()
        for link in root.findall("link"):
            if link.get("name") == "rotor":
                cyl = link.find(".//visual/geometry/cylinder")
                if cyl is not None:
                    return float(cyl.get("radius"))
    except Exception:
        pass
    return 0.01554   # fallback: sqrt(2*Jd/m_disc)


# ── Virtual implementation ────────────────────────────────────────────────────

class Virtual(QubeInterface):
    """
    QUBE-Servo 3 simulator.

    Integrates the DC-motor ODE using forward Euler at *freq* Hz and renders
    the rotating disc plus a live state trace in a matplotlib window.

    The URDF (Virtual_model/Qube_Servo_3.urdf) is parsed at construction
    to obtain the disc radius used for visualisation.

    Parameters
    ----------
    freq     : Simulation / control-loop frequency [Hz].
    viz_rate : How often the visualisation refreshes [Hz].  Must be ≤ freq.
    """

    def __init__(self, freq: float = 100.0, viz_rate: float = 30.0):
        self._Ts    = 1.0 / freq
        self._N_viz = max(1, int(freq / viz_rate))

        # Physics state
        self._theta     = 0.0
        self._theta_dot = 0.0
        self._voltage   = 0.0
        self._enabled   = False

        # Circular history buffers (5-second window)
        self._hist_len = int(freq * 5)
        self._hist_t   = np.zeros(self._hist_len)
        self._hist_th  = np.zeros(self._hist_len)
        self._hist_v   = np.zeros(self._hist_len)
        self._step     = 0
        self._viz_step = 0

        # Geometry from URDF
        self._disc_r = _parse_disc_radius(_URDF_PATH)

        # Matplotlib handles (created in open())
        self._fig       = None
        self._ax_disc   = None
        self._ax_plot   = None
        self._marker    = None
        self._th_line   = None
        self._v_line    = None
        self._led_patch = None

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def open(self) -> None:
        plt.ion()
        self._fig, (self._ax_disc, self._ax_plot) = plt.subplots(
            1, 2, figsize=(11, 4.5)
        )
        self._fig.suptitle("QUBE-Servo 3  —  Virtual Simulation", fontsize=12)
        self._setup_disc_view()
        self._setup_plot_view()
        self._fig.tight_layout(rect=[0, 0, 1, 0.94])
        self._fig.canvas.flush_events()
        print(f"[Virtual] Simulation window opened  (disc r = {self._disc_r*1000:.1f} mm, URDF: {_URDF_PATH})")

    def close(self) -> None:
        self.write(0.0)
        self.enable(False)
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
        print("[Virtual] Simulation closed.")

    # ── initialisation helpers ─────────────────────────────────────────────────

    def reset(self) -> None:
        self._theta     = 0.0
        self._theta_dot = 0.0
        self._voltage   = 0.0
        self._step      = 0
        self._hist_t[:] = 0.0
        self._hist_th[:] = 0.0
        self._hist_v[:] = 0.0

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

    # ── control loop ──────────────────────────────────────────────────────────

    def read(self) -> tuple[float, float]:
        if self._enabled:
            self._step_physics()

        # Store into circular buffer
        idx = self._step % self._hist_len
        self._hist_t[idx]  = self._step * self._Ts
        self._hist_th[idx] = self._theta
        self._hist_v[idx]  = self._voltage
        self._step += 1

        # Refresh visualisation at viz_rate
        self._viz_step += 1
        if self._viz_step % self._N_viz == 0:
            self._update_viz()

        return self._theta, self._theta_dot

    def write(self, voltage: float) -> None:
        self._voltage = max(min(voltage, 18.0), -18.0)

    # ── private ───────────────────────────────────────────────────────────────

    def _step_physics(self) -> None:
        """
        Forward Euler integration of the motor ODE:

            Jeq · θ̈  =  (Kt/Rm)·(V − Km·θ̇)  −  Beq·θ̇
        """
        angular_acc = (
            (_Kt * self._voltage - _Kt * _Km * self._theta_dot) / (_Rm * _Jeq)
            - _Beq * self._theta_dot / _Jeq
        )
        self._theta_dot += self._Ts * angular_acc
        self._theta     += self._Ts * self._theta_dot

    def _setup_disc_view(self) -> None:
        ax = self._ax_disc
        margin = self._disc_r * 4.0
        ax.set_aspect("equal")
        ax.set_xlim(-margin, margin)
        ax.set_ylim(-margin, margin)
        ax.set_title("Disc — top view")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.grid(True, alpha=0.3)

        # Housing outline
        body_half = 0.05
        body = plt.Rectangle(
            (-body_half, -body_half), body_half * 2, body_half * 2,
            linewidth=1.5, edgecolor="dimgrey", facecolor="whitesmoke", zorder=1,
        )
        ax.add_patch(body)

        # Spinning disc
        disc = plt.Circle((0, 0), self._disc_r, color="silver", zorder=2)
        ax.add_patch(disc)

        # Orientation marker (radial line on the disc face)
        self._marker, = ax.plot(
            [0, self._disc_r], [0, 0], color="crimson", linewidth=2.5, zorder=3
        )

        # LED indicator (top-right corner of body)
        led_x = body_half * 0.8
        led_y = body_half * 0.8
        self._led_patch = plt.Circle(
            (led_x, led_y), body_half * 0.10, facecolor="grey",
            edgecolor="black", linewidth=0.8, zorder=4,
        )
        ax.add_patch(self._led_patch)

        # Annotations
        ax.annotate(
            "LED", xy=(led_x, led_y), xytext=(led_x + 0.005, led_y + 0.005),
            fontsize=6, color="dimgrey",
        )

    def _setup_plot_view(self) -> None:
        ax = self._ax_plot
        ax.set_title("State history  (rolling 5 s window)")
        ax.set_xlabel("time [s]")
        ax.set_ylabel("θ [rad]  /  V [V]")
        ax.set_xlim(0.0, 5.0)
        ax.set_ylim(-15.0, 15.0)
        ax.grid(True, alpha=0.3)
        self._th_line, = ax.plot([], [], color="steelblue", linewidth=1.2,
                                 label="θ  [rad]")
        self._v_line,  = ax.plot([], [], color="tomato",    linewidth=1.0,
                                 linestyle="--", label="V  [V]")
        ax.legend(loc="upper right", fontsize=8)

    def _update_viz(self) -> None:
        if self._fig is None:
            return

        # ── Disc marker ───────────────────────────────────────────────────────
        a = self._theta
        self._marker.set_data(
            [0.0, self._disc_r * math.cos(a)],
            [0.0, self._disc_r * math.sin(a)],
        )

        # ── Time-series (chronological order from circular buffer) ─────────────
        n = min(self._step, self._hist_len)
        if self._step <= self._hist_len:
            ts  = self._hist_t[:n]
            ths = self._hist_th[:n]
            vs  = self._hist_v[:n]
        else:
            roll = self._step % self._hist_len
            ts  = np.roll(self._hist_t,  -roll)
            ths = np.roll(self._hist_th, -roll)
            vs  = np.roll(self._hist_v,  -roll)
            ts  = ts - ts[0]   # re-anchor time axis to 0

        if n > 0:
            self._th_line.set_data(ts, ths)
            self._v_line.set_data(ts, vs)
            t_end = float(ts[-1])
            self._ax_plot.set_xlim(max(0.0, t_end - 5.0), max(5.0, t_end))

        self._fig.canvas.flush_events()
        plt.pause(0.001)
