import numpy as np
from scipy.optimize import fsolve
import cantera as ct

# Function to compute adiabatic flame temperature and properties for a given air-based OFR
def adiabatic_flame_temp(OFR, T_target):
    moles_fuel = 1
    moles_O2_stoich = 5  # Stoichiometric O₂ for C₃H₈
    moles_air_stoich = moles_O2_stoich / 0.21  # Stoichiometric air (O₂ is 21% of air)
    moles_air = moles_air_stoich * OFR
    moles_O2 = moles_air * 0.21  # O₂ in the air
    moles_N2 = moles_air * 0.79  # N₂ in the air
    
    # Define gas mixture with gri30 mechanism file
    gas = ct.Solution('gri30.yaml')
    
    # Define initial conditions with propane and air components
    gas.TPX = 298.15, None, {'C3H8': moles_fuel, 'O2': moles_O2, 'N2': moles_N2}
    
    # Equilibrate the mixture adiabatically, allowing pressure to vary
    gas.equilibrate('HP')
    
    # Get equilibrium pressure and other properties
    pressure = gas.P
    R_products = ct.gas_constant / gas.mean_molecular_weight
    k_products = gas.cp / gas.cv
    rho_products = gas.density
    
    # Return the difference from target temperature and additional properties
    return gas.T - T_target, pressure, R_products, k_products, rho_products

# Wrapper function for fsolve to solve for temperature difference
def temp_difference(OFR, T_target):
    return adiabatic_flame_temp(OFR, T_target)[0]

# Define the target temperature
T_target = 1200  # Kelvin
# Initial guess for OFR (air-based)
OFR_initial_guess = 1.0

# Solve for the OFR that achieves the target temperature
OFR_solution = fsolve(temp_difference, OFR_initial_guess, args=(T_target,))[0]

# Get final properties using the solved OFR
_, final_pressure, R_products_solution, k_products_solution, rho_products_solution = adiabatic_flame_temp(OFR_solution, T_target)

# Collect data for plotting parameter values against OFR
OFR_values = np.linspace(0.1, 6, 100)
T_final_values = []
pressure_values = []
R_products_values = []
k_products_values = []
rho_products_values = []

# Calculate properties for each OFR value
for OFR in OFR_values:
    moles_air = (5 / 0.21) * OFR  # Air moles based on stoichiometric O₂
    moles_O2 = moles_air * 0.21
    moles_N2 = moles_air * 0.79
    gas = ct.Solution('gri30.yaml')
    gas.TPX = 298.15, None, {'C3H8': 1, 'O2': moles_O2, 'N2': moles_N2}
    gas.equilibrate('HP')
    T_final_values.append(gas.T)
    pressure_values.append(gas.P)
    R_products_values.append(ct.gas_constant / gas.mean_molecular_weight)
    k_products_values.append(gas.cp / gas.cv)
    rho_products_values.append(gas.density)







