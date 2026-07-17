#!/home/slate/SLATE/venv/bin/python3

from core.mail_temp import temp_mail_send
from core.common import filename_timestamp



from_address    = "john@esrad.org.uk"
to_address      = "john.waters@cooptel.net"
mail_subject    = "test" + filename_timestamp()
mail_body       = "O'er seas that have no beaches to end their waves upon\n" \
                + "I sailed with twelve peaches, a sofa and a swan.\n"

temp_mail_send(from_address, to_address, mail_subject, mail_body)
