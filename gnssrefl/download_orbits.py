# -*- coding: utf-8 -*-
"""
downloads RINEX files
kristine larson
2020sep03 - modified environment variable requirement
"""
import argparse
import gnssrefl.gps as g
import sys
import subprocess
import os
import wget

def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("orbit", help="orbit name (gps,gnss,gps+glo, or specific e.g. jax) ", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day", help="day (zero if you use day of year earlier)", type=int)
    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    orbit_list = ['igs', 'igr','jax','grg','wum','gbm','nav','gps','gps+glo','gnss','gfr','esa','gnss2','brdc','ultra','rapid']


#   assign to normal variables
    pCtr = args.orbit
    year = args.year
    month = args.month
    day = args.day

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

    if (day == 0):
        # then you are using day of year as input
        doy = month
        year,month,day=g.ydoy2ymd(year, doy) 
        doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day)
    else:
        doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day)


    if pCtr not in orbit_list:
        print('You picked an orbit type - ', pCtr, ' - that I do not recognize')
        print(orbit_list)
        sys.exit()

    # if generic names used, we direct people to these orbit types
    if pCtr == 'gps':
        pCtr = 'nav'

    # this is picked up from CDDIS
    if pCtr == 'gnss':
        pCtr = 'gbm'

    if pCtr == 'gps+glo':
        pCtr = 'jax'

    # using gfz multi-gnss for rapid
    if pCtr == 'rapid':
        pCtr = 'gfr'

    if pCtr == 'nav':
        navname,navdir,foundit = g.getnavfile(year, month, day) 
        if foundit:
            print('\n SUCCESS:', navdir+'/'+navname)
    else:
        if (pCtr == 'igs') or (pCtr == 'igr'):
            filename, fdir, foundit = g.getsp3file_flex(year,month,day,pCtr)
        else:
            if pCtr == 'esa':
                    # this is ugly - but hopefully will work for now.  
                filename, fdir, foundit = g.getsp3file_flex(year,month,day,pCtr)
            elif pCtr == 'gfr':
            # rapid GFZ is available again ... 
                filename, fdir, foundit = g.rapid_gfz_orbits(year,month,day)
            # also at GFZ
            elif pCtr == 'ultra':
                hour = 0 # for now
                filename, fdir, foundit = g.ultra_gfz_orbits(year,month,day,hour)
            elif (pCtr == 'gnss2'):
                # use IGN instead of CDDIS
                filename,fdir,foundit = g.avoid_cddis(year,month,day)
            elif (pCtr == 'brdc'):
                # https://cddis.nasa.gov/archive/gnss/data/daily/2021/brdc/
                # test code to get rinex 3 broadcast file
                # will not store it in ORBITS because it is not used explicitly
                # this is not operational as yet
                filename,fdir,foundit = g.rinex3_nav(year,month,day)
            else:
                filename, fdir, foundit = g.getsp3file_mgex(year,month,day,pCtr)
        if foundit:
            print('SUCCESS:', fdir+'/'+filename )
        else:
            print(filename , ' not found')



if __name__ == "__main__":
    main()
