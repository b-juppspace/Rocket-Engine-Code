import numpy as np
from scipy.optimize import fsolve
import cantera as ct

# Function to compute the adiabatic flame temperature and additional properties for a given OFR
def adiabatic_flame_temp(OFR, T_target):
    moles_fuel = 1
    moles_O2_stoich = 2
    moles_O2 = moles_O2_stoich * OFR
    
    # Define gas mixture with gri30 mechanism file
    gas = ct.Solution('gri30.yaml')
    
    # Define the initial conditions of combustion without specifying pressure
    gas.TPX = 298.15, None, {'C3H8': moles_fuel, 'O2': moles_O2}
    
    # Equilibrate the mixture adiabatically, allowing pressure to vary
    gas.equilibrate('HP')
    
    # Get the equilibrium pressure
    pressure = gas.P
    
    # Calculate R_products and k_products
    R_products = ct.gas_constant / gas.mean_molecular_weight
    k_products = gas.cp / gas.cv
    rho_products = gas.density
    
    # Return the difference between the computed and target temperatures
    return gas.T - T_target, pressure, R_products, k_products, rho_products

# Wrapper function for fsolve to only return the temperature difference
def temp_difference(OFR, T_target):
    return adiabatic_flame_temp(OFR, T_target)[0]

# Define the target temperature
T_target = 2500
# Initial guess for OFR
OFR_initial_guess = 1.0

# Solve for the OFR that results in the target temperature
OFR_solution = fsolve(temp_difference, OFR_initial_guess, args=(T_target,))[0]

# Get the final properties using the solved OFR
_, final_pressure, R_products_solution, k_products_solution, rho_products_solution = adiabatic_flame_temp(OFR_solution, T_target)

# Collect data for plotting the resulting parameter values against OFR:

OFR_values = np.linspace(0.1, 6, 100)
T_final_values = []
pressure_values = []
R_products_values = []
k_products_values = []
rho_products_values = []

# Calculate T_final, pressure, R_products, k_products, rho_products for each OFR value
for OFR in OFR_values:
    moles_O2 = 2 * OFR
    gas = ct.Solution('gri30.yaml')
    gas.TPX = 298.15, None, {'CH4': 1, 'O2': moles_O2}
    gas.equilibrate('HP')
    T_final_values.append(gas.T)
    pressure_values.append(gas.P)
    R_products_values.append(ct.gas_constant / gas.mean_molecular_weight)
    k_products_values.append(gas.cp / gas.cv)
    rho_products_values.append(gas.density)





