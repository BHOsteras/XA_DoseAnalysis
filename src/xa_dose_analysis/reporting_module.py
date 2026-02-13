# This module contains utility function to report various properties of the data.

import pandas as pd

def _calc_ci(data_vector, ci = 95, n = 10000):
    """
    This function calculated the confidence interval of the median of the data_vector.
    The default number of bootstrap samples is 1000.
    """
    # Create an empty list to store the medians of the bootstrap samples:
    medians = []
    # Create a for loop to create the bootstrap samples:
    for i in range(n):
        # Create a bootstrap sample:
        sample = data_vector.sample(frac=1, replace=True)
        # Calculate the median of the bootstrap sample:
        medians.append(sample.median())
    # Create a pandas series of the medians:
    ci = pd.Series(medians)
    # Return the median and the confidence interval:
    return ci.quantile(0.025), ci.quantile(0.975)

def _format_min_sec(data_vector):
    """
    This function formats the data_vector from seconds to minutes and seconds.
    Then the function returns the minutes and seconds as strings.
    If there is less than 10 seconds the function returns a string with a leading zero.
    """
    minutes, seconds = divmod(data_vector, 60)
    minutes = str(round(minutes))
    seconds = round(seconds)
    if seconds < 10:
        seconds = '0' + str(round(seconds))
    else:
        seconds = str(round(seconds))
    return minutes, seconds


def print_obs_per_lab(data):
    for lab in data['Modality Room'].unique():
        print(lab + ': n = ' + str(len(data[data['Modality Room'] == lab])))

def print_median_dap_per_lab(data):
    for lab in data['Modality Room'].unique():
        print(lab + ': DAP = ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].median(), 1)) + ' Gy*cm2')

def print_summary_per_lab(data, ci = False):
    data = data.sort_values(by=['Modality Room'])
    for lab in data['Modality Room'].unique():
        if ci:
            lci, uci = _calc_ci(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'])
        print(lab + ': n = {:4}'.format(len(data[data['Modality Room'] == lab])) + \
              ', DAP: Median - ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].median(), 2)) + ' (Gy*cm2),' + \
              (' 95% CI: [' + str(round(lci, 2)) + ' - ' + str(round(uci, 2)) + ']' if ci else '') + \
              # 25 th percentile:
              ' IQR [' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].quantile(0.25), 2)) + \
              ' - ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].quantile(0.75), 2)) + '], ' + \
              'Range (' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].min(), 2)) + \
              ' - ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].max(), 2)) + ').')

def print_summary_per_lab_inc_cak(data, ci = False):
    data = data.sort_values(by=['Modality Room'])
    for lab in data['Modality Room'].unique():
        if ci:
            lci, uci = _calc_ci(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'])
        print(lab + ': n = {:4}'.format(len(data[data['Modality Room'] == lab])) + \
              ', DAP: Median - ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].median(), 2)) + ' (Gy*cm2),' + \
              (' 95% CI: [' + str(round(lci, 2)) + ' - ' + str(round(uci, 2)) + ']' if ci else '') + \
              # 25 th percentile:
              ' IQR [' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].quantile(0.25), 2)) + \
              ' - ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].quantile(0.75), 2)) + '], ' + \
              'Range (' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].min(), 2)) + \
              ' - ' + str(round(data[data['Modality Room'] == lab]['DAP Total (Gy*cm2)'].max(), 2)) + ').')
        if ci:
            lci_cak, uci_cak = _calc_ci(data[data['Modality Room'] == lab]['CAK (mGy)'])
        print(lab + ': n = {:4}'.format(len(data[data['Modality Room'] == lab])) + \
              ', CAK: Median - ' + str(round(data[data['Modality Room'] == lab]['CAK (mGy)'].median(), 2)) + ' (mGy),' + \
              (' 95% CI: [' + str(round(lci_cak, 2)) + ' - ' + str(round(uci_cak, 2)) + ']' if ci else '') + \
              # 25 th percentile:
              ' IQR [' + str(round(data[data['Modality Room'] == lab]['CAK (mGy)'].quantile(0.25), 2)) + \
              ' - ' + str(round(data[data['Modality Room'] == lab]['CAK (mGy)'].quantile(0.75), 2)) + '], ' + \
              'Range (' + str(round(data[data['Modality Room'] == lab]['CAK (mGy)'].min(), 2)) + \
              ' - ' + str(round(data[data['Modality Room'] == lab]['CAK (mGy)'].max(), 2)) + ').')

def print_summary(data, ci = False):
    if ci:
        lci, uci = _calc_ci(data['DAP Total (Gy*cm2)'])

    print('Alle: n = {:4}'.format(len(data)) + ', DAP: Median - ' + str(round(data['DAP Total (Gy*cm2)'].median(), 1)) + ',' +\
            (' 95% CI: [' + str(round(lci, 2)) + ' - ' + str(round(uci, 2)) + ']' if ci else '') + \
            # 25 th percentile:
            ' IQR [' + str(round(data['DAP Total (Gy*cm2)'].quantile(0.25), 1)) + \
            ' - ' + str(round(data['DAP Total (Gy*cm2)'].quantile(0.75), 1)) + '], ' + \
            'Range (' + str(round(data['DAP Total (Gy*cm2)'].min(), 1)) + \
            ' - ' + str(round(data['DAP Total (Gy*cm2)'].max(), 1)) + ').')

