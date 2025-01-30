
'''----------------------------------------------------------------------
 * Gabriel Gosselin, CCRS                                                    -
 * ----------------------------------------------------------------------
'''

# The following locale settings are used to ensure that Python is configured
# the same way as PCI's C/C++ code.  
import locale
locale.setlocale(locale.LC_ALL, "")
locale.setlocale(locale.LC_NUMERIC, "C")

import os, glob, fnmatch, sys, time

from pci.ortho import ortho
from pci.pyramid import pyramid
from pci.thr import thr
from pci.bit2poly import bit2poly
from pci.exceptions import *
from pci.api import datasource as ds
from pci.api.cts import crs_to_mapunits
#-----------------------------------------------------------------------------------------------------
#  Discover candidate files inside a folder, ingest the files, create a MFILE and run INSINFO
#-----------------------------------------------------------------------------------------------------
'''VERSIONS
2021-03-10  v1.5  - Added section A2
                  - Added a counter when reading the files metadata
2023-04-02  v2.0  - Added the footprint generation option
'''

#----------------------------------------------------------------------------------------------
#  User defined variables
#----------------------------------------------------------------------------------------------
## Input mode - Valid options are 1 (MFILE) or 2 (Search folder + keyword)
Input_mode = 2
Input_mode_1_MFILE=r"E:\InSAR_tutorial\RS2_Vancouver\55_OrbAdjust_resamp\MFILE_Multilooked_files_to_ortho_list.txt"
Input_mode_2_Search_Folder=r"E:\WP98_Results\Sentinel-1\2019_ASC"
Input_mode_2_keyword="*.pix"

## Ortho options
Orthos_extent_option = 1

Ortho_resolution_X = "8"
Ortho_resolution_Y = "8"

option1_AOI_vector_file = r"D:\WP98_RawData_and_ancillary\LSTP_clip_layer_UTM18T_D000.pix"
option1_AOI_file_SegmentNumber=2

option2_ortho_projection = "UTM 11S D000"
option2_ortho_upper_left_x= "486408"       
option2_ortho_upper_left_y= "5449977"
option2_ortho_lower_right_x= "488346"    
option2_ortho_lower_right_y= "5447527"

# DEM options
DEM_file=r"D:\WP98_RawData_and_ancillary\LSTP_GLO30-DEM_UTM18T_D000.pix"
Elevation_channel=1

#Output options
create_footprints = "yes"   # Valid options: "yes" or "no"

filename_output_format = 1 
Prefix = ""                   # Optional. Leave blank "" for no prefix.
output_folder=r"E:\WP98_Results\Sentinel-1\2019_ASC\orthos"

''' 
"------------------------------------------------------------------------------------------------------
 Specifications
"------------------------------------------------------------------------------------------------------
A) Ortho images extents options
Corner coordinates and resolution must be provided in a format compatible with the specified projection
Read the ortho documentation for more details
Orthos_extent_option, valid options are:  
    1 (area of interest). Orthos projection, dimensions and resolution are  are taken from the input AOI vector file
    2 (user defined) 
    3 (file defined)  Bounds and resolution are taken for each input image. 

Options 1 and 2 will ensure that all output orthos will have the same number of lines and columns.
This is usefull for stacks of data covering approximatively the same area. 


B) filename_output_format. Valid options: 1,2,3,4 and 5
1 : the prefix o will be added at the beginning of the file. Work only with already ingested data.
2: 



'''


#----------------------------------------------------------------------------------------------
#  Quick validation
#----------------------------------------------------------------------------------------------
start = time.time()
yes_validation_list = ["yes","y","yys","yse","yee","yss","ys"]

if create_footprints.lower() in yes_validation_list:
    create_footprints = True
    print ("Ortho footprints will be created")
else:
    create_footprints = False
    print("Ortho footprints won't be created")

#----------------------------------------------------------------------------------------------
#  Program
#----------------------------------------------------------------------------------------------

# Create output file if not already existing
if not os.path.exists(output_folder):  
    os.makedirs(output_folder)

#-----------------------------------------------------------------------------------------
#A.1) Find all Interferogram to orthorectify

files_to_ortho_list=[]
if Input_mode==1:   #Read an Existing MFILE and create a list of file to process    

    with open(Input_mode_1_MFILE, "r") as ins:
        for line in ins:
            line=line.strip()
            files_to_ortho_list.append(line)

elif Input_mode==2: #Search folder with a keyword    
   
   for root, dirs, files in os.walk(Input_mode_2_Search_Folder):
        for filename in fnmatch.filter(files, Input_mode_2_keyword):
            files_to_ortho_list.append(os.path.join(root,filename))                
