from itertools import product
import numpy as np
import pandas as pd
import utilities as utils


def load_results(Collection, var):
    runs = Collection.runs
    for run in runs:
        run.load_result(var)
        run.results["project"], run.results["r_carbon"], run.results["r_cost"] = (
            run.scenario.split("_")
        )
    return pd.concat([run.results for run in runs])


def PolicyCost(Collection):
    SCALE = 8760 / 73 * 1e-6
    df = load_results(Collection, "SummaryPolicy")
    df = utils.filter(df, include={"Case": "policy"})
    df = utils.filter(
        df,
        include={
            "PolicySummarySet": ["subsidy cost", "tax revenue", "net policy cost"]
        },
    )
    df.loc[df["PolicySummarySet"] == "tax revenue", "value"] *= -1
    df["value"] = df["value"] * SCALE
    df = df[["project", "r_carbon", "r_cost", "PolicySummarySet", "value"]]
    return df


def NetHeatingCost(Collection, Case):
    SCALE = 8760 / 73 * 1e-6
    df = load_results(Collection, "SummaryPolicy")
    df = utils.filter(df, include={"PolicySummarySet": "heating cost - net"})
    df = utils.filter(df, include={"Case": Case})
    df["value"] = df["value"] * SCALE
    df = df[["project", "r_carbon", "r_cost", "PolicySummarySet", "value"]]
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

    outdir = r"C:\Users\jujmo\OneDrive - Danmarks Tekniske Universitet\Papers\J3 - article\consolidated-results"
    projects = ["A", "B", "C", "D", "E"]

    dfs = []

    for project in projects:
        input_path = f"data/{project}/runInfo.csv"

        Collection = utils.RunCollection(input_path)
        Collection.keep_feasible_runs()

        consumer_pre = NetHeatingCost(Collection, "baseline")
        consumer_post = NetHeatingCost(Collection, "policy")
        policy = PolicyCost(Collection)

        consumer_n = pd.merge(
            consumer_post,
            consumer_pre,
            on=["project", "r_carbon", "r_cost", "PolicySummarySet"],
            suffixes=("_post", "_pre"),
        )
        consumer_n["value"] = consumer_n["value_post"] / consumer_n["value_pre"]
        consumer_n = consumer_n.drop(columns=["value_post", "value_pre"])
        consumer_n = utils.rename_values(
            consumer_n, {"PolicySummarySet": {"heating cost - net": "Consumer Cost"}}
        )

        policy_n = pd.merge(
            policy,
            consumer_pre,
            on=["project", "r_carbon", "r_cost"],
            suffixes=("_df2", "_df1"),
        )
        policy_n["value"] = policy_n["value_df2"] / policy_n["value_df1"]
        policy_n = policy_n.drop(
            columns=["PolicySummarySet_df1", "value_df2", "value_df1"]
        )
        policy_n = policy_n.rename(columns={"PolicySummarySet_df2": "PolicySummarySet"})
        policy_n = utils.rename_values(
            policy_n, {"PolicySummarySet": {"net policy cost": "Policy Cost"}}
        )

        df = pd.concat([consumer_n, policy_n], ignore_index=True)
        df = df.sort_values(by=["project", "r_carbon", "r_cost"]).reset_index(drop=True)
        dfs.append(df)

    results = pd.concat(dfs, ignore_index=True)
    results["value"] = results["value"].round(3)


    results = results.pivot_table(
        index=["project", "r_carbon", "r_cost"],
        columns="PolicySummarySet",
        values="value",
        fill_value=0,
    ).reset_index()

    results = fill_nans(results)

    results = results.rename(
        columns={"project": "Scenario", "r_carbon": "R_e", "r_cost": "R_c"}
    )

    results.to_csv(f"{outdir}/CostSummary.csv", index=False, na_rep="NaN")
