from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union
import pandas as pd

# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class RunInfo:
    """
    Represents information about a run.
    Attributes:
        project (str): The project name.
        scenario (str): The scenario name.
        timeseries (str): The timeseries information.
        tax_carbon (str): The carbon tax information.
        subsidy_opex (str): The operational expenditure subsidy information.
        subsidy_capex (str): The capital expenditure subsidy information.
        subsidy_carbon (str): The carbon subsidy information.
        outdir (Path): The output directory path.
        results (pd.DataFrame): The loaded results.
    Methods:
        __post_init__(self) -> None: Initializes the outdir attribute.
        __str__(self) -> str: Returns a string representation of the RunInfo object.
        load_result(self, var: str) -> None: Loads a variable/parameter result from a CSV file.
    """

    project: str
    scenario: str
    timeseries: str
    tax_carbon: str
    subsidy_opex: str
    subsidy_capex: str
    subsidy_carbon: str
    outdir: Path = field(init=False)
    results: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.outdir = Path("results") / self.project / self.scenario

    def __str__(self) -> str:
        return f"-> Project: {self.project}, scenario: {self.scenario}; timeseries={self.timeseries}, tax_carbon={self.tax_carbon}, subsidy_opex={self.subsidy_opex}, subsidy_capex={self.subsidy_capex}, subsidy_carbon={self.subsidy_carbon}"

    def load_result(self, var: str) -> None:
        file: Path = self.outdir / "csv" / f"{var}.csv"
        if file.exists():
            self.results = pd.read_csv(file)
        else:
            self.results = pd.DataFrame()
            print(f"File {file} does not exist. Skipping loading results for {self.scenario}, {var}.")


