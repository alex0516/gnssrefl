#
# Author: Kristine M. Larson
# Date: august 25, 2020
# Purpose: help set up json input file needed for gnssIR_lomb.py

import argparse
import json
import os
import subprocess
import sys

import gnssrefl.gps as g

def main():

# user inputs the observation file information
    parser = argparse.ArgumentParser()
# required arguments
    parser.add_argument("station", help="station (lowercase)", type=str)
    parser.add_argument("lat", help="latitude (degrees)", type=float)
    parser.add_argument("long", help="longitude (degrees)", type=float)
    parser.add_argument("height", help="ellipsoidal height (meters)", type=float)
# these are the optional inputs 
    parser.add_argument("-e1", default=None, type=int, help="lower limit elevation angle (deg)")
    parser.add_argument("-e2", default=None, type=int, help="upper limit elevation angle (deg)")
    parser.add_argument("-h1", default=None, type=float, help="lower limit reflector height (m)")
    parser.add_argument("-h2", default=None, type=float, help="upper limit reflector height (m)")
    parser.add_argument("-nr1",default=None, type=float, help="lower limit noise region for QC(m)")
    parser.add_argument("-nr2",default=None, type=float, help="upper limit noise region for QC(m)")
    parser.add_argument("-peak2noise", default=None, type=float, help="peak to noise ratio used for QC")
    parser.add_argument("-ampl", default=None, type=float, help="required spectral peak amplitude for QC")
    parser.add_argument("-allfreq", default=None, type=str, help="set to True to include all GNSS")
    parser.add_argument("-l1", default=None, type=str, help="set to True to only use GPS L1")
    parser.add_argument("-l2c", default=None, type=str, help="set to True to only use GPS L2C")
    parser.add_argument("-xyz", default=None, type=str, help="set to True if using Cartesian coordinates")
    parser.add_argument("-refraction", default=None, type=str, help="Set to False to turn off refraction correction")
    parser.add_argument("-extension", default=None, type=str, help="Provide extension name so you can try different strategies")
    parser.add_argument("-query_unr", default=None, type=str, help="set to True if you want to use the Nevada Reno database values (enter 0,0,0 for lat/lon/ht)")
    args = parser.parse_args()
#

# make sure environment variables exist
    g.check_environ_variables()

# rename the user inputs into variables
#
    station = args.station
    NS = len(station)
    if (NS != 4):
        print('station name must be four characters long. Exiting.')
        sys.exit()

# location of the site - does not have to be very good.  within 100 meters is fine
    Lat = args.lat
    Long = args.long
    Height = args.height

    if args.xyz == 'True':
        xyz = [Lat, Long, Height]
        Lat,Long,Height = g.xyz2llhd(xyz)

    if args.query_unr == 'True':
        # try to find the default coordinates 
        #Lat, Long, Height = g.queryUNR(station)
        # updated to new database
        Lat, Long, Height = g.queryUNR_modern(station)
        if (Lat == 0):
            print('Tried to find coordinates in our UNR database. Not found so exiting')
            sys.exit()

# start the lsp dictionary
    lsp={}
    lsp['station'] = station
    lsp['lat'] = Lat; lsp['lon'] = Long; lsp['ht']=Height

#   spectral peak amplitude
    if args.ampl == None:
        reqA = 6.0
    else:
        reqA = args.ampl 

# reflector height (meters)
    if (args.h1 != None):
        h1 = args.h1
    else:
        h1=0.5

    if (args.h2 != None):
        h2 = args.h2
    else:
        h2=6.0
#
    if (h1 > h2):
        print('h1 cannot be greater than h2. ', h1, h2, ' Exiting.')
        sys.exit()

    lsp['minH'] = h1; lsp['maxH'] = h2

# elevation angles (degrees)
    if (args.e1 != None):
        e1 = args.e1
    else:
        e1 = 5

    if (args.e2 != None):
        e2 = args.e2
    else:
        e2 = 25
    lsp['e1'] = e1; lsp['e2'] = e2

# the default noise region will the same as the RH exclusion area for now
    nr1=h1 
    nr2=h2
    if (args.nr1 != None):
        nr1 = args.nr1
    if (args.nr2 != None):
        nr2 = args.nr2
#
    lsp['NReg'] = [nr1, nr2]

    if (args.peak2noise == None):
        lsp['PkNoise'] = 2.7  # just a starting point for water - should be 3 or 3.5 for snow ... 
    else:
        lsp['PkNoise'] = args.peak2noise  

# where the instructions will be written
    xdir = os.environ['REFL_CODE']
    outputdir  = xdir + '/input' 
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir',outputdir])

    if args.extension == None:
        outputfile = outputdir + '/' + station + '.json'
    else:
        outputfile = outputdir + '/' + station + '.' + args.extension + '.json'


    lsp['polyV'] = 4 ; # polynomial order for DC removal
    lsp['pele'] = [5, 30] # elevation angles used for DC removal
    lsp['ediff']= 2 ; # degrees
    lsp['desiredP']= 0.005 ; # precision of RH in meters
# azimuth regions in degrees (in pairs)
# you can of course have more subdivisions here
    lsp['azval'] = [0, 90 , 90 ,180 , 180 , 270 , 270 , 360] 
# 
#   default frequencies to use - and their required amplitudes. The amplitudes are not set in stone
    # this is the case for only GPS, but the good L2 
    lsp['freqs'] = [1, 20, 5]; lsp['reqAmp'] = [reqA, reqA,reqA]
    if args.allfreq == 'True':
        # 307 was making it crash.  did not check as to why
        # includes glonass, galileo, and beidou
        lsp['freqs'] = [1, 20, 5, 101, 102, 201, 205, 206,207,208,302, 306]; 
        lsp['reqAmp'] =[ reqA,reqA,reqA,reqA,reqA,reqA, reqA,reqA,reqA,reqA,reqA,reqA ]

    if args.l1 == 'True':
        lsp['freqs'] = [1]
        lsp['reqAmp'] = [reqA]

    if args.l2c == 'True':
        lsp['freqs'] = [20]
        lsp['reqAmp'] = [reqA]

    lsp['refraction'] = True
    if args.refraction == 'False':
        lsp['refraction'] = False

# write new RH results  each time you run the code
    lsp['overwriteResults'] = True; 

# if snr file does not exist, try to make one
    lsp['seekRinex'] = False; 

# compress snr files after analysis - saves disk space
    lsp['wantCompression'] = False; 

# periodogram plots come to the screen
    lsp['plt_screen'] = False; 

# command line req to only do a single satellite - default is do all satellites
    lsp['onesat'] = None; 

# default will now be False ....
# send some information on periodogram RH retrievals to the screen
    lsp['screenstats'] = False

# save the output plots
    lsp['pltname'] = station + '_lsp.png'

# how long can the arc be, in minutes 
    lsp['delTmax'] = 75 # - this is appropriate for 5-30 degrees
 
    print('writing out to:', outputfile)
    with open(outputfile, 'w+') as outfile:
        json.dump(lsp, outfile,indent=4)

if __name__ == "__main__":
    main()
