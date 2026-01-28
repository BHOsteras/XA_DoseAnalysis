"""
This module contains a functions for returning a mapping dictionary to facilitate interpretation of the decription column 
(column: 'Beskrivelse') to a new column (column: 'Mapped Procedures').
The 'Mapped Procedures' column is used to organize the description into useful categories, make relevant plots, etc.
"""

def get_rad_xa_mapping_dict():
    """
    Here the user can hardcode the mapping dictionary for interventional radiology procedures:

    In the inteventional radiology department, the description column (column: 'Beskrivelse') usually contains
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



    # Create the mapping dictionary:
    mapping = { # Caput og Collum prosedyrer:
                'Caput Embolisering'                    : 'Caput Embolisering',
                'Caput Trombektomi & ~Caput Embolisering'
                                                        : 'Trombektomi',
                'Caput og collum & ~Caput Embolisering & ~Caput Trombektomi'    
                                                        : 'Caput og collum',
                'Myelografi'                            : 'Myelografi',
                'RG Columna - Vertebroplastikk (int.)'  : 'Vertebroplastikk',  # UL
                'RG Columna & ~Myelografi & ~Caput & ~Vertebroplastikk '
                                                        : 'RG Columna eks. Myelografi og vertebroplastikk',  # UL
                'Cervical Nerverotsinjeksjon'           : 'Cervical Nerverotsinjeksjon',
                
                # IVS Operasjon:
                'RG Tinningben'                         : 'Cochlia',
                'RG Scoliose'                           : 'Scoliose',
                
                # RF Prosedyrer:
                'RG Shuntveier'                         : 'Shuntveier/Shuntventil', 
                'RG Shuntventil'                        : 'Shuntveier/Shuntventil',
                'Diafragmabevegelse'                    : 'Diafragmabevegelse',
                'Hysterosalpingografi'                  : 'HSG',
                'RG Svelgfunksjon'                      : 'Svelgfunksjon',      
                'Øsofagus & ~Svelgfunksjon'             : 'Øsofagus/ØVD, eks. svelgfunksjon',
                'Øsophagus & ~Svelgfunksjon'            : 'Øsofagus/ØVD, eks. svelgfunksjon',
                'RG ØVD & ~Svelgfunksjon'               : 'Øsofagus/ØVD, eks. svelgfunksjon', 
                'RG Nedleggelse av ventrikkelsonde & ~ØVD' 
                                                        : 'Nedleggelse av ventrikkelsonde',
                'Urethragrafi'                          : 'Urethragrafi/Urografi/Urinveier/MUCG',
                'RG Urografi'                           : 'Urethragrafi/Urografi/Urinveier/MUCG',
                'RG MUCG'                               : 'Urethragrafi/Urografi/Urinveier/MUCG',
                'RG Urinveier & ~Nefrostomi & ~Pyelografi' 
                                                        : 'Urethragrafi/Urografi/Urinveier/MUCG', 
                'RG Defecografi'                        : 'Defecografi',
                'RG Gastroskopi & ~PTBD'                : 'Gastroskopi',    
                'RG Videofluoroskopi & ~Øsofagus & ~ØVD & ~Svelgfunksjon'
                                                        : 'Videofluoroskopi',
                 
                # Abdomen/Bekken prosedyrer:
                'Nefrostomi & innleggelse av dren & ~PTC'      
                                                        : 'Nefrostomi innleggelse', 
                'Nefrostomi & ~innleggelse av dren & ~PTC'  
                                                        : 'Nefrostomi/Pyelografi skifte eller fjerning',
                'Pyelografi & ~Nefrostomi'              : 'Nefrostomi/Pyelografi skifte eller fjerning',
                'Lever TACE'                            : 'TACE',
                'PTC, diagnostikk'                      : 'PTC/PTBD/ERCP',
                'Galleveier - PTBD'                     : 'PTC/PTBD/ERCP',
                'PTC Stentinnleggelse'                  : 'PTC/PTBD/ERCP',
                'ERCP'                                  : 'PTC/PTBD/ERCP',
                'RG Galleblære & ~PTC & ~Galleveier'    : 'RG Galleblære u. PTC eller Galleveier',               
                'BEVAR/FEVAR'                           : 'BEVAR/FEVAR',
                'TEVAR & ~BEVAR/FEVAR'                  : 'TEVAR',
                'EVAR & ~TEVAR & ~BEVAR/FEVAR'          : 'EVAR',
                'RGA Abdomen PTA'                       : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'RGA Abdomen Embolisering & ~EVAR'      : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'RGA Aorta PTA & ~EVAR'                 : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'RGA Abdomen Stent & ~EVAR'             : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'RGA Aorta Stent'                       : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'Bekken Embolisering (int.) & ~TACE & ~EVAR'    
                                                        : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'Lever Embolisering (int.) & ~TACE'     : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',                                                    
                'RGA Bekken PTA &~EVAR'                 : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'RGA Bekken Stent & ~EVAR'              : 'Abdomen/Bekken/Aorta PTA/Embolisering/Stent/Stentgraft',
                'RGA Milt'                              : 'Milt/Nyrer',
                'RGA Nyrer & ~RGA Abdomen Stent & ~EVAR & ~Aorta & ~Bekken Embolisering'
                                                        : 'Milt/Nyrer',
                'RGA Nyrer PTA & ~RGA Abdomen Stent & ~EVAR & ~Aorta & ~Bekken Embolisering'                        
                                                        : 'Milt/Nyrer',

                'RG Abdomen - Abscessografi & ~PTC, diagnostikk & ~Galleveier - PTBD & ~Galleblære & ~Nefrostomi'
                                                        : 'RG Abdomen - Abscessografi, Fjerning/Skifte av dren',
                'RG Abdomen - Skifte av dren & ~PTC, diagnostikk & ~Galleveier - PTBD & ~Galleblære & ~Nefrostomi & ~Galleblære'
                                                        : 'RG Abdomen - Abscessografi, Fjerning/Skifte av dren',
                'RG Abdomen - Fjerning av dren & ~PTC, diagnostikk & ~Galleveier - PTBD & ~Galleblære & ~Nefrostomi'
                                                        : 'RG Abdomen - Abscessografi, Fjerning/Skifte av dren',
                #'RG Abdomen & ~PTC, diagnostikk (int.) & ~ERCP & ~ØVD & ~Galleveier - PTBD & ~RG Galleblære & ~Embolisering & ~RGL & ~dren & ~Abscessografi' 
                #                                        : 'RG Abdomen diverse',

                
                # Thorax prosedyrer:
                'RGV Pulmonalarterier'                  : 'Pulmonalarterier/PTA/Embolisering',
                'RGV Thorax & ~Pulmonalarterier'        : 'RGV Thorax',

                # Andre
                'RGL'                                   : 'Lymfangiografi', 

                # Ekstremiteter:                                        
                'RGV Underex'                           : 'Underex',
                'RGA Underex & ~Bekken & ~Abdomen'      : 'Underex',
                'RGV Overex & ~Thorax'                  : 'Overex',
                'RGA Overex & ~EVAR & ~Caput'           : 'Overex',
                } 

    return mapping