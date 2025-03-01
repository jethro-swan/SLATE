import re
import sys

#from constants import NS_SEPARATOR as NSS

# RegExp list:

re_realname = re.compile(r"")

# Names in SLATE are limited to alphanumeric Latin characters:
re_slatename = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*$")
#re_slatename = re.compile(r"^[a-fA-F0-9]{1,}$")

re_access_token = re.compile(r"^[0-9a-fA-F]{32}$") # (currently same as for FPH)

#re_password \
#= re.compile(r"^[A-Za-z0-9!£\$%\^&*()-+-=\[\]{}:@~;'#<>?,.\\/']${16,}]")
# THIS NEEDS TO BE IMPROVED

re_pin = re.compile(r"^[0-9]{6}$")

#------------------------------------------------------------------------------
# Email:
#re_email = re.compile(r"(\w(\w_-\.)+\w)+@(\.\w+(\w_-)+)+\.\w{2,4}")
#re_email = re.compile(r"^w+[+.w-]*@([w-]+.)*w+[w-]*.([a-z]{2,4}|d+)$")
#re_email = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$")
re_email = \
re.compile(r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+")
# (Not perfect, but good enough for most practical purposes)

#------------------------------------------------------------------------------
# Payment value:
re_pvalue = re.compile(r"^\d{1,}\.\d{2}$")

# It is assumed that any number input with "," thousands separators will have
# these stripped out before being tested against the RE.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Transaction ID:
re_transid = re.compile(r"^\d{1,}:\d{19,}:[0-9a-f]{16}$")


#------------------------------------------------------------------------------
# Password:
pwre = r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*\W)(?!.* ).{12,48}$"
#pwre = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
re_password = re.compile(pwre)


# RegExp list:

#------------------------------------------------------------------------------
# HRNS = Human-Readable NameSpace
# human-readable namespace path (external)
re_hrns = re.compile(r"^(\S+\.)*\S+$")
#re_hrns = re.compile(r"^([a-z0-9_-]+\.)*[a-z0-9_-]+$")
# (NB, the current version handles only unaccented latin characters)

# See: https://docs.python.org/3/library/re.html
#
# For Unicode (str) patterns:
#
#   Matches Unicode word characters; this includes most characters that can be
#   part of a word in any language, as well as numbers and the underscore. If
#   the ASCII flag is used, only [a-zA-Z0-9_] is matched.
#
# For 8-bit (bytes) patterns:
#
#   Matches characters considered alphanumeric in the ASCII character set; this
#   is equivalent to [a-zA-Z0-9_]. If the LOCALE flag is used, matches
#   characters considered alphanumeric in the current locale and the underscore.

#------------------------------------------------------------------------------
# FPH = Full Path Hash = hash of FIP
re_fph = re.compile(r"^[0-9a-fA-F]{32}$") # string of 32 hex digits
#re_fph = re.compile(r"^[0-9a-f]{16}$") # string of 16 hex digits

#------------------------------------------------------------------------------
# Payment value:
#re_pvalue = re.compile(r"^\d{1,}\.\d{2}$")
re_pvalue = re.compile(r"^\d{1,}$")

# It is assumed that any number input with "," thousands separators will have
# these stripped out before being tested against the RE.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Transaction ID:

re_filename =re.compile(r"^[a-zA-Z0-9_]{1,}$")


re_datestamp = re.compile(r"^[\d]{4}-[\d]{2}-[\d]{2}_[\d]{2}:[\d]{2}:[\d]{2}$")
