"""Draw the demo hunts' "photos": cartoon household objects as SVG (theme/assets/demo-<name>.svg).

    python -I tools/make_demo_art.py

Each picture is a 400x400 scene (a wall, a floor line, a soft shadow) with one object in the middle, drawn with the
app's ink outline, so the example hunts, the album and the landing page look alive without real photos.
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "theme" / "assets"
INK = "#3A1E2A"
S = 'stroke="%s" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"' % INK


def scene(wall, floor, body, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" role="img" aria-label="%s">'
            '<rect width="400" height="400" fill="%s"/><rect y="292" width="400" height="108" fill="%s"/>'
            '<path d="M0 292h400" stroke="%s" stroke-opacity=".15" stroke-width="4"/>'
            '<ellipse cx="200" cy="318" rx="118" ry="16" fill="%s" fill-opacity=".14"/>%s</svg>\n' % (title, wall, floor, INK, INK, body))


ART = {
    "teapot": ("#DDEBFF", "#B98A6A", "A spotty teapot",
               '<path d="M118 196c-30-8-52 14-44 40 6 20 30 30 52 28" fill="none" %s/>'
               '<path d="M282 214l52-38c10-6 18 2 12 12l-46 70" fill="#FF9DBD" %s/>'
               '<path d="M120 190c0-40 36-62 80-62s80 22 80 62v70c0 26-26 46-80 46s-80-20-80-46z" fill="#FF9DBD" %s/>'
               '<path d="M152 134c10-24 86-24 96 0" fill="#F0679A" %s/><circle cx="200" cy="112" r="14" fill="#FFC234" %s/>'
               '<circle cx="160" cy="210" r="11" fill="#fff"/><circle cx="214" cy="190" r="9" fill="#fff"/><circle cx="244" cy="240" r="12" fill="#fff"/>'
               '<circle cx="186" cy="262" r="8" fill="#fff"/><circle cx="150" cy="268" r="6" fill="#fff"/>' % (S, S, S, S, S)),
    "teddy": ("#FFF0D9", "#9C7BB0", "A teddy bear",
              '<circle cx="146" cy="104" r="28" fill="#C8875A" %s/><circle cx="254" cy="104" r="28" fill="#C8875A" %s/>'
              '<ellipse cx="200" cy="240" rx="76" ry="70" fill="#C8875A" %s/><ellipse cx="200" cy="246" rx="44" ry="42" fill="#F2C9A0"/>'
              '<ellipse cx="128" cy="286" rx="30" ry="24" fill="#C8875A" %s/><ellipse cx="272" cy="286" rx="30" ry="24" fill="#C8875A" %s/>'
              '<circle cx="200" cy="142" r="66" fill="#C8875A" %s/><ellipse cx="200" cy="164" rx="30" ry="22" fill="#F2C9A0" %s/>'
              '<circle cx="176" cy="130" r="7" fill="%s"/><circle cx="224" cy="130" r="7" fill="%s"/><path d="M192 156h16l-8 8z" fill="%s" %s/>'
              '<path d="M182 200l18 14 18-14" fill="#FF6FA3" %s/><circle cx="200" cy="208" r="7" fill="#FF6FA3" %s/>' % (S, S, S, S, S, S, S, INK, INK, INK, S, S, S)),
    "duck": ("#CFF3F7", "#7FC8DD", "A yellow rubber duck",
             '<path d="M96 236c0-30 40-44 86-38l60-6c40 0 66 28 62 62-4 40-48 60-104 60s-104-24-104-78z" fill="#FFD43B" %s/>'
             '<circle cx="232" cy="150" r="54" fill="#FFD43B" %s/><path d="M280 152c22-6 44 2 50 14-12 12-34 14-52 6" fill="#FF8A3D" %s/>'
             '<circle cx="246" cy="134" r="8" fill="%s"/><circle cx="249" cy="131" r="2.5" fill="#fff"/>'
             '<path d="M140 238c20 26 60 30 84 6" fill="none" %s/>' % (S, S, S, INK, S)),
    "ball": ("#FFF6CC", "#7CC6A4", "A stripy beach ball",
             '<circle cx="200" cy="200" r="104" fill="#fff" %s/>'
             '<path d="M200 96c-40 30-56 70-56 104s16 74 56 104c-56 0-104-46-104-104S144 96 200 96z" fill="#FF6FA3"/>'
             '<path d="M200 96c40 30 56 70 56 104s-16 74-56 104c56 0 104-46 104-104S256 96 200 96z" fill="#4A7BF0"/>'
             '<path d="M200 96c-14 30-18 70-18 104s4 74 18 104c14-30 18-70 18-104s-4-74-18-104z" fill="#FFC234"/>'
             '<circle cx="200" cy="200" r="104" fill="none" %s/><circle cx="200" cy="200" r="16" fill="#fff" %s/>' % (S, S, S)),
    "book": ("#E7F7E9", "#C59A72", "A big dinosaur book",
             '<path d="M92 112h196c10 0 16 6 16 16v168c0 8-6 14-16 14H92z" fill="#22B07F" %s/>'
             '<path d="M92 112v198" %s/><rect x="104" y="296" width="196" height="14" fill="#fff" %s/>'
             '<path d="M150 236c0-26 18-44 44-44h20l8-22c12-4 26 4 28 14l-10 2 2 14c14 6 18 20 14 36z" fill="#FFC234" %s/>'
             '<path d="M164 204l6-12 10 10M184 194l6-12 10 10" fill="none" %s/><circle cx="234" cy="184" r="4" fill="%s"/>'
             '<path d="M130 140h130" stroke="#fff" stroke-width="10" stroke-linecap="round"/>' % (S, S, S, S, S, INK)),
    "sock": ("#FDE2EA", "#8FB6E8", "A rainbow sock",
             '<path d="M150 80h92v150c0 18 6 26 18 34 24 16 30 40 14 56-16 18-46 16-76 2l-46-22c-20-10-24-22-24-42V80z" fill="#fff" %s/>'
             '<path d="M150 80h92v30h-92z" fill="#FF6FA3"/><path d="M150 110h92v30h-92z" fill="#FF8A3D"/>'
             '<path d="M150 140h92v30h-92z" fill="#FFC234"/><path d="M150 170h92v30h-92z" fill="#22B07F"/>'
             '<path d="M150 200h92v30h-92z" fill="#4A7BF0"/>'
             '<path d="M150 80h92v150c0 18 6 26 18 34 24 16 30 40 14 56-16 18-46 16-76 2l-46-22c-20-10-24-22-24-42V80z" fill="none" %s/>'
             '<path d="M150 80h92" %s/>' % (S, S, S)),
    "banana": ("#E5F0FF", "#D4A373", "A banana",
               '<path d="M96 168c40 92 150 120 214 60 10-10 4-22-8-18-60 26-136 4-180-60z" fill="#FFD43B" %s/>'
               '<path d="M122 150c-8-10-6-22 4-26l14 4c4 8 2 18-4 24z" fill="#8A5A43" %s/>'
               '<path d="M130 176c44 56 110 70 160 48" fill="none" stroke="#E0A800" stroke-width="5" stroke-linecap="round"/>'
               '<circle cx="306" cy="214" r="5" fill="%s"/>' % (S, S, INK)),
    "plant": ("#FFF1E6", "#B5838D", "A cactus in a pot",
              '<path d="M176 236V120c0-18 12-30 24-30s24 12 24 30v116z" fill="#22B07F" %s/>'
              '<path d="M176 190h-26c-14 0-22-8-22-22v-26c0-8 6-12 12-12s12 4 12 12v20h24" fill="#22B07F" %s/>'
              '<path d="M224 172h22c12 0 20-8 20-20v-20c0-8-6-12-12-12s-12 4-12 12v16h-18" fill="#22B07F" %s/>'
              '<path d="M200 110v6M190 150v6M210 180v6M194 210v6" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
              '<circle cx="200" cy="94" r="10" fill="#FF6FA3" %s/>'
              '<path d="M136 236h128l-14 76h-100z" fill="#FF8A3D" %s/><path d="M130 236h140v20H130z" fill="#FF8A3D" %s/>' % (S, S, S, S, S, S)),
    "clock": ("#EAF4FF", "#9DB4C0", "A round clock",
              '<circle cx="200" cy="190" r="100" fill="#fff" %s/><circle cx="200" cy="190" r="84" fill="none" stroke="#4A7BF0" stroke-width="8"/>'
              '<path d="M200 190v-52M200 190l38 20" %s/><circle cx="200" cy="190" r="8" fill="%s"/>'
              '<path d="M200 116v10M200 254v10M126 190h10M264 190h10" %s/>'
              '<path d="M136 290l-14 22M264 290l14 22" %s/>' % (S, S, INK, S, S)),
    "toothbrush": ("#E8FAF4", "#8ECAE6", "A toothbrush and a cup",
                   '<path d="M150 186h100l-10 120h-80z" fill="#4A7BF0" %s/>'
                   '<path d="M214 196l46-120" stroke="%s" stroke-width="22" stroke-linecap="round"/>'
                   '<path d="M214 196l46-120" stroke="#FF6FA3" stroke-width="12" stroke-linecap="round"/>'
                   '<path d="M248 70l30 10-10 30-30-10z" fill="#fff" %s/><path d="M256 74l-8 24M266 78l-8 24" stroke="#4A7BF0" stroke-width="3"/>'
                   '<circle cx="176" cy="240" r="9" fill="#fff" fill-opacity=".7"/>' % (S, INK, S)),
}


def main():
    for name, (wall, floor, title, body) in ART.items():
        (OUT / ("demo-%s.svg" % name)).write_bytes(scene(wall, floor, body, title).encode("utf-8"))
    print("wrote %d demo pictures" % len(ART))


if __name__ == "__main__":
    main()