@dataclass
class RunCollection:
    """
    Represents a collection of runs loaded from a CSV file.
    Attributes:
        file (Union[str, Path]): The path to the CSV file.
        runs (List[RunInfo]): The list of RunInfo objects loaded from the CSV file.
    Methods:
        __post_init__(self) -> None:
            Initializes the RunCollection object after the file attribute is set.
            Loads the runs from the CSV file.
        load_runs(self) -> List[RunInfo]:
            Reads run parameters from the CSV file and returns a list of RunInfo objects.
        validate_dataframe(self, df: pd.DataFrame) -> None:
            Validates that the dataframe is not empty and does not contain missing values.
    """

    file: Union[str, Path]
    runs: List[RunInfo] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.file)
        self.runs = self.load_runs()

    def load_runs(self) -> List[RunInfo]:
        """Read run parameters from a csv-file and return a list of RunInfo objects."""
        df = pd.read_csv(self.path)
        self.validate_dataframe(df)
        loaded_runs = [RunInfo(**row.to_dict()) for _, row in df.iterrows()]

        print(f"-> Loaded {len(loaded_runs)} runs from {self.path}")
        print_line()
        for run in loaded_runs:
            print(str(run))
        print_line()
        return loaded_runs

    def validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate that the dataframe is not empty and does not contain missing values."""
        if df.empty:
            raise ValueError("The CSV file is empty")
        if df.isna().any().any():
            missing_info = df[df.isna().any(axis=1)]
            raise ValueError(
                f"Missing values detected in the following rows:\n{missing_info}"
            )

    def keep_feasible_runs(self):
        """
        Keeps runs from the RunCollection where the policy.lst file contains either:
        - 'MIP status (101): integer optimal solution'
        - 'MIP status (102): integer optimal, tolerance'
        """
        valid_runs = []
        
        for run in self.runs:
            policy_file = run.outdir / "policy.lst"
            
            if policy_file.exists():
                with open(policy_file, 'r') as file:
                    contents = file.read()
                    if "MIP status (101): integer optimal solution" in contents or \
                       "MIP status (102): integer optimal, tolerance" in contents:
                        valid_runs.append(run)
                    else:
                        print(f"-> Removing infeasible run: {run}")
            else:
                print(f"-> policy.lst not found for run: {run}")
        
        self.runs = valid_runs
        print(f"-> {len(self.runs)} valid runs remaining after removal of infeasible ones.")



# =============================================================================
# Data handling
# =============================================================================


def filter(df: pd.DataFrame, include: dict = {}, exclude: dict = {}) -> pd.DataFrame:
    """
    Filters a DataFrame based on inclusion (whitelist) and exclusion (blacklist) criteria.
    Keys are strings that correspond to dataframe columns.
    Values correspond to strings or lists of strings that are the elements to keep or remove.

    Args:
        df (pd.DataFrame): The DataFrame to be filtered.
        include (dict): A dictionary specifying the inclusion criteria. Default is an empty dictionary.
        exclude (dict): A dictionary specifying the exclusion criteria. Default is an empty dictionary.

    Returns:
        pd.DataFrame: The filtered DataFrame.

    Examples:
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
        >>> include_criteria = {'A': [1, 3]}
        >>> exclude_criteria = {'B': 'x'}
        >>> filtered_df = filter_df(df, include=include_criteria, exclude=exclude_criteria)
        >>> print(filtered_df)
           A  B
        2  3  z
    """
    df = df.copy()
    if include:
        for key, value in include.items():
            if isinstance(value, str):
                df = df[df[key] == value]
            else:
                df = df[df[key].isin(value)]
    if exclude:
        for key, value in exclude.items():
            if isinstance(value, str):
                df = df[df[key] != value]
            else:
                df = df[~df[key].isin(value)]
    return df


def rename_values(
    df: pd.DataFrame, rename_dict: Dict[str, Dict[str, str]]
) -> pd.DataFrame:
    """
    Renames values in a DataFrame based on a provided dictionary, with added checks
    for column existence.

    Args:
        df (pd.DataFrame): The DataFrame to be modified.
        rename_dict (Dict[str, Dict[str, str]]): Dictionary specifying rename operations in the form
                                                 {column_name: {old_value: new_value}}, with a check for column existence.

    Returns:
        pd.DataFrame: Modified DataFrame with values renamed according to rename_dict, if columns exist.

    Examples:
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
        >>> rename_dict = {'A': {1: 'One', 2: 'Two'}, 'B': {'z': 'zed'}}
        >>> renamed_df = rename_values(df, rename_dict)
        >>> print(renamed_df)
           A  B
        0  One  x
        1  Two  y
        2    3  zed
    """
    # Ensure the DataFrame is not modified in place
    df = df.copy()

    # Iterate over the dictionary to replace values in the specified columns, with a check for column existence
    for column, replacements in rename_dict.items():
        if column in df.columns:
            if pd.api.types.is_categorical_dtype(df[column]):    # type: ignore
                # For categorical columns, use rename_categories
                df[column] = df[column].cat.rename_categories(replacements)
            else:
                # For non-categorical columns, use replace as before
                df[column] = df[column].replace(replacements)
        else:
            print(f"Column '{column}' does not exist in the DataFrame.")

    return df


def rename_columns(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Wrapper for rename pandas function, specific for column mapping.

    Args:
        df (pd.DataFrame): The DataFrame whose columns need to be renamed.
        column_mapping (Dict[str, str]): A dictionary mapping old column names to new column names.

    Returns:
        pd.DataFrame: The DataFrame with renamed columns.

    Example:
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        >>> column_mapping = {'A': 'New_A', 'B': 'New_B'}
        >>> renamed_df = rename_columns(df, column_mapping)
        >>> print(renamed_df)
           New_A  New_B
        0      1      4
        1      2      5
        2      3      6
    """
    df = df.rename(columns=column_mapping)
    return df


def aggregate(df: pd.DataFrame, categories: List[str], sums: List[str]) -> pd.DataFrame:
    """
    Aggregates data in a DataFrame by grouping it based on specified columns and summing the values in other columns.
    It's a wrapper for the pandas groupby function with the sum operation, and it resets the index.

    Args:
        df (pd.DataFrame): The DataFrame to be aggregated.
        categories (List[str]): A list of column names to group the data by.
        sums (List[str]): A list of column names to sum the values of.

    Returns:
        pd.DataFrame: The aggregated DataFrame.

    Examples:
        >>> df = pd.DataFrame({'Category': ['A', 'A', 'B', 'B'], 'Value': [1, 2, 3, 4]})
        >>> categories = ['Category']
        >>> sums = ['Value']
        >>> aggregated_df = aggregate_data(df, categories, sums)
        >>> print(aggregated_df)
          Category  Value
        0        A      3
        1        B      7
    """
    df = df.groupby(categories, as_index=False, observed=False)[sums].sum()
    return df


