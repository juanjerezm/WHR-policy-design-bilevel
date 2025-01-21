from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
import utilities as utils


# TODO This function has been hacked to work with missing files. This is an issue of on the gams side, because the GDX is not produced if the parameter is empty.
def load_results(Collection, var): 
    runs = Collection.runs
    for run in runs:
        try:
            run.load_result(var)
        except FileNotFoundError:
            columns = ["project", "r_carbon", "r_cost", "Case", "OperationalSummarySet", "value"]
            run.results = pd.DataFrame(columns=columns)
        run.results["project"], run.results["r_carbon"], run.results["r_cost"] = (
            run.scenario.split("_")
        )
    return pd.concat([run.results for run in runs])


def HROperationSummary(Collection, Case):
    SCALE = 8760 / 73 * 1e-6    # Timestep scaling and MWh to TWh conversion
    df = load_results(Collection, "SummaryOperations")
    df = utils.filter(df, include={"Case": Case})
    df = utils.aggregate(df, categories=["project", "r_carbon", "r_cost", "Case", "OperationalSummarySet"], sums=["value"])
    df.loc[df["OperationalSummarySet"] == "Production", "value"] *= SCALE
    return df


def fill_nans(df):
    # Generate a DataFrame with all combinations of r_carbon, r_cost, and PolicySummarySet
    r_carbon_vals = df["r_carbon"].unique()
    r_cost_vals = df["r_cost"].unique()
    project_vals = df["project"].unique()

    # Create a DataFrame with all combinations
    all_combinations = pd.DataFrame(
        list(product(project_vals, r_carbon_vals, r_cost_vals)),
        columns=["project", "r_carbon", "r_cost"],
    )

    # Merge the complete combinations with the original dataframe
    df = pd.merge(
        all_combinations,
        df,
        on=["project", "r_carbon", "r_cost"],
        how="left",
    )

    return df


if __name__ == "__main__":

    outdir = Path.home() / "OneDrive - Danmarks Tekniske Universitet/Papers/J3 - article/consolidated-results"

    projects = ["A", "B", "C", "D", "E"]

    dfs = []

    for project in projects:
        input_path = f"data/{project}/runInfo.csv"

        Collection = utils.RunCollection(input_path)
        Collection.keep_feasible_runs()

        # HR_pre = HROperationSummary(Collection, "baseline")
        HR_pro = HROperationSummary(Collection, "policy")
        print(project)
        print(HR_pro)

        # consumer_n = pd.merge(
        #     HR_pro,
        #     HR_pre,
        #     on=["project", "r_carbon", "r_cost", "OperationalSummarySet"],
        #     suffixes=("_post", "_pre"),
        # )
        # consumer_n["value"] = consumer_n["value_post"] / consumer_n["value_pre"]
        # consumer_n = consumer_n.drop(columns=["value_post", "value_pre"])
        # consumer_n = utils.rename_values(
        #     consumer_n, {"PolicySummarySet": {"heating cost - net": "Consumer Cost"}}
        # )


        df = HR_pro
        # df = df.sort_values(by=["project", "r_carbon", "r_cost"]).reset_index(drop=True)
        dfs.append(df)

    results = pd.concat(dfs, ignore_index=True)
    results["value"] = results["value"].round(3)

    # Calculate capacity factor. It is the division of the production by the installed capacity (both in OperationalSummarySet 

    results = results.pivot_table(index=['project', 'r_carbon', 'r_cost', 'Case'], columns='OperationalSummarySet', values='value', fill_value=0).reset_index()

    results["Capacity Factor"] = results["Production"] / results["Capacity"] * 1e6/8760
    results["Capacity Factor"] = results["Capacity Factor"].round(3)

    results = results.melt(id_vars=["project", "r_carbon", "r_cost", "Case"], value_vars=["Production", "Capacity", "Capacity Factor"], var_name="OperationalSummarySet", value_name="value")

    results = fill_nans(results)

    results = results.rename(
        columns={"project": "Scenario", "r_carbon": "R_e", "r_cost": "R_c"}
    )

    results.to_csv(f"{outdir}/HROperationSummary.csv", index=False, na_rep="NaN")
