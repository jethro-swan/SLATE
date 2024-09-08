import sqlite3
import random
import os
import pickle

from constants import SLATE_DB_DIR
from common import filename_timestamp as timestamp
from common import nshash
from unix_functions import fcopy


BOLLOXDB = SLATE_DB_DIR + "utterbollox.db"


def create_bollox_db():

    #with sqlite3.connect(AGENTS_DB) as conn:
    with sqlite3.connect(BOLLOXDB) as conn:
        cursor = conn.cursor()
        # Create agents table:
        cursor.execute("""
    	    CREATE TABLE IF NOT EXISTS things (



            );"""
        )

        conn.commit()
        cursor.close()


#cm = ["Cthulhu", "Yog Sothoth", "Azathoth", "Dagon", "Hastur"]

#for thingy in cm:
#    print(thingy)

#onions = pickle.dumps(cm)

onions = pickle.dumps(["Cthulhu", "Yog Sothoth", "Azathoth", "Dagon", "Hastur"])

cthulhu = "Cthulhu"
onions = pickle.dumps([cthulhu])


cm2 = pickle.loads(onions)
cm2.append("Yog Sothoth")
cm2.append("Azathoth")

for thingy in cm2:
    print(thingy)


#cm3 = pickle.loads(onions)
#cm4 = cm3.append("Yog Sothoth")


#for thingy in cm4:
#    print(thingy)
