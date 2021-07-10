#!/usr/bin/env python 

import logging
import os
import sys

INFO = logging.INFO
DEBUG = logging.DEBUG
WARNING = logging.WARNING

if __name__== '__main__':            
    #set up logging
    logging.basicConfig()
    
    logging.getLogger('master').setLevel(INFO) #INFO, DEBUG
    
    #set help message
    help = """
Usage: tsp NETLIST OUTPUT_DIR [DO_PROFILE]

 NETLIST -- string -- pathname for netlist
 OUTPUT_DIR -- string -- output directory for csv file.
 DO_PROFILE -- bool -- if True, profile. Otherwise don't. Defalt=False.
 """

    #got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = [2, 3]
    if num_args not in num_args_needed:
        print(help)
        if num_args > 0:
            print("Got %d argument(s), need %s.\n" % (num_args, num_args_needed))
        sys.exit(0)
    
    #extract inputs
    netlist = sys.argv[1]
    output_dir = sys.argv[2]
    do_profile = False
    if num_args == 3 and sys.argv[3] == 'True':
        do_profile = True

    print("Arguments: NETLIST=%s, OUTPUT_DIR=%s, DO_PROFILE=%s\n" %
          (netlist, output_dir, do_profile))

    #handle corner cases
    if os.path.exists(output_dir):
        print("\nOutput path '%s' already exists.  Exiting.\n" % output_dir)
        sys.exit(0)

    # make directory
    os.mkdir(output_dir)

    # initialize state from netlist file
    from netlist.Web3SustLoopNoEvm import SimState #FIXME: replace w import netlist
    state = SimState()
    
    #go
    from engine.SimEngine import SimEngine
    master = SimEngine(state, output_dir)
    if not do_profile:
        master.run()
    else:
        import cProfile
        stats_filename = os.path.join(output_dir, 'stats')
        cProfile.run('master.run()', stats_filename)
        print(f'Output stats file: {stats_filename}. To see: ./showstats.py outdir_csv/stats 20 cumulative')
    print(f'Output directory: {output_dir}')
