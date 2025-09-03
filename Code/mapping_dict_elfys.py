"""
This module contains a functions for returning a mapping dictionary to facilitate interpretation of the decription column 
(column: 'Beskrivelse') to a new column (column: 'Mapped Procedures').
The 'Mapped Procedures' column is used to organize the description into useful categories, make relevant plots, etc.
"""

def get_elfys_mapping_dict():
    """
    Here the user can hardcode the mapping dictionary for Electrophysiology procedures:

    If the dataset includes procedure names from the era before IDS7 PACS, pass the argument True to the function.
    
    In the Electrophysiology department, the description column (column: 'Beskrivelse') can potentially contain
    several different procedure codes. These codes have been concatinated into one string with each procedure 
    separated by a comma. This results in multiple different strings representing the same procedure, 
    with only minor variations. For instance if ultrasound was used, the string will contain ', UL ...'.

    This function involves a mapping dictionary that maps the different strings to the same procedure.
    If a substring is found in the description column, the corresponding value in the mapping dictionary.
    The mapped procedures are put in a new column (column: 'Mapped Procedures').

    For some procedures it is nessecary to use several criteria to identify the procedure.
    For instance: Nefrostomi med innleggelse av dren, as this can be a complex procedure.
    For such cases the key in the mapping dictionary use ' & ' to separate the criteria.
    Example: mapping = {'Nefrostomi & innleggelse av dren' : 'Nefrostomi innleggelse'}

    Other procedures are similar but musch less complex.
    For instance: Nefrostomi med skifte av dren eller fjerning av dren.
    For such cases the key in the mapping dictionary can use ' & ' to separate the criteria,
    but also use a '~' in front of the criteria that is an exclusion criteria.
    So to make a Nefrostomi med skifte av dren eller fjerning av dren procedure, 
    the mapping dictionary can be:
    Example: mapping = {'Nefrostomi & ~innleggelse av dren' : 'Nefrostomi skifte eller fjerning'}

    To change or add to the mapping of procedures, edit the 'mapping' dictionary below.
    """

    mapping = { 'RGA Cor Ablasjon SVT (int.)'                   : 'RGA Cor Ablasjon SVT (int.) m og u 3D',
                'RGA Cor Ablasjon SVT m 3D (int.)'              : 'RGA Cor Ablasjon SVT (int.) m og u 3D',
                'RGA Cor Ablasjon VT m 3D (int.) & ~RGA Cor Ablasjon SVT'  : 'RGA Cor Ablasjon VT (int.) m 3D',
            
                'RGA Cor Ablasjon Atrieflimmer (int.)'          : 'RGA Cor Ablasjon Atrieflimmer (int.) m og u 3D',             # Utgått?
                'RGA Cor Ablasjon Atrieflimmer med 3D (int.)'   : 'RGA Cor Ablasjon Atrieflimmer (int.) m og u 3D',

                'RGA Cor Pulsed field ablasjon (elektroporasjon) atrieflimmer' : 'RGA Cor Pulsed field ablasjon (elektroporasjon) atrieflimmer',

                'RGA Cor Cryo Ablasjon Atrieflimmer (int.)'     : 'RGA Cor Cryo Ablasjon Atrieflimmer (int.)',

                'RGA Cor Ablasjon Atrieflutter (int.) & ~Atrieflimmer' : 'RGA Cor Ablasjon Atrieflutter (int.) m og u 3D',

                'RGA Cor Elfys SVT (int.)'                      : 'RGA Cor Elfys VT el. SVT (int.)',
                'RGA Cor Elfys VT (int.)'                       : 'RGA Cor Elfys VT el. SVT (int.)',

                'RGA Cor CRT-D (int.)'                          : 'RGA Cor CRT-D (int.) ink. CRT-P',
                'RGA Cor CRT-P (int.)'                          : 'RGA Cor CRT-D (int.) ink. CRT-P',

                'RGA Cor 2-k PM (int.)'                         : 'RGA Cor Implantasjon PM/ICD (int.) ink. 2k og 1k PM',
                'RGA Cor 1-k PM (int.)'                         : 'RGA Cor Implantasjon PM/ICD (int.) ink. 2k og 1k PM',
                'RGA Cor 2-K ICD (int.)'                        : 'RGA Cor Implantasjon PM/ICD (int.) ink. 2k og 1k PM',
                'RGA Cor 1-k ICD (int.)'                        : 'RGA Cor Implantasjon PM/ICD (int.) ink. 2k og 1k PM',
                'RGA Cor Implantasjon PM/ICD (int.) & ~CRT'     : 'RGA Cor Implantasjon PM/ICD (int.) ink. 2k og 1k PM',         # Utgått?
                
                'RGV Cor Biopsi høyre ventrikkel'               : 'RGV Cor Biopsi',
                'RGV Cor Hø kat, måling av trykk og flow i lille kretsløp & ' +
                '~RGV Cor Biopsi høyre ventrikkel'              : 'RGV Cor Hø kat, måling av trykk og flow i lille kretsløp',
                'RGV Cor Høyre kat. Arytmi & ~RGV Cor Biopsi høyre ventrikkel' : 'RGV Cor Høyre kat. Arytmi'}

    return mapping