def print_summary_inc_cak(data, ci = False):
    if ci:
        lci, uci = _calc_ci(data['DAP Total (Gy*cm2)'])

    print('Alle: n = {:4}'.format(len(data)) + ', DAP: Median - ' + str(round(data['DAP Total (Gy*cm2)'].median(), 1)) + ',' +\
            (' 95% CI: [' + str(round(lci, 2)) + ' - ' + str(round(uci, 2)) + ']' if ci else '') + \
            # 25 th percentile:
            ' IQR [' + str(round(data['DAP Total (Gy*cm2)'].quantile(0.25), 1)) + \
            ' - ' + str(round(data['DAP Total (Gy*cm2)'].quantile(0.75), 1)) + '], ' + \
            'Range (' + str(round(data['DAP Total (Gy*cm2)'].min(), 1)) + \
            ' - ' + str(round(data['DAP Total (Gy*cm2)'].max(), 1)) + ').')
    if ci:
        lci, uci = _calc_ci(data['CAK (mGy)'])

    print('Alle: n = {:4}'.format(len(data)) + ', CAK: Median - ' + str(round(data['CAK (mGy)'].median(), 1)) + ',' +\
            (' 95% CI: [' + str(round(lci, 2)) + ' - ' + str(round(uci, 2)) + ']' if ci else '') + \
            # 25 th percentile:
            ' IQR [' + str(round(data['CAK (mGy)'].quantile(0.25), 1)) + \
            ' - ' + str(round(data['CAK (mGy)'].quantile(0.75), 1)) + '], ' + \
            'Range (' + str(round(data['CAK (mGy)'].min(), 1)) + \
            ' - ' + str(round(data['CAK (mGy)'].max(), 1)) + ').')

def report_exposure_time_all(data, ci = False):
    if ci:
        lci, uci = _calc_ci(data['F+A Time (s)'])
    
    median_min, median_sec = _format_min_sec(data['F+A Time (s)'].median())
    
    if ci:
        lci_min, lci_sec = _format_min_sec(lci)
        uci_min, uci_sec = _format_min_sec(uci)
    
    lIQR_min, lIQR_sec = _format_min_sec(data['F+A Time (s)'].quantile(0.25))
    uIQR_min, uIQR_sec = _format_min_sec(data['F+A Time (s)'].quantile(0.75))
    lrange_min, lrange_sec = _format_min_sec(data['F+A Time (s)'].min())
    urange_min, urange_sec = _format_min_sec(data['F+A Time (s)'].max())

    print('All '+ ': n = {:4}'.format(len(data)) + \
        ', Exposure time: Median - ' + median_min + ':' + median_sec + ' (min:s),' + \
        (' 95% CI: [' + lci_min + ':' + lci_sec + ' - ' + uci_min + ':' + uci_sec + ']' if ci else '') + \
        # 25 th percentile:
        ' IQR [' + lIQR_min + ':' + lIQR_sec + ' - ' + uIQR_min + ':' + uIQR_sec + '], ' + \
        'Range (' + lrange_min + ':' + lrange_sec + ' - '  + urange_min + ':' + urange_sec + ').')

def report_exposure_time_per_lab(data, ci = False):
    data = data.sort_values(by=['Modality Room'])
    
    for lab in data['Modality Room'].unique():
        if ci:
            lci, uci = _calc_ci(data[data['Modality Room'] == lab]['F+A Time (s)'])
        
        median_min, median_sec = _format_min_sec(data[data['Modality Room'] == lab]['F+A Time (s)'].median())
        
        if ci:
            lci_min, lci_sec = _format_min_sec(lci)
            uci_min, uci_sec = _format_min_sec(uci)
        
        lIQR_min, lIQR_sec = _format_min_sec(data[data['Modality Room'] == lab]['F+A Time (s)'].quantile(0.25))
        uIQR_min, uIQR_sec = _format_min_sec(data[data['Modality Room'] == lab]['F+A Time (s)'].quantile(0.75))
        lrange_min, lrange_sec = _format_min_sec(data[data['Modality Room'] == lab]['F+A Time (s)'].min())
        urange_min, urange_sec = _format_min_sec(data[data['Modality Room'] == lab]['F+A Time (s)'].max())

        print(lab + ': n = {:4}'.format(len(data[data['Modality Room'] == lab])) + \
        ', Exposure time: Median - ' + median_min + ':' + median_sec + ' (min:s),' + \
        (' 95% CI: [' + lci_min + ':' + lci_sec + ' - ' + uci_min + ':' + uci_sec + ']' if ci else '') + \
        # 25 th percentile:
        ' IQR [' + lIQR_min + ':' + lIQR_sec + ' - ' + uIQR_min + ':' + uIQR_sec + '], ' + \
        'Range (' + lrange_min + ':' + lrange_sec + ' - '  + urange_min + ':' + urange_sec + ').')