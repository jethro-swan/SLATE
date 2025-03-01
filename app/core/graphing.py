#!/home/john/NESTS/SLATE/venv/bin/python3
# -*- coding: utf-8 -*-
#
#  islands.py
#
#  Copyright 2023 John Waters <john.waters@lrc.org.uk>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.


#===============================================================================
# This is a ridiculously simple script to generate payments between two
# randomly-selected agents. The payments may be either fixed at 1 (the default)
# or randomly-generated within a defined range.
#
# All agents have access to a default money ("legal tender" - LT) usable between
# any of them. This is what they have to use unless they share access to an
# island money.
#
# In this simulation, there may be up to 10,000 agents (100 by default, numbered
# 0 to 99) and up to 9 "island" monies (1, 4 or 9, excluding the LT "island 0").
#
# For the sake of simplicity, the monies (including LT) are identified by the
# 10s digit (0 being LT). However, the method of distinction is arbitrary and
# other options may be added in due course.

import datetime, time
import os
import shutil
import random
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

colours = [
    "#000000",
    "#ff0000",
    "#ff7f00",
    "#ffff00",
    "#00ff00",
    "#0000ff",
    "#4b0082",
    "#8f00ff",

]





# os.system("dot -Tpng " + gvfile2 + " -o " + gpath)







#-------------------------------------------------------------------------------
#
script_version          = "0.30"