else:            
    print ("Error - Input mode must be set with 1 (MFILE) or 2 (Search Folder+ keyword)")
    sys.exit()        
            
# For Input_mode==2,   verify if at least one file was found.  
if len(files_to_ortho_list)==0:
    print ("\t")
    print ("Error - no files found")
    print ("Specify another keyword or search folder")
    sys.exit()


#A.2) Print the list of found files 
total_files=str(len(files_to_ortho_list))
print("Number of inputs files: "+ total_files)
print("\t")

for input_files in files_to_ortho_list: 
    print (input_files)



# B.1) Apply a naming convention to the output file

#Early validation
if filename_output_format not in [1,2,3,4,5]:
    print("\t")
    print ("Error - Output file name format is not valid")
    print ("Specified value is "+str(filename_output_format))
    print ("Accepted values are: 1, 2, 3 or 4")
    sys.exit()

print (time.strftime("%H:%M:%S") + " Reading the input file metadata")
print ("\t")

Acquisition_DateTime2=[]
Acquisition_DateTime3=[]
SensorModelName2=[]
Acquisition_Type2=[]
SourceID2=[]
PlatformName2=[]
Orbit_Direction2=[]
BeamMode2=[]
ProductType2=[]
projection_list=[]

count = 1
for ii in files_to_ortho_list:
    with ds.open_dataset(ii,ds.eAM_READ) as ds2:
        aux=ds2.aux_data

        print (((time.strftime("%H:%M:%S")) + " Reading metadata, file "+str(count)+" of " +
                                                                                    str(len(files_to_ortho_list))))
        projection_list.append(crs_to_mapunits(ds2.crs))

        Acquisition_DateTime=aux.get_file_metadata_value('Acquisition_DateTime')
        Acquisition_DateTime2.append(Acquisition_DateTime)

        Acquisition_Type=aux.get_file_metadata_value('Acquisition_Type')
        Acquisition_Type2.append(Acquisition_Type)

        SensorModelName=aux.get_file_metadata_value('SensorModelName')
        SensorModelName2.append(SensorModelName)

        SourceID=aux.get_file_metadata_value('SourceID')
        SourceID2.append(SourceID)

        PlatformName=aux.get_file_metadata_value('PlatformName')
        PlatformName2.append(PlatformName)

        Orbit_Direction=aux.get_file_metadata_value('OrbitDirection')
        Orbit_Direction2.append(Orbit_Direction)

        BeamMode=aux.get_file_metadata_value('BeamMode')
        BeamMode2.append(BeamMode)

        ProductType=aux.get_file_metadata_value('ProductType')
        ProductType2.append(ProductType)
        count=count+1

for ii in Acquisition_DateTime2:
    a=ii.replace("-","")
    b=a.replace(":","")
    Acquisition_DateTime3.append(b[:8])

#-----------------------------------------------------------------------------------------
# Build output filename based on user choice 
#-----------------------------------------------------------------------------------------

output_file_name=[]


if filename_output_format == 1:
    for input_file in files_to_ortho_list :
        basename = os.path.basename (input_file)
        output_file_name.append(basename)

elif filename_output_format == 2:    # Source ID
    for ii in SourceID2:
        temp=Prefix+ii+".pix"
        output_file_name.append(temp)

elif filename_output_format == 3:   # Compact date
    for date in Acquisition_DateTime3:
        temp=Prefix+date+".pix"
        output_file_name.append(temp)

elif filename_output_format == 4:
    for type, date in zip (Acquisition_Type2, Acquisition_DateTime3):
        temp=Prefix+type+"_"+ date +".pix"
        output_file_name.append(temp)

elif filename_output_format == 5:
    for type, date, orbit in zip (SensorModelName2, Acquisition_DateTime3,Orbit_Direction2):
        temp=Prefix+type+"_"+date+"_"+orbit+".pix"
        output_file_name.append(temp)


#######################################################################################################################
# B) Find the bounding box of the area of interest (AOI) if  Orthos_extent_option==1

if Orthos_extent_option == 1:
    print (time.strftime("%H:%M:%S") + " Extracting the bounding box coordinate around the input AOI")
    print ("   Input AOI: " + option1_AOI_vector_file)

    X_coordinates = []
    Y_coordinates = []
    # open the dataset in write mode
    with ds.open_dataset(option1_AOI_vector_file) as ds1:
        AOI_MapProjection=crs_to_mapunits(ds1.crs)
        
        print("\t")
        print ("   AOI Map projection: " + AOI_MapProjection)
        ## DO A VALIDATION OF THE PROJECTION HERE, 
        
        # get vector segment 
        io = ds1.get_vector_io(option1_AOI_file_SegmentNumber)
        xs = []
        ys = []
        # iterate over shapes in the segment
        for index, shape in zip(io.shape_ids, io):
            # iterate over rings in the shape:
            xs.append(shape.extents[0])
            xs.append(shape.extents[2])
            ys.append(shape.extents[1])
            ys.append(shape.extents[3]) 

    #Upper left and lower right coordinates of the bounding box to 
    #calculate the DBIW window for every image              
    AOI_UL_X=min(xs)
    AOI_UL_Y=max(ys)
    AOI_LR_X=max(xs)
    AOI_LR_Y=min(ys)  

    print ("AOI Extends")
    print (AOI_UL_X,AOI_UL_Y,AOI_LR_X,AOI_LR_Y )
    print ("\t")


