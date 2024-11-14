import cantera as ct
import numpy as np
import pandas as pd



from matplotlib import pyplot as plt
import matplotlib

from IPython.display import display, HTML

import scipy
import scipy.optimize

# Import plotting modules and define plotting preference

plt.rcParams["axes.labelsize"] = 14
plt.rcParams["xtick.labelsize"] = 12
plt.rcParams["ytick.labelsize"] = 12
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["figure.figsize"] = (8, 6)
plt.rcParams["figure.dpi"] = 120

# Get the best of both ggplot and seaborn
plt.style.use("ggplot")
plt.style.use("seaborn-v0_8-deep")

plt.rcParams["figure.autolayout"] = True

def extrapolate_uncertainty(grids, speeds, plot=True):
    """
    Given a list of grid sizes and a corresponding list of flame speeds,
    extrapolate and estimate the uncertainty in the final flame speed.
    Also makes a plot, unless called with `plot=False`.
    """
    grids = list(grids)
    speeds = list(speeds)

    def speed_from_grid_size(grid_size, true_speed, error):
        """
        Given a grid size (or an array or list of grid sizes)
        return a prediction (or array of predictions)
        of the computed flame speed, based on
        the parameters `true_speed` and `error`.

        It seems, from experience, that error scales roughly with
        1/grid_size, so we assume that form.
        """
        return true_speed + error / np.array(grid_size)

    # Fit the chosen form of speed_from_grid_size, to the last four
    # speed and grid size values.
    popt, pcov = scipy.optimize.curve_fit(speed_from_grid_size, grids[-4:], speeds[-4:])

    # How bad the fit was gives you some error, `percent_error_in_true_speed`.
    perr = np.sqrt(np.diag(pcov))
    true_speed_estimate = popt[0]
    percent_error_in_true_speed = perr[0] / popt[0]
    print(
        f"Fitted true_speed is {popt[0] * 100:.4f} ± {perr[0] * 100:.4f} cm/s "
        f"({percent_error_in_true_speed:.1%})"
    )

    # How far your extrapolated infinite grid value is from your extrapolated
    # (or interpolated) final grid value, gives you some other error, `estimated_percent_error`
    estimated_percent_error = (
        speed_from_grid_size(grids[-1], *popt) - true_speed_estimate
    ) / true_speed_estimate
    print(f"Estimated error in final calculation {estimated_percent_error:.1%}")

    # The total estimated error is the sum of these two errors.
    total_percent_error_estimate = abs(percent_error_in_true_speed) + abs(
        estimated_percent_error
    )
    print(f"Estimated total error {total_percent_error_estimate:.1%}")

    if plot:
        plt.semilogx(grids, speeds, "o-")
        plt.ylim(
            min(speeds[-5:] + [true_speed_estimate - perr[0]]) * 0.95,
            max(speeds[-5:] + [true_speed_estimate + perr[0]]) * 1.05,
        )
        plt.plot(grids[-4:], speeds[-4:], "or")
        extrapolated_grids = grids + [grids[-1] * i for i in range(2, 8)]
        plt.plot(
            extrapolated_grids, speed_from_grid_size(extrapolated_grids, *popt), ":r"
        )
        plt.xlim(*plt.xlim())
        plt.hlines(true_speed_estimate, *plt.xlim(), colors="r", linestyles="dashed")
        plt.hlines(
            true_speed_estimate + perr[0],
            *plt.xlim(),
            colors="r",
            linestyles="dashed",
            alpha=0.3,
        )
        plt.hlines(
            true_speed_estimate - perr[0],
            *plt.xlim(),
            colors="r",
            linestyles="dashed",
            alpha=0.3,
        )
        plt.fill_between(
            plt.xlim(),
            true_speed_estimate - perr[0],
            true_speed_estimate + perr[0],
            facecolor="red",
            alpha=0.1,
        )

        above = popt[1] / abs(
            popt[1]
        )  # will be +1 if approach from above or -1 if approach from below

        plt.annotate(
            "",
            xy=(grids[-1], true_speed_estimate),
            xycoords="data",
            xytext=(grids[-1], speed_from_grid_size(grids[-1], *popt)),
            textcoords="data",
            arrowprops=dict(
                arrowstyle="|-|, widthA=0.5, widthB=0.5",
                linewidth=1,
                connectionstyle="arc3",
                color="black",
                shrinkA=0,
                shrinkB=0,
            ),
        )

        plt.annotate(
            f"{abs(estimated_percent_error):.1%}",
            xy=(grids[-1], speed_from_grid_size(grids[-1], *popt)),
            xycoords="data",
            xytext=(5, 15 * above),
            va="center",
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
        )

        plt.annotate(
            "",
            xy=(grids[-1] * 4, true_speed_estimate - (above * perr[0])),
            xycoords="data",
            xytext=(grids[-1] * 4, true_speed_estimate),
            textcoords="data",
            arrowprops=dict(
                arrowstyle="|-|, widthA=0.5, widthB=0.5",
                linewidth=1,
                connectionstyle="arc3",
                color="black",
                shrinkA=0,
                shrinkB=0,
            ),
        )
        plt.annotate(
            f"{abs(percent_error_in_true_speed):.1%}",
            xy=(grids[-1] * 4, true_speed_estimate - (above * perr[0])),
            xycoords="data",
            xytext=(5, -15 * above),
            va="center",
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
        )

        plt.ylabel("Flame speed (m/s)")
        plt.xlabel("Grid size")
        plt.show()

    return true_speed_estimate, total_percent_error_estimate

