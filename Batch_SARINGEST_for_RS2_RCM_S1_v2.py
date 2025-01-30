#!/usr/bin/env python

'''
----------------------------------------------------------------------------------------------
Discover Sentinel, Radarsat-2 or RCM scenes and proceed to their ingestion.
----------------------------------------------------------------------------------------------
'''
# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale
locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")

import os, glob, fnmatch, sys, time

from pci.saringest import saringest
from pci.saringestaoi import saringestaoi
from pci.api import datasource as ds
from pci.exceptions import *

# -------------------------------------------------------------------------------------------------
#  User defined variables
# -------------------------------------------------------------------------------------------------
# Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
input_mode = 2

input_mode_1_MFILE = r"E:\InSAR_tutorial\RS2_Vancouver\55_OrbAdjust_resamp\MFILE_Multilooked_Interferogram_list.txt"
input_mode_2_Search_Folder = r"D:\WP98_RawData_and_ancillary\S1A_ASC_2019_P135"
input_mode_2_keyword = "manifest.safe"

# Ingest algorithm
ingest_algo = "saringestaoi"   # Valid options are "saringest" or "saringestaoi"

saringestaoi_clipfile = r"D:\WP98_RawData_and_ancillary\LSTP_clip_layer_UTM18T_D000.pix"
saringestaoi_dem = r"D:\WP98_RawData_and_ancillary\LSTP_GLO30-DEM_UTM18T_D000.pix"        # Leave to r"" (blank) to not specified an aoi file

# Output options
output_folder = r"E:\WP98_Results\Sentinel-1\2019_ASC"
output_filename_format = 5
date_format = "compact"          # Valid options are "compact" or "unique"
prefix = "p135_"                    # Optional


'''
"------------------------------------------------------------------------------------------------------
 Specifications
"------------------------------------------------------------------------------------------------------
## Ingest algorithm

if ingest_algo == "saringestaoi"
  use case: 
  ** leave saringestaoi_clipfile  and saringestaoi_dem  blank to ingest the whole scene, this will give the same results 
     than SARINGEST. 

  ** specify saringestaoi_clipfile  and leave saringestaoi_dem  blank. The  gmted2010.pix file provided in 
      C:\PCI Geomatics\CATALYST Professional\etc will be use. 
      Note: The clip file must be a vector file containing a polygon. The script will error iff one of the scenes to be
      ingested is not at least partially overlapping with the clip file. 
       
      Note: For a given scene, if a portion of it is included in the AOI but not overlapping the DEM, the concerned
            portion will be set as NoDATA. 
       

##  Output File name format. 
A.1) The following metadata will be extracted from every input file
Relevant metadata --> examples

* Acquisition_DateTime --> 2019-05-14T11:08:19.061659Z
    date_time_compact  --> 20190514
    date_time_unique   --> 20190514_110819061659

* BeamMode               --> FQ8W, IW, EW..   etc
* OrbitDirection         --> Descending  (will be simplified to DESC or ASC). 
* Product_Type           --> SLC, GRD  
* SensorModelName        --> RADARSAT_2, SENTINEL_1
* PlatformName           --> RASARSAT-2, SENTINEL-1
    sensor_name_compact  --> RS2, S1
* Polarizations          --> VV,VH
          pol_c          --> VV-VH  (comma will be replace by hyphen) 
* Source_ID              --> S1B_IW_SL1__1_DV_20210601T235241_20210601T235314_027170_033ECC_5529.SAFE
                         --> PDS_07302870
  
A.2) output_filename_format  --> Example (S)

1: prefix + SourceID2  
        --> LSTP_S1B_IW_SL1__1_DV_20210601T235241_20210601T235314_027170_033ECC_5529.SAFE.pix
        --> LSTP_PDS_07302870.pix

2: prefix + PlatformName2 + date_time_compact  
        --> LSTP_RS2_20190514.pix
        
3: Prefix + PlatformName2 + date_time_compact + BeamMode +  Orbit_Direction2
        --> LSTP_RS2_20190514_FQ08_ASC.pix         
        
4: Prefix + PlatformName2 + date_time_unique + BeamMode +  Orbit_Direction2 + Product Type        
        --> LSTP_RS2_20190514_110819061659_FQ08_ASC_SLC.pix

5: Prefix + PlatformName2 + date_time_unique + BeamMode + pol_c + Orbit_Direction2 + Product Type
-        -> LSTP_RS2_20190514_110819061659_FQ08_HH-VV-VH-VV_ASC_SLC.pix
'''


# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
#  Main program
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

calibration_type = "sigma"
Subset_input_data = "no"

# ------------------------------------------------------------------------------------------------------
# A) Early Validation
# ------------------------------------------------------------------------------------------------------
start = time.time()
if output_filename_format not in [1,2,3,4,5]:
    print("\t")
    print ("Error - Output file name format is not valid")
    print ("Specified value is "+str(Output_filename_format))
    print ("Accepted values are: 1, 2, 3, 4 or 5")
    sys.exit()

