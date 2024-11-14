import CoolProp.CoolProp as CP
import numpy as np
import matplotlib.pyplot as plt

# Define the substance
substance = 'Methane'

# Define the range of temperatures (K)
temperatures = np.linspace(200, 2000, 10)  # 10 temperatures from 200K to 2000K

# Define the range of pressures (Pa)
pressures = np.linspace(100000, 1000000, 100)  # Pressure range from 10,000 Pa to 10,000,000 Pa

# Initialize a dictionary to hold volume values for each temperature
volume_data = {T: [] for T in temperatures}
saturation_liquid = []
saturation_vapor = []

# Calculate volumes for each temperature and pressure
for T in temperatures:
    for P in pressures:
        try:
            # Calculate the molar volume (m^3/mol)
            volume = CP.PropsSI('Dmolar', 'T', T, 'P', P, substance) ** -1
            volume_data[T].append(volume)
        except ValueError:
            volume_data[T].append(np.nan)  # Handle values that CoolProp can't calculate

    # Get saturation properties at this temperature
    try:
        Psat = CP.PropsSI('P', 'T', T, 'Q', 0, substance)  # Saturation pressure
        v_liquid = CP.PropsSI('Dmolar', 'T', T, 'Q', 0, substance) ** -1  # Liquid molar volume
        v_vapor = CP.PropsSI('Dmolar', 'T', T, 'Q', 1, substance) ** -1  # Vapor molar volume
        saturation_liquid.append((v_liquid, Psat))
        saturation_vapor.append((v_vapor, Psat))
    except ValueError:
        pass

# Plot the P-V diagram
plt.figure(figsize=(10, 6))
for T in temperatures:
    plt.plot(volume_data[T], pressures, label=f'T = {T} K')


plt.xlabel('Molar Volume (m^3/mol)')
plt.ylabel('Pressure (Pa)')
plt.title('P-V Diagram for Methane at Different Temperatures')



# Plot saturation lines
if saturation_liquid and saturation_vapor:
    v_liquid, P_liquid = zip(*saturation_liquid)
    v_vapor, P_vapor = zip(*saturation_vapor)
    plt.plot(v_liquid, P_liquid, 'r--', label='Saturation Liquid')
    plt.plot(v_vapor, P_vapor, 'b--', label='Saturation Vapor')

plt.legend()
plt.grid(True, which="both", ls="--")

plt.show()

