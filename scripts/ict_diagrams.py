#!/usr/bin/env python3
"""Draw original, labelled teaching diagrams; no external images or generation service.

Coordinates are deliberately explicit so technical relationships remain reviewable.
The PNGs are embedded in both exports and remain available beside the Markdown.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notes/upper-sixth-ict/figures"
FONT_DIR = Path(os.environ.get("ICT_NOTES_FONT_DIR", "/usr/share/fonts/truetype/dejavu"))
W = 1800
INK = "#192D46"
BLUE = "#2459A6"
LIGHT = "#EEF4FC"
GREY = "#526276"
PALE = "#F5F6F8"
RED = "#9A2837"
WHITE = "white"


def font(size=38, bold=False, mono=False):
    family = "DejaVuSansMono" if mono else "DejaVuSans"
    suffix = "-Bold" if bold else ""
    return ImageFont.truetype(str(FONT_DIR / f"{family}{suffix}.ttf"), size)


class Diagram:
    def __init__(self, filename, height=700):
        self.filename = filename
        self.height = height
        self.im = Image.new("RGB", (W, height), WHITE)
        self.d = ImageDraw.Draw(self.im)

    def text(self, x, y, text, size=38, bold=False, color=INK, width=None,
             mono=False, align="center"):
        f = font(size, bold, mono)
        lines = []
        for explicit in str(text).split("\n"):
            if width is None:
                lines.append(explicit)
                continue
            current = ""
            for word in explicit.split():
                candidate = (current + " " + word).strip()
                if current and self.d.textlength(candidate, font=f) > width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        text = "\n".join(lines)
        bbox = self.d.multiline_textbbox((0, 0), text, font=f, spacing=10, align=align)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        left, top = x - tw / 2, y - th / 2
        if left < 8 or top < 8 or left + tw > W - 8 or top + th > self.height - 8:
            raise ValueError(f"Out-of-bounds text in {self.filename}: {text!r}")
        self.d.multiline_text((left - bbox[0], top - bbox[1]), text, font=f,
                              fill=color, spacing=10, align=align)
        return tw, th

    def box(self, x, y, width, height, text, fill=LIGHT, color=BLUE, size=38):
        rect = (x - width / 2, y - height / 2, x + width / 2, y + height / 2)
        self.d.rounded_rectangle(rect, radius=18, fill=fill, outline=color, width=4)
        tw, th = self.text(x, y, text, size=size, width=width - 35)
        if tw > width - 20 or th > height - 16:
            raise ValueError(f"Text does not fit box in {self.filename}: {text!r}")

    def line(self, a, b, color=GREY, width=5, dashed=False):
        if not dashed:
            self.d.line([a, b], fill=color, width=width)
            return
        dx, dy = b[0] - a[0], b[1] - a[1]
        distance = math.hypot(dx, dy)
        for start in range(0, int(distance), 30):
            end = min(start + 17, distance)
            self.d.line([(a[0] + dx * start / distance, a[1] + dy * start / distance),
                         (a[0] + dx * end / distance, a[1] + dy * end / distance)],
                        fill=color, width=width)

    def arrow(self, a, b, color=BLUE, both=False, dashed=False, width=5):
        self.line(a, b, color, width, dashed)
        def head(start, end):
            angle = math.atan2(end[1] - start[1], end[0] - start[0])
            length, spread = 22, 0.45
            points = [end,
                      (end[0] - length * math.cos(angle - spread),
                       end[1] - length * math.sin(angle - spread)),
                      (end[0] - length * math.cos(angle + spread),
                       end[1] - length * math.sin(angle + spread))]
            self.d.polygon(points, fill=color)
        head(a, b)
        if both:
            head(b, a)

    def save(self):
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / self.filename
        self.im.save(path, optimize=True, dpi=(300, 300))
        return path


def draw_all():
    made = []
    def save(d):
        made.append(d.save())

    d = Diagram("01-ai-flow.png", 680)
    d.box(330, 165, 470, 150, "Examples + known answers")
    d.arrow((580, 165), (725, 165))
    d.box(970, 165, 470, 150, "Training learns useful patterns")
    d.arrow((970, 245), (970, 385))
    d.box(330, 470, 470, 150, "New input: a message or image")
    d.arrow((580, 470), (725, 470))
    d.box(970, 470, 470, 150, "Learned model")
    d.arrow((1210, 470), (1345, 470))
    d.box(1545, 470, 380, 150, "Prediction or generated output", size=35)
    d.text(1000, 615, "Human checks the output and its consequences", 35)
    save(d)

    d = Diagram("02-intelligent-loop.png", 690)
    labels = ["Sensor gathers input", "Rules or model interpret", "Action or recommendation", "Measure the result"]
    for x, label in zip([270, 690, 1110, 1530], labels):
        d.box(x, 260, 340, 175, label, size=37)
    for x in [440, 860, 1280]:
        d.arrow((x, 260), (x + 80, 260))
    d.line((1530, 350), (1530, 555), BLUE)
    d.line((1530, 555), (270, 555), BLUE)
    d.arrow((270, 555), (270, 350))
    d.text(900, 495, "Feedback supports the next decision", 37, bold=True)
    save(d)

    d = Diagram("03-train-test.png", 700)
    d.box(330, 160, 470, 170, "Training images + correct labels")
    d.arrow((580, 160), (825, 160))
    d.box(1110, 160, 550, 170, "Train and adjust model")
    d.arrow((1110, 250), (1110, 405))
    d.box(330, 495, 470, 170, "Separate, unseen test images", fill=PALE)
    d.arrow((580, 495), (825, 495))
    d.box(1110, 495, 550, 170, "Use the trained model without retraining")
    d.arrow((1390, 495), (1500, 495))
    d.box(1610, 495, 210, 170, "Check output", size=32)
    d.text(920, 645, "Do not reuse training pictures as the independent test.", 35, bold=True)
    save(d)

    d = Diagram("04-ai-development.png", 730)
    points = [(330, 180), (900, 180), (1470, 180), (1470, 530), (900, 530), (330, 530)]
    labels = ["1 Define problem", "2 Collect and prepare data", "3 Train model", "4 Evaluate on new cases", "5 Deploy safely", "6 Monitor and improve"]
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        if a[1] == b[1]:
            sign = 1 if b[0] > a[0] else -1
            d.arrow((a[0] + sign * 220, a[1]), (b[0] - sign * 220, b[1]))
        else:
            sign = 1 if b[1] > a[1] else -1
            d.arrow((a[0], a[1] + sign * 90), (b[0], b[1] - sign * 90))
    for (x, y), label in zip(points, labels):
        d.box(x, y, 440, 175, label)
    d.text(900, 355, "Revise earlier decisions when evidence requires it", 34, width=650)
    save(d)

    d = Diagram("05-local-network.png", 790)
    for a, b in [((280, 220), (650, 370)), ((280, 550), (650, 370)),
                 ((650, 370), (1130, 130)), ((650, 370), (1130, 370)),
                 ((650, 370), (1130, 620)), ((1130, 620), (1570, 620))]:
        d.line(a, b, BLUE)
    for x, y, w, h, t in [(280, 220, 360, 140, "Computer A"), (280, 550, 360, 140, "Computer B"),
                           (650, 370, 310, 140, "Switch"), (1130, 130, 360, 140, "Network printer"),
                           (1130, 370, 360, 140, "Local file service"), (1130, 620, 310, 140, "Router"),
                           (1570, 620, 340, 140, "Other networks / Internet")]:
        d.box(x, y, w, h, t, size=35)
    d.text(1500, 265, "Local sharing does not require the external link.", 35, width=410)
    save(d)

    d = Diagram("06-network-scope.png", 760)
    labels = [(230, 150, "PAN", "Around one person"), (560, 265, "LAN", "Home, room or building"),
              (890, 380, "CAN", "Several campus buildings"), (1220, 495, "MAN", "City-scale sites"),
              (1550, 610, "WAN", "Distant towns or regions")]
    for i, (x, y, short, detail) in enumerate(labels):
        if i:
            px, py = labels[i - 1][:2]
            d.arrow((px + 135, py + 65), (x - 135, y - 65))
        d.box(x, y, 290, 190, short + "\n" + detail, size=33)
    d.text(1100, 110, "Coverage categories describe extent, not fixed speeds.", 38, width=1000, bold=True)
    save(d)

    d = Diagram("07-architectures.png", 700)
    d.text(440, 90, "Peer-to-peer services", 42, bold=True)
    d.text(1340, 90, "Client/server service", 42, bold=True)
    peers = [(220, 250), (650, 250), (435, 530)]
    for i, a in enumerate(peers):
        for b in peers[i + 1:]:
            d.arrow(a, b, both=True)
    for i, (x, y) in enumerate(peers, 1):
        d.box(x, y, 245, 110, f"Peer {i}", size=35)
    for x in [1080, 1340, 1600]:
        d.arrow((x, 475), (1340, 280), both=True)
        d.box(x, 530, 235, 110, "Client", size=35)
    d.box(1340, 225, 430, 110, "Shared server", size=38)
    d.line((890, 130), (890, 625), "#C3CCD8", 3, dashed=True)
    d.text(900, 655, "Service roles are different from physical cable topology.", 34)
    save(d)

    d = Diagram("08-topology-star.png", 780)
    points = [(400, 180, "Computer A"), (1400, 180, "Computer B"),
              (330, 590, "Computer C"), (1470, 590, "Printer"), (900, 655, "Computer D")]
    for x, y, _ in points:
        d.line((900, 355), (x, y), BLUE)
    for x, y, text in points:
        d.box(x, y, 330, 110, text, size=35)
    d.box(900, 355, 350, 140, "Central switch", size=39)
    d.text(900, 80, "STAR: a separate endpoint link to the centre", 39, bold=True)
    save(d)

    d = Diagram("09-topology-bus.png", 600)
    d.text(900, 80, "BUS: one shared backbone", 42, bold=True)
    d.line((200, 390), (1600, 390), BLUE, 10)
    for x in [200, 1600]:
        d.line((x, 350), (x, 430), INK, 10)
    for x, name in zip([430, 900, 1370], ["Computer A", "Computer B", "Computer C"]):
        d.line((x, 240), (x, 390), BLUE)
        d.box(x, 185, 330, 110, name, size=35)
    d.text(210, 495, "Terminator", 33)
    d.text(1590, 495, "Terminator", 33)
    d.text(900, 450, "Shared coaxial segment (traditional example)", 34)
    save(d)

    d = Diagram("10-topology-ring.png", 780)
    pts = [(900 + 550 * math.cos(a), 410 + 240 * math.sin(a))
           for a in [i * math.pi / 3 for i in range(6)]]
    for i, a in enumerate(pts):
        d.line(a, pts[(i + 1) % len(pts)], BLUE)
    for i, (x, y) in enumerate(pts):
        d.box(x, y, 210, 100, f"Node {i + 1}", size=35)
    d.text(900, 75, "RING: each node has two neighbours", 42, bold=True)
    d.text(900, 410, "Closed path", 42, bold=True)
    save(d)

    d = Diagram("11-topology-mesh.png", 780)
    pts = [(430, 210), (1370, 210), (430, 600), (1370, 600)]
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            d.line(a, b, BLUE)
    for (x, y), name in zip(pts, ["A", "B", "C", "D"]):
        d.box(x, y, 230, 110, "Node " + name, size=36)
    d.text(900, 75, "FULL MESH: four nodes, six links", 42, bold=True)
    d.text(900, 715, "4 × (4 − 1) ÷ 2 = 6", 40, bold=True)
    save(d)

    d = Diagram("12-topology-tree.png", 770)
    for p, q in [((900, 145), (480, 355)), ((900, 145), (1320, 355)),
                 ((480, 355), (260, 620)), ((480, 355), (700, 620)),
                 ((1320, 355), (1100, 620)), ((1320, 355), (1540, 620))]:
        d.line(p, q, BLUE)
    for x, y, text, w in [(900, 145, "Main switch", 350), (480, 355, "Branch switch", 350),
                           (1320, 355, "Branch switch", 350), (260, 620, "Endpoint A", 290),
                           (700, 620, "Endpoint B", 290), (1100, 620, "Endpoint C", 290),
                           (1540, 620, "Endpoint D", 290)]:
        d.box(x, y, w, 110, text, size=35)
    d.text(900, 55, "TREE: a hierarchy of branches", 40, bold=True)
    save(d)

    d = Diagram("13-equipment-path.png", 510)
    xs = [190, 545, 900, 1255, 1610]
    labels = ["Host + NIC", "LAN switch", "Router / gateway", "Access equipment", "Provider network"]
    details = ["Local endpoint", "Forwards frames", "Between IP networks", "Modem / ONT as appropriate", "External route"]
    for a, b in zip(xs, xs[1:]):
        d.arrow((a + 140, 235), (b - 140, 235), both=True)
    for x, text, sub in zip(xs, labels, details):
        d.box(x, 235, 280, 145, text, size=35)
        d.text(x, 405, sub, 30, width=290)
    d.text(900, 70, "Different roles can share one physical gateway device.", 40, bold=True)
    save(d)

    d = Diagram("14-peer-lab.png", 630)
    d.line((340, 250), (900, 250), BLUE)
    d.line((900, 250), (1460, 250), BLUE)
    d.box(340, 250, 400, 140, "Computer A")
    d.box(900, 250, 310, 140, "Switch")
    d.box(1460, 250, 400, 140, "Computer B")
    d.text(340, 400, "192.168.50.10 /24", 34, mono=True)
    d.text(1460, 400, "192.168.50.11 /24", 34, mono=True)
    d.text(1460, 505, "Controlled ICT-Lab share", 33, width=430)
    d.text(900, 80, "Isolated, teacher-approved example network", 40, bold=True)
    d.text(650, 555, "No gateway is needed for this same-subnet test.", 33, width=1020)
    save(d)

    d = Diagram("15-vpn-tunnel.png", 650)
    d.d.rounded_rectangle((95, 190, 1375, 510), radius=45, fill=LIGHT, outline=BLUE, width=6)
    d.text(750, 120, "Encrypted, authenticated tunnel between VPN endpoints", 38, bold=True)
    d.arrow((365, 350), (615, 350), both=True)
    d.arrow((885, 350), (1085, 350), both=True)
    d.box(240, 350, 240, 160, "VPN client", fill=WHITE, size=35)
    d.box(750, 350, 260, 160, "Other network / Internet", fill=WHITE, size=32)
    d.box(1220, 350, 260, 170, "VPN gateway + firewall", fill=WHITE, size=33)
    d.arrow((1385, 350), (1460, 350), both=True)
    d.box(1610, 350, 280, 170, "Permitted internal service", size=33)
    d.text(900, 580, "The tunnel protects transport; policy still limits access.", 37, bold=True)
    save(d)

    d = Diagram("16-cia.png", 770)
    pts = [(900, 180), (380, 585), (1420, 585)]
    for i, a in enumerate(pts):
        d.line(a, pts[(i + 1) % 3], BLUE, 8)
    d.box(900, 150, 590, 130, "CONFIDENTIALITY\nOnly authorised readers", size=35)
    d.box(380, 610, 590, 130, "INTEGRITY\nNo inappropriate alteration", size=35)
    d.box(1420, 610, 590, 130, "AVAILABILITY\nAccess when required", size=35)
    d.text(900, 410, "Balanced security", 43, bold=True)
    save(d)

    d = Diagram("17-digital-signature.png", 730)
    # The key feeds the signing operation, not an encryption of the whole document.
    d.box(220, 235, 320, 140, "Original data", size=35)
    d.arrow((390, 235), (490, 235))
    d.box(700, 235, 400, 140, "Create signature", size=36)
    d.box(700, 85, 350, 100, "Private key", size=34)
    d.arrow((700, 140), (700, 160))
    d.arrow((910, 235), (1120, 235))
    d.box(1350, 235, 440, 140, "Data + signature", size=36)
    d.box(300, 550, 440, 140, "Received data + signature", size=35)
    d.arrow((530, 550), (670, 550))
    d.box(900, 550, 440, 140, "Verify using trusted public key", size=35)
    d.arrow((1130, 550), (1270, 550))
    d.box(1490, 550, 420, 140, "Valid / invalid result", size=35)
    d.text(900, 690, "A signature does not itself hide the message.", 36, bold=True)
    save(d)

    d = Diagram("18-validation.png", 700)
    d.box(300, 220, 400, 150, "Source mark: 86", size=39)
    d.arrow((510, 220), (690, 220))
    d.box(900, 220, 400, 150, "Entered mark: 68", size=38)
    d.arrow((1110, 220), (1290, 220))
    d.box(1500, 220, 400, 175, "Validation: 0–100\n68 is acceptable", size=34)
    d.arrow((300, 300), (720, 500))
    d.arrow((900, 300), (900, 435))
    d.box(900, 535, 740, 175, "Verification: compare source and entry\n86 ≠ 68 — investigate and correct", size=37)
    d.text(900, 70, "Acceptable input is not necessarily correct input.", 40, bold=True)
    save(d)

    d = Diagram("19-duplex.png", 830)
    for y, mode in [(155, "Simplex"), (400, "Half-duplex"), (660, "Full-duplex")]:
        d.box(350, y, 360, 110, "Device A", size=36)
        d.box(1450, y, 360, 110, "Device B", size=36)
        d.text(900, y - 80, mode, 40, bold=True)
    d.arrow((550, 155), (1250, 155))
    d.arrow((550, 375), (1250, 375))
    d.arrow((1250, 425), (550, 425), dashed=True)
    d.text(900, 490, "Different times", 32)
    d.arrow((550, 635), (1250, 635))
    d.arrow((1250, 685), (550, 685))
    d.text(900, 750, "Simultaneous directions supported", 32)
    save(d)

    d = Diagram("20-serial-parallel.png", 780)
    d.text(900, 70, "SERIAL: successive bits along a data path", 40, bold=True)
    d.box(285, 230, 330, 150, "Sender")
    d.box(1515, 230, 330, 150, "Receiver")
    d.arrow((470, 230), (1330, 230))
    d.text(900, 175, "1    0    1    1", 42, mono=True)
    d.text(900, 380, "PARALLEL: several bits on separate data paths", 40, bold=True)
    d.box(285, 585, 330, 260, "Sender")
    d.box(1515, 585, 330, 260, "Receiver")
    for y, bit in zip([485, 550, 615, 680], "1011"):
        d.arrow((470, y), (1330, y))
        d.text(900, y - 22, bit, 35, mono=True)
    save(d)

    d = Diagram("21-timing.png", 730)
    d.text(900, 70, "Asynchronous example: 1 start + 8 data + 1 stop", 40, bold=True)
    x0, cw = 245, 130
    for i, bit in enumerate("0" + "10110100" + "1"):
        x = x0 + i * cw
        d.d.rectangle((x, 200, x + cw, 320), fill=LIGHT if i in [0, 9] else WHITE, outline=BLUE, width=4)
        d.text(x + cw / 2, 260, bit, 45, mono=True)
    d.text(x0 + cw / 2, 365, "Start", 32)
    d.text(900, 150, "Eight data bits", 35)
    d.text(x0 + 9.5 * cw, 365, "Stop", 32)
    d.text(900, 455, "Synchronous example: coordinated blocks / stream", 40, bold=True)
    for x, t in [(400, "Block A"), (900, "Block B"), (1400, "Block C")]:
        d.box(x, 575, 450, 135, t, size=38)
    d.text(900, 690, "Timing and framing still follow agreed rules.", 34)
    save(d)

    d = Diagram("22-signals.png", 820)
    d.text(420, 65, "Analog: continuous variation", 38, bold=True)
    d.arrow((210, 350), (1690, 350), color=GREY, width=3)
    d.arrow((220, 350), (220, 120), color=GREY, width=3)
    points = [(x, 235 - 75 * math.sin((x - 230) / 90)) for x in range(235, 1650)]
    d.d.line(points, fill=BLUE, width=6)
    d.text(1630, 395, "Time", 32)
    d.text(125, 135, "Level", 28)
    d.text(420, 460, "Digital: defined symbol states", 38, bold=True)
    d.arrow((210, 720), (1690, 720), color=GREY, width=3)
    d.arrow((220, 720), (220, 515), color=GREY, width=3)
    bits = "10110010"
    points = []
    for i, bit in enumerate(bits):
        left, right = 240 + i * 175, 240 + (i + 1) * 175
        y = 550 if bit == "1" else 665
        if points:
            points.append((left, y))
        points += [(left, y), (right, y)]
        d.text((left + right) / 2, 770, bit, 34, mono=True)
    d.d.line(points, fill=BLUE, width=6)
    d.text(160, 550, "1", 32)
    d.text(160, 665, "0", 32)
    d.text(125, 505, "Level", 28)
    d.text(1720, 750, "Time", 28)
    save(d)

    d = Diagram("23-guided-media.png", 930)
    d.text(330, 210, "Twisted pair\nPaired conductors", 39, bold=True, width=480)
    for phase, color in [(0, BLUE), (math.pi, GREY)]:
        pts = [(x, 210 + 45 * math.sin((x - 680) / 50 + phase)) for x in range(680, 1640)]
        d.d.line(pts, fill=color, width=11)
    d.text(330, 490, "Coaxial cable\nShield + insulation + core", 37, bold=True, width=510)
    for radius, fill in [(115, GREY), (87, LIGHT), (29, BLUE)]:
        d.d.ellipse((1200 - radius, 490 - radius, 1200 + radius, 490 + radius), fill=fill, outline=INK, width=3)
    d.text(1510, 490, "Cross-section", 33, width=290)
    d.text(330, 785, "Optical fibre\nLight in a core", 39, bold=True, width=480)
    d.d.rounded_rectangle((680, 710, 1640, 860), radius=25, fill=LIGHT, outline=BLUE, width=4)
    d.d.rectangle((680, 755, 1640, 815), fill=WHITE, outline=BLUE, width=3)
    d.arrow((740, 785), (1570, 785))
    d.text(1160, 680, "Cladding around the core", 33)
    d.text(1160, 895, "Do not look into a live optical connector.", 30)
    save(d)

    d = Diagram("24-peripheral-control.png", 760)
    d.text(440, 75, "Polling: repeated checks", 38, bold=True)
    d.text(1340, 75, "Interrupt + buffer", 38, bold=True)
    for x, name in [(220, "CPU"), (650, "Device"), (1110, "CPU"), (1570, "Device")]:
        d.box(x, 210, 250, 110, name, size=37)
        d.line((x, 270), (x, 665), GREY, 3)
    for y in [345, 500]:
        d.arrow((230, y), (640, y + 35))
        d.text(435, y - 30, "Status?", 31)
        d.arrow((640, y + 80), (230, y + 115), color=GREY)
        d.text(435, y + 65, "Not ready", 29)
    d.box(1570, 400, 340, 120, "Data in buffer", size=32)
    d.arrow((1510, 480), (1120, 525))
    d.text(1315, 455, "Interrupt request", 31)
    d.box(1110, 610, 320, 120, "Handle event", size=33)
    d.line((890, 120), (890, 700), "#C3CCD8", 3, dashed=True)
    save(d)

    d = Diagram("25-tcp-recovery.png", 850)
    d.text(450, 65, "Sender", 42, bold=True)
    d.text(1350, 65, "Receiver", 42, bold=True)
    d.line((450, 120), (450, 780), GREY, 4)
    d.line((1350, 120), (1350, 780), GREY, 4)
    d.arrow((450, 165), (1350, 230))
    d.text(900, 155, "Data part 1", 33)
    d.arrow((1350, 280), (450, 335))
    d.text(900, 265, "Acknowledge part 1", 33)
    d.line((450, 390), (1050, 435), RED, 5)
    d.line((1025, 410), (1075, 460), RED, 7)
    d.line((1025, 460), (1075, 410), RED, 7)
    d.text(900, 375, "Data part 2 lost", 33, color=RED)
    d.text(450, 500, "Timeout", 33, color=RED)
    d.arrow((450, 565), (1350, 620))
    d.text(900, 550, "Retransmit part 2", 33)
    d.arrow((1350, 690), (450, 750))
    d.text(900, 675, "Acknowledge through part 2", 33)
    d.text(900, 815, "Illustrative parts; actual TCP uses byte sequence numbers.", 31)
    save(d)

    d = Diagram("26-osi.png", 900)
    rows = [("7", "Application", "Application communication"), ("6", "Presentation", "Representation / encoding"),
            ("5", "Session", "Dialogue / session coordination"), ("4", "Transport", "Application-to-application delivery"),
            ("3", "Network", "Addressing / routing"), ("2", "Data Link", "Local frames / media access"),
            ("1", "Physical", "Signals / media / interfaces")]
    d.text(900, 55, "OSI reference model", 43, bold=True)
    for i, (number, name, detail) in enumerate(rows):
        y = 155 + i * 103
        d.d.rounded_rectangle((120, y - 43, 1680, y + 43), radius=10,
                              fill=LIGHT if i % 2 == 0 else PALE, outline=BLUE, width=3)
        d.text(230, y, number, 40, bold=True)
        d.text(650, y, name, 39, bold=True)
        d.text(1250, y, detail, 32, width=690)
    d.text(900, 850, "A conceptual model, not seven mandatory separate programs.", 33)
    save(d)

    d = Diagram("27-encapsulation.png", 760)
    d.d.rounded_rectangle((90, 100, 1710, 595), radius=20, fill=PALE, outline=BLUE, width=4)
    d.text(300, 150, "LINK FRAME", 35, bold=True)
    d.d.rounded_rectangle((405, 195, 1650, 550), radius=20, fill=LIGHT, outline=BLUE, width=4)
    d.text(625, 245, "IP PACKET", 35, bold=True)
    d.d.rounded_rectangle((705, 300, 1585, 510), radius=20, fill=WHITE, outline=BLUE, width=4)
    d.text(925, 345, "TCP SEGMENT", 33, bold=True)
    d.box(1250, 435, 500, 95, "Application data", size=35)
    d.arrow((900, 600), (900, 675))
    d.text(900, 715, "The frame is transmitted as physical signals.", 36, bold=True)
    save(d)

    d = Diagram("28-parity.png", 740)
    examples = [(170, "Sent (even)", "10110100", "4 ones: passes"),
                (390, "One bit flipped", "10100100", "3 ones: fails"),
                (610, "Two bits flipped", "11010100", "4 ones: passes")]
    for y, title, bits, result in examples:
        d.text(230, y, title, 34, bold=True, width=310)
        for i, bit in enumerate(bits):
            x = 445 + i * 118
            d.d.rectangle((x, y - 55, x + 118, y + 55), fill=LIGHT if i == 7 else WHITE,
                          outline=BLUE, width=3)
            d.text(x + 59, y, bit, 43, mono=True)
        d.text(1580, y, result, 33, bold=True, color=RED if "fails" in result else INK, width=310)
    d.text(1330, 70, "Parity bit", 30)
    d.text(900, 705, "Passing parity does not prove that the content is unchanged.", 34, bold=True)
    save(d)

    d = Diagram("29-internet-services.png", 730)
    for x, y in [(300, 160), (1500, 160), (300, 570), (1500, 570)]:
        d.line((900, 365), (x, y), BLUE)
    d.box(900, 365, 650, 180, "INTERNET\nInterconnected IP networks", size=40)
    for x, y, text in [(300, 160, "World Wide Web"), (1500, 160, "E-mail"),
                        (300, 570, "Voice / messaging"), (1500, 570, "File transfer")]:
        d.box(x, y, 450, 140, text, size=36)
    d.text(900, 690, "The Web is one service using the Internet.", 38, bold=True)
    save(d)

    d = Diagram("30-connectivity.png", 540)
    xs = [180, 540, 900, 1260, 1620]
    labels = ["User device", "Local LAN / Wi-Fi", "Router / gateway", "Access equipment", "ISP / Internet"]
    details = ["Interface + browser", "Local connection", "Route to remote networks", "Matches the service", "External connectivity"]
    for a, b in zip(xs, xs[1:]):
        d.arrow((a + 135, 250), (b - 135, 250), both=True)
    for x, text, sub in zip(xs, labels, details):
        d.box(x, 250, 270, 160, text, size=34)
        d.text(x, 420, sub, 30, width=300)
    d.text(900, 75, "Internet connectivity requires the whole relevant path.", 39, bold=True)
    save(d)

    d = Diagram("31-url.png", 660)
    url = "https://portal.mboa.example/learn/ict.html?term=1#tasks"
    f = font(39, mono=True)
    total = d.d.textlength(url, font=f)
    start = (W - total) / 2
    d.text(900, 265, url, 39, mono=True)
    # Compute actual separators instead of assuming character counts.
    spans = [(0, url.index(":"), "Scheme", 180, 470),
             (url.index("//") + 2, url.index("/learn"), "Host", 620, 470),
             (url.index("/learn"), url.index("?"), "Path", 1030, 470),
             (url.index("?") + 1, url.index("#"), "Query", 1450, 470),
             (url.index("#") + 1, len(url), "Fragment", 1560, 115)]
    for a, b, name, lx, ly in spans:
        x1 = start + d.d.textlength(url[:a], font=f)
        x2 = start + d.d.textlength(url[:b], font=f)
        sy = 310 if ly > 265 else 215
        d.line((x1, sy), (x2, sy), BLUE, 5)
        d.line(((x1 + x2) / 2, sy), (lx, ly - 35 if ly > 265 else ly + 35), GREY, 3)
        d.text(lx, ly, name, 37, bold=True)
    d.text(900, 585, "Reserved .example domain — an illustration, not a live service", 34)
    save(d)

    d = Diagram("32-cookie.png", 800)
    d.text(420, 75, "Browser", 42, bold=True)
    d.text(1380, 75, "Server", 42, bold=True)
    d.line((420, 130), (420, 700), GREY, 4)
    d.line((1380, 130), (1380, 700), GREY, 4)
    d.arrow((420, 185), (1380, 245))
    d.text(900, 170, "1 Request a page", 35)
    d.arrow((1380, 355), (420, 415))
    d.text(900, 335, "2 Response sets an eligible cookie", 35)
    d.arrow((420, 540), (1380, 600))
    d.text(900, 515, "3 Later request returns the cookie", 35)
    d.text(900, 745, "A token can support a session; the site's rules and browser settings apply.", 31, width=1580)
    save(d)

    d = Diagram("33-ecommerce.png", 720)
    pts = [(330, 175), (900, 175), (1470, 175), (1470, 525), (900, 525), (330, 525)]
    names = ["1 Find and check seller", "2 Place order", "3 Payment + confirmation", "4 Fulfil order", "5 Receive delivery", "6 Support / returns"]
    for i, a in enumerate(pts[:-1]):
        b = pts[i + 1]
        if a[1] == b[1]:
            direction = 1 if b[0] > a[0] else -1
            d.arrow((a[0] + 220 * direction, a[1]), (b[0] - 220 * direction, b[1]))
        else:
            d.arrow((a[0], a[1] + 90), (b[0], b[1] - 90))
    for (x, y), name in zip(pts, names):
        d.box(x, y, 440, 175, name, size=37)
    d.text(900, 355, "Payment is one stage, not proof of delivery.", 35, width=700, bold=True)
    save(d)

    d = Diagram("34-blended-learning.png", 630)
    for a, b in [(330, 900), (900, 1470)]:
        d.arrow((a + 220, 285), (b - 220, 285))
    for x, name, detail in [(330, "Prepare", "Read / watch a small offline or online resource"),
                             (900, "Practise together", "Discuss and perform a supervised task"),
                             (1470, "Review and improve", "Use feedback, then try independently")]:
        d.box(x, 285, 440, 230, name + "\n" + detail, size=34)
    d.text(900, 100, "BLENDED LEARNING", 42, bold=True)
    d.text(900, 520, "Choose delivery methods that fit learners' access and the learning objective.", 35, width=1600)
    save(d)

    d = Diagram("35-html-tree.png", 950)
    edges = [((900, 110), (500, 330)), ((900, 110), (1300, 330)),
             ((500, 330), (300, 550)), ((500, 330), (700, 550)),
             ((1300, 330), (1000, 550)), ((1300, 330), (1300, 550)), ((1300, 330), (1600, 550))]
    for x in [970, 1190, 1410, 1630]:
        edges.append(((1300, 550), (x, 790)))
    for a, b in edges:
        d.line(a, b, BLUE)
    for x, y, w, label in [(900, 110, 300, "<html>"), (500, 330, 300, "<head>"), (1300, 330, 300, "<body>"),
                            (300, 550, 240, "<meta>"), (700, 550, 240, "<title>"),
                            (1000, 550, 240, "<header>"), (1300, 550, 240, "<main>"), (1600, 550, 240, "<footer>"),
                            (970, 790, 185, "<h2>"), (1190, 790, 185, "<p>"), (1410, 790, 185, "<ul>"), (1630, 790, 185, "<table>")]:
        d.box(x, y, w, 110, label, size=34)
    d.text(500, 720, "Metadata: not the main displayed content", 34, width=650)
    d.text(1250, 900, "Presented content is organised inside the body.", 32, width=1000)
    save(d)

    return made


if __name__ == "__main__":
    paths = draw_all()
    print(f"Drew {len(paths)} original diagrams in {OUT.relative_to(ROOT)}")
