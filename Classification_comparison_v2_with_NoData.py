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

from pci.api import datasource as ds
from pci.clip import clip
from pci.thr import thr
from pci.model import model
from pci.exceptions import *
from pci.exceptions import PCIException
import numpy as np


start = time.time()
# -----------------------------------------------------------------------------------------------------
#  Script to compare to compare two thematic classification.
# -----------------------------------------------------------------------------------------------------
'''
The aim of the script is to compare two thematic classifications by computing a frequency matrix. 
    1)	The unique values of the first classification (classif_layer_1) are found and stored in an array. 
    2)	The unique values of the second classification (classif_layer_2) are found and stored in an array.
    3)	For the first unique value of the classif_layer_1, the frequency of all unique values of the second 
         classification are computed. 
    4)	The result is stored in a text file.
    5)	Redo steps 3 and 4 for every unique value in the array of classif_layer_1
Requirements: 
    1) The two thematic classifications must be stored in the same pix file. 
    2) The two thematic classifications must be in 8 bit. 
    3) If remove_nodata = True , only the common area will be process

'''
# ----------------------------------------------------------------------------------------------
#  User defined variables
# ----------------------------------------------------------------------------------------------

## Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
input_file = r'D:\HBL_Palsas_classif\Database_merge.pix'
classif_layer_1 = 11
classif_layer_2 = 9

# available options are 'yes' or 'no'
apply_common_nodata = 'yes'
nodata_value = 0

# available options are 'yes' or 'no'
subset_data = 'no'
subset_vector_file = r"D:\HBL_Palsas_classif\clip_layer_test2.pix"
subset_segment = 2

output_file_name = "Palsa_classif_compare_full.txt"

delete_if_exist = True
# ---------------------------------------------------------------------------------------------
#  Main program
# ----------------------------------------------------------------------------------------------
#
yes_validation_list = ["yes", "y", "yse", "ys"]


# A ) Conformity  check
if apply_common_nodata.lower() in yes_validation_list:
    apply_common_nodata = True
else:
    apply_common_nodata = False

if subset_data.lower() in yes_validation_list:
    subset_data = True
    if not os.path.exists(subset_vector_file):
        print ("Error - The subset_vector_file does not exists or the path is wrong")
        sys.exit()
else:
    subset_data = False

# --------------------------------------------------------------------------------------------------------------------
#B)  Data preprocessing
# --------------------------------------------------------------------------------------------------------------------
print("\t")
output_line = ((time.strftime("%H:%M:%S")) + " Data preprocessing")
print (output_line)
output_line = ((time.strftime("%H:%M:%S")) + " Extracting the thematic layers form the main database (data_copy)")
print (output_line)

base = os.path.basename(input_file)
prefix = (output_file_name[:-4] + "_")
output_folder = os.path.dirname(input_file)
clip_out = os.path.join(output_folder, prefix + base)

fili = input_file
print (fili)
dbic = [classif_layer_1, classif_layer_2]
dbsl = []
sltype = ""
filo = clip_out
print (filo)
ftype = "PIX"
foptions = ""

if subset_data is True:
    print ("here_1")
    clipmeth = "LAYERVEC"
    clipfil = subset_vector_file
    cliplay = [subset_segment]
    laybnds = "SHAPES"
else:
    print ("here_2")
    clipmeth = "FILE"
    clipfil = input_file
    cliplay = [1]
    laybnds = "EXTENTS"

coordtyp = ""
clipul = ""
cliplr = ""
clipwh = ""
initvalu = [0]
setnodat = "Y"
oclipbdy = "N"

# check if filo exists
if os.path.exists(filo) == True and delete_if_exist == True:
    os.remove(filo)

try:
    clip(fili, dbic, dbsl, sltype, filo, ftype,
         foptions, clipmeth, clipfil, cliplay,
         laybnds, coordtyp, clipul, cliplr,
         clipwh, initvalu, setnodat, oclipbdy)
except PCIException as e:
    print(e)
except Exception as e:
    print(e)

input_file = filo

