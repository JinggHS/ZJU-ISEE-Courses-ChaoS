from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


NN = 800
HBAR = 6.63e-34 / (2 * np.pi)
M_ELECTRON = 9.1e-31
EV_TO_J = 1.6e-19
J_TO_EV = 1.0 / EV_TO_J
OUTPUT_DIR = Path("outputs")


def save_figure(fig, filename, dpi=180):
    """Save the figure to the outputs directory."""
    target = OUTPUT_DIR / filename
    fig.savefig(target, dpi=dpi)


def solve_schrodinger(x_nm, potential_eV):
    """Use finite differences to solve the 1D stationary Schrodinger equation."""
    dx_m = (x_nm[1] - x_nm[0]) * 1e-9
    chi0 = HBAR**2 / (2 * M_ELECTRON * dx_m**2)
    potential_joule = potential_eV * EV_TO_J

    diagonal = 2 * chi0 + potential_joule
    off_diagonal = np.full(len(x_nm) - 1, -chi0)
    hamiltonian = np.diag(diagonal)
    hamiltonian += np.diag(off_diagonal, k=1)
    hamiltonian += np.diag(off_diagonal, k=-1)

    eigenvalues_joule, eigenfunctions = np.linalg.eigh(hamiltonian)
    energies_eV = eigenvalues_joule * J_TO_EV

    for index in range(eigenfunctions.shape[1]):
        norm = np.sqrt(np.trapezoid(np.abs(eigenfunctions[:, index]) ** 2, x_nm))
        eigenfunctions[:, index] /= norm

    return energies_eV, eigenfunctions


def orient_wavefunctions_for_plot(
    x_nm,
    eigenfunctions,
    state_count=4,
    odd_peak_negative=False,
):
    """Flip signs for plotting only, since the global phase is physically arbitrary."""
    oriented = eigenfunctions.copy()
    max_states = min(state_count, oriented.shape[1])
    center_index = len(x_nm) // 2

    for state in range(max_states):
        if odd_peak_negative and state % 2 == 0:
            # For n=1,3,... match the reference style by forcing the central lobe downward.
            if oriented[center_index, state] > 0:
                oriented[:, state] *= -1
        elif odd_peak_negative and state % 2 == 1:
            # For n=2,4,... force the dominant lobe on the left of center upward.
            left_half = oriented[:center_index, state]
            left_index = np.argmax(np.abs(left_half))
            if left_half[left_index] < 0:
                oriented[:, state] *= -1
        else:
            peak_index = np.argmax(np.abs(oriented[:, state]))
            if oriented[peak_index, state] < 0:
                oriented[:, state] *= -1

    return oriented


def infinite_square_well(width_nm, nn=NN):
    x_nm = np.linspace(0.0, width_nm, nn)
    potential_eV = np.zeros_like(x_nm)
    return x_nm, potential_eV


def triangular_well(width_nm, slope_eV_per_nm=0.0128, nn=NN):
    x_nm = np.linspace(-width_nm / 2, width_nm / 2, nn)
    potential_eV = slope_eV_per_nm * np.abs(x_nm)
    return x_nm, potential_eV


def parabolic_well(x_limit_nm=20.0, nn=NN):
    x_nm = np.linspace(-x_limit_nm, x_limit_nm, nn)
    potential_eV = 8.0 * (x_nm / 20.0) ** 2
    return x_nm, potential_eV


def analytical_infinite_well_energies(width_nm, quantum_numbers):
    width_m = width_nm * 1e-9
    values_joule = (
        quantum_numbers**2 * np.pi**2 * HBAR**2 / (2 * M_ELECTRON * width_m**2)
    )
    return values_joule * J_TO_EV


def plot_potential_and_states(
    x_nm,
    potential_eV,
    energies_eV,
    eigenfunctions,
    title,
    filename,
    odd_peak_negative=False,
):
    eigenfunctions = orient_wavefunctions_for_plot(
        x_nm,
        eigenfunctions,
        state_count=4,
        odd_peak_negative=odd_peak_negative,
    )
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    axes = axes.ravel()

    axes[0].plot(x_nm, potential_eV * 1000, color="black")
    axes[0].set_title(title, fontsize=11)
    axes[0].set_xlabel("x (nm)")
    axes[0].set_ylabel("V (meV)")

    axes[1].axis("off")

    for state in range(4):
        ax = axes[state + 2]
        ax.plot(x_nm, eigenfunctions[:, state], color="black")
        ax.set_title(f"State n={state + 1}", fontsize=11)
        ax.set_xlabel("x (nm)")
        ax.set_ylabel(rf"$\psi_{state + 1}(x)$")

    fig.tight_layout()
    save_figure(fig, filename, dpi=180)
    plt.close(fig)


