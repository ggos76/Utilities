#!/usr/bin/env python

'''
----------------------------------------------------------------------------------------------
Batch script for mosaicking a series of images based on the acquisition date or an inpout
text file.
----------------------------------------------------------------------------------------------
'''

# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale
locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")

import os
import fnmatch
import sys
import time

from pci.api import datasource as ds
from pci.exceptions import PCIException
from pci.api.cts import crs_to_mapunits
from pci.reproj import reproj
from pci.mosprep import mosprep
from pci.mosdef import mosdef
from pci.mosrun import mosrun
from pci.pyramid import pyramid

# -------------------------------------------------------------------------------------------------
#  User defined variables
# -------------------------------------------------------------------------------------------------
# Input mode - Valid options are 1 (MFILE) or 2 (Search subfolders + keyword)

input_mode = 2
input_mode1_mfile = r""

input_folder = r"E:\WP98_Results\Sentinel-1\2019_ASC\orthos\A"
search_keyword = "*.pix"
exclusion_list = ["footprint", "S1A"]    # Leave blank [] for no exclusion.

Output_mosaic_basename = "RS2mos_"
Output_mosaic_channels = [1,2]
Output_resolution_X_Y = [8, 8]

Output_projection = "UTM 18T D000"  # Be careful here with typos
NoDataValue = [-32768.00000]
output_folder = r"E:\WP98_Results\Sentinel-1\2019_ASC\orthos\A"


'''
"------------------------------------------------------------------------------------------------------
 Specifications
"------------------------------------------------------------------------------------------------------
All input scenes belonging to the same mosaic (as defined by a list of a subfolder) must share the same 
projection. The script will error otherwise. 

'''

#----------------------------------------------------------------------------
# Data search and lists creation
#---------------------------------------------------------------------------
start = time.time()
Output_projection_no_space = Output_projection.replace(" ","")
Output_projection_no_space.strip()
def conformity_reproject (input_file):

    with ds.open_dataset(input_file) as ds1:
        image_projection = crs_to_mapunits(ds1.crs)
        col = ds1.width
        row = ds1.height

    image_projection_clean = image_projection.replace(" ", "")
    image_projection_clean.strip()
    if image_projection_clean != Output_projection_no_space:
        print ("Input image projection: " + image_projection_clean)
        print ("Target projection: " + Output_projection_no_space)
        print ("Input image projection is different than the target projection")
        print ("Input image reprojection")


        # File reprojection if necessary
        fili = input_file
        dbic = Output_mosaic_channels
        dbsl = []
        sltype = "all"

        basename_out = os.path.basename (input_file[:-4])
        outfolder = os.path.dirname(input_file)
        filo = os.path.join (outfolder, basename_out + "_reproj.pix")
        ftype = "PIX"
        foptions = ""
        repmeth = "BR"
        dbsz = [col, row]
        pxsz = Output_resolution_X_Y
        maxbnds = "yes"
        mapunits = Output_projection
        llbounds = "yes"
        ulx = ""  # Bounds of the area of interest
        uly = ""
        lrx = ""
        lry = ""
        resample = "near"
        proc = ""

        try:
            reproj(fili, dbic, dbsl, sltype, filo, ftype, \
                   foptions, repmeth, dbsz, pxsz, maxbnds, \
                   mapunits, llbounds, ulx, uly, lrx, \
                   lry, resample, proc)
        except PCIException as e:
            print(e)
        except Exception as e:
            print(e)
        tested_file = filo

    else :
        tested_file = input_file

    return (tested_file)


## SEARCH for inputs files

if input_mode == 1:  #Read an input mfile
    print ("Reading the mfile" + input_mode1_mfile)
    with open(input_mode_1_mfile, "r") as ins:
        for line in ins:
            line = line.strip()
            files_to_ortho_list.append(line)

if input_mode == 2: # Search inside the input directory and subdirectories for all files that match the keyword
    VendorInput_List = []
    VendorInput_ListPath = []
    root_list = []
    for root, dirs, files in os.walk(input_folder):
        for filename in fnmatch.filter(files, search_keyword):
            VendorInput_List.append(filename)
            VendorInput_ListPath.append(os.path.join(root, filename))
            root_list.append(root)

    # Create a list of subfolders by finding the unique roots
    unique_subfolders_list = []
    for ii in root_list:
        if ii not in unique_subfolders_list:
            unique_subfolders_list.append(ii)

sub_num = str(len(unique_subfolders_list))
print ("Number of found subfolders: " + sub_num)
print ("List of unique subfolders: ")
for ii in unique_subfolders_list:
    print (ii)


# ----------------------------------------------------------------------------------------------------------------
# Main program
# ----------------------------------------------------------------------------------------------------------------

# A) Searching for subsfolders withing in input folder and then create a list of pix files within each subfolders
#    for mosaicking.

