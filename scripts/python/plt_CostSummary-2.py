import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import utilities as utils
import utilities_plotting as utils_plot
from pathlib import Path

def create_subplot(ax, df, r_e, r_c, is_bottom_row, is_left_column, is_top_row):
    bars = df.plot.barh(
        stacked=True,
        ax=ax,
        color=['#77AADD','#EE8866','#EEDD88'],
        zorder=3,
        legend=False,
        width=0.5,
    )

    systemic_values = df["Consumer Cost"] + df["subsidy cost"] + df["tax revenue"]
    policy_net = df["subsidy cost"] + df["tax revenue"]
    y_positions = np.arange(len(df))

    nan_mask = systemic_values.isna()

    # Plot a scatter plot for systemic values
    scatter_systemic = ax.scatter(
        systemic_values[~nan_mask],
        y_positions[~nan_mask],
        s=20,
        edgecolor="none",
        facecolor="black",
        linewidth=0,
        zorder=5,
    )

    # Plot a scatter plot for net policy values
    scatter_net = ax.scatter(
        policy_net[~nan_mask],
        y_positions[~nan_mask],
        s=30,
        marker="D",
        edgecolor="gray",
        facecolor="none",
        zorder=5,
    )

    # Plot a different marker for NaN values
    scatter_nan = ax.scatter(
        [0]*nan_mask.sum(),
        y_positions[nan_mask],
        s=25,
        color="red",
        marker='x',
        zorder=5,
    )

    # Set y-axis labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df["Scenario"])

    # Apply subplot properties
    set_subplot_properties(ax, r_e, r_c, is_bottom_row, is_left_column, is_top_row)

    return bars, scatter_systemic, scatter_net, scatter_nan


def set_subplot_properties(ax, r_e, r_c, is_bottom_row, is_left_column, is_top_row):
    # Set x-axis limits and ticks
    ax.set_xlim(-0.25, 0.40+1e-3)
    major_ticks = np.arange(-0.2, 0.40 + 1e-3, 0.1)
    minor_ticks = np.arange(-0.2, 0.40 + 1e-3, 0.05)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)

    # Format x-axis labels
    if is_bottom_row:
        ax.set_xlabel("Cost difference (% of baseline)")
        ax.set_xticklabels([f"{x*100:+.0f}%" for x in major_ticks], rotation=90, fontsize=8)
    else:
        ax.set_xlabel("")
        ax.set_xticklabels([])

    # Set y-axis label for left column
    if is_left_column:
        r_e_formatted = f"{r_e - 100:+d}%"  # Format Re as requested
        ax.set_ylabel(
            f"{r_e_formatted}", fontweight="bold", fontsize=10, rotation=90
        )

    # Set title for top row
    if is_top_row:
        r_c_formatted = f"{r_c - 100:+d}%"  # Format Rc as requested
        ax.set_title(f"{r_c_formatted}", fontweight="bold", fontsize=10)

    # Remove top and right spines for a cleaner look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

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

    # Plot each subplot
    for row, r_e in enumerate(r_e_values):
        for col, r_c in enumerate(r_c_values):
            ax = axs[row, col]
            df = utils.filter(data, {"R_e": [r_e], "R_c": [r_c]})
            df = df[["Scenario", "Consumer Cost", "subsidy cost", "tax revenue"]]

            if not df.empty:
                bars, scatter_systemic, scatter_net, scatter_nan = create_subplot(
                    ax,
                    df,
                    r_e,
                    r_c,
                    is_bottom_row=(row == len(r_e_values) - 1),
                    is_left_column=(col == 0),
                    is_top_row=(row == 0),
                )

    (_, _, x_center), (y_down, _, y_center) = utils_plot.axes_coordinates(axs)

    # Common labels
    fig.supylabel('Carbon Emissions Limit', fontsize=10, fontweight='bold', y=y_center+0.05)
    fig.suptitle('Consumer Cost Limit', fontsize=10, fontweight='bold',x=x_center+0.02)

    # Create a single legend for the entire figure
    legend = fig.legend(
        [bars.containers[0][0], bars.containers[1][0], bars.containers[2][0], scatter_net, scatter_systemic, scatter_nan],
        ["Consumer Cost", "Policy Cost (Subsidy Expense)", "Policy Cost (Tax Revenue)", "Net Policy Cost", "Net Systemic Cost", "Infeasible"],
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(x_center, 0.0),
    )
    
    plt.tight_layout()
    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(top=0.9, wspace=0.15, hspace=0.3, bottom=(y_down + legend_height))

    return fig


def main(file_path):
    data = pd.read_csv(file_path)
    data = utils.filter(data, {"Scenario": ["C", "D", "E"]})

    # Substract 1 to show the difference from the baseline
    data["Consumer Cost"] = data["Consumer Cost"] - 1

    r_e_values = sorted(list(set(data["R_e"])), reverse=True)
    r_c_values = sorted(list(set(data["R_c"])))

    data["Scenario"] = pd.Categorical(data["Scenario"])
    data = data.sort_values("Scenario", ascending=False)
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
        plt.savefig(outdir / "CostSummary-2.png", dpi=DPI, bbox_inches="tight")
        print(f"---> Plot saved to {outdir}CostSummary-2.png")
    if SHOW:
        plt.show()


if __name__ == "__main__":

    basedir = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article"
    outdir = basedir / "illustrations" / "plots"
    input_file = basedir / "consolidated-results" / "CostSummary.csv"

    SHOW = True
    SAVE = True
    
    FIGSIZE = (18.5, 11)  # cm
    DPI = 600

    plt.rc("font", size=8.5)
    plt.rc("font", family="Times New Roman")

    main(input_file)
