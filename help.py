#!/usr/bin/env python 

if __name__== '__main__':            

    #set help message
    help = """
Usage: help  

TOOLS: 

  === Help ===
  ./help.py [[this file]]

  === Generate results and plot ===
  ./tokenspice.py [[Run TokenSPICE simulation. Input netlist. Output rundir w/ csv.]]
  ./plot_1.py [[Plot results from 1 run. Input csv. Output pngs.]]
  ./showstats.py [[Show performance statistics for a run]]
  Example flow: see bottom

  === Running tests === 
  pytest [[run all tests]]
  pytest engine/ [[run all tests in engine/ directory]]
  pytest tests/test_foo.py [[run a single pytest-based test file]]
  pytest tests/test_foo.py::test_foobar [[run a single pytest-based test]]

  === Config files, with params to change === 
  -System parameters: ~/tokenspice.conf
  -Logging: ./logging.conf

  == Example flow ==
  rm -rf outdir_csv; ./tokenspice.py mynetlist1.py outdir_csv 1>out.txt 2>&1 &
  tail -f out.txt
  rm -rf outdir_png; ./plot_1.py outdir_csv outdir_png
  eog outdir_png
"""
    print(help)