# -----------------------------------------------------------------------------------------------------------------------
# Quick check for the presence of NoData values for both channels:
with ds.open_dataset(filo) as ds5:
    reader = ds.BasicReader(ds5)
    # read the raster channels
    raster = reader.read_raster(0, 0, reader.width, reader.height)

    layer_1 = raster.data[:, :, (0)]
    layer_2 = raster.data[:, :, (1)]

    layer_1_rsp = layer_1.reshape(-1)
    layer_2_rsp = layer_2.reshape(-1)

    layer_1_nval = np.delete(layer_1_rsp, np.where(layer_1_rsp == nodata_value))
    layer_2_nval = np.delete(layer_2_rsp, np.where(layer_2_rsp == nodata_value))

    layer_1_nodata = len(layer_1_rsp) - len(layer_1_nval)
    layer_1_nval_pct = round((layer_1_nodata / (reader.width * reader.height)) * 100,2)
    layer_2_nodata = len(layer_2_rsp) - len(layer_2_nval)
    layer_2_nval_pct = round((layer_2_nodata / (reader.width * reader.height)) * 100,2)

    print ("Number of NoData values in layer 1 : " + str(layer_1_nodata) + " (" + str (layer_1_nval_pct) + "%)")
    print ("Number of NoData values in layer 2 : " + str(layer_2_nodata) + " (" + str (layer_2_nval_pct) + "%)")


if apply_common_nodata is True:
    print ("\t")
    output_line = ((time.strftime("%H:%M:%S")) + " Creating the common NoData values bitmap")
    print(output_line)

    file = filo
    dbic = [1]
    dbob = []
    tval = [nodata_value, nodata_value]
    comp = 'off'
    dbsn = 'NoData'
    dbsd = 'NoDataVal'

    thr( file, dbic, dbob, tval, comp, dbsn, dbsd )


    # Write an output EASI model file for the second thematic layer.
    outeasi_list = []
    outeasi = ("if %2 = " + str(nodata_value) + " then")
    outeasi_list.append(outeasi)
    outeasi = "%%2 = 1"
    outeasi_list.append(outeasi)
    outeasi = "endif"
    outeasi_list.append(outeasi)

    outeasi = "if %%2 = 1 then"
    outeasi_list.append(outeasi)
    outeasi = ("%1 ="  + str(nodata_value))
    outeasi_list.append(outeasi)
    outeasi = ("%2 =" + str(nodata_value))
    outeasi_list.append(outeasi)
    outeasi = "endif"
    outeasi_list.append(outeasi)

    file1 = os.path.join(output_folder, "easi_model.txt")
    with open(file1, "w") as f:
        f.write("\n".join(outeasi_list))

    output_line = ((time.strftime("%H:%M:%S")) + " Applying the EASI model to set the NoData")
    print(output_line)
    file = filo
    source = file1
    undefval = []
    model(file, source, undefval)


# --------------------------------------------------------------------------------------------------------------------
# C)  Find the unique values
# --------------------------------------------------------------------------------------------------------------------

new_line = ("\t")
output_folder = os.path.dirname(input_file)
output_file_lines = []
file = os.path.join(output_folder, output_file_name)

# A ) Open input file
print("\t")
output_line = ((time.strftime("%H:%M:%S")) + " Reading the input raster file")
print (output_line)
output_file_lines.append(output_line)

with ds.open_dataset(input_file, ds.eAM_READ) as ds2:
    aux = ds2.aux_data
    num_cols = ds2.width
    num_rows = ds2.height
    num_channels = ds2.chan_count
    ref_crs = ds2.crs  # coordinate system
    ref_geocoding = ds2.geocoding  # Geocoding

    output_line = ("Input raster: " + input_file)
    print (output_line)
    output_file_lines.append(output_line)

    output_line =("  X - Number of columns (pixels): " + str(num_cols))
    print (output_line)
    output_file_lines.append(output_line)

    output_line = ("  Y - Number of rows (lines): " + str(num_rows))
    print (output_line)
    output_file_lines.append(output_line)

    output_line = ("Number of channels: " + str(num_channels))
    print (output_line)

    print (new_line)
    output_file_lines.append(new_line)


#B) Find the uniques values for both input layer
print("\t")
output_line = ((time.strftime("%H:%M:%S")) + " Finding the uniques values for both thematic rasters")
print (output_line)
output_file_lines.append(output_line)

with ds.open_dataset(input_file) as ds3:
    reader = ds.BasicReader(ds3)
    # read the raster channels
    raster = reader.read_raster(0, 0, reader.width, reader.height)

    layer_1 = raster.data[:, :, (0)]
    layer_2 = raster.data[:, :, (1)]

    if apply_common_nodata is True:
        print ("Ataboy")
        layer_1_rsp = layer_1.reshape(-1)
        layer_2_rsp = layer_2.reshape(-1)
        layer_1_nval = np.delete(layer_1_rsp, np.where(layer_1_rsp == nodata_value))
        layer_2_nval = np.delete(layer_2_rsp, np.where(layer_1_rsp == nodata_value))
        print("Size of layer 1 after NoData removal: " + str(len(layer_1_nval)))
        print("Size of layer 2 after NoData removal: " + str(len(layer_2_nval)))
        layer_1 = layer_1_nval
        layer_2 = layer_2_nval


    print ("here5")
    unique_1, frequency_1 = np.unique(layer_1, return_counts = True)
    unique_2, frequency_2 = np.unique(layer_2, return_counts = True)
    print ("here6")


