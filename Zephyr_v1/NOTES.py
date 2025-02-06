#-----------NOTES--------------
# To use this program, run Main.py!

# 1. Clean up combustion and combustion optimiser connection, they both do
# the same thing. DONE

# 2. Fix ratio graph printing twice. DONE

# 3. Assumed exit pressure = atmospheric pressure, no introduction of pressure
# difference in thrust equation, could implement this for future purposes.

# 4. Any point making a GUI for user interface?

# 5. Convergent section and combustion chamber need improvement.

# 6. MASS FLOW RATE EQ

# PRINTS:
# combustion
print(f"The OFR that results in an adiabatic flame temperature of {T_target} K is approximately {OFR_solution:.4f}")
print(f"The specific gas constant of the products is approximately {R_products_solution:.2f} J/(kg·K)")
print(f"The specific heat capacity ratio (k) of the products is approximately {k_products_solution:.2f}")

# areas and radius
print(f"The Area of the nozzle at the inlet is {A_nozzle_inlet:.6f} m^2")
print(f"The Radius of the nozzle at the inlet is {R_inlet:.6f} m^2")
print(f"The Area of the nozzle at the throat is {At:.6f} m^2")
print(f"The Radius of the nozzle at the throat is {At_radius:.6f} m^2")
print(f"The Area of the nozzle at the exit is {A_nozzle_exit:.6f} m^2")
print(f"The Radius of the nozzle at the exit is {R_exit:.6f} m^2")

# temperatures
print(f"The Temperature Ratio at exit is {Tr_at_exit:.2f} ")
print(f"The combustion temperature is assumed to be the adiabatic flame temperature {Tc:.2f} K")
print(f"The Temperature at exit is {Te:.2f} K")
print(f"The Temperature at nozzle throat is {Tt:.2f} K")

# velocity
print(f"The velocity at nozzle throat is {ut:.2f} m/s")
print(f"The exhaust velocity is {ue:.2f} m/s")

# thrust
print(f"The thrust produced by the engine is {F:.2f} kN")
print(f"The thrust coefficient of the engine is {CF:.2f} ")

# PLOTS:
from ratio_plot import plot_data
plot_data(M_values, Pr_Ma, Ar_Ma, Tr_Ma, rhor_Ma)

from combustion_plot import combustion_charts
combustion_charts(OFR_solution, T_target, OFR_values, T_final_values, R_products_values, k_products_values, R_products_solution, k_products_solution)