
import seaborn as sns
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from xa_dose_analysis import reporting_module as bh_report

# This module contains functions for performing the various common plots.

def plot_representative_dose_by_procedure(data, y_max=20, save=False):
    """
    This function will create a boxplot with whiskers.
    The line in the middle will represent the median.
    The box will represent the interquartile range (IQR) of the data.
    The whiskers will represent the 2.5th to 97.5th percentile.
    The dots will represent the outliers.
    There will be one box per procedure
    """

    # Create a dataframe with the data for the procedure:
    data = data.sort_values(by=['Mapped Procedures'])
    
    # Make a boxplot:
    fig, ax = plt.subplots(figsize=(15, 10))
    sns.boxplot(x='Mapped Procedures', y='DAP Total (Gy*cm2)', data=data, ax=ax)
    
    # Reduce the range of the y-axis:
    if y_max > 0:
        ax.set_ylim([0, y_max])
    else:
        y_max = data['DAP Total (Gy*cm2)'].max()

    # add an annotation to the top of the axis with the maximum value and number of observations outside the plot area:
    list_max = []
    list_n_outside = []
    for xtick in ax.get_xticklabels():
        list_max.append(data[data['Mapped Procedures'] == xtick.get_text()]['DAP Total (Gy*cm2)'].max())
        list_n_outside.append(data[data['Mapped Procedures'] == xtick.get_text()]['DAP Total (Gy*cm2)'].gt(y_max).sum())
        
    # Put an annotation on the axis:
    for i, xtick in enumerate(ax.get_xticklabels()):
        if list_max[i] > y_max:
            ax.annotate('Maks = ' + str(round(list_max[i], 1)) + '\n' + 'n$_{(>'+ str(y_max) + ')}$ = ' + str(list_n_outside[i]), xy=(i, y_max), \
                        xytext=(i, y_max + y_max/20), ha='center', va='bottom', fontsize=10 , arrowprops=dict(facecolor='black', shrink=0.05), rotation=90)


    # Add a different string to each x-ticklabel:
    labels = []
    for i, xtick in enumerate(ax.get_xticklabels()):
        n_obs = len(data[data['Mapped Procedures'] == xtick.get_text()])
        labels.append(xtick.get_text() + '\n' +'(' + 'n = ' + str(n_obs) + ')')
    _ = ax.set_xticklabels(labels, rotation=90)





    # Add a title:
    _ = plt.suptitle('Overview Procedures', fontsize=30, y=1.07)
    # Set new label for the x-axis:
    _ = ax.set_xlabel('Prosedyre')
    # Set new label for the y-axis:
    _ = ax.set_ylabel('DAP (Gy*cm2)')
    # Increase the size of the title and labels:
    _ = ax.xaxis.label.set_size(30)
    _ = ax.yaxis.label.set_size(30)
    # Add a weak dotted grid to the plot:
    _ = ax.grid(True, linestyle=':', linewidth=0.5)


    # Increase the font size of the x-ticklabels:
    _ = ax.tick_params(labelsize=10)   
    print('-'*50)
    print('\n')

    if save:
        if not os.path.exists('Figures'):
            os.makedirs('Figures')
        # if the procedure contains a forward slash, replace it with a dash:
        procedure = procedure.replace('/', '-')
        fig.savefig('Figures/oversikt.png', bbox_inches='tight')
    return

def plot_air_kerma_angle_heatmap(exp_data, procedure_name, bin_size=10, plot_absolute=False, save=False):
    """
    Plots heatmaps of Air Kerma distribution over C-arm angles:
    1. (Optional) Absolute Air Kerma (mGy) summed per angle bin
    2. Normalized Air Kerma (% of total) per angle bin
    
    Parameters
    ----------
    exp_data : pd.DataFrame
        Exposure-level data containing angle and Air Kerma columns.
    procedure_name : str
        Name of the procedure (used for title and filename).
    bin_size : int
        Size of angle bins in degrees (default 10).
    plot_absolute : bool
        If True, also plots the absolute Air Kerma heatmap (default False).
    save : bool
        If True, saves the figures to the Figures folder.
    """
    col_primary = "Positioner Primary Angle (deg)"
    col_secondary = "Positioner Secondary Angle (deg)"
    col_ak = "Air Kerma (mGy)"

    # Drop rows with missing values in the relevant columns:
    df = exp_data[[col_primary, col_secondary, col_ak]].dropna()

