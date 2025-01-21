from pathlib import Path
import pandas as pd
import utilities as utils


def mapping_values():
    df = pd.read_csv("scripts/python/mapping_values.csv")

    map_fuels = dict(zip(df["name_internal"], df["fuel category"]))
    map_colors = dict(zip(df["fuel category"], df["color"]))

    print(map_fuels)
    return map_fuels, map_colors


def deficit(input_path, var):
    """
    Entry point of the program.
    """

    runs = utils.RunCollection(input_path).runs

    for run in runs:
        run.load_result(var)
        multiply_by(run, 'beta_b')
        run.results["scenario"] = run.scenario

    data = process_results(runs)

    # sum over columns of data
    data = data.sum(axis=1)
    data = data.to_frame(name='Electricity\n(CPH-deficit)')

    return data


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
    fuel_map, color_map = mapping_values()

    df = pd.concat([run.results for run in runs])
    df["F"] = df["J"].map(fuel_map)
    df = utils.aggregate(df, categories=["scenario", "case", "F"], sums=["level"])
    df = utils.diff(df, ref_col="case", ref_item="baseline", diff_col="level")
    SCALE = 8760 / 73 * 1e-6  # Temporal adjustement, and MWh -> TWh

    df["level"] = df["level"] * SCALE
    df = utils.exclude_empty_category(df, "F")
    df = df.drop(columns=["case"])
    df = df.pivot(index="scenario", columns="F", values="level")
    return df
