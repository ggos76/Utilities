
import time
import os
import sys
from winreg import KEY_CREATE_SUB_KEY
import pci
from pci.exceptions import PCIException
from pci.api import datasource as ds
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import csv

# ----------------------------------------------------------------------------------------------------------------------
# User defined variables
# ----------------------------------------------------------------------------------------------------------------------
# A) I/O options
input_type = "text"                                              # Valid options are "raster" or "text"
text_csv_header = "yes"                                            # Valid options are "yes" or "no"

input_file = r"D:\HBL_3MAPS_regression_rates\20241119_attempt_3\20241119_Stats_2010_2017_2024_min_100_n=13714_no_div0.csv"
x_axis_int = 10
y_axis_int = 12

#input_file = r"D:\HBL_Palsa_Mapping_regional\small_Landsat_test.pix"
#x_axis_int = 1
#y_axis_int = 2

## B) 2D Plots options
# Reducing the number of points for faster rendering of the 2D scatter plot
# Recommended when input_type = "raster"
apply_point_reduction = "no"                               # Valid options are "yes" or "no"
number_of_points = 20000

# Calculate and add a regression line to the 2D scatter plot
display_regression_line = "NO"                                           # Valid options are "yes" or "no"
polynomial_order = 1

output_plot_name = r'D:\HBL_3MAPS_regression_rates\20241119_attempt_3\fdjsfdsj.png'
plot_title = 'average area loss per year (%)'
x_axis_name = '2010-2017: average area loss per year (%), min $100m^2$, n = 13 714'
y_axis_name = '2017-2024: average area loss per year (%)'

display_scatter_plot = "yes"
'''
# ----------------------------------------------------------------------------------------------------------------------
# Notes
# ----------------------------------------------------------------------------------------------------------------------
 Text file must be in CSV format. 
 if text_csv_header = "yes",  the first line of the input data will be remove. 

 *Number of samples for displaying and saving data. 
  10 000 samples is fast.
  20 000 samples is manageable. 
'''


# ----------------------------------------------------------------------------------------------------------------------
# Do not modify after this
# ----------------------------------------------------------------------------------------------------------------------
def coefficent_sign(input_coef, rf):
    if input_coef > 0:
        polycoef_expression = (" + " + str(round(input_coef, rf)))
    else:
        ee = str(abs(round(input_coef, rf)))
        polycoef_expression = (" - " + ee)
        # polycoef_expression = str(round(input_coef,rf))

    return (polycoef_expression)


# ----------------------------------------------------------------------------------------------------------------------
# A) Quick validation of the input parameters
# ----------------------------------------------------------------------------------------------------------------------
start = time.time()
# Hard coded values
yes_validation_list = ["yes", "y", "yse", "ys"]
no_validation_list = ["no", "n", "nn"]
yes_no_validation_list = yes_validation_list + no_validation_list

# A) I/O options
input_type = input_type.lower()
if input_type not in ["raster", "text"]:
    print ('Error !  The input_type parameter must be "raster" or "text"')
    sys.exit()

if input_type == "raster": 
    input_raster = True
else: 
    input_raster = False

if input_type == "text": 
    input_csv_text = True

    text_csv_header = text_csv_header.lower()
    if text_csv_header not in yes_no_validation_list: 
        print ('Error !  text_csv_header must be set with "yes" or "no"')
        sys.exit()

    elif text_csv_header in yes_validation_list: 
        remove_header = True 
    else:   
        remove_header = False
else: 
    input_csv_text = False

# Checking for the input file
if not os.path.exists(input_file):
    print ("Error ! - The input_file does not exists or the path is wrong")
    sys.exit()

if int(x_axis_int) != x_axis_int or int(y_axis_int) != y_axis_int: 
    print ("Error ! - x_axis_int and y_axis_int must be integers")
    sys.exit()
elif  x_axis_int == y_axis_int or x_axis_int < 1 or y_axis_int < 1: 
    print ("Error ! - x_axis_int and y_axis_int must be  different and >= 1")
    sys.exit()
else:
    # redundant check to avoid edge cases like 1.000000
    x_axis_int = int(x_axis_int) 
    y_axis_int = int(y_axis_int)
    # Indexation to Python standard, column 1 is 0, raster channel 1 is 0, etc
    x_axis_int = x_axis_int - 1
    y_axis_int = y_axis_int - 1

# B) 2D Plots options
apply_point_reduction = apply_point_reduction.lower()
if apply_point_reduction not in yes_no_validation_list:
    print ('Error ! apply_point_reduction be set with "yes" or "no"')
    sys.exit()
