"""
This module contains functions for working with exports from IDS7 and DoseTrack.

-------------------------------- IDS7 Excel Data: --------------------------------
These functions reqire an export of the IDS7 worklist data with the column titles in the first row.
The following columns are required:
Henvisnings-ID
Beskrivelse

The following columns are recommended:
Bestilt dato og tidspunkt
Avbrutt
Henvisningskategori (RIS)

The following columns are optional:
Kjønn
Pasient:    This is required for the functions aimed at detecting and correcting errors in the datasets. 
            E.G. multiple accessions on the same patient.
-------------------------------------------------------------------------------------

-------------------------------- DoseTrack Excel Data: --------------------------------
These functions require an export of the DoseTrack data with the column titles in the first row.
It is usually a good idea right after the excel export to filter the excel file by using only the rows with ordinal = 1.
This will greatly reduce the size of the excel file while still maintaining the procedure level data.
For Acquisition level data, another python module should be created.

The following columns are required in the DoseTrack data:
Accession Number
-------------------------------------------------------------------------------------

The following functions are included in this module:

-------------------------------- Filtering the data: --------------------------------
remove_unnecessary_columns: Which removes the a few unnessecary columns from the IDS7 dataframe:
                            Prioritet- og lesemerkeikon, Lagt til i demonstrasjon-ikon og Status.

filter_NaT:                 Removes rows with NaT in the column 'Bestilt dato og tidspunkt'.

filter_cancelled:           Removes rows where the procedures have been cancelled: 'Avbrutt' == 'Avbrutt'.

filter_phantom_etc:         Removes rows representing non-human subjects: 'Henvisningskategori (RIS)' == 'X Fantom/objekt/dyr/test'.
-------------------------------------------------------------------------------------

-------------------------------- Checking the data: --------------------------------
check_accession_format:     Checks if the accession number has a correct start and length.
                            The currently allowed accession numbers are:
                            (NORRH|NRRH|NRAK|NIRH|NKRH|NKUL|NNRH|NRRA|NRUL)

check_accession_ids7_vs_dt: Checks whether the accession numbers in IDS7 are in DoseTrack.
                            It will add a column to the ids7 dataframe called Henvisning_i_dt which is true or false, correspondigly.

check_accession_dt_vs_ids7: Checks whether the accession numbers in DoseTrack are in IDS7.
                            It will add a column to the DoseTrack dataframe called Henvisning_i_ids7 which is true or false, correspondigly.
-------------------------------------------------------------------------------------

--------------- Attempt to detect and correct errrors in the datasets: --------------
check_patents_with_multiple_bookings_on_same_time_with_different_accession: 
                            
                            This function is used to report whether there are patients with multiple bookings on the
                            same time with different accession numbers. This can be used to explore the extent of possibly duplicates.

check_patents_with_multiple_bookings_on_same_day_with_different_accession:

                            This function is used to report whether there are patients with multiple bookings on the
                            same day (but not on the same time). This can be used to explore the extent of possibly duplicates with 
                            slightly different booking times.


overwrite_duplicated_accession_numbers:     For a few patients having a procedure, there has been created two accession numbers in IDS7.
                                            This can for instance be if the patient has both a Liver and a Speen procedure, and the
                                            user has erroneously created two accession numbers for the same patient.
                                            
                                            This function will check if there are two accession numbers for the same patient at the same time.
                                            If only one of these are in dosetrack while the rest is not, 
                                            the accession number will be overwritten by the accession number used by dosetrack.

run_all_cleanup_filters_and_checks:         This function runs all the functions in this module in the correct order for conveniance.
-------------------------------------------------------------------------------------

--------- Funciton for merging IDS7 and DoseTrack dataframes: ----------
merge_ids7_dt:              This function merged the data from IDS7 and DoseTrack based on accession number.
                            Is needs to have the columns 'Accession Number' and 'Henvisnings-ID' in the DoseTrack and IDS7 dataframes, respectively.
                            It also needs to have the column 'Beskrivelse' in the IDS7 dataframe.
                            In this function there is a lost of optional columns for both dataframes to be included in the merged dataframe.
                            The users should add parameters to the optional lists if they would like them added to the merged dataframe.

--------------- Function for exporting data: ----------
export_examination_codes_to_text_file:      This function generates a txt file with one line for each combination of aggregated
                                            examination descriptions in a folder called Reports.
                                            These lists can be printed and shown to the department to promote discussion on which
                                            procedures are important, and which should not be reported on.
                        
delete_reports:                             A Utility function for easy deleting of all the reports in the report folder.
                                            If True is passed the Reports folder is also deleted.
-------------------------------------------------------------------------------------

# Utility functions:
_concatenate_protocol(series):
    This function concatenates all the protocol information into a single string, for the merged dataframe.

_check_for_column(data, source, column_name):
    This function checks if a column is in the dataframe and outputs a warning if it is not present.

_print_pasient_column_tutorial():
    This function prints a tutorial for how to create the Pasient column in the IDS7 data using excel.

_add_optional_columns(data, agg_dict, agg_dict_optional, source):
    This function adds the optional columns to the aggregation dictionary, if the column exists in the dataframe.
-------------------------------------------------------------------------------------
"""