about = "\n" \
+ "This script can be run in any directory. By default, it creates ./gv/\n" \
+ "and ./output/ in the directory from which it is run, but those\n" \
+ "subdirectories can be created in any writeable directory by using the -D\n" \
+ "option, e.g.\n" \
+ "\t./islands -D /var/omsim/islands/\n" \
+ "\n" \
+ "The default values are\n" \
+ "- number of payments\t= 10,000\n" \
+ "- number of agents\t= 100\n" \
+ "- number of islands\t= 10\n" \
+ "(where legal tender is treated as island 0).\n" \
+ "These values can be overridden using the following options:\n" \
+ "  -p <number of payments>\n" \
+ "  -a <number of agents>\n" \
+ "     (allowed values: 20, 50, 100, 200, 500, 1000, 2000, 5000 or 10000)\n" \
+ "  -i <number of islands>\n" \
+ "     (allowed values: 2, 5 or 10)\n" \
+ "\n" \
+ "  -B    causes the balance charts to be drawn\n" \
+ "  -G    causes the payments graphs to be drawn\n" \
+ "\n" \
+ "By default, legal tender (island 0) is not included when plotting the\n" \
+ "payment graphs. Otherwise, for anything other than a relatively small\n" \
+ "number of agents, the resulting graph would be excessively large (and\n" \
+ "possibly beyond GraphViz\"s capability to handle). This can be included\n" \
+ "by using the -C option.\n" \
+ "\n" \
+ "  -S  causes the output to be plotted as SVG rather than PNG.\n" \
+ "\n" \
+ "By default, there is one single run of payments, but this can be\n" \
+ "overridden to plot both the balance charts and the payments graphs at\n" \
+ "fixed interval (which must by an integral divisor of the total number of\n" \
+ "payments) using the -P option:\n" \
+ "    -P <number of steps>\n" \
+ "This causes the balance charts or payments graphs for all islands to be\n" \
+ "drawn at regular intervals. This is generally more useful for displaying\n" \
+ "the progressive development/completion of the islands\" networks, but\n" \
+ "may also be helpful in illustrating the proressive smoothing of the\n" \
+ "balance distributions over time, particularly where the payments values\n" \
+ "are selected randomly rather than being fixed at 1.\n" \
+ "\n" \
+ "By default, all payments have a fixed size (1). This can be overridden\n" \
+ "using the -R option to force it to generate random payments (always\n" \
+ "integers) between 1 and and an upper limit N, e.g.\n" \
+ "    -R <random payment limit>\n" \
+ "\n" \
+ "The -W causes creation of an HTML graph/chart page for each step.\n" \
+ "\n" \
+ "If the -V option is used, the script will provide a running commentary\n" \
+ "in the terminal, explaining what it is doing and where it is putting\n" \
+ "things.\n" \
+ "\n" \
+ "If the -E option is used, the script will provide output the payments\n" \
+ "(one per line) to STDOUT. This overrides the -V option.\n" \
+ "\n" \
+ "The -h option summarizes the available options.\n" \
+ "\n" \
+ "All output goes to the ./output/ folder (unless overridden by -D). Here,\n" \
+ "each run of the script creates a subdirectory with a name in the form\n" \
+ "    YYYY-MM-DD_hhmmss\n" \
+ "e.g.\n" \
+ "    ./output/2023-03-13_210132/\n" \
+ "under which it creates one or more "step" subdirectories (00/ at least)\n" \
+ "each of which contains the balances/ and graphs/ subdirectories.\n" \
+ "\n" \
+ "For example, typical output (in this case for a run with 5 islands and 5\n" \
+ "steps) looks like:\n" \
+ "\n" \
+ " ./islands -V -p 10000 -a 100 -i 5 -G -P 5\n" \
+ "  ------------------------------------------------------------\n" \
+ "      Number of payments:\t10000\n" \
+ "      Number of agents:\t\t100\n" \
+ "      Number of islands:\t5\n" \
+ "      Agents on each island:\t20\n" \
+ "      Include LT graph:\t\tFalse\n" \
+ "      Plot payment graphs:\tTrue\n" \
+ "      Plot graphs as SVG:\tFalse\n" \
+ "      Show balance plots:\tFalse\n" \
+ "      Show progress in:\t\t5 steps\n" \
+ "      Data directory: \t\t.\n" \
+ "      Random payment limit:\t1\n" \
+ "  ------------------------------------------------------------\n" \
+ "  10000 payments in 5 steps\n\n" \
+ "      island 1  : ./output/2023-03-13_210132/00/graphs/1_graph.png\n" \
+ "      island 2  : ./output/2023-03-13_210132/00/graphs/2_graph.png\n" \
+ "      island 3  : ./output/2023-03-13_210132/00/graphs/3_graph.png\n" \
+ "      island 4  : ./output/2023-03-13_210132/00/graphs/4_graph.png\n\n" \
+ "      island 1  : ./output/2023-03-13_210132/01/graphs/1_graph.png\n" \
+ "      island 2  : ./output/2023-03-13_210132/01/graphs/2_graph.png\n" \
+ "      island 3  : ./output/2023-03-13_210132/01/graphs/3_graph.png\n" \
+ "      island 4  : ./output/2023-03-13_210132/01/graphs/4_graph.png\n\n" \
+ "      island 1  : ./output/2023-03-13_210132/02/graphs/1_graph.png\n" \
+ "      island 2  : ./output/2023-03-13_210132/02/graphs/2_graph.png\n" \
+ "      island 3  : ./output/2023-03-13_210132/02/graphs/3_graph.png\n" \
+ "      island 4  : ./output/2023-03-13_210132/02/graphs/4_graph.png\n\n" \
+ "      island 1  : ./output/2023-03-13_210132/03/graphs/1_graph.png\n" \
+ "      island 2  : ./output/2023-03-13_210132/03/graphs/2_graph.png\n" \
+ "      island 3  : ./output/2023-03-13_210132/03/graphs/3_graph.png\n" \
+ "      island 4  : ./output/2023-03-13_210132/03/graphs/4_graph.png\n\n" \
+ "      island 1  : ./output/2023-03-13_210132/04/graphs/1_graph.png\n" \
+ "      island 2  : ./output/2023-03-13_210132/04/graphs/2_graph.png\n" \
+ "      island 3  : ./output/2023-03-13_210132/04/graphs/3_graph.png\n" \
+ "      island 4  : ./output/2023-03-13_210132/04/graphs/3_graph.png\n\n"

#-------------------------------------------------------------------------------
# Defaults:
default_n_passes        = 10000
max_graph_passes        = 10000
options_n_agents        = ["20", "50", "100",
                           "200", "500", "1000",
                           "2000", "5000", "10000"
                          ]
default_n_agents        = 100
options_n_islands       = ["2","5","10"] # including LT (island 0)
default_n_islands       = 10
default_lt_graph        = False
default_plot_graphs     = False
default_plot_svg        = False
default_plot_balances   = False
default_plot_histograms = False
default_plot_lorenz     = False
default_export_csv      = False
default_about_islands   = False
default_data_dir        = ""             # default is the local directory


