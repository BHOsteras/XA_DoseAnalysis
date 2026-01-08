"""
This module contains a functions for returning a mapping dictionary to facilitate interpretation of the decription column 
(column: 'Beskrivelse') to a new column (column: 'Mapped Procedures').
The 'Mapped Procedures' column is used to organize the description into useful categories, make relevant plots, etc.
"""

def get_DSA_mapping_dict():
    """
    Here the user can hardcode the mapping dictionary for the DSA interventional dose reporting for 2024:

    If the dataset includes procedure names from the era before IDS7 PACS, pass the argument True to the function.
    
    In the PCI labs, the description column (column: 'Beskrivelse') can potentially contain
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

    mapping = { # INT01 - Hode og hals Hjerte/Blodkar
                'RGA Caput'                                                     : 'INT01 - Hode og hals Hjerte/Blodkar',
                'RGL Collum'                                                    : 'INT01 - Hode og hals Hjerte/Blodkar',
                'RGA Collum'                                                    : 'INT01 - Hode og hals Hjerte/Blodkar',
                'RGV Caput'                                                     : 'INT01 - Hode og hals Hjerte/Blodkar',    
                'RGV Collum'                                                    : 'INT01 - Hode og hals Hjerte/Blodkar',               
                # INT08 - Hode og hals ikke Hjerte/Blodkar
                'RG Cervicalcolumna'                                            : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                'RG Svelgfunksjon dynamisk undersøkelse (RF) & ~Øsofagus'       : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                'RG Videofluoroskopi'                                           : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                'RG Hypopharynx & ~Øsofagus'                                    : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                'RG CVK & ~RGA & ~RGV'                                          : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                'RG Shunt'                                                      : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                'RG ØVD'                                                        : 'INT08 - Hode og hals ikke Hjerte/Blodkar',
                
                # INT02 - Thorax Hjerte/Blodkar
                'RGA Thorax & ~RGA Abdomen'                                     : 'INT02 - Thorax Hjerte/Blodkar',   
                'RGA Aorta TEVAR & ~BEVAR/FEVAR & ~Aorta EVAR'                  : 'INT02 - Thorax Hjerte/Blodkar',
                'RGL Thorax'                                                    : 'INT02 - Thorax Hjerte/Blodkar',
                'RGV Thorax & ~TIPS'                                            : 'INT02 - Thorax Hjerte/Blodkar',
                'RGA Bronkialarterier'                                          : 'INT02 - Thorax Hjerte/Blodkar',
                'RGV Pulmonalarterier'                                          : 'INT02 - Thorax Hjerte/Blodkar',
                'RGA Thoracalaorta'                                             : 'INT02 - Thorax Hjerte/Blodkar',
                
                # INT09 - Thorax ikke Hjerte/Blodkar
                'RG Thorax - Drenasje'                                          : 'INT09 - Thorax ikke Hjerte/Blodkar',
                'RG Thorax gjennomlysning (RF)'                                 : 'INT09 - Thorax ikke Hjerte/Blodkar',
                'RG Øsofagus TBE'                                               : 'INT09 - Thorax ikke Hjerte/Blodkar',
                'RG Bronkoskopi (RF)'                                           : 'INT09 - Thorax ikke Hjerte/Blodkar',
                'RG Trachea gjennomlysning (RF)'                                : 'INT09 - Thorax ikke Hjerte/Blodkar',
                'RG Thorax '                                                    : 'INT09 - Thorax ikke Hjerte/Blodkar',
                'RG Øsofagus & ~ØVD & ~Svelgfunksjon & ~Hypopharynx'            : 'INT09 - Thorax ikke Hjerte/Blodkar',
                
                # INT03 - Hjerte
                'RGV Pulmonalklaff'                                             : 'INT03 - Hjerte',
                'RGV Cor'                                                       : 'INT03 - Hjerte',
                'RGA Cor'                                                       : 'INT03 - Hjerte',
                'RGA Aorta Aortaklaff'                                          : 'INT03 - Hjerte',
                
                # INT04 - Abdomen Hjerte/Blodkar
                'RGA Abdomen                  '                                 : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGA Nyrer'                                                     : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGA Lever'                                                     : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGA Milt'                                                      : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGA Aorta BEVAR/FEVAR & ~TEVAR& ~RGA Bekken'                   : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGA Tarm'                                                      : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGV PancreasTX'                                                : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGV Vena Cava'                                                 : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGV Abdomen'                                                   : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGV Portvene'                                                  : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGV Binyrer'                                                   : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGV Lever'                                                     : 'INT04 - Abdomen Hjerte/Blodkar',
                'RGL Abdomen'                                                   : 'INT04 - Abdomen Hjerte/Blodkar',

                # INT11 - Abdomen ikke Hjerte/Blodkar
                'RG Abdomen'                                                    : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Tarmpassasje'                                               : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Tynntarm'                                                   : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Diafragmabevegelse'                                         : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Galleveier'                                                 : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Gastroskopi'                                                : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Nefrostomi'                                                 : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Antegrad pyelografi'                                        : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Lever'                                                      : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG ERCP'                                                       : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG V+D enkeltkontrast'                                         : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Galleblære'                                                 : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Nedleggelse av'                                             : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                'RG Tarm - Perkutan'                                            : 'INT11 - Abdomen ikke Hjerte/Blodkar',
                
                # INT05 - Bekken Hjerte/Blodkar
                'RGA Prostata'                                                  : 'INT05 - Bekken Hjerte/Blodkar',
                'RGA Uterus'                                                    : 'INT05 - Bekken Hjerte/Blodkar',
                'RGA Bekken'                                                    : 'INT05 - Bekken Hjerte/Blodkar',
                'RGV Bekken'                                                    : 'INT05 - Bekken Hjerte/Blodkar',
                'RGL Bekken'                                                    : 'INT05 - Bekken Hjerte/Blodkar',
                
                # INT12 - Bekken ikke Hjerte/Blodkar 
                'RG Urinveier'                                                  : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Lumbo-sacralcolumna'                                        : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Bekken'                                                     : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Hofte'                                                      : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Defecografi'                                                : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG MUCG (RF)'                                                  : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Urografi'                                                   : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Urinveier'                                                  : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Hysterosalpingograf'                                        : 'INT12 - Bekken ikke Hjerte/Blodkar',
                'RG Urethragrafi'                                               : 'INT12 - Bekken ikke Hjerte/Blodkar',
                
                # INT06 - Ekstremitet Hjerte/Blodkar
                'RGA Overex'                                                    : 'INT06 - Ekstremitet Hjerte/Blodkar',
                'RGV Overex'                                                    : 'INT06 - Ekstremitet Hjerte/Blodkar',
                'RGV Underex'                                                   : 'INT06 - Ekstremitet Hjerte/Blodkar',
                'RGA Underex'                                                   : 'INT06 - Ekstremitet Hjerte/Blodkar',
                'RGL Overex'                                                    : 'INT06 - Ekstremitet Hjerte/Blodkar',
                'RGL Underex'                                                   : 'INT06 - Ekstremitet Hjerte/Blodkar',

                # INT13 - Ekstremitet ikke Hjerte/Blodkar 
                'Artrografi'                                                    : 'INT13 - Ekstremitet ikke Hjerte/Blodkar',
                
                # INT07 - Øvrig og sammenslåtte koder Hjerte/Blodkar
                'Totalcolumna gjennomlysning (RF)'                              : 'INT07 - Øvrig og sammenslåtte koder Hjerte/Blodkar',
                'Abdomen & Bekken & ~EVAR & ~Stent & ~Embolisering'             : 'INT07 - Øvrig og sammenslåtte koder Hjerte/Blodkar',

                # INT14 - Øvrig ikke Hjerte/Blodkar 
                'RGA Columna'                                                   : 'INT14 - Øvrig ikke Hjerte/Blodkar',
                'Abdomen Embolisering & Bekken'                                 : 'INT14 - Øvrig ikke Hjerte/Blodkar',
                'Aorta EVAR & TEVAR'                                            : 'INT14 - Øvrig ikke Hjerte/Blodkar',
                'Aorta EVAR & Bekken Embolisering'                              : 'INT14 - Øvrig ikke Hjerte/Blodkar',
                'RG Columnae'                                                   : 'INT14 - Øvrig ikke Hjerte/Blodkar',
                'RG Colon'                                                      : 'INT14 - Øvrig ikke Hjerte/Blodkar',
                'RG Øsofagus & Svelgfunksjon'                                   : 'INT14 - Øvrig ikke Hjerte/Blodkar', 
                'RG Øsofagus & Hypopharynx & ~TBE'                              : 'INT14 - Øvrig ikke Hjerte/Blodkar'

            }
    return mapping
