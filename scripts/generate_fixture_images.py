from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
COMICS = ROOT / 'your_content' / 'comics'
SIZE = (1000, 1352)
INK = '#1f2430'
PAPER = '#fffdf8'


def load_fonts() -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    candidates = [
        ('arialbd.ttf', 64),
        ('arialbd.ttf', 42),
        ('arial.ttf', 28),
        ('arial.ttf', 22),
    ]
    fallback = ImageFont.load_default()
    fonts = {}
    names = ['banner', 'title', 'body', 'small']
    for name, (font_name, size) in zip(names, candidates):
        try:
            fonts[name] = ImageFont.truetype(font_name, size)
        except OSError:
            fonts[name] = fallback
    return fonts


FONTS = load_fonts()


def new_page(bg: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new('RGB', SIZE, bg)
    return img, ImageDraw.Draw(img)


def rounded(draw, box, fill, outline=INK, width=5, radius=26):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def banner(draw, text: str, subtitle: str, fill: str):
    rounded(draw, (120, 28, 880, 120), fill=fill, radius=28, width=6)
    draw.text((500, 64), text, font=FONTS['banner'], fill=PAPER, anchor='mm')
    draw.text((500, 103), subtitle, font=FONTS['small'], fill=PAPER, anchor='mm')


def skyline(draw, sky: str, city: str):
    draw.rectangle((0, 0, 1000, 520), fill=sky)
    for i, x in enumerate(range(30, 1000, 95)):
        h = 120 + (i % 5) * 45
        draw.rectangle((x, 520 - h, x + 65, 520), fill=city)
        for wy in range(520 - h + 16, 520 - 16, 28):
            for wx in range(x + 10, x + 56, 18):
                draw.rectangle((wx, wy, wx + 8, wy + 10), fill='#f6d365')


def floor(draw, top='#d8b07a', rail='#8c6244'):
    draw.rectangle((0, 520, 1000, 1352), fill=top)
    draw.rectangle((0, 520, 1000, 560), fill='#b17e52')
    for x in range(0, 1000, 60):
        draw.rectangle((x, 520, x + 18, 760), fill=rail)
    draw.rectangle((0, 742, 1000, 772), fill='#6f4c38')


def person(draw, *, x=500, y=700, shirt='#f2c14e', hair='#4b3529', legs='#457b9d', pose='open'):
    skin = '#f2c7a5'
    draw.ellipse((x - 84, y - 134, x + 84, y + 34), fill=skin, outline=INK, width=6)
    draw.ellipse((x - 118, y - 170, x + 118, y - 18), fill=hair, outline=INK, width=6)
    draw.rectangle((x - 108, y - 18, x + 108, y + 278), fill=shirt, outline=INK, width=6)
    if pose == 'open':
        left_arm = [(x - 108, y + 28), (x - 184, y + 150), (x - 126, y + 188), (x - 64, y + 90)]
        right_arm = [(x + 108, y + 28), (x + 192, y + 152), (x + 140, y + 190), (x + 68, y + 90)]
    else:
        left_arm = [(x - 108, y + 38), (x - 170, y + 110), (x - 135, y + 152), (x - 66, y + 94)]
        right_arm = [(x + 108, y + 38), (x + 175, y + 110), (x + 138, y + 154), (x + 70, y + 96)]
    draw.polygon(left_arm, fill=skin, outline=INK)
    draw.polygon(right_arm, fill=skin, outline=INK)
    draw.polygon([(x - 40, y + 278), (x - 72, y + 472), (x - 12, y + 472), (x + 3, y + 278)], fill=legs, outline=INK)
    draw.polygon([(x + 40, y + 278), (x + 12, y + 472), (x + 72, y + 472), (x - 4, y + 278)], fill=legs, outline=INK)
    draw.ellipse((x - 40, y - 70, x - 16, y - 46), fill=INK)
    draw.ellipse((x + 16, y - 70, x + 40, y - 46), fill=INK)
    draw.arc((x - 40, y - 28, x + 40, y + 26), start=15, end=165, fill=INK, width=5)


def speech(draw, lines: list[str], accent='#457b9d'):
    rounded(draw, (120, 145, 880, 420), fill=PAPER, radius=40, width=7)
    draw.polygon([(468, 420), (538, 420), (502, 505)], fill=PAPER, outline=INK)
    y = 225
    for i, line in enumerate(lines):
        font = FONTS['title'] if i < 2 else FONTS['body']
        fill = INK if i < 2 else accent
        draw.text((500, y), line, font=font, fill=fill, anchor='mm')
        y += 64 if i < 2 else 42


def label_box(draw, box, fill, title, lines=3):
    rounded(draw, box, fill=fill, radius=18)
    x1, y1, x2, y2 = box
    for idx in range(lines):
        yy = y1 + 52 + idx * 40
        draw.line((x1 + 24, yy, x2 - 24, yy), fill=INK, width=4)
    draw.text(((x1 + x2) / 2, y2 + 36), title, font=FONTS['small'], fill=INK, anchor='mm')


def arrow(draw, start, end):
    draw.line((start, end), fill=INK, width=6)
    ex, ey = end
    draw.polygon([(ex, ey), (ex - 18, ey + 10), (ex - 8, ey - 18)], fill=INK)


def save(img: Image.Image, rel: str):
    path = COMICS / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='PNG')
    print(path)