def diff(df, ref_col: str, ref_item: str, diff_col: str) -> pd.DataFrame:
    """
    Calculate the change in diff_col relative to a reference item on a reference column.
    Differences are calculated for each combination of elements in the columns that are not diff_col.

    Parameters:
    - df (pandas.DataFrame): The DataFrame to perform the difference calculation on.
    - ref_col (str): The name of the column that contains the reference.
    - ref_item (str): The reference item to subtract from other values in the DataFrame.
    - diff_col (str): The column to perform the difference calculation on.

    Returns:
    - pandas.DataFrame: The DataFrame with the difference values calculated.

    Raises:
    - ValueError: If the base item specified by `ref_item` is not found in the index.
    - ValueError: If the DataFrame's index does not match the base field specified by `ref_col`.

    Example:
    >>> import pandas as pd
    >>> data = {'A': ['x', 'x', 'y', 'y'], 'B': ['a', 'b', 'a', 'b'], 'C': [1, 2, 6, 5], 'D': [5, 4, 1, 2]}
    >>> df = pd.DataFrame(data)
    >>> diff(df, 'A', 'x', ['C', 'D'])
       A  B  C  D
    0  y  a  5 -4
    1  y  b  3 -2
    """
    if ref_col not in df.columns:
        raise ValueError(f"Column '{ref_col}' does not exist in the DataFrame.")
    if ref_item not in df[ref_col].values:
        raise ValueError(
            f"Reference item '{ref_item}' not found in the column '{ref_col}'."
        )

    df = df.copy()
    df = df.set_index([col for col in df.columns if col not in diff_col])

    # MultiIndex case
    if isinstance(df.index, pd.MultiIndex):
        idx_reference = [ref_item in index for index in df.index]
        df_reference = df[idx_reference].droplevel(ref_col)
        idx = [not i for i in idx_reference]
        df = df[idx].subtract(df_reference, axis=1, fill_value=0)

    # SingleIndex case: Adapted logic for a single-level index
    else:
        # Select the base rows and perform subtraction for the other rows
        df_reference = df.loc[[ref_item]]
        # Exclude the base row from the main dataframe
        df_filtered = df.drop(ref_item)
        # Subtract the base row from the rest of the dataframe
        df = df_filtered.subtract(df_reference.squeeze(), axis=1, fill_value=0)

    df = df.reset_index()
    return df

def exclude_empty_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    exist_category = df.groupby(category)["level"].sum()
    idx_exist = exist_category[exist_category != 0].index
    df = df[df[category].isin(idx_exist)]
    return df


def add_fuel_column(df: pd.DataFrame) -> pd.DataFrame:
    fuel_map = pd.read_csv('data/common/map-generator-fuel.csv', header=None, index_col=0, names=["generator", "fuel"])
    fuel_map = clean_quotation_marks(fuel_map)
    fuel_map = fuel_map.squeeze().to_dict()

    df['F'] = df['J'].map(fuel_map)
    
    # Add "(HR)" to the end of the fuel for J's starting with "HR_"
    df.loc[df['J'].str.startswith('HR_'), 'F'] += ' (HR)'
    
    return df


# =============================================================================
# Minor utilities
# =============================================================================


def print_line(length: int = 50) -> None:
    """
    Prints a horizontal line of a given length.
    Args:
        length (int): The length of the line. Default is 50.
    Returns:
        None
    """
    print("-" * length)


def print_title(title: str) -> None:
    """
    Prints a title surrounded by lines.

    Args:
        title (str): The title to be printed.

    Returns:
        None
    """
    print_line()
    print(title)
    print_line()


def clean_quotation_marks(df):
    """
    Clean quotation marks from the index, column names, and elements of a DataFrame.
    Args:
    df (pandas.DataFrame): The DataFrame to be cleaned.
    Returns:
    pandas.DataFrame: The cleaned DataFrame with quotation marks removed from index, column names, and elements.
    """
    df.index = df.index.str.replace("'", "")
    df.columns = df.columns.str.replace("'", "")
    df = df.map(lambda x: str(x).replace("'", ""))
    return df
