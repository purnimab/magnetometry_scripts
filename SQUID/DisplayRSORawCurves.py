# -*- coding: utf-8 -*-
import pylab as py
from matplotlib.widgets import Slider#, Button, RectangleSelector#, CheckButtons, RadioButtons
import sys
import numpy as np
import os.path

#READ IN ARGUMENTS - [filename] [measurement configuration - centering or not centering]
#LOAD FILE from a .rso.raw file
filename = sys.argv[1]
#check that it's a raw scan file
if os.path.split(filename)[1].count('rso.raw') == 0:
    print filename + " is not an RSO raw file"
    sys.exit(1)
#numPtsPerQuadrant = int(sys.argv[2])
#numQuadrants = int(sys.argv[3])
#print str(numPtsPerQuadrant) + ' points per quadrant * ' + str(numQuadrants) + ' quadrants'
filetypes = ['MvsT', 'MvsH']
#check file type - they have different orderings of columns
if filename.count('MvsT') > 0:
    filetype = 0
    print filetypes[filetype] + ' Sweep'
elif filename.count('MvsH') > 0:
    filetype = 1
    print filetypes[filetype] + ' Sweep'
#elif len(sys.argv) > 4:
#    filetype = int(sys.argv[-1] == 'MvsH') #check last item
#    print filetypes[filetype] + ' Sweep'
else:
    print filename + " is neither MvsH nor MvsT"
    sys.exit(1)

#centering mode does a centering scan before a measurement scan - only every other scan is valid
if len(sys.argv) > 2:
    centering = sys.argv[2] == 'centering'
else:
    centering = not filetype

#SEPARATE HEADER FROM DATA
headerline = ''
header = '' #header will be added to the beginning of any output files
nline = 0
inputfile = open(filename,'r')
while headerline != "[Data]\n":
    headerline = inputfile.readline()
    nline += 1
    header = header + headerline
columnLabels = inputfile.readline().strip().split(',') #list of columns, as formatted in the text file (with parentheses and spaces)
inputfile.close()

#READ IN DATA FILE, masked. Not all of them will be filled. The mask has values of True where data is missing
data = np.genfromtxt(filename, delimiter=',', skip_header=nline, names=True, usemask=True, dtype=None)
notmissing = np.logical_not(data.mask.view(bool).reshape(len(data),-1)) #turns the mask (an array of tuples) into a 2D array where True is a valid cell
#find empty columns
columnsWithData = np.logical_or.reduce(notmissing)

print "Reading " + filename
print "Columns with Data:"
print np.array(data.dtype.names)[columnsWithData]

s = data.shape
#determine number of points per IV curve
pointsPerCurve = 1
if filetype==0:
    while pointsPerCurve < s[0] and data['Start_Temperature_K'][pointsPerCurve] == data['Start_Temperature_K'][0]: #check same temperature value
        pointsPerCurve += 1
else:
    while pointsPerCurve < s[0] and data[pointsPerCurve]['Field_Oe'] == data[0]['Field_Oe']: #check same field value
        pointsPerCurve += 1
print str(pointsPerCurve) + " points per RSO curve"

#reshape IV curves so that the first index is the curve #, then each point in the curve, then temp, current, voltage, etc.
data.shape = (s[0]/pointsPerCurve, pointsPerCurve)
s = data.shape

#values for slider
tempindex = 0
minindex = 0
if centering:
    maxindex = s[0]/2-1
else:
    maxindex = s[0]-1

#create a figure
fig = py.figure(figsize=(20,15))
py.subplots_adjust(left=0.25, bottom=0.25)
py.hold(True)

#plot curves - called every time the IVcurve index is changed
def plotcurves(index):
    #pick out data for a specific temperature/field index
    #curve = data[index]
    
    #plot each curve
    if centering:
        curve = data[index*2+1] #centering - does two scans per real scan
    else:
        curve = data[index]
    py.subplot(1,1,1)
    py.cla()
    
    pos = list(curve['Position_cm'])
    v = list(curve['Long_Detrended_Voltage'])
    vfit = list(curve['Long_Detrended_Fit'])
    py.plot(pos, v, '.b-')
    py.plot(pos, vfit, '.r-')

    py.title('SQUID RSO Scan, Raw (b) and Fitted (r)')
    py.xlabel('Position (cm)')
    py.ylabel('Voltage (V)')
    
    py.suptitle(str(curve['Start_Temperature_K'][0])+" K, "+str(curve['Field_Oe'][0])+" Oe", size='x-large', x = .55, y = .2)
    py.draw()
    #py.hold(False)
plotcurves(tempindex)

#create a slider
axindex = py.axes([0.25, 0.1, 0.65, 0.03], axisbg='lightgoldenrodyellow')
sliderindex = Slider(axindex, 'Curve #', minindex, maxindex, valinit=tempindex, dragging=True, valfmt='%1.0f')

#when the slider value changes, the index of the IV curve also changes
def update(val):
    tempindex = round(sliderindex.val)
    if sliderindex.val != tempindex: #otherwise, set_val calls update, and you get infinite recursion
        sliderindex.set_val(tempindex)
    plotcurves(int(tempindex))
sliderindex.on_changed(update)

#bind left/right arrow keys to also change the index of the IV curve
def leftright(event):
    if event.key == 'left':
        if sliderindex.val > minindex:
            tempindex = sliderindex.val-1
            sliderindex.set_val(tempindex)
    elif event.key == 'right':
        if sliderindex.val < maxindex:
            tempindex = sliderindex.val+1
            sliderindex.set_val(tempindex)
arrows = fig.canvas.mpl_connect('key_release_event', leftright)

py.show()