elif apply_point_reduction in yes_validation_list: 
    apply_sampling = True
else: 
    apply_sampling = False

# Add check for number of points here

display_regression_line = display_regression_line.lower()
if display_regression_line not in yes_no_validation_list: 
        print ('Error !  Display_regression_line must be set with "yes" or "no"')
        sys.exit()
elif display_regression_line in yes_validation_list:
    display_regression = True
else: 
    display_regression = False

# Add a check for the polynomial order

if display_scatter_plot not in yes_no_validation_list: 
    sys.exit()
elif display_scatter_plot in yes_validation_list: 
    display_scatter_plot = True
else: 
    display_scatter_plot = False


# ----------------------------------------------------------------------------------------------------------------
# Main program
# ----------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------
# 1) Read the input file 
# ----------------------------------------------------------------------------------------------------------------

# Input data is raster
print ("-----------------------------------------------------------------------------------------------------")
if input_raster is True:

    print("\t")
    print((time.strftime("%H:%M:%S")) + "... Reading the input raster file")

    with ds.open_dataset(input_file) as ds1:

        # Read raster data
        reader = ds.BasicReader(ds1)
        raster = reader.read_raster(0, 0, reader.width, reader.height)


        x_axis_data = raster.data[:, :, x_axis_int]
        x_axis_data = x_axis_data.reshape(-1)

        y_axis_data = raster.data[:, :, y_axis_int]
        y_axis_data = y_axis_data.reshape(-1)

        print ("\t")
        print ("Input file: " + input_file)
        print("Number of Pixels (X)  and Lines (Y): " + str (reader.width) + ", " + str (reader.height))

        # Read the metadata to retrieve the NoDataValue at the File Level
        aux = ds1.aux_data
        nodata = aux.get_file_metadata_value('NO_DATA_VALUE')
        print ("No Data value is " + str(nodata))

    # Removing the NoData value from the array. There is no removal of NANs
    # (if needed,  look the code in s4A_PSI_INSPSC. for removing NANs)
    original_lenght = len(x_axis_data)
    x_axis_data = np.delete(x_axis_data, np.where(x_axis_data == float(nodata)))
    x_array_lenght = len(x_axis_data)
    y_axis_data = np.delete(y_axis_data, np.where(y_axis_data == float(nodata)))
    y_array_lenght = len(y_axis_data)

    # Quality control check
    if x_array_lenght != y_array_lenght:
        print ("Error - X and Y axis doesn't have the same amount of NoDataValue")
        print("X axis number of samples: " + str(x_array_lenght))
        print("Y axis number of samples: " + str(y_array_lenght))
        sys.exit()
    else:
        No_NoData  = original_lenght - x_array_lenght

        print ("Number of original samples: " + str (original_lenght))
        print ("Number of No Data Value removed: " + str(No_NoData))
        final_samples_pct = str(round (((original_lenght - No_NoData) / original_lenght) * 100, 2))
        print ("Final number of samples: " + str(x_array_lenght) + " ("+ final_samples_pct +"%)")

# Reading and parsing the CSV file
if input_csv_text is True:
    
    print("\t")
    print((time.strftime("%H:%M:%S")) + "... Reading the input CSV file")

    x_axis_csv = []
    y_axis_csv = []

    with open(input_file, 'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')

        for row in plots:
            x_axis_csv.append(row[x_axis_int])
            y_axis_csv.append(row[y_axis_int])

    if remove_header is True:
        x_axis_csv.pop(0)
        y_axis_csv.pop(0)

    csv_x_axis_data = []
    csv_y_axis_data = []
    for ii, jj in zip(x_axis_csv, y_axis_csv): 
        
        kk=float(ii)
        ll=float(jj)
        csv_x_axis_data.append(kk)
        csv_y_axis_data.append(ll)

    x_axis_data = np.asarray(csv_x_axis_data)
    y_axis_data = np.asarray(csv_y_axis_data)

'''
print (str(len(x_axis_data)))
print (str(len(y_axis_data)))
print (x_axis_data)
print (y_axis_data)
'''

