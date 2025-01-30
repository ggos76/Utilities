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

from pci.reproj import reproj
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

Input_mode_1_MFILE = r"F:\Air_Photos\georep_sourcess"
Input_mode_2_Search_Folder = r"F:\Air_Photos\georep_sources"
Input_mode_2_keyword = "*geo.tif"

prefix = ""
output_folder =  r"F:\Air_Photos\georep_sources\canmatrix_utm15VD000"
output_projection ="UTM 15V D000"
override_resolution = "yes"        # Valid key = "yes" or "no"
res_xy= [4.23,4.23]


# ---------------------------------------------------------------------------------------------
#  Main program
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
# A ) Find all data to ingest
file_reproj_list = []
if Input_mode == 1:  # Read an Existing MFILE and create a list of file to process

    with open(Input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line = line.strip()
            file_reproj_list.append(line)

elif Input_mode == 2:  # Search folder with a keyword

    for root, dirs, files in os.walk(Input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, Input_mode_2_keyword):
            file_reproj_list.append(os.path.join(root, filename))
else:
    print("Error- Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()

# For Input_mode==2,   verify if at least one file was found.  
if len(file_reproj_list) == 0:
    print("\t")
    print("Error- no files found")
    print("Specify another keyword or search folder")
    sys.exit()

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# ----------------------------------------------------------------------------------------------
# B) - File reprojection and exporting to the PIX file format

count = 1
for ii in file_reproj_list:

    with ds.open_dataset(ii) as ds1:
        file_mapunits = crs_to_mapunits(ds1.crs)
        file_proj = file_mapunits.replace(" ", "")
        file_res = ds1.geocoding.resolution

    out_proj_test = output_projection.replace(" ", "")

    if file_proj != out_proj_test:
        print((time.strftime("%H:%M:%S")) +" Reprojecting file " + str(count) + " of " + str(len(file_reproj_list)))
        print (" File input --> " + ii )
        print (" Original projection: " + file_mapunits)
        print (" New projection: " + output_projection)
        fili = ii
        dbic = [1]
        dbsl = []
        sltype  =   ""

        outname = os.path.basename(ii[:-4])

        filo    =  os.path.join (output_folder, prefix + outname + ".pix")
        print (" File output --> " + filo)
        ftype   =   ""  # uses PIX format by default
        foptions    =   ""  # no file options are used
        repmeth =   "BR"  # uses bounds and resolution method
        dbsz    =   []  # not used for BR method
        pxsz    =   res_xy
        maxbnds =   "YES"    # uses maximum bounds
        mapunits    =   output_projection
        llbounds    =   "NO"
        ulx =   ""
        uly =   ""
        lrx =   ""
        lry =   ""
        resample    =   "CUBIC"  # uses CUBIC resample
        proc    =   ""  # uses AUTO by default
        tipostrn    =   "CORNER,10" # uses CORNER tile positioning transformation with 10 meter stride

        reproj( fili, dbic, dbsl, sltype, filo, ftype, \
        foptions, repmeth, dbsz, pxsz, maxbnds,\
        mapunits, llbounds, ulx, uly, lrx, \
        lry, resample, proc, tipostrn )

        pyramid(file=filo, force='yes', poption='aver', dboc=[], olevels=[])

    else:
        print (" File already in the output projection, skip")

    count = count + 1
    print ("\t")

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
string1 = "10-Total proc time;" + str(ellapse_time_seconds)
