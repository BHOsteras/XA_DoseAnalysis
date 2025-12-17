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
                'RGA Caput og collum & ~Embolisering & ~Trombektomi & ~Stent & ~Injeksjon & ~PTA & ~Sklerosering'  : 'INT01 - Hode og hals',
                'RGA Caput & ~Embolisering & ~Trombektomi & ~Stent & ~Injeksjon & ~PTA & ~Sklerosering'            : 'INT01 - Hode og hals',
                'CT Caput & ~Embolisering & ~Trombektomi & ~Stent & ~Injeksjon & ~PTA & ~Sklerosering'             : 'INT01 - Hode og hals',
                'RG Cervicalcolumna'                                                                               : 'INT01 - Hode og hals',
                'RG Svelgfunksjon dynamisk undersøkelse (RF) & ~Øsofagus'                                          : 'INT01 - Hode og hals',
                'RG Videofluoroskopi'                                                                              : 'INT01 - Hode og hals',
                'RG Hypopharynx & ~Øsofagus'                                                                       : 'INT01 - Hode og hals',
                'RG ØVD & ~Øsofagus & ~Tarmpassasje & ~RG Colon & ~Abdomen'                                        : 'INT01 - Hode og hals', 
                'RG CVK & ~Embolisering & ~RGA Cor & ~RGV Cor & ~RGA Abdomen & ~Nedleggelse'                       : 'INT01 - Hode og hals',
        
                # INT08 - Hode og hals behandling
                'RGA Caput Embolisering (int.)'                                              : 'INT08 - Hode og hals',
                'RGA Caput Trombektomi/embolektomi (int.)'                                   : 'INT08 - Hode og hals',
                'RGA Caput Stent/stentgraft (int.)'                                          : 'INT08 - Hode og hals',
                'RGA Caput Injeksjon av terapeutisk substans (int.)'                         : 'INT08 - Hode og hals',
                'RGA Caput PTA (int.)'                                                       : 'INT08 - Hode og hals',
                'RGL Caput  - Sklerosering'                                                  : 'INT08 - Hode og hals',
                'RGL Collum - Sklerosering'                                                  : 'INT08 - Hode og hals',
                'RGA Collum Embolisering'                                                    : 'INT08 - Hode og hals',
                'RGV Caput Sklerosering'                                                     : 'INT08 - Hode og hals',    
                'RGV Collum Sklerosering'                                                    : 'INT08 - Hode og hals',
                'RG Shunt'                                                                   : 'INT08 - Hode og hals',
                
                # INT02 - Thorax diagnostikk
                'RG Thorax gjennomlysning (RF)'                                                 : 'INT02 - Thorax diagnostikk',
                'RGA Thoracalaorta & ~Embolisering & ~TEVAR & ~RGA Cor & ~Stent'                : 'INT02 - Thorax diagnostikk',
                'RGA Thorax & ~Embolisering & ~Stent & ~PTA & ~Trombektomi & ~RGA Cor'          : 'INT02 - Thorax diagnostikk',
                'RG Bronkoskopi (RF)'                                                           : 'INT02 - Thorax diagnostikk',
                'RG Trachea gjennomlysning (RF)'                                                : 'INT02 - Thorax diagnostikk',
                'RG Thorax & ~Drenasje & ~Embolisering & ~Sklerosering'                         : 'INT02 - Thorax diagnostikk',
                'RG Øsofagus & ~ØVD & ~Svelgfunksjon & ~Hypopharynx'                            : 'INT02 - Thorax diagnostikk',
                'RGV Pulmonalarterier & ~Embolisering & Stent & ~PTA & ~RGA Cor & ~Trombektomi' : 'INT02 - Thorax diagnostikk',
                'RG Øsofagus TBE'                                                               : 'INT02 - Thorax diagnostikk',
                'RGV Pulmonalarterier & ~Embolisering & Stent & ~PTA & ~RGA Cor & ~Trombektomi' : 'INT02 - Thorax diagnostikk',
                'RGV Thorax & ~Bytte & ~Fjerning & ~Innleggelse & ~Sklerosering'                : 'INT02 - Thorax diagnostikk',
                'RGV Pulmonalarterier & ~Embolisering & ~Stent & ~PTA & ~Trombektomi'           : 'INT02 - Thorax diagnostikk',
                
                # INT09 - Thorax behandling
                'RG Thorax - Drenasje'                                                          : 'INT09 - Thorax behandling',
                'RGA Thorax Embolisering & ~RGA Bekken'                                         : 'INT09 - Thorax behandling',   
                'RGA Thorax Stent/stentgraft & ~Caput'                                          : 'INT09 - Thorax behandling',
                'RGA Aorta TEVAR & ~BEVAR/FEVAR & ~Aorta EVAR'                                  : 'INT09 - Thorax behandling',
                'RGL Thorax - Sklerosering'                                                     : 'INT09 - Thorax behandling',
                'RGV Thorax Sklerosering'                                                       : 'INT09 - Thorax behandling',
                'RGA Bronkialarterier Embolisering'                                             : 'INT09 - Thorax behandling',
                'RGV Pulmonalarterier Embolisering'                                             : 'INT09 - Thorax behandling',
                'RGV Pulmonalarterier PTA'                                                      : 'INT09 - Thorax behandling',
                'RGV Pulmonalklaff & ~RGV Cor'                                                  : 'INT09 - Thorax behandling',
                'RGA Thorax Trombektomi & ~RGA Abdomen'                                         : 'INT09 - Thorax behandling',
                'RGV Thorax Innleggelse'                                                        : 'INT09 - Thorax behandling',
                'RGV Thorax Bytte & ~TIPS'                                                      : 'INT09 - Thorax behandling',
                'RGV Thorax Fjerning'                                                           : 'INT09 - Thorax behandling',

                
                # INT03 - Hjerte diagnostikk
                'RGV Cor Biopsi'                                                                : 'INT03 - Hjerte diagnostikk',
                'RGV Cor Hø kat & ~ASD'                                                         : 'INT03 - Hjerte diagnostikk',
                'RGV Cor Høyre kat & ~ASD'                                                      : 'INT03 - Hjerte diagnostikk',
                'RGA Cor Koronarangiografi & ~PCI & ~TAVI & ~Mitraclip & ~PTSMA & ~Agonal & ~PTA & ~RGV Cor Temporær PM' : 'INT03 - Hjerte diagnostikk',
                'RGA Cor FFR/IFR & ~PCI & ~TAVI & ~Mitraclip & ~PTSMA & ~RGV Cor Temporær'      : 'INT03 - Hjerte diagnostikk',
                'RGA Cor Hjertefilming & ~PCI & ~TAVI & ~Mitraclip & ~PTSMA'                    : 'INT03 - Hjerte diagnostikk',
                'RGV Cor Høyresidig hjertekateterisering & ~PTA & ~Bronkoskopi & ~PFO & ~ASD & ~PDA & ~RGV Vena Cava' : 'INT03 - Hjerte diagnostikk',
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
                'PCI & ~TAVI & ~Mitraclip & ~PTSMA & ~Agonal & ~PTA'                         : 'INT10 - Hjerte behandling',
                'RGA Cor Ablasjon'                                                           : 'INT10 - Hjerte behandling',
                'RGA Cor Mitralklaff Intervensjon'                                           : 'INT10 - Hjerte behandling',
                'RGA Cor TAVI'                                                               : 'INT10 - Hjerte behandling',
                'RGV Cor Mitraclip'                                                          : 'INT10 - Hjerte behandling',
                'RGA Cor PTSMA'                                                              : 'INT10 - Hjerte behandling',
                'RGA Aorta Aortaklaff valvuloplastikk'                                       : 'INT10 - Hjerte behandling',
                'RGA Cor Koarktasjon'                                                        : 'INT10 - Hjerte behandling',
                'RGV Pulmonalarterier PTA'                                                   : 'INT10 - Hjerte behandling',
                'RGV Cor PDA'                                                                : 'INT10 - Hjerte behandling',
                'RGV Cor Temporær PM'                                                        : 'INT10 - Hjerte behandling',

                # INT04 - Abdomen diagnostikk
                'RG Abdomen - Abscessografi & ~Fjerning & ~Innleggelse & ~Skifte & ~Drenasje'        : 'INT04 - Abdomen diagnostikk',
                'RG Abdomen gjennomlysning & ~PTBD & ~Fjerning & ~Innleggelse & ~Skifte & ~Drenasje' : 'INT04 - Abdomen diagnostikk',
                'RGA Abdomen & ~Embolisering & ~Stent & ~PTA & ~PCI'                                 : 'INT04 - Abdomen diagnostikk',
                'RGA Nyrer & ~Embolisering & ~Stent & ~PTA & ~TEVAR'                                 : 'INT04 - Abdomen diagnostikk',
                'RG Tarmpassasje'                                                                    : 'INT04 - Abdomen diagnostikk',
                'RG Galleveier - PTC, diagnostikk & ~stent & ~PTBD & ~Fjerning & ~Skifte & ~Annen'   : 'INT04 - Abdomen diagnostikk',
                'RGV PancreasTX'                                                                     : 'INT04 - Abdomen diagnostikk',
                'RGV Vena Cava Inferior & ~Embolisering & ~Stent & ~PTA'                             : 'INT04 - Abdomen diagnostikk',
                'RG Antegrad pyelografi & ~Nefrostomi'                                               : 'INT04 - Abdomen diagnostikk',
                'RGV Abdomen'                                                                        : 'INT04 - Abdomen diagnostikk',
                'RG Tynntarm'                                                                        : 'INT04 - Abdomen diagnostikk',
                'RG Diafragmabevegelse'                                                              : 'INT04 - Abdomen diagnostikk',
                'RG Gastroskopi'                                                                     : 'INT04 - Abdomen diagnostikk',
                'RGA Tarm & ~Embolisering & ~Stent & ~PTA'                                           : 'INT04 - Abdomen diagnostikk',
                'RGV Portvene & ~Stent & ~Fjerning & ~Embolisering & ~TIPS & ~PTA'                   : 'INT04 - Abdomen diagnostikk',
                'RG Galleblære & ~PTBD & ~Fjerning & ~Skifte & ~Annen'                               : 'INT04 - Abdomen diagnostikk',
                'RGV Binyrer Venekateterisering'                                                     : 'INT04 - Abdomen diagnostikk',
                'RGV Vena Cava & ~PTA & ~Stent'                                                      : 'INT04 - Abdomen diagnostikk',
                'RG V+D enkeltkontrast & ~Nedleggelse'                                               : 'INT04 - Abdomen diagnostikk',


                # INT11 - Abdomen behandling
                'RG Galleveier - Intern stent'                                               : 'INT11 - Abdomen behandling',
                'RG Galleveier - PTBD'                                                       : 'INT11 - Abdomen behandling',
                'RG Galleveier - Annen'                                                      : 'INT11 - Abdomen behandling',
                'RGA Aorta BEVAR/FEVAR & ~TEVAR'                                             : 'INT11 - Abdomen behandling',
                'RGA Aorta EVAR & ~TEVAR & ~RGA Bekken'                                      : 'INT11 - Abdomen behandling',
                'RGA Abdomen Embolisering & ~TEVAR & ~Bekken'                                : 'INT11 - Abdomen behandling',
                'RGA Aorta Stent/stentgraft & ~Thorax & ~Bekken'                             : 'INT11 - Abdomen behandling',
                'RGA Abdomen PTA & ~Bekken'                                                  : 'INT11 - Abdomen behandling',
                'RGA Abdomen Stent/stentgraft (int.) & ~Bekken & ~TEVAR'                     : 'INT11 - Abdomen behandling',
                'RGA Nyrer Stent/stentgraft & ~TEVAR'                                        : 'INT11 - Abdomen behandling',
                'RGA Nyrer Embolisering & ~TEVAR'                                            : 'INT11 - Abdomen behandling',
                'Nefrostomi'                                                                 : 'INT11 - Abdomen behandling',
                'RGL Abdomen - Sklerosering'                                                 : 'INT11 - Abdomen behandling',
                'RG Abdomen - Innleggelse av dren'                                           : 'INT11 - Abdomen behandling',
                'RG Abdomen - Fjerning av dren'                                              : 'INT11 - Abdomen behandling',
                'RG Abdomen - Skifte'                                                        : 'INT11 - Abdomen behandling',
                'RG Abdomen - Drenasje'                                                      : 'INT11 - Abdomen behandling',
                'RG Lever - Sklerosering'                                                    : 'INT11 - Abdomen behandling',
                'RG Lever - Injeksjon'                                                       : 'INT11 - Abdomen behandling',
                'RGA Lever SIRT'                                                             : 'INT11 - Abdomen behandling',
                'RGA Lever PTA'                                                              : 'INT11 - Abdomen behandling',
                'RGA Lever Embolisering'                                                     : 'INT11 - Abdomen behandling',
                'RGA Lever Stent/stentgraft '                                                : 'INT11 - Abdomen behandling',
                'RGA Lever TACE'                                                             : 'INT11 - Abdomen behandling',
                'RGA Lever PTA'                                                              : 'INT11 - Abdomen behandling',
                'RGA LeverTX'                                                                : 'INT11 - Abdomen behandling',
                'RGV Lever Embolisering'                                                     : 'INT11 - Abdomen behandling',
                'RGV Portvene Embolisering'                                                  : 'INT11 - Abdomen behandling',
                'RGV Portvene Stent'                                                         : 'INT11 - Abdomen behandling',
                'RGV Portvene PTA'                                                           : 'INT11 - Abdomen behandling',
                'RGV Lever TIPS'                                                             : 'INT11 - Abdomen behandling',
                'RGV Lever Stent/stentgraft'                                                 : 'INT11 - Abdomen behandling',
                'RGA Milt Embolisering'                                                      : 'INT11 - Abdomen behandling',
                'RGA Milt Stent/stentgraft'                                                  : 'INT11 - Abdomen behandling',
                'RGA Nyrer PTA'                                                              : 'INT11 - Abdomen behandling',
                'RGA NyreTX'                                                                 : 'INT11 - Abdomen behandling',
                'RGV Lever TIPS'                                                             : 'INT11 - Abdomen behandling',
                'RGA Tarm Embolisering'                                                      : 'INT11 - Abdomen behandling',
                'RGA Tarm PTA'                                                               : 'INT11 - Abdomen behandling',
                'RGA Tarm Stent/stentgraft & ~TEVAR'                                         : 'INT11 - Abdomen behandling',
                'RG ERCP'                                                                    : 'INT11 - Abdomen behandling',
                'RG Galleblære & Skifte'                                                     : 'INT11 - Abdomen behandling',
                'RG Abdomen - Drenasje'                                                      : 'INT11 - Abdomen behandling',
                'RG Nedleggelse av'                                                          : 'INT11 - Abdomen behandling',
                'RGV Vena Cava & PTA & ~RGV Bekken'                                          : 'INT11 - Abdomen behandling',
                'RG Tarm - Perkutan'                                                         : 'INT11 - Abdomen behandling',
                
                # INT05 - Bekken diagnostikk
                'RG Lumbo-sacralcolumna gjennomlysning (RF) & ~Myelografi & ~Markørinnleggelse' : 'INT05 - Bekken diagnostikk',
                'RGA Prostata & ~Embolisering'                                               : 'INT05 - Bekken diagnostikk',
                'RGV Bekken & ~Embolisering & Stent & ~PTA'                                  : 'INT05 - Bekken diagnostikk',
                'RG Bekken og hofte'                                                         : 'INT05 - Bekken diagnostikk',
                'RG MUCG (RF) & ~RG Colon'                                                   : 'INT05 - Bekken diagnostikk',
                'RG Urografi'                                                                : 'INT05 - Bekken diagnostikk',
                'RG Urinveier & ~Nefrostomi & ~Nyrer & ~Stent'                               : 'INT05 - Bekken diagnostikk',
                'RG Hysterosalpingograf'                                                     : 'INT05 - Bekken diagnostikk',
                'RG Urethragrafi'                                                            : 'INT05 - Bekken diagnostikk',

                # INT12 - Bekken behandling 
                'RGA Bekken Stent/stentgraft & ~TAVI & ~Aorta BEVAR/FEVAR'                   : 'INT12 - Bekken behandling',
                'RG Urinveier - Innlegging av stent & ~Nefrostomi'                           : 'INT12 - Bekken behandling',
                'RGA Bekken Embolisering & ~Abdomen & ~Aorta & ~Thorax'                      : 'INT12 - Bekken behandling',
                'RGA Prostata Embolisering'                                                  : 'INT12 - Bekken behandling',
                'RGV Bekken Embolisering & ~Abdomen & ~Aorta & ~Thorax'                      : 'INT12 - Bekken behandling',
                'RGV Bekken Sklerosering'                                                    : 'INT12 - Bekken behandling',
                'RGV Bekken PTA & ~PCI'                                                      : 'INT12 - Bekken behandling',
                'RGA Bekken PTA & ~PCI & ~TAVI & ~EVAR & ~Nyrer & ~Tarm & ~Abdomen'          : 'INT12 - Bekken behandling',
                'RGL Bekken - Sklerosering'                                                  : 'INT12 - Bekken behandling',
                'RG Bekken - Sklerosering'                                                   : 'INT12 - Bekken behandling',
                'RG Hofte - Injeksjon'                                                       : 'INT12 - Bekken behandling',
                'RG Defecografi'                                                             : 'INT12 - Bekken behandling',
                'RGA Uterus Embolisering'                                                    : 'INT12 - Bekken behandling',
                
                # INT06 - Ekstremitet diagnostikk
                'RGA Overex & ~TEVAR  & ~Stent & ~Trombektomi & ~PTA & ~Annen & ~Embolisering'  : 'INT06 - Ekstremitet diagnostikk',
                'RGV Overex  & ~Stent & ~Trombektomi & ~PTA & ~Annen & ~Embolisering'           : 'INT06 - Ekstremitet diagnostikk',
                'RGV Underex. & ~Stent & ~Trombektomi & ~PTA & ~Annen & ~Embolisering & ~Bekken & ~Sklerosering' : 'INT06 - Ekstremitet diagnostikk',
                'RGA Underex  & ~Stent & ~Trombektomi & ~PTA & ~Annen & ~Embolisering & ~Bekken & ~Sklerosering' : 'INT06 - Ekstremitet diagnostikk',
                # INT13 - Ekstremitet behandling
                'RGL Overex. - Sklerosering'                                                 : 'INT13 - Ekstremitet behandling',
                'RGL Underex. - Sklerosering'                                                : 'INT13 - Ekstremitet behandling',
                'RGA Underex. PTA & ~RGA Bekken'                                             : 'INT13 - Ekstremitet behandling',
                'RGA Overex. PTA & ~Thorax'                                                  : 'INT13 - Ekstremitet behandling',
                'RGA Overex. Annen intervensjon'                                             : 'INT13 - Ekstremitet behandling',
                'RGA Overex. Embolisering & ~TEVAR'                                          : 'INT13 - Ekstremitet behandling',
                'RGV Overex. Sklerosering'                                                   : 'INT13 - Ekstremitet behandling',
                'RGV Overex. PTA & ~Thorax'                                                  : 'INT13 - Ekstremitet behandling',
                'RGA Underex. Trombektomi/embolektomi & ~RGA Bekken & ~TAVI'                 : 'INT13 - Ekstremitet behandling',
                'RGV Underex. Sklerosering  & ~RGA Bekken'                                   : 'INT13 - Ekstremitet behandling',
                'RGA Underex. Embolisering  & ~RGA Bekken'                                   : 'INT13 - Ekstremitet behandling',
                
                
                # INT07 - Øvrig og sammenslåtte US diagnostikk
                #'Columna'                                                                    : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'Totalcolumna gjennomlysning (RF) & ~Myelografi & ~Markørinnleggelse'        : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'Abdomen & Bekken & ~EVAR & ~Stent & ~Embolisering'                          : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'RG Colon'                                                                   : 'INT07 - Øvrig og sammenslåtte US diagnostikk',
                'RG Øsofagus & Svelgfunksjon'                                                : 'INT07 - Øvrig og sammenslåtte US diagnostikk', 
                'RG Øsofagus & Hypopharynx & ~TBE'                                           : 'INT07 - Øvrig og sammenslåtte US diagnostikk',

                # INT14 - Øvrig og sammenslåtte US behandling
                'RGA Columna Embolisering'                                                   : 'INT14 - Øvrig og sammenslåtte US behandling',
                'Abdomen Embolisering & Bekken'                                              : 'INT14 - Øvrig og sammenslåtte US behandling',
                'Aorta EVAR & TEVAR'                                                         : 'INT14 - Øvrig og sammenslåtte US behandling',
                'Aorta EVAR & Bekken Embolisering'                                           : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Cyste'                                                         : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Injeksjon'                                                     : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Sideledd'                                                      : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Biopsi'                                                        : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Myelografi'                                                    : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Markørinnleggelse'                                             : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Punksjon'                                                      : 'INT14 - Øvrig og sammenslåtte US behandling',
                'RG Columna - Vertebroplastikk'                                              : 'INT14 - Øvrig og sammenslåtte US behandling',

        
            }
    return mapping
