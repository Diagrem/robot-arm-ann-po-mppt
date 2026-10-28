"""Generate bar plots from experimental summary or separately flagged paper values."""
import argparse
import csv
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, default=Path("data/dynamic_summary.csv"))
    p.add_argument("--paper-summary", action="store_true", help="Use published thesis table, NOT experimental recreation")
    p.add_argument("--output-dir", type=Path, default=Path("outputs"))
    a = p.parse_args()
    if a.paper_summary:
        a.summary = Path("data/paper_reported_summary.csv")
    if not a.summary.exists():
        raise SystemExit(f"Missing file {a.summary}. Run analyze_dynamic.py first.")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with a.summary.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    names = [r["algorithm"] for r in rows]
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for field, caption, name in [("mean_power_w", "Mean estimated power (W)", "average_power_comparison.png"),
                                 ("power_range_w", "Estimated power range (W)", "power_range_comparison.png")]:
        values = [float(r[field]) for r in rows]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(names, values)
        ax.set_ylabel(caption)
        ax.set_ylim(0, max(values) * 1.25)
        for idx, val in enumerate(values):
            ax.text(idx, val, f"{val:.5f}", ha="center", va="bottom", fontsize=9)
        if a.paper_summary:
            ax.set_title("Thesis-reported summary (not reproduced experiment)")
        fig.tight_layout()
        fig.savefig(a.output_dir / name, dpi=160)
        plt.close(fig)
        print("Saved", a.output_dir / name)


if __name__ == "__main__":
    main()
