from core.csv_import import import_minimal_payment_set_as_csv


csv_file_path = "/home/john/NESTS/SLATE/app/core/temp/sandbox_payment_set_1.csv"


owner_identifier = "wy.ycx.io.gn.de"
currency_identifier = "xhj.isv.es"
namespace_identifier = "wy.ycx.io.gn.de"

import_minimal_payment_set_as_csv(
        owner_identifier,
        currency_identifier,
        namespace_identifier,
        csv_file_path
    )
