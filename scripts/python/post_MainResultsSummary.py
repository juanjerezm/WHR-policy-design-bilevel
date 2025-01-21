import utilities as utils
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

HR_units = [
    "HR_S-near",
    "HR_S-far",
    "HR_M-near",
    "HR_M-far",
    "HR_L-near",
    "HR_L-far",
]


def HRCapacity(Collection, var):
    SCALE = 1
    df = load_results(Collection, var)
    df = utils.aggregate(
        df, categories=["scenario", "case", "r_carbon", "r_cost"], sums=["level"]
    )
    df = utils.diff(df, ref_col="case", ref_item="baseline", diff_col="level")
    df["level"] = df["level"] * SCALE
    df = df.drop(columns=["case"])
    df = df.pivot(index="r_carbon", columns="r_cost", values="level")
    df = df.sort_index(ascending=False)
    df = df.round(2)
    return df


def HRProduction(Collection, var):
    SCALE = 8760 / 73 * 1e-3
    df = load_results(Collection, var)
    df = utils.filter(df, include={"J": HR_units})
    df = utils.aggregate(
        df, categories=["scenario", "case", "r_carbon", "r_cost"], sums=["level"]
    )
    df = utils.diff(df, ref_col="case", ref_item="baseline", diff_col="level")
    df["level"] = df["level"] * SCALE
    df = df.drop(columns=["case"])
    df = df.pivot(index="r_carbon", columns="r_cost", values="level")
    df = df.sort_index(ascending=False)
    df = df.round(0)
    return df


def NetPolicyCost(Collection):
    SCALE = 8760 / 73 * 1e-6
    df = load_results(Collection, "SummaryPolicy")
    df = utils.filter(df, include={"PolicySummarySet": "net policy cost"})
    df = utils.filter(df, include={"Case": 'policy'})
    df = utils.aggregate(
        df,
        categories=["scenario", "Case", "r_carbon", "r_cost"],
        sums=["value"],  # this case is uppercase
    )
    df["value"] = df["value"] * SCALE
    df = df.drop(columns=["Case"])  # this case is uppercase
    # print(df.head(100))     # 

    # HERE ABOVE
    # THE PROBLEM IS THAT NOW I INCLUDED net policy cost in the baseline case as well

    df = df.pivot(index="r_carbon", columns="r_cost", values="value")
    df = df.sort_index(ascending=False)
    df = df.round(2)
    return df


def NetHeatingCost(Collection, Case):
    SCALE = 8760 / 73 * 1e-6
    df = load_results(Collection, "SummaryPolicy")
    df = utils.filter(df, include={"PolicySummarySet": "heating cost - net"})
    df = utils.filter(df, include={"Case": Case})
    df["value"] = df["value"] * SCALE
    df = df.drop(columns=["case"])
    df = df.pivot(index="r_carbon", columns="r_cost", values="value")
    df = df.sort_index(ascending=False)
    df = df.round(3)
    return df


def NetHeatingCostChange(Collection):
    heating_cost_baseline = NetHeatingCost(Collection, "baseline")
    heating_cost_policy = NetHeatingCost(Collection, "policy")
    heating_cost_change = heating_cost_policy - heating_cost_baseline
    heating_cost_change = heating_cost_change.round(3)
    return heating_cost_change


def PolicyCostRatio(Collection):
    policy_cost = NetPolicyCost(Collection)
    heating_cost_baseline = NetHeatingCost(Collection, "baseline")
    policy_cost_ratio = policy_cost / heating_cost_baseline
    policy_cost_ratio = policy_cost_ratio.round(3)
    return policy_cost_ratio


def ConsumerCostRatio(Collection):
    heating_cost_baseline = NetHeatingCost(Collection, "baseline")
    heating_cost_policy = NetHeatingCost(Collection, "policy")
    consumer_cost_ratio = heating_cost_policy / heating_cost_baseline
    consumer_cost_ratio = consumer_cost_ratio.round(3)
    return consumer_cost_ratio


def TotalCostRatio(Collection):
    policy_cost_ratio = PolicyCostRatio(Collection)
    consumer_cost_ratio = ConsumerCostRatio(Collection)
    total_cost_ratio = policy_cost_ratio + consumer_cost_ratio
    return total_cost_ratio


def Emissions(Collection, Case):
    SCALE = 8760 / 73 * 1e-3
    df = load_results(Collection, "SummaryPolicy")
    df = utils.filter(df, include={"PolicySummarySet": "carbon emissions"})
    df = utils.filter(df, include={"Case": Case})
    df["value"] = df["value"] * SCALE
    df = df.drop(columns=["case"])
    df = df.pivot(index="r_carbon", columns="r_cost", values="value")
    df = df.sort_index(ascending=False)
    df = df.round(3)
    return df


def EmissionRatio(Collection):
    emissions_baseline = Emissions(Collection, "baseline")
    emissions_policy = Emissions(Collection, "policy")
    emissions_ratio = emissions_policy / emissions_baseline
    emissions_ratio = emissions_ratio.round(3)
    return emissions_ratio


def EmissionChange(Collection):
    emissions_baseline = Emissions(Collection, "baseline")
    emissions_policy = Emissions(Collection, "policy")
    emissions_change = emissions_policy - emissions_baseline
    emissions_change = emissions_change.round(3)
    return emissions_change


def AbatementCost(Collection, entity):
    emissions_change = EmissionChange(Collection)  # kton
    if entity == "policy":
        entity_cost = NetPolicyCost(Collection)  # M€
    elif entity == "consumer":
        entity_cost = NetHeatingCostChange(Collection)  # M€
    elif entity == "total":
        entity_cost = NetPolicyCost(Collection) + NetHeatingCostChange(Collection)  # M€
    else:
        raise ValueError("Invalid entity. Must be 'policy', 'consumer', or 'total'.")
    abatement_cost = (-1e3) * entity_cost / emissions_change
    abatement_cost = abatement_cost.round(1)
    return abatement_cost


def load_results(Collection, var):
    runs = Collection.runs
    for run in runs:
        run.load_result(var)
        run.results["scenario"] = run.scenario
        _, run.results["r_carbon"], run.results["r_cost"] = run.scenario.split("_")
    return pd.concat([run.results for run in runs])


def plot_multiple_heatmaps(dfs, titles):
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    for ax, df, title in zip(axs.flatten(), dfs, titles):
        sns.heatmap(df.transpose(), annot=True, cmap='coolwarm', fmt=".1f", ax=ax)
        ax.set_title(title)
        ax.set_xlabel("r_cost")
        ax.set_ylabel("r_carbon")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    project = "D"

    input_path = f"data/{project}/runInfo.csv"

    Collection = utils.RunCollection(input_path)
    Collection.keep_feasible_runs()

    # results = HRCapacity(Collection, 'y_h')
    results = HRProduction(Collection, 'x_h')

    # results = NetPolicyCost(Collection)
    # results = ConsumerCostRatio(Collection)
    # results = TotalCostRatio(Collection)
    # results = PolicyCostRatio(Collection)

    # results = EmissionRatio(Collection)

    # results = NetHeatingCostChange(Collection)
    # results = EmissionChange(Collection)
    # results = AbatementCost(Collection,'policy')

    print(results)
