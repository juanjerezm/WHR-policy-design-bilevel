import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import utilities as utils
import utilities_plotting as utils_plot
from pathlib import Path

def create_subplot(ax, df,scenario):
    bars = df[["Consumer Cost", "subsidy cost"]].plot.barh(
        stacked=True,
        ax=ax,
        color=['#77AADD','#EE8866'],
        zorder=3,
        legend=False,
    )

    net_values = df["Consumer Cost"] + df["subsidy cost"]
    y_positions = np.arange(len(df))

    nan_mask = net_values.isna()

    # Plot a scatter plot for valid values
    scatter_valid = ax.scatter(
        net_values[~nan_mask],
        y_positions[~nan_mask],
        s=15,
        color="black",
        zorder=5,
    )

    # Plot a different marker for NaN values
    scatter_nan = ax.scatter(
        [0]*nan_mask.sum(),
        y_positions[nan_mask],
        s=10,
        color="red",
        marker='x',
        zorder=5,
    )

    # Format y-axes
    ax.set_yticks(y_positions)
    ax.set_yticklabels((df["R_e"] - 100).apply(lambda x: f"{x:+d}%"))
    ax.set_ylabel(f"Carbon Emissions Limit")
    ax.text(-0.3, 0.5, f"{scenario}", transform=ax.transAxes, weight="bold", va="center", ha="center", rotation=90)

    # Format x-axes
    ax.set_xlabel("Cost difference (% of baseline)")

    ax.set_xlim(-2, 4)

    major_ticks = np.arange(-2, 4.01, 1)
    minor_ticks = np.arange(-2, 4.01, 0.5)
    
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)  
    ax.set_xticklabels([f"{x*100:+.0f}%" for x in major_ticks], rotation=90, fontsize=8)

    # ax.set_title(f"{scenario}", fontweight="bold", fontsize=10)
    
    # Remove top and right spines for a cleaner look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add grid lines
    ax.grid(axis="x", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)
    ax.grid(axis="x", which="minor", linestyle="--", linewidth=0.3, alpha=0.5, zorder=0)
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)

    return bars, scatter_valid, scatter_nan


def create_plot(data, scenarios):
    fig, axs = plt.subplots(
        len(scenarios),  
        1,  
        figsize=(FIGSIZE[0] / 2.54, FIGSIZE[1] / 2.54),
        sharey=True,
        sharex=True,
    )

    # Plot each subplot
    for row, scenario in enumerate(scenarios):
        ax = axs[row]
        df = utils.filter(data, {"Scenario": [scenario]})
        df = df[["R_e", "Consumer Cost", "subsidy cost"]]

        if not df.empty:
            bars, scatter_valid, scatter_nan = create_subplot(
                ax,
                df,
                scenario
            )

    (_, _, x_center), (y_down, _, _) = utils_plot.axes_coordinates(axs)

    # Create a single legend for the entire figure
    legend = fig.legend(
        [bars.containers[0][0], bars.containers[1][0], scatter_valid, scatter_nan],
        ["Consumer Cost", "Subsidy Cost", "Net Systemic Cost", "Infeasible"],
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(x_center-0.02, 0.0),
    )
    
    plt.tight_layout()
    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(wspace=0.15, hspace=0.3, bottom=(y_down + legend_height))

    return fig


def main(file_path):
    data = pd.read_csv(file_path)
    data = utils.filter(data, include={"Scenario": ["A", "B"], "R_c": [100]})
    
    # Substract 1 to show the difference from the baseline
    data["Consumer Cost"] = data["Consumer Cost"] - 1

    data = utils.rename_values(data, {"Scenario": {"A": "OPEX Subsidy","B": "CAPEX Subsidy"}})

    scenarios = sorted(list(set(data["Scenario"])), reverse=True)


    fig = create_plot(data, scenarios)

    if SAVE:
        plt.savefig(outdir / "CostSummary-1.png", dpi=DPI, bbox_inches="tight")
        print(f"---> Plot saved to {outdir}CostSummary-1.png")
    if SHOW:
        plt.show()


if __name__ == "__main__":

    basedir = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article"
    outdir = basedir / "illustrations" / "plots"
    input_file = basedir / "consolidated-results" / "CostSummary.csv"

    SHOW = True
    SAVE = True
    
    FIGSIZE = (8.5, 10)  # cm
    DPI = 600

    plt.rc("font", size=8.5)
    plt.rc("font", family="Times New Roman")

    main(input_file)
