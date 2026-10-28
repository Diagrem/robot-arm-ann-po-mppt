"""Record raw readings to CSV to validate communication and wiring."""
import argparse
from pathlib import Path
from mppt_reference.serial_utils import open_serial, save_samples, send, stream_samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--output", type=Path, default=Path("data/mppt_monitor_log.csv"))
    args = parser.parse_args()
    with open_serial(args.port) as ser:
        send(ser, "STOP")
        try:
            n = save_samples(stream_samples(ser, args.seconds), args.output)
        finally:
            send(ser, "STOP")
    print(f"Saved {n} samples: {args.output}")


if __name__ == "__main__":
    main()