# Calibration type    
if calibration_type.lower() not in ["sigma","gamma","beta","none"]:
    print ("Error- Calibration type is invalid")
    print ("Specified value is " + calibration_type)
    print ('"Accepted values are: "sigma", "beta", "gamma" or "none"')
    sys.exit()

if ingest_algo.lower() not in ["saringest", "saringestaoi"]:
    print("Error- ingest_algo option is not valid")
    print ('Valid options are: "saringest" or "saringestaoi')


if ingest_algo.lower() == "saringestaoi":

    if saringestaoi_clipfile != "":
        if not os.path.exists(saringestaoi_clipfile):
            print ("Error - the specified saringestaoi_clipfile path/file name does not exists or is incorrect")
            print ("Entered value: " + saringestaoi_clipfile )
            sys.exit()

    if saringestaoi_dem != "":
        if not os.path.exists(saringestaoi_dem):
            print ("Error - the specified saringestaoi_dem path/file name does not exists or is incorrect")
            print ("Entered value: " + saringestaoi_dem )
            sys.exit()

    if saringestaoi_clipfile == "" and saringestaoi_dem == "":
        print ("SARINGESTAOI selected - No clipping will be applied")

    # Special use case where the user has a clip file but no DEM or a DEM with insufficient extents
    if saringestaoi_clipfile != "" and saringestaoi_dem == "":
        saringestaoi_dem = r"C:\PCI Geomatics\CATALYST Professional\etc\gmted2010.pix"
        if not os.path.exists(saringestaoi_dem):
            print ("Surrogate DEM not found")
            print ("Surrogate DEM path:" + saringestaoi_dem )

# Subset option
if Subset_input_data.lower() not in ["yes","y","ys","yse","n","no","nn"]:   
    print ("Error- Specified subset option is invalid")
    print ("Specified value is "+ str(Subset_input_data))
    print ("Accepted values are: yes or no")
    sys.exit()    

if date_format.lower() not in ["compact","unique"]:
    print("Error - specified date_format options is invalid")
    print('Accepted values are: "compact" or "unique"')
    sys.exit()

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# ------------------------------------------------------------------------------------------------------
#B) Find the files to ingest 
print ("-----------------------------------------------------------------------------------------------")
print ("                                      Data search                                              ") 
print ("-----------------------------------------------------------------------------------------------")

if input_mode == 2: 
    print (time.strftime("%H:%M:%S") + " Retrieving files in " + output_folder +
                       " matching the keyword < " + input_mode_2_keyword +" >" )

file_ingest_list = []

