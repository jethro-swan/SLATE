#!/home/john/NESTS/SLATE/venv/bin/python3

from app.core.om_trad import *


name1, namespace1 = split_hrns("tom.dick.harry")
print(name1 + " : " + namespace1)
