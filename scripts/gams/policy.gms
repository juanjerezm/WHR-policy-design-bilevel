* ======================================================================
* DESCRIPTION:
* ======================================================================
* Written by Juan Jerez, jujmo@dtu.dk, 2024.

* ----- NOTES / TODO -----


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
option optcr = 1e-4     // Tolerance for optimality
option reslim = 1e6     // Limit in seconds for the solver (1e6 ≈ 27.7 hours)
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
* This section runs two GAMS scripts: parameters.gms and baseline.gms
* Parameters.gms creates a gdx-file containing relevant parameters
* Baseline.gms runs the model without policy design, i.e. lower-level only

$call gams scripts/gams/parameters.gms --project=%project% --scenario=%scenario% --timeseries=%timeseries% o=%outDir%/parameters.lst
$eval error_parameters errorLevel
$if not %error_parameters%==0   $abort "parameters.gms did not execute successfully. Errorlevel: %error_parameters%"

$call gams scripts/gams/baseline.gms   --project=%project% --scenario=%scenario% --timeseries=%timeseries% o=%outDir%/baseline.lst
$eval error_baseline errorLevel
$if not %error_baseline%==0     $abort "baseline.gms did not execute successfully. Errorlevel: %error_baseline%"

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

* ----- Set aliases -----
alias(J,JJ)

* ======================================================================
* PARAMETERS
* ======================================================================
* ----- Parameter declaration -----
PARAMETERS
* Cost parameters
C_c(J)                  'Capacity-based cost (EUR/MW)'
C_p(T,J)                'Production-based cost (EUR/MWh)'

* System parameters
B_co2                   'Baseline carbon emissions (ton-CO2)'
B_cost                  'Baseline heat supply costs (EUR)'
B_yh(J)                 'Baseline capacity of HR generators (MW)'
B_xh(J)                 'Baseline production of all generators (MWh)'
D(T)                    'Demand of heat (MW)'
R_co2                   'Policy ratio for carbon emissions relative to baseline (-)'
R_cost                  'Policy ratio for heat supply costs relative to baseline (-)'

* Technical parameters
F_a(T,J)                'Generator availabity factor (-)'
Y_s(J)                  'Capacity of waste-heat source (MW)'
Y_f(J)                  'Capacity of generator (fuel-side) (MWh)'
alpha(T,J)              'Fuel-to-heat ratio (-)'
rho(J)                  'Loss factor of DH connection (-)'
omega(T,J)              'Carbon-to-heat ratio (ton-co2/MWh-heat)'

* Big-M parameters
M_1(T,J)                'Big-M - eq_max_firing'
M_2(T,J)                'Big-M - eq_max_source'
M_3(T,J)                'Big-M - eq_heat_capacity'
M_4(T,J)                'Big-M - eq_stationarity_xh'
M_5(J)                  'Big-M - eq_stationarity_yh'

* Other parameters from baseline case, for output comparison
B_cost_OPX_DH           'Total OPEX cost - DH generators (EUR)'
B_cost_OPX_HR           'Total OPEX cost - HR generators (EUR)'
B_cost_CPX_HR           'Total CAPEX cost - HR generators (EUR)'
;

* ----- Load parameters -----
$gdxin results/%project%/%scenario%/parameters.gdx
$load T, J, J_DH, J_HR
$load C_c, C_p
$load D
$load F_a, Y_s, Y_f, alpha, rho, omega
$load M_1, M_2, M_3, M_4, M_5
$load R_co2, R_cost
$gdxin

* Load parameters from baseline case
$gdxin results/%project%/%scenario%/baseline.gdx
$load B_co2, B_cost, B_yh, B_xh
$load B_cost_OPX_DH, B_cost_OPX_HR, B_cost_CPX_HR
$gdxin

* ======================================================================
* VARIABLES
* ======================================================================
* ----- Variable declaration -----
FREE VARIABLES
obj                         'Objective variable: Cost of policy (EUR)'
;

* Primal variables
POSITIVE VARIABLES
x_h(T,J)                    'Heat production (MWh)'
y_h(J)                      'Heat output capacity - HR generators (MW)'
k_p                         'Subsidy per production unit (EUR/MWh)'
k_c                         'Subsidy per capacity unit (EUR/MW)'
u_p                         'Tax per production unit - DH generators (EUR/ton)'
v                           'Carbon-based subsidy factor (EUR/MWh-ton)'
;