# ----------------------------------------------------------------------------------------------------------------
# 2) Calculating the correlation coefficient and polynomial terms on the original data
# ---------------------------------------------------------------------------------------------------------------
if display_regression is True: 
    print ("\t")
    print ("-----------------------------------------------------------------------------------------------------")
    print ((time.strftime("%H:%M:%S"))+"...Computing the correlation coefficient and polynomial terms on the original data")
    print ("\t")

    # C.1) Defining the polynomial equation parameters.
    sample_size = str(len(x_axis_data))
    ccoef = np.corrcoef(x_axis_data, y_axis_data)[0,1]
    print ("Correlation coefficient: " + str(ccoef))
    print ("Number of samples: " + sample_size)

    print ("Calculating the polynomial terms...")
    print ("\t")
    coef = np.polyfit(x_axis_data, y_axis_data, polynomial_order)

    poly_term_no = len(coef)
    print (str(poly_term_no))
    print ("Polynomial coefficients: " + str(coef))

    # C.2) Defining the polynomial equation parameters for the terminal.
    R2 = "R\u00b2"
    sx2 = "x\u00b2"
    sx3 = "x\u00b3"
    sx4 = "x\u2074"
    sx5 = "x\u2075"
    rf = 6  # rounding factor

    # C.3) Defining the polynomial equation parameters for the output text file.
    # (not possible to use unicodes characters in a plain text file).
    R2p = "R2"
    sx2p = "x2"
    sx3p = "x3"
    sx4p = "x4"
    sx5p = "x5"

    r_squared = ccoef ** 2
    if polynomial_order == 1:
        print ("Polynomial order 1")
        c0 = str(round(coef[0], rf))

        input_coef = coef[1]
        (polycoef_expression) = coefficent_sign(input_coef, rf)
        c1 = polycoef_expression

        poly_eq = ("y = " + c0 + "x " + c1)
        print (poly_eq)
        print (R2 + "= " + str(round(r_squared, 4)) + ("(Linear R**2)"))
    
    # you will need to expand to other polynomial terms. 


# ------------------------------------------------------------------------------------------------------------
# 3) Creating the 2Dscatter plot with the points density
# ------------------------------------------------------------------------------------------------------------
print ("\t")
print ("-----------------------------------------------------------------------------------------------------")
print ((time.strftime("%H:%M:%S"))+"... Creating and saving the 2D scatterplot")
print("\t")

if  apply_sampling is True: 
    print ((time.strftime("%H:%M:%S")) + "...Data sampling for  faster rendering of the scatterplot density")
    print ("\t")
    sampling_factor = int(round (x_array_lenght / number_of_points, 0))
    print ("The Sampling factor is :  " + str(sampling_factor))
    # Numpy array slicing
    x_samp = x_axis_data[1::sampling_factor]
    y_samp = y_axis_data[1::sampling_factor]
    
    x_samp_lenght = len(x_samp)
    pct_of_original = round((x_samp_lenght/x_array_lenght) * 100, 2)

    print("   Original number of points: " + str(x_array_lenght))
    print("   Array size after sampling: " + str(x_samp_lenght))
    print("  Percentage of original: " + str (pct_of_original) + "%")
    
    x = x_samp
    y = y_samp
        
else: 
    x = x_axis_data
    y = y_axis_data


# Calculate the correlation coefficients of the sample arrays
sample_size = str(len(x))
ccoef = np.corrcoef(x, y)[0,1]
print ("  Correlation coefficient of sample data: " + str(ccoef))
print ("  Sampled data size: " + sample_size)

# Calculate the point density
print ("   " + (time.strftime("%H:%M:%S")) + "...Calculating the points density")
xy = np.vstack([x,y])
z = gaussian_kde(xy)(xy)
# Sort the points by density, so that the densest points are plotted last
idx = z.argsort()
x, y, z = x[idx], y[idx], z[idx]

print("   " + (time.strftime("%H:%M:%S")) + "...Creating and saving the output file")


figure, ax = plt.subplots()
ax.scatter(x, y, c=z, s=25)

if display_regression is True:
    plt.plot(np.unique(x), np.poly1d(np.polyfit(x, y, polynomial_order))(np.unique(x)), color='k', linewidth=1)

plt.grid(axis='x', alpha=0.5)
plt.grid(axis='y', alpha=0.5)
plt.title (plot_title, fontsize=12, weight="bold")
plt.xlabel (x_axis_name, fontsize=12)
plt.ylabel (y_axis_name, fontsize=12)
plt.xlim((0,15))
plt.ylim((0,15))
#
# Saving the plot as a PNG file
plt.tight_layout()
figure = plt.gcf()
figure.set_size_inches(10, 8)
plt.savefig(output_plot_name, dpi=300, facecolor='w', edgecolor='w',
            orientation='landscape', format=None, transparent=False,
            bbox_inches='tight', pad_inches=0.1, metadata=None)


if display_scatter_plot is True:
    plt.show()
# -------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------

print("----------------------------------------------------------------------------------------------------")
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