#-------------------------------------------------------------------------------
# Set command line options:

ap = argparse.ArgumentParser(description="Simulate island monies")
ap.add_argument("-p", "--number-of-passes", dest="n_passes", action="store",
                help="number of passes", default=str(default_n_passes))
ap.add_argument("-a", "--number-of-agents", dest="n_agents", action="store",
                help="number of agents",
                choices=options_n_agents, default=str(default_n_agents))
ap.add_argument("-i", "--number-of-islands",dest="n_islands", action="store",
                help="number of islands",
                choices=options_n_islands, default=str(default_n_islands))
ap.add_argument("-C", "--include-lt-graph",
                dest="lt_graph", action="store_true", default=default_lt_graph,
                help="include plot of LT graph")
ap.add_argument("-G", "--plot_graphs", dest="plot_graphs", action="store_true",
                help="plot graphs", default=default_plot_graphs)
ap.add_argument("-S", "--plot-svg", dest="plot_svg", action="store_true",
                default=default_plot_svg,
                help="plot graph as SVG (default is PNG)")
ap.add_argument("-B", "--plot-balance-distribution",dest="plot_balances",
                action="store_true", default=default_plot_balances,
                help="plot balance distribution")
#ap.add_argument("-I", "--import-csv", dest="import_csv_file", action="store",
#                help="import CSV data set", default="")
ap.add_argument("-D", "--data-directory", dest="data_dir", action="store",
                default=".", help="specify data directory")
ap.add_argument("-P", "--progression", dest="number_of_steps",
                action="store", default="",
                help="Show progression of islands at intervals of fixed size")
ap.add_argument("-V", "--verbose", dest="verbose", action="store_true",
                default=False, help="Running commentary on terminal")
ap.add_argument("-R", "--random-payment-limit", dest="random_payment_limit",
                 action="store", default="1",
                 help="(If no value is supplied, payments are fixed at 1.)")
ap.add_argument("-W", "--create-html-segment",
                dest="create_html_segment", action="store_true", default=False,
                help="Create an HTML graph/chart page for each step")
ap.add_argument("-E", "--export-csv", dest="export_csv",
                action="store_true", default=default_export_csv,
                help="export payments as CSV to STDOUT")
ap.add_argument("-A","--about-islands", dest="about_islands",
                action="store_true", default=default_about_islands,
                help="Display explanatory notes")
ap.add_argument("-v", "--version", action="version",
                version="%(prog)s " + script_version)
args = ap.parse_args()

if args.about_islands:
    print(about)
    quit()

n_passes = int(args.n_passes)
n_agents = int(args.n_agents)
n_islands = int(args.n_islands)

lt_graph = args.lt_graph

plot_graphs = args.plot_graphs

plot_svg = args.plot_svg

plot_balances = args.plot_balances

export_csv = args.export_csv
#export_csv = False

number_of_steps = args.number_of_steps
if number_of_steps:
    n_steps = int(number_of_steps)
    if n_steps > 100:
        print("No more than 100 steps allowed")
        quit()


create_html_segment = args.create_html_segment
#create_html_segment = False

#import_csv_file = args.import_csv_file
import_csv_file = False
#if not import_csv_file: # empty string
#    import_csv_file = "[no file specified]"

verbose = args.verbose

rpl = args.random_payment_limit
if rpl == "":
    random_payment = 1
else:
    random_payment = int(rpl)

optype = ".png"
if plot_svg:            # default image format is PNG
    optype = ".svg"

data_dir = args.data_dir

if export_csv:          # Verbose output is suppressed if spewing CSV to STDOUT
    verbose = False

