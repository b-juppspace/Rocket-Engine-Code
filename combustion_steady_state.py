import cantera as ct
import matplotlib.pyplot as plt
import numpy as np

# Load the GRI-Mech 3.0 mechanism from a YAML file
gas = ct.Solution('gri30.yaml')

OFR = 5
moles_methane = 1
moles_O2_stoich = 2
moles_O2 = moles_O2_stoich * OFR

# Set the temperature, pressure, and composition of the gas mixture
gas.TPX = 2500, None, {'CH4': moles_methane, 'O2': moles_O2}

# Create an IdealGasReactor object with the specified gas mixture
r = ct.IdealGasReactor(gas)

# Create a ReactorNet object to handle the reactor network
net = ct.ReactorNet([r])

# Time-stepping parameters
time = 0.0
end_time = 50
time_step = 1e-1

# Data storage
times = []
production_rates_over_time = []
temperatures_over_time = []

# Time-stepping loop
while time < end_time:
    net.advance(time + time_step)
    times.append(net.time)
    production_rates_over_time.append(gas.net_production_rates.copy())
    temperatures_over_time.append(gas.T)
    time += time_step

# Convert to arrays for easier plotting
production_rates_over_time = np.array(production_rates_over_time)
temperatures_over_time = np.array(temperatures_over_time)

# Plotting
species_indices = [gas.species_index(s) for s in ['CH4', 'O2', 'CO2', 'H2O']]
species_names = ['CH4', 'O2', 'CO2', 'H2O']

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

for i, idx in enumerate(species_indices):
    ax1.plot(times, production_rates_over_time[:, idx], label=species_names[i])
ax1.set_ylabel('Net Production Rate (mol/m^3·s)')
ax1.legend()
ax1.set_title('Net Production Rates of Key Species Over Time')
ax1.ticklabel_format(useOffset=False)

ax2.plot(times, temperatures_over_time, label='Temperature', linestyle='--', color='k')
ax2.set_ylabel('Temperature (K)')
ax2.set_xlabel('Time (s)')
ax2.legend()
ax2.set_title('Temperature Over Time')
ax2.ticklabel_format(useOffset=False)

plt.tight_layout()
plt.show()