* Dual variables
FREE VARIABLES
lambda_1(T)                 'Dual variable for heat balance equation (EUR/MWh)'
;
POSITIVE VARIABLES
mu_1(T,J)                   'Dual variable for maximum firing capacity equation - DH generators (EUR/MWh)'
mu_2(T,J)                   'Dual variable for maximum waste-heat source capacity equation - HR generators (EUR/MWh)'
mu_3(T,J)                   'Dual variable for maximum heat capacity equation - HR generators (EUR/MWh)'
;

* Linearization variables
BINARY VARIABLES
theta_1(T,J)                'Auxiliary variable for linearization - eq_max_firing'
theta_2(T,J)                'Auxiliary variable for linearization - eq_max_source'
theta_3(T,J)                'Auxiliary variable for linearization - eq_heat_capacity'
theta_4(T,J)                'Auxiliary variable for linearization - eq_stationarity_xh'
theta_5(J)                  'Auxiliary variable for linearization - eq_stationarity_yh'
;

* ----- Variable attributes -----
$ifi NOT %tax_carbon%     == 'yes'  u_p.fx=0;
$ifi NOT %subsidy_capex%  == 'yes'  k_c.fx=0;
$ifi NOT %subsidy_opex%   == 'yes'  k_p.fx=0;
$ifi NOT %subsidy_carbon% == 'yes'  v.fx=0;


* ======================================================================
* EQUATIONS
* ======================================================================
* ----- Equation declaration -----
EQUATIONS
* Upper-level
eq_obj                      'Objective function: cost of policy'
eq_carbon_limit             'Limit on carbon emissions'
eq_heatcost_limit           'Limit on heat supply cost'

* Lower-level
eq_heat_balance(T)          'Heat balance constraint'
eq_max_firing(T,J)          'Maximum firing capacity - DH generators'
eq_max_source(T,J)          'Maximum waste-heat source capacity - HR generators'
eq_heat_capacity(T,J)       'Maximum heat output capacity - HR generators'

* Stationarity conditions
eq_stationarity_xh_dh(T,J)  'Stationarity condition for heat production variable - DH generators'
eq_stationarity_xh_hr(T,J)  'Stationarity condition for heat production variable - HR generators'
eq_stationarity_yh(J)       'Stationarity condition for heat capacity variable - HR generators'

* Complementarity slackness - linearization
eq_cmpl_firing_max_p(T,J)   'Complementarity linearization: eq_max_firing (primal)'
eq_cmpl_firing_max_d(T,J)   'Complementarity linearization: eq_max_firing (dual)'
eq_cmpl_source_max_p(T,J)   'Complementarity linearization: eq_max_source (primal)'
eq_cmpl_source_max_d(T,J)   'Complementarity linearization: eq_max_source (dual)'
eq_cmpl_capacity_p(T,J)     'Complementarity linearization: eq_heat_capacity (primal)'
eq_cmpl_capacity_d(T,J)     'Complementarity linearization: eq_heat_capacity (dual)'
eq_cmpl_stnrt_xh_p(T,J)     'Complementarity linearization: eq_stationarity_xh (primal)'
eq_cmpl_stnrt_xh_dh_d(T,J)  'Complementarity linearization: eq_stationarity_xh (dual) - DH generators'
eq_cmpl_stnrt_xh_hr_d(T,J)  'Complementarity linearization: eq_stationarity_xh (dual) - HR generators'
eq_cmpl_stnrt_yh_p(J)       'Complementarity linearization: eq_stationarity_yh (primal)'
eq_cmpl_stnrt_yh_d(J)       'Complementarity linearization: eq_stationarity_yh (dual)'
;

* ----- Equation definition -----
eq_obj..                                obj                         =e=   sum((T,J), C_p(T,J) * x_h(T,J))
                                                                        + sum(J_HR, C_c(J_HR) * y_h(J_HR)) 
                                                                        - sum(T, lambda_1(T) * D(T)) 
                                                                        + sum((T,J_DH), F_a(T,J_DH) * Y_f(J_DH) * mu_1(T,J_DH)) 
                                                                        + sum((T,J_HR), F_a(T,J_HR) * Y_s(J_HR) * mu_2(T,J_HR))
                                                                        ;

eq_carbon_limit..                       B_co2 * R_co2               =g= sum((T,J), omega(T,J) * x_h(T,J));