if verbose:
    print("-"*60)
    print("\tNumber of payments:\t" + str(n_passes))
    print("\tNumber of agents:\t" + str(n_agents))
    print("\tNumber of islands:\t" + str(n_islands))
    print("\tAgents on each island:\t" + str(n_agents // n_islands))
    print("\tInclude LT graph:\t" + str(lt_graph))
    print("\tPlot payment graphs:\t" + str(plot_graphs))
    print("\tPlot graphs as SVG:\t" + str(plot_svg))
    print("\tShow balance plots:\t" + str(plot_balances))
    print("\tExport CSV dataset:\t" + str(export_csv))
#    if import_csv_file:
#        print("\tImport CSV dataset:\t" + import_csv_file)
#    else:
#        print("\tDo not import dataset")
    if number_of_steps:
        print("\tShow progress in:\t" + str(number_of_steps) + " steps")
    else:
        print("\tProgress not shown")
    print("\tCreate HTML containers:\t" + str(create_html_segment))
    print("\tData directory:\t\t" + data_dir)
    print("\tRandom payment limit:\t" +  str(rpl))
    print("-"*60)

if plot_graphs and n_passes > max_graph_passes:
    print("Cannot plot payment graphs if number of passes (-p) exceeds "
          + str(max_graph_passes))
    quit()

if number_of_steps:
    if (n_passes % n_steps) != 0:
        print("The number of passes must be a multiple of " + str(n_steps))
        quit()
    else:
        if verbose:
            print("Show progress every " + str(n_passes // n_steps) \
                  + " payments\n")

island_size = n_agents // n_islands


#-------------------------------------------------------------------------------
# The data directory tree is created if it does not exist already:
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
if not os.path.exists(data_dir + "/gv"):
    os.mkdir(data_dir + "/gv")
if not os.path.exists(data_dir + "/output"):
    os.mkdir(data_dir + "/output")

#-------------------------------------------------------------------------------
# Return current date+time in "%Y-%m-%d_%H%M%S" format
# YYYY-MM-DD_hhmmss
def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

#-------------------------------------------------------------------------------
# For convenience of segmentation, the values are constrained:
#    n_agents = {20, 50, 100, 200, 500, 1000, 2000, 5000, 10000} (default = 100)
#    n_islands = {2,5,10}

island_divisor = n_agents // n_islands
#
# The island currencies are identified by the 10s digit in the agent number.
def identify_island(agent_number):
    island_number = (agent_number // island_divisor) % 10
    return island_number

# Not all agents eligible to join a particular island will have done so after
# only a small number of passes. Therefore their membership is recorded in a
# parallel array:
def members_of(island):
    island_members = []
    for a in range(n_agents):
        if members[island][a]:
            island_members.append(a)
    return island_members


# Each "island" is identified by a distinct colour, with LT (the global money)
# is identified by black.
def island_colour(island_number):
    colour = [ "#000000", "#ff0000", "#ffaa00", "#00aa00", "#0055ff",
               "#aa0000", "#aa00ff", "#aa5500", "#aaaa00", "#4e8daa"
             ]
    if island_number in range(len(colour)):
        return colour[island_number]
    else:
        return ""

# (For convenience, LT is treated as a "global island". Maybe it should be
# called "Pangea".)

#-------------------------------------------------------------------------------
# There is a fixed number of agents (20, 50, 100, 200, 500, 1000, 2000, 5000 or
# 10000 (100 by default), numbered 0 upwards. Two are selected randomly at each
# pass of the main loop:
def pick_agent():
    return random.randint(0,n_agents-1)

def agent_id(agent):
    if n_agents > 100:
        return str(agent).zfill(3)
    else:
        return str(agent).zfill(2)

#-------------------------------------------------------------------------------
# The dataset arrays are initialized:

payments = [ [ 0 for y in range(n_agents) ] for x in range(n_islands) ]
balances = [ [ 0 for y in range(n_agents) ] for x in range(n_islands) ]
members  = [ [ False for y in range(n_agents) ] for x in range(n_islands) ]

#-------------------------------------------------------------------------------
#

def payment_value():
    if random_payment == 1:
        return 1
    else:
        return random.randint(0,float(rpl))

fname = timestamp() # The output set directory name is the current date+time.




suffix = "_"
if plot_balances:
    suffix += "B"
if plot_graphs:
    suffix += "G"

print("suffix:\t" + suffix)











# The output directory is created (to group output files):
if not os.path.exists("output"):
    os.mkdir(data_dir + "/output")
opdir = data_dir + "/output/" + fname + suffix
os.mkdir(opdir)


# A separate graph is created for each island:
island_graph_filename = []
for n in range(n_islands):
    island_graph_filename.append(fname + "_" + str(n) + ".gv")

f = [] # array of file handles for islands
for n in range(n_islands):
    f.append(open(data_dir + "/gv/" + island_graph_filename[n], "w"))

# The header is created for each of the GV graphs:
for n in range(n_islands):
    f[n].write("digraph payments {\n"
               + "\trankdir=LR\n"
               + "\tnode [shape=circle]\n"
               + "\tfontsize="30"\n"
              )
    f[n].close()

# The island at any stage in the progression comprises only those agents who
# have used that island currency. Otherl agents eligible to join this island are
# not yet included in the set.
def island_data(island, data_array):
    d = []
    for a in range(n_agents):
        if members[island][a]:
            d.append(data_array[island][a])
    return d

if number_of_steps:
    n_steps = int(number_of_steps)
else:
    n_steps = 1
n_passes_per_step = n_passes // n_steps

if verbose:
    if n_steps == 1:
        print(str(n_passes) + " payments\n")
    else:
        print(str(n_passes) + " payments in " + str(n_steps) + " steps\n")

# A separate graph is created for each island:
island_graph_fname = []
for n in range(n_islands):
    island_graph_fname.append(fname + "_" + str(n) + ".gv")

f = [] # array of file handles for islands
for n in range(n_islands):
    f.append(open(data_dir + "/gv/" + island_graph_fname[n], "w"))

# The header is created for each of the GV graphs:
for n in range(n_islands):
    f[n].write("digraph payments {\n"
               + "\trankdir=LR\n"
               + "\tnode [shape=circle]\n"
               + "\tfontsize="30"\n"
              )
    f[n].close()

step_count = 0           #===========-------------------------------------------
for s in range(n_steps): # outer loop: n_passes = n_steps * n_passes_per_step

    step = str(step_count).zfill(2)

    # The step directory is created along with its subdirectories.
    outdir = opdir + "/" + str(step_count).zfill(2)

    step_count += 1

    if not os.path.exists(outdir):
        os.mkdir(outdir)
    if plot_balances:
        if not os.path.exists(outdir + "/balances"):
            os.mkdir(outdir + "/balances")
    if plot_graphs:
        if not os.path.exists(outdir + "/graphs"):
            os.mkdir(outdir + "/graphs")

    css_string = "<style>" \
                 + "body, p {" \
                 + "font-family: Verdana, Arial, sans-serif;\n" \
                 + "font-size: 14px;\n" \
                 + "}\n" \
                 + "</style>\n"

    if create_html_segment: # The HTML containers are opened:
        html_b_f = open(outdir + "/balances.html", "w")
        html_g_f = open(outdir + "/graphs.html", "w")
        # These will be closed when the script terminates.
        html_b_f.write("<html>\n<head>\n<title>Balance charts</title>\n" \
                       + css_string + "</head>\n<body>\n"
                      )
        html_g_f.write("<html>\n<head>\n<title>Payment graphs</title>\n" \
                       + css_string + "</head>\n<body>\n"
                      )

    if verbose:
        if create_html_segment:
            print("Creating HTML container(s) in " + outdir + "/")
        else:
            print()

                                       #===========-----------------------------
    for p in range(n_passes_per_step): # inner loop: progression steps

        f = [] # array of file handles for islands
        for n in range(n_islands):
            f.append(open(data_dir + "/gv/" + island_graph_fname[n], "a"))

        payer = pick_agent()
        payee = pick_agent()
        if (payer != payee): # ignore if payer = payee
            payer_island = identify_island(payer)
            payee_island = identify_island(payee)
            if (payer_island == payee_island) and (payee_island != 0):
                island = payee_island # = payer_island
                # The payer and payee are identified as members of this island.
                members[island][payer] = True
                members[island][payee] = True
                # The GraphViz line is appended to the accumulator file:
                f[island].write("\t"
                                + agent_id(payer) + " -> " + agent_id(payee)
                                + " [color="" + island_colour(island) \
                                + "" penwidth=2.0 fontname="Verdana"]\n"
                               )
            else: # use LT
                island = 0
                # NB Although all agents have access to LT, not all agents will
                #    have used it during the first few hundred passes. Therefore
                #    LT is treated here as an island (one with an inevitably
                #    faster growing membership). This will also make the dataset
                #    comparisons more realistic.
                members[island][payer] = True
                members[island][payee] = True
                # The GraphViz line is appended:
                f[0].write("\t" + agent_id(payer) + " -> " + agent_id(payee)
                           + " [color="" + island_colour(0)
                           + "" penwidth=2.0 fontname="Verdana"]\n"
                          )

            payment = payment_value() # either a random value or 1.

            if export_csv:
                print(str(island)
                      + "," + str(payer)
                      + "," + str(payee)
                      + "," + str(payment)
                     )

            balances[island][payer] -= payment  # The payment is made
            balances[island][payee] += payment  #

            payments[island][payee] += 1        # count of all payments made

    f[n].close()

    #---------------------------------------------------------------------------
    if plot_graphs: # the payment graphs are drawn

        if lt_graph:
            first_island = 0
        else:
            first_island = 1

        for n in range(first_island,n_islands): # LT is ignored by default.
            fn = fname + "_" + str(n)

            # The GV accumulator file is copied to a temporary file in order to
            # allow it to be terminated correctly:
            gvfile = data_dir + "/gv/" + fname + "_" + str(n) + ".gv"
            gvfile2 = data_dir + "/gv/" + fname + "_" + str(n) + "_.gv"
            shutil.copy(gvfile, gvfile2)
            with open(gvfile2, "a") as gv_f:    # append } to copy of GV
                gv_f.write("}\n")               # accumulator

            #gpath = outdir + "/graphs/" + str(n) + "_graph" + optype
            gfile = "graphs/" + str(n) + "_graph" + optype
            gpath = outdir + "/" + gfile

            if verbose:
                print("\tisland " + str(n) + "\t: " + gpath)

            os.system("dot -Tpng " + gvfile2 + " -o " + gpath)

            if create_html_segment:
                #html_g_f.write("<hr />")
                html_g_f.write("<p>island " + str(n) \
                               + " : step " + str(s) + "</p>")
                html_g_f.write("<img src="" + gfile + "" width="980" />\n")
                html_b_f.write("<br />")


    #---------------------------------------------------------------------------
    if plot_balances: # the balance charts are drawn

        for i in range(n_islands):

            bfile = "balances/" + str(i) + "_balances" + optype # .png | .svg
            fn = outdir + "/" + bfile

#            fn = outdir + "/balances/" \
#                 + str(i) + "_balances" + optype # ".png" | ".svg"

            X = members_of(i)

            Y = island_data(i, balances)
            Y.sort()

            xaxis_label = "agents arranged by order of balance held"
            yaxis_label = "balance"

            if verbose:
                print("\tisland " + str(i) + "\t: " + fn)

            plt.scatter( X,
                         Y,
                         c = island_colour(i),
                         s = 5.0
                       )

            ax = plt.gca()
            ax.set(xticklabels=[])
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))

            plt.grid(axis = "y", alpha = 0.75)
            plt.xlabel("agents (arranged by order of balance held)")
            title = "balances : island " + str(i)
            if i == 0:
                title += " (legal tender)"
            title += "\n" + str(n_agents) + " agents"
            title += "\n" + str(n_islands) + " islands\n" + str(n_passes)

            if random_payment == 1:
                title += " payments of 1 unit"
            else:
                #title += " random payments between 0 and " + str(rpl)
                title += " random payments between 0 and " + str(random_payment)
            plt.title(title, loc="left")

            plt.margins(0.01) # Place plot tails close to Y axes.

            plt.ylabel(yaxis_label)
            plt.savefig(fn)
            plt.close()


            if create_html_segment:
                html_b_f.write("<hr />")
                html_b_f.write("<p>island " + str(i) + "</p>")
                html_b_f.write("<img src="" + bfile + "" />\n<br />")


    if create_html_segment: # terminate and close HTML files
        html_b_f.write("</body>\n</html>\n")
        html_g_f.write("</body>\n</html>\n")
        html_b_f.close()
        html_g_f.close()

os.system("rm " + data_dir + "/gv/*") # clean-up

#===============================================================================

if verbose:
    if n_agents <= 100:
        print("Island membership:")
        for i in range(n_islands):
            s = "\tisland " + str(i) + " |"
            for a in range(n_agents):
                if members[i][a]:
                    s += "*"
                else:
                    s += " "
            s += "|"
            print(s)