# Define bins covering the full range of possible angles (centered on multiples of bin_size):
    half = bin_size / 2
    primary_bins = np.arange(0 - half, 180 + half + bin_size, bin_size)
    primary_bins = np.unique(np.concatenate([-primary_bins[::-1], primary_bins]))
    secondary_bins = np.arange(0 - half, 90 + half + bin_size, bin_size)
    secondary_bins = np.unique(np.concatenate([-secondary_bins[::-1], secondary_bins]))

    # Bin the angles and sum the Air Kerma per bin:
    df = df.copy()
    df['primary_bin'] = pd.cut(df[col_primary], bins=primary_bins, right=False)
    df['secondary_bin'] = pd.cut(df[col_secondary], bins=secondary_bins, right=False)
    
    heatmap_data = df.groupby(['secondary_bin', 'primary_bin'], observed=False)[col_ak].sum().unstack(fill_value=0)

    # Create axis labels from bin centers:
    x_labels = [f"{int(b.left + half)}" for b in heatmap_data.columns]
    y_labels = [f"{int(b.left + half)}" for b in heatmap_data.index]

    # Reverse y-axis so cranial is on top:
    heatmap_data = heatmap_data.iloc[::-1]
    y_labels = y_labels[::-1]

    # Trim to only show bins that have data (with 1 bin margin):
    col_mask = heatmap_data.sum(axis=0) > 0
    row_mask = heatmap_data.sum(axis=1) > 0
    
    # Find the index of the "0" label (center bin) in each axis:
    col_center = x_labels.index("0")
    row_center = y_labels.index("0")

    # Find the max distance from center to any bin with data (+ 1 bin margin):
    col_indices = np.where(col_mask)[0]
    row_indices = np.where(row_mask)[0]
    col_extent = max(col_center - col_indices.min(), col_indices.max() - col_center) + 1
    row_extent = max(row_center - row_indices.min(), row_indices.max() - row_center) + 1

    # Clamp to valid range:
    col_start = max(0, col_center - col_extent)
    col_end = min(len(x_labels), col_center + col_extent + 1)
    row_start = max(0, row_center - row_extent)
    row_end = min(len(y_labels), row_center + row_extent + 1)

    heatmap_trimmed = heatmap_data.iloc[row_start:row_end, col_start:col_end]
    x_labels_trimmed = x_labels[col_start:col_end]
    y_labels_trimmed = y_labels[row_start:row_end]

    # Mask for cells with no Air Kerma:
    zero_mask = heatmap_trimmed == 0

    proc_safe = procedure_name.replace('/', '-')

    # --- Plot 1: Absolute Air Kerma (optional) ---
    if plot_absolute:
        fig1, ax1 = plt.subplots(figsize=(14, 8))
        sns.heatmap(heatmap_trimmed, ax=ax1, cmap='YlOrRd', linewidths=0.5, linecolor='grey',
                    xticklabels=x_labels_trimmed, yticklabels=y_labels_trimmed,
                    mask=zero_mask,
                    cbar_kws={'label': 'Air Kerma (mGy)'})
        ax1.set_xlabel('LAO / RAO angle (deg)\n← RAO    |    LAO →', fontsize=14)
        ax1.set_ylabel('Cranial / Caudal angle (deg)\n← Caudal    |    Cranial →', fontsize=14)
        ax1.set_title(f'{procedure_name} — Air Kerma by C-arm angle', fontsize=20)
        ax1.tick_params(labelsize=10)
        plt.tight_layout()

        if save:
            if not os.path.exists('Figures'):
                os.makedirs('Figures')
            fig1.savefig(f'Figures/{proc_safe}_AK_angles_absolute.png', bbox_inches='tight')

    # --- Plot 2: Normalized (percentage) ---
    total_ak = heatmap_trimmed.values.sum()
    heatmap_pct = (heatmap_trimmed / total_ak) * 100

    fig2, ax2 = plt.subplots(figsize=(14, 8))
    sns.heatmap(heatmap_pct, ax=ax2, cmap='YlOrRd', linewidths=0.5, linecolor='grey',
                xticklabels=x_labels_trimmed, yticklabels=y_labels_trimmed,
                mask=zero_mask,
                cbar_kws={'label': '% of total Air Kerma'})
    ax2.set_xlabel('LAO / RAO angle (deg)\n← RAO    |    LAO →', fontsize=14)
    ax2.set_ylabel('Cranial / Caudal angle (deg)\n← Caudal    |    Cranial →', fontsize=14)
    ax2.set_title(f'{procedure_name} — Air Kerma distribution by C-arm angle (%)', fontsize=20)
    ax2.tick_params(labelsize=10)
    plt.tight_layout()

    if save:
        if not os.path.exists('Figures'):
            os.makedirs('Figures')
        fig2.savefig(f'Figures/{proc_safe}_AK_angles_percent.png', bbox_inches='tight')

    plt.show()

