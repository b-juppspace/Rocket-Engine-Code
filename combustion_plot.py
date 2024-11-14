import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def combustion_charts(OFR_solution, T_target, OFR_values, T_final_values, R_products_values, k_products_values, rho_products_values, pressure_values, R_products_solution, k_products_solution, rho_products_solution, final_pressure):
    # Plot the results
    plt.figure(figsize=(10, 6))
    plt.plot(OFR_values, T_final_values, label='Adiabatic Flame Temperature')
    plt.axvline(OFR_solution, color='r', linestyle='--', label=f'OFR ≈ {OFR_solution:.4f}')
    plt.axhline(T_target, color='g', linestyle='--', label=f'Target Temperature = {T_target} K')
    plt.xlabel('Oxidizer-to-Fuel Ratio (OFR)')
    plt.ylabel('Adiabatic Flame Temperature (K)')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
    plt.title('Adiabatic Flame Temperature vs OFR')
    plt.legend()
    plt.grid(True)

    # Plot R_products vs OFR
    plt.figure(figsize=(10, 6))
    plt.plot(OFR_values, R_products_values, label='Specific Gas Constant (R_products)')
    plt.axvline(OFR_solution, color='r', linestyle='--', label=f'OFR ≈ {OFR_solution:.4f}')
    plt.axhline(R_products_solution, color='g', linestyle='--', label=f'Specific Gas Constant = {R_products_solution:.4f} J/(kg·K)')
    plt.xlabel('Oxidizer-to-Fuel Ratio (OFR)')
    plt.ylabel('Specific Gas Constant (J/(kg·K))')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
    plt.title('Specific Gas Constant vs OFR')
    plt.legend()
    plt.grid(True)

    # Plot k_products vs OFR
    plt.figure(figsize=(10, 6))
    plt.plot(OFR_values, k_products_values, label='Specific Heat Capacity Ratio (k_products)')
    plt.axvline(OFR_solution, color='r', linestyle='--', label=f'Target OFR ≈ {OFR_solution:.4f}')
    plt.axhline(k_products_solution, color='g', linestyle='--', label=f'Specific Heat Capacity = {k_products_solution:.4f}')
    plt.xlabel('Oxidizer-to-Fuel Ratio (OFR)')
    plt.ylabel('Specific Heat Capacity Ratio (k)')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
    plt.title('Specific Heat Capacity Ratio vs OFR')
    plt.legend()
    plt.grid(True)

    # Plot rho_products vs OFR
    plt.figure(figsize=(10, 6))
    plt.plot(OFR_values, rho_products_values, label='Density of products (rho_products)')
    plt.axvline(OFR_solution, color='r', linestyle='--', label=f'Target OFR ≈ {OFR_solution:.4f}')
    plt.axhline(rho_products_solution, color='g', linestyle='--', label=f'Density of Products = {rho_products_solution:.4f} kg m^-3')
    plt.xlabel('Oxidizer-to-Fuel Ratio (OFR)')
    plt.ylabel('Density of Products (kg m^-3)')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
    plt.title('Density of Products vs OFR')
    plt.legend()
    plt.grid(True)

    # Plot pressure vs OFR
    plt.figure(figsize=(10, 6))
    plt.plot(OFR_values, pressure_values, label='Pressure')
    plt.axvline(OFR_solution, color='r', linestyle='--', label=f'Target OFR ≈ {OFR_solution:.12f}')
    plt.axhline(final_pressure, color='g', linestyle='--', label=f'Final Pressure = {final_pressure:.12f} Pa')
    plt.xlabel('Oxidizer-to-Fuel Ratio (OFR)')
    plt.ylabel('Pressure (Pa)')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.4f}'))
    plt.title('Pressure vs OFR')
    plt.legend()
    plt.grid(True)

    plt.show()
