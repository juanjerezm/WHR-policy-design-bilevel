import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import utilities as utils
import utilities_plotting as utils_plot
import seaborn as sns
from pathlib import Path


def create_subplot(ax, ax2, df, r_e, r_c, is_bottom_row, is_left_column, is_top_row):
    df = df.pivot(index="Scenario", columns="OperationalSummarySet", values="value")
    df = df.sort_index(ascending=False)

    # Plot capacity bars
    bars_capacity = ax.barh(
        df.index,
        df["Capacity"],
        color=sns.color_palette("colorblind")[1],
        label="Capacity",
        zorder=1,
    )

    # Overlay production hatch (as share of capacity bar)
    bars_production = ax.barh(
        df.index,
        df["Capacity"] * df["Capacity Factor"],
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
        [1000] * nan_mask.sum(),
        y_positions[nan_mask],
        s=15,
        color="red",
        marker="x",
        zorder=5,
    )

    # Set y-axis labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df.index)

    # Apply subplot properties
    set_subplot_properties(ax, ax2, r_e, r_c, is_bottom_row, is_left_column, is_top_row)

    return bars_capacity, bars_production, scatter_nan


def set_subplot_properties(
    ax, ax2, r_e, r_c, is_bottom_row, is_left_column, is_top_row
):
    # Set x-axis limits and ticks
    ax.set_xlim(0, 2000)
    major_ticks_primary = np.arange(0, 2000 + 1e-3, 500)
    minor_ticks_primary = np.arange(0, 2000 + 1e-3, 250)
    ax.set_xticks(major_ticks_primary)
    ax.set_xticks(minor_ticks_primary, minor=True)

    ax2.set_xlim(0, 2 * 8760 / 1000) # Comment if removing secondary axis
    major_ticks_secondary = np.arange(
        0, 2 * 8760 / 1000 + 1e-3, 2 * 8760 / 1000 * 1 / 4
    ) # Comment if removing secondary axis
    minor_ticks_secondary = np.arange(
        0, 2 * 8760 / 1000 + 1e-3, 2 * 8760 / 1000 * 1 / 8
    ) # Comment if removing secondary axis
    ax2.set_xticks(major_ticks_secondary) # Comment if removing secondary axis
    ax2.set_xticks(minor_ticks_secondary, minor=True) # Comment if removing secondary axis

    # Bottom row: set primary x-axis ticks and labels
    if is_bottom_row:
        ax.set_xlabel("WHR Capacity (GW)")
        ax.set_xticklabels([f"{x/1000:.1f}" for x in major_ticks_primary], rotation=0)
    else:
        ax.set_xlabel("")
        ax.set_xticklabels([])

    # Top row: set Consumer Cost title, as well as secondary x-axis ticks and labels
    if is_top_row:
        r_c_formatted = f"{r_c - 100:+d}%"
        ax.set_title(f"{r_c_formatted}", fontweight="bold", fontsize=10)
        ax2.set_xticklabels([f"{x:.1f}" for x in major_ticks_secondary], rotation=0) # Comment if removing secondary x-axis
        ax2.set_xlabel("WHR Production (TWh/year)") # Comment if removing secondary x-axis
    else: # Comment if removing secondary x-axis
        ax2.set_xlabel("") # Comment if removing secondary x-axis
        ax2.set_xticklabels([]) # Comment if removing secondary x-axis

    # Set y-axis label for left column
    if is_left_column:
        r_e_formatted = f"{r_e - 100:+d}%"
        ax.set_ylabel(f"{r_e_formatted}", fontweight="bold", fontsize=10, rotation=90)

    # Remove top and right spines for a cleaner look
    # ax.spines["top"].set_visible(False) # Uncomment if removing secondary x-axis
    # ax.spines["right"].set_visible(False) # Uncomment if removing secondary x-axis

    # Add grid lines
    ax.grid(axis="x", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)
    ax.grid(axis="x", which="minor", linestyle="--", linewidth=0.3, alpha=0.5, zorder=0)
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)


def create_plot(data, r_e_values, r_c_values):
    fig, axs = plt.subplots(
        len(r_e_values),
        len(r_c_values),
        figsize=(FIGSIZE[0] / 2.54, FIGSIZE[1] / 2.54),
        sharey=True,
        sharex=True,
    )

    axs_secondary = np.array([[ax.twiny() for ax in row] for row in axs])

    # Plot each subplot
    for row, r_e in enumerate(r_e_values):
        for col, r_c in enumerate(r_c_values):
            ax_primary = axs[row, col]
            ax_secondary = axs_secondary[row, col]
            df = utils.filter(
                data,
                {
                    "R_e": [r_e],
                    "R_c": [r_c],
                    "OperationalSummarySet": ["Capacity", "Capacity Factor"],
                },
            )

            df = df[["Scenario", "OperationalSummarySet", "value"]]

            if not df.empty:
                bars_capacity, bars_production, scatter_nan = create_subplot(
                    ax_primary,
                    ax_secondary,
                    df,
                    r_e,
                    r_c,
                    is_bottom_row=(row == len(r_e_values) - 1),
                    is_left_column=(col == 0),
                    is_top_row=(row == 0),
                )

    (_, _, x_center), (y_down, _, y_center) = utils_plot.axes_coordinates(axs)

    # Common labels
    fig.supylabel("Carbon Emissions Limit", fontsize=10, fontweight="bold", y=y_center)
    fig.suptitle(
        "Consumer Cost Limit", fontsize=10, fontweight="bold", x=x_center + 0.02
    )

    # Create a single legend for the entire figure
    legend = fig.legend(
        [bars_capacity, bars_production, scatter_nan],
        ["WHR Capacity", "WHR Production", "Infeasible"],
        loc="lower center",
        ncol=5,
        bbox_to_anchor=(x_center, 0.0),
    )

    plt.tight_layout()
    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(top=0.82, wspace=0.15, hspace=0.3, bottom=(y_down + legend_height))

    return fig


def main(file_path):
    data = pd.read_csv(file_path)
    data = utils.filter(data, {"Scenario": ["C", "D", "E"]})

    r_e_values = sorted(list(set(data["R_e"])), reverse=True)
    r_c_values = sorted(list(set(data["R_c"])))

    data["Scenario"] = pd.Categorical(data["Scenario"], ordered=True)
    data = utils.rename_values(
        data,
        {
            "Scenario": {
                "C": "OPEX Sub. + CT",
                "D": "CAPEX Sub. + CT",
                "E": "CT only",
            }
        },
    )

    fig = create_plot(data, r_e_values, r_c_values)

    if SAVE:
        plt.savefig(outdir / "HRSummary-2-optA.png", dpi=DPI, bbox_inches="tight")
        print(f"---> Plot saved to {outdir}HRSummary-2-optA.png")
    if SHOW:
        plt.show()


if __name__ == "__main__":

    basedir = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article"
    outdir = basedir / "illustrations" / "plots"
    input_file = basedir / "consolidated-results" / "HROperationSummary.csv"

    SHOW = True
    SAVE = True
    
    FIGSIZE = (18.5, 11)  # cm
    DPI = 600

    plt.rc("font", size=8.5)
    plt.rc("font", family="Times New Roman")

    main(input_file)
