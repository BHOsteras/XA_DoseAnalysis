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

    mapping = { # INT01 - Hode og hals diagnostikk
                'RGA Caput og collum'                                                        : 'INT01 - Hode og hals',
                'RGA Caput & ~Embolisering & ~Trombektomi & ~Stent & ~Injeksjon & ~PTA'      : 'INT01 - Hode og hals',
                'CT Caput'                                                                   : 'INT01 - Hode og hals',
                'RGV Caput - Venografi'                                                      : 'INT01 - Hode og hals',
                'RG Cervicalcolumna'                                                         : 'INT01 - Hode og hals',
                'RG Svelgfunksjon dynamisk undersøkelse (RF)'                                : 'INT01 - Hode og hals',
                'RG Videofluoroskopi svelgfunksjon (RF)'                                     : 'INT01 - Hode og hals',
                'RG Hypopharynx'                                                             : 'INT01 - Hode og hals',
                # INT08 - Hode og hals behandling
                'RGA Caput Embolisering (int.)'                                              : 'INT08 - Hode og hals',
                'RGA Caput Trombektomi/embolektomi (int.)'                                   : 'INT08 - Hode og hals',
                'RGA Caput Stent/stentgraft (int.)'                                          : 'INT08 - Hode og hals',
                'RGA Caput Injeksjon av terapeutisk substans (int.)'                         : 'INT08 - Hode og hals',
                'RGA Caput PTA (int.)'                                                       : 'INT08 - Hode og hals',
                'RGL Caput  - Sklerosering'                                                  : 'INT08 - Hode og hals',
                'RGL Collum - Sklerosering'                                                  : 'INT08 - Hode og hals',
                'RGV Caput Sklerosering'                                                     : 'INT08 - Hode og hals',
                'RGV Collum Sklerosering'                                                    : 'INT08 - Hode og hals',
                
                # INT02 - Thorax diagnostikk
                'RG Thorax gjennomlysning (RF)'                                              : 'INT02 - Thorax diagnostikk',
                'RGA Thoracalaorta'                                                          : 'INT02 - Thorax diagnostikk',
                'RGA Thorax & ~Embolisering & Stent & ~PTA'                                  : 'INT02 - Thorax diagnostikk',
                'RG Bronkoskopi (RF)'                                                        : 'INT02 - Thorax diagnostikk',
                'RG Trachea gjennomlysning (RF)'                                             : 'INT02 - Thorax diagnostikk',
                'RG Thorax'                                                                  : 'INT02 - Thorax diagnostikk',
                'RG ØVD'                                                                     : 'INT02 - Thorax diagnostikk',
                'RG Øsofagus'                                                                : 'INT02 - Thorax diagnostikk',
                'RG Svelgfunksjon'                                                           : 'INT02 - Thorax diagnostikk',
                'RGV Pulmonalarterier & ~Embolisering & Stent & ~PTA'                        : 'INT02 - Thorax diagnostikk',
                
                # INT09 - Thorax behandling
                'RG Thorax - Drenasje'                                                       : 'INT09 - Thorax behandling',
                'RGA Thorax Embolisering'                                                    : 'INT09 - Thorax behandling',   
                'RGA Thorax Stent/stentgraft'                                                : 'INT09 - Thorax behandling',
                'RGA Aorta TEVAR & ~BEVAR/FEVAR & ~Aorta EVAR'                               : 'INT09 - Abdomen behandling',
                'RGL Thorax - Sklerosering'                                                  : 'INT09 - Thorax behandling',
                'RGV Thorax Sklerosering'                                                    : 'INT09 - Thorax behandling',
                'RGA Aorta TEVAR'                                                            : 'INT09 - Thorax behandling',
                'RGA Bronkialarterier Embolisering'                                          : 'INT09 - Thorax behandling',
                'RGV Pulmonalarterier Embolisering'                                          : 'INT09 - Thorax behandling',
                'RGV Pulmonalarterier PTA'                                                   : 'INT09 - Thorax behandling',
                'RGV Pulmonalklaff'                                                          : 'INT09 - Thorax behandling',

                
                # INT03 - Hjerte diagnostikk
                'RGV Cor Biopsi'                                                             : 'INT03 - Hjerte diagnostikk',
                'RGV Cor Hø kat'                                                             : 'INT03 - Hjerte diagnostikk',
                'RGV Cor Høyre kat'                                                          : 'INT03 - Hjerte diagnostikk',
                'RGV Cor Høyresidig hjertkateterisering & ~ASD & ~PFO & ~PTA'                       : 'INT03 - Hjerte diagnostikk',
                'RGA Cor Koronarangiografi & ~PCI & ~TAVI & ~Mitraclip & ~PTSMA'             : 'INT03 - Hjerte diagnostikk',
                'RGA Cor FFR/IFR & ~PCI & ~TAVI & ~Mitraclip & ~PTSMA'                       : 'INT03 - Hjerte diagnostikk',
                'RGA Cor Hjertefilming & ~PCI & ~TAVI & ~Mitraclip & ~PTSMA'                 : 'INT03 - Hjerte diagnostikk',
                # INT10 - Hjerte behandling
                'RGV Cor PFO'                                                                : 'INT10 - Hjerte behandling',
                'RGV Cor ASD'                                                                : 'INT10 - Hjerte behandling',
                'RGA Cor Generatorbytte'                                                     : 'INT10 - Hjerte behandling',
                'RGA Cor Revisjon'                                                           : 'INT10 - Hjerte behandling',
                'RGA Cor CRT'                                                                : 'INT10 - Hjerte behandling',
                'RGA Cor 2-K'                                                                : 'INT10 - Hjerte behandling',
                'RGA Cor 1-k'                                                                : 'INT10 - Hjerte behandling',
                'RGA Cor Pulsed field ablasjon'                                              : 'INT10 - Hjerte behandling',
                'RGA Cor Elfys'                                                              : 'INT10 - Hjerte behandling',
                'RGA Cor Cryo Ablasjon'                                                      : 'INT10 - Hjerte behandling',
                'RGA Cor Ablasjon'                                                           : 'INT10 - Hjerte behandling',
                'RGA Cor Mitralklaff Intervensjon'                                           : 'INT10 - Hjerte behandling',
                'RGA Cor TAVI'                                                               : 'INT10 - Hjerte behandling',
                'RGV Cor Mitraclip'                                                          : 'INT10 - Hjerte behandling',
                'RGA Cor PTSMA'                                                              : 'INT10 - Hjerte behandling',
                'RGA Aorta Aortaklaff valvuloplastikk'                                       : 'INT10 - Hjerte behandling',
                'RGA Cor Koarktasjon'                                                        : 'INT10 - Hjerte behandling',
                'RGV Pulmonalarterier PTA'                                                   : 'INT10 - Hjerte behandling',
                'RGV Cor PDA'                                                                : 'INT10 - Hjerte behandling',

                

                # INT04 - Abdomen diagnostikk
                'RG Abdomen - Abscessografi & ~Fjerning'                                     : 'INT04 - Abdomen diagnostikk',
                'RG Abdomen gjennomlysning'                                                  : 'INT04 - Abdomen diagnostikk',
                'RG Abdomen - Abscessografi'                                                 : 'INT04 - Abdomen diagnostikk',
                'RGA Abdomen & ~Embolisering & Stent & ~PTA'                                 : 'INT04 - Abdomen diagnostikk',
                'RGA Nyrer & ~Embolisering & Stent & ~PTA'                                   : 'INT04 - Abdomen diagnostikk',
                'RGA Milt & ~Embolisering & Stent & ~PTA'                                    : 'INT04 - Abdomen diagnostikk',
                'RG Tarmpassasje'                                                            : 'INT04 - Abdomen diagnostikk',
                'RG Galleveier - PTC, diagnostikk & ~stent'                                  : 'INT04 - Abdomen diagnostikk',
                'RGV PancreasTX'                                                             : 'INT04 - Abdomen diagnostikk',
                'RGV Vena Cava Inferior'                                                     : 'INT04 - Abdomen diagnostikk',
                'RGA Nyrer & ~Stent'                                                         : 'INT04 - Abdomen diagnostikk',
                'RG Antegrad pyelografi & ~Nefrostomi'                                       : 'INT04 - Abdomen diagnostikk',
                'RGV Abdomen'                                                                : 'INT04 - Abdomen diagnostikk',
                'RG Shuntveier'                                                              : 'INT04 - Abdomen diagnostikk',
                'RG Tynntarm'                                                                : 'INT04 - Abdomen diagnostikk',
                'RG Diafragmabevegelse'                                                      : 'INT04 - Abdomen diagnostikk',
                'RG Shuntventil gjennomlysning (RF)'                                         : 'INT04 - Abdomen diagnostikk',
                'RG Gastroskopi'                                                             : 'INT04 - Abdomen diagnostikk',
                'RGA Tarm & ~Embolisering & Stent & ~PTA'                                    : 'INT04 - Abdomen diagnostikk',

                # INT11 - Abdomen behandling
                'RG Galleveier - Intern stent'                                               : 'INT11 - Abdomen behandling',
                'RG Galleveier - PTBD'                                                       : 'INT11 - Abdomen behandling',
                'RGA Aorta BEVAR/FEVAR & ~TEVAR'                                             : 'INT11 - Abdomen behandling',
                'RGA Aorta EVAR & ~TEVAR'                                                    : 'INT11 - Abdomen behandling',
                'RGA Abdomen Embolisering'                                                   : 'INT11 - Abdomen behandling',
                'RGA Aorta Stent/stentgraft'                                                 : 'INT11 - Abdomen behandling',
                'RGA Abdomen PTA'                                                            : 'INT11 - Abdomen behandling',
                'RGA Abdomen Stent/stentgraft (int.)'                                        : 'INT11 - Abdomen behandling',
                'RGA Nyrer Stent/stentgraft'                                                 : 'INT11 - Abdomen behandling',
                'Nefrostomi'                                                                 : 'INT11 - Abdomen behandling',
                'RGL Abdomen - Sklerosering'                                                 : 'INT11 - Abdomen behandling',
                'RG Abdomen - Innleggelse av dren'                                           : 'INT11 - Abdomen behandling',
                'RG Abdomen - Fjerning av dren'                                              : 'INT11 - Abdomen behandling',
                'RG Abdomen - Skifte'                                                        : 'INT11 - Abdomen behandling',
                'RG Lever - Sklerosering'                                                    : 'INT11 - Abdomen behandling',
                'RG Lever - Injeksjon'                                                       : 'INT11 - Abdomen behandling',
                'RGA Lever SIRT'                                                             : 'INT11 - Abdomen behandling',
                'RGA Lever PTA'                                                              : 'INT11 - Abdomen behandling',
                'RGA Lever Stent/stentgraft '                                                : 'INT11 - Abdomen behandling',
                'RGA Lever TACE'                                                  : 'INT11 - Abdomen behandling',
                'RGA Lever PTA'                                                 : 'INT11 - Abdomen behandling',
                'RGA LeverTX'                                               : 'INT11 - Abdomen behandling',
                'RGV Lever Embolisering'                                                 : 'INT11 - Abdomen behandling',
                'RGV Lever TIPS'                                            : 'INT11 - Abdomen behandling',
                'RGV Lever Stent/stentgraft'                                                : 'INT11 - Abdomen behandling',
                'RGA Milt Embolisering'                                                 : 'INT11 - Abdomen behandling',
                'RGA Milt Stent/stentgraft'                                                : 'INT11 - Abdomen behandling',
                'RGA NyreTX'                                                : 'INT11 - Abdomen behandling',
                'RGV Lever TIPS'                                            : 'INT11 - Abdomen behandling',
                'RGV Portvene'                                                : 'INT11 - Abdomen behandling',
                'RG Galleblære'                                               : 'INT11 - Abdomen behandling',
                'RGA Tarm Embolisering'                                                : 'INT11 - Abdomen behandling',
                'RGA Tarm PTA'                                                : 'INT11 - Abdomen behandling',
                'RGA Tarm Stent/stentgraft'                                               : 'INT11 - Abdomen behandling',
                
                # INT05 - Bekken diagnostikk
                'RG Lumbo-sacralcolumna gjennomlysning (RF)'                                 : 'INT05 - Bekken diagnostikk',
                'RGA Prostata & ~Embolisering'                                               : 'INT05 - Bekken diagnostikk',
                'RGV Bekken & ~Embolisering & Stent & ~PTA'                                  : 'INT05 - Bekken diagnostikk',
                'RG Bekken og hofte'                                                         : 'INT05 - Bekken diagnostikk',
                'RG MUCG (RF)'                                                               : 'INT05 - Bekken diagnostikk',
                'RG Urografi'                                                                : 'INT05 - Bekken diagnostikk',
                'RG Urinveier'                                                               : 'INT05 - Bekken diagnostikk',
                'RG Hysterosalpingograf'                                                     : 'INT05 - Bekken diagnostikk',
                'RG Urethragrafi'                                                            : 'INT05 - Bekken diagnostikk',

                # INT12 - Bekken behandling 
                'RGA Bekken Stent/stentgraft'                                                : 'INT12 - Bekken behandling',
                'RG Urinveier - Innlegging av stent'                                         : 'INT12 - Bekken behandling',
                'RGA Bekken Embolisering'                                                    : 'INT12 - Bekken behandling',
                'RGA Prostata Embolisering'                                                  : 'INT12 - Bekken behandling',
                'RGV Bekken Embolisering'                                                    : 'INT12 - Bekken behandling',
                'RGV Bekken Sklerosering'                                                    : 'INT12 - Bekken behandling',
                'RGV Bekken PTA'                                                             : 'INT12 - Bekken behandling',
                'RGL Bekken - Sklerosering'                                                  : 'INT12 - Bekken behandling',
                'RG Bekken - Sklerosering'                                                  : 'INT12 - Bekken behandling',
                'RG Hofte - Injeksjon'                                                    : 'INT12 - Bekken behandling',

                
                # INT06 - Ekstremitet diagnostikk
                'RGA Overex'                                                                 : 'INT06 - Ekstremitet diagnostikk',
                'RGV Overex'                                                                 : 'INT06 - Ekstremitet diagnostikk',
                'RGV Underex.'                                                               : 'INT06 - Ekstremitet diagnostikk',
                'RGA Underex'                                                                : 'INT06 - Ekstremitet diagnostikk',
                # INT13 - Ekstremitet behandling
                'RGL Overex. - Sklerosering'                                                 : 'INT13 - Ekstremitet behandling',
                'RGL Underex. - Sklerosering'                                                : 'INT13 - Ekstremitet behandling',
                'RGA Overex. PTA'                                                    : 'INT13 - Ekstremitet behandling',
                'RGA Overex. Annen intervensjon'                                             : 'INT13 - Ekstremitet behandling',
                'RGA Overex. Embolisering'                                                  : 'INT13 - Ekstremitet behandling',
                'RGV Overex. Sklerosering'                                                   : 'INT13 - Ekstremitet behandling',
                'RGA Underex. Trombektomi/embolektomi'                                       : 'INT13 - Ekstremitet behandling',
                'RGV Underex. Sklerosering'                                                  : 'INT13 - Ekstremitet behandling',
                
                
                # INT07 - Øvrig og sammenslåtte US diagnostikk
                'Columna'                                                                    : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'Totalcolumna gjennomlysning (RF)'                                           : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'Abdomen & Bekken & ~EVAR & ~Stent & ~Embolisering'                          : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'RG Colon'                                                                   : 'INT07 - Øvrig og sammenslåtte US diagnostikk',

                # INT14 - Øvrig og sammenslåtte US behandling
                'RGA Columna Embolisering'                                                   : 'INT14 - Øvrig og sammenslåtte US behandling',
                'Abdomen & Bekken'                                                           : 'INT14 - Øvrig og sammenslåtte US behandling',
                'Aorta EVAR & TEVAR'                                                         : 'INT14 - Øvrig og sammenslåtte US behandling',

        
            }
    return mapping
