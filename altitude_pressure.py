def exit_pressure_at_altitude(altitude):
    # Constants
    P0 = 101.325  # kPa (sea level pressure)
    L = 0.0065    # Temperature lapse rate in K/m
    T0 = 288.15   # Standard temperature at sea level in K
    g = 9.80665   # Gravitational acceleration in m/s^2
    M = 0.0289644 # Molar mass of Earth's air in kg/mol
    R = 8.3144598 # Universal gas constant in J/(mol K)

    # Calculate pressure at given altitude
    Pe = P0 * (1 - (L * altitude) / T0) ** (g * M / (R * L))
    return Pe