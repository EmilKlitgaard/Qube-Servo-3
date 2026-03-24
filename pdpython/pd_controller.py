from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

import numpy as np


@dataclass
class PDController:
	Rm: float = 7.5
	kt: float = 0.0422
	km: float = 0.0422
	Jm: float = 1.4e-6
	Jh: float = 0.6e-6
	mr: float = 0.095
	Lr: float = 0.085
	mp: float = 0.024
	Lp: float = 0.129
	g: float = 9.81

	k1: float = 60.0
	k2: float = 9.0
	k3: float = 9.0
	k4: float = 3.0

	voltage_limit: float = 10.0
	default_dt: float = 1.0 / 500.0

	_prev_theta: Optional[float] = field(default=None, init=False, repr=False)
	_prev_alpha: Optional[float] = field(default=None, init=False, repr=False)
	_prev_time: Optional[float] = field(default=None, init=False, repr=False)

	@property
	def Jr(self) -> float:
		return self.Jm + self.Jh

	@property
	def lp(self) -> float:
		return self.Lp / 2.0

	@property
	def Jp(self) -> float:
		return (1.0 / 3.0) * self.mp * self.Lp**2

	def reset(self) -> None:
		self._prev_theta = None
		self._prev_alpha = None
		self._prev_time = None

	@staticmethod
	def clamp(value: float, lo: float, hi: float) -> float:
		return max(min(value, hi), lo)

	def _estimate_rates(self, theta: float, alpha: float, dt: Optional[float]) -> Tuple[float, float, float]:
		if dt is None:
			if self._prev_time is None:
				dt_used = self.default_dt
			else:
				dt_used = max(time.perf_counter() - self._prev_time, 1e-6)
		else:
			dt_used = max(dt, 1e-6)

		if self._prev_theta is None or self._prev_alpha is None:
			theta_dot = 0.0
			alpha_dot = 0.0
		else:
			theta_dot = (theta - self._prev_theta) / dt_used
			alpha_dot = (alpha - self._prev_alpha) / dt_used

		self._prev_theta = theta
		self._prev_alpha = alpha
		self._prev_time = time.perf_counter()
		return theta_dot, alpha_dot, dt_used

	def compute_voltage(
		self,
		alpha: float,
		theta: float,
		*,
		dt: Optional[float] = None,
		alpha_dot: Optional[float] = None,
		theta_dot: Optional[float] = None,
	) -> float:
		if alpha_dot is None or theta_dot is None:
			theta_dot_est, alpha_dot_est, _ = self._estimate_rates(theta, alpha, dt)
			if theta_dot is None:
				theta_dot = theta_dot_est
			if alpha_dot is None:
				alpha_dot = alpha_dot_est

		alpha_tilde = alpha - math.pi
		v_unsat = -(
			self.k1 * alpha_tilde
			+ self.k2 * alpha_dot
			- self.k3 * theta
			- self.k4 * theta_dot
		)
		return self.clamp(v_unsat, -self.voltage_limit, self.voltage_limit)

	def motor_torque(self, voltage: float, theta_dot: float) -> float:
		return (self.kt / self.Rm) * (voltage - self.km * theta_dot)

	def dynamics(self, state: Sequence[float], voltage: float) -> np.ndarray:
		theta, alpha, theta_dot, alpha_dot = state
		tau = self.motor_torque(voltage, theta_dot)

		m11 = self.Jr + self.mp * self.Lr**2 + self.mp * self.lp**2 * math.sin(alpha) ** 2
		m12 = self.mp * self.Lr * self.lp * math.cos(alpha)
		m21 = m12
		m22 = self.Jp + self.mp * self.lp**2

		c1 = (
			2.0 * self.mp * self.lp**2 * math.sin(alpha) * math.cos(alpha) * theta_dot * alpha_dot
			- self.mp * self.Lr * self.lp * math.sin(alpha) * alpha_dot**2
		)
		c2 = -self.mp * self.lp**2 * math.sin(alpha) * math.cos(alpha) * theta_dot**2

		g1 = 0.0
		g2 = self.mp * self.g * self.lp * math.sin(alpha)

		mass_matrix = np.array([[m11, m12], [m21, m22]], dtype=float)
		rhs = np.array([tau - c1 - g1, -c2 - g2], dtype=float)
		qdd = np.linalg.solve(mass_matrix, rhs)

		return np.array([theta_dot, alpha_dot, qdd[0], qdd[1]], dtype=float)

	def closed_loop_dynamics(self, _t: float, state: Sequence[float]) -> np.ndarray:
		theta, alpha, theta_dot, alpha_dot = state
		voltage = self.compute_voltage(
			alpha=alpha,
			theta=theta,
			alpha_dot=alpha_dot,
			theta_dot=theta_dot,
		)
		return self.dynamics(state, voltage)

