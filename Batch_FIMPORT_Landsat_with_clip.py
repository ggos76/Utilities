#!/usr/bin/env python
'''----------------------------------------------------------------------
 * - Copyright (c) 2023  All rights reserved.                          -

 * ----------------------------------------------------------------------
'''

# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale
locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")

import os, fnmatch, sys, time, pathlib

from pci.fimport import fimport
from pci.clip import clip
from pci.api import datasource as ds
from pci.exceptions import PCIException

#-----------------------------------------------------------------------------------------------------
#  Discover Landsat-08 scenes and import them into a PIX file. 
#-----------------------------------------------------------------------------------------------------
'''
*** Metadata content -->(example): 

Acquisition_DateTime2 --> ( 2019-08-05T15:38:21.681110Z )
Acquisition_DateTime3 --> ( 20190805 )
Landsat_product_id    --> ( LC08_L1TP_014028_20190805_20200827_02_T1 )
PlatformName2         --> ( Landsat-8 )
Source_ID           -->  ( LC80140282019217LGN00 )
WRS_PATH            --> ( 14 )
WRS_ROW             -->( 28 )

*** output_filename_format

1 =  prefix + Landsat_product_id + ".pix" 
2 = 
3 = prefix + Acquisition_DateTime3 + PlatformName2 + WRS_PATH + WRS_ROW + ".pix" 
4 = prefix + Acquisition_DateTime3 + Source_ID + ".pix" 

'''

#----------------------------------------------------------------------------------------------
#  User defined variables
#----------------------------------------------------------------------------------------------

# Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
Input_mode = 2

Input_mode_1_MFILE = r" "
Input_mode_2_Search_Folder = r"D:\HBL_Palsas_classif\Lansat_TS\In\Unzip"
Input_mode_2_keyword = "*_MTL.txt"

import_MS = "no"
import_MS_Thermal = "yes"   # Use this option for the new level2  Landsat collection
import_PAN = "yes"

# Output options
output_folder = r"E:\out_landsat"
output_filename_format = 3
prefix = "HBL_"                    # Optional

