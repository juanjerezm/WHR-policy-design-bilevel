# WHR-policy-design-bilevel

Analysis framework, data files, model, and raw results of the research article  
**“Design and evaluation of policy schemes supporting waste-heat recovery into district heating networks”**

## Overview
This repository includes scripts for scenario setup, model execution, and result analysis. The repository is structured to facilitate high-performance computing (HPC) submissions and detailed post-processing of results.

## Key Components

- **data/common (or <project-name>)**  
  Contains GAMS-ready data files. Detailed data sources and preparation methods can be found in the research article. 
  Some original sources and supporting files can be found in `data/_master`, but are not used by the model workflow.

- **scripts/gams/**  
  GAMS scripts that configure and run the optimization model.  

- **scripts/python/**  
  Python scripts for result analysis, data visualization, and automated HPC job submission.

- **results/**  
  Raw outputs from the model runs, organized by project and scenario. These include model logs, GDX files, and CSV summaries.

## Installation & Requirements
1. **Software**:  
   - [GAMS](https://www.gams.com/) (tested with version 46 or later).  
   - Python 3.12 or later (tested with this version, probably works with python 3.10 onwards).  
2. **Package Dependencies**:  
   - Create virtual environment.
   - Install standard python packages from `environment.yml`.
   - Install the GAMS-python API package that corresponds to your GAMS version. 
3. **High-Performance Computing (Optional)**:  
   - Adapt scripts in `scripts/python/` to match your HPC environment (e.g., SLURM scripts, PBS scripts, etc.).

## Running the Model
1. **Prepare Data**: Ensure the necessary data files are located in the `data/` directory.  
   - By default, files in `data/common` are used across scenarios, unless specifically overridden by files in `data/<project-name>/<scenario-name>`, for the respective project and scenario.
   - Similarly, different timeseries can be used by specifying the --timeseries flag and placing the corresponding data files in the folder `data/common/timeseries/<timeseries-name>/`

2. **Execute Model (locally)**:  
   - Navigate the terminal to the main directory.  
   - Run `run.gms` to perform a complete model run, including baseline and policy scenario analyses, using the following command:
      ```
      gams run.gms --project=<project-name> --scenario=<scenario-name> --timeseries=<timeseries-name> --tax_carbon=<yes|no> --subsidy_capex=<yes|no> --subsidy_opex=<yes|no> --subsidy_carbon=<yes|no>
      ```  
   - Alternatively, run the model directly from GAMS and redefine flags in the code if needed.

3. **Execute Model (HPC)**:  
   - Create a csv file containing the configuration flags for each scenario to be run. Example is given in file `runInfo-example.csv`.
   - Run the script `scripts/python/HPC_submission.py` in your HPC environment. See further documentation in that script.

4. **Extract Results**:
   - Monitor progress and outputs in the `results/<project-name>/<scenario-name>` directory. 
   - CSV results can be exported directly from GAMS' gdx-reader or by running `scripts/python/export_results.py`

## Current Analysis
   - This repository contains the analysis carried out in the publication cited below.
   - Each run is named in the format *X_YYY_ZZZ*, with *X* being the project (policy case), *YYY* the carbon emission limit, and *ZZZ* the consumer cost allowance.
   - Policy nomenclature is as follows:
     - A: Standalone OPEX-based WHR subsidy
     - B: Standalone CAPEX-based WHR subsidy
     - C: OPEX-based WHR subsidy + carbon tax
     - D: CAPEX-based WHR subsidy + carbon tax
     - E: Standalone carbon tax
   - Results are included in GDX format. CSV format available for feasible runs.


## Citation
If you use this repository or data in your research, please cite:  
> Jerez Monsalves, J. (2025). *Design and evaluation of policy schemes supporting waste-heat recovery into district heating networks*. [Journal/Repository details once published].

***Proper citation to be updated once published***


## License
This project is licensed under the [Apache-2.0 License](LICENSE).


## Contact
- **Author**: Juan Jerez Monsalves
- **Date**: February 2025

For questions please reach out to:  
- **Email**: [jujmo@dtu.dk](mailto:jujmo@dtu.dk) or [juanjerezmonsalves@gmail.com](mailto:juanjerezmonsalves@gmail.com)
