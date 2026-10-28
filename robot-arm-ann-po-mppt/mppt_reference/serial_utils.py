"""Shared reference serial logger. Hardware connection required."""
from __future__ import annotations

import csv
import time
from pathlib import Path

from .core import Sample

FIELDS = list(Sample.__dataclass_fields__)


def open_serial(port: str, baudrate: int = 115200):
    try:
        import serial
    except ImportError as exc:
        raise SystemExit("Install dependencies: pip install -r requirements.txt") from exc
    ser = serial.Serial(port, baudrate=baudrate, timeout=1)
    time.sleep(2)  # Arduino UNO resets when serial port opens
    return ser


def send(ser, message: str) -> None:
    ser.write((message.rstrip() + "\n").encode("ascii"))
    ser.flush()


def stream_samples(ser, seconds: float):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line:
            continue
        sample = Sample.from_csv_line(line)
        if sample is not None:
            yield sample


def save_samples(samples, filename: Path, callback=None) -> int:
    filename.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with filename.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for sample in samples:
            writer.writerow(sample.as_dict())
            count += 1
            if callback is not None:
                callback(sample)
    return count
