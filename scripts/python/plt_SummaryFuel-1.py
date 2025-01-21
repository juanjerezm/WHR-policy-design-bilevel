from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Optional
import numpy as np
import pandas as pd
import utilities as utils
import utilities_plotting as utils_plot
import matplotlib.pyplot as plt


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
            print(f"Run {self.id} is infeasible. Skipping loading results for {var}.")
            return

        file = self.outdir / "csv" / f"{var}.csv"

        if not file.exists():
            self.results = pd.DataFrame()
            print(f"This shouldn't occur... ID: {self.id}, var: {var}")
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

        # Fill NaN values, calculate the new 'level', and drop unnecessary columns
        self.results = self.results.fillna(0)
        self.results["level"] = self.results["original"] * self.results[par]
        self.results = self.results.drop(columns=["original", par])

    def aggregate(self):
        if self.infeasible:
            self.results = pd.DataFrame()
            print(f"Run {self.id} is infeasible. Skipping aggregation.")
            return

        map_fuels, _ = mapping_values()
        df = self.results
        df["F"] = df["J"].map(map_fuels)
        df = utils.aggregate(df, categories=["case", "F"], sums=["level"])
        df = utils.diff(df, ref_col="case", ref_item="baseline", diff_col="level")
        df["level"] = df["level"] * SCALE
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


def make_plot(collection):
    fig, axs = plt.subplots(
        len(collection.projects),
        1,
        figsize=(FIGSIZE[0] / 2.54, FIGSIZE[1] / 2.54),
        sharey=True,
        sharex=True,
    )

    # Lists to collect all unique handles and labels
    all_handles = []
    all_labels = []
    scatter_nan = None

    # Plot each subplot and collect handles/labels
    for row, project in enumerate(collection.projects):
        ax = axs[row]
        bars, scatter = make_subplot(ax, collection, project)

        # Get handles and labels from this axis, and add to collection if not already present
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if label not in all_labels:  # Use label to check for duplicates
                all_handles.append(handle)
                all_labels.append(label)

        # Keep track of scatter if it exists
        if scatter is not None:
            scatter_nan = scatter

    # Format x-axes
    if FORMATTED_XAXIS:
        major_ticks_primary = np.arange(-28, 7 + 1e-3, 7)
        minor_ticks_primary = np.arange(-28, 7 + 1e-3, 7)
        axs[-1].set_xlim(-28, 7)
        axs[-1].set_xticks(major_ticks_primary)
        axs[-1].set_xticks(minor_ticks_primary, minor=True)
        axs[-1].set_xlabel("Change in fuel consumption (TWh/year)")

    (_, _, x_center), (y_down, _, _) = utils_plot.axes_coordinates(axs)

    # Add scatter point if it exists and not already in handles
    if scatter_nan is not None and "Infeasible" not in all_labels:
        all_handles.append(scatter_nan)
        all_labels.append("Infeasible")

    # Create the combined legend
    legend = fig.legend(
        all_handles,
        all_labels,
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(x_center, 0.0),
    )

    plt.tight_layout()
    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(wspace=0.1, hspace=0.1, bottom=(y_down + legend_height))

    return fig

def make_subplot(ax, collection, project):
    _, map_colors = mapping_values()

    df = pd.concat([run.results for run in collection.runs if run.project == project])
    df = df[["R_e", "F", "level"]]
    df = df.pivot(index="R_e", columns="F", values="level")
    df = df.reindex(collection.ratios_e)  # This fills in missing rows with NaN
    df.index = df.index.map(lambda x: f"-{100 - x}%")

    bars = df.plot.barh(
        stacked=True,
        ax=ax,
        legend=False,
        label=df.columns,
        color=[map_colors[col] for col in df.columns],
    )

    infeasible_runs = [
        run for run in collection.runs if run.project == project and run.infeasible
    ]
    if infeasible_runs:
        y_positions = [
            collection.ratios_e.index(run.ratio_e) for run in infeasible_runs
        ]
        nan = ax.scatter(
            [0] * len(y_positions),
            y_positions,
            color="red",
            marker="x",
            label="Infeasible",
        )
    else:
        nan = None

        # Format y-axes
    ax.set_ylabel(f"Carbon Emissions Limit")
    ax.text(-0.25, 0.5, f"{PROJECT_NAMES[project]}", transform=ax.transAxes, weight="bold", va="center", ha="center", rotation=90)

    # Add grid lines
    ax.grid(axis="x", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)
    ax.grid(axis="x", which="minor", linestyle="--", linewidth=0.3, alpha=0.5, zorder=0)
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.5, alpha=0.5, zorder=0)

    return bars, nan

def main(inputfile, var, multiplier):
    collection = Collection(file=Path(inputfile))

    for run in collection.runs:
        run.load_result(var, multiplier)
        run.aggregate()

    fig = make_plot(collection)

    if SAVE:
        plt.savefig(OUTDIR / f"{PLOTNAME}.png", dpi=DPI, bbox_inches="tight")
        print(f"Plot saved to {OUTDIR / PLOTNAME}.png")
    if SHOW:
        plt.show()


if __name__ == "__main__":
    OUTDIR = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article" / "illustrations" / "plots"
    PLOTNAME = "FuelSummary-1"
    SAVE = True
    SHOW = True

    SCALE = 8760 / 73 * 1e-6 # Temporal scaling + MWh to TWh
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

    plt.rc("font", size=8.5)
    plt.rc("font", family="Times New Roman")

    main(inputfile="ModelRuns-1.csv", var="x_h", multiplier="alpha")
