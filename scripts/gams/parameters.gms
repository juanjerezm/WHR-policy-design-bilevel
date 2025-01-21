* ======================================================================
* DESCRIPTION:
* ======================================================================
* Written by Juan Jerez, jujmo@dtu.dk, 2024.

* ----- NOTES / TODO -----


* ======================================================================
*  SETUP:
* ======================================================================
* ----- Options -----
$eolCom                 //
// eolCom activates end-of-line comments with '//'
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


* ======================================================================
*  SETS
* ======================================================================

SET
T(*)        'Timesteps' 
/ 
$onDelim
$if     EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-timesteps.csv' $include 'data/%project%/%scenario%/common/timeseries/%timeseries%/ts-timesteps.csv' 
$if NOT EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-timesteps.csv' $include                      'data/common/timeseries/%timeseries%/ts-timesteps.csv'
$offDelim
/
;

SET J(*)    'Generators'
/
$onDelim
$if     EXIST   'data/%project%/%scenario%/name-generator.csv' $include 'data/%project%/%scenario%/name-generator.csv'
$if NOT EXIST   'data/%project%/%scenario%/name-generator.csv' $include               'data/common/name-generator.csv'
$offDelim
/;

SET F(*)    'Fuels'
/
$onDelim
$if     EXIST   'data/%project%/%scenario%/name-fuel.csv' $include 'data/%project%/%scenario%/name-fuel.csv'
$if NOT EXIST   'data/%project%/%scenario%/name-fuel.csv' $include               'data/common/name-fuel.csv'
$offDelim
/;

SET JF(J,F) 'Generator-fuel mapping'
/
$onDelim
$if     EXIST   'data/%project%/%scenario%/map-generator-fuel.csv' $include 'data/%project%/%scenario%/map-generator-fuel.csv'
$if NOT EXIST   'data/%project%/%scenario%/map-generator-fuel.csv' $include               'data/common/map-generator-fuel.csv' 
$offDelim
/;

* ======================================================================
*  Auxiliary data loading (required after definition of sets, but before subsets)
* ======================================================================
* --- Define acronyms ---
ACRONYMS BP 'Backpressure', HO 'Heat-only', HR 'Heat recovery';
ACRONYMS timeVar 'time-variable data';

* --- Load data attributes ---
SET GnrtAttrs(*)    'Generator attributes (auxiliary set)'
/
$onDelim
$include    'data/common/attribute-generator.csv'
$offDelim
/;

SET FuelAttrs(*)    'Fuel attributes (auxiliary set)'
/
$onDelim
$include    'data/common/attribute-fuel.csv'
$offDelim
/;

Set OtherAttrs(*)    'Other attributes (auxiliary set)'
/
$onDelim
$include    'data/common/attribute-other.csv'
$offDelim
/;

* --- Load data values --- *
TABLE GnrtData(J,GnrtAttrs)    'Generator data'
$onDelim
$if     EXIST   'data/%project%/%scenario%/data-generator.csv' $include 'data/%project%/%scenario%/data-generator.csv'
$if NOT EXIST   'data/%project%/%scenario%/data-generator.csv' $include               'data/common/data-generator.csv'
$offDelim
;

TABLE FuelData(F,FuelAttrs)    'Fuel data'
$onDelim
$if     EXIST  'data/%project%/%scenario%/data-fuel.csv' $include 'data/%project%/%scenario%/data-fuel.csv'
$if NOT EXIST  'data/%project%/%scenario%/data-fuel.csv' $include               'data/common/data-fuel.csv'
$offDelim
;

PARAMETER OtherData(OtherAttrs)    'Other data'
/
$onDelim
$if     EXIST  'data/%project%/%scenario%/data-other.csv' $include 'data/%project%/%scenario%/data-other.csv'
$if NOT EXIST  'data/%project%/%scenario%/data-other.csv' $include               'data/common/data-other.csv'
$offDelim
/
;

* ======================================================================
* SUBSETS
* ======================================================================
* ----- Subset declaration -----
SETS
J_BP(J)                 'Backpressure generators'
J_HO(J)                 'Heat-only generators'
J_HR(J)                 'Heat-recovery generators'
J_DH(J)                 'District-heating existing generators'
F_EL(F)                 'Electricity fuel'
;

