"""Compare true collected CSV measurements (not the paper's published summary)."""
import argparse
from pathlib import Path
from mppt_reference.analysis import summarize_csv, write_summary

FILES = {"basic": "dynamic_basic_po.csv", "adaptive": "dynamic_adaptive_po.csv", "ann": "dynamic_ann_po.csv"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, default=Path("data"))
    p.add_argument("--output", type=Path, default=Path("data/dynamic_summary.csv"))
    a = p.parse_args()
    summary = []
    for name, file in FILES.items():
        path = a.input_dir / file
        if not path.is_file():
            raise SystemExit(f"Missing experimental data: {path}. Do not replace with fabricated values.")
        summary.append({"algorithm": name, **summarize_csv(path)})
    write_summary(a.output, summary)
    for row in summary:
        print(f"{row['algorithm']:>8}: mean={row['mean_power_w']:.5f} W, "
              f"peak={row['max_power_w']:.5f} W, range={row['power_range_w']:.5f} W")
    print("Saved", a.output)


if __name__ == "__main__":
    main()
