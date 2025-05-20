import os


fname = os.getcwd() + "/seed_primid_details.txt"
with open(fname, "r") as f:
    primid_details = f.readlines()
for line in primid_details:
    l = line.split("=")
    if l[0].strip() == "seed_primid_realname":
        seed_primid_realname = l[1].strip()
    elif l[0].strip() == "seed_primid_email_1":
        seed_primid_email_1 = l[1].strip()
    elif  l[0].strip() == "seed_primid_email_2":
        seed_primid_email_2 = l[1].strip()
    elif  l[0].strip() == "seed_primid_password":
        seed_primid_password = l[1].strip()
    elif l[0].strip() == "seed_primid_pin":
        seed_primid_pin = l[1].strip()
    elif l[0].strip() == "seed_primid_access_token":
        seed_primid_access_token = l[1].strip()

print("seed_primid_realname:\t\t = " + seed_primid_realname)
print("seed_primid_email_1:\t\t = " + seed_primid_email_1)
print("seed_primid_email_2:\t\t = " + seed_primid_email_1)
print("seed_primid_password:\t\t = " + seed_primid_password)
print("seed_primid_pin:\t\t = " + seed_primid_pin)
print("seed_primid_access_token:\t = " + seed_primid_access_token)
