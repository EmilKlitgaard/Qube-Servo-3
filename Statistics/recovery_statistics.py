from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats


BASE_DIR = Path(__file__).resolve().parent.parent
SIMULATION_CSV = BASE_DIR / "logs" / "pendulum_recovery_times.csv"
REAL_CSV = BASE_DIR / "logs" / "recovery_times.csv"


def _is_float(value: str) -> bool:
	try:
		float(value)
	except (TypeError, ValueError):
		return False
	return True


def _row_looks_like_data(row: list[str]) -> bool:
	return len(row) >= 2 and _is_float(row[0]) and _is_float(row[-1])


def load_recovery_times(path: Path) -> np.ndarray:
	with path.open(newline="", encoding="utf-8-sig") as file:
		rows = [row for row in csv.reader(file) if row]

	if not rows:
		raise ValueError(f"No data found in {path}")

	if _row_looks_like_data(rows[0]):
		data_rows = rows
		time_index = len(rows[0]) - 1
	else:
		header = [column.strip() for column in rows[0]]
		data_rows = rows[1:]

		if "recovery_time_s" in header:
			time_index = header.index("recovery_time_s")
		elif "recovery_time" in header:
			time_index = header.index("recovery_time")
		else:
			time_index = len(header) - 1

	values: list[float] = []
	for row in data_rows:
		if len(row) <= time_index:
			continue

		try:
			value = float(row[time_index])
		except ValueError:
			continue

		if math.isfinite(value):
			values.append(value)

	if not values:
		raise ValueError(f"No numeric recovery times found in {path}")

	return np.asarray(values, dtype=float)


def summarize(values: np.ndarray) -> dict[str, float]:
	if values.size == 0:
		raise ValueError("Cannot summarize an empty dataset")

	mean = float(np.mean(values))
	std = float(np.std(values, ddof=1)) if values.size > 1 else float("nan")
	return {
		"count": float(values.size),
		"mean": mean,
		"std": std,
		"median": float(np.median(values)),
		"min": float(np.min(values)),
		"max": float(np.max(values)),
		"variance": float(np.var(values, ddof=1)) if values.size > 1 else float("nan"),
		"cv": float(std / mean) if values.size > 1 and mean != 0 else float("nan"),
	}


def format_value(value: float, precision: int = 4) -> str:
	if value is None or not math.isfinite(value):
		return "nan"
	return f"{value:.{precision}f}"


def print_summary(label: str, summary: dict[str, float]) -> None:
	print(f"{label}:")
	print(f"  n      = {int(summary['count'])}")
	print(f"  mean   = {format_value(summary['mean'])} s")
	print(f"  std    = {format_value(summary['std'])} s")
	print(f"  median = {format_value(summary['median'])} s")
	print(f"  min    = {format_value(summary['min'])} s")
	print(f"  max    = {format_value(summary['max'])} s")


