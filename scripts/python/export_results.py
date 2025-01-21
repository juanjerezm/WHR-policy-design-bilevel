import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

import gams.transfer as gt
import pandas as pd
from utilities import RunCollection, RunInfo, print_line


def parse_args():
    """
    Parse command line arguments for submitting jobs to HPC.
    """
    parser = argparse.ArgumentParser(description="Submit jobs to HPC")
    parser.add_argument(
        "--input_path", type=Path, help="Path to the CSV file containing scenarios"
    )
    return parser.parse_args()


def main(vars, pars):
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

    Collection = RunCollection(input_path)
    Collection.keep_feasible_runs()
    runs = Collection.runs
    
    for run in runs:
        gdx2csv(run, vars, pars)

def gdx2df_vars(
    paths: Union[List[str], List[Path]],
    variables: Optional[List[str]] = None,
    attributes: List[str] = ["level"],
) -> Dict[str, pd.DataFrame]:
    """
    Reads GDX files from the given paths and returns all or some variables in a dictionary of pandas DataFrames.

    Args:
        paths (Union[List[str], List[Path]]): A list of file paths to the GDX files.
        variables (List[str], optional): A list of variable names to read from the GDX files. If None, all variables will be read.
        attributes (List[str], optional): A list of attribute names to include in the resulting DataFrames. Defaults to ['level'].

    Returns:
        dict: A dictionary where the keys are variable names and the values are pandas DataFrames containing the data.

    """
    gams_attrs = ["level", "marginal", "lower", "upper", "scale"]

    paths = [Path(path) for path in paths]

    # case names are the entire filename without the extension
    cases = [path.stem for path in paths]

    # read gdx files into containers
    containers = [gt.Container(str(path)) for path in paths]

    data_all = dict()
    for case, container in zip(cases, containers):
        if variables is None:
            spec_var = container.listVariables()
        else:
            spec_var = variables

        for var in spec_var:
            df_temp = container[var].records  # type: ignore
            if df_temp is None:
                print(f"Empty DataFrame for {var} in {case}")
                continue

            df_temp.insert(0, "case", case)
            df_temp.drop(
                columns=[col for col in gams_attrs if col not in attributes],
                inplace=True,
            )

            if var not in data_all:
                data_all[var] = pd.DataFrame()
            data_all[var] = pd.concat([data_all[var], df_temp])

    return data_all


def gdx2df_pars(
    paths: Union[List[str], List[Path]], parameters: List[str]
) -> Dict[str, pd.DataFrame]:
    """
    Reads GDX files from the given paths and returns the specified parameters in a dictionary of DataFrames.

    Note:
    - If a parameter is not found in a GDX file, an empty DataFrame will be returned for that parameter.

    Args:
        paths ([List[str], List[Path]]): A list of file paths to the GDX files.
        parameters (List[str]): A list of parameters names to read from the GDX files.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary where the keys are parameter names and the values are pandas DataFrames containing the data.

    """

    paths = [Path(path) for path in paths]

    # case names are the last part of the file name after the last hyphen
    cases = [path.stem for path in paths]

    # read gdx files into containers
    containers = [gt.Container(str(path)) for path in paths]

    data_all = dict()
    for case, container in zip(cases, containers):
        for par in parameters:
            try:
                df_temp = container[par].records  # type: ignore
            except KeyError:
                print(f"KeyError: {par} not found in {case}")
                continue
            if df_temp is None:
                print(f"Empty DataFrame for {par} in {case}")
                continue

            df_temp.insert(0, "case", case)
            if par not in data_all:
                data_all[par] = pd.DataFrame()
            data_all[par] = pd.concat([data_all[par], df_temp])

    return data_all


def gdx2csv(
    Run: RunInfo, vars: Optional[List[str]] = None, pars: Optional[List[str]] = None
) -> Dict[str, pd.DataFrame]:
    data: Dict[str, pd.DataFrame] = {}
    paths = [
        Run.outdir / "baseline.gdx",
        Run.outdir / "policy.gdx",
    ]

    print_line()
    print(f"-> Exporting results to CSV for {Run.project} - {Run.scenario}")

    data = {}

    if vars:
        if not isinstance(vars, list) or not all(
            isinstance(item, str) for item in vars
        ):
            raise TypeError("vars must be a list of strings")

    data.update(
        gdx2df_vars(paths, vars)
    )  # outside the if statement to include all variables if vars is None

    if pars:
        if not isinstance(pars, list) or not all(
            isinstance(item, str) for item in pars
        ):
            raise TypeError("pars must be a list of strings")
        data.update(gdx2df_pars(paths, pars))


    # Quick-and-dirty way of including beta_b in the output, as it is not included in the final GDX files
    df_temp = gdx2df_pars([Run.outdir / "parameters.gdx"], ['beta_b'])

    # Create the baseline and policy dataframes
    df_baseline = df_temp['beta_b'].copy()
    df_baseline['case'] = 'baseline'
    df_policy = df_temp['beta_b'].copy()
    df_policy['case'] = 'policy'

    df = pd.concat([df_baseline, df_policy])
    df = {'beta_b': df} # wrap it in a dictionary
    data.update(df)  # update the data dictionary with the beta_b dataframe


    csv_dir = Run.outdir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    for key in data.keys():
        data[key].to_csv(csv_dir / f"{key}.csv", index=False)
        print(f"-> {key}.csv saved to {csv_dir}")

    return data


if __name__ == "__main__":
    vars = None
    pars = ['SummaryExpenses', 'SummaryOperations', 'SummaryPolicy', 'SummaryProduction', 'SummaryRatio', 'v_adj_CO2', 'v_adj_MWh','alpha','omega']
    main(vars, pars)
