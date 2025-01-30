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

from pci.psiqinterp import psiqinterp
from pci.pyramid import pyramid
from pci.api import datasource as ds
from pci.exceptions import *

# -----------------------------------------------------------------------------------------------------
#  Discover candidate files inside a folder, ingest the files, create a MFILE and run INSINFO
# -----------------------------------------------------------------------------------------------------
'''
definition)

'''

# ----------------------------------------------------------------------------------------------
#  User defined variables
# ----------------------------------------------------------------------------------------------

## Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
Input_mode = 2

Input_mode_1_MFILE = r"G:\test_ecclipse\dddddd.txt"
Input_mode_2_Search_Folder = r"G:\test_ecclipse"
Input_mode_2_keyword = "*.jpg"

# ---------------------------------------------------------------------------------------------
#  Program
# ----------------------------------------------------------------------------------------------

# Create output file if not already existing


# -----------------------------------------------------------------------------------------
# A.1) Find all data to ingest
file_rename_list = []
if Input_mode == 1:  # Read an Existing MFILE and create a list of file to process

    with open(Input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line = line.strip()
            file_rename_list.append(line)

elif Input_mode == 2:  # Search folder with a keyword

    for root, dirs, files in os.walk(Input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, Input_mode_2_keyword):
            file_rename_list.append(os.path.join(root, filename))
else:
    print("Error- Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()

# For Input_mode==2,   verify if at least one file was found.  
if len(file_rename_list) == 0:
    print("\t")
    print("Error- no files found")
    print("Specify another keyword or search folder")
    sys.exit()

count = 1
for ii in file_rename_list:
    print("Renaming file " + str(count) + " of " + str(len(file_rename_list)))
    tempname = os.path.basename(ii[:-4])
    temppath = os.path.dirname(ii)

    new_file = (tempname + "_ek5.jpg")

    new_file_out = os.path.join(temppath, new_file)

    os.rename(ii, new_file_out)
    count = count + 1

print("\t")
print("----------------------------------------------------------------------")
