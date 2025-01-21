import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

save = False

# ----- read data -----
unit_file = r"c:\Users\juanj\Downloads\energy producer census\ept_produktions-_og_forbrugsdata_2021-2023.xlsx"
unit_data = pd.read_excel(unit_file)


# ----- fixing data types -----
unit_data["fv_net"] = (
    pd.to_numeric(unit_data["fv_net"].replace(r"^\s*$", 0, regex=True), errors="coerce")
    .fillna(0)
    .astype(int)
)
unit_data["skrotdato"] = pd.to_datetime(unit_data["skrotdato"], errors="coerce")


# ----- filtering -----
unit_data = unit_data[unit_data["aar"] == 2023]  # only 2023 data
unit_data = unit_data[unit_data["fv_net"] != 0]  # only units connected to a DH network
# only units that are not decomissioned or decomissioned after 2023
unit_data = unit_data[
    (unit_data["skrotdato"].isna()) | (unit_data["skrotdato"] >= "2023-01-01")
]

# units with heat capacity and more than 2 TJ delivery (0.3% of energy, 35% of entries)
unit_data = unit_data[unit_data["varmekapacitet_MW"] > 0]
unit_data = unit_data[unit_data["varmelev_TJ"] > 2]

# main columns to keep
main_cols = [
    "vrkanl_ny",
    "anlaegstype_navn",
    "varmelev_TJ",
    "indfyretkapacitet_MW",
    "elkapacitet_MW",
    "varmekapacitet_MW",
]

# fuel columns to keep
fuel_cols = [
    "kul",
    "fuelolie",
    "spildolie",
    "gasolie",
    "raffinaderigas",
    "lpg",
    "naturgas",
    "affald",
    "biogas",
    "halm",
    "skovflis",
    "trae- og biomasseaffald",
    "traepiller",
    "bio-olie",
    "braendselsfrit",
    "solenergi",
    "vandkraft",
    "elektricitet",
]

# Keep necessary columns
unit_data = unit_data.rename(columns={col + "_TJ": col for col in fuel_cols})
unit_data = unit_data[main_cols + fuel_cols]


# ----- fuel-share calculation and capacity allocation -----
# we melt df based on fuel use, and calculate the fuel share in each unit
unit_data = unit_data.melt(id_vars=main_cols, var_name="fuel", value_name="fuel_value")

# sort by vrkanl_ny and fuel
unit_data = unit_data.sort_values(by=["vrkanl_ny", "fuel"])

# fuel-share calculation
unit_data["fuel_share"] = unit_data.groupby("vrkanl_ny")["fuel_value"].transform(
    lambda x: x / x.sum()
)

# If heat-pump, reverse the process: all fuel allocation to electricity
unit_data.loc[
    (unit_data["anlaegstype_navn"].str.contains("Varmepumpe"))
    & (unit_data["fuel"] != "elektricitet"),
    "fuel_share",
] = 0
unit_data.loc[
    (unit_data["anlaegstype_navn"].str.contains("Varmepumpe"))
    & (unit_data["fuel"] == "elektricitet"),
    "fuel_share",
] = 1

# if solar, reverse the process: all fuel to fuel-free. This works because the final data has a "source" column as well
unit_data.loc[
    (unit_data["anlaegstype_navn"] == "Solvarme")
    & (unit_data["fuel"] != "braendselsfrit"),
    "fuel_share",
] = 0
unit_data.loc[
    (unit_data["anlaegstype_navn"] == "Solvarme")
    & (unit_data["fuel"] == "braendselsfrit"),
    "fuel_share",
] = 1

# if excess heat, reverse the process: all fuel to fuel-free. This works because the final data has a "source" column as well
unit_data.loc[
    (unit_data["anlaegstype_navn"] == "Overskudsvarme")
    & (unit_data["fuel"] != "braendselsfrit"),
    "fuel_share",
] = 0
unit_data.loc[
    (unit_data["anlaegstype_navn"] == "Overskudsvarme")
    & (unit_data["fuel"] == "braendselsfrit"),
    "fuel_share",
] = 1

# allocate capacities based on fuel share
unit_data["fuel_capacity_allocation"] = (
    unit_data["fuel_share"] * unit_data["indfyretkapacitet_MW"]
)
unit_data["heat_capacity_allocation"] = (
    unit_data["fuel_share"] * unit_data["varmekapacitet_MW"]
)
unit_data["elec_capacity_allocation"] = (
    unit_data["fuel_share"] * unit_data["elkapacitet_MW"]
)

# drop original capacity columns and fuel columns
unit_data = unit_data.drop(
    columns=[
        "indfyretkapacitet_MW",
        "elkapacitet_MW",
        "varmekapacitet_MW",
        "fuel_value",
    ]
)

# remove any rows whose fuel_share is less than 3%, as these are likely start-up systems
unit_data = unit_data[unit_data["fuel_share"] > 0.03]

# ----- renaming data -----
# rename anlaegstype_navn to technology_type
unit_data = unit_data.rename(columns={"anlaegstype_navn": "technology_type"})

technology_map = {
    "Bioforgasn. m. FM": "gasification plus engine",
    "Dampturbine": "steam turbine",
    "Forbrændingsmotor": "combustion engine",
    "Gasturbine": "gas turbine",
    "Kombianlæg": "combined cycle",
    "Organic Rankine (ORC)": "organic rankine cycle",
    "Anden": "other",
    "Bioforgasn. m. KE": "gasification plus boiler",
    "Dampkedel": "steam boiler",
    "Elpatron": "boiler",
    "Geotermi": "geothermal",
    "Kedel": "boiler",
    "Overskudsvarme": "industrial heat",
    "Solvarme": "solar",
    "Varmepumpe": "heat pump - other",
    "Varmepumpe Anden": "heat pump - other",
    "Varmepumpe Grundvand": "heat pump - water",
    "Varmepumpe Kombi": "heat pump - other",
    "Varmepumpe Luft": "heat pump - air",
    "Varmepumpe Overskudsvarme": "heat pump - industrial heat",
    "Varmepumpe Solvarme": "heat pump - other",
    "Varmepumpe Spildevand": "heat pump - water",
    "Varmepumpe røggas": "heat pump - other",
}