* --- Subset definition ---
J_BP(J)     = YES$(GnrtData(J,'TYPE') EQ BP);
J_HO(J)     = YES$(GnrtData(J,'TYPE') EQ HO);
J_HR(J)     = YES$(GnrtData(J,'TYPE') EQ HR);
J_DH(J)     = YES$(NOT J_HR(J));
F_EL(F)     = YES$(sameas(F,'electricity'));

* ======================================================================
* PARAMETERS
* ======================================================================
* ----- Parameter declaration -----
PARAMETERS
* Cost parameters
C_f(T,J)                'Cost of fuel consumption (EUR/MWh)'
C_h(J)                  'Cost of heat production (EUR/MWh)'
C_e(J)                  'Cost of electricity production (EUR/MWh)'
C_c(J)                  'Cost of heat capacity (EUR/MW)'
C_ht(J)                 'Cost of heat transport (EUR/MWh)'
C_p(T,J)                'Cost per unit of production (EUR/MWh)'
AF_h(J)                 'Annualization factor for heat capacity (-)' // Internally calculated to annualize generation CAPEX
AF_ht(J)                'Annualization factor for heat transport (-)' // Internally calculated to annualize transport CAPEX

* System parameters
F_t                     'Temporal scale factor (-)' // Internally calculated to adjust capacity-based costs based on temporal resolution
D(T)                    'Demand of heat (MW)'
R_co2                   'Policy ratio for carbon emissions relative to baseline (-)'
R_cost                  'Policy ratio for heat supply costs relative to baseline (-)'

* Technical parameters
F_a(T,J)                'Generator availabity factor (-)'
Y_s(J)                  'Capacity of waste-heat source (MW)'
Y_f(J)                  'Capacity of generator (fuel-side) (MW)'
alpha(T,J)              'Fuel-to-heat ratio (-)'
beta_b(J)               'Power-to-heat coefficient of CHPs - Cb (-)'
eta(T,J)                'Generator efficiency (-)'
rho(J)                  'Loss factor of DH connection (-)'

* Fuel and carbon parameters
pi_e(T)                 'Price of electricity (EUR/MWh)'
pi_f(T,F)               'Price of fuel (EUR/MWh)'
omega_e(T)              'Carbon content of electricity grid - average (ton-CO2/MWh)'
omega_f(T,F)            'Carbon content of fuel (ton-CO2/MWh-fuel)'
omega(T,J)              'Carbon per heat production (ton-CO2/MWh-heat)'

* Big-M parameters
M_1(T,J)                'Big-M - eq_max_firing'
M_2(T,J)                'Big-M - eq_max_source'
M_3(T,J)                'Big-M - eq_heat_capacity'
M_4(T,J)                'Big-M - eq_stationarity_xh'
M_5(J)                  'Big-M - eq_stationarity_yh'
;


* ----- Parameter definition -----
* - One-dimensional parameters -
PARAMETERS
D(T)
/
$onDelim
$if     EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-demand-heat.csv' $include 'data/%project%/%scenario%/timeseries/%timeseries%/ts-demand-heat.csv'
$if NOT EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-demand-heat.csv' $include               'data/common/timeseries/%timeseries%/ts-demand-heat.csv'
$offDelim
/

pi_e(T)
/
$onDelim
$if     EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-electricity-price.csv' $include 'data/%project%/%scenario%/timeseries/%timeseries%/ts-electricity-price.csv'
$if NOT EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-electricity-price.csv' $include               'data/common/timeseries/%timeseries%/ts-electricity-price.csv'
$offDelim
/

omega_e(T)
/
$onDelim
$if     EXIST  'data/%project%/%scenario%/timeseries/%timeseries%/ts-electricity-carbon.csv' $include 'data/%project%/%scenario%/timeseries/%timeseries%/ts-electricity-carbon.csv'
$if NOT EXIST  'data/%project%/%scenario%/timeseries/%timeseries%/ts-electricity-carbon.csv' $include               'data/common/timeseries/%timeseries%/ts-electricity-carbon.csv'
$offDelim
/
;

* - Multi-dimensional parameters -
TABLE F_a(T,J)
$onDelim
$if     EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-generator-availability.csv' $include 'data/%project%/%scenario%/timeseries/%timeseries%/ts-generator-availability.csv'
$if NOT EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-generator-availability.csv' $include               'data/common/timeseries/%timeseries%/ts-generator-availability.csv'
$offDelim
;

