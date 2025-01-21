import matplotlib.pyplot as plt
import pandas as pd
from utilities import RunInfo, RunCollection, add_fuel_column
import argparse
from pathlib import Path
import sys

import utilities_plotting as utils_plot

import utilities as utils

# ----- Matplotlib settings -----
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 8


def mapping_values():
    df = pd.read_csv("scripts/python/mapping_values.csv")
    df["fuel category"] = df["fuel category"].str.replace("\\n", "\n")
    map_fuels = dict(zip(df["name_internal"], df["fuel category"]))
    map_colors = dict(zip(df["fuel category"], df["color"]))

    return map_fuels, map_colors

def main(var):
    """
    Entry point of the program.
    """

    args = parse_args()

    # Check if the argument was provided, otherwise ask interactively
    if args.input_path:
        input_path = args.input_path
    else:
        input_path = Path(
            input("Enter the path to the CSV file containing scenarios: ")
        )

    # Check if the file exists
    if not input_path.exists():
        sys.exit("ERROR: Input csv-file not found, script has stopped.")

    runs = RunCollection(input_path).runs

    for run in runs:
        run.load_result(var)
        multiply_by(run, MULTIPLY_BY)
        run.results["scenario"] = run.scenario

    data = process_results(runs)
        
    fig, ax = plt.subplots(figsize=(FIGSIZE[0] / 2.54, FIGSIZE[1] / 2.54))
    data.plot(kind="bar", stacked=True, color=color_map, legend=False, ax=ax, width=1.0)

    if PLOT_TITLE:
        ax.set_title(f'{runs[0].project}, {SCENARIO}, {CASE}', fontsize=11, fontweight='bold')
    
    ax.set_xlim(0,len(data)-1)
    ax.set_xticks([])
    ax.set_xlabel('Timesteps', fontweight='bold')

    if not FREE_YAXIS:
        utils_plot.format_yaxis([ax], Y_RANGE, Y_STEP, Y_TITLE)

    (_, _, x_center), (y_down, _, _) = utils_plot.axes_coordinates([ax])

    handles, labels = utils_plot.get_legend_elements([ax])

    legend = fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(x_center, 0),
        bbox_transform=fig.transFigure,
        ncol=2,
        title="Fuel Category",
        title_fontproperties={"weight": "bold"},
    )

    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(wspace=0.1, bottom=(y_down + legend_height))

    if save:
        output_path = outdir / f"{plot_name}.png"
        plt.savefig(output_path, dpi=DPI, bbox_inches='tight', pad_inches=0.05)
        print(f"Plot saved to {output_path}")
    if show:
        plt.show()

    return

def multiply_by(run, par):
    if not par:
        return run.results

    file: Path = run.outdir / "csv" / f"{par}.csv"
    df = pd.read_csv(file)
    df = df.rename(columns={"value": par})
    run.results = run.results.rename(columns={"level": "heat production"})
    run.results = pd.merge(run.results, df, on=["case", "T", "J"], how="outer")
    run.results = run.results.fillna(0)
    run.results["level"] = run.results["heat production"] * run.results[par]
    run.results = run.results.drop(columns=["heat production", par])
    return df


def process_results(runs):
    df = pd.concat([run.results for run in runs])
    df["F"] = df["J"].map(fuel_map)
    df = utils.filter(df, include={'case': CASE, 'scenario': SCENARIO})
    df = utils.aggregate(df, categories=["T", "F"], sums=["level"])
    df["level"] = df["level"] * SCALE
    df = utils.exclude_empty_category(df, "F")
    df = df.pivot(index="T", columns="F", values="level")
    df = sorting_units(df)
    return df

def sorting_units(df):
    capacity = df.max()
    production = df.sum()
    utilization_factor = production / (capacity * len(df))
    sorted_units = utilization_factor.sort_values(ascending=False)
    df = df[sorted_units.index]

    return df

def parse_args():
    """
    Parse command line arguments for submitting jobs to HPC.
    """
    parser = argparse.ArgumentParser(description="Submit jobs to HPC")
    parser.add_argument(
        "--input_path", type=Path, help="Path to the CSV file containing scenarios"
    )
    return parser.parse_args()


if __name__ == "__main__":
    
    show = True
    save = True

    # Get the user's home directory
    outdir = Path.home() / "OneDrive - Danmarks Tekniske Universitet" / "Papers" / "J3 - article" / "illustrations" / "plots"


    # outdir = Path(r"C:\Users\juanj\OneDrive - Danmarks Tekniske Universitet\Papers\J3 - article\illustrations\plots")
    plot_name = "tsHeatProdAbs_Baseline"

    CASE = "baseline"
    # SCENARIO = "A_095_100"
    SCENARIO = "A_090_100"

    MULTIPLY_BY = ""
    FREE_YAXIS = False

    DPI = 600
    FIGSIZE = (8.5, 9) # cm

    PLOT_TITLE = False
    Y_TITLE = "Heat Production (GWh/h)"
    Y_RANGE = (0, +12)
    Y_STEP  = 2.0
    SCALE = 1 * 1e-3  # MWh -> GWh

    
    fuel_map, color_map = mapping_values()

    main('x_h')
