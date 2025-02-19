#!/home/john/NESTS/SLATE/venv/bin/python3

from app.core.messaging import display_colour_subject_prefix
from app.core.messaging import send_message
from app.core.messaging import fetch_messages
from app.core.messaging import messages_available
from app.core.messaging import delete_all_messages
from app.core.messaging import delete_selected_messages
from app.core.messaging import select_messages






m = send_message(
        sender_identifier,      # FPH or HRNS
        recipient_identifier,   # FPH or HRNS
        subject_prefix,         # string
        subject,                # string
        longevity,              # integer: lifespan (seconds)
        expiry_datetime,        # string: YYYY-MM-DD_mm:ss
        message_body,           # string
        False                   # indelible (boolean)
    )
