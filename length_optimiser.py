import matplotlib.pyplot as plt
import numpy as np

# To optimise this we normalise both the L_cone and ue_correction_factor equations creating a composite
# objective function to balance the tradeoff. The the optimal 'theta' is found that minimises the 
# objective function. The normalised values are plotted, highlighting the optimal 'theta'.

def plot_and_optimize(theta, L_cone, ue_correction_factor, w1=0.5, w2=0.5):
    # Normalize values
    L_cone_normalized = (L_cone - np.min(L_cone)) / (np.max(L_cone) - np.min(L_cone))
    ue_correction_factor_normalized = (ue_correction_factor - np.min(ue_correction_factor)) / (np.max(ue_correction_factor) - np.min(ue_correction_factor))
    
    # Composite objective function (to minimize)
    objective_function = w1 * L_cone_normalized - w2 * ue_correction_factor_normalized

    # Find the optimal point
    optimal_index = np.argmin(objective_function)
    optimal_theta = theta[optimal_index]
    optimal_L_cone = L_cone[optimal_index]
    optimal_ue_correction_factor = ue_correction_factor[optimal_index]

    # Plotting
    plt.figure()
    plt.plot(theta, L_cone_normalized, label='Normalized Length of Cone')
    plt.plot(theta, ue_correction_factor_normalized, label='Normalized Correction Factor')
    plt.axvline(optimal_theta, color='gray', linestyle='--', label=f'Optimal Theta = {optimal_theta:.2f}')
    plt.xlabel('Theta (degrees)')
    plt.ylabel('Normalized Values')
    plt.legend()
    plt.title('Tradeoff Analysis for Length of Cone and Correction Factor')
    plt.grid(True)
    plt.show()

    # Print optimal values
    print(f'Optimal Theta: {optimal_theta:.1f} deg')
    print(f'Optimal Length of Cone: {optimal_L_cone:.3f} m')
    print(f'Optimal Correction Factor: {optimal_ue_correction_factor:.3f}')

    return optimal_theta, optimal_L_cone, optimal_ue_correction_factor

