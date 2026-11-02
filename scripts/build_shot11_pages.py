#!/usr/bin/env python3
"""Build three original SVG page layouts using verified public-domain text.

No third-party screenshot pixels, logos, photographs, or site CSS are used.
The SVG is both the full page and the source of the enlarged crop in Remotion.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path('/home/user/lab/public')
W, H = 1280, 900
FONT = "sans-serif"


def txt(x, y, s, size=20, weight=400, fill='#17232d', anchor='start', family=FONT):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" xml:space="preserve">{escape(s)}</text>')


def rect(x, y, w, h, fill='none', stroke='none', sw=1, rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def line(x1, y1, x2, y2, stroke='#70808c', sw=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>'


def svg_doc(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>' + ''.join(body) + '</svg>')


def common_header(parts, site, nav, accent):
    parts += [
        rect(0, 0, W, 7, accent),
        txt(42, 50, site, 27, 700, accent),
        txt(42, 91, nav, 16, 400, '#425565'),
        line(40, 111, 1240, 111, '#c8d0d6', 1),
    ]


def build_bls():
    p = []
    common_header(p, 'U.S. Bureau of Labor Statistics', 'HOME  /  SUBJECTS  /  DATA TOOLS  /  PUBLICATIONS  /  ECONOMIC NEWS RELEASE', '#174d70')
    p += [
        txt(42, 143, 'Economic News Release  >  Consumer Price Index', 15, 400, '#65737d'),
        txt(42, 184, 'Consumer Price Index Summary', 32, 700, '#17232d'),
        txt(42, 216, 'Transmission of material in this release: Wednesday, October 14, 2026  •  USDL-26-1574', 15, 400, '#596771'),
        txt(42, 256, 'CONSUMER PRICE INDEX - SEPTEMBER 2026', 21, 700),
        txt(42, 290, 'The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.6 percent in September.', 18),
        txt(42, 316, 'Over the last 12 months, the all items index increased 3.7 percent before seasonal adjustment.', 18),
        txt(42, 356, 'Table A. Percent changes in CPI for All Urban Consumers (CPI-U): U.S. city average', 18, 700),
    ]
    x0, y0, label_w, col_w, header_h, row_h = 40, 375, 280, 115, 64, 42
    total_w = label_w + 8 * col_w
    p.append(rect(x0, y0, total_w, header_h, '#edf2f5'))
    headers = [('Expenditure category', '')] + [(m, '2026') for m in ['Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sep.']] + [('12-mos.', 'Sep. 2026')]
    for i, (a, b) in enumerate(headers):
        cx = x0 + (0 if i == 0 else label_w + (i - 1) * col_w)
        cw = label_w if i == 0 else col_w
        p.append(rect(cx, y0, cw, header_h, 'none', '#75838d', 1))
        anchor_x = cx + 12 if i == 0 else cx + cw / 2
        anchor = 'start' if i == 0 else 'middle'
        p.append(txt(anchor_x, y0 + 25, a, 15 if i else 16, 700, '#26343e', anchor))
        if b:
            p.append(txt(anchor_x, y0 + 47, b, 15, 700, '#26343e', anchor))
    rows = [
        ('All items', ['0.9', '0.6', '0.5', '-0.4', '0.1', '0.4', '0.6', '3.7']),
        ('Food', ['0.0', '0.5', '0.2', '0.2', '0.1', '0.1', '0.0', '2.5']),
        ('Energy', ['10.9', '3.8', '3.9', '-5.7', '-1.5', '2.1', '5.2', '20.4']),
        ('Gasoline (all types)', ['21.2', '5.4', '7.0', '-9.7', '-2.9', '3.9', '9.1', '34.2']),
        ('Electricity', ['0.8', '2.1', '0.6', '-1.0', '0.1', '-0.2', '0.2', '4.4']),
        ('Shelter', ['0.3', '0.6', '0.3', '0.1', '0.1', '0.3', '0.4', '3.2']),
    ]
    for r, (label, vals) in enumerate(rows):
        yy = y0 + header_h + r * row_h
        fill = '#ffffff' if r % 2 == 0 else '#f7f9fa'
        p.append(rect(x0, yy, total_w, row_h, fill))
        p.append(rect(x0, yy, label_w, row_h, 'none', '#8a969e', 1))
        p.append(txt(x0 + 12, yy + 27, label, 19, 700 if r == 0 else 400))
        for c, val in enumerate(vals):
            xx = x0 + label_w + c * col_w
            p.append(rect(xx, yy, col_w, row_h, 'none', '#8a969e', 1))
            p.append(txt(xx + col_w / 2, yy + 27, val, 19, 700 if c >= 6 else 400, '#17232d', 'middle'))
    p += [
        txt(42, 742, 'Footnote (1): Not seasonally adjusted.', 14, 400, '#5d6a73'),
        txt(42, 790, 'Source: U.S. Bureau of Labor Statistics', 15, 400, '#5d6a73'),
    ]
    # A serif table echoes the official statistical-release look and the reference's table example.
    (OUT / 'lab11-bls-cpi.svg').write_text(svg_doc(p).replace('font-family="sans-serif"', 'font-family="serif"'), encoding='utf-8')


def build_census():
    p = []
    common_header(p, 'United States Census Bureau', 'CENSUS.GOV  /  BUSINESS & ECONOMY  /  ECONOMIC INDICATORS', '#263e68')
    p += [
        txt(300, 138, 'Census.gov  >  Economic Indicators  >  Press Release', 15, 400, '#65737d'),
        txt(42, 184, 'New Residential', 21, 700, '#263e68'),
        txt(42, 210, 'Construction', 21, 700, '#263e68'),
        txt(42, 252, 'Main', 17, 700, '#355577'),
        txt(42, 290, 'About the survey', 17, 400, '#455b70'),
        txt(42, 328, 'Data', 17, 400, '#455b70'),
        txt(42, 366, 'Technical documentation', 16, 400, '#455b70'),
        txt(42, 404, 'Release schedule', 17, 400, '#455b70'),
        line(265, 160, 265, 760, '#d3d9df', 1),
        txt(300, 170, 'FOR IMMEDIATE RELEASE: Tuesday, October 20, 2026', 15, 700, '#566573'),
        txt(300, 210, 'MONTHLY NEW RESIDENTIAL CONSTRUCTION,', 27, 700),
        txt(300, 244, 'SEPTEMBER 2026', 27, 700),
        txt(300, 280, 'October 20, 2026  •  CB26-162', 16, 400, '#65737d'),
        txt(300, 320, 'Building Permits', 22, 700),
    ]
    lines = [
        'Privately-owned housing units authorized by building permits in September were at a',
        'seasonally adjusted annual rate of 1,400,000. This is 0.2 percent below the revised',
        'August rate of 1,403,000 and is 3.0 percent below the September 2025 rate of 1,444,000.',
        'Single-family authorizations in September were at a rate of 845,000; this is 4.0 percent',
        'below the revised August figure of 880,000.',
    ]
    for i, s in enumerate(lines):
        p.append(txt(300, 360 + i * 34, s, 20))
    p += [
        txt(300, 566, 'Housing Starts', 22, 700),
        txt(300, 606, 'Privately-owned housing starts in September were at a seasonally adjusted annual rate', 20),
        txt(300, 640, 'of 1,221,000. This is 5.2 percent (±11.8 percent) below the revised August estimate.', 20),
        txt(300, 700, 'Housing Completions', 22, 700),
        txt(300, 740, 'Privately-owned housing completions in September were at a seasonally adjusted annual rate', 20),
        txt(300, 774, 'of 1,192,000.', 20),
        line(300, 812, 1215, 812, '#c8d0d6', 1),
        txt(300, 846, 'Additional Release Materials  •  Current Press Release  •  Tables', 16, 400, '#52687b'),
    ]
    (OUT / 'lab11-census-construction.svg').write_text(svg_doc(p), encoding='utf-8')


def build_eia():
    p = []
    common_header(p, 'U.S. Energy Information Administration', 'EIA.GOV  /  ENERGY EXPLAINED  /  U.S. ENERGY FACTS', '#18536e')
    p += [
        txt(300, 138, 'Energy Explained  >  U.S. energy facts  >  Consumption and production', 15, 400, '#65737d'),
        txt(42, 190, 'Energy Explained', 22, 700, '#18536e'),
        txt(42, 232, 'What is energy?', 17, 400, '#455b70'),
        txt(42, 270, 'Units and calculators', 17, 400, '#455b70'),
        txt(42, 308, 'U.S. energy facts', 17, 700, '#18536e'),
        txt(42, 346, 'Use of energy', 17, 400, '#455b70'),
        txt(42, 384, 'Energy and the', 17, 400, '#455b70'),
        txt(42, 409, 'environment', 17, 400, '#455b70'),
        line(265, 160, 265, 760, '#d3d9df', 1),
        txt(300, 175, 'U.S. energy facts explained', 32, 700),
        txt(300, 225, 'Measuring consumption and production', 24, 700),
        txt(300, 267, 'The transportation, industrial, residential, and commercial sectors are called end-use sectors.', 19),
        txt(300, 295, 'They consume primary energy and electricity produced by the electric power sector.', 19),
        txt(300, 350, 'Total energy consumption by the end-use sectors includes:', 21, 700),
    ]
    bullets = [
        (400, 'Primary energy use'),
        (450, 'Purchased electricity'),
        (500, 'Electrical system energy losses (energy conversion and other losses associated with'),
        (538, 'generating, transmitting, and distributing purchased electricity)'),
        (588, 'Other energy losses'),
    ]
    for idx, (yy, s) in enumerate(bullets):
        continuation = idx == 3
        if not continuation:
            p.append(txt(312, yy, '•', 23, 700, '#263943'))
        p.append(txt(340 if not continuation else 364, yy, s, 21))
    p += [
        txt(300, 670, 'Energy consumption by sector', 23, 700),
        txt(300, 710, 'The energy sources each sector primarily uses vary widely.', 19),
        txt(300, 740, 'Petroleum is the primary fuel in the transportation sector’s energy consumption mix.', 19),
        line(300, 790, 1215, 790, '#c8d0d6', 1),
        txt(300, 824, 'Source: U.S. Energy Information Administration  •  Monthly Energy Review', 16, 400, '#52687b'),
    ]
    (OUT / 'lab11-eia-sectors.svg').write_text(svg_doc(p), encoding='utf-8')


if __name__ == '__main__':
    build_bls()
    build_census()
    build_eia()
    print('Built lab11-bls-cpi.svg, lab11-census-construction.svg, lab11-eia-sectors.svg')
