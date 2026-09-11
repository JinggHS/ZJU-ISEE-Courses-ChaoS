from pathlib import Path

import matplotlib.pyplot as plt


OUT_DIR = Path("figures")

thickness = [100, 200, 300, 400, 500]

plots = {
    "jsc": {
        "values": [15.2440, 19.1619, 20.3298, 21.7037, 21.6822],
        "color": "#1f77b4",
        "ylabel": r"$J_{sc}$ (mA/cm$^2$)",
        "title": r"$J_{sc}$ vs. MAPbI3 Active-Layer Thickness",
        "filename": "q2_jsc_vs_thickness.png",
    },
    "voc": {
        "values": [1.0584, 1.0344, 1.0164, 1.0044, 0.9930],
        "color": "#d62728",
        "ylabel": r"$V_{oc}$ (V)",
        "title": r"$V_{oc}$ vs. MAPbI3 Active-Layer Thickness",
        "filename": "q2_voc_vs_thickness.png",
    },
    "ff": {
        "values": [81.5468, 81.2099, 80.9997, 80.8765, 80.7154],
        "color": "#2ca02c",
        "ylabel": "FF (%)",
        "title": "FF vs. MAPbI3 Active-Layer Thickness",
        "filename": "q2_ff_vs_thickness.png",
    },
    "pce": {
        "values": [13.1570, 16.0967, 16.7372, 17.6304, 17.3783],
        "color": "#9467bd",
        "ylabel": "PCE (%)",
        "title": "PCE vs. MAPbI3 Active-Layer Thickness",
        "filename": "q2_pce_vs_thickness.png",
    },
}


def plot_curve(values, color, ylabel, title, filename):
    span = max(values) - min(values)
    pad = span * 0.18 if span else max(values) * 0.05

    plt.figure(figsize=(7.2, 4.6), dpi=200)
    plt.plot(
        thickness,
        values,
        marker="o",
        linewidth=2.3,
        markersize=6,
        color=color,
    )
    plt.xlabel("MAPbI3 active-layer thickness (nm)", fontsize=11)
    plt.ylabel(ylabel, fontsize=11)
    plt.title(title, fontsize=13, pad=10)
    plt.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    plt.xlim(80, 520)
    plt.ylim(min(values) - pad, max(values) + pad)
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, bbox_inches="tight")
    plt.close()


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for config in plots.values():
        plot_curve(**config)


if __name__ == "__main__":
    main()
