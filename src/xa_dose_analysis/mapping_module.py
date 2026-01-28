"""
This module contains functions for mapping the description content (column: 'Beskrivelse') to a new column (column: 'Mapped Procedures').
"""

def _perform_mapping(df_data, key, value):
    """
    This utility function performs the mapping according to the following rules:
    First the key is separated in to a list of criteria, separated by ' & '.
    Then each criteria is checked for the presence of '~' which indicates an exclusion criteria.
    """

    def _check_criteria(description):
        """
        This utility function checks whether all the inclusion and exclusion criteria are satisfied in
        the description column 'Beskrivelse'.
        """
        # Check if all inclusion criteria are present in the description:
        if all(elem.lower() in description.lower() for elem in inclusion_criteria) & \
            ~any(elem.lower() in description.lower() for elem in exclusion_criteria):
            return True
        else:
            return False

    # Get the inclusion and exclusion criteria:
    key_list = key.split(' & ')
    inclusion_criteria = [x for x in key_list if not x.startswith('~')]
    exclusion_criteria = [x[1:] for x in key_list if x.startswith('~')]

    # Check df_data's 'Beskrivelse' column for substrings of all the inclusion and exclusion criteria:
    # 'Mapping Target' is set to True if all inclusion criteria are present and no exclusion criteria are present:
    # This is a temporary column that is used to check whether we are mapping allready mapped columns.
    df_data['Mapping Target'] = False
    df_data.loc[df_data['Beskrivelse'].apply(_check_criteria), 'Mapping Target'] = True

    # Check if no procedures were targeted by the mapping:
    if sum(df_data['Mapping Target'] == True) == 0:
        print('WARNING! No procedures were targeted by this mapping!')
        print('\n')
        df_data.drop('Mapping Target', axis=1, inplace=True)
        return df_data

    # Check if the mapping target is already mapped with a different value and give a warning and information if it is:
    if sum((df_data['Mapping Target'] == True) & ~((df_data['Mapped Procedures'] == 'Unmapped') | (df_data['Mapped Procedures'] == value))) > 0:
        print('\n')
        print('-'*30)
        print('\n')
        print('WARNING! Some or all mapping targets are already mapped!')
        print('\n')
        # Print all the inclusion criteria with an ' & ' between them:
        print('The current inclusion criteria are: ' + ' & '.join(inclusion_criteria))
        print('The current exclusion criteria are: ' + ' & '.join(exclusion_criteria))
        # Print a unique list of the already mapped procedures:
        print('\n')
        print('The following procedures are already mapped:')
        mapped_list = df_data['Beskrivelse'][(df_data['Mapping Target'] == True) &  
                                             (df_data['Mapped Procedures'] != 'Unmapped')].unique().tolist()
        print('\n')

        for item in mapped_list:
            # Print the 'Beskrivelse' column ' -> ' the 'Mapped Procedures' column, only of the 'Mapped Procedure' differs from value:
            if df_data['Mapped Procedures'][df_data['Beskrivelse'] == item].unique()[0] != value:
                print(f'{item}   --->   {df_data["Mapped Procedures"][df_data["Beskrivelse"] == item].unique()[0]}')
        print('\n')

        print('Please check the mapping dictionary and refine it to avoid mapping the same procedure twice.')
        print('\n')
        print('-'*30)
        print('\n')
        df_data.drop('Mapping Target', axis=1, inplace=True)
        return df_data    

    # Map the procedures:
    df_data.loc[df_data['Mapping Target'] == True, 'Mapped Procedures'] = value

    # Remove the temporary column:
    df_data.drop('Mapping Target', axis=1, inplace=True)

    return df_data

def map_procedures(df_data, mapping, verbose=False):
    """
    This function checks the relevant columns for the presence of the characters '&' and '~', which is used for mapping.
    It also initializes the 'Mapped Procedures' column and moves it to the front.
    Finally the mapping dictionary is passed line by line to the _perform_mapping function.
    """
        # Check the 'Beskrivelse' column for the following characters '&', '~':
    if sum(df_data['Beskrivelse'].str.contains('&')) > 0:
        print('WARNING! The "Beskrivelse" column contains the character "&".')
        print('This character is used to separate criteria for identifying procedures.')
        print('We need to find another separator character.')
        return
    
    if sum(df_data['Beskrivelse'].str.contains('~')) > 0:
        print('WARNING! The "Beskrivelse" column contains the character "~".')
        print('This character is used to exclude criteria for identifying procedures.')
        print('We need to find another separator character.')
        return

    # Initialize the 'Mapped Procedures' column:
    df_data['Mapped Procedures'] = 'Unmapped'

    # Move the 'Mapped Procedures' column to the front:
    cols = df_data.columns.tolist()
    cols.insert(0, cols.pop(cols.index('Mapped Procedures')))
    df_data = df_data.reindex(columns=cols)
   
    # Map the procedures:
    if verbose:
        print('Mapping procedures...\n')

    for key, value in mapping.items():
        if verbose:
            print(f'{key} -> {value}')
        df_data = _perform_mapping(df_data, key, value)

    return df_data