def remove_stale_thumbnails():
    for page in ['002', '003', '004', '005', '006', '007', '008', '009', '010']:
        thumb = COMICS / page / '_thumbnail.jpg'
        if thumb.exists():
            thumb.unlink()
            print(f'removed {thumb}')


def page_002():
    img, draw = new_page('#f4efe6')
    skyline(draw, '#d7ecff', '#6f8fa8')
    floor(draw)
    banner(draw, 'FULL METADATA', 'Page 002', '#d85b57')
    speech(draw, ['This page is carrying all the usual', 'metadata fields on purpose.', 'ALT TEXT  •  STORYLINE  •  TAGS  •  CHARACTERS'])
    person(draw, shirt='#f0c419')
    label_box(draw, (70, 880, 290, 1120), '#ffd6a5', 'ALT TEXT')
    label_box(draw, (390, 900, 610, 1140), '#caffbf', 'TAGS')
    label_box(draw, (710, 860, 930, 1100), '#bde0fe', 'STORYLINE')
    arrow(draw, (290, 970), (380, 910))
    arrow(draw, (610, 980), (700, 930))
    arrow(draw, (500, 1060), (500, 820))
    draw.text((500, 722), 'This panel should be easy to spot in a visual test run.', font=FONTS['body'], fill=INK, anchor='mm')
    save(img, '002/Page 2.png')


def page_003(filename: str, label: str, bg: str, accent: str, order_note: str):
    img, draw = new_page(bg)
    rounded(draw, (70, 70, 930, 1282), fill='#fff8ef', radius=36, width=7)
    banner(draw, f'IMAGE ORDER {label}', order_note, accent)
    draw.text((500, 240), f'PANEL {label}', font=FONTS['banner'], fill=accent, anchor='mm')
    draw.rectangle((180, 360, 820, 930), fill='#f7ead2', outline=INK, width=6)
    draw.ellipse((300, 470, 500, 670), fill='#ffe08a', outline=INK, width=6)
    draw.ellipse((500, 470, 700, 670), fill='#a8dadc', outline=INK, width=6)
    draw.text((400, 570), label, font=FONTS['banner'], fill=INK, anchor='mm')
    other = 'A' if label == 'B' else 'B'
    draw.text((600, 570), other, font=FONTS['banner'], fill=INK, anchor='mm')
    draw.text((500, 995), 'The explicit Filenames list should control which panel appears first.', font=FONTS['body'], fill=INK, anchor='mm')
    draw.text((500, 1044), f'This file is intentionally named {filename}.', font=FONTS['small'], fill=accent, anchor='mm')
    save(img, f'003/{filename}')


