
import time
import sys
import pci
from pci.exceptions import PCIException
from pci.api import datasource as ds
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# ----------------------------------------------------------------------------------------------------------------------
# User defined variables
# ----------------------------------------------------------------------------------------------------------------------

input_file = r'D:\test_python\test3_WorldView_DSM_vs_Glo30DEM.pix'
x_axis_chan = 1
y_axis_chan = 3

polynomial_order = 1

#  save_scatterplot is "yes" or "no"
save_scatterplot = "yes"
output_figure_name = 'D:\test_python\WV_glo30dem.png'
x_axis_name = 'WorldView-3 raw DSM (meters)'
y_axis_name = 'GLO-30 DEM , resampled at 1m (meters)'

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
# Main program
# Hard coded values
# Number of samples for displaying and saving data. 10 000 samples is fast.
num_samples = 20000

yes_validation_list = ["yes","y","yys","yse","yee","yss","ys"]

if save_scatterplot.lower() not in yes_validation_list:
    display_figure = False
    print ("Output scatter plot figure won't be saved and displayed")
else:
    print ("Output scatter plot figure will be saved and displayed")
    display_figure = True

# ----------------------------------------------------------------------------------------------------------------------
# B) Read the input file
# ----------------------------------------------------------------------------------------------------------------------
# Read the input channels and convert to numpy array - exclude the NoData values.
print("\t")
print((time.strftime("%H:%M:%S"))+"... Reading the input file")

with ds.open_dataset(input_file) as ds1:

    # Read raster data
    reader = ds.BasicReader(ds1)
    raster = reader.read_raster(0, 0, reader.width, reader.height)

    # (Indexation) starts at 0, not 1. PIX channel 3 is 2
    x_chan = x_axis_chan - 1
    x_axis_data = raster.data[:, :, x_chan]
    x_axis_data = x_axis_data.reshape(-1)

    y_chan = y_axis_chan - 1
    y_axis_data = raster.data[:, :, y_chan]
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
    print ("Final number of samples: " + str(x_array_lenght) + "("+ final_samples_pct +"%)")


# ----------------------------------------------------------------------------------------------------------------------
# C) Computing the correlation coefficient and polynomial terms on the original data
# ----------------------------------------------------------------------------------------------------------------------
print ("\t")
print ("--------------------------------------------------------------------------------------------------------------")
print ((time.strftime("%H:%M:%S"))+"...Computing the correlation coefficient and polynomial terms on the original data")
print ("\t")

# C.1) Defining the polynomial equation parameters.
sample_size = str(len(x_axis_data))
ccoef = np.corrcoef(x_axis_data, y_axis_data)[0,1]
print ("Correlation coefficient: " + str(ccoef))
print ("Number of samples: " + sample_size)

print ("Computing the polynomial terms...")
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

# ----------------------------------------------------------------------------------------------------------------------
# D) Creating the scatter plot with the points density
# ----------------------------------------------------------------------------------------------------------------------
if display_figure is True:
    print ("\t")
    print ("----------------------------------------------------------------------------------------------------------")
    print ((time.strftime("%H:%M:%S"))+"...Creating and saving the scatterplot")
    print("\t")

    # It's mandatory to sample the data to avoid very long computing time
    print ((time.strftime("%H:%M:%S")) + "...Data sampling for computing the scatterplot density")
    sampling_factor = int(round (x_array_lenght / num_samples, 0))
    print ("Sampling factor is :  " + str(sampling_factor))
    # Numpy array slicing
    x_samp = x_axis_data[1::sampling_factor]
    y_samp = y_axis_data[1::sampling_factor]
    len_samp = str (len(x_samp))
    print ("  Array size after sampling: " + len_samp)
    x = x_samp
    y = y_samp

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
    plt.plot(np.unique(x), np.poly1d(np.polyfit(x, y, polynomial_order))(np.unique(x)), color='k', linewidth=1)
    plt.grid(axis='x', alpha=0.5)
    plt.grid(axis='y', alpha=0.5)
    plt.xlabel (x_axis_name, fontsize=12)
    plt.ylabel (y_axis_name, fontsize=12)
    # Saving the plot to a PNG file

    plt.tight_layout()
    figure = plt.gcf()
    figure.set_size_inches(10, 8)
    plt.savefig(output_figure_name, dpi=300, facecolor='w', edgecolor='w',
                orientation='landscape', format=None, transparent=False,
                bbox_inches='tight', pad_inches=0.1, metadata=None)


    plt.show()

print("----------------------------------------------------------------")
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