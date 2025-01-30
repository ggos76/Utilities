#!/usr/bin/env python
'''----------------------------------------------------------------------
 * - Copyright (c) 2023.  All rights reserved.                          -

 * ----------------------------------------------------------------------
'''

# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale

locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")

import os, glob, fnmatch, sys, time

from pci.desatur import desatur
from pci.pyramid import pyramid
from pci.api import datasource as ds
from pci.api.cts import crs_to_mapunits

from pci.exceptions import *

start = time.time()
# -----------------------------------------------------------------------------------------------------
#  Batch script for reprojecting data from different sources to the same projection
# -----------------------------------------------------------------------------------------------------
'''
definition)

'''

# ----------------------------------------------------------------------------------------------
#  User defined variables
# ----------------------------------------------------------------------------------------------

## Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
Input_mode = 2

Input_mode_1_MFILE = r""
Input_mode_2_Search_Folder = r"F:\Air_Photos\geocoded_075_sinx\original"
Input_mode_2_keyword = "*.pix"

prefix = "d"
output_folder =  r"F:\Air_Photos\geocoded_075_sinx\desatur"

# ---------------------------------------------------------------------------------------------
#  Main program
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
# A ) Find all data to ingest
file_desatur_list = []
if Input_mode == 1:  # Read an Existing MFILE and create a list of file to process

    with open(Input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line = line.strip()
            file_desatur_list.append(line)

elif Input_mode == 2:  # Search folder with a keyword

    for root, dirs, files in os.walk(Input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, Input_mode_2_keyword):
            file_desatur_list.append(os.path.join(root, filename))
else:
    print("Error- Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()

# For Input_mode==2,   verify if at least one file was found.  
if len(file_desatur_list) == 0:
    print("\t")
    print("Error- no files found")
    print("Specify another keyword or search folder")
    sys.exit()

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# ----------------------------------------------------------------------------------------------
# B) - File desaturating

count = 1
for ii in file_desatur_list:

    print((time.strftime("%H:%M:%S")) +" Desaturating file " + str(count) + " of " + str(len(file_desatur_list)))
    print (" File input --> " + ii )
    filref   = ii
    fili     = ii
    dbic     = []
    desatamt = [50]
    desatper = [50]
    desatopt = ""

    out_basename = os.path.basename (ii)
    filo     = os.path.join (output_folder, prefix + out_basename)
    print (" File output --> " + filo )
    print ("\t")
    ftype    = ""
    foptions = ""


    desatur(filref, fili, dbic, desatamt, desatper, desatopt, filo, ftype, foptions)
    pyramid(file=filo, force='yes', poption='aver', dboc=[], olevels=[])
    
    count = count + 1



print ("\t")
print("--------------------------------------------------------------------------------------------------------------")
print ("\t")
print((time.strftime("%H:%M:%S")))
print("All processing completed")
print("\t")
end = time.time()

ellapse_time_seconds = round((end - start), 2)
ellapse_time_minutes = round((ellapse_time_seconds / 60), 2)
ellapse_time_hours = round((ellapse_time_seconds / 3600), 2)

print("Processing time (seconds): " + str(ellapse_time_seconds))
print("Processing time (minutes): " + str(ellapse_time_minutes))
print("Processing time (hours): " + str(ellapse_time_hours))

