import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

def ratio_plot(M_values, Pr_Ma, Ar_Ma, Tr_Ma, rhor_Ma):
    fig, ax1 = plt.subplots()

    color1 = 'tab:red'
    color2 = 'tab:green'
    color4 = 'tab:cyan'
    ax1.set_xlabel('Mach Number')
    ax1.set_ylabel('Pressure Ratio / Temperature Ratio / Density Ratio')
    ax1.plot(M_values, Pr_Ma, color=color1, label='Pressure Ratio P/P_o')
    ax1.plot(M_values, Tr_Ma, color=color2, label='Temperature Ratio T/T_o')
    ax1.plot(M_values, rhor_Ma, color=color4, label='Density Ratio rho/rho_o')
    ax1.tick_params(axis='y')
    ax1.set_ylim(0.01, 1)
    ax1.set_xlim(0.1)
    ax1.set_xscale('log')
    plt.gca().xaxis.set_major_formatter(ScalarFormatter())

    ax2 = ax1.twinx()
    color3 = 'tab:blue'
    ax2.set_ylabel('Area Ratio')
    ax2.plot(M_values, Ar_Ma, color=color3, label='Area Ratio A/A_t')
    ax2.tick_params(axis='y')
    ax2.set_ylim(1, 100)
    ax2.set_yscale('log')
    plt.gca().yaxis.set_major_formatter(ScalarFormatter())

    label_index = 20
    ax1.text(M_values[label_index], Pr_Ma[label_index], 'Pressure Ratio P/P_o', color=color1, verticalalignment='bottom')
    ax1.text(M_values[30], Tr_Ma[30], 'Temperature Ratio T/T_o', color=color2, verticalalignment='bottom')
    ax1.text(M_values[30], rhor_Ma[30], 'Density Ratio rho/rho_o', color=color4, verticalalignment='bottom')
    ax2.text(M_values[label_index], Ar_Ma[label_index], 'Area Ratio A/A_t', color=color3, verticalalignment='bottom')

    plt.title('Pressure Ratio, Area Ratio, and Temperature Ratio vs Mach Number')
    fig.tight_layout()
    plt.show()
