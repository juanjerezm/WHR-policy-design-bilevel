#!/usr/bin/env python3

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import utilities as utils
import utilities_plotting as utils_plot

# ------------------------------------------------------------
# ModelRun & Collection as before, aggregator() accepts a "scale" argument
# ------------------------------------------------------------

@dataclass
class ModelRun:
    id: str
    project: str = field(init=False)
    ratio_e: int = field(init=False)
    ratio_c: int = field(init=False)
    outdir: Path = field(init=False)
    infeasible: bool = field(init=False, default=False)
    results: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self._parse_id()
        self.outdir = Path("results") / self.project / self.id
        self.infeasible = not (self.outdir / "csv").exists()

    def _parse_id(self) -> None:
        """Extract and assign project, ratio_e, and ratio_c from the id."""
        parts = self.id.split("_")
        if len(parts) != 3:
            raise ValueError(f"Invalid run ID: {self.id}")
        self.project = parts[0]
        self.ratio_e = int(parts[1])
        self.ratio_c = int(parts[2])

    def __str__(self) -> str:
        return f"-> Run ID: {self.id}"

    def load_result(self, var: str, multiplier: Optional[str] = None) -> None:
        if self.infeasible:
            self.results = pd.DataFrame()
            print(f"Run {self.id} is infeasible. Skipping results for {var}.")
            return

        file = self.outdir / "csv" / f"{var}.csv"
        if not file.exists():
            self.results = pd.DataFrame()
            print(f"No {var}.csv for run {self.id}")
        else:
            self.results = pd.read_csv(file)
            if multiplier:
                self._multiply_by(multiplier)

    def _multiply_by(self, par: str) -> None:
        file = self.outdir / "csv" / f"{par}.csv"
        if not file.exists():
            print(f"Multiplier file {file} not found. Skipping multiplication.")
            return

        self.results = self.results.rename(columns={"level": "original"})
        df = pd.read_csv(file)
        df = df.rename(columns={"value": par})

        # Merge based on the type of `par`
        if par == "beta_b":
            self.results = pd.merge(self.results, df, on=["case", "J"], how="outer")
        else:
            self.results = pd.merge(
                self.results, df, on=["case", "T", "J"], how="outer"
            )

        # Fill NaN, compute new 'level'
        self.results = self.results.fillna(0)
        self.results["level"] = self.results["original"] * self.results[par]
        self.results = self.results.drop(columns=["original", par])

    def aggregate(self, scale: float) -> None:
        """Aggregates and applies the given scale factor to each run's results."""
        if self.infeasible:
            self.results = pd.DataFrame()
            print(f"Run {self.id} is infeasible. Skipping aggregation.")
            return

        map_fuels, _ = mapping_values()
        df = self.results
        df["F"] = df["J"].map(map_fuels)
        df = utils.aggregate(df, categories=["case", "F"], sums=["level"])
        df = utils.diff(df, ref_col="case", ref_item="baseline", diff_col="level")
        df["level"] = df["level"] * scale
        df = df.drop(columns=["case"])
        df["project"] = self.project
        df["R_e"] = self.ratio_e
        df["R_c"] = self.ratio_c
        self.results = df


@dataclass
class Collection:
    file: Path
    ids: List[str] = field(init=False, default_factory=list)
    projects: List[str] = field(init=False, default_factory=list)
    ratios_e: List[int] = field(init=False, default_factory=list)
    ratios_c: List[int] = field(init=False, default_factory=list)
    runs: List[ModelRun] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        df = pd.read_csv(self.file, header=None)
        self.ids = df[0].tolist()
        self._unique_attrs()
        self.runs = [ModelRun(id=id) for id in self.ids]

    def _unique_attrs(self) -> None:
        projects_set = set()
        ratios_e_set = set()
        ratios_c_set = set()

        for id in self.ids:
            project, ratio_e, ratio_c = id.split("_")
            projects_set.add(project)
            ratios_e_set.add(int(ratio_e))
            ratios_c_set.add(int(ratio_c))

        self.projects = sorted(projects_set)
        self.ratios_e = sorted(ratios_e_set)
        self.ratios_c = sorted(ratios_c_set)


