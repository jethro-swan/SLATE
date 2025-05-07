
# Account balances are stored as integers, assuming cents (euros or dollars) or
# pence (sterling) to be the smallest value.
def integer_to_money_format(amount):
    if amount is not None:
        return "{:10.2f}".format(amount/100)
    else:
        return ""

def integer_to_money_s_format(amount):
    return "{:1.2f}".format(amount/100)


def thick_line():
    print("\n" + "="*160 + "\n")

def thin_line():
    print("\n" + "-"*160 + "\n")

def title_line(title):
    print("\n=== " + title + " " + "="*(155 - len(title)) + "\n")

def thin_title_line(title):
    print("\n--- " + title + " " + "-"*(155 - len(title)) + "\n")




def pause():
    input("\nPress ENTER to continue...\n")


def yN(prompt):
    r = input(prompt + " [yN] ")
    if (len(r) > 0) and (r[0].lower() == "y"):
        return True
    else:
        return False

def Yn(prompt):
    r = input(prompt + " [Yn] ")
    if (len(r) == 0):
        return True
    elif r[0].lower() == "n":
        return False
    else:
        return True


def yesno(b):
    if b:
        return "yes"
    else:
        return "no"


def entity_type_verbose(etype):
    if not (etype in ["namespace", "currency", "account", "primid", "secid"]):
        return ""
    if etype == "primid":
        return "login identity"
        #return "primary identity"
    if etype == "secid":
        return "alias"
        #return "secondary identity"
    else:
        return etype


# Create the *identity* type display string:
def etype_to_adtype(etype):
    if etype == "primid":
        return "login identity"
    elif etype == "secid":
        return "alias"
    else:
        return ""




def get_cli_number_input(prompt_message, min_num, max_num, default_num):
    input_value = input(prompt_message)
    try:
        number_given = int(input_value)
        if number_given < min_num:
            number_given = min_num
            print(
                "\nThis has been increased to " + str(min_num) + ". Any " \
                + "fewer would be too few.\n"
            )
        elif number_given > max_num:
            number_given = max_num
            print(
                "\nThis has been decreased to " + str(max_num) + ". Any " \
                + "more would be unmanageably many.\n"
            )
    except ValueError:
        number_given = default_num
        if input_value:
            print("Invalid ", end="")
        else:
            print("\nNo ", end="")
        print(
            "value entered. Therefore using the default value " \
            + str(default_num) + ".\n"
        )
    return number_given