def plot_energy_vs_quantum_number(width_nm=50.0):
    quantum_numbers = np.arange(1, 11)
    x_nm, potential_eV = infinite_square_well(width_nm)
    energies_eV, _ = solve_schrodinger(x_nm, potential_eV)
    theory_eV = analytical_infinite_well_energies(width_nm, quantum_numbers)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(quantum_numbers, energies_eV[:10] * 1000, "o-", label="Numerical")
    ax.plot(quantum_numbers, theory_eV * 1000, "s--", label="Analytical")
    ax.set_xlabel("Quantum number n")
    ax.set_ylabel("Energy (meV)")
    ax.set_title("First 10 eigenenergies of a 50 nm infinite square well")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, "infinite_well_energy_levels.png", dpi=180)
    plt.close(fig)

    return energies_eV[:10], theory_eV


def plot_width_scan(widths_nm):
    ground_eV = []
    first_excited_eV = []

    for width_nm in widths_nm:
        x_nm, potential_eV = infinite_square_well(width_nm)
        energies_eV, _ = solve_schrodinger(x_nm, potential_eV)
        ground_eV.append(energies_eV[0])
        first_excited_eV.append(energies_eV[1])

    ground_eV = np.array(ground_eV)
    first_excited_eV = np.array(first_excited_eV)
    gap_eV = first_excited_eV - ground_eV

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(widths_nm, ground_eV * 1000, "o-", label="Ground state")
    ax.plot(widths_nm, first_excited_eV * 1000, "s-", label="First excited state")
    ax.plot(widths_nm, gap_eV * 1000, "^-", label="Energy gap")
    ax.set_xlabel("Well width (nm)")
    ax.set_ylabel("Energy (meV)")
    ax.set_title("Infinite-well energies vs width")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, "infinite_well_width_scan.png", dpi=180)
    plt.close(fig)

    return ground_eV, first_excited_eV, gap_eV


def plot_triangle_comparison():
    x_50, v_50 = triangular_well(50.0)
    e_50, psi_50 = solve_schrodinger(x_50, v_50)
    psi_50 = orient_wavefunctions_for_plot(x_50, psi_50, odd_peak_negative=True)

    x_100, v_100 = triangular_well(100.0)
    e_100, psi_100 = solve_schrodinger(x_100, v_100)
    psi_100 = orient_wavefunctions_for_plot(x_100, psi_100, odd_peak_negative=True)

    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    x_limit = (-50, 50)

    axes = axes.ravel()
    axes[0].plot(x_50, v_50 * 1000, color="black", linestyle="--", linewidth=1.8, label="50 nm")
    axes[0].plot(x_100, v_100 * 1000, color="tab:red", linewidth=1.5, label="100 nm")
    axes[0].set_xlim(*x_limit)
    axes[0].set_title("Triangular Well Potential", fontsize=11)
    axes[0].set_xlabel("x (nm)")
    axes[0].set_ylabel("V (meV)")
    axes[0].legend(fontsize=9)

    axes[1].axis("off")

    for plot_index, state in enumerate(range(4), start=2):
        ax = axes[plot_index]
        ax.plot(
            x_50,
            psi_50[:, state],
            color="black",
            linestyle="--",
            linewidth=1.8,
            label="50 nm",
        )
        ax.plot(
            x_100,
            psi_100[:, state],
            color="tab:red",
            linewidth=1.4,
            label="100 nm",
        )
        ax.set_xlim(*x_limit)
        ax.set_title(f"State n={state + 1}", fontsize=11)
        ax.set_xlabel("x (nm)")
        ax.set_ylabel(rf"$\psi_{state + 1}(x)$")
        ax.legend(fontsize=8, loc="upper right")

    fig.tight_layout()
    save_figure(fig, "triangular_well_comparison.png", dpi=180)
    save_figure(fig, "triangular_well_comparison_v2.png", dpi=180)
    plt.close(fig)

    return e_50, e_100


