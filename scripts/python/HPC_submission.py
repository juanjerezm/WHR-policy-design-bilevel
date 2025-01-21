import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from string import Template
from utilities import RunCollection, RunInfo, print_line

"""
This script is used to submit jobs to a High-Performance Computing (HPC) system.
It reads run parameters from a CSV file, creates jobscripts based on a template, and submits them.

Minimum usage:
module load python3/3.11.0
module load pandas

python3 HPC_submission.py path/to/runInfo.csv --submit

Arguments:
- path/to/runInfo.csv: Path to the CSV file containing the run parameters.
- --submit: Optional flag to indicate whether to submit the jobs or not, set to False by default.
- --template_path: Optional argument to specify the path to the job template file.
- --max_runs: Optional argument to specify the maximum number of runs allowed.

The script performs the following steps:
1. Reads the run parameters from the CSV file.
4. Validates the run parameters and ensures there are no missing values.
5. Checks if the number of run is below the maximum allowed.
6. Loads the template file for the job script.
7. Creates a job script for each run based on the template.
8. Submits the job scripts to the HPC system (if the --submit flag is provided).

Note: This script requires Python 3.11 or higher to run.

Author: Juan Jerez Monsalves, jujmo@dtu.dk
Date: July 2024
"""


TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")


cfg = {
    "template_path": Path("scripts/python/job_template.sh"),
    "max_runs": 10,
    "submit_flag": False,
}


def load_template() -> Template:
    """Load the template file for the jobscript."""
    with cfg["template_path"].open(mode="r") as file:
        job_template = Template(file.read())
    return job_template


@dataclass
class JobInfo(RunInfo):
    outdir: Path = field(default_factory=Path)
    jobscript_path: Path = field(init=False)

    def __post_init__(self):
        self.jobscript_path = self.outdir / f"jobscript_{TIMESTAMP}.sh"

    def make_job(self):
        content = load_template().safe_substitute(
            project=self.project,
            scenario=self.scenario,
            timeseries=self.timeseries,
            tax_carbon=self.tax_carbon,
            subsidy_opex=self.subsidy_opex,
            subsidy_capex=self.subsidy_capex,
            subsidy_carbon=self.subsidy_carbon,
        )

        with self.jobscript_path.open(mode="w+") as file:
            file.write(content)
        print(f"Submission file for scenario '{self.scenario}' created")

    def submit_job(self):
        if cfg["submit_flag"]:
            with self.jobscript_path.open(mode="r") as file:
                subprocess.run(["bsub"], stdin=file, cwd=Path.cwd())
            print(f"Scenario '{self.scenario}' successfully submitted")
        else:
            print(f"Scenario '{self.scenario}' not submitted due to config settings")


def parse_args():
    """
    Parse command line arguments for submitting jobs to HPC.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Submit jobs to HPC")
    parser.add_argument(
        "input_path", type=Path, help="Path to the CSV file containing scenarios"
    )
    parser.add_argument(
        "--template_path",
        type=Path,
        default=cfg["template_path"],
        help="Path to the job template file",
    )
    parser.add_argument(
        "--max_runs",
        type=int,
        default=cfg["max_runs"],
        help="Maximum number of runs allowed",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        default=cfg["submit_flag"],
        help="Submit the job or not",
    )

    args = parser.parse_args()

    cfg.update(
        {
            "input_path": Path(args.input_path),
            "template_path": Path(args.template_path),
            "max_runs": args.max_runs,
            "submit_flag": args.submit,
        }
    )


def main():
    """
    Entry point of the program.
    """
    if len(sys.argv) > 1:
        parse_args()
    else:
        # Interactive input for input_path if running in an IDE without command-line arguments
        input_path = input("Enter the path to the CSV file containing scenarios: ")
        cfg["input_path"] = Path(input_path)

    if not cfg["input_path"].exists():
        sys.exit("ERROR: Input csv-file not found, script has stopped.")

    runs = RunCollection(cfg["input_path"]).runs

    runs = [JobInfo(**vars(run)) for run in runs]

    if len(runs) > cfg["max_runs"]:
        raise ValueError(
            f"Number of scenarios ({len(runs)}) exceeds the maximum allowed runs ({cfg['max_runs']})"
        )

    for run in runs:
        run.jobscript_path.parent.mkdir(parents=True, exist_ok=True)
        run.make_job()
    print_line()

    for run in runs:
        run.submit_job()
    print_line()


if __name__ == "__main__":
    main()
