import os
import re
from collections import defaultdict

RESULT_DIR = "mb_all_results"

# mb_<trace>_<cache>_<block>_<assoc>_<wt|wb>_<wa|nw>.txt
fname_re = re.compile(
    r"mb_(?P<trace>\w+)_(?P<cache>\d+)_(?P<block>\d+)_(?P<assoc>\d+)_(?P<wp>wt|wb)_(?P<alloc>wa|nw)\.txt"
)

df_re = re.compile(r"demand fetch:\s+(\d+)", re.IGNORECASE)
cb_re = re.compile(r"copies back:\s+(\d+)", re.IGNORECASE)


data = defaultdict(lambda: defaultdict(dict))

for fname in os.listdir(RESULT_DIR):
    m = fname_re.match(fname)
    if not m:
        continue

    trace = m.group("trace")
    cache = int(m.group("cache"))
    block = int(m.group("block"))
    assoc = int(m.group("assoc"))
    wp = m.group("wp").upper()      # WT / WB
    alloc = "WA" if m.group("alloc") == "wa" else "WNA"

    with open(os.path.join(RESULT_DIR, fname)) as f:
        txt = f.read()

    df = int(df_re.search(txt).group(1))
    cb = int(cb_re.search(txt).group(1))

    data[trace][(cache, block, assoc)][(wp, alloc)] = (df, cb)


# ======================================================
# Part 1: WT vs WB (fixed WNA)
# ======================================================
for trace in sorted(data.keys()):
    print("\n% ===============================================")
    print(f"% Part 1: WT vs WB (WNA) — {trace}.trace")
    print("% ===============================================\n")

    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\small")
    print(rf"\caption{{Memory Bandwidth Comparison (WT vs WB, WNA) on {trace}.trace}}")
    print(r"\begin{tabular}{ccccccc}")
    print(r"\hline")
    print(r"Cache & Block & Assoc & Policy & Demand Fetch & Copies Back & Total \\")
    print(r"\hline")

    for (cache, block, assoc) in sorted(data[trace].keys()):
        for wp in ["WT", "WB"]:
            key = (wp, "WNA")
            if key not in data[trace][(cache, block, assoc)]:
                continue
            df, cb = data[trace][(cache, block, assoc)][key]
            print(f"{cache//1024}KB & {block}B & {assoc} & {wp} & {df} & {cb} & {df+cb} \\\\")
        print(r"\hline")

    print(r"\end{tabular}")
    print(r"\end{table}")


# ======================================================
# Part 2: WA vs WNA (fixed WB)
# ======================================================
for trace in sorted(data.keys()):
    print("\n% ===============================================")
    print(f"% Part 2: WA vs WNA (WB) — {trace}.trace")
    print("% ===============================================\n")

    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\small")
    print(rf"\caption{{Memory Bandwidth Comparison (WA vs WNA, WB) on {trace}.trace}}")
    print(r"\begin{tabular}{ccccccc}")
    print(r"\hline")
    print(r"Cache & Block & Assoc & Policy & Demand Fetch & Copies Back & Total \\")
    print(r"\hline")

    for (cache, block, assoc) in sorted(data[trace].keys()):
        for alloc in ["WNA", "WA"]:
            key = ("WB", alloc)
            if key not in data[trace][(cache, block, assoc)]:
                continue
            df, cb = data[trace][(cache, block, assoc)][key]
            print(f"{cache//1024}KB & {block}B & {assoc} & {alloc} & {df} & {cb} & {df+cb} \\\\")
        print(r"\hline")

    print(r"\end{tabular}")
    print(r"\end{table}")