def page_004(filename: str, label: str, bg: str, accent: str, hidden: bool = False):
    img, draw = new_page(bg)
    banner_text = 'HIDDEN FILE' if hidden else 'AUTO DISCOVERY'
    banner(draw, banner_text, f'{filename} should {"not render" if hidden else "render automatically"}', accent)
    rounded(draw, (120, 180, 880, 1180), fill='#fffdf5', radius=38, width=7)
    draw.text((500, 340), label, font=FONTS['banner'], fill=accent, anchor='mm')
    for idx, x in enumerate((230, 500, 770)):
        draw.ellipse((x - 85, 470, x + 85, 640), fill=['#e76f51', '#2a9d8f', '#e9c46a'][idx], outline=INK, width=6)
    draw.text((500, 760), 'No Filename field here.', font=FONTS['title'], fill=INK, anchor='mm')
    draw.text((500, 825), 'The engine should discover visible image files in sorted order.', font=FONTS['body'], fill=INK, anchor='mm')
    if hidden:
        draw.rectangle((160, 930, 840, 1090), fill='#ffcad4', outline=INK, width=6)
        draw.text((500, 1010), 'If you ever see this panel, hidden-file filtering broke.', font=FONTS['body'], fill=INK, anchor='mm')
    save(img, f'004/{filename}')


def page_005():
    img, draw = new_page('#f8f5ed')
    banner(draw, 'POST TEXT', 'Singular Filename case', '#588157')
    rounded(draw, (140, 200, 860, 1160), fill='#fffdf8', radius=34, width=7)
    draw.rectangle((320, 360, 680, 980), fill='#f2e8cf', outline=INK, width=7)
    draw.rectangle((360, 300, 640, 380), fill='#a3b18a', outline=INK, width=6)
    for y in range(470, 920, 70):
        draw.line((385, y, 615, y), fill='#7f5539', width=5)
    person(draw, x=170, y=760, shirt='#84a98c', hair='#3d405b', legs='#bc6c25', pose='closed')
    person(draw, x=835, y=760, shirt='#dda15e', hair='#6d597a', legs='#6c757d', pose='closed')
    draw.text((500, 1045), 'This page is paired with a visible post.txt body.', font=FONTS['title'], fill=INK, anchor='mm')
    draw.text((500, 1105), 'The cover image should feel like a title card for attached notes.', font=FONTS['body'], fill='#588157', anchor='mm')
    save(img, '005/cover.png')


def page_006():
    img, draw = new_page('#eef6ff')
    banner(draw, 'TRANSCRIPTS', 'English.md should win over English.txt', '#6d597a')
    rounded(draw, (80, 160, 920, 1230), fill='#fffdf8', radius=36, width=7)
    rounded(draw, (130, 270, 450, 520), fill='#cde7ff', radius=26)
    rounded(draw, (550, 270, 870, 520), fill='#ffd6e0', radius=26)
    person(draw, x=290, y=760, shirt='#90caf9', hair='#264653', legs='#577590')
    person(draw, x=710, y=760, shirt='#ffafcc', hair='#5a189a', legs='#4361ee')
    draw.text((290, 396), 'ENGLISH', font=FONTS['title'], fill=INK, anchor='mm')
    draw.text((710, 396), 'FRANCAIS', font=FONTS['title'], fill=INK, anchor='mm')
    draw.text((500, 1040), 'Lots of spoken dialogue belongs here.', font=FONTS['title'], fill=INK, anchor='mm')
    draw.text((500, 1100), 'This panel is meant to look transcript-heavy at a glance.', font=FONTS['body'], fill='#6d597a', anchor='mm')
    save(img, '006/Page 6.png')


def page_007():
    img, draw = new_page('#0b1d35')
    draw.rectangle((0, 0, 1000, 1352), fill='#102542')
    for r in range(30, 330, 30):
        draw.ellipse((500 - r, 520 - r, 500 + r, 520 + r), outline='#f4d35e', width=5)
    banner(draw, 'SOCIAL OVERRIDE', 'Dramatic share-card moment', '#c1121f')
    person(draw, x=500, y=760, shirt='#f4d35e', hair='#1b1b1e', legs='#669bbc')
    draw.rectangle((250, 930, 750, 1110), fill='#fefae0', outline=INK, width=7)
    draw.text((500, 995), 'ANNOUNCEMENT', font=FONTS['title'], fill='#c1121f', anchor='mm')
    draw.text((500, 1050), 'Strong focal image for custom social preview metadata.', font=FONTS['body'], fill=INK, anchor='mm')
    save(img, '007/Page 7.png')