# print unique values array
tempuniq = str(unique_1)
output_line = (" Unique Values (classif_layer_1) :" + tempuniq)
print (output_line)
output_file_lines.append(output_line)
tempuniq = str(unique_2)
output_line = (" Unique Values (classif_layer_2) :" + tempuniq)
print (output_line)
output_file_lines.append(output_line)

# print frequency array
tempfreq = str(frequency_1)
output_line = (" Frequency Values (classif_layer_1): " + tempfreq)
print (output_line)
output_file_lines.append(output_line)
tempfreq = str(frequency_2)
output_line = (" Frequency Values (classif_layer_2): "+ tempfreq)
print (output_line)
output_file_lines.append(output_line)

# Verification to check if there is the same number of pixels in both frequency
sum_layer_1 = np.sum(frequency_1)
sum_layer_2 = np.sum(frequency_2)

if sum_layer_1 != sum_layer_2 :
    print (" Error - the sum of pixels for both layer is not the same")
    sys.exit()
else :
    output_line = (" Pixels count for layer 1: " + str(sum_layer_1))
    output_file_lines.append(output_line)
    print (output_line)
    output_line = (" Pixels count for layer 1: " + str(sum_layer_2))
    output_file_lines.append(output_line)
    print (output_line)


print("\t")
output_file_lines.append(new_line)
output_line = ((time.strftime("%H:%M:%S")) + " Comparing the two thematic layers")
print(output_line)
output_file_lines.append(output_line)

# CM - write the first two lines of the confusion matrix
output_cmatrix_lines = []
output_cmatrix_lines.append(new_line)
out_cm1 = (".;.;layer2;.;.;.;.;.;.;layer2")
output_cmatrix_lines.append(out_cm1)
out_cm2a = ("..."+";"+"cl"+";")
out_cm2b = ';'.join(map(str,unique_2))
out_cm2 = (out_cm2a + out_cm2b + ";.;cl;"+ out_cm2b)
print (out_cm2)
output_cmatrix_lines.append(out_cm2)


for ii in unique_1:
    print("-------------------------------------------------------------")
    output_line = ("Thematic layer 1 unique value: " + str (ii))
    print (output_line)
    output_file_lines.append(output_line)

    layer_1_rsp = layer_1.reshape(-1)
    layer_2_rsp = layer_2.reshape(-1)

    layer_2_rsp = np.delete (layer_2_rsp, np.where(layer_1_rsp != ii))
    unique_tp, frequency_tp = np.unique(layer_2_rsp, return_counts=True)

    output_line = (" Unique value(s) of thematic layer 2: " + str (unique_tp))
    print (output_line)
    output_file_lines.append(output_line)
    output_line = (" Frequency of unique values: " + str (frequency_tp))
    print(output_line)
    output_file_lines.append(output_line)
    output_file_lines.append(new_line)

    # ------------------------------------------------------------------------------------
    print ("\t")
    # Need to find occurences where an unique value in layer does not contain all original
    # unique values of the second layer and add a frequency of 0.

    matrix_output_value = []
    matrix_output_freq = []

    print (unique_2)
    print (list(unique_2))
    unique_tp_list = list(unique_tp)
    frequency_tp_list = list(frequency_tp)

    for jj in unique_2:
        print ("val" + str(jj))

        if jj in unique_tp:
            matrix_output_value.append(jj)
            pos_val = unique_tp_list.index(jj)
            fq = frequency_tp_list[pos_val]
            matrix_output_freq.append(fq)
        else:
            matrix_output_value.append (jj)
            matrix_output_freq.append(0)

    print (ii, matrix_output_value, matrix_output_freq)

    # CM - write the other lines of the confusion matrix
    out_cm3a = ("layer1" + ";"+ str(ii)+";")
    out_cm3b = ';'.join(map(str, matrix_output_freq))
    out_cm3c = (out_cm3a + out_cm3b + ";.;" + str(ii)+";")

    #compute the frequency in pct
    temp_sum = np.sum(matrix_output_freq)
    temp_pct = []
    for ii in list(matrix_output_freq):
        aa = round((ii/temp_sum) * 100,2)
        temp_pct.append (aa)

    out_cm3d = ';'.join(map(str, temp_pct))
    out_cm3 = out_cm3c + out_cm3d
    print (out_cm3)
    output_cmatrix_lines.append(out_cm3)


with open(file, "w") as f:
    f.write("\n".join(output_file_lines))

with open(file, "a") as f:
    f.write("\n".join(output_cmatrix_lines))

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

