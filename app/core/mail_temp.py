import os, sys


def temp_mail_send(from_address, to_address, mail_subject, mail_body):

    sendemail_str = "sendemail -f " + from_address + " -t " + to_address \
                  + " -u \"" + mail_subject + "\" -m \"" + mail_body + "\"\n"

    #print(sendemail_str)
    os.system(sendemail_str)