eq_heatcost_limit..                     B_cost * R_cost             =g= + sum(T, lambda_1(T)*D(T))
                                                                        - sum((T,J_DH), F_a(T,J_DH) * Y_f(J_DH) * mu_1(T,J_DH)) 
                                                                        - sum((T,J_HR), F_a(T,J_HR) * Y_s(J_HR) * mu_2(T,J_HR));

eq_heat_balance(T)..                    D(T)                        =e= sum(J_DH, (1 - rho(J_DH)) * x_h(T,J_DH)) + sum(J_HR, (1 - rho(J_HR)) * x_h(T,J_HR));
eq_max_firing(T,J)$(J_DH(J))..          F_a(T,J) * Y_f(J)           =g=         alpha(T,J)  * x_h(T,J);
eq_max_source(T,J)$(J_HR(J))..          F_a(T,J) * Y_s(J)           =g=      (1-alpha(T,J)) * x_h(T,J);
eq_heat_capacity(T,J)$(J_HR(J))..       0                           =g=                       x_h(T,J) - y_h(J);

eq_stationarity_xh_dh(T,J)$J_DH(J)..    0                           =l= C_p(T,J)       + omega(T,J) * u_p          - (1-rho(J)) * lambda_1(T) + alpha(T,J) * mu_1(T,J);
eq_stationarity_xh_hr(T,J)$J_HR(J)..    0                           =l= C_p(T,J) - k_p - ((1 - R_co2) * B_co2 * v) - (1-rho(J)) * lambda_1(T)                          + (1-alpha(T,J)) * mu_2(T,J) + mu_3(T,J);
eq_stationarity_yh(J)$J_HR(J)..         0                           =l= C_c(J) * (1 - k_c) - sum(T, mu_3(T,J));

eq_cmpl_firing_max_p(T,J)$(J_DH(J))..   M_1(T,J)*(1 - theta_1(T,J)) =g= F_a(T,J) * Y_f(J) - alpha(T,J) * x_h(T,J);
eq_cmpl_firing_max_d(T,J)$(J_DH(J))..   M_1(T,J)*     theta_1(T,J)  =g= mu_1(T,J);

eq_cmpl_source_max_p(T,J)$(J_HR(J))..   M_2(T,J)*(1 - theta_2(T,J)) =g= F_a(T,J) * Y_s(J) - (1-alpha(T,J)) * x_h(T,J);
eq_cmpl_source_max_d(T,J)$(J_HR(J))..   M_2(T,J)*     theta_2(T,J)  =g= mu_2(T,J);

eq_cmpl_capacity_p(T,J)$J_HR(J)..       M_3(T,J)*(1 - theta_3(T,J)) =g= y_h(J) - x_h(T,J);
eq_cmpl_capacity_d(T,J)$J_HR(J)..       M_3(T,J)*     theta_3(T,J)  =g= mu_3(T,J);

eq_cmpl_stnrt_xh_p(T,J)..               M_4(T,J)*(1 - theta_4(T,J)) =g= x_h(T,J);
eq_cmpl_stnrt_xh_dh_d(T,J)$J_DH(J)..    M_4(T,J)*     theta_4(T,J)  =g= C_p(T,J) + omega(T,J) * u_p                - (1-rho(J)) * lambda_1(T) + alpha(T,J) * mu_1(T,J) ;
eq_cmpl_stnrt_xh_hr_d(T,J)$J_HR(J)..    M_4(T,J)*     theta_4(T,J)  =g= C_p(T,J) - k_p - ((1 - R_co2) * B_co2 * v) - (1-rho(J)) * lambda_1(T)                          + (1-alpha(T,J)) * mu_2(T,J) + mu_3(T,J);

eq_cmpl_stnrt_yh_p(J)$J_HR(J)..         M_5(J)*  (1 - theta_5(J))   =g= y_h(J);
eq_cmpl_stnrt_yh_d(J)$J_HR(J)..         M_5(J)*       theta_5(J)    =g= C_c(J) * (1 - k_c) - sum(T, mu_3(T,J));


* ======================================================================
* MODEL AND SOLVE
* ======================================================================
model
model_policy 'policy model' 
/all/
;

model_policy.optfile = 1;
solve model_policy using mip minimizing obj;

* ======================================================================
* POST-PROCESSING
* ======================================================================
* ----- Checking complementarity conditions -----
SET CMPL    'Complementary conditions'
/'eq_max_firing', 'eq_max_source', 'eq_heat_capacity', 'eq_stationarity_xh', 'eq_stationarity_yh'/
;

