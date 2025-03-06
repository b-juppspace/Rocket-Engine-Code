import cantera as ct
import numpy as np
import matplotlib.pyplot as plt

# Define fuel and air mixture parameters
moles_fuel = 1  # 1 mole of propane (C3H8)
moles_O2_stoich = 5  # Stoichiometric oxygen moles for 1 mole of propane
moles_N2_per_O2 = 3.76  # Air contains 3.76 moles of N2 per mole of O2
OFR = 1.0  # Oxygen-to-fuel ratio (stoichiometric combustion)

# Calculate air composition
moles_O2 = moles_O2_stoich * OFR
moles_N2 = moles_O2 * moles_N2_per_O2

# Initialize gas object using GRI-3.0 mechanism
gas = ct.Solution('gri30.yaml')

# Set initial temperature
T_initial = 298.15  # Initial temperature [K]
composition = {'C3H8': moles_fuel, 'O2': moles_O2, 'N2': moles_N2}

# Pressure and volume ranges for testing
pressure_range = np.linspace(1e5, 1e6, 10)  # Pressures in Pascals
volume_range = np.linspace(0.01, 0.1, 10)  # Volumes in cubic meters

# Arrays to store results
temperatures_uv = np.zeros((len(pressure_range), len(volume_range)))
pressures_uv = np.zeros((len(pressure_range), len(volume_range)))

# Iterate over pressures and volumes
for i, P_initial in enumerate(pressure_range):
    for j, volume in enumerate(volume_range):
        # Constant Volume Combustion (UV)
        gas.TPX = T_initial, P_initial, composition
        gas.equilibrate('UV')  # Equilibrate at constant internal energy and volume
        temperatures_uv[i, j] = gas.T  # Store final temperature
        pressures_uv[i, j] = gas.P  # Store final pressure

# Visualize Results: Heatmaps for Temperature and Pressure
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Heatmap for Temperature
c1 = axes[0].contourf(volume_range, pressure_range / 1e5, temperatures_uv, levels=20, cmap='hot')
axes[0].set_title('Final Temperature (UV)')
axes[0].set_xlabel('Volume (m³)')
axes[0].set_ylabel('Initial Pressure (bar)')
fig.colorbar(c1, ax=axes[0])

# Heatmap for Pressure
c2 = axes[1].contourf(volume_range, pressure_range / 1e5, pressures_uv / 1e5, levels=20, cmap='viridis')
axes[1].set_title('Final Pressure (UV)')
axes[1].set_xlabel('Volume (m³)')
axes[1].set_ylabel('Initial Pressure (bar)')
fig.colorbar(c2, ax=axes[1])

plt.tight_layout()
plt.show()

# Analyze Optimal Conditions (e.g., Maximize Temperature)
optimal_index = np.unravel_index(np.argmax(temperatures_uv), temperatures_uv.shape)
optimal_pressure = pressure_range[optimal_index[0]] / 1e5  # Convert to bar
optimal_volume = volume_range[optimal_index[1]]

print(f"Optimal Conditions for Maximum Temperature:")
print(f"  Pressure: {optimal_pressure:.2f} bar")
print(f"  Volume: {optimal_volume:.3f} m³")
print(f"  Temperature: {temperatures_uv[optimal_index]:.2f} K")
