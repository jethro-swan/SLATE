This directory contains four sets of files:

(1) The SLATE core files, all of which are in the "core" subdirectory. These 
    are required by the SWI, the CLI and REST API.

(2) The SLATE SWI files (Flask) including:
	routes.py
	forms.py
	models.py
	errors.py
	templates/*
	static/*

(3) The SLATE CLI scripts (the names of which begin with "slate"). These are
    symlinked from  /usr/local/bin  and are usable by any agent owning an
    SSH login account.

(4) The development/test scripts (the names of which begin with "test"). These
    are run from this directory as
	./test.py 
    	./test_fph_hrns_map.py