TABLE eta(T,J)
$onDelim
$if     EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-generator-efficiency.csv' $include 'data/%project%/%scenario%/timeseries/%timeseries%/ts-generator-efficiency.csv'
$if NOT EXIST   'data/%project%/%scenario%/timeseries/%timeseries%/ts-generator-efficiency.csv' $include               'data/common/timeseries/%timeseries%/ts-generator-efficiency.csv'
$offDelim
;

* - Assigned parameters -
C_h(J)$(J_HO(J) OR J_HR(J))     = GnrtData(J,'variable O&M - heat production');
C_e(J)$(J_BP(J))                = GnrtData(J,'variable O&M - electricity production');
C_ht(J)$(J_HR(J))               = GnrtData(J,'variable O&M - heat transport');
AF_h(J)$(J_HR(J))               = GnrtData(J,'discount rate') / (1 - (1 + GnrtData(J,'discount rate'))**(-GnrtData(J,'lifetime - heat capacity')));
AF_ht(J)$(J_HR(J))              = GnrtData(J,'discount rate') / (1 - (1 + GnrtData(J,'discount rate'))**(-GnrtData(J,'lifetime - heat transport')));
C_c(J)$(J_HR(J))                = GnrtData(J,'investment cost - heat capacity') * AF_h(J)
                                + GnrtData(J,'investment cost - heat transport') * GnrtData(J,'length - heat transport') * AF_ht(J)
                                + GnrtData(J,'fixed O&M - heat capacity');
Y_f(J)                          = GnrtData(J,'capacity - fuel');
Y_s(J)                          = GnrtData(J,'capacity - waste-heat source');
beta_b(J)$J_BP(J)               = GnrtData(J,'Cb');
rho(J)                          = GnrtData(J,'loss factor - heat transport') * GnrtData(J,'length - heat transport');

pi_f(T,F)                       = FuelData(F,'fuel price')$(NOT F_EL(F)) + pi_e(T)$(F_EL(F));
omega_f(T,F)                    = FuelData(F,'co2 content')$(NOT F_EL(F)) + omega_e(T)$(F_EL(F));

R_co2                           = OtherData('policy carbon ratio');
R_cost                          = OtherData('policy cost ratio');

* ----- Parameter operations -----
F_t                             = 8760/card(T);
C_c(J_HR)                       = C_c(J_HR)/F_t;

alpha(T,J)                      = (beta_b(J) + 1)/eta(T,J);
omega(T,J)                      = sum(F$JF(J,F), omega_f(T,F)) * alpha(T,J);
C_f(T,J)                        = sum(F$JF(J,F), pi_f(T,F) + omega_f(T,F)*FuelData(F,'carbon quota price') + FuelData(F,'fuel tax') + FuelData(F,'volumetric tariff'));
C_f(T,J)$J_BP(J)                = sum(F$JF(J,F), C_f(T,J) - (1-1/(1.25*alpha(T,J)))*FuelData(F,'fuel tax')); // Reimbursing fuel tax for CHPs based on electricity-attributed fuel consumption (125% method) 
C_p(T,J)                        = alpha(T,J) * C_f(T,J) + C_h(J) + C_ht(J) + (C_e(J) - pi_e(T)) * beta_b(J);

* ----- Defining big-Ms -----
alias(T,TT); // required to find the maximum possible over t, on an equation already indexed by T

M_1(T,J)$J_DH(J)                = MAX(0, F_a(T,J)*Y_f(J), ((1-rho(J))*500 - C_p(T,J))/alpha(T,J)); //done

M_2(T,J)$J_HR(J)                = MAX(0, F_a(T,J)*Y_s(J), ((1-rho(J))*500 - C_p(T,J) + 500)/(1-alpha(T,J))); // Assumed subsidies max 500

M_3(T,J)$J_HR(J)                = MAX(0, smax(TT,(F_a(TT,J)*Y_s(J))/(1-alpha(TT,J))), C_c(J)); //done

M_4(T,J)$J_DH(J)                = MAX(0, F_a(T,J)*Y_f(J), 1e5);                     // did not calculate the second equation
M_4(T,J)$J_HR(J)                = MAX(0, F_a(T,J)*Y_s(J)/(1-alpha(T,J)), C_c(J));   // did not calculate the second equation

M_5(J)$J_HR(J)                  = MAX(0, smax(T,(F_a(T,J)*Y_s(J))/(1-alpha(T,J))), C_c(J)); //done

execute_unload '%outDir%/parameters.gdx';

* ======================================================================
* END OF FILE
