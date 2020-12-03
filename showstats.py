#!/usr/bin/env python 

import copy
import numpy
import os
import sys

from util.constants import * #S_PER_YEAR etc

if __name__== '__main__':    
    
    #set help message
    help = """
Usage: showstats.py FILENAME NUM_SHOW SORT_BY 

 FILENAME -- string -- stats filename (including path)
 NUM_SHOW -- int -- only show the top 'NUM_SHOW' functions 
 SORT_BY -- string -- one of 'cumulative', 'time'
  cumulative -- cumulative time by a function and its callees. To understand what functions take the most time
  internal -- time spent *within* a function, but not callees. To understand what functions were looping a lot, and taking a lot of time.
  internal_callers -- which funcs called the ones above

Example: ./showstats.py outdir_csv/stats 20 cumulative
 """

    #got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = [3]
    if num_args not in num_args_needed:
        print(help)
        if num_args > 0:
            print(f"Got {num_args} argument(s), need {num_args_needed}.\n")
        sys.exit(0)
    
    #extract inputs
    filename = sys.argv[1]
    num_show = int(eval(sys.argv[2]))
    sort_by = sys.argv[3]

    print(f"Argument FILENAME: '{filename}'")
    print(f"Argument NUM_SHOW: '{num_show}'")
    print(f"Argument SORT_BY: '{sort_by}'")
    print()

    #corner cases
    if not os.path.exists(filename):
        print(f"Input file '{filename}' does not exist. Exiting.")
        sys.exit(0)
    if num_show < 1:
        print(f"Input NUM_SHOW is invalid. Exiting.")
        sys.exit(0)
        
    #====================================
    #do work
    # Note: assumes python3.6. Different in 3.7+.

    import pstats
    p = pstats.Stats(filename)

    print('=' * 80)
    if sort_by == 'cumulative':
        print('Highest-impact by cumulative time in a function and its callees')
        print('=' * 80)
        p.sort_stats('cumulative').print_stats(num_show) 

    elif sort_by == 'internal':
        print('Highest-impact by time spent *within* a function')
        print('=' * 80)
        p.sort_stats('time', 'cumulative').print_stats(num_show)
        
    elif sort_by == 'internal_callers':
        print('Highest-impact by functions looping a lot _and_ taking time')
        print('=' * 80)
        p.sort_stats('time').print_stats(num_show).print_callers(num_show)
        
    else:
        print(f"Input sort_by is invalid. Exiting.")
        sys.exit(0)
        
    #===========================================================
    print("Done")
