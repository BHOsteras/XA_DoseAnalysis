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

    mapping = { 'RGA Cor Ablasjon SVT (int.)'                   : 'Ablation',
                'RGA Cor Ablasjon SVT m 3D (int.)'              : 'Ablation',
                'RGA Cor Ablasjon VT m 3D (int.) & ~RGA Cor Ablasjon SVT'  : 'Ablation',
            
                'RGA Cor Ablasjon Atrieflimmer (int.)'          : 'Ablation',             # Utgått?
                'RGA Cor Ablasjon Atrieflimmer med 3D (int.)'   : 'Ablation',

                'RGA Cor Pulsed field ablasjon (elektroporasjon) atrieflimmer' : 'Ablation',

                'RGA Cor Cryo Ablasjon Atrieflimmer (int.)'     : 'Ablation',

                'RGA Cor Ablasjon Atrieflutter (int.) & ~Atrieflimmer' : 'Ablation',

                'RGA Cor Elfys SVT (int.)'                      : 'Electrophysiology',
                'RGA Cor Elfys VT (int.)'                       : 'Electrophysiology',

                'RGA Cor CRT-D (int.)'                          : 'Pacemaker',
                'RGA Cor CRT-P (int.)'                          : 'Pacemaker',

                'RGA Cor 2-k PM (int.)'                         : 'Pacemaker',
                'RGA Cor 1-k PM (int.)'                         : 'Pacemaker',
                'RGA Cor 2-K ICD (int.)'                        : 'Pacemaker',
                'RGA Cor 1-k ICD (int.)'                        : 'Pacemaker',
                'RGA Cor Implantasjon PM/ICD (int.) & ~CRT'     : 'Pacemaker',         # Utgått?
                
                'RGV Cor Biopsi høyre ventrikkel'               : 'RGV Cor Biopsi',
                'RGV Cor Hø kat, måling av trykk og flow i lille kretsløp & ' +
                '~RGV Cor Biopsi høyre ventrikkel'              : 'RGV Cor Hø kat, måling av trykk og flow i lille kretsløp',
                'RGV Cor Høyre kat. Arytmi & ~RGV Cor Biopsi høyre ventrikkel' : 'RGV Cor Høyre kat. Arytmi'}

    return mapping
