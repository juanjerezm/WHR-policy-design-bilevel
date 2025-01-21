* ======================================================================
* DESCRIPTION:
* ======================================================================
* Written by Juan Jerez, jujmo@dtu.dk, 2024.

* ----- NOTES / TODO -----
* - 

* ======================================================================
*  SETUP:
* ======================================================================
* ----- Options -----
$eolCom // 
$onEmpty                // Allows empty sets
$offListing             // Suppresses echoing of input lines in the listing file
$offSymList             // Suppresses listing of symbol map
$offInclude             // Suppresses listing of include-files 
option solprint = off   // Toggles solution listing
option limrow = 0
option limcol = 0
option EpsToZero = on

* ----- Control flags -----
* Run flags
* --project: project's name, a project is a collection of scenarios
* --scenario: scenario's name, a scenario is an individual run of the model
* --timeseries: timeseries name

$ifi not setglobal project          $SetGlobal project          'df_proj'
$ifi not setglobal scenario         $SetGlobal scenario         'df_scen'
$ifi not setglobal timeseries       $SetGlobal timeseries       'spacing_120'

* ----- Directories and filenames -----
$SetGlobal outDir 'results/%project%/%scenario%/';
$ifi %system.filesys% == msnt   $call 'mkdir    .\results\%project%\%scenario%\';
$ifi %system.filesys% == unix   $call 'mkdir -p ./results/%project%/%scenario%/';

* ----- Execution of other scripts -----
* This section runs parameters.gms, which creates a gdx-file containing relevant parameters

$call gams scripts/gams/parameters.gms --project=%project% --scenario=%scenario% --timeseries=%timeseries% o=%outDir%/parameters.lst


* ======================================================================
*  SETS
* ======================================================================
* ----- Set declaration -----
SET
T                       'Timesteps'
J                       'Generators'
J_DH(J)                 'Existing district heating (DH) generators'
J_HR(J)                 'New heat-recovery (HR) generators'
;

* ======================================================================
* PARAMETERS
* ======================================================================
* ----- Parameter declaration -----
PARAMETERS
* Cost parameters
C_c(J)                  'Capacity-based cost (EUR/MW)'
C_p(T,J)                'Production-based cost (EUR/MWh)'

* System parameters
D(T)                    'Demand of heat (MW)'

* Technical parameters
F_a(T,J)                'Generator availabity factor (-)'
Y_s(J)                  'Capacity of waste-heat source (MW)'
Y_f(J)                  'Capacity of generator (fuel-side) (MWh)'
alpha(T,J)              'Fuel-to-heat ratio (-)'
rho(J)                  'Loss factor of DH connection (-)'
omega(T,J)              'Carbon-to-heat ratio (ton-CO2/MWh-heat)'
;

* ----- Load parameters -----
$gdxin results/%project%/%scenario%/parameters.gdx
$load T, J, J_DH, J_HR
$load C_c, C_p
$load D
$load F_a, Y_s, Y_f, alpha, rho, omega
$gdxin


* ======================================================================
* VARIABLES
* ======================================================================
* ----- Variable declaration -----
FREE VARIABLES
obj                         'Objective variable: Cost of heat supply (EUR)'
;

POSITIVE VARIABLES
x_h(T,J)                    'Heat production (MWh)'
y_h(J)                      'Heat output capacity - HR generators (MW)'
;

* ----- Variable attributes -----


* ======================================================================
* EQUATIONS
* ======================================================================
* ----- Equation declaration -----
EQUATIONS
eq_obj                      'Objective function: cost of heat supply'
eq_heat_balance(T)          'Heat balance constraint'
eq_max_firing(T,J)          'Maximum firing capacity - DH generators'
eq_max_source(T,J)          'Maximum waste-heat source capacity - HR generators'
eq_heat_capacity(T,J)       'Maximum heat output capacity - HR generators'
;

* ----- Equation definition -----
eq_obj..                                obj                         =e=   sum((T,J), C_p(T,J) * x_h(T,J))
                                                                        + sum(J_HR, C_c(J_HR) * y_h(J_HR)) 
                                                                        ;

eq_heat_balance(T)..                    D(T)                        =e= sum(J_DH, (1 - rho(J_DH)) * x_h(T,J_DH)) + sum(J_HR, (1 - rho(J_HR)) * x_h(T,J_HR));
eq_max_firing(T,J)$(J_DH(J))..          F_a(T,J) * Y_f(J)           =g=         alpha(T,J)  * x_h(T,J);
eq_max_source(T,J)$(J_HR(J))..          F_a(T,J) * Y_s(J)           =g=      (1-alpha(T,J)) * x_h(T,J);
eq_heat_capacity(T,J)$(J_HR(J))..       0                           =g=                       x_h(T,J) - y_h(J);


* ======================================================================
* MODEL AND SOLVE
* ======================================================================
model
model_baseline 'reference model' 
/all/
;

model_baseline.optfile = 1;

solve model_baseline using lp minimizing obj;


* ======================================================================
* POST-PROCESSING
* ======================================================================
* ----- Outputs results -----
* These are baseline indicators for policy design 
PARAMETER
B_co2                   'Total carbon emissions (ton-CO2)'
B_cost                  'Total heat supply cost (EUR)'
B_cost_OPX_DH           'Total OPEX cost - DH generators (EUR)'
B_cost_OPX_HR           'Total OPEX cost - HR generators (EUR)'
B_cost_CPX_HR           'Total CAPEX cost - HR generators (EUR)'
B_yh(J)                 'Total heat-recovery capacity (MW)'
B_xh(J)                 'Total heat production (MWh)'
;

B_co2           = sum((T,J), omega(T,J) * x_h.l(T,J));
B_cost          = obj.l;
B_cost_OPX_DH   = sum((T,J_DH), C_p(T,J_DH) * x_h.l(T,J_DH));
B_cost_OPX_HR   = sum((T,J_HR), C_p(T,J_HR) * x_h.l(T,J_HR));
B_cost_CPX_HR   = sum(J_HR,     C_c(J_HR)   * y_h.l(J_HR));
B_yh(J_HR)      = y_h.l(J_HR);
B_xh(J)         = sum(T, x_h.l(T,J));


* ======================================================================
* OUTPUTS
* ======================================================================
display ">> Timeseries used:"
display '%timeseries%';

display ">> Installed capacity (MW)"
display y_h.l;

display ">> Total carbon emissions (ton-CO2)"
display B_co2;

display ">> Total heat supply costs (EUR)"
display B_cost;

execute_unload '%outDir%/baseline.gdx';


* ======================================================================
* END OF FILE
