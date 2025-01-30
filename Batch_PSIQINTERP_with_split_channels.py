#!/usr/bin/env python

'''
----------------------------------------------------------------------------------------------------------
Batch script for converting complex (SLC, MLC) to detected data (amplitude, intensity,decibels).
----------------------------------------------------------------------------------------------------------
'''

# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale
locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")

import os, glob, fnmatch, sys, time

from pci.psiqinterp import psiqinterp
from pci.pyramid import pyramid
from pci.exceptions import *

start = time.time()

# ----------------------------------------------------------------------------------------------
#  User defined variables
# ----------------------------------------------------------------------------------------------
# Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
Input_mode = 2

Input_mode_1_MFILE = r""
Input_mode_2_Search_Folder = r"D:\WP98_Results\test_psiqinterp\in"
Input_mode_2_keyword = "*.pix"

interpretation_type = "Int"
split_channels = "yes"   # Valid options "yes" or "no"
input_channels = [1,2,3,4]
output_chan_description= ["HH","HV","VH", "VV"] # mandatory if split_channels = "yes"


prefix = "test1"
output_folder =  r"D:\WP98_Results\test_psiqinterp\out"


'''
"------------------------------------------------------------------------------------------------------
 Specifications
"------------------------------------------------------------------------------------------------------
A.1) The interpretation type. You can enter either the short or long form of the following values:

Int or Intensity: Intensity 
Amp or Amplitude: Amplitude 
dB or Decibel: Decibel 


'''
# ---------------------------------------------------------------------------------------------
# A) Quick Validation
# ----------------------------------------------------------------------------------------------
if interpretation_type.lower() in ["int","intensity"]:
    cinterp_type = "intensity"
elif interpretation_type.lower() in ["amp","amplitude"]:
    cinterp_type = "amplitude"
elif interpretation_type.lower() in ["db","decibel"]:
    cinterp_type = "decibel"
else:
    print ("Error - the interpretation_type option is not valid")
    print ("Entered value: " + interpretation_type )
    sys.exit()

if split_channels.lower() in ["y","yes","ys","yse"]:
    split_chan = True
    print("Split channels option is True")
    if input_channels == 1:
        print("Error - The number of input channels must be greater than 1 when the split channels option is selected")
        sys.exit()
    if len(input_channels) != len(output_chan_description):
        print("Number of input channels: " + str (len(input_channels)))
        print("Number of channels descriptions: " + str(len(output_chan_description)))
        print("Error - the number of input channels must be equal to the number of output channel descriptions")
        sys.exit()

    for test_int, test_str in zip (input_channels,output_chan_description) :
        if type (test_int) != int:
            print ("Error - All channels in input_channels must be integer")
            sys.exit()
        if type (test_str) != str:
            print ("Error - All output channels description must be strings")
            sys.exit()
else :
    split_chan = False
    print("Split channels option is False")

# ---------------------------------------------------------------------------------------------
# B) Data Ingestion and metadata extraction
# ----------------------------------------------------------------------------------------------
start = time.time()

file_psiqinterp_list = []
if Input_mode == 1:  # Read an Existing MFILE and create a list of file to process

    with open(Input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line = line.strip()
            file_psiqinterp_list.append(line)

elif Input_mode == 2:  # Search folder with a keyword

    for root, dirs, files in os.walk(Input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, Input_mode_2_keyword):
            file_psiqinterp_list.append(os.path.join(root, filename))
else:
    print("Error- Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()

# For Input_mode==2,   verify if at least one file was found.
if len(file_psiqinterp_list) == 0:
    print("\t")
    print("Error- no files found")
    print("Specify another keyword or search folder")
    sys.exit()

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

num_files = str (len(file_psiqinterp_list))
print((time.strftime("%H:%M:%S")) + num_files + " files have been found")

# ---------------------------------------------------------------------------------------------
# C)  Main program
# ----------------------------------------------------------------------------------------------

count = 1
for ii in file_psiqinterp_list:
    print ("\t")
    out_basename = os.path.basename (prefix + ii[:-4])
    print((time.strftime("%H:%M:%S")) +" Converting file " + str(count) + " of " + num_files +
                            " to " + cinterp_type)
    print ("   File input --> " + ii )

    if split_chan is True:
        chan_count = 1
        for in_chan in input_channels:
            print ("   Processing channel " + str (chan_count) + " of " + str(len(input_channels)))
            fili = ii
            dbic = [input_channels[in_chan-1]]
            cinterp = cinterp_type
            dboc = []
            out_basename2 = (out_basename + "_"+ cinterp_type +"_"+ output_chan_description[in_chan-1] + ".pix")
            filo = os.path.join (output_folder, out_basename2)
            ftype = "PIX"
            foptions = ""

            psiqinterp(fili, dbic, cinterp, dboc, filo, ftype, foptions)
            print("    Generating the overviews")
            pyramid(file=filo, force='yes', poption='aver', dboc=[], olevels=[])
            chan_count = chan_count + 1

    if split_chan is False:
        fili = ii
        dbic = input_channels
        cinterp = cinterp_type
        dboc = []
        out_basename2 = (out_basename + "_" + cinterp_type + ".pix")
        filo = os.path.join(output_folder, out_basename2)
        print("   File output --> " + filo)
        ftype = "PIX"
        foptions = ""

        psiqinterp(fili, dbic, cinterp, dboc, filo, ftype, foptions)
        print("    Generating the overviews")
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