def plot_representative_dose(data, procedure, y_max=20, save=False):
    """
    This function will create a boxplot with whiskers.
    The line in the middle will represent the median.
    The box will represent the interquartile range (IQR) of the data.
    The whiskers will represent the 2.5th to 97.5th percentile.
    The dots will represent the outliers.
    There will be one box per room that has performed the procedure.
    """

    # Create a dataframe with the data for the procedure: .str.contains
    data = data[data['Mapped Procedures'] == procedure]
    data = data.sort_values(by=['Modality Room'])
    
    # Make a boxplot:
    fig, ax = plt.subplots(figsize=(15, 10))
    sns.boxplot(x='Modality Room', y='DAP Total (Gy*cm2)', data=data, ax=ax)
    print('Reporting doses for ' + procedure + ':')
    print('\n')
    bh_report.print_summary(data[data['Mapped Procedures'] == procedure], True)
    print('\n')
    bh_report.print_summary_per_lab(data[data['Mapped Procedures'] == procedure], True)
    # Reduce the range of the y-axis:
    if y_max > 0:
        ax.set_ylim([0, y_max])
    else:
        y_max = data['DAP Total (Gy*cm2)'].max()

    # add an annotation to the top of the axis with the maximum value and number of observations outside the plot area:
    list_max = []
    list_n_outside = []
    for xtick in ax.get_xticklabels():
        list_max.append(data[data['Modality Room'] == xtick.get_text()]['DAP Total (Gy*cm2)'].max())
        list_n_outside.append(data[data['Modality Room'] == xtick.get_text()]['DAP Total (Gy*cm2)'].gt(y_max).sum())
        
    # Put an annotation on the axis:
    for i, xtick in enumerate(ax.get_xticklabels()):
        if list_max[i] > y_max:
            ax.annotate('Maks = ' + str(round(list_max[i], 1)) + '\n' + 'n$_{(>'+ str(y_max) + ')}$ = ' + str(list_n_outside[i]), xy=(i, y_max), \
                        xytext=(i, y_max + y_max/20), ha='center', va='bottom', fontsize=12 , arrowprops=dict(facecolor='black', shrink=0.05))


    # Add a different string to each x-ticklabel:
    labels = []
    for i, xtick in enumerate(ax.get_xticklabels()):
        n_obs = len(data[data['Modality Room'] == xtick.get_text()])
        labels.append(xtick.get_text() + '\n' +'(' + 'n = ' + str(n_obs) + ')')
    _ = ax.set_xticklabels(labels)

    # Add a title:
    _ = plt.suptitle(procedure, fontsize=30, y=1.04)
    # Set new label for the x-axis:
    _ = ax.set_xlabel('Lab')
    # Set new label for the y-axis:
    _ = ax.set_ylabel('DAP (Gy*cm2)')
    # Increase the size of the title and labels:
    _ = ax.xaxis.label.set_size(30)
    _ = ax.yaxis.label.set_size(30)
    # Add a weak dotted grid to the plot:
    _ = ax.grid(True, linestyle=':', linewidth=0.5)


    # Increase the font size of the x-ticklabels:
    _ = ax.tick_params(labelsize=15)   
    print('-'*50)
    print('\n')

    if save:
        if not os.path.exists('Figures'):
            os.makedirs('Figures')
        # if the procedure contains a forward slash, replace it with a dash:
        procedure = procedure.replace('/', '-')
        fig.savefig('Figures/' + procedure + '.png', bbox_inches='tight')
    return



# This function will delete all plots in the Figures folder.
def delete_all_plots(delete_folder=False):
    """
    This function will delete all plots in the Figures folder.
    """
    files = glob.glob('Figures/*')
    for f in files:
        os.remove(f)
    if delete_folder:
        if os.path.exists('Figures'):
            os.rmdir('Figures')
    return