def mapping_values():
    df = pd.read_csv("scripts/python/mapping_values.csv")
    df["fuel category"] = df["fuel category"].str.replace("\\n", "\n")
    map_fuels = dict(zip(df["name_internal"], df["fuel category"]))
    map_colors = dict(zip(df["fuel category"], df["color"]))
    return map_fuels, map_colors


# -------------------------------------------------------------------
# Draws a single subplot: one project from one collection
# -------------------------------------------------------------------
def make_subplot(ax, collection, project, col_index):
    """
    Draws a single subplot for the given `project` using `collection`.
    col_index is the column # in the overall figure, which can help
    us do per-column logic if desired.
    Returns the bar container (bars) and possibly a scatter handle (scatter_nan).
    """
    _, map_colors = mapping_values()

    # Filter + pivot
    df = pd.concat([run.results for run in collection.runs if run.project == project])
    if df.empty:
        return None, None

    df = df[["R_e", "F", "level"]]
    df = df.pivot(index="R_e", columns="F", values="level")
    df = df.reindex(collection.ratios_e)  # ensures consistent row order
    df.index = df.index.map(lambda x: f"-{100 - x}%")

    # Build list of colors from the mapping
    color_list = []
    for fuelcat in df.columns:
        color_list.append(map_colors.get(fuelcat, "black"))

    # Stacked bar chart
    bars = df.plot.barh(
        stacked=True,
        ax=ax,
        legend=False,   # no local legend
        label=df.columns,
        color=color_list,
    )

    # Mark infeasible runs
    infeasible_runs = [
        run for run in collection.runs if run.project == project and run.infeasible
    ]
    if infeasible_runs:
        y_positions = [collection.ratios_e.index(run.ratio_e) for run in infeasible_runs]
        scatter_nan = ax.scatter(
            [0] * len(y_positions),
            y_positions,
            color="red",
            marker="x",
            label="Infeasible",
        )
    else:
        scatter_nan = None

    return bars, scatter_nan


# -------------------------------------------------------------------
# Helper to set each column's x-axis & label, but only on bottom row
# -------------------------------------------------------------------
def configure_xaxis(ax, col, row, nrows):
    """
    Different x-axis settings for each column (0,1,2).
    Only apply ax.set_xlabel(...) if row == nrows - 1 (bottom row).
    """
    if col == 0:
        # Column 0
        major_ticks_primary = np.arange(-24, 24 + 1e-3, 8)
        minor_ticks_primary = np.arange(-24, 24 + 1e-3, 8)
        ax.set_xlim(-24, 24)
        ax.set_xticks(major_ticks_primary)
        ax.set_xticks(minor_ticks_primary, minor=True)
        # Only label bottom row
        if row == nrows - 1:
            ax.set_xlabel("Change in heat production\n(TWh/year)")

    elif col == 1:
        # Column 1
        major_ticks_primary = np.arange(-28, 7 + 1e-3, 7)
        minor_ticks_primary = np.arange(-28, 7 + 1e-3, 7)
        ax.set_xlim(-28, 7)
        ax.set_xticks(major_ticks_primary)
        ax.set_xticks(minor_ticks_primary, minor=True)
        if row == nrows - 1:
            ax.set_xlabel("Change in fuel consumption\n(TWh/year)")

    elif col == 2:
        # Column 2
        major_ticks_primary = np.arange(-1.5, 0.3 + 1e-6, 0.3)
        minor_ticks_primary = np.arange(-1.5, 0.3 + 1e-6, 0.3)
        ax.set_xlim(-1.5, 0.3)
        ax.set_xticks(major_ticks_primary)
        ax.set_xticks(minor_ticks_primary, minor=True)
        if row == nrows - 1:
            ax.set_xlabel("Change in carbon emissions\n(Mt/year)")


