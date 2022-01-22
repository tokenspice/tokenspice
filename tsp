#!/usr/bin/env python

import cProfile
import importlib
import logging
import pstats
import os
import sys

import brownie

if len(sys.argv) > 0 and sys.argv[1] == "ganache":
    os.system("./ganache.py")
    sys.exit(0)

from engine.SimEngine import SimEngine #pylint: disable=wrong-import-position
from util.plotutil import csvToPngs    #pylint: disable=wrong-import-position

INFO = logging.INFO
DEBUG = logging.DEBUG
WARNING = logging.WARNING

# ==========================================================================
# tsp help
HELP_MAIN = """
TokenSPICE - EVM agent-based token simulator
                                            
Usage: tsp run|plot|showstats
  tsp run -- run simulation
  tsp plot -- plot results
  tsp showstats -- see run stats
  tsp ganache -- run local chain
 """


# ========================================================================
# tsp run

HELP_RUN = """
Usage: tsp run NETLIST OUTPUT_DIR [DO_PROFILE]

 NETLIST -- string -- pathname for netlist
 OUTPUT_DIR -- string -- output directory for csv file.
 DO_PROFILE -- bool -- if True, profile. Otherwise don't. Defalt=False.
"""


def do_run():
    if len(sys.argv) not in [4, 5]:
        print(HELP_RUN)
        sys.exit(0)

    # extract inputs
    assert sys.argv[1] == "run"
    netlist_str = sys.argv[2]
    output_dir = sys.argv[3]
    do_profile = False
    if len(sys.argv) == 5 and sys.argv[4] == "True":
        do_profile = True

    print(
        f"Arguments: NETLIST={netlist_str}, OUTPUT_DIR={output_dir},"
        " DO_PROFILE={do_profile}"
    )

    # handle corner cases
    if os.path.exists(output_dir):
        print(f"\nOutput path '{output_dir}' already exists.  Exiting.\n")
        sys.exit(0)

    # make directory
    os.mkdir(output_dir)

    # go
    netlist_module = _importNetlistModule(netlist_str)
    netlist_state = netlist_module.SimState()
    netlist_log_func = netlist_module.netlist_createLogData


    engine = SimEngine(netlist_state, output_dir, netlist_log_func)
    if not do_profile:
        engine.run()
    else:
        stats_filename = os.path.join(output_dir, "stats")
        cProfile.run("engine.run()", stats_filename)
        print(
            f"Output stats file: {stats_filename}. To see: tsp showstats "
            "outdir_csv/stats 20 cumulative"
        )
    print(f"Output directory: {output_dir}")

    if brownie.network.is_connected():
        brownie.network.disconnect()


def _importNetlistModule(netlist_str: str):
    module_str = netlist_str.replace("/", ".").replace(".py", "")
    netlist_module = importlib.import_module(module_str)
    return netlist_module


# ==========================================================================
# tsp plot

HELP_PLOT = """
Usage: tsp plot NETLIST INPUT_CSV_DIR OUTPUT_PNG_DIR

 NETLIST -- string -- pathname for netlist
 INPUT_CSV_DIR -- string -- input directory for csv file. 
 OUTPUT_PNG_DIR -- string -- output directory for png files. Can't exist yet.
"""


def do_plot():
    # got the right number of args?  If not, output help
    if len(sys.argv) not in [5]:
        print(HELP_PLOT)
        sys.exit(0)

    # extract inputs
    assert sys.argv[1] == "plot"
    netlist_str = sys.argv[2]
    input_csv_dir = sys.argv[3]
    output_png_dir = sys.argv[4]

    #
    base_input_csv_filename = "data.csv"  # magic number. Set in engine/SimEngine.py
    input_csv_filename = os.path.join(input_csv_dir, base_input_csv_filename)

    print(
        f"Arguments: NETLIST={netlist_str}, INPUT_CSV_DIR={input_csv_dir}, "
        "OUTPUT_PNG_DIR={output_pngdir}"
    )
    print(f"Base input filename: '{base_input_csv_filename}' (hardcoded)")
    print(f"Full input filename: '{input_csv_filename}'")
    print()

    # corner cases
    if not os.path.exists(input_csv_dir):
        print(f"Input directory '{input_csv_dir}' does not exist. Exiting.")
        sys.exit(0)

    if not os.path.exists(input_csv_filename):
        print(f"Input filename '{input_csv_filename}' does not exist. Exiting.")
        sys.exit(0)

    if os.path.exists(output_png_dir):
        print(f"Output path '{output_png_dir}' already exists. Exiting.")
        sys.exit(0)

    # get netlist module
    netlist_module = _importNetlistModule(netlist_str)
    netlist_plot_instrs_func = netlist_module.netlist_plotInstructions

    # main work
    csvToPngs(input_csv_filename, output_png_dir, netlist_plot_instrs_func)

    print("Done")


# ========================================================================
# tsp showstats

HELP_SHOWSTATS = """
Usage: tsp showstats FILENAME NUM_SHOW SORT_BY 

 FILENAME -- string -- stats filename (including path)
 NUM_SHOW -- int -- only show the top 'NUM_SHOW' functions 
 SORT_BY -- string -- one of 'cumulative', 'time'
  cumulative -- cumulative time by a function and its callees. To understand what functions take the most time
  internal -- time spent *within* a function, but not callees. To understand what functions were looping a lot, and taking a lot of time.
  internal_callers -- which funcs called the ones above

Example: tsp showstats outdir_csv/stats 20 cumulative
"""


def do_showstats():
    if len(sys.argv) not in [5]:
        print(HELP_SHOWSTATS)
        sys.exit(0)

    # extract inputs
    assert sys.argv[1] == "showstats"
    filename = sys.argv[2]
    num_show = int(eval(sys.argv[3])) # pylint: disable=eval-used
    sort_by = sys.argv[4]

    print(f"Argument FILENAME: '{filename}'")
    print(f"Argument NUM_SHOW: '{num_show}'")
    print(f"Argument SORT_BY: '{sort_by}'")
    print()

    # corner cases
    if not os.path.exists(filename):
        print(f"Input file '{filename}' does not exist. Exiting.")
        sys.exit(0)
    if num_show < 1:
        print("Input NUM_SHOW is invalid. Exiting.")
        sys.exit(0)

    # do work
    # Note: assumes python3.6. Different in 3.7+.
    p = pstats.Stats(filename)

    print("=" * 80)
    if sort_by == "cumulative":
        print("Highest-impact by cumulative time in a function and its callees")
        print("=" * 80)
        p.sort_stats("cumulative").print_stats(num_show)

    elif sort_by == "internal":
        print("Highest-impact by time spent *within* a function")
        print("=" * 80)
        p.sort_stats("time", "cumulative").print_stats(num_show)

    elif sort_by == "internal_callers":
        print("Highest-impact by functions looping a lot _and_ taking time")
        print("=" * 80)
        p.sort_stats("time").print_stats(num_show).print_callers(num_show)

    else:
        print("Input sort_by is invalid. Exiting.")
        sys.exit(0)

    print("Done")


# ========================================================================
# main
def do_main():
    logging.basicConfig()
    logging.getLogger("master").setLevel(INFO)

    if len(sys.argv) == 1:
        print(HELP_MAIN)

    elif sys.argv[1] == "run":
        do_run()

    elif sys.argv[1] == "plot":
        do_plot()

    elif sys.argv[1] == "showstats":
        do_showstats()

    else:
        print(HELP_MAIN)


if __name__ == "__main__":
    do_main()