import pandas as pd
import numpy as np
import re
import os
import glob

# Utility functions:
def _concatenate_protocol(series):
    """
    This function concatenates all the protocol information into a single string.
    """
    sort = series.sort_values()
    return ', '.join(sort.astype(str))

def _check_for_column(data, source, column_name):
    """
    This function checks if a column is in the dataframe.
    If the column is not in the dataframe, the function will print a warning.
    """
    if column_name not in data.columns:
        print('WARNING: The column "' + column_name + '" does not exist in the "' + source + '" dataframe.')
        return False
    else:
        return True

def _check_for_fnr(data):
    """
    This function check for a column named Fødselsnummer.
    """
    if 'Fødselsnummer' in data.columns:
        print('WARNING!!!: The column "Fødselsnummer" exists in the IDS7 dataframe.')
        print('This column must be deleted, or anonymized before the data can be used!!!')
        _print_pasient_column_tutorial()
        return True

def _print_pasient_column_tutorial():
    """
    This function prints a tutorial for how to create the Pasient column in the IDS7 data using excel.
    """
    print('\n')
    print('User Guide to get the "Pasienter" column in the IDS7 data:')
    print('\n')
    print('Note that the "Pasient column is not a column in IDS7, but must be created manually for anonymity reasons.')
    print('This can be done in excel after export to a safe location using the following method:')
    print("Copy the personal ID's from the column Fødelsnummer to a new column.")
    print('Then mark the new column and click the data fan -> "Fjern Duplikater"')
    print('Next to this column write for instance: "PAS0001"') 
    print('Then doubleclick the small square in the bottom right corner of the cell to autofill.')
    print('This will create a unique identifier for each patient.')
    print('Make a new blank column next to the Fødselsnummer column, and fill it with the new anonymized patient ID.')
    print('Use the =FINN.RAD() function in excel. First argument is the Fødselsnr')
    print('The second argument is the matrix of the unique fødselsnr and the anonymized patient ID (remember $-signs)')
    print('The third argument is the column number of the anonymized patient ID in the matrix: 2')
    print('The fourth argument is USANN')
    print('Finally, copy the annonymized column into a new column named "Pasient" and remember to paste as numbers.')
    print('Make sure to delete the column "Fødselsnummer" and the key-matrix of the unique Fødselsnummer and the anonymized patient ID.')
    print('Then save the file.')
    print('\n')

def _add_optional_columns(data, agg_dict, agg_dict_optional, source, verbose=False):
    """
    This function adds the optional columns to the aggregation dictionary, if the column exists in the dataframe.
    """
    for column_name in agg_dict_optional.keys():
        if column_name in data.columns:
            agg_dict[column_name] = agg_dict_optional[column_name]
        elif verbose:
            print('WARNING: The column "' + column_name + '" does not exist in the "' + source + '" dataframe.')
            print('This column will not be included in the merged data.')
            print('\n')
    return agg_dict


def import_excel_files_to_dataframe(root_folder):
    """
    Imports all Excel files from a folder tree into one DataFrame.
    
    Args:
        root_folder (str): Path to the root folder containing Excel files.
        
    Returns:
        pd.DataFrame: Combined DataFrame with data from all Excel files.
    """
    from pathlib import Path
    # List to store individual DataFrames
    dataframes = []

    # Traverse through the folder tree
    for file_path in Path(root_folder).rglob("*.xlsx"):  # Find all Excel files recursively
        try:
            # Read Excel file into a DataFrame
            print(f"Reading {file_path}...")
            df = pd.read_excel(file_path)
            df['Source_File'] = file_path.name  # Add a column to track the source file
            dataframes.append(df)  # Append to list
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Combine all DataFrames into one
    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df


