#!/usr/bin/env python 

import copy
import matplotlib
from matplotlib import pyplot
import numpy
import os
from pylab import figure, axes, pie, title, show
import sys
from typing import Any

from util.constants import * #S_PER_YEAR etc

def listToFloat(x_array):
    return [float(x_item) for x_item in x_array]

def applyMult(y, mult):
    if mult == MULT1:
        return y
    elif mult == MULT100:
        return list(numpy.array(y) * 100.0)
    elif mult == DIV1M:
        return list(numpy.array(y) / 1e6)
    elif mult == DIV1B:
        return list(numpy.array(y) / 1e9)
    else:
        raise ValueError(mult)

def multUnitStr(mult, unit):
    if mult == MULT1 and unit == DOLLAR:
        return "$"
    elif mult == DIV1M and unit == DOLLAR:
        return "$M"
    elif mult == DIV1M and unit == COUNT:
        return "count, in millions"
    elif mult == DIV1B and unit == DOLLAR:
        return "$B"
    elif mult == DIV1B and unit == COUNT:
        return "count, in billions"
    elif mult == MULT100 and unit == PERCENT:
        return "%"
    else:
        raise ValueError(f"can't handle mult={mult} with unit={unit}")
    return

if __name__== '__main__':    
    
    #set help message
    help = """
Usage: plot_1 INPUT_DIR

 INPUT_DIR -- string -- input directory for csv file. 
 OUTPUT_DIR -- string -- output directory for png files. Can't exist yet.
 """

    #got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = [2]
    if num_args not in num_args_needed:
        print(help)
        if num_args > 0:
            print(f"Got {num_args} argument(s), need {num_args_needed}.\n")
        sys.exit(0)
    
    #extract inputs
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    base_input_filename = "data.csv" #magic number. Set in engine/SimEngine.py
    full_input_filename = os.path.join(input_dir, base_input_filename)

    print(f"Argument INPUT_DIR: '{input_dir}'")
    print(f"Argument OUTPUT_DIR: '{output_dir}'")
    print(f"Base input filename: '{base_input_filename}' (hardcoded)")
    print(f"Full input filename: '{full_input_filename}'")
    print()

    #corner cases
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist. Exiting.")
        sys.exit(0)
        
    if not os.path.exists(full_input_filename):
        print(f"Input filename '{full_input_filename}' does not exist. Exiting.")
        sys.exit(0)
        
    if os.path.exists(output_dir):
        print(f"Output path '{output_dir}' already exists. Exiting.")
        sys.exit(0)

    #create output dir
    os.mkdir(output_dir)

    #====================================
    #do work
    import csv
    header: Any = None
    values: Any = []
    with open(full_input_filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader: #row = ['Tick', 'Second', ..] or [1.0, 100.0, ..]
            if header is None:
                header = row
                header = [param.strip() for param in header]
            else:
                values.append(row)
    values = numpy.array(values) #[tick_i, valuetype_i]

    #header has these columns (as strs): {Tick, Second, Month, Year, Num_mkts}
    # and *many* more: see what gets added to 'dataheader' in SimEngine.createLogData().

    #plot
    x = listToFloat(values[:,header.index("Year")])

    #what to plot: (name in header, name for plot)
    LINEAR, LOG, BOTH = 'linear', 'log', 'both' #pyplot.yscale interprets 1st 2
    MULT1, MULT100, DIV1M, DIV1B = 0, 1, 2, 3 #multiply or divide the value?
    COUNT, DOLLAR, PERCENT = "#", "$", "%" #units
    class Param:
        def __init__(self, y_header_names, labels, y_pretty_name, y_scale, mult, unit):
            self.y_header_names = y_header_names # list[str]
            self.labels = labels #list[str]
            self.y_pretty_name = y_pretty_name #str
            self.y_scale = y_scale #one of LINEAR, ..
            self.mult = mult #one of MULT1, ..
            self.unit = unit #one of COUNT, ..
            
    y_params = [
        Param(["OCEAN_price"], [""], "OCEAN Price", LOG, MULT1, DOLLAR),
        #Param(["ocean_rev_growth/yr"], [""], "Annual Ocean Revenue Growth", BOTH, MULT100, PERCENT),
        Param(["overall_valuation", "fundamentals_valuation","speculation_valuation"],
              ["Overall", "Fundamentals (P/S=30)", "Speculation"], "Valuation", LOG, DIV1M, DOLLAR),
        Param(["dao_USD/mo", "dao_OCEAN_in_USD/mo", "dao_total_in_USD/mo"],
              ["Income as USD (ie network revenue)", "Income as OCEAN (ie from 51%; priced in USD)", "Total Income"],
              "Monthly OceanDAO Income", LOG, DIV1M, DOLLAR),
        Param(["ocean_rev/yr","allmkts_rev/yr"], ["Ocean", "All marketplaces"],
              "Annual Revenue", LOG, DIV1M, DOLLAR),
        Param(["tot_OCEAN_supply", "tot_OCEAN_minted", "tot_OCEAN_burned"],
              ["Total supply","Tot # Minted","Tot # Burned"], "OCEAN Token Count", BOTH, DIV1M, COUNT),
        Param(["OCEAN_minted/mo", "OCEAN_burned/mo"], ["# Minted/mo", "# Burned/mo"],
              "Monthly # OCEAN Minted & Burned", BOTH, DIV1M, COUNT),
        Param(["rnd_to_sales_ratio", "mkts_annual_growth_rate"], ["R&D/sales ratio", "Marketplaces annual growth rate"],
              "R&D/Sales Ratio and Marketplaces Growth Rate", BOTH, MULT100, PERCENT),
        Param(["RND/mo"], [""], "Monthly R&D Spend", BOTH, DIV1M, DOLLAR),
        
        # Param(["OCEAN_burned_USD/mo", "OCEAN_minted_USD/mo"],
        #       ["$ of OCEAN Burned/mo", "$ of OCEAN Minted/mo"],
        #       "Monthly OCEAN (in USD) Minted & Burned", LOG, DIV1M, DOLLAR),
        # Param(["OCEAN_burned_USD/mo", "ocean_rev/mo", "allmkts_rev/mo"],
        #       ["$ OCEAN Burned monthly", "Ocean monthly revenue", "Marketplaces monthly revenue"],
        #       "Monthly OCEAN Burned & Revenues", LOG, DIV1M, DOLLAR),
    ]

    #replace BOTH with 2 entries
    y_params2 = []
    for p in y_params:
        if p.y_scale in [LINEAR, BOTH]:
            p2 = copy.copy(p)
            p2.y_scale = LINEAR
            y_params2.append(p2)
        if p.y_scale in [LOG, BOTH]:
            p2 = copy.copy(p)
            p2.y_scale = LOG
            y_params2.append(p2)
    y_params = y_params2

    #===========================================================
    #main loop to create pngs
    for p in y_params:
        ys = [listToFloat(values[:,header.index(name)])
              for name in p.y_header_names]

        ys = [applyMult(y, p.mult) for y in ys]

        fig, ax = pyplot.subplots()
        
        ax.set_xlabel("Year")
        
        for y, label in zip(ys, p.labels):
            if label == "":
                ax.plot(x, y)
            else:
                ax.plot(x, y, label=label)
        if len(p.labels) > 1:
            ax.legend()

        mult_unit_s = multUnitStr(p.mult, p.unit)
        ax.set_ylabel(f"{p.y_pretty_name} ({mult_unit_s})")
        
        ax.set_title(f"{p.y_pretty_name}" + f" ({p.y_scale})")
        
        pyplot.yscale(p.y_scale)
        
        if p.y_scale == LOG: #turn off exponential notation 
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

        ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2g'))
        max_y = max([max(y) for y in ys])
        if max_y < 1000.0:
            ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2f'))
        
        max_x = max(10, math.ceil(max(x)))
        if max_x < 12:
            xticks = list(range(max_x+1))
        elif max_x < 22:
            xticks = [i for i in range(max_x+1) if (i%2)==0]
        elif max_x < 52:
            xticks = [i for i in range(max_x+1) if (i%5)==0]
        elif max_x < 152:
            xticks = [i for i in range(max_x+1) if (i%10)==0]
        elif max_x < 202:
            xticks = [i for i in range(max_x+1) if (i%20)==0]
        pyplot.xticks(xticks)

        #pyplot.show() #popup

        base_output_filename = f"{p.y_pretty_name}_{p.y_scale}.png".replace('/',"_per_").replace(" ","_").replace(",","_").replace("'","").replace("__","_")
        full_output_filename = os.path.join(output_dir, base_output_filename)
        pyplot.savefig(full_output_filename,bbox_inches='tight') 
        print(f"Created '{full_output_filename}'")


    #===========================================================
    print("Done")