# -------------------------------------------------------------------
# Main figure-building routine (multi-column approach)
# -------------------------------------------------------------------
def make_plot_multiple(collections):
    """
    Creates a single figure with subplots arranged in:
      Rows = distinct projects
      Columns = each of the given Collections.
    We assume each collection has the same .projects in the same order.
    """
    projects = collections[0].projects
    nrows = len(projects)
    ncols = len(collections)

    fig, axs = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        # figsize=(FIGSIZE[0] / 2.54 * ncols, FIGSIZE[1] / 2.54 * nrows),
        figsize =(18/2.54, 10/2.54),
        sharey=True,
    )

    # Force axs to be a 2D array
    if nrows == 1 and ncols == 1:
        axs = np.array([[axs]])
    elif nrows == 1:
        axs = axs[np.newaxis, :]
    elif ncols == 1:
        axs = axs[:, np.newaxis]

    all_handles = []
    all_labels = []

    # Plot
    for col, collection in enumerate(collections):
        for row, project in enumerate(projects):
            ax = axs[row, col]
            bars, scatter = make_subplot(ax, collection, project, col_index=col)

            # Only put "OPEX Subsidy"/"CAPEX Subsidy" text on the leftmost column
            if col == 0:
                ax.text(
                    -0.35, 0.5,
                    PROJECT_NAMES[project],
                    transform=ax.transAxes,
                    weight="bold",
                    va="center",
                    ha="center",
                    rotation=90,
                )
                ax.set_ylabel("Carbon Emissions Limit")
            else:
                ax.set_ylabel("")

            # Grid lines
            ax.grid(axis="x", which="major", linestyle="--", linewidth=0.5, alpha=0.5)
            ax.grid(axis="x", which="minor", linestyle="--", linewidth=0.3, alpha=0.5)
            ax.grid(axis="y", which="major", linestyle="--", linewidth=0.5, alpha=0.5)

            # Collect legend handles/labels
            handles, labels = ax.get_legend_handles_labels()
            for h, l in zip(handles, labels):
                if l not in all_labels:
                    all_labels.append(l)
                    all_handles.append(h)

            # Configure the x-axis (range/ticks). Only label the bottom row
            if FORMATTED_XAXIS:
                configure_xaxis(ax, col, row, nrows)

    (_, _, x_center), (y_down, _, _) = utils_plot.axes_coordinates(axs)

    # Single legend at the bottom
    legend = fig.legend(
        all_handles,
        all_labels,
        loc="lower center",
        ncol=4,
        bbox_to_anchor=(x_center, 0.0),
        title="Fuel Source Category",
        title_fontproperties={'weight': 'bold'}
    )

    plt.tight_layout()
    # Adjust if legend is cut off
    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(bottom=y_down + legend_height)

    return fig


# -------------------------------------------------------------------
# Main driver: builds the collections, sets per-column scale, calls make_plot_multiple
# -------------------------------------------------------------------
def main(inputfile, var, multipliers):
    """
    1) Build one Collection per multiplier
    2) Scale the runs appropriately per column
    3) Create the final multi-column figure
    4) Save/Show
    """
    # Example of three columns with different scales
    scale_per_column = [
        (8760/73) * 1e-6,  # MWh to TWh
        (8760/73) * 1e-6,  # MWh to TWh
        (8760/73) * 1e-6,  # t to Mt
    ]

    collections = []
    for col_idx, multiplier in enumerate(multipliers):
        c = Collection(file=Path(inputfile))
        for run in c.runs:
            run.load_result(var, multiplier)
            run.aggregate(scale=scale_per_column[col_idx])
        collections.append(c)

    # Build the multi-column figure
    fig = make_plot_multiple(collections)

    # Save or show
    if SAVE:
        plt.savefig(OUTDIR / f"{PLOTNAME}.png", dpi=DPI, bbox_inches="tight")
        print(f"Plot saved to {OUTDIR / PLOTNAME}.png")
    if SHOW:
        plt.show()


# -------------------------------------------------------------------
# Script entry point
# -------------------------------------------------------------------
if __name__ == "__main__":

    OUTDIR = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article" / "illustrations" / "plots"
    PLOTNAME = "HeatFuelEmissionSummary-1"
    SAVE = True
    SHOW = True

    FIGSIZE = (8.5, 10)  # cm
    DPI = 600
    FORMATTED_XAXIS = True

    PROJECT_NAMES = {
        "A": "OPEX Subsidy",
        "B": "CAPEX Subsidy",
        "C": "OPEX Sub. + CT",
        "D": "CAPEX Sub. + CT",
        "E": "CT only",
    }

    multipliers = [None, "alpha", "omega"]

    plt.rc("font", size=8.5)
    plt.rc("font", family="Times New Roman")
    main(inputfile="ModelRuns-1.csv", var="x_h", multipliers=multipliers)
