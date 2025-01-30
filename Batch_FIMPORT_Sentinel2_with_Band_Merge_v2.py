#!/usr/bin/env python

# ----------------------------------------------------------------------
# - Copyright (c) 2021.  All rights reserved.                          -
# - PCI Geomatics, 90 Allstate Parkway, Markham, Ontario, Canada.      -
# - Not to be used, reproduced or disclosed without permission.        -
# ----------------------------------------------------------------------

# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale
locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")


import os
import glob
import fnmatch
import sys
import time
import datetime
import pathlib
import shutil

from pci.api import datasource as ds
from pci.exceptions import PCIException

from pci.fimport import fimport
from pci.clip  import clip
from pci.resamp import resamp
from pci.pcimod import pcimod
from pci.iii import iii
from pci.pyramid import pyramid
#-----------------------------------------------------------------------------------------------------
#  Discover candidate files inside a folder, ingest the files, create a MFILE and run INSINFO
#-----------------------------------------------------------------------------------------------------
'''
** Extracted metadata   -----> example
** Acquisition_DateTime -----> 2019-05-06T16:00:21.088184Z
    date_compact    -----> 20190506
    date_unique      -----> 20190506_160021088184Z
** PlatformName         -----> Sentinel-2
    pname_compact    -----> S2
** PROCESSING_LEVEL    -----> Level-1C
      pl_compact     - ----> L1C
** SourceID            -----> S2A_MSIL1C_20190506T154911_N0207_R054_T18TXS_20190506T210337

**SPACECRAFT_NAME    - ----> Sentinel-2A


output_name_format
1 :  prefix + SourceID    prefix_S2A_MSIL1C_20190506T154911_N0207_R054_T18TXS_20190506T210337
2 :  prefix + pname_compact + date_unique + pl_compact

'''

#----------------------------------------------------------------------------------------------
#  Variables to set
#----------------------------------------------------------------------------------------------
input_folder = r"D:\LSTP_CP_QP_data\Sentinel-2\unpack"
keyword = "manifest.safe"


output_folder = r"D:\LSTP_CP_QP_data\Sentinel-2\merged"
prefix = "LSTP_"
output_filename_format = 2

# Valid inputs  "yes"  or "no"
import_10m_bands="y"
import_20m_bands="y"
import_60m_bands="no"

perform_clip = "yes"
clip_layer_AOI = r"D:\WP98_Ancillary\LSTP_clip_layer_UTM18T_D000.pix"

Merge_20m_bands_to_10m_bands = "yes"


#----------------------------------------------------------------------------------------------
#  Program
#----------------------------------------------------------------------------------------------
start = time.time()

VendorInput_List=[]
VendorInput_listPath=[]

#----------------------------------------------------------------------------------------------
# A)  SEEK FOR FILES
#     Search inside the input directory and subdirectories for all files that match the keyword
for root, dirs, files in os.walk(input_folder):
    for filename in fnmatch.filter(files, keyword):
        VendorInput_List.append (filename)
        VendorInput_listPath.append(os.path.join(root,filename))


#----------------------------------------------------------------------------------------------
# B)  EARLY VALIDATION
if  len (VendorInput_listPath) == 0:
    print ("Error ! - No files found, please select a different keyword of check the input folder")
    sys.exit ()

else:
    print ("Number of discovered files using <"+ keyword+ "> for keyword: " + str(len (VendorInput_listPath))) 
    print ("\t")

yes_list = ["yes","y","yy", "yse"]
if import_10m_bands.lower() in yes_list:
    import_10m = True
else:
    import_10m = False
    
if import_20m_bands.lower() in yes_list:
    import_20m = True
else:
    import_20m = False

if import_60m_bands.lower() in yes_list:
    import_60m = True
else:
    import_60m = False
	   
if import_10m is False and import_20m is False and import_60m is False:
    print ("Error! - At least one band groups (10, 20 or 60m) must be set to yes")
    sys.exit()

if Merge_20m_bands_to_10m_bands in yes_list:
    merge_10_20 = True
else:
    merge_10_20 = False

if merge_10_20 is True and import_10m is False:
    print ("Error! - The 10m bands must be set to yes when Merge_20m_bands_to_10m_bands is set to yes")
    sys.exit()
