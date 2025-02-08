#!/home/john/NESTS/SLATE/venv/bin/python3
#!/home/slate/SLATE/venv/bin/python3
#!/usr/bin/env python3
#
# This is a simple CLI tool for the management of SLATE post-installation

import os
import sys
import re
import argparse
import shutil

from app.core.slate_core import create_entities_db
from app.core.slate_seed import create_seed_entities

from app.core.unix_functions import create_dir
from app.core.unix_functions import create_file
from app.core.unix_functions import sym_link
from app.core.unix_functions import get_path
from app.core.unix_functions import set_owner
from app.core.unix_functions import fcopy
from app.core.unix_functions import fcopysl
from app.core.unix_functions import treecopy
from app.core.unix_functions import treecopysl
from app.core.unix_functions import remove_tree
from app.core.unix_functions import move_tree

script_name = sys.argv[0].replace("./", "").replace(".py", "")

#==============================================================================
# Since this script is generally accessed over SSH, it should be invoked from
# the agent's home directory in which a file named .slate.cnf exists containing
# the agent's FPH.

#cwd = os.getcwd()
#cnf_path = cwd + "/.slate.cnf"

#if not os.path.exists(cnf_path):
#    sys.stderr.write("No ~/.slate.cnf file found in home directory.")
##    sys.exit(1)
#else:
#    with open(cnf_path, "r") as f:
#        agent_cfg_fph = f.read().strip()
#    if re_fph.match(agent_cfg_fph):
#        hrns = fph_to_hrns(agent_cfg_fph)
#        if hrns: # FPH is in register
#            agent_fph = agent_cfg_fph
#        else:
#            sys.stderr.write("The FPH " + agent_fph + " is not registered.")
#            sys.exit(1)



#==============================================================================
#

re_dataset = re.compile(r"^[0-9]{3}$")

# Multiple entity types can be created using a single CSV file.
# - This must specify one entity per row
# - Any dependencies in that row must be satisfied by an earlier row



#------------------------------------------------------------------------------
p = argparse.ArgumentParser(description = "Entity creation by CSV import")
p.add_argument(
    "-n", "--namespaces", dest = "create_namespaces", action = "store_true",
    help = "Specify "
)
p.add_argument(
    "-c", "--current", dest = "show_current_dataset", action = "store_true",
    help = "List the SLATE data sets currently available"
)
p.add_argument(
    "-n", "--new", dest = "new_dataset", action = "store",
    help = "Create a new SLATE dataset"
)
p.add_argument(
    "-d", "--delete", dest = "dataset_to_be_deleted", action = "store",
    help = "Delete an existing dataset"
)
p.add_argument(
    "-l", "--list", dest = "list_datasets_available", action = "store_true",
    help = "List available datasets"
)
p.add_argument(
    "-D", "--delete-all", dest = "delete_all_datasets", action = "store_true",
    help = "Delete all datasets and create a new empty dataset 0"
)
args = p.parse_args()

if args.show_current_dataset:
    slate_dataset = show_current_dataset()
    print(slate_dataset)
    sys.exit(1)
elif args.dataset_to_be_used:
    m = use_dataset(args.dataset_to_be_used)
    print(m)
    sys.exit(1)
elif args.new_dataset:
    m = create_new_dataset(args.new_dataset)
    sys.stderr.write(m)
    sys.exit(1)
elif args.dataset_to_be_deleted:
    m = delete_dataset(args.dataset_to_be_deleted)
    sys.stderr.write(m)
    sys.exit(1)
elif args.list_datasets_available:
    slate_datasets = list_datasets()
    for dataset in slate_datasets:
        print(dataset)
    sys.exit(1)
elif args.delete_all_datasets:
    m = delete_all_datasets()
    sys.stderr.write(m)
    sys.exit(1)
else:
    sys.stderr.write("No action specified")
    sys.exit(1)

#------------------------------------------------------------------------------