# Functions for filtering the IDS7 dataframe:
def remove_unnecessary_columns(df_ids7, verbose=False):
    """
    This function removes columns that are automatically included in the export but not needed for analysis, these are:
    Prioritet- og lesemerkeikon
    Lagt til i demonstrasjon-ikon
    Status
    """
    if 'Prioritet- og lesemerkeikon' in df_ids7.columns:
        if verbose:
            print('Dropping unnecessary column: Prioritet- og lesemerkeikon')
        df_ids7.drop('Prioritet- og lesemerkeikon', axis=1, inplace=True)

    if 'Lagt til i demonstrasjon-ikon' in df_ids7.columns:
        if verbose:
            print('Dropping unnecessary column: Lagt til i demonstrasjon-ikon')
        df_ids7.drop('Lagt til i demonstrasjon-ikon', axis=1, inplace=True)

    if 'Status' in df_ids7.columns:
        if verbose:
            print('Dropping unnecessary column: Status')
        df_ids7.drop('Status', axis=1, inplace=True)
    
    return df_ids7

def filter_NaT(df_ids7, verbose=False):
    """
    This function removes row with NaT in the column 'Bestilt dato og tidspunkt'
    """
    # Check whether the column 'Bestilt dato og tidspunkt' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Bestilt dato og tidspunkt'):
        print('Without this column, we cannot remove rows with NaT in the column "Bestilt dato og tidspunkt".')
        print('\n')
        return df_ids7
    
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7
    
    if verbose:
        print('Number of rows with NaT in the column "Bestilt dato og tidspunkt": {}'.format(sum(df_ids7['Bestilt dato og tidspunkt'].isnull())))

    df_ids7 = df_ids7[df_ids7['Bestilt dato og tidspunkt'].notnull()]
    return df_ids7

def filter_cancelled(df_ids7, verbose=False):
    """ 
    This function removes rows where the procedures have been cancelled.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Avbrutt' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Avbrutt'):
        print('Without this column, we cannot remove cancelled procedures.')
        print('\n')
        return df_ids7
    
    if _check_for_column(df_ids7, 'IDS7', 'Avbrutt'):
        if verbose:
            print('Number of cancelled procedures: {}'.format(sum(df_ids7['Avbrutt'] == 'Avbrutt')))
        df_ids7 = df_ids7[df_ids7['Avbrutt'] != 'Avbrutt']
        return df_ids7

def filter_phantom_etc(df_ids7, verbose=False):
    """ 
    This function removes rows representing non-human subjects (phantoms, animals, etc.).
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Henvisningskategori (RIS)' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisningskategori (RIS)'):
        print('Without this column, we cannot remove non-human subjects, such as phantoms, animals or other test acquisitions.')
        print('This could potentially lead to reduced data quality.')
        print('\n')
        return df_ids7
    
    if verbose:
        print('Number of non-human subjects: {}'.format(sum(df_ids7['Henvisningskategori (RIS)'] == 'X Fantom/objekt/dyr/test')))

    df_ids7 = df_ids7[df_ids7['Henvisningskategori (RIS)'] != 'X Fantom/objekt/dyr/test']
    return df_ids7