if merge_10_20 is True and import_20m is False:
    print ("Error! - The 20m bands must be set to yes when Merge_20m_bands_to_10m_bands is set to yes")
    sys.exit()

if perform_clip.lower() in yes_list: 
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




# Create the output directory if it doesn't already exist
if not os.path.exists(output_folder):  
    os.makedirs(output_folder)


file=open(os.path.join(output_folder, prefix + "_MFILE_DiscoveredFiles.txt"), "w")  
file.write('\n'.join(VendorInput_listPath))
file.close()  

#----------------------------------------------------------------------------------------------
# C) File metadata retrieval 

Acquisition_DateTime2 =[]
PlatformName2 = []
Processing_level2 = []
SourceID2=[]
 
for ii in VendorInput_listPath:
    with ds.open_dataset(ii + ":Band Resolution:10m",ds.eAM_READ) as ds2:
        aux = ds2.aux_data

        Acquisition_DateTime = aux.get_file_metadata_value('Acquisition_DateTime')
        Acquisition_DateTime2.append(Acquisition_DateTime)

        PlatformName = aux.get_file_metadata_value('PlatformName')
        if PlatformName == "Sentinel-2":
            pname = "S2"
        else:
            pname = PlatformName
        PlatformName2.append(pname)

        Processing_level = aux.get_file_metadata_value('PROCESSING_LEVEL')
        if Processing_level == "Level-1C":
            plevel = "L1C"
        elif Processing_level == "Level-2A":
            plevel = "L2A"
        else: 
            plevel = Processing_level
        Processing_level2.append(plevel)
            
        SourceID=aux.get_file_metadata_value('SourceID')
        SourceID2.append(SourceID)
    
# C.2) Date time formatting   
date_time_compact = []
date_time_unique = []  # necessary for scenes on the same swath. 
string_replace = str.maketrans({'-': '', ':': '', 'T': '_', '.': '', 'Z': ''})

for ii in Acquisition_DateTime2:   
    output_string = ii.translate(string_replace)
    date_time_compact.append(output_string[:8])
    date_time_unique.append (output_string)


# C.4) Output filename formatting
output_file_name = []

if output_filename_format == 1:
    for ii in SourceID2:
        temp = prefix + ii
        output_file_name.append(temp)
elif output_filename_format == 2:
    for ii, jj, ll in zip(PlatformName2, date_time_unique, Processing_level2 ):
        temp = prefix + ii + "_" + jj + "_" +  ll
        output_file_name.append(temp)


# Create a list of files to ingest with the selected band groups (10, 20 and 60m).
files_to_ingest = []
out_filename2 = []  

for ii,jj in zip(VendorInput_listPath, output_file_name):
    if import_10m is True:
        temp10 = ii + ":Band Resolution:10M"
        files_to_ingest.append(temp10)
        outname = os.path.join(output_folder, jj + "_10m.pix")
        out_filename2.append(outname)
        
    if import_20m is True:
        temp20 = ii + ":Band Resolution:20M"
        files_to_ingest.append(temp20)
        outname = os.path.join(output_folder,jj + "_20m.pix")
        out_filename2.append(outname)
        
    if import_60m is True:
        temp60 = ii + ":Band Resolution:60M"
        files_to_ingest.append(temp60)
        outname = os.path.join(output_folder, jj + "_60m.pix")
        out_filename2.append(outname)

for ii, jj in zip(files_to_ingest,out_filename2) :
    print (ii)
    print (jj)
    print ("\t")


print ("------------------------------------------------------------------------------------------")
print ("                     Sentinel-2 scenes ingestion using FIMPORT                            ")
print ("------------------------------------------------------------------------------------------")
IngestedFilesPath=[]

count = 1

nb_files = str (len(files_to_ingest))

for ii, jj in zip(files_to_ingest, out_filename2):
    print ( time.strftime("%H:%M:%S") + " Importing file " + str(count) + " of " + nb_files )
    print ("   file input -->" +  ii)
    print ("   file output-->" + jj )
    print ("\t")   
    fili = ii
    filo = jj
    dbiw = []
    poption = 'AVER'
    dblayout = 'band'

    try:
        fimport(fili, filo, dbiw, poption, dblayout)
        IngestedFilesPath.append(filo)
    except PCIException as e:
        print(e)
    except Exception as e:
        print(e)  
    count=count+1


