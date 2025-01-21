import os
import csv
import itertools

def create_folders_and_csvs(base_directory, letter, carbon_ratios, cost_ratios):
    # Generate combinations of carbon and cost ratios
    elements = [f"{letter}_{carbon:03d}_{cost:03d}" for carbon, cost in itertools.product(carbon_ratios, cost_ratios)]

    # Create each folder and CSV file for each element (combination)
    for element in elements:
        folder_path = os.path.join(base_directory, element)

        try:
            # Create the folder
            os.makedirs(folder_path, exist_ok=True)
            print(f"Folder created: {folder_path}")

            # Extract carbon ratio and cost ratio from folder name (e.g., "E_090_100")
            _, carbon_str, cost_str = element.split('_')
            carbon_ratio = int(carbon_str) / 100.0  # Convert to 1-basis
            cost_ratio = int(cost_str) / 100.0      # Convert to 1-basis

            # Create the CSV content with quotes around the policy names
            csv_content = [
                ['\'policy carbon ratio\'', carbon_ratio],
                ['\'policy cost ratio\'', cost_ratio]
            ]

            # Write the CSV file in the respective folder
            csv_file_path = os.path.join(folder_path, "data-other.csv")
            with open(csv_file_path, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(csv_content)

            print(f"CSV file created: {csv_file_path}")

        except OSError as error:
            print(f"Error creating folder or file {folder_path}: {error}")

    return elements

def create_run_info_csv(base_directory, letter, elements, tax_carbon, subsidy_opex, subsidy_capex, subsidy_carbon):
    # Generate the runInfo.csv content
    runinfo_content = []

    for element in elements:
        # Determine the flags for tax and subsidies
        tax_carbon_flag = "yes" if tax_carbon else "no"
        subsidy_opex_flag = "yes" if subsidy_opex else "no"
        subsidy_capex_flag = "yes" if subsidy_capex else "no"
        subsidy_carbon_flag = "yes" if subsidy_carbon else "no"

        # Append the row to runInfo.csv content
        runinfo_content.append([
            letter,  # Project
            element,  # Scenario
            "spacing_120",  # Timeseries (can be modified if needed)
            tax_carbon_flag,  # Tax on carbon
            subsidy_opex_flag,  # Subsidy on opex
            subsidy_capex_flag,  # Subsidy on capex
            subsidy_carbon_flag  # Subsidy on carbon
        ])

    # Write the runInfo.csv file in the base directory
    runinfo_file_path = os.path.join(base_directory, "runInfo.csv")
    os.makedirs(base_directory, exist_ok=True)  # Ensure the base directory exists
    with open(runinfo_file_path, mode='w', newline='') as runinfo_file:
        writer = csv.writer(runinfo_file)
        # Write the header
        writer.writerow([
            "project", "scenario", "timeseries", "tax_carbon", "subsidy_opex", "subsidy_capex", "subsidy_carbon"
        ])
        # Write all the rows
        writer.writerows(runinfo_content)

    print(f"runInfo.csv created at {runinfo_file_path}")

if __name__ == "__main__":
    # Parameters for generating elements
    letter = "A"  # Can be changed dynamically
    carbon_ratios = [95, 90, 85, 80]  # These are in 100-basis (e.g., 0.95 as 95)
    cost_ratios = [100, 110, 120]  # These are in 100-basis (e.g., 1.00 as 100)

    # Define tax and subsidy flags (set as True or False)
    tax_carbon = False
    subsidy_opex = True
    subsidy_capex = False
    subsidy_carbon = False

    # Base directory (it ends with the letter)
    base_directory = f"data/{letter}"

    # Step 1: Create folders and individual CSVs
    elements = create_folders_and_csvs(base_directory, letter, carbon_ratios, cost_ratios)

    # Step 2: Create the runInfo.csv
    create_run_info_csv(base_directory, letter, elements, tax_carbon, subsidy_opex, subsidy_capex, subsidy_carbon)