def make_callback(flame):
    """
    Create and return a callback function that you will attach to
    a flame solver. The reason we define a function to make the callback function,
    instead of just defining the callback function, is so that it can store
    a pair of lists that persist between function calls, to store the
    values of grid size and flame speed.

    This factory returns the callback function, and the two lists:
    (callback, speeds, grids)
    """
    speeds = []
    grids = []

    def callback(_):
        speed = flame.velocity[0]
        grid = len(flame.grid)
        speeds.append(speed)
        grids.append(grid)
        print(f"Iteration {len(grids)}")
        print(f"Current flame speed is is {speed * 100:.4f} cm/s")
        if len(grids) < 5:
            return 1.0  #
        try:
            extrapolate_uncertainty(grids, speeds)
        except Exception as e:
            print("Couldn't estimate uncertainty. " + str(e))
            return 1.0  # continue anyway
        return 1.0

    return callback, speeds, grids

# Inlet Temperature in Kelvin and Inlet Pressure in Pascals
# In this case we are setting the inlet T and P to room temperature conditions
# CHANGE INLET PRESSURE WHEN CALCULATED
To = 300
Po = 101325 * 5

# Define the gas-mixutre and kinetics
# In this case, we are choosing a GRI3.0 gas
gas = ct.Solution("gri30.yaml")

# Create a stoichiometric CH4/Air premixed mixture
gas.set_equivalence_ratio(1.0, "CH4", {"O2": 7.1066})
gas.TP = To, Po

# Domain width in metres
width = 0.014

# Create the flame object
flame = ct.FreeFlame(gas, width=width)

# Define logging level
loglevel = 1

# Define tight tolerances for the solver
refine_criteria = {"ratio": 2, "slope": 0.01, "curve": 0.01}
flame.set_refine_criteria(**refine_criteria)

# Set maxiumum number of grid points to be very high (otherwise default is 1000)
flame.set_max_grid_points(flame.domains[flame.domain_index("flame")], 1e4)

# Set up the the callback function and lists of speeds and grids
callback, speeds, grids = make_callback(flame)
flame.set_steady_callback(callback)

flame.solve(loglevel=loglevel, auto=True)

Su0 = flame.velocity[0]
print(f"Flame Speed is: {Su0 * 100:.2f} cm/s")

best_true_speed_estimate, best_total_percent_error_estimate = extrapolate_uncertainty(
    grids, speeds
)

best_true_speed_estimate