count_sub = 1
for input_subfolfer in unique_subfolders_list:

    print ("\t")
    print ((time.strftime("%H:%M:%S") + "...Folder " + str(count_sub) + (" of ") + sub_num +" - checking content of "
            + input_subfolfer))

    if input_mode == 2:
        files_sub_list = []
        for root, dirs, files in os.walk(input_subfolfer):
            for filename in fnmatch.filter(files, search_keyword):
                files_sub_list.append(os.path.join(root, filename))

        print ("   Number of files found in " + input_subfolfer + ": " + str(len(files_sub_list)))


        # Remove files from the search if the file contains an item form the exclusion list.
        if len(exclusion_list) != 0:
            for x_del in exclusion_list:
                files_sub_list = [x for x in files_sub_list if x_del not in x]
            print ("    Number of files after exclusion: " + str(len(files_sub_list)))

        mfile_to_disk_list = []
        for input_file in files_sub_list:

            (tested_file) = conformity_reproject(input_file)
            mfile_to_disk_list.append (tested_file)
            print (tested_file)

        file = os.path.join(input_subfolfer, "MFILE_file_to_mosaic.txt")
        with open(file, "w") as f:
            f.write("\n".join(mfile_to_disk_list))

    count_sub = count_sub + 1

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

mosaic_total = str (len(unique_subfolders_list))
count_mosaic = 1
for input_subfolder in unique_subfolders_list:


    print ("\t")
    print ("----------------------------------------------------------------------------------------------------")
    print ((time.strftime("%H:%M:%S")) + "... Processing  mosaic " + str (count_mosaic) + " of " + mosaic_total)
    print ("----------------------------------------------------------------------------------------------------")

    # -------------------------------------------------------------------------------------------------------------
    #                                        MOSPREP (Mosaic preparation)
    # ------------------------------------------------------------------------------------------------------------

    print ("----------------------------------------------------------------------------------------------------")
    print ((time.strftime("%H:%M:%S")) + "...Step 1 - MOSPREP (Mosaic preperation)")
    print ("\t")

    unique_basename = os.path.basename (input_subfolder)
    output_subfolder = os.path.join (output_folder, unique_basename)

    if not os.path.exists(output_subfolder):
        os.makedirs(output_subfolder)

    mfile = os.path.join (input_subfolder, "MFILE_file_to_mosaic.txt")
    silfile = os.path.join (output_subfolder, unique_basename + "_project.mos")
    nodatval = NoDataValue
    sortmthd = ""
    normaliz = "none"
    balspec = "none"
    loclmask = ""
    globfile = ""
    globmask = []
    cutmthd = "MINSQDIFF"

    try:
        mosprep(  mfile, silfile, nodatval, sortmthd, normaliz,balspec, loclmask, globfile, globmask, cutmthd )
    except PCIException as e:
        print(e)
    except Exception as e:
        print(e)

    # -------------------------------------------------------------------------------------------------------------
    #                                      MOSDEF - Mosaic Definition
    # -------------------------------------------------------------------------------------------------------------
    print ("----------------------------------------------------------------------------------------------------")
    print ((time.strftime("%H:%M:%S")) + "...Step 2 - MOSDEF (Mosaic Definition)")
    print ("\t")


    mdfile = os.path.join(output_subfolder, unique_basename + "_mosdef.xml")
    dbic = Output_mosaic_channels
    tispec = ""
    tipostrn = ""
    mapunits = ""
    pxszout = Output_resolution_X_Y
    blend = [3]
    nodatval = NoDataValue
    ftype = "PIX"
    foptions = ""

    try:
        mosdef( silfile, mdfile, dbic, tispec, tipostrn, mapunits, pxszout, blend, nodatval, ftype, foptions )
    except PCIException as e:
        print(e)
    except Exception as e:
        print(e)

    # ------------------------------------------------------------------------------------------------------------
    #                            MOSRUN - Create a mosaic
    # ------------------------------------------------------------------------------------------------------------

    print ("----------------------------------------------------------------------------------------------------")
    print ((time.strftime("%H:%M:%S")) + "...Step 3 - MOSRUN (Create a mosaic)")
    print ("\t")

    outdir = output_subfolder	# output folder
    tilist = ""
    crsrcmap = "yes"
    extirule = ""
    delempti = ""
    proc = ""
    resample = ""

    try:
        mosrun(silfile, mdfile, outdir, tilist, crsrcmap, extirule, delempti, proc, resample )
    except PCIException as e:
        print(e)
    except Exception as e:
        print(e)

    for_pyramid_list = []
    for root, dirs, files in os.walk(output_subfolder):
        for filename in fnmatch.filter(files, "*mosdef_1_1.pix"):
            for_pyramid_list.append(os.path.join(root, filename))

    pyramid(file=for_pyramid_list[0], force='yes', poption='aver', dboc=[], olevels=[])

    count_mosaic = count_mosaic + 1

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