# Functions for checking the IDS7 and DoseTrack dataframes:
def check_accession_format(df_ids7, verbose=False):
    """
    This function checks if the accession number has a correct start and length.
    The currently allowed accession numbers are:
    (NORRH|NRRH|NRAK|NIRH|NKRH|NKUL|NNRH|NRRA|NRUL)
    Additionally the length of the accession number must be 16 characters.
    If verbose is True, the function will print the number of invalid accession numbers
    and the invalid accession numbers.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, we cannot check the accession number format, or merge IDS7 with DoseTrack data.')
        print('\n')
        return df_ids7
    
    valid_formats = r'^(NORRH|NRRH|NKRH|NIRH|NNRH|NRUL|NKUL|NRRA|NRAK|NLVO|MUAH_)'
    patten = re.compile(valid_formats)

    # HenvinsingsID must have the correct start and length of 16 characters (MUAH_ numbers have 12):
    is_valid_format = (df_ids7['Henvisnings-ID'].str.match(patten)) &  \
                      ((df_ids7['Henvisnings-ID'].str.len() == 16) | (df_ids7['Henvisnings-ID'].str.len() == 12))

    if verbose:
        print('Number of rows with invalid accession number: {}'.format(sum(~is_valid_format)))
        # Print the invalid accession numbers:
        if sum(~is_valid_format) > 0:
            print(df_ids7[~is_valid_format]['Henvisnings-ID'])
    
    return df_ids7[is_valid_format]

def _convert_old_siemens_pacs_accession_format(df_dt, verbose=False):
    """
    This function is called if the check_accession_ids7_vs_dt function detects that the column 
    'Accession Number' contains the old Siemens PACS accession numbers.
    These numbers have 7 numerical digits. 
    In the new PACS these have been converted to the new format by attaching "MUAH_" in front of the number.
    This function will convert the old format to the new format.
    """
    if verbose:
        print('{} entries was found matching the old siemens PACS format (7 characters long with only numbers.)' .format(sum(df_dt['Accession Number'].str.match(r'^[0-9]{7}$'))))
        print('These will be converted to the new Sectra PACS format by adding "MUAH_" in front of the number.')

    # Convert any entries of the df_dt['Accession Number'] that are 7 characters long and only contains numbers:
    df_dt.loc[df_dt['Accession Number'].str.match(r'^[0-9]{7}$'), 'Accession Number'] = 'MUAH_' + \
    df_dt.loc[df_dt['Accession Number'].str.match(r'^[0-9]{7}$'), 'Accession Number']
    return df_dt

def check_accession_ids7_vs_dt(df_ids7, df_dt, verbose=False):
    """
    This function check whether the accession numbers in IDS7 are in DoseTrack.
    It will add a column to the ids7 dataframe called Henvisning_i_dt which is 
    True if the accession number is in DoseTrack and False otherwise.
    If verbose is True, the function will print the number of accession numbers in IDS7
    and the number of accession numbers in IDS7 not in DoseTrack.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, it is impossible to merge the IDS7 with the DoseTrack data.')
        print('\n')
        return df_ids7
    
    if not _check_for_column(df_dt, 'DoseTrack', 'Accession Number'):
        print('Without this column, it is impossible to merge the DoseTrack with the IDS7 data.')
        print('\n')
        return df_ids7
    
    # Check if the column 'Accession Number' contains the old Siemens PACS accession numbers (7 digits long and only numbers):
    # If any such numbers are found, convert them to the new format:
    if sum(df_dt['Accession Number'].str.match(r'^[0-9]{7}$')) > 0:
        df_dt = _convert_old_siemens_pacs_accession_format(df_dt, verbose=verbose)

    df_ids7['Henvisning_i_dt'] = df_ids7['Henvisnings-ID'].isin(df_dt['Accession Number'].values)
    
    if verbose:
        print('Number of accession numbers in IDS7: {}'.format(len(df_ids7['Henvisnings-ID'].drop_duplicates())))
        print('Number of accession numbers in IDS7 not in DoseTrack: {}'.format(len(df_ids7[df_ids7['Henvisning_i_dt'] == False]['Henvisnings-ID'].drop_duplicates())))

    return df_ids7

def check_accession_dt_vs_ids7(df_dt, df_ids7, verbose=False):
    """
    This function check whether the accession numbers in DoseTrack are in IDS7.
    It will add a column to the DoseTrack dataframe called Henvisning_i_ids7 which is 
    True if the accession number is in IDS7 and False otherwise.
    If verbose is True, the function will print the number of accession numbers in DoseTrack
    and the number of accession numbers in DoseTrack not in IDS7.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_dt, 'DoseTrack', 'Accession Number'):
        print('Without this column, it is impossible to merge the DoseTrack with the IDS7 data.')
        print('\n')
        return df_ids7
    
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, it is impossible to merge the IDS7 with the DoseTrack data.')
        print('\n')
        return df_ids7
    
    df_dt['Henvisning_i_ids7'] = df_dt['Accession Number'].isin(df_ids7['Henvisnings-ID'].values)
    
    if verbose:
        print('Number of accession numbers in DoseTrack: {}'.format(len(df_dt['Accession Number'].drop_duplicates())))
        print('Number of accession numbers in DoseTrack not in IDS7: {}'.format(len(df_dt[df_dt['Henvisning_i_ids7'] == False]['Accession Number'].drop_duplicates())))

    return df_dt

# Functions for attempting to detect and correct errrors in the datasets:
def check_patents_with_multiple_bookings_on_same_time_with_different_accession(df_ids7):
    """
    This function is used to report whether there are patients with multiple bookings on the
    same time with different accession numbers. This is useful in order to check whether there is a large 
    number of patients with multiple rows of data that must be merged.
    A previous run on over 4000 lines of PACS data revealed 20 cases of different accession no on the same time.
    Many of these were cancelled procedusres, and should be removed in data filtration.
    Others were infact the same procedure. These shoudl have their accession number changed to the one
    reported in the dosetrack data.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7


    # Check whether the column 'Pasient' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Pasient'):
        print('Without this column, we cannot keep track of which procedures are on the same patient.')
        _print_pasient_column_tutorial()
        return
    
    # Check whether the column 'Bestilt dato og tidspunkt' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Bestilt dato og tidspunkt'):
        print('Without this column, we cannot keep track of which procedures are on the same time.')
        print('\n')
        return
    
    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, we cannot keep track of bookings.')
        print('\n')
        return
    
    # Make a list of all patients with multiple bookings on the same day with different accession numbers:
    patient_list = df_ids7['Pasient'].drop_duplicates()
    for patient in patient_list:
        # Get the booking times for this patient:
        booking_times = df_ids7[df_ids7['Pasient'] == patient]['Bestilt dato og tidspunkt']
        # Sort the booking times:
        booking_times = booking_times.sort_values()
        # if there is more than one booking:
        if len(booking_times) > 1:
            # loop through all bookings:
            for i in range(len(booking_times)-1):
                # Check if the booking times are on the same day but different time with different accesstion numbers:
                if (booking_times.iloc[i] == booking_times.iloc[i+1]):
                    # Get the accession numbers:
                    acc_no = df_ids7[(df_ids7['Pasient'] == patient) & (df_ids7['Bestilt dato og tidspunkt'] == booking_times.iloc[i])]['Henvisnings-ID'].drop_duplicates()
                    # Check if there are multiple accession numbers:
                    if len(acc_no) > 1:
                        print('Patient: ' + str(patient) + ' has multiple accession numbers at ' + str(booking_times.iloc[i]) + ':')
                        print(acc_no)
                        print('')

