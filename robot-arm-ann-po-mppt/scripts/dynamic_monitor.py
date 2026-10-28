"""Record dynamic shading experiment for one mode. Reference-only serial protocol."""
from __future__ import annotations
import argparse
import time
from pathlib import Path
from mppt_reference.serial_utils import open_serial, save_samples, send, stream_samples

MODES = {"basic": (0, "dynamic_basic_po.csv"),
         "adaptive": (1, "dynamic_adaptive_po.csv"),
         "ann": (2, "dynamic_ann_po.csv")}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", required=True)
    p.add_argument("--mode", choices=MODES, required=True)
    p.add_argument("--seconds", type=float, default=180)
    p.add_argument("--out-dir", type=Path, default=Path("data"))
    p.add_argument("--model", type=Path, default=Path("models/ann_pwm_model.joblib"))
    p.add_argument("--prediction-interval", type=float, default=1.0)
    a = p.parse_args()
    mode, filename = MODES[a.mode]
    model = None
    if a.mode == "ann":
        if not a.model.is_file():
            raise SystemExit(f"Train model first: {a.model}")
        import joblib
        model = joblib.load(a.model)  # Only trusted local models.
        from mppt_reference.ann import predict_pwm
    with open_serial(a.port) as ser:
        send(ser, f"MODE,{mode}")
        send(ser, "DYNAMIC_START")
        last_prediction = 0.0

        def on_sample(sample):
            nonlocal last_prediction
            if model is not None and time.monotonic() - last_prediction >= a.prediction_interval:
                recommended = predict_pwm(model, sample.angle_deg, sample.voltage_v)
                send(ser, f"ANN_PWM,{recommended}")
                last_prediction = time.monotonic()

        try:
            n = save_samples(stream_samples(ser, a.seconds), a.out_dir / filename,
                             callback=on_sample)
        finally:
            send(ser, "STOP")
    print(f"{a.mode}: {n} readings saved to {a.out_dir / filename}")


if __name__ == "__main__":
    main()