#-----------------------------------------------------------------------------------------
# C) Orthorectification

Orthorectified_Data_list=[]
number_of_files = str(len(files_to_ortho_list))

print ("\t")
count = 1
for input_file, outname in zip(files_to_ortho_list, output_file_name):

    print (((time.strftime("%H:%M:%S")) + " Orthorectifying file "+str(count)+" of " + number_of_files))
    print ("   Input file: " + input_file)

    base=os.path.basename(input_file)

    if Orthos_extent_option == 1:
        mapunits=AOI_MapProjection
        ulx=str(AOI_UL_X)     
        uly=str(AOI_UL_Y)
        lrx=str(AOI_LR_X)
        lry=str(AOI_LR_Y)
        bxpxsz = Ortho_resolution_X
        bypxsz = Ortho_resolution_Y
        
    elif Orthos_extent_option == 2:
        mapunits=option2_ortho_projection
        ulx=option2_ortho_upper_left_x    
        uly=option2_ortho_upper_left_y
        lrx=option2_ortho_lower_right_x
        lry=option2_ortho_lower_right_y
        bxpxsz=Ortho_resolution_X
        bypxsz=Ortho_resolution_Y
    
    elif Orthos_extent_option==3:
        mapunits=""
        ulx=""
        uly=""
        lrx=""
        lry=""
        bxpxsz="10"
        bypxsz="10"
    
    mfile=input_file
    dbic = []           # Blank, will process all channels of the input file.
    mmseg = []
    dbiw = []
    srcbgd = "NONE"


    filo = os.path.join(output_folder,"o" + outname)
    # If a file with the same name exists we add an unique ID at the end. This can happen under certain namming
    # format.
    if os.path.exists(filo):
        filo = os.path.join(output_folder,"o" + outname[:-4] +"_" +str(count)+".pix")

    ftype = "PIX"
    foptions = "TILED256"
    outbgd = [-32768.00000]
    edgeclip = []
    tipostrn = ""
    filedem = DEM_file
    dbec = [Elevation_channel]
    backelev = []
    elevref =""
    elevunit =""
    elfactor = []
    proc = ""
    sampling = [1]
    resample = "near"
    
    #pyramids options
    file=filo
    force = 'yes'
    poption= 'aver' 
    dboc=[]
    olevels=[]
   
    try:    
        ortho( mfile, dbic, mmseg, dbiw, srcbgd, filo, ftype, foptions, outbgd,
        ulx, uly, lrx, lry, edgeclip, tipostrn, mapunits, bxpxsz, bypxsz, filedem, 
        dbec, backelev, elevref, elevunit, elfactor, proc, sampling,resample )

        pyramid (file,dboc,force,olevels,poption)
        Orthorectified_Data_list.append(filo)
    except PCIException as e:
        print (e)
    except Exception as e:
        print (e)
    print("   Output orthorectified file: " + filo)

    #-----------------------------------------------------------------------------------------
    if create_footprints is True:
        print ("   Creating the ortho footprints")

    # ----------------
    file = filo
    dbic = [1]
    dbob = []
    tval = [-1000, 10000]  # threshold range (min,max)
    comp = 'off'
    dbsn = 'footprt'  # output segment name
    dbsd = 'bitmap to generate footprint'  # output segment description

    thr(file, dbic, dbob, tval, comp, dbsn, dbsd)
    # ----------------
    fili = filo
    dbib = [2]
    outname = os.path.basename(filo[:-4])
    filo = os.path.join(output_folder, outname + "_footprint.pix")
    smoothv = "no"
    dbsd = "ortho_footprint"  # output layer description
    ftype = ""  # defaults to PIX
    foptions = ""  # output format options

    bit2poly(fili, dbib, filo, smoothv, dbsd, ftype, foptions)

    count = count + 1
    
# Generating an MFILE of Orthorectified files    
file=open(os.path.join(output_folder,'Orthorectified_Data_list.txt'), "w")  
file.write('\n'.join(Orthorectified_Data_list))
file.close()        
   
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
