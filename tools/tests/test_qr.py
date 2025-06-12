#!/home/slate/SLATE/venv/bin/python3

from app.core.qrcode import qrencode_invitation

from app.core.constants import QR_CODES


hub_url = "https://locus01.lrc.org.uk"
namespace_hrns = "bb.cc"
currency_hrns = "hrs.bb.cc"
inviter_hrns = "bb.cc"

qr_png_filename = qrencode_invitation(currency_hrns, namespace_hrns, inviter_hrns)

print(qr_png_filename)
print(QR_CODES + qr_png_filename)