def check_patents_with_multiple_bookings_on_same_day_with_different_accession(df_ids7):
    """
    This function is used to report whether there are patients with multiple bookings on the
    same day (not on the same time, as they are included in the data curation) with
    different accession numbers. This is useful in order to check whether there is a large 
    number of patients with multiple rows of data that must be merged.
    On an earlier run with 4000 lines from the PACS only two cases was found.
    Both cases included cancelled procedures.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Pasient' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Pasient'):
        print('Without this column, we cannot keep track of which procedures are on the same patient.')
        _print_pasient_column_tutorial()
        return 
    
    # Check whether the column 'Bestilt dato og tidspunkt' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Bestilt dato og tidspunkt'):
        print('Without this column, we cannot keep track of which procedures are on the same day.')
        print('\n')
        return 
    
    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, we cannot keep track of bookings.')
        print('\n')
        return 

    # Make a list of all patients with multiple bookings on the same day with different accession numbers:
    patient_list = df_ids7['Pasient'].drop_duplicates()
    for patient in patient_list:
        # Get the booking times for this patient:
        booking_times = df_ids7[df_ids7['Pasient'] == patient]['Bestilt dato og tidspunkt']
        # Sort the booking times:
        booking_times = booking_times.sort_values()
        # if there is more than one booking:
        if len(booking_times) > 1:
            # loop through all bookings:
            for i in range(len(booking_times)-1):
                # Check if the booking times are on the same day but different time with different accesstion numbers:
                if (booking_times.iloc[i].date() == booking_times.iloc[i+1].date()) & (booking_times.iloc[i].time() != booking_times.iloc[i+1].time()):
                    # Get the accession numbers:
                    acc_no = df_ids7[(df_ids7['Pasient'] == patient) & (df_ids7['Bestilt dato og tidspunkt'] == booking_times.iloc[i])]['Henvisnings-ID'].drop_duplicates()
                    # Check if there are multiple accession numbers:
                    if len(acc_no) > 1:
                        print('Patient: ' + str(patient) + ' has multiple accession numbers at ' + str(booking_times.iloc[i].date()) + ':')
                        print(acc_no)
                        print('')

def overwrite_duplicated_accession_numbers(df_ids7, df_dt, verbose=False, manual_replace=False):
    """
    For a few patients having a procedure, there has been created two accession numbers in IDS7.
    DoseTrack will only use one of these if the patient only got one procedure.
    This function will search for procedures on the same patient on the same time with different accessionnumbers.
    If only one of these are in dosetrack while the rest is not, the accession number will be overwritten by the accession number
    used by dosetrack. If both or non of the accesssion numbers are in used, they remain untouched.
    After the accession numbers have been overwritten the function check_accession_ids7_vs_dt is run from this function.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Pasient' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Pasient'):
        print('Without this column, we cannot keep track of which procedures are on the same patient.')
        _print_pasient_column_tutorial()
        return df_ids7
    
    # Check whether the column 'Bestilt dato og tidspunkt' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Bestilt dato og tidspunkt'):
        print('Without this column, we cannot keep track of which procedures are on the same time.')
        print('\n')
        return df_ids7
    
    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, we cannot keep track of bookings.')
        print('\n')
        return df_ids7


    # Test if the column Henvisning_i_dt exists:
    if 'Henvisning_i_dt' not in df_ids7.columns:
        # If not, run the function check_accession_ids7_vs_dt:
        if verbose:
            print('The column Henvisning_i_dt does not exist. Running check_accession_ids7_vs_dt')
        df_ids7 = check_accession_ids7_vs_dt(df_ids7, df_dt, verbose=verbose)

    # Go through all the patients in the IDS7 data:
    patient_list = df_ids7['Pasient'].unique()
    status_changed = False
    for patient in patient_list:
        # Go through all the individual booking times for this patient:
        booking_times = sorted(df_ids7[df_ids7['Pasient'] == patient]['Bestilt dato og tidspunkt'].unique())
        for time in booking_times:
            # Get the accession number for this patient at this booking time:
            acc_nr = df_ids7[(df_ids7['Pasient'] == patient) & (df_ids7['Bestilt dato og tidspunkt'] == time)]['Henvisnings-ID'].unique()
            # Check if there is more than one accession number for this patient at this time:
            if len(acc_nr) > 1:
                # Make a pandas series with accession numbers as index and true/false as values:
                acc_nr_in_dt = pd.Series(index=acc_nr, data = np.nan)
                # Go through all the accession numbers for this patient at this time:
                for acc in acc_nr:
                    # Check if the accession number is in the DoseTrack data:
                    acc_nr_in_dt[acc] = df_ids7[(df_ids7['Pasient'] == patient) & (df_ids7['Bestilt dato og tidspunkt'] == time) & \
                                                (df_ids7['Henvisnings-ID'] == acc)]['Henvisning_i_dt'].values[0]
                # Check if there are both true and false values:
                if acc_nr_in_dt.nunique() > 1:
                    # Warn the user that there might be ambigous data regarding this procedure if there are several true and at least one false:
                    if len(acc_nr_in_dt[acc_nr_in_dt == True]) > 1 and len(acc_nr_in_dt[acc_nr_in_dt == False]) > 0:
                        print('WARNING: there are two or more accessions with data in dosetrack and at least one without.')
                        print('Please investigate patient: ' + str(patient) + ', time: ' + str(time) + ', accession numbers: ' + str(acc_nr))
                        # Loop to help the user manually enter the accession number that should be used:
                        if manual_replace:
                            while True:
                                # Get the user to enter the accession number that should be used:
                                print('\n')
                                print('Please enter the accession number that should be used:')
                                # List the accession numbers without data in dosetrack along with descriptions:
                                print('Accession numbers without data in dosetrack:')
                                for acc in acc_nr_in_dt[acc_nr_in_dt == False].index:
                                    print(acc + ', Beskrivelse: ')
                                    for beskrivelse in df_ids7[(df_ids7['Pasient'] == patient) & (df_ids7['Bestilt dato og tidspunkt'] == time) & \
                                                (df_ids7['Henvisnings-ID'] == acc)]['Beskrivelse']:
                                        print(beskrivelse)
                                # List the accession numbers with data in dosetrack along with descriptions:
                                print('\n')
                                print('Accession numbers with data in dosetrack:')
                                for acc in acc_nr_in_dt[acc_nr_in_dt == True].index:
                                    print(acc + ', Beskrivelse: ')
                                    for beskrivelse in df_ids7[(df_ids7['Pasient'] == patient) & (df_ids7['Bestilt dato og tidspunkt'] == time) & \
                                                (df_ids7['Henvisnings-ID'] == acc)]['Beskrivelse']:
                                        print(beskrivelse)                                   
                                manual_input = input()
                                # Check if the accession number is in the list of accession numbers for this patient at this time with data in dosetrack:
                                if manual_input in acc_nr_in_dt[acc_nr_in_dt == True].index:
                                    # Insert the manually entered accession number into all the rows for the same patient and booking with no dosetrack data:
                                    df_ids7.loc[(df_ids7['Pasient'] == patient) & \
                                                (df_ids7['Bestilt dato og tidspunkt'] == time) & \
                                                (df_ids7['Henvisning_i_dt'] == False) \
                                                , 'Henvisnings-ID'] = manual_input
                                    status_changed = True
                                    print('Inserted accession number: ' + str(manual_input) + ' for patient: ' + str(patient) + ', time: ' + str(time) + ' for elements not in dosetrack.')
                                    break
                                print('WARNING!!! The accession number you entered is not in the list of accession numbers with data in dosetrack.')
                        else:
                            print('Switch the manual_replace flag to True to enable manual accession number replacement.')
                    else:
                        # Insert the accession number which is included in the DoseTrack data into all the rows for the same 
                        # patient and booking with no dosetrack data:
                        df_ids7.loc[(df_ids7['Pasient'] == patient) & \
                                    (df_ids7['Bestilt dato og tidspunkt'] == time) & \
                                    (df_ids7['Henvisning_i_dt'] == False) \
                                    , 'Henvisnings-ID'] = acc_nr_in_dt[acc_nr_in_dt == True].index[0]
                        status_changed = True
                        print('Inserted accession number: ' + str(acc_nr_in_dt[acc_nr_in_dt == True].index[0]) + \
                            ' for patient: ' + str(patient) + ', time: ' + str(time) + ', accession numbers: ' + str(acc_nr))
    if status_changed:
        # Run the function check_accession_ids7_vs_dt again to update the column Henvisning_i_dt:
        if verbose:
            print('The accession numbers have been changed. Running check_accession_ids7_vs_dt')
        df_ids7 = check_accession_ids7_vs_dt(df_ids7, df_dt, verbose=verbose)

    return df_ids7

