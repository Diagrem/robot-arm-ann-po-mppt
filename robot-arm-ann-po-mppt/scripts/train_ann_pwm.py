"""Train a thesis-informed MLP on own labeled sweep data (not report aggregates)."""
import argparse
import csv
from pathlib import Path
import joblib
from mppt_reference.ann import train_model


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=Path("data/ann_train_data.csv"))
    p.add_argument("--model", type=Path, default=Path("models/ann_pwm_model.joblib"))
    args = p.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Missing actual training samples: {args.input}")
    with args.input.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if len(rows) < 10:
        raise SystemExit(f"Only {len(rows)} labeled sweeps; collect at least 10 before training")
    x = [[float(row["angle_deg"]), float(row["voltage_v"])] for row in rows]
    y = [float(row["best_pwm"]) for row in rows]
    model = train_model(x, y)
    args.model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model)
    print(f"Saved {args.model}. Used {len(rows)} sweep labels; not a validated generalization score.")


if __name__ == "__main__":
    main()
