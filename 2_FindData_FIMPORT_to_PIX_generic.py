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

from pci.api import datasource as ds
from pci.exceptions import PCIException

from pci.fimport import fimport
#-----------------------------------------------------------------------------------------------------
#  Discover candidate files inside a folder, ingest the files, create a MFILE and run INSINFO
#-----------------------------------------------------------------------------------------------------
'''
definition)

    1) Description
    Based on a keyword (keyword), this script search for all candidate image inside a user specified folder (input_dir) and then
    import those images into a pix file. The new file names are base on their acquisition dates (retrieved from the file metadata). 
  
    An MFILE is created from the discovered files and used by INSINFO to fing the suitable Interferometric pairs candidates. 
    Detected and/or non overlapping images that match the specified keyword will be included in the MFILE.

    2) Keywords. 
        Sentinel 2= "manifest.safe"
        

     3) DBIW      [Xoffset, Yoffset, Xsize, Ysize]
        DBIW_in=[]    // Will ingest the whole file
        
     4) Prefix : Complete the description
                 
'''

#----------------------------------------------------------------------------------------------
#  Variables to set
#----------------------------------------------------------------------------------------------

keyword = "*.tif"

input_dir = r"F:\Air_Photos\BeaverAOI1"
output_dir = r"F:\Air_Photos\BeaverAOI1"
prefix = ""



#----------------------------------------------------------------------------------------------
#  Program
#----------------------------------------------------------------------------------------------
start = time.time()

VendorInput_List=[]
VendorInput_listPath_open=[]
VendorInput_listPath=[]

# Create the output directory if it doesn't already exist
if not os.path.exists(output_dir):  
    os.makedirs(output_dir)

## SEEK FOR FILES AND FILE METADATA RETRIEVAL   
# Search inside the input directory and subdirectories for all files that match the keyword
for root, dirs, files in os.walk(input_dir):
    for filename in fnmatch.filter(files, keyword):
        VendorInput_List.append (filename)
        VendorInput_listPath.append(os.path.join(root,filename))

	   
	   
print ("Number of discovered files using <"+ keyword+ "> for keyword: " + str(len (VendorInput_listPath))) 

print ("------------------------------------------------------------------------------------------")
print ("\t")


file=open(os.path.join(output_dir, prefix+"_MFILE_DiscoveredFiles.txt"), "w")  
file.write('\n'.join(VendorInput_listPath))
file.close()  

    
print ("--------------------------  Importing the files to PIX------------------------------------")
print ("------------------------------------------------------------------------------------------")
IngestedFilesPath=[]

tot_image = str(len(VendorInput_listPath))

count = 1
for input_image in VendorInput_listPath:
    
    print ((time.strftime("%H:%M:%S")) + "...Ingesting file " + str(count) + " of " + tot_image )
    fili= input_image
    outname = os.path.basename (input_image[:-4])
    print (fili)
    filo = os.path.join(output_dir,prefix + outname + ".pix")
    dbiw = []
    poption = 'AVER'
    dblayout = 'tiled256'

    
    try:
        fimport(fili, filo, dbiw, poption, dblayout)
    except PCIException as e:
        print(e)
    except Exception as e:
        print(e)  
    
    count=count+1
    print ('\t')


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