PARAMETERS
cmpl_check_2D(T,J,CMPL)
cmpl_check_1D(J,CMPL)
cmpl_max(CMPL)
cmpl_sum(CMPL)
;

cmpl_check_2D(T,J,'eq_max_firing')$(NOT J_HR(J))    = abs(
                                                        mu_1.l(T,J) * (F_a(T,J) * Y_f(J) - alpha(T,J) * x_h.l(T,J))
                                                        );
cmpl_check_2D(T,J,'eq_max_source')$(J_HR(J))        = abs(
                                                        mu_2.l(T,J) * (F_a(T,J) * Y_s(J) - (1-alpha(T,J)) * x_h.l(T,J))
                                                        );
cmpl_check_2D(T,J,'eq_heat_capacity')$(J_HR(J))     = abs(
                                                        mu_3.l(T,J) * (y_h.l(J) - x_h.l(T,J))
                                                        );
cmpl_check_2D(T,J,'eq_stationarity_xh')             = abs(
                                                        x_h.l(T,J) * (C_p(T,J) - k_p.l$J_HR(J) - ((1 - R_co2) * B_co2 * v.l)$J_HR(J) - (1-rho(J)) * lambda_1.l(T) + alpha(T,J) * mu_1.l(T,J)$J_DH(J) + (1-alpha(T,J)) * mu_2.l(T,J)$J_HR(J) + mu_3.l(T,J)$J_HR(J) + omega(T,J) * u_p.l$J_DH(J))
                                                        );
cmpl_check_1D(J,'eq_stationarity_yh')$(J_HR(J))     = abs(
                                                        y_h.l(J) * (C_c(J) * (1 - k_c.l) - sum(T, mu_3.l(T,J)))
                                                        );

cmpl_max(CMPL) = smax((T,J), cmpl_check_2D(T,J,CMPL)) + smax(J, cmpl_check_1D(J,CMPL));
cmpl_sum(CMPL) = sum((T,J), cmpl_check_2D(T,J,CMPL)) + sum(J, cmpl_check_1D(J,CMPL));


* ----- Summary of main results -----
SET Case                    'Case set'
/'baseline', 'policy'/;

SET SetAux1
/'limit', 'actual'/;

SET OperationalSummarySet
/'Capacity', 'Production'/;

SET ExpensesSummarySet      'Summary set for expenses of heat-supply results'
/'OPEX - DH', 'OPEX - HR', 'CAPEX - HR'/;

SET PolicySummarySet        'Summary set for policy results'
/'carbon emissions', 'subsidy cost', 'tax revenue', 'net policy cost', 'heating cost - gross', 'heating cost - net'/;


PARAMETERS
SummaryOperations(OperationalSummarySet, J, Case)   'Summary parameter holding operational results'
SummaryHR(OperationalSummarySet, Case)              'Summary parameter holding total HR results'
SummaryExpenses(ExpensesSummarySet, Case)           'Summary parameter holding heat supply expenses'
SummaryPolicy(PolicySummarySet, Case)               'Summary parameter holding policy results'
SummaryRatio(PolicySummarySet, SetAux1)             'Summary parameter holding policy ratios'
SummaryProduction(J, Case)                          'Summary parameter holding production results'
;

SummaryOperations('Capacity', J_HR, 'baseline')     = EPS + B_yh(J_HR);
SummaryOperations('Production', J_HR, 'baseline')   = EPS + B_xh(J_HR);

SummaryOperations('Capacity', J_HR, 'policy')       = EPS + y_h.l(J_HR);
SummaryOperations('Production', J_HR, 'policy')     = EPS + sum(T, x_h.l(T,J_HR));

SummaryHR('Capacity', 'baseline')                   = EPS + sum(J_HR, B_yh(J_HR));
SummaryHR('Production', 'baseline')                 = EPS + sum(J_HR, B_xh(J_HR));

SummaryHR('Capacity', 'policy')                     = EPS + sum(J_HR, y_h.l(J_HR));
SummaryHR('Production', 'policy')                   = EPS + sum((T,J_HR), x_h.l(T,J_HR));

SummaryExpenses('OPEX - DH', 'baseline')            = EPS + B_cost_OPX_DH;
SummaryExpenses('OPEX - HR', 'baseline')            = EPS + B_cost_OPX_HR;
SummaryExpenses('CAPEX - HR', 'baseline')           = EPS + B_cost_CPX_HR;

