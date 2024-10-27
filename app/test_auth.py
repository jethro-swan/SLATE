#!/usr/bin/env python3

from core.auth import auth_hash, check_auth_hash
from core.auth import authenticate_web_access, authenticate_cli_access
from core.auth import list_password_characters, password_valid
from core.auth import generate_password, list_url_safe_password_characters
from core.auth import url_safe_password_valid, generate_url_safe_password
from core.auth import generate_access_token
from core.auth import pin_random_ord, pin_prompt_message, authenticate_pin
from core.display import thinline, thickline, title_line

#def thickline():
#    print("\n" + "="*160 + "\n")

#def thinline():
#    print("\n" + "-"*160 + "\n")

#def title_line(title):
#    print("\n=== " + title + " " + "="*(155 - len(title)) + "\n")



title_line("Generate fake passwords")

fpw = []
for n in [8, 12, 16, 20, 24, 32]:
    fpw.append(generate_password(n))
for pw in fpw:
    print("\t" + pw)

title_line("Validate the fake passwords' format and check their authentication")

for pw in fpw:
    if password_valid(pw):
        print("Password  " + pw + "  format validated")
        ah = auth_hash(pw)
        if check_auth_hash(pw, ah):
            print("Password  " + pw + "  authenticated")
        else:
            print("Password  " + pw + "  not authenticated")
    else:
        print("Invalid password: \t" + pw)


title_line("Show valid password characters")

print(list_password_characters())

title_line("Show valid \"URL-safe\" password characters")

print(list_url_safe_password_characters())

thickline()
