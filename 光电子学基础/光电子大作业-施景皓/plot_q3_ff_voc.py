from pathlib import Path

import matplotlib.pyplot as plt


OUT_DIR = Path("figures")

bulk = [
    (1e-3, 1.2285, 83.1317),
    (5e-4, 1.1947, 82.7049),
    (1e-4, 1.1115, 81.8506),
    (5e-5, 1.0764, 81.3987),
    (1e-5, 0.9932, 80.6951),
    (5e-6, 0.9568, 80.6626),
    (1e-6, 0.8762, 80.6719),
    (5e-7, 0.8424, 80.6273),
    (1e-7, 0.7722, 79.4362),
    (5e-8, 0.7436, 78.5247),
    (1e-8, 0.6747, 75.6589),
    (5e-9, 0.6448, 73.6698),
    (1e-9, 0.5681, 65.7934),
]

surface = [
    (1e2, 1.3328, 87.8985),
    (1e1, 1.3328, 87.8985),
    (1, 1.3328, 87.8982),
    (1e-1, 1.3328, 87.8959),
    (1e-2, 1.3328, 87.8726),
    (1e-3, 1.3328, 87.6395),
    (1e-4, 1.3300, 85.5855),
    (1e-5, 1.3104, 76.0971),
    (1e-6, 1.1004, 79.8305),
    (1e-7, 0.9562, 82.6531),
    (1e-8, 0.8568, 83.4523),
    (1e-9, 0.7756, 82.4557),
]


def sorted_by_voc(rows):
    return sorted(rows, key=lambda row: row[1])


def plot_single(data, color, marker, title, filename, xlim, ylim):
    rows = sorted_by_voc(data)

    plt.figure(figsize=(7.0, 4.8), dpi=220)
    plt.plot(
        [row[1] for row in rows],
        [row[2] for row in rows],
        marker=marker,
        linewidth=2.2,
        markersize=5.5,
        color=color,
    )
    plt.xlabel(r"$V_{oc}$ (V)", fontsize=11)
    plt.ylabel("FF (%)", fontsize=11)
    plt.title(title, fontsize=13, pad=10)
    plt.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    plt.xlim(*xlim)
    plt.ylim(*ylim)
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, bbox_inches="tight")
    plt.close()


def plot_comparison():
    bulk_rows = sorted_by_voc(bulk)
    surface_rows = sorted_by_voc(surface)

    plt.figure(figsize=(7.4, 5.0), dpi=220)
    plt.plot(
        [row[1] for row in bulk_rows],
        [row[2] for row in bulk_rows],
        marker="o",
        linewidth=2.2,
        markersize=5.5,
        color="#1f77b4",
        label="Bulk SRH",
    )
    plt.plot(
        [row[1] for row in surface_rows],
        [row[2] for row in surface_rows],
        marker="s",
        linewidth=2.2,
        markersize=5.2,
        color="#d62728",
        label="Surface SRH-dominant",
    )
    plt.xlabel(r"$V_{oc}$ (V)", fontsize=11)
    plt.ylabel("FF (%)", fontsize=11)
    plt.title(
        r"FF--$V_{oc}$ Curves for Different SRH Recombination Mechanisms",
        fontsize=13,
        pad=10,
    )
    plt.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    plt.legend(frameon=True, fontsize=10)
    plt.xlim(0.52, 1.38)
    plt.ylim(63, 90)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "q3_ff_voc_comparison.png", bbox_inches="tight")
    plt.close()


def main():
    OUT_DIR.mkdir(exist_ok=True)
    plot_single(
        bulk,
        "#1f77b4",
        "o",
        r"FF--$V_{oc}$ Curve for Bulk SRH Recombination",
        "q3_bulk_ff_voc.png",
        (0.52, 1.26),
        (63, 85),
    )
    plot_single(
        surface,
        "#d62728",
        "s",
        r"FF--$V_{oc}$ Curve for Surface SRH-Dominant Recombination",
        "q3_surface_ff_voc.png",
        (0.72, 1.36),
        (74, 90),
    )
    plot_comparison()


if __name__ == "__main__":
    main()