if perform_clip is True :

    print ("\t")
    print ("-------------------------------------------------------------------------------------")
    print ("                                  Image clipping                                      ")
    print ("-------------------------------------------------------------------------------------")
    print ("\t")

    nb_clip = str(len(IngestedFilesPath))
    count = 1
    outclip_files = []
    for ii in IngestedFilesPath:
        
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

            outclip_files.append(filo)
        except PCIException as e:
            print (e)
        except Exception as e:
            print (e)  
        count = count + 1


    # Deleting the full scenes after clipping. 
    print ("\t")
    print ("Deleting the full scenes")
    for ii in IngestedFilesPath: 
        os.remove(ii)

if merge_10_20 is True: 

    print ("\t")
    print ("--------------------------------------------------------------------")
    print ("                    Spectral bands merging                          ")
    print ("--------------------------------------------------------------------")


    # Find first all 10m files. This part of the script is based on a
    # strict naming convention. 
    find_10m_bands = []

    for root, dirs, files in os.walk(output_folder):
        for filename in fnmatch.filter(files, "*_10m.pix"):
            find_10m_bands.append(os.path.join(root,filename))

    print ("\t")
    print ("Number of files to process: " + str(len(find_10m_bands)))
    print ("\t")

    count=1
    for ii in find_10m_bands:
        
        print ("\t")
        print ((time.strftime("%H:%M:%S"))+" Processing file "+str(count)+" of "+str(len(find_10m_bands))+"...")
        print ("Creating a copy of " + ii)

        OutFile = os.path.basename(ii)
        OutFileM = "merged_"+OutFile
        OutFilePath = os.path.join (output_folder,OutFileM)
        shutil.copy2(ii, OutFilePath)
        
        # find the corresponding 20m file
        TempName = os.path.basename(ii)
        TempName20m = TempName.replace("10m.pix","20m.pix")
        #print TempName20m
        
        # Resampling the 20m file to 10m 
        print("Resampling 20m bands to 10m")
        fili = os.path.join(output_folder, TempName20m)
        dbic = [1,2,3,4,5,6]
        dbsl = []
        sltype=	"ALL"
        
        base = os.path.basename(ii[:-4])
        filo = os.path.join(output_folder,base+"_resamp10m.pix")
        
        ftype = "PIX"
        foptions = ' '
        pxszout = [10,10]	# output with a 10 meter resolution
        resample = "near"	# Cubic Convolution method

        try:
            resamp(fili, dbic, dbsl, sltype, filo, ftype, foptions, pxszout, resample)
            resamp20m = filo
        except PCIException as e:
            print(e)
        except Exception as e:
            print(e)  
            
        # Transfer all resampled 20m bands into the copy of the 10m bands file
        # A) Add six empty 32R channels to merged_*
        file = os.path.join (output_folder,OutFileM)
        print ("Transfering 20m resampled spectral bands to the 10m bands")
        
        pciop = "add"
        pcival = [0,0,0,6,0,0]
           
        try:
            pcimod(file,pciop,pcival)
        except PCIException as e:
            print(e)
        except Exception as e:
            print(e)     
        
        # B) Transfer the resampled 20m to 10m into the 10m pix file
        fili = resamp20m	
        filo = os.path.join (output_folder,OutFileM)	# larger file in which to perform composite
        dbic = [1,2,3,4,5,6]	# image channel 1
        dboc = [5,6,7,8,9,10]	# image output to channel 1 in composite
        dbiw = []	# use full image
        dbow = []	# position image at 0x0 and 256x256 for lower-right corner
            
        try:
            iii(fili, filo, dbic, dboc, dbiw, dbow)
            pyramid(file=filo, force='yes', poption='aver', dboc=[], olevels=[])
            count=count+1
        except PCIException as e:
            print(e)
        except Exception as e:
            print(e)  
            

print("--------------------------------------------------------------")
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
print ("\t")
input('Press ENTER to exit')
