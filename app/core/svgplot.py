#!/home/slate/SLATE/venv/bin/python3


from app.core.common import filename_timestamp

test_svg_file = "/var/slate/active/temp/test_svg_" + filename_timestamp()

# Temporary test values:
x_min = -1000
x_max = 1000
n_transactions = 20


def parabola_plot(balance, pstep, b_max):

    svg_head = """
    <?xml version="1.0" encoding="utf-8" standalone="no"?>
    <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
    "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
    <svg version="1.1" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 450 323"
    text-rendering="geometricPrecision" font-family="FreeSans, sans-serif">
    """

    svg_background = """
    <path
    d="M 0.500,0.610 V 278.390 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#ffb2ff"
    />
    <path
    d="M 0.500,0.610 V 264.501 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#ffbeff"
    />
    <path
    d="M 0.500,0.610 V 253.390 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#fabeff"
    />
    <path
    d="M 0.500,0.610 V 242.279 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#f4beff"
    />
    <path
    d="M 0.500,0.610 V 231.167 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#eebeff"
    />
    <path
    d="M 0.500,0.610 V 220.056 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#e8beff"
    />
    <path
    d="M 0.500,0.610 V 208.945 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#e2beff"
    />
    <path
    d="M 0.500,0.610 V 195.056 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#dcbeff"
    />
    <path
    d="M 0.500,0.610 V 181.167 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#d6beff"
    />
    <path
    d="M 0.500,0.610 V 167.278 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#d0beff"
    />
    <path
    d="M 0.500,0.610 V 153.389 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#cabeff"
    />
    <path
    d="M 0.500,0.610 V 136.722 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#c4beff"
    />
    <path
    d="M 0.500,0.610 V 120.055 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#bebeff"
    />
    <path
    d="M 0.500,0.610 V 103.389 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#bec4ff"
    />
    <path
    d="M 0.500,0.610 V 86.722 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#becaff"
    />
    <path
    d="M 0.500,0.610 V 67.277 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#bed0ff"
    />
    <path
    d="M 0.500,0.610 V 47.833 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#bed6ff"
    />
    <path
    d="M 0.500,0.610 V 25.610 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#bedcff"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,278.390 V 0.610 Z"
    fill="#ffb2ff"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,264.501 V 0.610 Z"
    fill="#ffbeff"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,253.390 V 0.610 Z"
    fill="#ffbefa"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,242.279 V 0.610 Z"
    fill="#ffbef4"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,231.167 V 0.610 Z"
    fill="#ffbeee"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,220.056 V 0.610 Z"
    fill="#ffbee8"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,208.945 V 0.610 Z"
    fill="#ffbee2"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,195.056 V 0.610 Z"
    fill="#ffbedb"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,181.167 V 0.610 Z"
    fill="#ffbed6"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,167.278 V 0.610 Z"
    fill="#ffbed0"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,153.389 V 0.610 Z"
    fill="#ffbeca"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,136.722 V 0.610 Z"
    fill="#ffbec4"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,120.055 V 0.610 Z"
    fill="#ffbebe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,103.389 V 0.610 Z"
    fill="#ffc4be"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,86.722 V 0.610 Z"
    fill="#ffcabe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,67.277 V 0.610 Z"
    fill="#ffd0be"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,53.388 V 0.610 Z"
    fill="#ffd6be"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,25.610 V 0.610 Z"
    fill="#ffdbbe"
    />
    <path
    d="M 0.500,0.610 Q 48.312,278.390 96.125,278.390 V 0.610 Z"
    fill="#bee2ff"
    />
    <path
    d="M 6.238,0.610 Q 51.181,278.390 96.125,278.390 V 0.610 Z"
    fill="#bee8ff"
    />
    <path
    d="M 11.975,0.610 Q 54.050,278.390 96.125,278.390 V 0.610 Z"
    fill="#beeeff"
    />
    <path
    d="M 17.712,0.610 Q 56.919,278.390 96.125,278.390 V 0.610 Z"
    fill="#bef4ff"
    />
    <path
    d="M 23.450,0.610 Q 59.787,278.390 96.125,278.390 V 0.610 Z"
    fill="#befaff"
    />
    <path
    d="M 29.188,0.610 Q 62.656,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffff"
    />
    <path
    d="M 34.925,0.610 Q 65.525,278.390 96.125,278.390 V 0.610 Z"
    fill="#befffa"
    />
    <path
    d="M 40.663,0.610 Q 68.394,278.390 96.125,278.390 V 0.610 Z"
    fill="#befff4"
    />
    <path
    d="M 46.400,0.610 Q 71.263,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffee"
    />
    <path
    d="M 52.138,0.610 Q 74.131,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffe8"
    />
    <path
    d="M 57.875,0.610 Q 77.000,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffe2"
    />
    <path
    d="M 63.613,0.610 Q 79.869,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffdc"
    />
    <path
    d="M 69.350,0.610 Q 82.737,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffd6"
    />
    <path
    d="M 75.088,0.610 Q 85.606,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffd0"
    />
    <path
    d="M 80.825,0.610 Q 88.475,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffca"
    />
    <path
    d="M 86.562,0.610 Q 91.344,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffc4"
    />
    <path
    d="M 92.300,0.610 Q 94.213,278.390 96.125,278.390 V 0.610 Z"
    fill="#beffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 143.938,278.390 191.750,0.610 Z"
    fill="#ffe2be"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 141.069,278.390 186.012,0.610 Z"
    fill="#ffe8be"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 138.200,278.390 180.275,0.610 Z"
    fill="#ffeebe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 135.331,278.390 174.537,0.610 Z"
    fill="#fff4be"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 132.463,278.390 168.800,0.610 Z"
    fill="#fffabe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 129.594,278.390 163.062,0.610 Z"
    fill="#ffffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 126.725,278.390 157.325,0.610 Z"
    fill="#faffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 123.856,278.390 151.588,0.610 Z"
    fill="#f4ffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 120.988,278.390 145.850,0.610 Z"
    fill="#eeffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 118.119,278.390 140.113,0.610 Z"
    fill="#e8ffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 115.250,278.390 134.375,0.610 Z"
    fill="#e2ffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 112.381,278.390 128.637,0.610 Z"
    fill="#dbffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 109.512,278.390 122.900,0.610 Z"
    fill="#d6ffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 106.644,278.390 117.162,0.610 Z"
    fill="#d0ffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 103.775,278.390 111.425,0.610 Z"
    fill="#caffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 100.906,278.390 105.688,0.610 Z"
    fill="#c4ffbe"
    />
    <path
    d="M 96.125,0.610 V 278.390 Q 98.037,278.390 99.950,0.610 Z"
    fill="#beffbe"
    />
    <polygon points="96.125,278.390, 191.750,264.501, 191.750,278.390,
    0.500,278.390, 0.500,264.501"
    fill="#e8e8e8"
    />
    """

    svg_tail = "</svg>"


    svg_width = 600     # total width of SVG plot area
    svg_height = 600    # total height of SVG plot area
    svg_margin = 10
    X0 = svg_width/2 + svg_margin
    Y0 = svg_height + svg_margin

    Sx = x_max/X0
    Sy = Y0/pstep

    with open("test_svg_file", "w") as svgf:
        svgf.write(svg_head)
        svgf.write(svg_background)
        svgf.write(svg_tail)
