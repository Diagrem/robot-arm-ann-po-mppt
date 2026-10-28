"""Test inference of a locally trained model (never load untrusted model files)."""
import argparse
from pathlib import Path
import joblib
from mppt_reference.ann import predict_pwm


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, default=Path("models/ann_pwm_model.joblib"))
    p.add_argument("--angle", type=float, required=True)
    p.add_argument("--voltage", type=float, required=True)
    a = p.parse_args()
    if not a.model.is_file():
        raise SystemExit("Train a model from actual static data first")
    model = joblib.load(a.model)  # Load ONLY files created/trusted by you.
    print("Recommended PWM (reference model):", predict_pwm(model, a.angle, a.voltage))


if __name__ == "__main__":
    main()
