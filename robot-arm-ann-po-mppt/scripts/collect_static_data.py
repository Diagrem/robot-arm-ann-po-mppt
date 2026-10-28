"""Collect static PWM sweeps. Each completed sweep produces one ANN label."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from mppt_reference.serial_utils import FIELDS, open_serial, send, stream_samples

TRAIN_FIELDS = ["angle_deg", "voltage_v", "best_pwm", "best_power_w", "sweep_id"]


def best_by_sweep(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        if int(row["mode"]) != 3:
            continue
        key = (int(row["angle_deg"]), int(row["sweep_id"]))
        groups.setdefault(key, []).append(row)
    labels = []
    for (angle, sweep), entries in sorted(groups.items()):
        # Ignore incomplete sweep to avoid labeling partial observations.
        if len({int(r["pwm"]) for r in entries}) < 18:
            continue
        best = max(entries, key=lambda r: float(r["estimated_power_w"]))
        labels.append({"angle_deg": angle, "voltage_v": best["voltage_v"],
                       "best_pwm": best["pwm"], "best_power_w": best["estimated_power_w"],
                       "sweep_id": sweep})
    return labels


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", required=True)
    p.add_argument("--seconds", type=float, default=180)
    p.add_argument("--out-dir", type=Path, default=Path("data"))
    args = p.parse_args()
    rows = []
    with open_serial(args.port) as ser:
        send(ser, "STATIC_SWEEP")
        try:
            rows = [s.as_dict() for s in stream_samples(ser, args.seconds)]
        finally:
            send(ser, "STOP")
    write_csv(args.out_dir / "static_sweep_log.csv", FIELDS, rows)
    labels = best_by_sweep(rows)
    write_csv(args.out_dir / "ann_train_data.csv", TRAIN_FIELDS, labels)
    print(f"Recorded {len(rows)} samples, {len(labels)} complete PWM sweeps")
    if len(labels) < 10:
        print("Note: this is a reference pipeline; collect more complete sweeps before training ANN")


if __name__ == "__main__":
    main()
