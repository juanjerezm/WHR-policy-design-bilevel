* ======================================================================
* DESCRIPTION:
* ======================================================================
* 
* Written by Juan Jerez, jujmo@dtu.dk, 2024.

* This script sets up flags, directories, and filenames for the model runs. 
* It executes the entire model run, including the creation of the parameter file, the baseline run, and the policy run.
* The policy script is run, within which the others are called.

* ----- NOTES / TODO -----


* ======================================================================
*  SETUP:
* ======================================================================
* ----- Options -----
$eolCom                 // 
// Activates end-of-line comments with '//'
$onEmpty                // Allows empty sets
$offListing             // Suppresses echoing of input lines in the listing file
$offSymList             // Suppresses listing of symbol map
$offInclude             // Suppresses listing of include-files 


* ----- Control flags -----
* Run flags
* --project: project's name, a project is a collection of scenarios
* --scenario: scenario's name, a scenario is an individual run of the model
* --timeseries: timeseries name

$ifi not setglobal project          $SetGlobal project          'df_proj'
$ifi not setglobal scenario         $SetGlobal scenario         'df_scen'   
$ifi not setglobal timeseries       $SetGlobal timeseries       'spacing_120'   

* Policy flags
$ifi not setglobal tax_carbon       $SetGlobal tax_carbon       'no'           // set to 'yes' to include tax per CO2 emissions
$ifi not setglobal subsidy_capex    $SetGlobal subsidy_capex    'no'           // set to 'yes' to include subsidy per MW of installed WHR capacity
$ifi not setglobal subsidy_opex     $SetGlobal subsidy_opex     'no'           // set to 'yes' to include subsidy per MWh of heat recoreved
$ifi not setglobal subsidy_carbon   $SetGlobal subsidy_carbon   'no'           // set to 'yes' to include subsidy per MWh of heat recovered, proportional to CO2 emissions saved

* ----- Directories and filenames -----
$SetGlobal outDir 'results/%project%/%scenario%/';
$ifi %system.filesys% == msnt   $call 'mkdir    .\results\%project%\%scenario%\';
$ifi %system.filesys% == unix   $call 'mkdir -p ./results/%project%/%scenario%/';


* ----- Execution of other scripts -----
$call gams scripts/gams/policy.gms --project=%project% --scenario=%scenario% --timeseries=%timeseries% --tax_carbon=%tax_carbon% --subsidy_capex=%subsidy_capex% --subsidy_opex=%subsidy_opex% --subsidy_carbon=%subsidy_capex% o=%outDir%/policy.lst
$eval error_policy errorLevel
$if not %error_policy%==0   $abort "policy.gms did not execute successfully. Errorlevel: %error_policy%"