def compare_datasets(simulation: np.ndarray, reality: np.ndarray) -> dict[str, float]:
	sim_summary = summarize(simulation)
	real_summary = summarize(reality)

	mean_diff = real_summary["mean"] - sim_summary["mean"]
	std_diff = real_summary["std"] - sim_summary["std"]
	median_diff = real_summary["median"] - sim_summary["median"]
	min_diff = real_summary["min"] - sim_summary["min"]
	max_diff = real_summary["max"] - sim_summary["max"]

	t_stat, t_p = stats.ttest_ind(reality, simulation, equal_var=False, nan_policy="omit")
	u_stat, u_p = stats.mannwhitneyu(reality, simulation, alternative="two-sided")
	levene_stat, levene_p = stats.levene(reality, simulation, center="median")
	ks_stat, ks_p = stats.ks_2samp(reality, simulation, alternative="two-sided", mode="auto")
	wasserstein = stats.wasserstein_distance(reality, simulation)

	pooled_std = (
		math.sqrt(
			((simulation.size - 1) * np.var(simulation, ddof=1) + (reality.size - 1) * np.var(reality, ddof=1))
			/ (simulation.size + reality.size - 2)
		)
		if simulation.size > 1 and reality.size > 1 and (simulation.size + reality.size - 2) > 0
		else float("nan")
	)

	cohen_d = (
		(real_summary["mean"] - sim_summary["mean"]) / pooled_std
		if math.isfinite(pooled_std) and pooled_std != 0
		else float("nan")
	)
	relative_mean_error = mean_diff / real_summary["mean"] if real_summary["mean"] != 0 else float("nan")
	relative_std_error = std_diff / real_summary["std"] if real_summary["std"] != 0 else float("nan")
	normalized_wasserstein = wasserstein / real_summary["mean"] if real_summary["mean"] != 0 else float("nan")

	return {
		"simulation_mean": sim_summary["mean"],
		"reality_mean": real_summary["mean"],
		"mean_difference": mean_diff,
		"relative_mean_error": relative_mean_error,
		"simulation_std": sim_summary["std"],
		"reality_std": real_summary["std"],
		"std_difference": std_diff,
		"relative_std_error": relative_std_error,
		"simulation_cv": sim_summary["cv"],
		"reality_cv": real_summary["cv"],
		"median_difference": median_diff,
		"min_difference": min_diff,
		"max_difference": max_diff,
		"welch_t_stat": float(t_stat),
		"welch_t_p": float(t_p),
		"mann_whitney_u": float(u_stat),
		"mann_whitney_p": float(u_p),
		"levene_stat": float(levene_stat),
		"levene_p": float(levene_p),
		"ks_stat": float(ks_stat),
		"ks_p": float(ks_p),
		"wasserstein_distance": float(wasserstein),
		"normalized_wasserstein": normalized_wasserstein,
		"cohen_d": cohen_d,
	}


def print_comparison(result: dict[str, float]) -> None:
	print("Differences (reality - simulation):")
	print(f"  mean   = {format_value(result['mean_difference'])} s")
	print(f"  std    = {format_value(result['std_difference'])} s")
	print(f"  median = {format_value(result['median_difference'])} s")
	print(f"  min    = {format_value(result['min_difference'])} s")
	print(f"  max    = {format_value(result['max_difference'])} s")
	print()

	print("Variability:")
	print(f"  simulation CV  = {format_value(result['simulation_cv'])}")
	print(f"  reality CV     = {format_value(result['reality_cv'])}")
	std_ratio = (
		result["reality_std"] / result["simulation_std"]
		if math.isfinite(result["simulation_std"]) and result["simulation_std"] != 0
		else float("nan")
	)
	print(f"  std ratio      = {format_value(std_ratio)}")
	print(f"  std difference  = {format_value(result['std_difference'])} s")
	print()

	print("Significance tests:")
	print(f"  Welch t-test   p = {format_value(result['welch_t_p'], 6)}")
	print(f"  Mann-Whitney U p = {format_value(result['mann_whitney_p'], 6)}")
	print(f"  Levene test    p = {format_value(result['levene_p'], 6)}")
	print(f"  KS test        p = {format_value(result['ks_p'], 6)}")
	print()

	print("How closely simulation matches reality:")
	print(f"  Wasserstein distance   = {format_value(result['wasserstein_distance'])} s")
	print(f"  Normalized Wasserstein = {format_value(result['normalized_wasserstein'])}")
	print(f"  Cohen's d              = {format_value(result['cohen_d'])}")
	print(f"  Relative mean error    = {format_value(result['relative_mean_error'])}")
	print(f"  Relative std error     = {format_value(result['relative_std_error'])}")


def main() -> None:
	simulation = load_recovery_times(SIMULATION_CSV)
	reality = load_recovery_times(REAL_CSV)

	simulation_summary = summarize(simulation)
	reality_summary = summarize(reality)

	print_summary("Simulation", simulation_summary)
	print()
	print_summary("Reality", reality_summary)
	print()

	comparison = compare_datasets(simulation, reality)
	print_comparison(comparison)


if __name__ == "__main__":
	main()