SummaryExpenses('OPEX - DH', 'policy')              = EPS + sum((T,J_DH), C_p(T,J_DH) * x_h.l(T,J_DH));
SummaryExpenses('OPEX - HR', 'policy')              = EPS + sum((T,J_HR), C_p(T,J_HR) * x_h.l(T,J_HR));
SummaryExpenses('CAPEX - HR', 'policy')             = EPS + sum(J_HR, C_c(J_HR) * y_h.l(J_HR));

SummaryPolicy('carbon emissions', 'baseline')       = EPS + B_co2;
SummaryPolicy('subsidy cost', 'baseline')           = EPS + 0;
SummaryPolicy('tax revenue', 'baseline')            = EPS + 0;
SummaryPolicy('net policy cost', 'baseline')        = EPS + 0;
SummaryPolicy('heating cost - gross', 'baseline')   = EPS + B_cost;
SummaryPolicy('heating cost - net', 'baseline')     = EPS + SummaryPolicy('heating cost - gross', 'baseline') - SummaryPolicy('net policy cost', 'baseline');

SummaryPolicy('carbon emissions', 'policy')         = EPS + sum((T,J), omega(T,J) * x_h.l(T,J));
SummaryPolicy('subsidy cost', 'policy')             = EPS + sum((T,J_HR), k_p.l * x_h.l(T,J_HR)) + sum((T,J_HR), ((1 - R_co2) * B_co2 * v.l) * x_h.l(T,J_HR)) + sum(J_HR, C_c(J_HR) * k_c.l * y_h.l(J_HR));
SummaryPolicy('tax revenue', 'policy')              = EPS + sum((T,J_DH), u_p.l       * x_h.l(T,J_DH) * omega(T,J_DH));
SummaryPolicy('net policy cost', 'policy')          = EPS + SummaryPolicy('subsidy cost', 'policy') - SummaryPolicy('tax revenue', 'policy');
SummaryPolicy('heating cost - gross', 'policy')     = EPS + SummaryExpenses('OPEX - DH', 'policy') + SummaryExpenses('OPEX - HR', 'policy') + SummaryExpenses('CAPEX - HR', 'policy');
SummaryPolicy('heating cost - net', 'policy')       = EPS + SummaryPolicy('heating cost - gross', 'policy') - SummaryPolicy('net policy cost', 'policy');

SummaryRatio('carbon emissions', 'limit')           = EPS + R_co2;
SummaryRatio('heating cost - net', 'limit')         = EPS + R_cost;

SummaryRatio('carbon emissions', 'actual')          = EPS + SummaryPolicy('carbon emissions', 'policy') / SummaryPolicy('carbon emissions', 'baseline');
SummaryRatio('heating cost - net', 'actual')        = EPS + SummaryPolicy('heating cost - net', 'policy') / SummaryPolicy('heating cost - net', 'baseline');

SummaryProduction(J, 'baseline')                    = EPS + 100 * B_xh(J)/sum(JJ, B_xh(JJ));
SummaryProduction(J, 'policy')                      = EPS + 100 * sum(T, x_h.l(T,J))/sum((T,JJ), x_h.l(T,JJ));

PARAMETERS
v_adj_CO2   'Carbon-adjusted carbon-subsidy (EUR/ton)'
v_adj_MWh   'Energy-adjusted carbon-subsidy (EUR/MWh)'
;

v_adj_CO2 = EPS + v.l * sum((T,J_HR), x_h.l(T,J_HR));
v_adj_MWh = EPS + v.l * ((1 - R_co2) * B_co2);

* ======================================================================
* OUTPUTS
* ======================================================================
display ">> Project, scenario and timeseries:"
display '%project%, %scenario%, %timeseries%';

display ">> Subsidies and taxes:"
display k_p.l, k_c.l, v.l, u_p.l, v_adj_CO2, v_adj_MWh;

display ">> HR Summary:"
display SummaryHR;

display ">> Detailed HR Summary:"
display SummaryOperations;

display ">> Policy Ratio:"
display SummaryRatio;

display ">> Policy Summary:"
display SummaryPolicy;

display ">> DH Expense Summary:"
display SummaryExpenses;

display ">> Heat Production Summary:"
display SummaryProduction;

display ">> Complementarity checks, maximum:"
display cmpl_max;

display ">> Complementarity checks, sum:"
display cmpl_sum;

execute_unload '%outDir%/policy.gdx'

* * * ======================================================================
* * * END OF FILE