# Funciton for merging IDS7 and DoseTrack dataframes:
def merge_ids7_dt(df_ids7, df_dt, verbose=False):
    """ 
    This function merged the data from IDS7 and DoseTrack based on accession number.
    In the process of preparing the merge of the IDS7 data, all the procedure descriptions for the same 
    accession number are concatenated into one string.
    For the DoseTrack data, the sum of the DAP, CAK and F+A Time are calculated for each accession number.
    """
    # Stop execution if the dataframe contains the column 'Fødselsnummer':
    if _check_for_fnr(df_ids7):
        return df_ids7

    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Henvisnings-ID'):
        print('Without this column, we cannot merge the IDS7 into the DoseTrack data.')
        print('\n')
        return False
    
    # Check whether the column 'Beskrivelse' exists:
    if not _check_for_column(df_ids7, 'IDS7', 'Beskrivelse'):
        print('Without this column, we do not know whick procedure has been performed.')
        print('\n')
        return False
    
    # Check whether the column 'Accession Number' exists:
    if not _check_for_column(df_dt, 'DoseTrack', 'Accession Number'):
        print('Without this column, we do not know whick procedure has been performed.')
        print('\n')
        return False

    # Prepare the manditory IDS7 data for merge:
    agg_dict_ids7 = {'Henvisnings-ID': 'first', 
                     'Beskrivelse': _concatenate_protocol}
    
    # Herer users can list all optional columns that should be included in the merge. If these do not exist in the data they are ignored.
    # prepare the optional IDS7 data for merge:
    agg_dict_ids7_optional = {'Pasient': 'first',
                              'Kjønn': 'first'}
    
    # Insert the optional IDS7 data into the aggregation dictionary if the column exists:
    agg_dict_ids7 = _add_optional_columns(df_ids7, agg_dict_ids7, agg_dict_ids7_optional, 'IDS7', verbose=verbose)

    # Prepare the manditory DoseTrack data for merge:
    agg_dict_dt = {'Accession Number': 'first'}
    
    # Herer users can list all optional columns that should be included in the merge. If these do not exist in the data they are ignored.
    # prepare the optional DoseTrack data for merge:
    agg_dict_dt_optional = {'Study Date': 'first',
                            'Age (Years)': 'first',
                            'DAP Total (Gy*cm2)': 'sum',
                            'CAK (mGy)': 'sum',
                            'F+A Time (s)': 'sum',
                            'Modality Room': 'first'}
    
    agg_dict_dt = _add_optional_columns(df_dt, agg_dict_dt, agg_dict_dt_optional, 'DoseTrack', verbose=verbose)

    
    df_ids7_to_merge = df_ids7[df_ids7['Henvisning_i_dt'] == True].groupby('Henvisnings-ID', as_index = False).agg(agg_dict_ids7)

    # Prepare the DoseTrack data for merge:
    df_dt_to_merge = df_dt[df_dt['Henvisning_i_ids7'] == True].groupby('Accession Number', as_index = False).agg(agg_dict_dt)
    
    # Merge the IDS7 and DoseTrack data:
    data = pd.merge(df_ids7_to_merge, df_dt_to_merge, how='outer', left_on='Henvisnings-ID', right_on='Accession Number')
    
    # Drop the redundant column:
    data.drop('Henvisnings-ID', axis=1, inplace=True)

    if verbose:
        print('The IDS7 and DoseTrack has merged data of length: {}'.format(len(data)))

    return data

