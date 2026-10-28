"""Thesis-informed reference utilities. Not the original study code."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Optional

RESISTANCE_OHM = 40.0
PWM_MAX = 255


def limit_pwm(value: float | int) -> int:
    return max(0, min(PWM_MAX, int(round(value))))


def estimated_power(voltage: float, pwm: int, resistance_ohm: float = RESISTANCE_OHM) -> float:
    if resistance_ohm <= 0:
        raise ValueError("Resistance must be positive")
    return (limit_pwm(pwm) / PWM_MAX) * (float(voltage) ** 2) / resistance_ohm


@dataclass
class Sample:
    time_ms: int
    angle_deg: int
    pwm: int
    voltage_v: float
    current_a: float
    estimated_power_w: float
    mode: int
    sweep_id: int

    @classmethod
    def from_csv_line(cls, raw: str) -> Optional["Sample"]:
        """Reference CSV wire format: time,angle,pwm,voltage,current,p_est,mode,sweep_id.

        Not guaranteed to match the original Arduino serial output.
        """
        pieces = next(csv.reader([raw.strip()]))
        if len(pieces) != 8:
            return None
        try:
            return cls(int(pieces[0]), int(pieces[1]), limit_pwm(int(pieces[2])),
                       float(pieces[3]), float(pieces[4]), float(pieces[5]),
                       int(pieces[6]), int(pieces[7]))
        except ValueError:
            return None

    def as_dict(self) -> dict:
        return vars(self).copy()


class PerturbObserve:
    def __init__(self, initial_pwm: int = 80, step_size: int = 4, adaptive: bool = False):
        self.pwm = limit_pwm(initial_pwm)
        self.step = step_size
        self.adaptive = adaptive
        self.direction = 1
        self.previous_power: float | None = None

    def update(self, power: float) -> int:
        if self.previous_power is not None:
            delta = power - self.previous_power
            if delta < 0:
                self.direction *= -1
            if self.adaptive:
                # Example thresholds only. Exact thresholds are not stated in the paper.
                magnitude = abs(delta)
                step = 12 if magnitude > 0.08 else 7 if magnitude > 0.035 else 4 if magnitude > 0.01 else 2
            else:
                step = self.step
            self.pwm = limit_pwm(self.pwm + self.direction * step)
        self.previous_power = power
        return self.pwm

    def recommend(self, pwm: int) -> None:
        """ANN assisted initialization / re-centering before subsequent P&O updates."""
        self.pwm = limit_pwm(pwm)
        self.previous_power = None
