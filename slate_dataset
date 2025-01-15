#!/usr/bin/env python3
#
# This is a simple CLI tool for the management of SLATE post-installation

import os
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

# Create a new dataset.
#
def create_new_dataset(new_dataset): # integer [0,999]
    if isinstance(new_dataset, str):
        dataset = int(new_dataset)
    if dataset > 999:
        return "Dataset number must be between 0 and 999"
    dataset_number = str(dataset).zfill(3)
    if  os.path.exists("/var/slate/" + dataset_number):
        return "Dataset " + dataset_number + " exists already"
    else:
        new_dataset_path = "/var/slate/" + dataset_number
        os.mkdir(new_dataset_path, mode=0o600)
        os.symlink(new_dataset_path, "/var/slate/active")
        os.mkdir(new_dataset_path + "/maps", mode=0o600)
        os.mkdir(new_dataset_path + "/db", mode=0o600)
        os.mkdir(new_dataset_path + "/data", mode=0o600)
        os.mkdir(new_dataset_path + "/logs", mode=0o600)
        os.mkdir(new_dataset_path + "/data", mode=0o600)
        os.mkdir(new_dataset_path + "/test_generated_fake_details", mode=0o600)
        create_entities_db()
        create_seed_entities()
    return ""

# List the existing datasets.
# If none, or if /var/slate does not exist, /var/slate/000/ is created.
#
def list_datasets():
    dataset_list = []
    m = ""
    if os.path.exists("/var/slate"):
        datasets = os.listdir("/var/slate")
        for dataset_number in datasets:
            #if dataset_number.isnumeric():
            if re_dataset.match(dataset_number):
                dataset_list.append(dataset_number)
        if dataset_list == []: # not datasets
            m = create_new_dataset("000")
    else:
        os.mkdir("/var/slate/", mode=0o600)
        m = create_new_dataset("000")
        #os.symlink("/var/slate/000", "/var/slate/active")
        m = "/var/slate/000 created (mode = 0o600) because no dataset existed"
    return dataset_list, m

# Show the currently active dataset number:
#
def show_current_dataset():
    if os.path.exists("/var/slate/active"): # symlink to current dataset
        symlink_path = os.readlink("/var/slate/active")
        fname = symlink_path.split("/")[-1]
        return fname, ""
    else:
        return "", "The dataset symlink is missing"

# Delete a dataset.
#
def delete_dataset(dataset_to_be_deleted):
    if isinstance(dataset_to_be_deleted, str):
        dataset = int(ataset_to_be_deleted)
    if dataset > 999:
        return "Dataset number must be between 0 and 999"
    dataset_number = str(dataset).zfill(3)
    dataset_path = "/var/slate/" + dataset_number
    if not os.path.exists(dataset_path):
        return "Dataset " + dataset_number + " exists already"
    active_dataset, m = show_current_dataset()
    if dataset_to_be_deleted == active_dataset:
        return "The active dataset cannot be deleted. Select another first."
    else:
        shutil.rmtree(dataset_path, ignore_errors=False, onerror=None)
        return ""

# Delete all existing datasets and create a new dataset 0.
#
def delete_all_datasets():
    shutil.rmtree("/var/slate", ignore_errors=False, onerror=None)
    os.mkdir("/var/slate/", mode=0o600)
    m = create_new_dataset("000")
    m = "/var/slate/000 created (mode = 0o600) after all datasets deleted."
    return m


#------------------------------------------------------------------------------
p = argparse.ArgumentParser(description = "SLATE datasets management")
p.add_argument(
    "-u", "--use", dest = "dataset_to_be_used", action = "store",
    help = "Specify dataset to use, creating it if it does not exist already."
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
    m = use_dataset(dataset_to_be_used)
    print(m)
    sys.exit(1)
elif args.new_dataset:
    m = create_new_dataset(new_dataset)
    sys.stderr.write(m)
    sys.exit(1)
elif args.dataset_to_be_deleted:
    m = delete_dataset(dataset_to_be_deleted)
    sys.stderr.write(m)
    sys.exit(1)
elif args.list_datasets_available:
    slate_datasets = list_slate_datasets()
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