def write_report(summary_lines):
    lines = [
        "# 作业6第2题数值结果摘要",
        "",
        "本文件由 `eigenfunction.py` 自动生成，可直接作为报告写作提纲。",
        "",
    ]
    lines.extend(summary_lines)
    (OUTPUT_DIR / "report_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    summary = []

    x_inf, v_inf = infinite_square_well(50.0)
    e_inf, psi_inf = solve_schrodinger(x_inf, v_inf)
    plot_potential_and_states(
        x_inf,
        v_inf,
        e_inf,
        psi_inf,
        "50 nm Infinite Square Well",
        "infinite_well_50nm_states.png",
    )
    summary.append("## 1. 50 nm 无限深势阱")
    summary.extend(
        f"- 第 {i + 1} 个能级: {value * 1000:.4f} meV" for i, value in enumerate(e_inf[:4])
    )
    summary.append("")

    numerical_eV, theory_eV = plot_energy_vs_quantum_number(50.0)
    rel_error = np.abs((numerical_eV - theory_eV) / theory_eV)
    summary.append("## 2. 前10个本征能级与理论公式比较")
    summary.append(
        f"- 最大相对误差: {rel_error.max():.4%}，最小相对误差: {rel_error.min():.4%}"
    )
    summary.append("- 数值解与解析解基本重合，偏差主要来自有限差分离散化。")
    summary.append("")

    widths_nm = np.arange(10.0, 101.0, 10.0)
    ground_eV, first_excited_eV, gap_eV = plot_width_scan(widths_nm)
    summary.append("## 3. 无限深势阱宽度扫描")
    summary.append(
        f"- 10 nm 时基态/第一激发态/能级差: "
        f"{ground_eV[0] * 1000:.4f} / {first_excited_eV[0] * 1000:.4f} / {gap_eV[0] * 1000:.4f} meV"
    )
    summary.append(
        f"- 100 nm 时基态/第一激发态/能级差: "
        f"{ground_eV[-1] * 1000:.4f} / {first_excited_eV[-1] * 1000:.4f} / {gap_eV[-1] * 1000:.4f} meV"
    )
    summary.append("- 随宽度增大，能量与能级差都下降，趋势接近 1/L^2。")
    summary.append("")

    x_tri, v_tri = triangular_well(50.0)
    e_tri, psi_tri = solve_schrodinger(x_tri, v_tri)
    plot_potential_and_states(
        x_tri,
        v_tri,
        e_tri,
        psi_tri,
        "50 nm Triangular Well",
        "triangular_well_50nm_states.png",
        odd_peak_negative=True,
    )
    summary.append("## 4. 50 nm 三角势阱")
    summary.extend(
        f"- 第 {i + 1} 个能级: {value * 1000:.4f} meV" for i, value in enumerate(e_tri[:4])
    )
    summary.append("")

    e_tri_50, e_tri_100 = plot_triangle_comparison()
    summary.append("## 5. 三角势阱宽度从 50 nm 变到 100 nm（斜率不变）")
    summary.append(
        f"- 50 nm 基态/第一激发态: {e_tri_50[0] * 1000:.4f} / {e_tri_50[1] * 1000:.4f} meV"
    )
    summary.append(
        f"- 100 nm 基态/第一激发态: {e_tri_100[0] * 1000:.4f} / {e_tri_100[1] * 1000:.4f} meV"
    )
    summary.append("- 低能级几乎不变，因为低能态主要局域在阱中心附近，而两种宽度在中心区域的势能斜率完全相同。")
    summary.append("")

    x_par, v_par = parabolic_well()
    e_par, psi_par = solve_schrodinger(x_par, v_par)
    plot_potential_and_states(
        x_par,
        v_par,
        e_par,
        psi_par,
        "Parabolic Well: V = 8(x/20)^2 eV",
        "parabolic_well_states.png",
        odd_peak_negative=True,
    )
    gaps_meV = np.diff(e_par[:4]) * 1000
    summary.append("## 6. 抛物线势阱")
    summary.extend(
        f"- 第 {i + 1} 个能级: {value * 1000:.4f} meV" for i, value in enumerate(e_par[:4])
    )
    summary.append("- 相邻能级差 (meV): " + ", ".join(f"{gap:.4f}" for gap in gaps_meV))
    summary.append("- 相邻能级差近似相等，符合简谐振子型势阱的特征。")
    summary.append("")

    write_report(summary)


if __name__ == "__main__":
    main()
