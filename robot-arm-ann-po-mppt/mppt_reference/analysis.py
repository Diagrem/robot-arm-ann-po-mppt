"""Report summary functions. The power range is max minus min, not variance."""
from __future__ import annotations
import csv
from pathlib import Path


def summarize_csv(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No measurements in: {path}")
    power = [float(r["estimated_power_w"]) for r in rows]
    pwm = [float(r["pwm"]) for r in rows]
    n = len(rows)
    return {"mean_power_w": sum(power) / n, "max_power_w": max(power),
            "power_range_w": max(power) - min(power), "mean_pwm": sum(pwm) / n,
            "samples": n}


def write_summary(path: Path, results: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
