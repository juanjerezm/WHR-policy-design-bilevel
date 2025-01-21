import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import utilities as utils
import utilities_plotting as utils_plot

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

    runs = utils.RunCollection(input_path).runs

    for run in runs:
        run.load_result(var)
        multiply_by(run, MULTIPLY_BY)
        run.results["scenario"] = run.scenario

    data = process_results(runs)
    fig, ax = plt.subplots(figsize=(WIDTH / 2.54, HEIGHT / 2.54))
    data.plot(kind="bar", stacked=True, color=color_map, legend=False, ax=ax)

    ax.set_title(runs[0].project, fontsize=11, fontweight='bold')

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
        title="Fuel",
        title_fontproperties={"weight": "bold"},
    )

    _, legend_height = utils_plot.legend_dimensions(fig, legend)
    plt.subplots_adjust(wspace=0.1, bottom=(y_down + legend_height))


    plt.show()

    return


def multiply_by(run, par):
    if not par:
        return run.results

    file: Path = run.outdir / "csv" / f"{par}.csv"
    df = pd.read_csv(file)
    df = df.rename(columns={"value": par})
    run.results = run.results.rename(columns={"level": "heat production"})
    run.results = pd.merge(run.results, df, on=["case", "J"], how="outer")
    run.results = run.results.fillna(0)
    run.results["level"] = run.results["heat production"] * run.results[par]
    run.results = run.results.drop(columns=["heat production", par])
    return df


def process_results(runs):
    df = pd.concat([run.results for run in runs])
    df["F"] = df["J"].map(fuel_map)
    df = utils.aggregate(df, categories=["scenario", "case", "F"], sums=["level"])
    df = utils.diff(df, ref_col="case", ref_item="baseline", diff_col="level")
    df["level"] = df["level"] * SCALE
    df = utils.exclude_empty_category(df, "F")
    df = df.drop(columns=["case"])
    df = df.pivot(index="scenario", columns="F", values="level")
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

    MULTIPLY_BY = "beta_b"
    FREE_YAXIS = False

    WIDTH   = 9 # cm
    HEIGHT  = 11 # cm
    Y_TITLE = "Electricity Cogeneration Change [TWh/year]"
    Y_RANGE = (-0.8, 0.00)
    Y_STEP  = 0.1

    SCALE = 8760 / 73 * 1e-6  # Temporal adjustement, and MWh -> TWh

    fuel_map, color_map = mapping_values()

    main("x_h")
