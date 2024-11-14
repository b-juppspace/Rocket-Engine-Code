import numpy as np

# Define the nozzle expansion equations as functions
# Stagnation enthalpy consists of the sum of the static (or local) enthalpy and the fluid kinetic 
# energies.
# To = T + (v^2)/(2*cp)
# Inside combustion chambers, where velocities are typically small, the local combustion pressure 
# typically equals the stagnation pressure. Therefore, Pc = Po

def area_ratio_M(M, k):
    # A/At
    term1 = (k-1)/2
    term2 = (k+1) / (k-1)
    return (1/M) * np.sqrt( ( (1 + term1*(M**2)) / (1 + term1))**term2 )

def pressure_ratio(M, k):
    # P/Po, P/Pc
    return 1 / ((1 + 0.5*(k-1) * M**2)**(k/(k-1)))

def temperature_ratio(M, k):
    # T/To, T/Tc
    return 1 / (1 + (k-1)/2 * M**2)

def density_ratio(M, k):
    # rho/rhoc
    return 1 / (1 + (k-1)/2 * M**2)**(1/(k-1))



