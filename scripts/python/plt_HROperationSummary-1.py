import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import utilities as utils
import utilities_plotting as utils_plot
import seaborn as sns
from pathlib import Path


def create_subplot(ax, ax2, df, scenario, is_top_row, is_bottom_row):
    df = df.pivot(index="R_e", columns="OperationalSummarySet", values="value")
    df.index = df.index.map(lambda x: f"-{100 - x}%")  # R_e to presentation format

    # Plot capacity bars
    bars_capacity = ax.barh(
        df.index,
        df["Capacity"],
        color=sns.color_palette("colorblind")[1],
        label="Capacity",
        zorder=1,
    )

    # Overlay production hatch
    bars_production = ax2.barh(
        df.index,
        df["Production"],
        color="none",
        edgecolor="black",
        hatch="//////",
        lw=0,
        zorder=2,
    )

    # Include a marker for NaN values
    nan_mask = df["Capacity"].isna()
    y_positions = np.arange(len(df.index))
    scatter_nan = ax.scatter(
        [3500 / 2] * nan_mask.sum(),
        y_positions[nan_mask],
        s=15,
        color="red",
        marker="x",
        zorder=5,
    )

    # Format y-axes
    ax.set_ylabel(f"Carbon Emissions Limit")
    ax.text(-0.3, 0.5, f"{scenario}", transform=ax.transAxes, weight="bold", va="center", ha="center", rotation=90)

    # Format x-axes
    # ax.set_title(f"{scenario}", fontweight="bold", fontsize=10)

    # Add grid lines
    ax.grid(axis="x", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)
    ax.grid(axis="x", which="minor", linestyle="--", linewidth=0.3, alpha=0.5, zorder=0)
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)

    return bars_capacity, bars_production, scatter_nan


def create_plot(data, scenarios):
    fig, axs_primary = plt.subplots(
        len(scenarios),
        1,
        figsize=(FIGSIZE[0] / 2.54, FIGSIZE[1] / 2.54),
        sharey=True,
        sharex=True,
    )

    axs_secondary = np.array([ax.twiny() for ax in axs_primary])

    # Plot each subplot
    for row, scenario in enumerate(scenarios):
        ax_primary = axs_primary[row]
        ax_secondary = axs_secondary[row]
        df = utils.filter(data, {"Scenario": [scenario]})
        df = df[["R_e", "OperationalSummarySet", "value"]]

        if not df.empty:
            bars_capacity, bars_production, scatter_nan = create_subplot(
                ax_primary,
                ax_secondary,
                df,
                scenario,
                is_top_row=(row == 0),
                is_bottom_row=(row == len(scenarios) - 1),
            )

    # Scaling factor to align production bar length with corresponding capacity factor
    scaling = 8760 * 1e-6  # MW to TWh/year

    major_ticks_primary = np.arange(0, 3500 + 1e-3, 500)
    minor_ticks_primary = np.arange(0, 3500 + 1e-3, 250)
    major_ticks_secondary = np.arange(0, 3500 * scaling + 1e-3, 3500 * scaling * 1 / 7)
    minor_ticks_secondary = np.arange(0, 3500 * scaling + 1e-3, 3500 * scaling * 1 / 14)

    axs_primary[-1].set_xlim(0, 3500)
    axs_primary[-1].set_xticks(major_ticks_primary)
    axs_primary[-1].set_xticks(minor_ticks_primary, minor=True)
    axs_primary[-1].set_xticklabels([f"{x/1000:.1f}" for x in major_ticks_primary], rotation=0)
    axs_primary[-1].set_xlabel("WHR Capacity (GW)")

    axs_secondary[0].set_xlim(0, 3500 * scaling)
    axs_secondary[0].set_xticks(major_ticks_secondary)
    axs_secondary[0].set_xticks(minor_ticks_secondary, minor=True)
    axs_secondary[0].set_xticklabels(
        [f"{x:.1f}" for x in major_ticks_secondary], rotation=0
    )
    axs_secondary[0].set_xlabel("WHR Production (TWh/year)")

    axs_secondary[-1].set_xlim(0, 3500 * scaling)
    axs_secondary[-1].set_xticks(major_ticks_secondary)
    axs_secondary[-1].set_xticks(minor_ticks_secondary, minor=True)
    axs_secondary[-1].set_xticklabels([f"" for x in major_ticks_secondary], rotation=0)
    axs_secondary[-1].set_xlabel("")

    (_, _, x_center), (y_down, _, _) = utils_plot.axes_coordinates(axs_primary)

    # # Create a single legend for the entire figure
    legend = fig.legend(
        [bars_capacity, bars_production, scatter_nan],
        ["WHR Capacity", "WHR Production", "Infeasible"],
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(x_center-0.025, 0.0), # for some reason not well-aligned
    )

    plt.tight_layout()
    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(wspace=0.15, hspace=0.3, bottom=(y_down + legend_height))

    return fig


def main(file_path):
    data = pd.read_csv(file_path)
    data = utils.filter(data, include={"Scenario": ["A", "B"], "R_c": [100]})
    data = utils.rename_values(
        data, {"Scenario": {"A": "OPEX Subsidy", "B": "CAPEX Subsidy"}}
    )

    scenarios = sorted(list(set(data["Scenario"])), reverse=True)

    fig = create_plot(data, scenarios)

    if SAVE:
        plt.savefig(outdir / "HRSummary-1.png", dpi=DPI, bbox_inches="tight")
        print(f"---> Plot saved to {outdir}HRSummary-1.png")
    if SHOW:
        plt.show()


if __name__ == "__main__":

    basedir = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article"
    outdir = basedir / "illustrations" / "plots"
    input_file = basedir / "consolidated-results" / "HROperationSummary.csv"

    SHOW = True
    SAVE = True
    
    FIGSIZE = (8.5, 10)  # cm
    DPI = 600

    plt.rc("font", size=8.5)
    plt.rc("font", family="Times New Roman")

    main(input_file)
