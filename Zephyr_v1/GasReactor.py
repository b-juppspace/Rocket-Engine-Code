import cantera as ct
import matplotlib.pyplot as plt
import numpy as np

# Define initial conditions and gas mixture
temperature_initial = 300  # Initial temperature (K)
pressure_initial = ct.one_atm  # Initial pressure (Pa)
composition = 'CH4:1, O2:2'  # Composition (mole fractions)

# Load the GRI-Mech 3.0 mechanism
gas = ct.Solution('gri30.yaml')
gas.TPX = 900, pressure_initial, composition

# Create an IdealGasReactor object
reactor = ct.IdealGasReactor(gas)

# Create a ReactorNet object to handle the reactor network
net = ct.ReactorNet([reactor])

# Time-stepping parameters
end_time = 0.01  # Total simulation time (s)
time_step = 1e-5  # Time step size (s)

# Data storage
times = []
temperatures = []
species_concentrations = {}
pressures = []
heat_release_rate = []
reaction_rates = {}
emissions = {}

# Time-stepping loop
while net.time < end_time:
    net.step()
    times.append(net.time)
    temperatures.append(gas.T)
    for species in gas.species_names:
        if species not in species_concentrations:
            species_concentrations[species] = []
        species_concentrations[species].append(gas[species].X)
    pressures.append(gas.P)
    heat_release_rate.append(reactor.thermo.net_production_rates[gas.species_index('CO2')])  # Example: Heat release rate from CO2 formation
    for i, reaction in enumerate(gas.reactions()):
        if reaction.equation not in reaction_rates:
            reaction_rates[reaction.equation] = []
        reaction_rates[reaction.equation].append(gas.forward_rate_constants[i] * gas.net_rates_of_progress[i])
    for species in ['NO', 'CO', 'CH4']:  # Example: Emissions of NO, CO, and unburned CH4
        if species not in emissions:
            emissions[species] = []
        emissions[species].append(gas[species].X)


# Convert lists to numpy arrays for plotting
times = np.array(times)
temperatures = np.array(temperatures)
pressures = np.array(pressures)
heat_release_rate = np.array(heat_release_rate)
species_concentrations = {species: np.array(concentration) for species, concentration in species_concentrations.items()}
reaction_rates = {reaction: np.array(rate) for reaction, rate in reaction_rates.items()}
emissions = {species: np.array(emission) for species, emission in emissions.items()}


from scipy.interpolate import interp1d

# Identify the maximum length among all rate arrays
max_rate_length = max(len(rate) for rate in reaction_rates.values())
print(f'{max_rate_length}')
# Interpolate the reaction rates to match the length of the times array
interpolated_reaction_rates = {}
for reaction, rate in reaction_rates.items():
    if len(rate) < max_rate_length:
        interp_func = interp1d(times[:len(rate)], rate, kind='linear', fill_value='extrapolate')
        interpolated_reaction_rates[reaction] = interp_func(times[:max_rate_length])
    else:
        interpolated_reaction_rates[reaction] = rate

# Plotting
plt.figure(figsize=(12, 10))

# Temperature profile
plt.subplot(3, 2, 1)
plt.plot(times, temperatures)
plt.xlabel('Time (s)')
plt.ylabel('Temperature (K)')
plt.title('Temperature Profile Over Time')

# Species concentrations
plt.subplot(3, 2, 2)
for species in gas.species_names:
    plt.plot(times, species_concentrations[species], label=species)
plt.xlabel('Time (s)')
plt.ylabel('Mole Fraction')
plt.title('Species Concentrations Over Time')
plt.legend()

# Pressure profile
plt.subplot(3, 2, 3)
plt.plot(times, pressures)
plt.xlabel('Time (s)')
plt.ylabel('Pressure (Pa)')
plt.title('Pressure Profile Over Time')

# Heat release rate
plt.subplot(3, 2, 4)
plt.plot(times, heat_release_rate)
plt.xlabel('Time (s)')
plt.ylabel('Heat Release Rate (mol/m³·s)')
plt.title('Heat Release Rate Over Time')

# Reaction rates
#plt.subplot(3, 2, 5)
#for reaction, rate in interpolated_reaction_rates.items():
#    plt.plot(times, rate, label=reaction)
#plt.xlabel('Time (s)')
#plt.ylabel('Reaction Rate (mol/m³·s)')
#plt.title('Reaction Rates Over Time')
#plt.legend()


# Emissions
plt.subplot(3, 2, 6)
for species, emission in emissions.items():
    plt.plot(times, emission, label=species)
plt.xlabel('Time (s)')
plt.ylabel('Concentration (mol/m³)')
plt.title('Emissions Over Time')
plt.legend()

plt.tight_layout()
plt.show()
