#!/usr/bin/bash

SR=/home/slate/SLATE

# Existing files are removed if present:
rm -f $SR/tools/slate_*
rm -f $SR/tools/fph_to_hrns
rm -f $SR/tools/hrns_to_fph

# The ./pyv/ directory is used to hold a version with .py extension to force
# correct syntax highlighting when editing. These are then hard linked to a
# version without the .py extension:
ln -f $SR/tools/pyv/fph_to_hrns.py $SR/tools/fph_to_hrns
ln -f $SR/tools/pyv/hrns_to_fph.py $SR/tools/hrns_to_fph
ln -f $SR/tools/pyv/slate_import_accounts.py $SR/tools/slate_import_accounts
ln -f $SR/tools/pyv/slate_import_currencies.py $SR/tools/slate_import_currencies
ln -f $SR/tools/pyv/slate_import_namespaces.py $SR/tools/slate_import_namespaces
ln -f $SR/tools/pyv/slate_import_primids.py $SR/tools/slate_import_primids
ln -f $SR/tools/pyv/slate_import_secids.py $SR/tools/slate_import_secids
ln -f $SR/tools/pyv/slate_list_entities.py $SR/tools/slate_list_entities

# The default installation directory is /home/slate/ but the development is
# done currently using a different path. Therefore this must be changed where
# necessary:
sed -i 's/john\/NESTS/slate/' $SR/tools/slate_*
sed -i 's/john\/NESTS/slate/' $SR/tools/fph_to_hrns
sed -i 's/john\/NESTS/slate/' $SR/tools/hrns_to_fph

# Finally, a copy of the tools is put where an unmodified PATH can find it:
sudo cp $SR/tools/fph_to_hrns /usr/local/bin/
sudo cp $SR/tools/hrns_to_fph /usr/local/bin/
sudo cp $SR/tools/slate_* /usr/local/bin/
