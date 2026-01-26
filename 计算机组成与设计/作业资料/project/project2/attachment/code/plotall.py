
import glob
import re
import matplotlib.pyplot as plt

# =====================================================
# Global style settings
# =====================================================
DATA_DIR = "code"

I_COLOR = "#0015ff"   # Instruction Cache
D_COLOR = "#ff00b3"   # Data Cache
Y_LIM_DEFAULT = (0.00, 1.02)  # fallback, though we'll override per plot

# trace name shown in figures
TRACE_DISPLAY_NAME = {
    "cc": "cc",
    "full": "spice",
    "tex": "tex",
}

hit_pattern = re.compile(r"hit rate[:\s]+([0-9.]+)", re.IGNORECASE)


def load_hit_rates(pattern, x_transform=lambda x: x):
    files = sorted(
        glob.glob(f"{pattern}"),
        key=lambda x: int(re.findall(r"\d+", x)[0])
    )

    xs, i_hits, d_hits = [], [], []

    for fname in files:
        x = int(re.findall(r"\d+", fname)[0])
        x = x_transform(x)

        with open(fname, "r") as f:
            hits = []
            for line in f:
                m = hit_pattern.search(line)
                if m:
                    hits.append(float(m.group(1)))

        if len(hits) < 2:
            print(f"Warning: failed to parse {fname}")
            continue

        xs.append(x)
        i_hits.append(hits[0])
        d_hits.append(hits[1])

    return xs, i_hits, d_hits


def plot_curve(xs, i_hits, d_hits,
               xlabel, title, outfile,
               xscale=None, xbase=None,
               linestyle=None,
               ylim=(0.0, 1.05)):

    plt.figure(figsize=(9, 5))

    plt.plot(xs, i_hits,
             marker='o',
             linestyle=linestyle or '-',
             color=I_COLOR,
             label="Instruction Cache")

    plt.plot(xs, d_hits,
             marker='s',
             linestyle=linestyle or '-',
             color=D_COLOR,
             label="Data Cache")

    if xscale:
        if xbase:
            plt.xscale(xscale, base=xbase)
        else:
            plt.xscale(xscale)

    plt.ylim(*ylim)
    plt.xlabel(xlabel)
    plt.ylabel("Hit Rate")
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both")

    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    plt.close()

    print(f"Saved: {outfile}")


# =====================================================
# 1. Associativity (cc / spice / tex)
# =====================================================
for trace in ["cc", "full", "tex"]:
    xs, i, d = load_hit_rates(f"assoc_{trace}_*.txt")
    plot_curve(
        xs, i, d,
        xlabel="Associativity (log₂ scale)",
        title=f"Impact of Associativity ({TRACE_DISPLAY_NAME[trace]}.trace)",
        outfile=f"associativity_{trace}_trace.png",
        xscale='log',
        xbase=2,
        ylim=(0.7, 1.02)
    )


# =====================================================
# 2. Block Size (cc / spice / tex)
# =====================================================
for trace in ["cc", "full", "tex"]:
    xs, i, d = load_hit_rates(f"bs_{trace}_*.txt")
    plot_curve(
        xs, i, d,
        xlabel="Block Size (Bytes, log₂ scale)",
        title=f"Impact of Block Size ({TRACE_DISPLAY_NAME[trace]}.trace)",
        outfile=f"block_size_{trace}_trace.png",
        xscale='log',
        xbase=2,
        ylim=(0.7, 1.02)
    )


# =====================================================
# 3. Working Set (cc / spice / tex)
# =====================================================
for trace in ["cc", "full", "tex"]:
    xs, i, d = load_hit_rates(
        f"ws_{trace}_*.txt",
        x_transform=lambda x: x / 1024   # Bytes → KB
    )
    plot_curve(
        xs, i, d,
        xlabel="Cache Size (KB, log₂ scale)",
        title=f"Working Set Characterization ({TRACE_DISPLAY_NAME[trace]}.trace)",
        outfile=f"working_set_{trace}_trace.png",
        linestyle='--',
        xscale='log',
        xbase=2,
        ylim=(0.0, 1.02)
    )