def page_008():
    img, draw = new_page('#edf6f9')
    skyline(draw, '#d0f4de', '#588157')
    floor(draw, top='#cdb4db', rail='#6d597a')
    banner(draw, 'EXTRA FIELDS', 'Mood, Location, Custom CTA', '#7b2cbf')
    person(draw, x=500, y=720, shirt='#ffbe0b', hair='#432818', legs='#3a86ff')
    for box, color, text in [
        ((120, 900, 330, 1120), '#ffcad4', 'MOOD'),
        ((395, 840, 605, 1060), '#d9ed92', 'LOCATION'),
        ((670, 900, 880, 1120), '#a0c4ff', 'CTA'),
    ]:
        label_box(draw, box, color, text)
    draw.text((500, 1185), 'This page should feel like it has extra contextual metadata.', font=FONTS['body'], fill=INK, anchor='mm')
    save(img, '008/Page 8.png')


def page_009():
    img, draw = new_page('#f1f3f5')
    banner(draw, 'EXTERNAL TRANSCRIPT', 'Transcript lives outside the page folder', '#3a5a40')
    rounded(draw, (100, 180, 900, 1180), fill='#fffdf8', radius=36, width=7)
    draw.ellipse((500 - 250, 520 - 250, 500 + 250, 520 + 250), fill='#ced4da', outline=INK, width=6)
    draw.ellipse((500 - 160, 520 - 160, 500 + 160, 520 + 160), fill='#adb5bd', outline=INK, width=6)
    draw.rectangle((425, 740, 575, 1030), fill='#6c757d', outline=INK, width=6)
    draw.rectangle((360, 930, 640, 1010), fill='#495057', outline=INK, width=6)
    draw.arc((300, 320, 700, 720), start=300, end=30, fill='#52b788', width=10)
    draw.arc((250, 270, 750, 770), start=300, end=30, fill='#40916c', width=10)
    draw.text((500, 1110), 'Broadcast-style dialogue belongs here.', font=FONTS['title'], fill=INK, anchor='mm')
    draw.text((500, 1168), 'The transcript source should still be found from the shared folder.', font=FONTS['body'], fill='#3a5a40', anchor='mm')
    save(img, '009/Page 9.png')


def page_010():
    img, draw = new_page('#0b132b')
    for i in range(0, 1000, 70):
        for j in range(0, 1352, 90):
            r = 4 + ((i + j) // 40) % 4
            draw.ellipse((i + 20, j + 20, i + 20 + r, j + 20 + r), fill='#f8f9fa')
    banner(draw, 'FUTURE PAGE', 'This should stay unpublished in normal builds', '#ef476f')
    draw.ellipse((250, 360, 750, 860), fill='#1c2541', outline='#5bc0be', width=7)
    draw.ellipse((380, 510, 620, 750), fill='#5bc0be', outline=INK, width=6)
    draw.rectangle((455, 820, 545, 1045), fill='#f4d35e', outline=INK, width=6)
    draw.rectangle((390, 930, 610, 995), fill='#ee964b', outline=INK, width=6)
    draw.text((500, 1095), 'COMING LATER', font=FONTS['banner'], fill='#f4d35e', anchor='mm')
    draw.text((500, 1160), 'If this page appears in the site, scheduled-post logic failed.', font=FONTS['body'], fill=PAPER, anchor='mm')
    save(img, '010/Future Page.png')


def main():
    remove_stale_thumbnails()
    page_002()
    page_003('panel-b.png', 'B', '#fff0f0', '#d62828', 'This image should render first.')
    page_003('panel-a.png', 'A', '#eef7ff', '#277da1', 'This image should render second.')
    page_004('alpha.png', 'ALPHA', '#f6fff8', '#2d6a4f')
    page_004('beta.png', 'BETA', '#fff7ed', '#bc6c25')
    page_004('_hidden.png', 'HIDDEN', '#fff0f3', '#ff006e', hidden=True)
    page_005()
    page_006()
    page_007()
    page_008()
    page_009()
    page_010()


if __name__ == '__main__':
    main()