# Utility function to run all filters and checks:
def run_all_cleanup_filters_and_checks(df_ids7, df_dt, verbose=False, manual_replace=False):
    """
    This utilityfunction runs the following funcions:
    filter_NaT
    remove_unnecessary_columns
    filter_cancelled
    filter_phantom_etc
    check_accession_format
    check_accession_ids7_vs_dt
    overwrite_duplicated_accession_numbers
    """
    df_ids7 = remove_unnecessary_columns(df_ids7, verbose=verbose)
    df_ids7 = filter_NaT(df_ids7, verbose=verbose)
    df_ids7 = filter_cancelled(df_ids7, verbose=verbose)
    df_ids7 = filter_phantom_etc(df_ids7, verbose=verbose)
    df_ids7 = check_accession_format(df_ids7, verbose=verbose)
    df_ids7 = check_accession_ids7_vs_dt(df_ids7, df_dt, verbose=verbose)
    df_ids7 = overwrite_duplicated_accession_numbers(df_ids7, df_dt, verbose=verbose, manual_replace=manual_replace)
    df_dt   = check_accession_dt_vs_ids7(df_dt, df_ids7, verbose=verbose)

    return df_ids7

# Functions for exporting the data:
def export_examination_codes_to_text_file(df_data, laboratory=None):
    """
    This function exports the examination codes for all laboratories (if no laboratory argument is given),
    or for a specific laboratory (if the laboratory argument is given).
    The input is the dataframe with the IDS7 data and the name of the lab as a string.
    """

    # The following two statements enables the function to work with both the IDS7 and the merged data.
    # If the column Accession Number exists, use the merged dataset instead of IDS7:
    if 'Accession Number' in df_data.columns:
        accession_col = 'Accession Number'
        lab_col = 'Modality Room'
        dataset = 'Merged'

    else:
        accession_col = 'Henvisnings-ID'
        lab_col = 'Rom/modalitet (RIS)'
        dataset = 'IDS7'
    
    # Check whether the column 'Henvisnings-ID' exists:
    if not _check_for_column(df_data, dataset, accession_col):
        print('Without this column, we cannot aggregate procedures per accession.')
        print('\n')
        return
    
    # Check whether the column 'Rom/modalitet (RIS)' exists:
    if not _check_for_column(df_data, dataset, lab_col):
        print('Without this column, we cannot list procedures per laboratory.')
        print('\n')
        return
    
    # Check whether the column 'Beskrivelse' exists:
    if not _check_for_column(df_data, dataset, 'Beskrivelse'):
        print('Without this column, we cannot make a list of procedures.')
        print('\n')
        return
    
    # Iterate through all the labs in the dataset:
    
    # Filter the dataset to only include the the given lab is lab is not None:
    if laboratory is not None:
        df_data = df_data[df_data[lab_col] == laboratory]
        if len(df_data) == 0:
            print('No rows with the given lab: ' + laboratory)
            return

    for lab in df_data[lab_col].unique():
        df_lab = df_data[df_data[lab_col] == lab]
        # Exit function with an error if there are no rows with the given lab:
        if len(df_lab) == 0:
            print('No rows with the given lab: ' + lab)
            return

        # Make an pandas series with an index of the accession numbers that store the codes:
        codes = pd.Series(index = df_lab[accession_col].unique())
        for accession_no in codes.index:
            procedure = df_lab[df_lab[accession_col] == accession_no]['Beskrivelse'].unique()
            procedure.sort()
            # Merge all the codes into one string:
            code = ''
            for i in procedure:
                code += i + ', '
            # Remove the last comma and space:
            code = code[:-2]
            # Store the code in the series:
            codes[accession_no] = code

        # Make a list of unique codes:
        unique_codes = codes.unique()
        # Sort the list:
        unique_codes.sort()
        # Export the list to a text file in the Reports folder:
        if not os.path.exists('Reports'):
                os.makedirs('Reports')
        with open('Reports/Examination_codes_' + lab + '.txt', 'w') as f:
            # Write (n=number of procedures) before each code:
            for code in unique_codes:
                f.write('(n = ' + str(sum(codes == code)) + ') ' + code + '\n')

def delete_reports(delete_folder=False):
    """
    This function deletes all the reports in the Reports folder.
    """
    files = glob.glob('Reports/*')
    for f in files:
        os.remove(f)
        
    if delete_folder:
        if os.path.exists('Reports'):
            os.rmdir('Reports')
    return