if input_mode == 1:  # Read an existing MFILE and create a list of file to process

    with open(input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line = line.strip()
            file_ingest_list.append(line)

elif input_mode == 2:  # Search folder with a keyword

    for root, dirs, files in os.walk(input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, input_mode_2_keyword):
            file_ingest_list.append(os.path.join(root, filename))
else:
    print("Error- Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()

# For input_mode==2,   verify if at least one file was found.
if len(file_ingest_list) == 0:
    print("\t")
    print("Error- no files found")
    print("Specify another keyword or search folder")
    sys.exit()

print ("   Number of scenes found: " + str (len(file_ingest_list)))
print ("\t")

# ------------------------------------------------------------------------------------------------------
#C) Metadata extraction
print ("-----------------------------------------------------------------------------------------------")
print ("                                    Metadata extraction                                        ") 
print ("-----------------------------------------------------------------------------------------------")

# C.1) Metadata extraction
print (time.strftime("%H:%M:%S") + " Metadata extraction")
print ("\t")

Acquisition_DateTime2 = []
SensorModelName2 = []
Acquisition_Type2 = []
SourceID2 = []
PlatformName2 = []
Orbit_Direction2 = []
BeamMode2 = []
ProductType2 = []
pol_c = []

count = 1
nb_files = str (len(file_ingest_list))
for ii in file_ingest_list:

    print ("\t")
    print (time.strftime("%H:%M:%S") + " Extracting metadata, file  " + str(count)+ " of " + nb_files )
    print ("   Reading file -->" + ii)
        
    with ds.open_dataset(ii,ds.eAM_READ) as ds2:
        aux = ds2.aux_data
        
        Acquisition_DateTime = aux.get_file_metadata_value('Acquisition_DateTime')
        Acquisition_DateTime2.append(Acquisition_DateTime)  
        
        Acquisition_Type=aux.get_file_metadata_value('Acquisition_Type')
        Acquisition_Type2.append(Acquisition_Type)        
        
        SensorModelName=aux.get_file_metadata_value('SensorModelName')
        SensorModelName2.append(SensorModelName)
                
        SourceID = aux.get_file_metadata_value('SourceID')
        SourceID2.append (SourceID)

        PlatformName = aux.get_file_metadata_value('PlatformName')
        if PlatformName == "RADARSAT-2":
            pname = "RS2"
        elif PlatformName == "SENTINEL-1":
            pname = "S1"
        else:         
            pname = PlatformName

        PlatformName2.append(pname)
        
        Orbit_Direction = aux.get_file_metadata_value('OrbitDirection')
        if Orbit_Direction == "Descending":
            orbit_type = "DESC"
        elif Orbit_Direction == "Ascending":
            orbit_type = "ASC"
        else:
            orbit_type = Orbit_Direction      
        Orbit_Direction2.append(orbit_type) 
        
        BeamMode=aux.get_file_metadata_value('BeamMode')
        BeamMode2.append(BeamMode) 
        
        ProductType = aux.get_file_metadata_value('ProductType')
        ProductType2.append(ProductType)

        Polarizations = aux.get_file_metadata_value('Polarizations')
        temp_pol_c = Polarizations.replace(", ", "-")
        pol_c.append (temp_pol_c)
            
    count = count + 1


# C.2) Date time formatting
print ("\t")
print (time.strftime("%H:%M:%S") + " Acquisition date and time formatting...")

date_time_compact = []
date_time_unique = []  # necessary for scenes on the same swath.
string_replace = str.maketrans({'-': '', ':': '', 'T': '_', '.': '', 'Z': ''})

for ii in Acquisition_DateTime2:   
    output_string = ii.translate(string_replace)
    date_time_compact.append(output_string[:8])
    date_time_unique.append (output_string)

if date_format.lower() == "compact":
    date_out = date_time_compact
elif date_format.lower() == "unique":
    date_out = date_time_unique
else:
    sys.exit()

# C.4) Output filename formatting
output_file_name = []

if output_filename_format == 1: # Prefix + Source_ID
    for ii in SourceID2:
        temp = prefix + ii + ".pix"
        output_file_name.append(temp)

elif output_filename_format == 2:  # Prefix + PlatformName2 + date
    for pname, date in zip(PlatformName2, date_out):
        temp = prefix + pname + "_" + date + ".pix"
        output_file_name.append(temp)

elif output_filename_format == 3:  # Prefix + PlatformName2 + date + BeamMode +  Orbit_Direction2
    for pname, beam, date, orbdir in zip(PlatformName2, date_out, BeamMode2, Orbit_Direction2):
        temp = prefix + pname + "_" + date + "_" + beam + "_" + orbdir + ".pix"
        output_file_name.append(temp)

elif output_filename_format == 4: # Prefix + PlatformName2 + date + BeamMode +  Orbit_Direction2 + Product Type
    for pname, date, beam, orbdir, ptype in zip(PlatformName2, date_out, BeamMode2, Orbit_Direction2, ProductType2 ):
        temp = prefix + pname + "_" + date + "_" + beam + "_" + orbdir + "_" + ptype + ".pix"
        output_file_name.append(temp)
         
elif output_filename_format == 5: # Prefix + PlatformName2 + date + BeamMode + pol_c + Orbit_Direction2 + Product Type
    for pname, date, beam, pol, orbdir, ptype in zip(PlatformName2, date_out, BeamMode2, pol_c, Orbit_Direction2, ProductType2):
        temp = prefix + pname + "_" + date + "_" + beam + "_" + pol + "_"+ orbdir + "_" + ptype + ".pix"
        output_file_name.append(temp)
# ------------------------------------------------------------------------------------------------------
#E) SAR data ingestion
print ("-----------------------------------------------------------------------------------------------")
print ("                                    SAR data ingestion                                        ")
print ("-----------------------------------------------------------------------------------------------")

num_files = str(len(file_ingest_list))
count = 1
for img, outname in zip(file_ingest_list, output_file_name):

    print ("\t")
    outname_path = os.path.join(output_folder, outname)
    print ((time.strftime("%H:%M:%S"))+" Ingesting file " + str(count)+" of " + num_files + "...")
    print ("   Ingesting-->" + img)
    print ("   Output file--> " + outname_path)

    # If a file with the same name exists we add a unique ID at the end.
    # This can happen under certain naming options.

    if os.path.exists(outname_path):
        print ("   Output file name already exist")
        outname2 = outname[:-4]
        outname3 = outname2 + "_"+ str(count)
        outname_path2 = os.path.join(output_folder, outname3)
        print("   Output file name replaced by:" + outname_path)
    else :
        outname_path2 = outname_path


    fili = img
    filo = outname_path2
    calibtyp = calibration_type
    dbiw = []
    poption = 'AVER'
    dblayout = 'pixel'

    maskfile = saringestaoi_clipfile
    mask = [2]
    filedem = saringestaoi_dem
    dbec = [1]
    fillop = "nodata"

    if ingest_algo.lower() == "saringest":
        try :
            print ("   saringest")
            saringest(fili, filo, dbiw, poption, dblayout, calibtyp)
        except PCIException as e:
            print (e)
        except Exception as e:
            print (e)

    if  ingest_algo.lower() == "saringestaoi":
        try :
            print("   saringestaoi")
            print("   DEM file:" + filedem )
            saringestaoi(fili, filo, calibtyp, dbiw, maskfile, mask, fillop, filedem, dbec, poption, dblayout)
        except PCIException as e:
            print (e)
        except Exception as e:
            print (e)

    count = count + 1

print("------------------------------------------------------------------------------")
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
