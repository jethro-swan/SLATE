#!/usr/bin/bash

# NESTS/SLATE - a networked tool to support user-created and -stewarded
# currencies and measures (open money and open measure)
# Copyright (C) 2026. 2025, 2024, 2023, 2022 John Waters
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

SR=/home/slate/SLATE

# Existing files are removed if present:
#rm -f $SR/tools/slate_*
#rm -f $SR/tools/fph_to_hrns
#rm -f $SR/tools/hrns_to_fph

# The ./pyv/ directory is used to hold a version with .py extension to force
# correct syntax highlighting when editing. These are then hard linked to a
# version without the .py extension:
#ln -f $SR/tools/pyv/fph_to_hrns.py $SR/tools/fph_to_hrns
#ln -f $SR/tools/pyv/hrns_to_fph.py $SR/tools/hrns_to_fph
#ln -f $SR/tools/pyv/slate_import_accounts.py $SR/tools/slate_import_accounts
#ln -f $SR/tools/pyv/slate_import_currencies.py $SR/tools/slate_import_currencies
#ln -f $SR/tools/pyv/slate_import_namespaces.py $SR/tools/slate_import_namespaces
#ln -f $SR/tools/pyv/slate_import_primids.py $SR/tools/slate_import_primids
#ln -f $SR/tools/pyv/slate_import_secids.py $SR/tools/slate_import_secids
#ln -f $SR/tools/pyv/slate_list_indentifiers.py $SR/tools/slate_list_identifiers

# Finally, a copy of the tools is put where an unmodified PATH can find it:
sudo cp $SR/tools/fph_to_hrns /usr/local/bin/
sudo cp $SR/tools/hrns_to_fph /usr/local/bin/
sudo cp $SR/tools/slate_* /usr/local/bin/