technology_category_map = {
    "Bioforgasn. m. FM": "CHP",
    "Dampturbine": "CHP",
    "Forbrændingsmotor": "CHP",
    "Gasturbine": "CHP",
    "Kombianlæg": "CHP",
    "Organic Rankine (ORC)": "CHP",
    "Anden": "FF",
    "Bioforgasn. m. KE": "HOB",
    "Dampkedel": "HOB",
    "Elpatron": "HOB",
    "Geotermi": "FF",
    "Kedel": "HOB",
    "Overskudsvarme": "FF",
    "Solvarme": "FF",
    "Varmepumpe": "HP",
    "Varmepumpe Anden": "HP",
    "Varmepumpe Grundvand": "HP",
    "Varmepumpe Kombi": "HP",
    "Varmepumpe Luft": "HP",
    "Varmepumpe Overskudsvarme": "HP",
    "Varmepumpe Solvarme": "HP",
    "Varmepumpe Spildevand": "HP",
    "Varmepumpe røggas": "HP",
}

source_map = {
    "Anden": "industry",
    "Geotermi": "geothermal",
    "Overskudsvarme": "industry",
    "Solvarme": "solar",
    "Varmepumpe": "industry",  # assumed
    "Varmepumpe Anden": "industry", # from data source
    "Varmepumpe Grundvand": "ambient",  # to reduce model complexity
    "Varmepumpe Kombi": "industry", # from data source
    "Varmepumpe Luft": "ambient",  # to reduce model complexity
    "Varmepumpe Overskudsvarme": "industry", # from data source
    "Varmepumpe Solvarme": "solar",  # to reduce model complexity
    "Varmepumpe Spildevand": "ambient",  # to reduce model complexity
    "Varmepumpe røggas": "industry",
}

fuel_map = {
    "skovflis": "wood chips",
    "traepiller": "wood pellets",
    "affald": "municipal waste",
    "halm": "straw",
    "kul": "coal",
    "naturgas": "natural gas",
    "biogas": "biofuels",
    "raffinaderigas": "refinery gas",
    "brændselsfrit": "fuel free",
    "elektricitet": "electricity",
    "bio-olie": "biofuels",
    "fuelolie": "fuel oil",
    "gasolie": "gas oil",
    "trae- og biomasseaffald": "wood waste",
    "solenergi": "solar",
    "omgivelsesvarme": "ambient heat",
    "braendselsfrit": "fuel free",
}

# add energy source
unit_data["source"] = unit_data["technology_type"].map(source_map).fillna("")

# add technology category
unit_data["technology_category"] = unit_data["technology_type"].map(
    technology_category_map
)

# rename anlaegstype_navn elemnts by technology_map
unit_data["technology_type"] = unit_data["technology_type"].map(technology_map)

# rename fuel category
unit_data["fuel"] = unit_data["fuel"].map(fuel_map).fillna(unit_data["fuel"])


# ----- consolidation at national level -----
# aggregate capacity and varmelev values
DK_data = (
    unit_data.groupby(["technology_category", "fuel", "source"])
    .agg(
        {
            "fuel_capacity_allocation": "sum",
            "heat_capacity_allocation": "sum",
            "elec_capacity_allocation": "sum",
            "varmelev_TJ": "sum",
        }
    )
    .reset_index()
)

# calculate efficiencies
DK_data["heat_efficiency"] = (
    DK_data["heat_capacity_allocation"] / DK_data["fuel_capacity_allocation"]
)
DK_data["total_efficiency"] = (
    DK_data["elec_capacity_allocation"] + DK_data["heat_capacity_allocation"]
) / DK_data["fuel_capacity_allocation"]

# calculate cb factor
DK_data["cb"] = (
    DK_data["elec_capacity_allocation"] / DK_data["heat_capacity_allocation"]
)

# Production in CPH
CPH_prod = pd.read_csv('data/_master/ts-demand-heat.csv', header=None, names=['timestep', 'demand'])
CPH_prod = CPH_prod['demand'].sum()

# Total production
DK_prod = DK_data['varmelev_TJ'].sum()
DK_prod = DK_prod * 277.778 # TJ to MWh

scaling_factor = DK_prod/CPH_prod

print(f"Demand scaling factor: {scaling_factor}")

# ----- Final cleaning -----
# removing anything with heat capacity less than 55 MW, to remove small generators
# this leaves out 0.6% of remaining capacity, and 0.4% of heat generation 
DK_data = DK_data[DK_data["heat_capacity_allocation"] > 55]

round_cols = [
    "fuel_capacity_allocation",
    "heat_capacity_allocation",
    "elec_capacity_allocation",
    "varmelev_TJ",
    "heat_efficiency",
    "total_efficiency",
    "cb",
]

DK_data[round_cols] = DK_data[round_cols].round(3)

DK_data = DK_data.sort_values(by="heat_capacity_allocation", ascending=False)
DK_data = DK_data.reset_index(drop=True)


# ----- printing and saving -----
print(DK_data.head(100))


if save == True:
    unit_data.to_csv("data/_master/unit_data.csv", index=False)
    DK_data.to_csv("data/_master/national_data.csv", index=False)