perform_clip = "yes"
clip_layer_AOI = r"D:\HBL_Palsas_classif\Clip_layer_Landsat_TS.pix"
delete_original_after_clipping = "yes"
# out_file_option = 1    # options are 1 (error) 2 (replace) 3 (unique ID)
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
#  Main program
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
start = time.time()
# ------------------------------------------------------------------------------------------------------
# A ) Find all scenes to ingest
file_ingest_list = []
if Input_mode == 1:  # Read an Existing MFILE and create a list of file to process

    with open(Input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line = line.strip()
            file_ingest_list.append(line)

elif Input_mode == 2:  # Search folder with a keyword

    for root, dirs, files in os.walk(Input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, Input_mode_2_keyword):
            file_ingest_list.append(os.path.join(root, filename))
else:
    print("Error- Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()

# For Input_mode == 2,   verify if at least one file was found.
if len(file_ingest_list) == 0:
    print("\t")
    print("Error- no files found")
    print("Specify another keyword or search folder")
    sys.exit()


# ------------------------------------------------------------------------------------------------------
#A) Early validation

yes_validation_list = ["y","yes","yse","yy", "yys"]

if output_filename_format not in [1,2,3,4]:
    print("\t")
    print ("Error - Output file name format is not valid")
    print ("Specified value is " + str(Output_filename_format))
    print ("Accepted values are: 1, 2, 3 or 4")
    sys.exit()

import_MS = import_MS.lower()
if import_MS in yes_validation_list:
    import_MS = True
    import_type = "?t=MS"
    suffix_out = "_MS.pix"
else:     
    import_MS = False

import_MS_Thermal = import_MS_Thermal.lower()
if import_MS_Thermal in yes_validation_list:
    import_MS_Thermal = True
    import_type = "?t=MS_Thermal"
    suffix_out = "_MS_Thermal.pix"
else:
    import_MS_Thermal = False

if import_MS_Thermal is True and import_MS is True:
    print ("Error - import_MS_Thermal and import_MS are selection")
    print ("Only one of the two option can be selected")
    sys.exit()

import_PAN = import_PAN.lower()
if import_PAN in yes_validation_list:
    import_PAN = True
else:     
    import_PAN = False

perform_clip = perform_clip.lower()
if perform_clip in yes_validation_list:
    perform_clip = True

    if pathlib.Path(clip_layer_AOI).is_file() is True: 
        print ("AOI clip layer found")
        print ("\t")
    else:
        print ("Error! - Clip layer not found")
        print ("Please verify the path and filename of  clip_layer_AOI")      
        sys.exit()
else:     
    perform_clip = False

delete_original_after_clipping = delete_original_after_clipping.lower()
if delete_original_after_clipping in yes_validation_list:
    delete_original_after_clipping = True
else:
    delete_original_after_clipping = False

# ------------------------------------------------------------------------------------------------------
#C.1) Paths formating
newpaths_list = []

for ii in file_ingest_list:
    print (ii)
    drivel =  (ii[0])

    input_scene = ("file:/" + drivel + "%3A/" + ii[3:]) 
    input_scene2 = input_scene.replace("\\","//")   
    print (input_scene2)
    newpaths_list.append (input_scene2)
    

#C.2) Metadata acquistion

print ("\t")
print (time.strftime("%H:%M:%S") + " Metadata acquistion")
print ("\t")

Acquisition_DateTime2 =[]
Acquisition_DateTime3 =[]
Landsat_product_id2 = []
PlatformName2=[]
Source_id2 =[] 
wrs_path2 = []
wrs_row2 = []

num_files = str (len (newpaths_list))
count = 1
for ii in newpaths_list:
    print(time.strftime("%H:%M:%S") + " Importing metadata, file " + str (count) + " of "+ num_files)

    with ds.open_dataset(ii + import_type, ds.eAM_READ) as ds2:
        aux = ds2.aux_data
        
        Acquisition_DateTime = aux.get_file_metadata_value('Acquisition_DateTime')
        Acquisition_DateTime2.append(Acquisition_DateTime)  
        
        Landsat_product_id = aux.get_file_metadata_value('LANDSAT_PRODUCT_ID')
        Landsat_product_id2.append(Landsat_product_id)     

        PlatformName = aux.get_file_metadata_value('PlatformName')
        PlatformName2.append(PlatformName)     

        SourceID = aux.get_file_metadata_value('SourceID')
        Source_id2.append(SourceID) 
        
        wrs_path = aux.get_file_metadata_value('WRS_PATH')
        wrs_path2.append(wrs_path)

        wrs_row = aux.get_file_metadata_value('WRS_ROW')
        wrs_row2.append(wrs_row)

        count = count  +1

for ii in Acquisition_DateTime2:   
    a=ii.replace("-","")
    b=a.replace(":","")
    Acquisition_DateTime3.append(b[:8]) 

# ------------------------------------------------------------------------------------------------------
#D) Build ouput filename based on user choice 
# ------------------------------------------------------------------------------------------------------

output_file_name=[]

if output_filename_format == 1:    # Source ID
    for ii in Landsat_product_id2:
        temp = prefix + ii
        output_file_name.append(temp)

elif output_filename_format == 3: # prefix + Acquisition_DateTime3 + PlatformName2 + WRS_PATH + WRS_ROW + ".pix" 
    for ii, jj, kk, ll in zip (Acquisition_DateTime3, PlatformName2, wrs_path2, wrs_row2):        
        temp = prefix + ii + "_" + jj + "_path" + kk  + "_row" + ll
        output_file_name.append(temp)

elif output_filename_format == 4:  # prefix + Acquisition_DateTime3 + Source_ID
    for ii, jj in zip(Acquisition_DateTime3, Source_id2):
        temp = prefix + ii + "_" + jj
        output_file_name.append(temp)
else:
    print ("Error! - choose another value")
    sys.exit()
    
# ------------------------------------------------------------------------------------------------------
#E) SARINGESTAOI
#   Ingest the files stored in the MFILE , use the acquisition date to name the files.
# ------------------------------------------------------------------------------------------------------

print ("------------------------------------------------------------------------------------------")
print ("                     Landsat scenes ingestion using FIMPORT                               ")
print ("------------------------------------------------------------------------------------------")
out_MS_list = []
out_MS_list2 = []   # Only for the scenes with a panchromatric band
out_PAN_list = []

count=1
for scene, outname, pfname in zip(newpaths_list, output_file_name, PlatformName2):

    outname_path = os.path.join(output_folder, outname)
    print ("\t")
    print ((time.strftime("%H:%M:%S"))+" Ingesting file "+str(count)+" of "+str(len(file_ingest_list))+"...")
    print ("   Ingesting-->" + scene)

    if import_MS or import_MS_Thermal is True:
        fili = scene + import_type
        filo = outname_path + suffix_out
        filo_ms_temp = filo
        print ("   Importing the MS file-->:" + filo)
        
        dbiw = []
        poption = "AVER"
        dblayout = "TILED"

        try:
            fimport(fili, filo, dbiw, poption, dblayout)
        except PCIException as e:
            print (e)
        except Exception as e:
            print (e)
        out_MS_list.append(filo)            

    if import_PAN is True:

        if pfname in ["Landsat-8","Landsat-9"]:
            print ("   Panchromatic band ingestion")
            fili = scene + "?t=PAN"
            filo = outname_path + "_PAN.pix"
            print ("   Importing the PAN file-->:" + filo)
            try:
                fimport(fili, filo, dbiw, poption, dblayout)
            except PCIException as e:
                print (e)
            except Exception as e:
                print (e)
            out_PAN_list.append (filo)
            out_MS_list2.append (filo_ms_temp)

    count = count+1


if perform_clip is True :

    print ("\t")
    print ("-------------------------------------------------------------------------------------")
    print ("                                  Image clipping                                     ")
    print ("-------------------------------------------------------------------------------------")
    print ("\t")

    file_to_process = out_MS_list + out_PAN_list

    nb_clip = str(len(file_to_process))
    count = 1
    for ii in file_to_process:
        
        print ("\t")      
        print ((time.strftime("%H:%M:%S"))+ " Clipping file "+ str(count)+" of "+ nb_clip + "...")
        print ("  Input file -->" + ii)
        fili = ii

        with ds.open_dataset(ii) as ds2:
            chans = ds2.chan_count

        dbic = [1,-chans]
        dbsl = []
        sltype = ""

        outnane = os.path.basename (ii)
        outname_filo = "s" + outnane
        
        filo = os.path.join (output_folder, outname_filo)
        print ("  Output_file -->" + filo)

        ftype = "PIX"
        foptions = ""
        clipmeth = "LAYERVEC"
        clipfil = clip_layer_AOI
        cliplay = [2]
        laybnds = "EXTENTS"
        coordtyp = ""
        clipul = ""
        cliplr = ""
        clipwh = ""
        initvalu = [0]
        setnodat = "Y";
        oclipbdy = "N"
        try:
            clip (fili, dbic, dbsl, sltype, filo, ftype, \
            foptions, clipmeth, clipfil, cliplay, \
            laybnds, coordtyp, clipul, cliplr, \
            clipwh, initvalu, setnodat, oclipbdy )
        except PCIException as e:
            print (e)
        except Exception as e:
            print (e)  

        if delete_original_after_clipping is True:
            print("  Deleting original  input file")
            os.remove(ii)

        count = count + 1
print("---------------------------------------------------------------------------------------------------------")
print("---------------------------------------------------------------------------------------------------------")
print ((time.strftime("%H:%M:%S")))
print ("All processing completed")
print ("\t")
end = time.time()

ellapse_time_seconds = round((end - start),2)
ellapse_time_minutes = round((ellapse_time_seconds/60),2)
ellapse_time_hours = round((ellapse_time_seconds/3600),2)

print ("Processing time (seconds): " + str(ellapse_time_seconds))
print ("Processing time (minutes): " + str(ellapse_time_minutes))
print ("Processing time (hours): " + str(ellapse_time_hours))
print ("\t")
