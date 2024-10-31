# WHR-policy-design-bilevel

Analysis framework, data files, and results for the research article "Design and evaluation of policy schemes supporting waste-heat recovery into district heating networks"

## Overview
This repository includes scripts for scenario setup, model execution, and result analysis. The repository is structured to facilitate high-performance computing (HPC) submissions and detailed post-processing of results.

## Key Components

### Data
- **data/A, B, C, ...**: Contains the data files in gams-ready format. Sources are detailed in the research article.

### Scripts
- **scripts/gams/**: Contains GAMS scripts for model execution.
- **scripts/python/**: Contains Python scripts for result analysis and HPC submission.

### Results
- **results/**: Contains the raw output of model runs, organized by project and scenario.

## Running the Model
Execute `run.gms` to run the entire model, including parameter setup, baseline run, and policy run.

## License
This project is licensed under the Apache-2.0 license. 

## Contact
For any questions or issues, please contact Juan Jerez Monsalves at jujmo@dtu.dk or juanjerezmonsalves@gmail.com.
