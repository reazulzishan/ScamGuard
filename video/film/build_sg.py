"""ScamGuard (CS Funda) — "Scam or safe?"

Reuses the CommerceGuard engine (captions, real-cell camera, code typing, glass, charts, footage).
python build_sg.py          -> this folder (YouTube 1920x1080)
python build_sg.py reels    -> ../reels/part1..3 (1080x1920), standalone reels with frame-1 hooks
Every number on screen comes from notebooks/01_scamguard_live.ipynb or reports/results.json.
"""
import importlib.util, json, re, shutil, sys
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
VID = HERE.parent                      # video/ (script, vo, words)
ROOT = VID.parent                      # ScamGuard/
CG = Path.home() / "Projects/CommerceGuard"

# Load the Episode 2 module for its helpers (footage, charts, hbars); it brings its own copy of the engine as e.b.
spec = importlib.util.spec_from_file_location("e", CG / "video_ep2/film/build_ep2.py")
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
b = e.b

# ---- point the engine at ScamGuard's material
b.HERE = HERE; e.HERE = HERE
b.REC = VID
b.EP1_SFX = False
b.BOXES = json.loads((ROOT / "recording/boxes.json").read_text())
meta = json.loads((VID / "vo/scenes.json").read_text())
b.SCENES = {k: v for k, v in meta.items() if k[0] in "SHXTABCD"}
CARDS = {"R1": "Why does an almost perfect model fail on real scams?", "R2": "Can a model that never saw this dataset beat them all?", "R3": ""}
b.OUTROS = {f"R{k[1]}": {**v, "id": f"R{k[1]}", "card": CARDS[f"R{k[1]}"]} for k, v in meta.items() if k.startswith("F")}
for k in b.OUTROS:
    src, dst = VID / f"words/F{k[1]}.words.json", VID / f"words/{k}.words.json"
    if src.exists():
        dst.write_text(src.read_text())
RES = json.loads((ROOT / "reports/results.json").read_text())
b.HOLD = {"S01": 0.5, "S02": 0.5, "S08": 0.4, "X02": 0.4, "X04": 0.6, "S10": 0.8, "H2": 0.3, "S13": 0.5, "S14": 0.5, "X07": 0.4,
          "S17": 0.8, "S18": 0.6, "H3": 0.3, "S20": 0.4, "S22": 0.8, "S24": 1.0, "S25": 1.2, "S26": 0.5, "S27": 0.6, "S28": 1.0, "S30": 1.6}
b.SFX = {"S04": ("whoosh-cinematic", 0.0), "S06": ("whoosh-short", 0.0), "S09": ("whoosh", 0.0), "S11": ("whoosh-short", 0.0),
         "S14": ("whoosh", 0.0), "S16": ("whoosh-short", 0.0), "S19": ("whoosh-cinematic", 0.0), "S23": ("whoosh", 0.0), "S26": ("whoosh-short", 0.0),
         "S28": ("whoosh", 0.0)}
INK, AMB, RED, GRN = b.INK, b.AMB, b.RED, b.GRN
MUTE = "#8B8A86"
at, label, kinetic, chapter, glass, aura, sweep = b.at, b.label, b.kinetic, b.chapter, b.glass, b.aura, b.sweep
chart, curve, dot, hbars, footage, sfx, EXTRA = e.chart, e.curve, e.dot, e.hbars, e.footage, e.sfx, e.EXTRA
e.CLIPLEN.update({"run_timelapse": 10})
FONT = "@font-face{font-family:'NotoBN';src:url('assets/fonts/NotoSansBengali.ttf');}"


# captions: digits come from the transcript; the recogniser sometimes writes taka as dollars
_cw = b.caption_words
def _caption_words(sid):
    out = _cw(sid)
    for w in out:
        w["text"] = re.sub(r"^\$", "", w["text"]).replace(".00", "")
    return out
b.caption_words = _caption_words


def seg(c, start, end, hl, zoom=2.2):
    return {"cell": c, "h": b.seg_h(c), "start": start, "end": end, "hl": hl, "zoom": zoom}


def capture(sc, segs):   # on a phone screen the real cell needs a closer camera
    b.capture(sc, [dict(s_, zoom=s_["zoom"] * (1.7 if sc.P else 1.0)) for s_ in segs])


# ---------------------------------------------------------------- an SMS phone (generic UI, no brand styling)
def sms_phone(sc, x, y, w, h, sender, msgs, t_in=0.0):
    """msgs: [(key, text, gloss, t)] newest last. Bubbles are grey incoming SMS; the sender is a plain number."""
    u = sc.u; ph = sc.id("ph")
    sc.css.append(FONT)
    sc.add(f'<div id="{ph}"><div class="sh"><div class="sav">{escape(sender[:1]) if sender[0].isalpha() else "#"}</div>'
           f'<div><b>{escape(sender)}</b><span>Text message · SMS</span></div></div><div class="sb" id="{ph}b"></div></div>',
           f"#{ph}{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:{48 * u}px;background:#0F1012;"
           f"border:{7 * u}px solid #2B2C30;box-shadow:0 {40 * u}px {100 * u}px rgba(0,0,0,.65);overflow:hidden;}}"
           f"#root .sh{{display:flex;align-items:center;gap:{16 * u}px;padding:{30 * u}px {28 * u}px {20 * u}px;border-bottom:{2 * u}px solid #232428;}}"
           f"#root .sav{{width:{68 * u}px;height:{68 * u}px;border-radius:50%;background:#3A3B40;color:{INK};font-weight:800;font-size:{32 * u}px;"
           f"display:flex;align-items:center;justify-content:center;}}#root .sh b{{display:block;font-size:{34 * u}px;}}"
           f"#root .sh span{{font-size:{26 * u}px;color:{MUTE};}}")
    if t_in > 0.05:
        sc.js.append(f'tl.fromTo("#{ph}",{{opacity:0,y:{60 * u}}},{{opacity:1,y:0,duration:.6,ease:"expo.out"}},{t_in:.2f});')
    bw = w * 0.82; yy = 140 * u; ys = {}
    for key, text, gloss, t in msgs:
        el = sc.id(f"m{key}")
        bn = bool(re.search(r"[ঀ-৿]", text))
        lines = max(1, -(-len(text) // int((bw - 44 * u) / ((20 if bn else 16) * u))))
        glines = max(1, -(-len(gloss) // int((bw - 44 * u) / (13 * u)))) if gloss else 0
        hh = lines * (34 * 1.5 + 2) * u + glines * 36 * u + 40 * u
        ys[key] = y + yy
        sc.html[-1] = sc.html[-1][:-len("</div></div>")] + (f'<div id="{el}" class="sm"><div class="st">{escape(text)}</div>'
                       + (f'<div class="sg">{escape(gloss)}</div>' if gloss else "") + "</div></div></div>")
        sc.css.append(f"#{el}{{left:{26 * u}px;top:{yy}px;width:{bw}px;}}")
        if t > 0.05:
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:.8,transformOrigin:"0% 100%"}},{{opacity:1,scale:1,duration:.35,ease:"back.out(1.6)"}},{t:.2f});')
            sfx(sc.sid, t, "pop", 0.25)
        yy += hh + 22 * u
    sc.ys = ys
    sc.css.append(f"#{ph}{{height:{min(h, yy + 24 * u)}px;}}")   # no empty phone below the last message
    sc.css.append(f"#root .sm{{position:absolute;padding:{16 * u}px {22 * u}px;background:#25262A;border-radius:{28 * u}px {28 * u}px {28 * u}px {8 * u}px;}}"
                  f"#root .sm .st{{font-family:'NotoBN',Inter,sans-serif;font-size:{34 * u}px;line-height:1.45;color:{INK};}}"
                  f"#root .sm .sg{{font-size:{26 * u}px;line-height:1.3;color:#9C9A94;margin-top:{6 * u}px;}}")
    return ph


def stamp(sc, name, text, x, y, color, t, size=64, rot=-8):
    el = sc.id(name)
    sc.add(f'<div id="{el}"><div class="stp" style="border-color:{color};color:{color}">{text}</div></div>',
           f"#{el}{{position:absolute;left:{x}px;top:{y}px;z-index:6;width:max-content;}}#{el} .stp{{transform:rotate({rot}deg);border:{7 * sc.u}px solid;"
           f"font-weight:900;font-size:{size * sc.u}px;padding:{6 * sc.u}px {24 * sc.u}px;border-radius:{12 * sc.u}px;background:rgba(20,21,23,.85);"
           f"letter-spacing:.04em;white-space:nowrap;}}")
    sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:.22,ease:"power4.in"}},{t:.2f});'
                 f'tl.fromTo("#{el} .stp",{{textShadow:"{6 * sc.u}px 0 #00E5FF,{-6 * sc.u}px 0 #FF2BD6",x:{4 * sc.u}}},'
                 f'{{textShadow:"0px 0 #00E5FF,0px 0 #FF2BD6",x:0,duration:.35,ease:"steps(5)"}},{t + .22:.2f});')   # RGB-split glitch as it lands
    sfx(sc.sid, t + 0.2, "impact-bass-1", 0.3)
    return el


def meters(sc, name, rows, x, y, w, rowh=96, fmt="{:.2f}"):
    """rows: [(model, score 0..1, t)] — real scores drawn as a bar with the number."""
    u = sc.u
    for i, (m, s, t) in enumerate(rows):
        col = RED if s >= 0.7 else (AMB if s >= 0.3 else GRN)
        lab, trk, fil, num = (sc.id(f"{name}{k}{i}") for k in "ltfn")
        yy = y + i * rowh * u
        sc.add(f'<div id="{lab}" class="ml">{m}</div><div id="{trk}" class="mt"><div id="{fil}" class="mf"></div></div><div id="{num}" class="mn">{fmt.format(s)}</div>',
               f"#{lab}{{left:{x}px;top:{yy}px;}}#{trk}{{left:{x}px;top:{yy + 46 * u}px;width:{w * 0.74}px;}}"
               f"#{fil}{{width:{max(1.5, s * 100)}%;background:{col};}}#{num}{{left:{x + w * 0.78}px;top:{yy + 22 * u}px;color:{col};}}")
        sc.appear(lab, t, y=8, d=.25)
        sc.js.append(f'tl.fromTo("#{trk}",{{opacity:0}},{{opacity:1,duration:.2}},{t:.2f});'
                     f'tl.fromTo("#{fil}",{{scaleX:0}},{{scaleX:1,duration:.7,ease:"expo.out"}},{t + .1:.2f});')
        sc.appear(num, t + .45, y=0, d=.2)
        sfx(sc.sid, t + .1, "click-soft", 0.25)
    sc.css.append(f"#root .ml{{position:absolute;font-size:{32 * u}px;font-weight:700;white-space:nowrap;}}"
                  f"#root .mt{{position:absolute;height:{22 * u}px;border-radius:{11 * u}px;background:rgba(243,240,232,.12);overflow:hidden;}}"
                  f"#root .mf{{height:100%;border-radius:{11 * u}px;transform-origin:left center;}}"
                  f"#root .mn{{position:absolute;font-size:{44 * u}px;font-weight:800;font-family:'JetBrains Mono',monospace;}}")


def card(sc, name, title, sub, x, y, w, t, color=INK, big=44):
    el = sc.id(name)
    sc.add(f'<div id="{el}" class="gc"><b style="color:{color}">{title}</b><span>{sub}</span></div>',
           f"#{el}{{left:{x}px;top:{y}px;width:{w}px;}}")
    sc.css.append(f"#root .gc{{position:absolute;padding:{22 * sc.u}px {28 * sc.u}px;{glass(sc)}}}#root .gc b{{display:block;font-size:{big * sc.u}px;line-height:1.1;}}"
                  f"#root .gc span{{display:block;font-size:{28 * sc.u}px;color:#B8B5AE;margin-top:{8 * sc.u}px;line-height:1.3;}}")
    if t > 0.05:
        sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:{30 * sc.u},scale:.96}},{{opacity:1,y:0,scale:1,duration:.5,ease:"expo.out"}},{t:.2f});')
    return el


def lock(sc, name, cx, cy, t_open=None, t_in=0.2, size=1.0):
    """A padlock drawn in CSS; opens at t_open."""
    u = sc.u * size; el, sh = sc.id(name), sc.id(name + "s")
    sc.add(f'<div id="{el}"><div id="{sh}" class="lks"></div><div class="lkb"><i></i></div></div>',
           f"#{el}{{position:absolute;left:{cx - 90 * u}px;top:{cy - 110 * u}px;width:{180 * u}px;height:{220 * u}px;}}"
           f"#root .lks{{position:absolute;left:{35 * u}px;top:0;width:{110 * u}px;height:{120 * u}px;border:{18 * u}px solid {AMB};border-bottom:none;"
           f"border-radius:{60 * u}px {60 * u}px 0 0;transform-origin:85% 100%;}}"
           f"#root .lkb{{position:absolute;left:0;top:{95 * u}px;width:{180 * u}px;height:{125 * u}px;background:{AMB};border-radius:{22 * u}px;}}"
           f"#root .lkb i{{position:absolute;left:{78 * u}px;top:{38 * u}px;width:{24 * u}px;height:{48 * u}px;background:#141517;border-radius:{12 * u}px;}}")
    sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:.6}},{{opacity:1,scale:1,duration:.45,ease:"back.out(1.7)"}},{t_in:.2f});')
    if t_open:
        sc.js.append(f'tl.to("#{sh}",{{y:{-40 * u},rotation:28,duration:.5,ease:"back.out(2)"}},{t_open:.2f});')
        sfx(sc.sid, t_open, "click-soft", 0.4)


def big_number(sc, name, value, cap, x, y, t, color=AMB, size=150, w=None):
    label(sc, name, value, x, y, size=size, color=color, weight=900, t=t)
    label(sc, name + "c", cap, x, y + size * 1.15 * sc.u, size=36, color="#D9D6CE", weight=700, t=t + 0.2, w=w)


def src_line(sc, text, t):
    return label(sc, "src", text, sc.W * (0.06 if not sc.P else 0.05), sc.H * (0.80 if not sc.P else 0.74), size=26, color=MUTE, t=t, w=sc.W * 0.88)


REAL = json.loads((VID / "realviz/real.json").read_text())   # extracted from the trained models (realviz/extract.py)
REAL2 = json.loads((VID / "realviz/real2.json").read_text())  # TF-IDF and e5 numbers for one SMS (realviz/extract2.py)


def stepbar(sc, names, cur, t=0.1):
    """Pipeline progress: every step as a chip, the current one lit."""
    u = sc.u; x = sc.W * 0.05; y = sc.H * 0.115
    w = (sc.W * 0.90 - (len(names) - 1) * 10 * u) / len(names)
    for i, n in enumerate(names):
        el = sc.id(f"sb{i}")
        on = i == cur; done = i < cur
        sc.add(f'<div id="{el}" class="sbc">{i + 1} · {n}</div>',
               f"#{el}{{left:{x + i * (w + 10 * u)}px;top:{y}px;width:{w}px;"
               f"background:{AMB if on else ('rgba(255,178,36,.18)' if done else 'rgba(255,255,255,.06)')};color:{'#141517' if on else ('#F3C77A' if done else '#8B8A86')};}}")
        sc.appear(el, t + i * 0.05, y=0, d=.2)
    sc.css.append(f"#root .sbc{{position:absolute;text-align:center;padding:{10 * u}px 0;border-radius:{10 * u}px;font-weight:900;font-size:{22 * u}px;letter-spacing:.03em;z-index:9;}}")


def hook_title(sc, lines, sub, y):
    for i, (txt, col) in enumerate(lines):
        label(sc, f"ht{i}", txt, sc.W * 0.05, y + i * 112 * sc.u, size=96, color=col, weight=900, t=0.15 + i * 0.25, w=sc.W * 0.92)
    label(sc, "hs", sub, sc.W * 0.05, y + len(lines) * 112 * sc.u + 20 * sc.u, size=36, color="#B8B5AE", weight=700, t=0.7, w=sc.W * 0.92)



def scanline(sc, name, x, y, w, h, t, d=1.4, label="SCANNING"):
    """A glowing scan bar sweeping down a phone, with a HUD tag."""
    u = sc.u; el, tg = sc.id(name), sc.id(name + "t")
    sc.add(f'<div id="{el}"></div><div id="{tg}" class="mono">{label}</div>',
           f"#{el}{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{6 * u}px;background:linear-gradient(90deg,transparent,{AMB},transparent);"
           f"box-shadow:0 0 {30 * u}px {8 * u}px rgba(255,178,36,.45);opacity:0;z-index:7;}}"
           f"#{tg}{{position:absolute;left:{x + w - 220 * u}px;top:{y - 44 * u}px;font-size:{24 * u}px;color:{AMB};letter-spacing:.2em;opacity:0;z-index:7;}}")
    sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:0}},{{opacity:1,y:{h * 0.08:.1f},duration:.15}},{t:.2f});tl.to("#{el}",{{y:{h},duration:{d},ease:"sine.inOut"}},{t + .15:.2f});tl.to("#{el}",{{opacity:0,duration:.2}},{t + d + .15:.2f});'
                 f'tl.fromTo("#{tg}",{{opacity:0}},{{opacity:1,duration:.15,yoyo:true,repeat:3}},{t:.2f});tl.to("#{tg}",{{opacity:0,duration:.2}},{t + d:.2f});')
    sfx(sc.sid, t, "riser", 0.15)


def countup(sc, el, to, t, d=1.2, dec=0, prefix="", suffix="", sel="b"):
    """Number counts up to its real value (deterministic: driven by the timeline)."""
    n = el.replace("-", "_")
    sc.js.append(f'const c_{n}={{v:0}};tl.to(c_{n},{{v:{to},duration:{d},ease:"power2.out",onUpdate:()=>{{const e=document.querySelector("#{el} {sel}")||document.querySelector("#{el} > div");'
                 f'if(e)e.textContent="{prefix}"+c_{n}.v.toLocaleString("en-US",{{minimumFractionDigits:{dec},maximumFractionDigits:{dec}}})+"{suffix}";}}}},{t:.2f});')


# ---------------------------------------------------------------- the scenes
SCAM_SMS = ("আপনার bKash একাউন্ট ২৪ ঘণ্টার মধ্যে বন্ধ হয়ে যাবে। এখনই ভেরিফাই করতে আপনার PIN দিন।",
            "Your bKash account will be blocked in 24 hours. Verify now with your PIN.")
CASHIN = "Cash In Tk 2,500.00 from 01712XXXXXX successful. Balance Tk 2,612.40. TrxID 9KX3..."
MISTAKE = "Bhai, vul kore apnar number e 2500 taka pathiye felsi, please ferot pathan."
MODELS = [("TF-IDF", "characters + words", "Model 1"), ("e5 embeddings", "multilingual meaning", "Model 2"),
          ("XLM-RoBERTa", "fine-tuned Transformer", "Model 3"), ("TigerLLM-1B", "Bangla LLM", "Model 4a"), ("Qwen2.5-3B", "multilingual LLM", "Model 4b")]
LOCKED = {r["model"]: r for r in RES["locked"]}


def S3(sid, W, H):
    sc = b.Scene(sid, W, H); u, P = sc.u, sc.P
    L = W * (0.06 if not P else 0.05)
    d = b.dur(sid)
    if sid == "S01":     # frame 1: the scam SMS already on screen
        aura(sc, (RED, AMB))
        pw, phh = (W * 0.32, H * 0.80) if not P else (W * 0.88, H * 0.40)
        px, py = (W * 0.08, H * 0.18) if not P else ((W - pw) / 2, H * 0.07)
        sms_phone(sc, px, py, pw, phh, "+880 17XX-XXXXXX", [("a", SCAM_SMS[0], SCAM_SMS[1], 0.0)])
        kx, ky = (W * 0.48, H * 0.30) if not P else (L, H * 0.42)
        label(sc, "q0", "Would you fall for this?", kx, ky - 90 * u, size=52, weight=800, t=0.0)
        label(sc, "q1", "SCAM", kx, ky, size=160 if not P else 170, color=RED, weight=900, t=0.2)
        label(sc, "q2", "or SAFE?", kx, ky + 180 * u, size=160 if not P else 170, color=GRN, weight=900, t=0.5)
        sfx(sid, 0.2, "impact-bass-1", 0.3)
        scanline(sc, "scan", px + 20 * u, py + 120 * u, pw - 40 * u, (240 if not P else 220) * u, 1.2)
    elif sid == "S02":
        chapter(sc, "THE THREAT · BANGLADESH, 2025")
        cw = W * (0.27 if not P else 0.88)
        pos = [(L, H * 0.30), (L + cw + 40 * u, H * 0.30), (L + 2 * (cw + 40 * u), H * 0.30)] if not P else [(L, H * 0.20), (L, H * 0.36), (L, H * 0.52)]
        c1 = card(sc, "c1", "81,423", "payment-fraud cases", *pos[0], cw, at(sid, "81"), RED, big=96 if not P else 110)
        countup(sc, c1, 81423, at(sid, "81"), d=1.4)
        card(sc, "c2", "Tk 92.60 crore", "lost", *pos[1], cw, at(sid, "crore", default=at(sid, "92")), RED, big=72 if not P else 96)
        c3 = card(sc, "c3", "10.7%", "recovered", *pos[2], cw, at(sid, "11"), AMB, big=96 if not P else 110)
        countup(sc, c3, 10.7, at(sid, "11"), d=1.0, dec=1, suffix="%")
        src_line(sc, "Source: Bangladesh Bank figures for 2025, reported by The Daily Observer (Aug 2026). All payment fraud, not one provider.", 1.0)
    elif sid == "S03":
        (fx, fy, fw, fh), (px, py, pw, phh) = e.layout(sc)
        footage(sc, "rafi_office", fx, fy, fw, fh, tag="Rafi · online seller (Ep 2)", tag_t=0.4)
        t1, t2 = at(sid, "cash"), at(sid, "mistake", default=at(sid, "call") + 1.2)
        sms_phone(sc, px, py, pw, phh, "01712XXXXXX", [("c", CASHIN, "sent from an ordinary mobile number", t1),
                                                       ("m", MISTAKE, "“I sent it by mistake, please send it back.”", t2)], t_in=0.3)
    elif sid == "S04":
        aura(sc, (AMB, GRN))
        kinetic(sc, [("Can a machine catch", 0.3, INK), ("a scam SMS", at(sid, "scam"), RED), ("before you do?", at(sid, "before"), AMB)],
                top=H * (0.20 if not P else 0.22), size=110)
        sc.css.append(FONT)
        chips = [("বাংলা", "bangla"), ("English", "english"), ("Banglish", "banglish")]
        for i, (c, tok) in enumerate(chips):
            el = sc.id(f"ch{i}")
            x = (L + i * 330 * u) if not P else L + i * 320 * u
            sc.add(f'<div id="{el}" class="chip">{c}</div>', f"#{el}{{left:{x}px;top:{H * (0.66 if not P else 0.60)}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:.7}},{{opacity:1,scale:1,duration:.35,ease:"back.out(2)"}},{at(sid, tok, default=4 + i):.2f});')
        sc.css.append(f"#root .chip{{position:absolute;padding:{14 * u}px {34 * u}px;font-family:'NotoBN',Inter,sans-serif;font-size:{48 * u}px;font-weight:800;{glass(sc)}}}")
    elif sid == "S05":
        chapter(sc, "FIVE MODELS · ONE HONEST TEST")
        vw = W * (0.50 if not P else 0.90)
        footage(sc, "run_timelapse", L, H * (0.17 if not P else 0.15), vw, vw * 9 / 16, tag="the real notebook run · 25 min → 10 s", tag_t=at(sid, "real", default=6))
        cx = (L + vw + 50 * u) if not P else L
        cy0 = H * (0.16 if not P else 0.47)
        cwid = (W - cx - L) if not P else W * 0.90
        for i, (m, sub, n) in enumerate(MODELS):
            x_, y_, w_ = ((cx, cy0 + i * 150 * u, cwid) if not P else (L + (i % 2) * W * 0.46, cy0 + (i // 2) * 160 * u, W * 0.44))
            card(sc, f"md{i}", f"{n} · {m}" if not P else m, sub, x_, y_, w_, 0.6 + i * 0.45, AMB if i == 4 else INK, big=38 if not P else 34)
    elif sid == "S06":
        chapter(sc, "THE DATA · 7,005 SMS")
        capture(sc, [seg(4, 0.2, d, [("(7005, 3)", at(sid, "7"))], zoom=1.5)])
    elif sid == "X01":
        chapter(sc, "WHAT THE MESSAGES LOOK LIKE")
        ex = [("normal", "How is your day?", GRN, at(sid, "normal")),
              ("promo", "৪৫TK cashback! ৩১GB+৫০০min.@৪৫৪TK ৩০days", AMB, at(sid, "promotion")),
              ("scam", "Apni 3 bhori sona jitechen! Bistrito jante kol korun: +88017XXXXXXXX", RED, at(sid, "scam"))]
        sc.css.append(FONT)
        for i, (lab_, txt, col, t) in enumerate(ex):
            el = sc.id(f"ex{i}")
            sc.add(f'<div id="{el}" class="exr"><i style="background:{col}">{lab_}</i><span>{escape(txt)}</span></div>',
                   f"#{el}{{left:{L}px;top:{H * (0.20 if not P else 0.18) + i * (170 if not P else 260) * u}px;width:{W - 2 * L}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,x:{-40 * u}}},{{opacity:1,x:0,duration:.45,ease:"expo.out"}},{t:.2f});')
        sc.css.append(f"#root .exr{{position:absolute;display:flex;gap:{24 * u}px;align-items:center;padding:{20 * u}px {24 * u}px;{glass(sc)}}}"
                      f"#root .exr i{{font-style:normal;font-weight:900;font-size:{30 * u}px;color:#141517;padding:{6 * u}px {18 * u}px;border-radius:{10 * u}px;}}"
                      f"#root .exr span{{font-family:'NotoBN',Inter,sans-serif;font-size:{38 * u}px;line-height:1.35;}}")
        label(sc, "n", "real examples from the training data · phone number masked", L, H * (0.74 if not P else 0.72), size=26, color=MUTE, t=at(sid, "four"))
        styles = ["Bengali", "English", "Banglish", "Code-mixed"]
        for i, s_ in enumerate(styles):
            label(sc, f"s{i}", s_, L + (i * 270 if not P else (i % 2) * 450) * u, H * (0.80 if not P else 0.66) + (0 if not P else (i // 2) * 70 * u) - (0 if not P else 120 * u),
                  size=34, color=AMB, weight=800, t=at(sid, "four") + 0.2 * i)
    elif sid == "S07":
        chapter(sc, "THE REAL-WORLD SET · NEVER TRAINED ON")
        capture(sc, [seg(5, 0.2, d * 0.62, [("(520, 2)", at(sid, "five", default=2.5))], zoom=1.8)])
        lock(sc, "lk", W * (0.5 if not P else 0.5), H * (0.55 if not P else 0.50), t_in=at(sid, "locked", default=d * 0.66))
        label(sc, "lkt", "257 messages · locked until the end", W / 2, H * (0.70 if not P else 0.62), size=44, color=AMB, weight=800,
              t=at(sid, "locked", default=d * 0.66) + 0.3, anchor="center")
    elif sid == "S08":
        chapter(sc, "TRAP 1 · SAME TEMPLATE, NEW NUMBER")
        capture(sc, [seg(7, 0.2, d, [("81 of 1401", at(sid, "81"))], zoom=2.0)])
    elif sid == "X02":
        chapter(sc, "WHY LEAKAGE IS CHEATING")
        pair = ["Bangladesh Bank account has been blocked. Call to reactivate: +8801713233245",
                "Bangladesh Bank account has been blocked. Call to reactivate: +8801718788890"]
        for i, txt in enumerate(pair):
            el = sc.id(f"p{i}")
            hl = txt.rsplit(" ", 1)
            sc.add(f'<div id="{el}" class="pr">{escape(hl[0])} <b>{escape(hl[1])}</b></div>',
                   f"#{el}{{left:{L}px;top:{H * (0.22 if not P else 0.20) + i * (130 if not P else 230) * u}px;width:{W - 2 * L}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:{20 * u}}},{{opacity:1,y:0,duration:.4,ease:"expo.out"}},{at(sid, "look", default=5) + i * 0.4:.2f});')
        sc.js.append(f'tl.to("#root .pr b",{{color:"{RED}",duration:.3}},{at(sid, "different", default=7):.2f});')
        sc.css.append(f"#root .pr{{position:absolute;padding:{20 * u}px {26 * u}px;font-family:'JetBrains Mono',monospace;font-size:{(32 if not P else 30) * u}px;"
                      f"line-height:1.4;{glass(sc)}}}#root .pr b{{color:{INK};}}")
        label(sc, "m1", "two real training messages · the only difference: the phone number", L, H * (0.48 if not P else 0.47), size=28, color=MUTE, t=at(sid, "different", default=7))
        big_number(sc, "g", "5,495", "near-duplicate groups · each one on ONE side of the split", L, H * (0.56 if not P else 0.54), at(sid, "5"), w=W * 0.86)
    elif sid == "S09":
        chapter(sc, "MODEL 1 · TF-IDF + LOGISTIC REGRESSION")
        capture(sc, [seg(11, 0.2, d, [("LAB PR-AUC 0.997", at(sid, "0.997", default=5))], zoom=2.2)])
    elif sid == "X03":
        b.code_scene(sc, "X03")
    elif sid == "X04":
        chapter(sc, "HOW TO READ THE SCORE · PRECISION–RECALL")
        box = (L, H * (0.15 if not P else 0.18), W * (0.56 if not P else 0.90), H * (0.66 if not P else 0.40))
        X, Y, bx = chart(sc, "pr", box, (0, 1), (0, 1), "recall · share of scams caught", "precision · right when it says scam",
                         ([0, .25, .5, .75, 1], [0, .25, .5, .75, 1], lambda v: f"{v:.0%}"))
        lab_, wild = RES["lab"]["TF-IDF"], RES["wild"]["TF-IDF"]
        curve(sc, bx, "rl", X, Y, [0, 1], [RES["base"]["lab"]] * 2, MUTE, at(sid, "random", default=14), dash=f"{12 * u} {9 * u}", width=4)
        curve(sc, bx, "rw", X, Y, [0, 1], [RES["base"]["wild"]] * 2, RED, at(sid, "real", default=20), dash=f"{12 * u} {9 * u}", width=4)
        curve(sc, bx, "cl", X, Y, lab_["recall"], lab_["precision"], AMB, at(sid, "precision", default=4), d=1.6, width=7)
        kx, ky = (box[0] + box[2] + 50 * u, H * 0.18) if not P else (L, H * 0.62)
        kw = (W - kx - L) if not P else W * 0.9
        label(sc, "p", "Precision: when it says scam, is it right?", kx, ky, size=34, weight=800, t=at(sid, "precision", default=4), w=kw)
        label(sc, "r", "Recall: of all scams, how many caught?", kx, ky + (110 if not P else 60) * u, size=34, weight=800, t=at(sid, "recall", default=8), w=kw)
        label(sc, "a", f"— TF-IDF, lab · area {lab_['ap']:.3f}", kx, ky + (230 if not P else 130) * u, size=32, color=AMB, weight=800, t=at(sid, "perfect", default=11), w=kw)
        label(sc, "b1", f"- - random, lab · {RES['base']['lab']:.2f}", kx, ky + (290 if not P else 180) * u, size=32, color=MUTE, weight=800, t=at(sid, "random", default=14), w=kw)
        label(sc, "b2", f"- - random, real set · {RES['base']['wild']:.2f}", kx, ky + (350 if not P else 230) * u, size=32, color=RED, weight=800, t=at(sid, "real", default=20), w=kw)
    elif sid == "S10":
        chapter(sc, "THEN: THE REAL MESSAGES")
        capture(sc, [seg(11, 0.2, d, [("WILD PR-AUC 0.923", at(sid, "0.92", default=2.5))], zoom=2.2)])
        stamp(sc, "st", "0.997 → 0.923", W * (0.5 if not P else 0.08), H * (0.68 if not P else 0.62), RED, at(sid, "strange", default=5), size=72)
    elif sid == "H2":    # reel 2 frame 1: the real false alarm, already on screen
        aura(sc, (RED, AMB))
        pw, phh = (W * 0.32, H * 0.62) if not P else (W * 0.88, H * 0.36)
        px, py = (W * 0.10, H * 0.22) if not P else ((W - pw) / 2, H * 0.07)
        sms_phone(sc, px, py, pw, phh, "Bank", [("s", "Salary credited: 35,000 BDT has been deposited to your account", "a real, safe message from the test set", 0.0)])
        stamp(sc, "st", "SCAM · 0.99", px + pw * 0.18, py + (400 if not P else 345) * u, RED, 0.5, size=76)
        kx, ky = (W * 0.50, H * 0.30) if not P else (L, H * 0.45)
        label(sc, "k1", "99.7 in the lab.", kx, ky, size=100, weight=900, t=0.0)
        label(sc, "k2", "Then this.", kx, ky + 130 * u, size=100, color=RED, weight=900, t=0.9)
        label(sc, "k3", "a real salary message, called a scam by the model", kx, ky + 260 * u, size=34, color="#B8B5AE", weight=700, t=1.4, w=W * (0.42 if not P else 0.9))
    elif sid in ("S11", "S12"):
        chapter(sc, "FALSE ALARMS" if sid == "S11" else "MISSED SCAMS")
        hl = ([("Salary credited: 35,000 BDT has been deposited to your account", at(sid, "salary")),
               ("Thank you for your recent bank deposit of BDT 5000.", at(sid, "deposit"))] if sid == "S11"
              else [("Claim your cashback reward #10 now! Limited time offer.", at(sid, "cashback"))])
        capture(sc, [seg(14, 0.2, d, hl, zoom=1.6)])
    elif sid == "S13":
        chapter(sc, "WHY? THE TRAINING SCAMS LOOK DIFFERENT")
        rows = [("link · training", 0.560, AMB, at(sid, "56"), True), ("link · real world", 0.019, RED, at(sid, "2"), True),
                ("OTP/PIN · training", 0.064, AMB, at(sid, "otp", default=11), False), ("OTP/PIN · real world", 0.172, RED, at(sid, "otp", default=11) + 0.4, False)]
        hbars(sc, "cu", rows, (L, H * (0.24 if not P else 0.22), W * (0.88 if not P else 0.90), 0), 0.62, fmt="{:.1%}", rowh=(100 if not P else 120), lab_w=(0.30 if not P else 0.48))
        label(sc, "n", "share of scam messages with each cue · notebook cell [8]", L, H * (0.68 if not P else 0.58), size=26, color=MUTE, t=at(sid, "56") + 1)
        words_ = ["OTP", "PIN", "Verify", "Blocked"]
        for i, w_ in enumerate(words_):
            label(sc, f"w{i}", w_, L + i * (300 if not P else 250) * u, H * (0.74 if not P else 0.64), size=60, color=RED, weight=900,
                  t=at(sid, w_.lower(), default=11 + i * 0.6))
    elif sid == "X05":
        chapter(sc, "PROBLEM 2 · WHO DECIDES WHAT A SCAM IS?")
        card(sc, "a", "Training data", "a cashback offer → labelled PROMOTION", L, H * (0.20 if not P else 0.18), W * (0.42 if not P else 0.90), at(sid, "training"), GRN, big=44)
        card(sc, "b2", "Real-world set", "a similar offer → labelled SCAM", (L + W * 0.46) if not P else L, H * (0.20 if not P else 0.33), W * (0.42 if not P else 0.90), at(sid, "real"), RED, big=44)
        sms_phone(sc, (W - W * 0.40) / 2 if not P else L, H * (0.45 if not P else 0.48), W * (0.40 if not P else 0.90), H * (0.33 if not P else 0.20), "Unknown",
                  [("l", "You have a new message from the lottery office. Claim winnings.", "labelled SAFE in the real-world set", at(sid, "lottery", default=12))],
                  t_in=at(sid, "lottery", default=12) - 0.5)
        stamp(sc, "st", "LABEL NOISE", W * (0.62 if not P else 0.40), H * (0.70 if not P else 0.64), AMB, at(sid, "safe", default=15), size=54)
    elif sid == "S14":
        chapter(sc, "SHORTCUT LEARNING")
        rows = [("contains a link", "SCAM", at(sid, "link")), ("mentions money", "SCAM", at(sid, "money"))]
        for i, (a_, b2, t) in enumerate(rows):
            y = H * (0.26 if not P else 0.22) + i * (160 if not P else 200) * u
            fs = 64 if not P else 54
            label(sc, f"a{i}", a_, L, y, size=fs, weight=900, t=t)
            label(sc, f"r{i}", "→", L + (560 if not P else 560) * u, y, size=fs, color=MUTE, weight=900, t=t + 0.2)
            label(sc, f"b{i}", b2, L + (680 if not P else 660) * u, y, size=fs, color=RED, weight=900, t=t + 0.3)
        kinetic(sc, [("The model learned a shortcut,", at(sid, "called", default=6), AMB), ("not the idea.", at(sid, "common", default=8), INK)],
                top=H * (0.60 if not P else 0.50), size=72)
    elif sid == "S15":
        chapter(sc, "MODEL 2 · MULTILINGUAL EMBEDDINGS")
        capture(sc, [seg(16, 0.2, d, [("LAB PR-AUC 0.997", at(sid, "lab")), ("WILD PR-AUC 0.913", at(sid, "real"))], zoom=3.2)])
    elif sid == "X06":
        chapter(sc, "WHAT IS AN EMBEDDING?")
        sc.css.append(FONT)
        msg = sc.id("msg")
        sc.add(f'<div id="{msg}" class="em">Bangladesh Bank account has been blocked. Call to reactivate: +88017XXXXXXXX</div>', f"#{msg}{{left:{L}px;top:{H * (0.22 if not P else 0.20)}px;width:{W - 2 * L}px;}}")
        sc.appear(msg, 0.3)
        vec = ", ".join(f"{v:+.3f}" for v in [0.021, 0.037, -0.031, 0.017, 0.041, -0.018, -0.039, -0.029])   # real e5 values for this message
        vv = sc.id("vec")
        sc.add(f'<div id="{vv}" class="mono vv">[{vec}, … 768 numbers]</div>', f"#{vv}{{left:{L}px;top:{H * (0.40 if not P else 0.34)}px;width:{W - 2 * L}px;}}")
        sc.appear(vv, at(sid, "768", default=4))
        sc.css.append(f"#root .em{{position:absolute;font-family:'NotoBN',Inter,sans-serif;font-size:{54 * u}px;font-weight:800;padding:{16 * u}px {26 * u}px;{glass(sc)}}}"
                      f"#root .vv{{position:absolute;font-size:{(34 if not P else 30) * u}px;color:{AMB};line-height:1.4;}}")
        label(sc, "il", "its real e5 embedding: the first 8 of 768 numbers", L, H * (0.40 if not P else 0.34) + (70 if not P else 130) * u, size=24, color=MUTE, t=at(sid, "768", default=4) + .3)
        box = (L, H * (0.50 if not P else 0.44), W * (0.50 if not P else 0.90), H * (0.30 if not P else 0.28))
        m = REAL["e5_map"]; xs, ys = m["x"], m["y"]
        xr, yr = (min(xs), max(xs)), (min(ys), max(ys))
        X, Y, bx = chart(sc, "sp", box, xr, yr, "PCA 1", "PCA 2", ([], [], lambda v: ""), t0=at(sid, "similar", default=6))
        cols = {"normal": GRN, "promo": AMB, "smish": RED}
        t0 = at(sid, "similar", default=6)
        for j, lab_ in enumerate(["normal", "promo", "smish"]):
            pts = "".join(f'<circle cx="{X(a_):.1f}" cy="{Y(b2):.1f}" r="{4 * u:.1f}"/>' for a_, b2, l_ in zip(xs, ys, m["label"]) if l_ == lab_)
            g = sc.id(f"pg{j}")
            e.layer(sc, bx, f'<g id="{g}" fill="{cols[lab_]}" fill-opacity=".55">{pts}</g>')
            sc.js.append(f'tl.fromTo("#{g}",{{opacity:0}},{{opacity:1,duration:.5}},{t0 + 0.3 + j * 0.5:.2f});')
        kx = (box[0] + box[2] + 40 * u) if not P else L
        ky = H * (0.54 if not P else 0.75)
        for j, (lab_, txt) in enumerate([("normal", "normal"), ("promo", "promotion"), ("smish", "scam")]):
            label(sc, f"lg{j}", "● " + txt, kx, ky + j * 52 * u, size=34, color=cols[lab_], weight=800, t=t0 + 0.3 + j * 0.5)
        label(sc, "k", "similar meaning → close together", kx, ky + 170 * u, size=34, weight=800, t=at(sid, "close", default=8), w=(W - kx - L) if not P else W * .9)
        label(sc, "il2", "real: 1,500 of the 7,005 messages, their e5 embeddings projected to 2-D (PCA)", box[0], box[1] + box[3] + 12 * u, size=24, color=MUTE, t=t0, w=box[2])
    elif sid == "S16":
        chapter(sc, "MODEL 3 · FINE-TUNE XLM-RoBERTa")
        cx, cy = (W * 0.30, H * 0.52) if not P else (W * 0.5, H * 0.40)
        for i in range(6):
            el = sc.id(f"ly{i}")
            sc.add(f'<div id="{el}" class="ly">layer {12 - 2 * i if i < 5 else 1}</div>',
                   f"#{el}{{left:{cx - 230 * u}px;top:{cy - 230 * u + i * 80 * u}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,x:{-60 * u}}},{{opacity:1,x:0,duration:.4,ease:"expo.out"}},{0.4 + i * 0.12:.2f});')
        sc.css.append(f"#root .ly{{position:absolute;width:{460 * u}px;height:{62 * u}px;line-height:{62 * u}px;text-align:center;font-weight:800;font-size:{28 * u}px;"
                      f"color:#D9D6CE;{glass(sc)}}}")
        kx, ky = (W * 0.55, H * 0.24) if not P else (L, H * 0.64)
        label(sc, "a", "Transformer · 12 layers", kx, ky, size=48, weight=900, t=0.6)
        label(sc, "b2", "pretrained on 100 languages", kx, ky + 80 * u, size=40, color=AMB, weight=800, t=at(sid, "100", default=4))
        label(sc, "c", "3 passes over the training data", kx, ky + 150 * u, size=40, weight=800, t=at(sid, "three", default=7))
        label(sc, "d", "validation macro-F1 0.991", kx, ky + 220 * u, size=48, color=GRN, weight=900, t=at(sid, "0.991", default=at(sid, "validation", default=10)))
    elif sid == "X07":
        chapter(sc, "FINE-TUNING · THE REAL TRAINING LOG")
        capture(sc, [seg(19, 0.2, d, [("val macro-F1 0.9914", at(sid, "checkpoint", default=14))], zoom=1.6)])
        box = (W * (0.60 if not P else 0.05), H * (0.14 if not P else 0.56), W * (0.34 if not P else 0.90), H * (0.30 if not P else 0.16))
        X, Y, bx = chart(sc, "ls", box, (1, 3), (0, 0.4), "epoch", "loss", ([1, 2, 3], [0, .2, .4], lambda v: f"{v:g}"), t0=at(sid, "loss", default=17))
        curve(sc, bx, "lc", X, Y, [1, 2, 3], [0.3605, 0.0718, 0.0353], RED, at(sid, "loss", default=17) + 0.2, d=1.2, width=6)
    elif sid == "T1":
        chapter(sc, "INSIDE THE TRANSFORMER · 1 · TOKENS")
        sc.css.append(FONT)
        tk = REAL["tokens"]
        msg = sc.id("msg")
        sc.add(f'<div id="{msg}" class="tmsg">{escape(tk["text"])}</div>', f"#{msg}{{left:{L}px;top:{H * (0.17 if not P else 0.15)}px;width:{W - 2 * L}px;}}")
        sc.appear(msg, 0.3)
        wrap = sc.id("chips")
        t0 = at(sid, "tokenizer", default=2.5)
        chips = ""
        for i, (pc, tid) in enumerate(zip(tk["pieces"], tk["ids"])):
            hot = pc.strip("▁") in ("b", "K", "ash")
            chips += (f'<div id="{sc.id(f"tk{i}")}" class="tkc{" hot" if hot else ""}{" sp" if pc in ("<s>", "</s>") else ""}">'
                      f'<b>{escape(pc.replace("▁", "␣"))}</b><i>{tid}</i></div>')
        sc.add(f'<div id="{wrap}">{chips}</div>', f"#{wrap}{{position:absolute;left:{L}px;top:{H * (0.36 if not P else 0.32)}px;width:{W - 2 * L}px;"
               f"display:flex;flex-wrap:wrap;gap:{12 * u}px;}}")
        for i in range(len(tk["pieces"])):
            sc.js.append(f'tl.fromTo("#{sc.id(f"tk{i}")}",{{opacity:0,y:{18 * u},scale:.85}},{{opacity:1,y:0,scale:1,duration:.25,ease:"back.out(2)"}},{t0 + i * 0.07:.2f});')
        th = at(sid, "look", default=9)
        sc.js.append(f'tl.to("#root .tkc.hot",{{backgroundColor:"rgba(255,178,36,.28)",borderColor:"{AMB}",scale:1.12,duration:.3}},{th:.2f});')
        sc.css.append(f"#root .tmsg{{position:absolute;font-family:'NotoBN',Inter,sans-serif;font-size:{(46 if not P else 42) * u}px;font-weight:700;line-height:1.4;padding:{18 * u}px {26 * u}px;{glass(sc)}}}"
                      f"#root .tkc{{display:flex;flex-direction:column;align-items:center;padding:{10 * u}px {14 * u}px;border:{2 * u}px solid rgba(243,240,232,.25);"
                      f"border-radius:{10 * u}px;background:rgba(255,255,255,.05);}}#root .tkc b{{font-family:'NotoBN','JetBrains Mono',monospace;font-size:{(36 if not P else 34) * u}px;}}"
                      f"#root .tkc i{{font-style:normal;font-family:'JetBrains Mono',monospace;font-size:{20 * u}px;color:#B8B5AE;margin-top:{4 * u}px;}}"
                      f"#root .tkc.sp b{{color:{MUTE};}}")
        lb = label(sc, "n", f"{len(tk['pieces'])} tokens", L, H * (0.70 if not P else 0.62), size=80, color=AMB, weight=900, t=at(sid, "26", default=6))
        label(sc, "n2", "real XLM-RoBERTa tokenizer · ␣ marks the start of a word · grey = id number", L, H * (0.70 if not P else 0.62) + 100 * u, size=26, color=MUTE, t=at(sid, "26", default=6), w=W * 0.88)
    elif sid == "T2":
        chapter(sc, "INSIDE THE TRANSFORMER · 2 · ATTENTION")
        sc.css.append(FONT)
        a_ = REAL["attention"]; pcs, att = a_["pieces"], a_["cls_to_token"]
        mx = max(att)
        top_ = H * (0.24 if not P else 0.22)
        colw = (W - 2 * L) / len(pcs)
        ta = at(sid, "after", default=7)
        hdr = [("768 numbers per token", 0.3), (f"{a_['layers']} layers · {a_['heads']} attention heads each", at(sid, "twelve", default=3)), ("every token looks at every token", at(sid, "every", default=4))]
        for i, (t_, tt) in enumerate(hdr):
            label(sc, f"h{i}", t_, L, top_ + i * 56 * u, size=38, weight=800, t=tt, color=AMB if i == 1 else INK, w=W * 0.88)
        base_y = H * (0.66 if not P else 0.56); bh = H * (0.22 if not P else 0.16)
        for i, (pc, v) in enumerate(zip(pcs, att)):
            bar, lab_ = sc.id(f"ab{i}"), sc.id(f"al{i}")
            hh = max(3, bh * v / mx)
            col = RED if v / mx > 0.8 else (AMB if v / mx > 0.55 else "rgba(243,240,232,.35)")
            sc.add(f'<div id="{bar}" class="ab"></div><div id="{lab_}" class="al">{escape(pc.replace("▁", ""))}</div>',
                   f"#{bar}{{left:{L + i * colw + colw * 0.15}px;top:{base_y - hh}px;width:{colw * 0.7}px;height:{hh}px;background:{col};}}"
                   f"#{lab_}{{left:{L + i * colw}px;top:{base_y + 10 * u}px;width:{colw}px;}}")
            sc.js.append(f'tl.fromTo("#{bar}",{{scaleY:0}},{{scaleY:1,duration:.5,ease:"expo.out"}},{ta + i * 0.03:.2f});')
            sc.appear(lab_, ta - 0.4, y=0, d=.2)
        tags = {"ash": "bKash", "▁PIN": "PIN", "▁২৪": "24", "▁ভে": "verify"}
        for i, (pc, v) in enumerate(zip(pcs, att)):
            if pc in tags:
                tg = sc.id(f"tg{i}")
                sc.add(f'<div id="{tg}" class="atag">{tags[pc]}</div>', f"#{tg}{{left:{L + i * colw + colw / 2}px;top:{base_y - bh * v / mx - 56 * u}px;}}")
                sc.js.append(f'tl.fromTo("#{tg}",{{opacity:0,y:{10 * u}}},{{opacity:1,y:0,duration:.3}},{at(sid, tags[pc].lower() if tags[pc] != "24" else "24", default=ta + 1):.2f});')
        sc.css.append(f"#root .atag{{position:absolute;transform:translateX(-50%);padding:{4 * u}px {12 * u}px;border-radius:{8 * u}px;background:{RED};color:#141517;"
                      f"font-weight:900;font-size:{26 * u}px;white-space:nowrap;}}")
        sc.css.append(f"#root .ab{{position:absolute;border-radius:{4 * u}px {4 * u}px 0 0;transform-origin:50% 100%;}}"
                      f"#root .al{{position:absolute;text-align:center;font-family:'NotoBN','JetBrains Mono',monospace;font-size:{(20 if not P else 19) * u}px;color:#D9D6CE;"
                      f"writing-mode:{'horizontal-tb' if not P else 'vertical-rl'};}}")
        label(sc, "n", "real attention of the fine-tuned model: last layer, average of 12 heads, from the classification token · attention shows focus, not proof",
              L, base_y + (60 if not P else 120) * u, size=24, color=MUTE, t=ta, w=W * 0.88)
    elif sid == "T3":
        chapter(sc, "INSIDE THE TRANSFORMER · 3 · THE VERDICT")
        ba = REAL["before_after"]; names_ = ["normal", "promotion", "scam"]
        cw = W * (0.40 if not P else 0.90)
        x2 = (L + cw + W * 0.08) if not P else L
        tb, tf = at(sid, "before", default=5), at(sid, "after", nth=0, default=10)
        label(sc, "b0", "untrained head (random)", L, H * (0.22 if not P else 0.20), size=40, weight=900, color=MUTE, t=tb - 0.3)
        meters(sc, "mb", [(n, v, tb + i * 0.2) for i, (n, v) in enumerate(zip(names_, ba["before"]))], L, H * (0.30 if not P else 0.27), cw, fmt="{:.1%}")
        y2 = H * (0.22 if not P else 0.50)
        label(sc, "a0", "after fine-tuning", x2, y2, size=40, weight=900, color=GRN, t=tf - 0.3)
        meters(sc, "ma", [(n, v, tf + i * 0.2) for i, (n, v) in enumerate(zip(names_, ba["after"]))], x2, y2 + H * 0.08, cw, fmt="{:.1%}")
        label(sc, "n", "real outputs for the bKash scam SMS · softmax over 3 classes · fine-tuned checkpoint saved by the notebook", L, H * (0.68 if not P else 0.735),
              size=24, color=MUTE, t=tb, w=W * 0.88)
    elif sid == "T4":
        chapter(sc, "HOW IT LEARNS · THE TRAINING LOOP")
        boxes = [("16 messages", "one batch"), ("XLM-RoBERTa", "278,045,955 weights"), ("3 scores", "softmax"), ("loss", "cross-entropy")]
        bw_ = (W - 2 * L - 3 * 40 * u) / 4 if not P else W * 0.42
        pos = [(L + i * (bw_ + 40 * u), H * 0.20) for i in range(4)] if not P else [(L + (i % 2) * (bw_ + 40 * u), H * 0.17 + (i // 2) * 150 * u) for i in range(4)]
        for i, ((t_, sub), (x_, y_)) in enumerate(zip(boxes, pos)):
            el = card(sc, f"b{i}", t_, sub, x_, y_, bw_, 0.3 + i * 0.35, RED if i == 3 else (AMB if i == 1 else INK), big=40)
        countup(sc, sc.id("b1"), 278045955, 0.65, d=1.6, sel="span", suffix=" weights")
        sc.css.append(f"#{sc.id('b1')} span{{font-family:'JetBrains Mono',monospace;}}")
        # data pulses forward (amber) and the error flowing back (red)
        y_f = (pos[0][1] + 125 * u) if not P else H * 0.36
        x_a, x_b = pos[0][0] + 20 * u, (pos[3][0] + bw_ - 20 * u) if not P else (pos[1][0] + bw_)
        tb = at(sid, "backpropagation", default=6)
        for k in range(3):
            fwd, bwd = sc.id(f"pf{k}"), sc.id(f"pb{k}")
            sc.add(f'<div id="{fwd}" class="pulse" style="background:{AMB}"></div><div id="{bwd}" class="pulse" style="background:{RED}"></div>',
                   f"#{fwd},#{bwd}{{left:{x_a}px;top:{y_f}px;}}")
            sc.js.append(f'tl.fromTo("#{fwd}",{{x:0,opacity:1}},{{x:{x_b - x_a},duration:1.1,ease:"none"}},{1.5 + k * 1.3:.2f});tl.to("#{fwd}",{{opacity:0,duration:.1}},{2.6 + k * 1.3:.2f});')
            sc.js.append(f'tl.fromTo("#{bwd}",{{x:{x_b - x_a},y:{14 * u},opacity:1}},{{x:0,duration:1.1,ease:"none"}},{tb + k * 1.3:.2f});tl.to("#{bwd}",{{opacity:0,duration:.1}},{tb + 1.1 + k * 1.3:.2f});')
        sc.css.append(f"#root .pulse{{position:absolute;width:{18 * u}px;height:{18 * u}px;border-radius:50%;opacity:0;box-shadow:0 0 {18 * u}px currentColor;}}")
        label(sc, "fw", "→ forward: predict", L, y_f + 30 * u, size=28, color=AMB, weight=800, t=1.5)
        label(sc, "bk", "← backpropagation: nudge every weight", L + (520 if not P else 0) * u, y_f + (30 if not P else 70) * u, size=28, color=RED, weight=800, t=tb)
        lr = REAL["lr"]
        box = (L, H * (0.48 if not P else 0.50), W * (0.62 if not P else 0.90), H * (0.30 if not P else 0.20))
        X, Y, bx = chart(sc, "lr", box, (0, lr["steps"]), (0, 2.1), "training step", "learning rate ×10⁻⁵",
                         ([0, lr["per_epoch"], 2 * lr["per_epoch"], lr["steps"]], [0, 1, 2], lambda v: f"{v:g}"), t0=at(sid, "steps", default=12) - 1.5)
        xs = [i * 4 for i in range(len(lr["lr"]))]
        curve(sc, bx, "lc", X, Y, xs, lr["lr"], AMB, at(sid, "steps", default=12) - 1.2, d=1.4, width=5)
        for ep in (1, 2):
            curve(sc, bx, f"ep{ep}", X, Y, [ep * lr["per_epoch"]] * 2, [0, 2.1], MUTE, at(sid, "epoch", default=13), dash=f"{8 * u} {8 * u}", width=3)
        mk = sc.id("mk")
        e.layer(sc, bx, f'<circle id="{mk}" cx="{X(0):.1f}" cy="{Y(0):.1f}" r="{12 * u}" fill="{RED}"/>')
        pts = [(X(x_), Y(y_)) for x_, y_ in zip(xs, lr["lr"])][::6]
        kf = ",".join(f'{{x:{px_ - X(0):.1f},y:{py_ - Y(0):.1f}}}' for px_, py_ in pts)
        sc.js.append(f'tl.to("#{mk}",{{keyframes:[{kf}],duration:3.2,ease:"none"}},{at(sid, "876", default=16) - 1.2:.2f});')
        label(sc, "n", f"real schedule from the notebook: {lr['warmup']}-step warm-up, then linear decay · {lr['per_epoch']} steps per epoch · {lr['steps']} total",
              box[0], box[1] + box[3] + 12 * u, size=24, color=MUTE, t=at(sid, "steps", default=12), w=box[2])
    elif sid == "T5":
        chapter(sc, "WHAT TF-IDF LEARNED · ITS REAL WEIGHTS")
        tw = dict((k_, v) for k_, v in REAL["tfidf_words"]["scam"])
        rows = [("korun + number  (call this number)", tw["korun 0"], RED, at(sid, "korun", default=4), True),
                ("করুন + number  (Bangla, same meaning)", tw["করন 0"], RED, at(sid, "korun", default=4) + 0.3, False),
                ("click", tw["click"], AMB, at(sid, "click", default=8), False), ("your", tw["your"], AMB, at(sid, "your", default=8.5), False),
                ("bank", tw["bank"], AMB, at(sid, "bank", default=9), False), ("income", tw["income"], AMB, at(sid, "income", default=9.5), False)]
        hbars(sc, "tw", rows, (L, H * (0.20 if not P else 0.18), W * (0.88 if not P else 0.90), 0), 2.8, fmt="+{:.2f}", rowh=(72 if not P else 110), lab_w=(0.44 if not P else 0.62))
        tb_ = at(sid, "honest", default=12)
        card(sc, "bug", "A bug I found making this video", "my text cleaning dropped Bangla vowel signs: করুন became করন. It still scored 0.997, but it will be fixed.",
             L, H * (0.67 if not P else 0.62), W * (0.88 if not P else 0.90), tb_, RED, big=40)
        sc.css.append(FONT + f"#{sc.id('bug')} span{{font-family:'NotoBN',Inter,sans-serif;}}")
        label(sc, "n", f"largest positive word weights for 'scam' out of {REAL['tfidf_words']['n_features']:,} features", L, H * (0.615 if not P else 0.56), size=24, color=MUTE,
              t=at(sid, "korun", default=4), w=W * 0.88)
    elif sid in ("A1", "B1", "C1", "D1"):      # Short hooks: the SMS on frame 1, the question in big type
        aura(sc, (RED, AMB) if sid != "D1" else (AMB, GRN))
        txt, gl, snd = (MISTAKE, "“I sent it by mistake, please send it back.”", "01712XXXXXX") if sid == "D1" else (SCAM_SMS[0], SCAM_SMS[1], "+880 17XX-XXXXXX")
        pw = W * 0.90; px, py = (W - pw) / 2, H * 0.06
        sms_phone(sc, px, py, pw, H * 0.40, snd, [("a", txt, gl, 0.0)])
        scanline(sc, "scan", px + 20 * u, py + 120 * u, pw - 40 * u, 200 * u, 0.9, label="ANALYZING")
        T = {"A1": ([("How a classic", INK), ("ML model decides", AMB)], "TF-IDF + logistic regression · step by step · real numbers"),
             "B1": ([("How a model", INK), ("reads meaning", AMB)], "multilingual embeddings (e5) · step by step · real numbers"),
             "C1": ([("Inside a", INK), ("Transformer", AMB)], "XLM-RoBERTa · real tokens, real attention, real training"),
             "D1": ([("Never trained.", INK), ("Still decides.", AMB)], "an open LLM, zero-shot · step by step · real numbers")}[sid]
        hook_title(sc, T[0], T[1], H * 0.36)
    elif sid == "A2":
        stepbar(sc, ["CLEAN", "PIECES", "TF-IDF", "WEIGHTS", "SOFTMAX"], 0)
        tf = REAL2["tfidf"]; sc.css.append(FONT)
        card(sc, "o", "original", f"<span style='font-family:NotoBN;font-size:{40 * u}px;color:#F3F0E8'>{escape(tf['text'])}</span>", L, H * 0.20, W * 0.90, 0.4, INK, big=30)
        card(sc, "c", "cleaned (what the model sees)", f"<span style='font-family:NotoBN;font-size:{40 * u}px;color:{AMB}'>{escape(tf['normalised'])}</span>", L, H * 0.40, W * 0.90, at(sid, "numbers", default=2), AMB, big=30)
        label(sc, "a", "2 4 → 0 · punctuation removed · lower case", L, H * 0.60, size=32, weight=800, t=at(sid, "punctuation", default=4), w=W * 0.9)
        card(sc, "bug", "BUG: Bangla vowel signs dropped", "<span style='font-family:NotoBN'>আপনার → আপনর · একাউন্ট → একউনট</span> — I will fix it", L, H * 0.66, W * 0.90,
             at(sid, "vowel", default=6), RED, big=40)
    elif sid == "A3":
        stepbar(sc, ["CLEAN", "PIECES", "TF-IDF", "WEIGHTS", "SOFTMAX"], 1)
        tf = REAL2["tfidf"]; sc.css.append(FONT)
        label(sc, "r", "2–5 letter pieces + words + word pairs", L, H * 0.20, size=40, weight=900, t=0.4, w=W * 0.9)
        for i, t_ in enumerate(tf["top"]):
            el = sc.id(f"pc{i}")
            sc.add(f'<div id="{el}" class="pc">{escape(t_["piece"].replace(" ", "␣"))}</div>', f"#{el}{{left:{L + (i % 3) * W * 0.30}px;top:{H * 0.28 + (i // 3) * 120 * u}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:.6}},{{opacity:1,scale:1,duration:.3,ease:"back.out(2)"}},{at(sid, "pieces", default=2) + i * 0.15:.2f});')
        sc.css.append(f"#root .pc{{position:absolute;padding:{14 * u}px {26 * u}px;font-family:'NotoBN','JetBrains Mono',monospace;font-size:{44 * u}px;font-weight:800;color:{AMB};{glass(sc)}}}")
        label(sc, "pn", "a few of this message's real pieces", L, H * 0.43, size=26, color=MUTE, t=at(sid, "pieces", default=2) + 1, w=W * 0.9)
        n1 = label(sc, "n1", f"{tf['n_active']}", L, H * 0.50, size=170, color=AMB, weight=900, t=at(sid, "174", default=8))
        countup(sc, n1, tf["n_active"], at(sid, "174", default=8), d=1.0, sel="div")
        label(sc, "n2", "pieces light up", L, H * 0.50 + 200 * u, size=48, weight=900, t=at(sid, "174", default=8) + 0.2)
        label(sc, "n3", f"out of {tf['n_features']:,} the model knows", L, H * 0.50 + 270 * u, size=40, color="#B8B5AE", weight=800, t=at(sid, "74", default=11), w=W * 0.9)
    elif sid == "A4":
        stepbar(sc, ["CLEAN", "PIECES", "TF-IDF", "WEIGHTS", "SOFTMAX"], 2)
        tf = REAL2["tfidf"]; sc.css.append(FONT)
        el = sc.id("f")
        sc.add(f'<div id="{el}" class="fm">tf-idf = (1 + log tf) × idf<br><small>idf = ln((1 + N) / (1 + df)) + 1</small></div>', f"#{el}{{left:{L}px;top:{H * 0.20}px;width:{W * 0.90}px;}}")
        sc.appear(el, at(sid, "tf", default=2))
        sc.css.append(f"#root .fm{{position:absolute;padding:{26 * u}px {30 * u}px;font-family:'JetBrains Mono',monospace;font-size:{44 * u}px;color:{INK};line-height:1.5;{glass(sc)}}}"
                      f"#root .fm small{{font-size:{34 * u}px;color:{AMB};}}")
        label(sc, "n", "N = 4,668 training messages · df = how many contain the piece · then each message is scaled to length 1", L, H * 0.36, size=26, color=MUTE, t=at(sid, "tf", default=2) + 1, w=W * 0.9)
        rows = [(f"“{t_['piece'].strip()}”", t_["idf"], RED if t_["idf"] > 5 else AMB, at(sid, "common", default=6) + i * 0.3, False) for i, t_ in enumerate(tf["top"][:4])]
        label(sc, "it", "real idf: rare pieces score higher", L, H * 0.43, size=40, weight=900, t=at(sid, "common", default=6) - 0.3, w=W * 0.9)
        hbars(sc, "idf", rows, (L, H * 0.49, W * 0.90, 0), 7.0, fmt="{:.2f}", rowh=110, lab_w=0.36)
        sc.css.append(f"#root .hbl{{font-family:'NotoBN',Inter,sans-serif;}}")
    elif sid == "A5":
        stepbar(sc, ["CLEAN", "PIECES", "TF-IDF", "WEIGHTS", "SOFTMAX"], 3)
        tf = REAL2["tfidf"]; sc.css.append(FONT)
        hdr = sc.id("th")
        sc.add(f'<div id="{hdr}" class="tr th"><span>piece</span><span>tf-idf</span><span>× weight</span><span>= adds</span></div>', f"#{hdr}{{top:{H * 0.19}px;}}")
        sc.appear(hdr, 0.3, y=0)
        for i, t_ in enumerate(tf["top"]):
            el = sc.id(f"tr{i}")
            sc.add(f'<div id="{el}" class="tr"><span>{escape(t_["piece"].strip())}</span><span>{t_["tfidf"]:.3f}</span><span>{t_["weight"]:+.2f}</span><b>{t_["contrib"]:+.3f}</b></div>',
                   f"#{el}{{top:{H * 0.23 + i * 76 * u}px;}}")
            sc.appear(el, at(sid, "multiply", default=4) + i * 0.35, y=10, d=.3)
        sc.css.append(f"#root .tr{{position:absolute;left:{L}px;width:{W * 0.90}px;display:grid;grid-template-columns:1.3fr 1fr 1fr 1fr;padding:{12 * u}px {20 * u}px;"
                      f"font-family:'NotoBN','JetBrains Mono',monospace;font-size:{36 * u}px;border-bottom:{1.5 * u}px solid rgba(243,240,232,.12);}}"
                      f"#root .tr b{{color:{RED};}}#root .th{{font-family:Inter,sans-serif;font-weight:900;font-size:{28 * u}px;color:{AMB};}}")
        label(sc, "s1", f"+ the other {tf['n_active'] - 6} pieces", L, H * 0.23 + 6 * 76 * u + 10 * u, size=30, color=MUTE, t=at(sid, "174", default=12), w=W * 0.9)
        y0 = H * 0.55
        sm = label(sc, "sum", f"{tf['sum_smish']:.2f}", L, y0, size=110, color=AMB, weight=900, t=at(sid, "4.36", default=14))
        countup(sc, sm, tf["sum_smish"], at(sid, "4.36", default=14), d=1.0, dec=2, sel="div")
        label(sc, "suml", "sum of all pieces", L + W * 0.36, y0 + 40 * u, size=36, weight=800, t=at(sid, "4.36", default=14))
        label(sc, "b2", f"{tf['intercept_smish']:+.2f}", L, y0 + 130 * u, size=110, color=RED, weight=900, t=at(sid, "bias", default=16))
        label(sc, "bl", "bias", L + W * 0.36, y0 + 170 * u, size=36, weight=800, t=at(sid, "bias", default=16))
        label(sc, "eq", f"= {tf['logits']['smish']:.2f}  scam score", L, y0 + 280 * u, size=90, color=GRN, weight=900, t=at(sid, "3.14", default=19), w=W * 0.9)
    elif sid == "A6":
        stepbar(sc, ["CLEAN", "PIECES", "TF-IDF", "WEIGHTS", "SOFTMAX"], 4)
        tf = REAL2["tfidf"]; names_ = [("normal", "normal"), ("promo", "promotion"), ("smish", "scam")]
        label(sc, "lg", "scores (logits)", L, H * 0.20, size=40, weight=900, t=0.3)
        for i, (k_, n) in enumerate(names_):
            label(sc, f"z{i}", f"{n}  {tf['logits'][k_]:+.2f}", L, H * 0.26 + i * 70 * u, size=48, weight=800, color=RED if k_ == "smish" else INK, t=0.4 + i * 0.2, mono=True)
        el = sc.id("sm")
        sc.add(f'<div id="{el}" class="fm">softmax: p = e<sup>z</sup> / Σ e<sup>z</sup></div>', f"#{el}{{left:{L}px;top:{H * 0.44}px;width:{W * 0.90}px;}}")
        sc.appear(el, at(sid, "softmax", default=2))
        sc.css.append(f"#root .fm{{position:absolute;padding:{22 * u}px {30 * u}px;font-family:'JetBrains Mono',monospace;font-size:{42 * u}px;color:{AMB};{glass(sc)}}}")
        meters(sc, "pm", [(n, tf["proba"][k_], at(sid, "probabilities", default=4) + i * 0.25) for i, (k_, n) in enumerate(names_)], L, H * 0.54, W * 0.90, fmt="{:.1%}")
        stamp(sc, "st", f"SCAM · {tf['proba']['smish']:.1%}", L + W * 0.15, H * 0.72, RED, at(sid, "answer", default=6.5), size=72)
    elif sid == "A7":
        aura(sc, (AMB, GRN))
        for i, (t_, c_, tok) in enumerate([("✓ fast", GRN, "fast"), ("✓ explainable", GRN, "explainable"), ("✓ runs anywhere", GRN, "anywhere"), ("✗ only knows pieces it has seen", RED, "only")]):
            label(sc, f"p{i}", t_, L, H * 0.18 + i * 100 * u, size=64, color=c_, weight=900, t=at(sid, tok, default=1 + i), w=W * 0.9)
        label(sc, "nx", "NEXT", L, H * 0.60, size=40, color=AMB, weight=900, t=at(sid, "next", default=6))
        label(sc, "nx2", "How a model reads meaning", L, H * 0.60 + 60 * u, size=72, weight=900, t=at(sid, "next", default=6), w=W * 0.9)
    elif sid == "B2":
        stepbar(sc, ["ENCODE", "COMPARE", "CLASSIFY"], 0)
        e5 = REAL2["e5"]; sc.css.append(FONT)
        card(sc, "m", "the bKash scam", f"<span style='font-family:NotoBN;color:#F3F0E8;font-size:{34 * u}px'>{escape(SCAM_SMS[0])}</span>", L, H * 0.19, W * 0.90, 0.3, RED, big=32)
        card(sc, "e", "e5 · multilingual encoder", "reads the whole message at once", L, H * 0.36, W * 0.90, at(sid, "e5", default=2), AMB, big=40)
        g = sc.id("grid"); cells = ""
        for i in range(768):
            v = e5["first8"][i] if i < 8 else None
            col = (GRN if v >= 0 else RED) if v is not None else "rgba(243,240,232,.10)"
            cells += f'<i style="background:{col}"></i>'
        sc.add(f'<div id="{g}" class="vg">{cells}</div>', f"#{g}{{left:{L}px;top:{H * 0.44}px;width:{W * 0.90}px;}}")
        sc.js.append(f'tl.fromTo("#{g} i",{{opacity:0}},{{opacity:1,duration:.02,stagger:.0022}},{at(sid, "768", default=5):.2f});')
        sc.css.append(f"#root .vg{{position:absolute;display:grid;grid-template-columns:repeat(32,1fr);gap:{3 * u}px;}}#root .vg i{{display:block;height:{13 * u}px;border-radius:{2 * u}px;}}")
        vec = ", ".join(f"{v:+.3f}" for v in e5["first8"])
        label(sc, "v", f"[{vec}, …]", L, H * 0.44 + 24 * 16 * u + 30 * u, size=30, color=AMB, mono=True, t=at(sid, "vector", default=8), w=W * 0.9)
        label(sc, "vn", "768 numbers · the first 8 are shown (green +, red −)", L, H * 0.44 + 24 * 16 * u + 130 * u, size=26, color=MUTE, t=at(sid, "vector", default=8), w=W * 0.9)
    elif sid == "B3":
        stepbar(sc, ["ENCODE", "COMPARE", "CLASSIFY"], 1)
        e5 = REAL2["e5"]; sc.css.append(FONT)
        label(sc, "h", "cosine similarity to our scam", L, H * 0.19, size=44, weight=900, t=0.3, w=W * 0.9)
        rows = []
        for i, (k_, txt) in enumerate(e5["others"].items()):
            card(sc, f"o{i}", k_, f"<span style='font-family:NotoBN'>{escape(txt[:60])}</span>", L, H * 0.26 + i * 0.16 * H, W * 0.62, at(sid, k_.split()[-1], default=4 + 2 * i), INK, big=34)
            rows.append((k_, e5["similarity"][k_], at(sid, k_.split()[-1], default=4 + 2 * i) + 0.4, i))
        for k_, v, t, i in rows:
            el = sc.id(f"sv{i}")
            sc.add(f'<div id="{el}" class="sv">{v:.3f}</div>', f"#{el}{{left:{L + W * 0.66}px;top:{H * 0.26 + i * 0.16 * H + 30 * u}px;}}")
            sc.appear(el, t, y=0, d=.3)
        sc.css.append(f"#root .sv{{position:absolute;font-family:'JetBrains Mono',monospace;font-weight:900;font-size:{72 * u}px;color:{AMB};}}")
        label(sc, "f", "cos θ = a · b / (|a| |b|)", L, H * 0.75, size=44, mono=True, color=GRN, weight=700, t=at(sid, "angle", default=3), w=W * 0.9)
    elif sid == "B4":
        stepbar(sc, ["ENCODE", "COMPARE", "CLASSIFY"], 2)
        label(sc, "h", "Similarity alone is not a decision.", L, H * 0.19, size=48, weight=900, t=at(sid, "alone", default=2), w=W * 0.9)
        box = (L, H * 0.30, W * 0.90, H * 0.36)
        m = REAL["e5_map"]; xs, ys = m["x"], m["y"]
        X, Y, bx = chart(sc, "sp", box, (min(xs), max(xs)), (min(ys), max(ys)), "PCA 1", "PCA 2", ([], [], lambda v: ""), t0=at(sid, "region", default=6) - 1)
        cols = {"normal": GRN, "promo": AMB, "smish": RED}
        for j, lab_ in enumerate(["normal", "promo", "smish"]):
            pts = "".join(f'<circle cx="{X(a_):.1f}" cy="{Y(b2):.1f}" r="{4 * u:.1f}"/>' for a_, b2, l_ in zip(xs, ys, m["label"]) if l_ == lab_)
            g = sc.id(f"pg{j}")
            e.layer(sc, bx, f'<g id="{g}" fill="{cols[lab_]}" fill-opacity=".55">{pts}</g>')
            sc.js.append(f'tl.fromTo("#{g}",{{opacity:0}},{{opacity:1,duration:.5}},{at(sid, "region", default=6) - 0.6 + j * 0.4:.2f});')
        label(sc, "lg", "● normal   ● promotion   ● scam", L, H * 0.68, size=34, weight=800, t=at(sid, "region", default=6), color="#D9D6CE")
        label(sc, "n", "real e5 embeddings of 1,500 training messages, in 2-D (PCA) · logistic regression learns the scam region from 4,668 labelled messages",
              L, H * 0.72, size=26, color=MUTE, t=at(sid, "region", default=6), w=W * 0.9)
    elif sid == "B5":
        e5 = REAL2["e5"]; names_ = [("normal", "normal"), ("promo", "promotion"), ("smish", "scam")]
        meters(sc, "pm", [(n, e5["proba"][k_], 0.4 + i * 0.25) for i, (k_, n) in enumerate(names_)], L, H * 0.16, W * 0.90, fmt="{:.1%}")
        stamp(sc, "st", f"SCAM · {e5['proba']['smish']:.0%}", L + W * 0.15, H * 0.42, RED, at(sid, "answer", default=1), size=72)
        label(sc, "c", "TF-IDF: 98.1% · e5: 77.0%", L, H * 0.54, size=44, weight=900, mono=True, t=at(sid, "confident", default=4), w=W * 0.9)
        label(sc, "c2", "less sure, but it reads meaning, not spelling", L, H * 0.54 + 70 * u, size=36, color="#B8B5AE", weight=800, t=at(sid, "meaning", default=6), w=W * 0.9)
        label(sc, "nx", "NEXT", L, H * 0.68, size=40, color=AMB, weight=900, t=at(sid, "next", default=8))
        label(sc, "nx2", "A Transformer we train ourselves", L, H * 0.68 + 60 * u, size=64, weight=900, t=at(sid, "next", default=8), w=W * 0.9)
    elif sid == "C9":
        aura(sc, (GRN, AMB))
        ba = REAL["before_after"]
        label(sc, "a", f"untrained: {ba['before'][2]:.1%} scam", L, H * 0.20, size=60, color=MUTE, weight=900, t=0.2, mono=True)
        label(sc, "b2", f"fine-tuned: {ba['after'][2]:.1%} scam", L, H * 0.27, size=60, color=GRN, weight=900, t=0.6, mono=True)
        label(sc, "nx", "NEXT", L, H * 0.50, size=40, color=AMB, weight=900, t=at(sid, "next", default=2))
        label(sc, "nx2", "An LLM that never saw this data", L, H * 0.50 + 60 * u, size=72, weight=900, t=at(sid, "next", default=2), w=W * 0.9)
    elif sid == "D2":
        chapter(sc, "ONE FORWARD PASS")
        steps_ = [("definition + question + SMS", "the prompt", 0.3), (f"{REAL['qwen_next']['prompt_tokens']} tokens", "after the tokenizer", at(sid, "167", default=4)),
                  ("Qwen2.5-3B", "3 billion parameters · one forward pass", at(sid, "billion", default=7)), ("a probability for every next word", "about 150,000 possible tokens", at(sid, "probability", default=9))]
        for i, (t_, sub, tt) in enumerate(steps_):
            card(sc, f"s{i}", t_, sub, L, H * 0.20 + i * 0.13 * H, W * 0.90, tt, AMB if i == 2 else INK, big=48)
        for k in range(3):
            pl = sc.id(f"pl{k}")
            sc.add(f'<div id="{pl}" class="pulse" style="background:{AMB}"></div>', f"#{pl}{{left:{W * 0.5}px;top:{H * 0.20}px;}}")
            sc.js.append(f'tl.fromTo("#{pl}",{{y:0,opacity:1}},{{y:{0.40 * H},duration:1.4,ease:"none"}},{2 + k * 1.6:.2f});tl.to("#{pl}",{{opacity:0,duration:.1}},{3.4 + k * 1.6:.2f});')
        sc.css.append(f"#root .pulse{{position:absolute;width:{20 * u}px;height:{20 * u}px;border-radius:50%;opacity:0;box-shadow:0 0 {22 * u}px {AMB};z-index:8;}}")
    elif sid == "D3":
        chapter(sc, "FROM PROBABILITIES TO AN ANSWER")
        qn = {}
        for w_, v in REAL["qwen_next"]["top"]:      # exact tokens first: "Yes" and " Yes" are different tokens
            qn.setdefault(w_.strip(), v)
        assert qn["Yes"] > 0.99, qn
        label(sc, "y", f"P(Yes) = {qn['Yes']:.4f}", L, H * 0.20, size=72, color=RED, weight=900, mono=True, t=at(sid, "yes", default=2))
        label(sc, "n", f"P(No)  = {qn['No']:.4f}", L, H * 0.27, size=72, color=GRN, weight=900, mono=True, t=at(sid, "no", default=4))
        label(sc, "f", f"score = {qn['Yes']:.4f} / ({qn['Yes']:.4f} + {qn['No']:.4f})", L, H * 0.40, size=42, mono=True, weight=700, t=at(sid, "share", default=7), w=W * 0.92)
        label(sc, "f2", f"= {qn['Yes'] / (qn['Yes'] + qn['No']):.2f}", L, H * 0.46, size=110, color=AMB, weight=900, mono=True, t=at(sid, "1.0", default=9))
        stamp(sc, "st", "SCAM · 1.00", L + W * 0.12, H * 0.62, RED, at(sid, "answer", default=10.5), size=80)
    elif sid == "D4":
        aura(sc, (GRN, AMB))
        q = LOCKED["Qwen2.5-3B (multilingual)"]
        label(sc, "a", "Locked real-world test", L, H * 0.18, size=48, weight=900, t=at(sid, "locked", default=3), w=W * 0.9)
        label(sc, "b2", f"PR-AUC {q['PR-AUC']:.3f}", L, H * 0.24, size=110, color=GRN, weight=900, mono=True, t=at(sid, "locked", default=3) + 0.3)
        label(sc, "c", f"caught {q['scams caught']:.1%} of scams · {q['false alarms']:.1%} false alarms · best of 5 models", L, H * 0.33, size=34, weight=800, color="#D9D6CE",
              t=at(sid, "best", default=5), w=W * 0.9)
        label(sc, "yt", "Full build on YouTube", L, H * 0.52, size=56, weight=900, t=at(sid, "youtube", default=7), color=AMB, w=W * 0.9)
        label(sc, "yt2", "▶ @csfunda.official", L, H * 0.52 + 80 * u, size=72, weight=900, t=at(sid, "youtube", default=7))
    elif sid == "S17":
        chapter(sc, "MODEL 3 · RESULT")
        capture(sc, [seg(19, 0.2, d, [("LAB PR-AUC 0.999", max(1.4, at(sid, "0.999", default=1.5))), ("WILD PR-AUC 0.904", at(sid, "0.9", nth=1, default=5))], zoom=2.0)])
    elif sid == "X08":
        chapter(sc, "THE KEY LESSON · LAB vs REAL")
        names = ["TF-IDF", "e5 embeddings", "XLM-RoBERTa (fine-tuned)"]
        rows = []
        for i, n in enumerate(names):
            rows += [(f"{n.split(' (')[0]} · lab", RES["lab"][n]["ap"], AMB, 0.4 + i * 0.3, False),
                     (f"{n.split(' (')[0]} · real", RES["wild"][n]["ap"], RED, at(sid, "dataset", default=4) + i * 0.3, False)]
        hbars(sc, "lr", rows, (L, H * (0.18 if not P else 0.16), W * (0.88 if not P else 0.90), 0), 1.0, fmt="{:.3f}", rowh=(78 if not P else 92), lab_w=(0.34 if not P else 0.52))
        label(sc, "k", "It mastered 7,005 messages, not scams.", L, H * (0.74 if not P else 0.66), size=56, color=AMB, weight=900, t=at(sid, "mastered", default=8), w=W * 0.88)
    elif sid == "S18":
        aura(sc, (AMB, GRN))
        kinetic(sc, [("What if the model", 0.2, INK), ("already knew", at(sid, "already"), AMB), ("what a scam is?", at(sid, "scam"), RED)],
                top=H * (0.28 if not P else 0.28), size=118)
    elif sid == "H3":    # reel 3 frame 1: one SMS, two models
        aura(sc, (AMB, GRN))
        pw, phh = (W * 0.34, H * 0.42) if not P else (W * 0.86, H * 0.26)
        px, py = (W * 0.06, H * 0.20) if not P else ((W - pw) / 2, H * 0.06)
        sms_phone(sc, px, py, pw, phh, "01712XXXXXX", [("m", MISTAKE, "“I sent it by mistake, please send it back.”", 0.0)])
        scanline(sc, "scan", px + 20 * u, py + 120 * u, pw - 40 * u, 170 * u, 1.0)
        cx0 = (W * 0.46) if not P else L
        cy0 = H * (0.22 if not P else 0.30)
        card(sc, "t", "TigerLLM-1B", "built for Bengali · 1 billion parameters", cx0, cy0, W * (0.48 if not P else 0.90), 0.0, GRN, big=56)
        card(sc, "q", "Qwen2.5-3B", "multilingual · 3 billion parameters", cx0, cy0 + (200 if not P else 220) * u, W * (0.48 if not P else 0.90), 0.0, AMB, big=56)
        label(sc, "vs", "Which one catches it?", cx0, cy0 + (430 if not P else 470) * u, size=72, weight=900, t=0.4, color=RED)
    elif sid == "S19":
        chapter(sc, "MODEL 4 · OPEN LLMs, ZERO-SHOT")
        txt = ("A message is a SCAM if it tries to make the reader act for the sender's benefit: share an OTP, PIN or password, "
               "click an unknown link, call or send money to an unknown number, pay a fee to get a prize, loan or job, "
               "or 'verify' an account to stop it being blocked.")
        el = sc.id("sys")
        sc.add(f'<div id="{el}" class="sysp"><i>system prompt · notebook cell [13]</i>{escape(txt)}</div>',
               f"#{el}{{left:{L}px;top:{H * (0.20 if not P else 0.20)}px;width:{W - 2 * L}px;}}")
        sc.appear(el, at(sid, "definition", default=4))
        sc.css.append(f"#root .sysp{{position:absolute;padding:{30 * u}px {34 * u}px;font-family:'JetBrains Mono',monospace;font-size:{(36 if not P else 32) * u}px;"
                      f"line-height:1.5;color:#E8E5DD;{glass(sc)}}}#root .sysp i{{display:block;font-style:normal;color:{AMB};font-size:{26 * u}px;margin-bottom:{12 * u}px;}}")
        label(sc, "n", "No training. Only a definition.", L, H * (0.70 if not P else 0.62), size=56, color=AMB, weight=900, t=0.5)
    elif sid == "S20":
        chapter(sc, "READING THE NEXT WORD")
        steps = [("SMS + definition", 0.4), ("LLM · one forward pass", at(sid, "forward", default=6)), ("next word: Yes or No?", at(sid, "yes", default=4))]
        for i, (s_, t) in enumerate(steps):
            card(sc, f"s{i}", s_, "", (L + i * W * 0.31) if not P else L, H * (0.20 if not P else 0.18 + i * 0.10), W * (0.28 if not P else 0.90), t, AMB if i == 2 else INK, big=40)
        qn = REAL["qwen_next"]["top"]
        tp = at(sid, "probability", default=3)
        meters(sc, "yn", [(f"next word “{w_.strip() or '·'}”", v, tp + i * 0.25) for i, (w_, v) in enumerate(qn[:4])],
               L, H * (0.42 if not P else 0.50), W * (0.50 if not P else 0.90), rowh=82, fmt="{:.4f}")
        label(sc, "f", "score = P(Yes) / (P(Yes) + P(No))", L, H * (0.745 if not P else 0.72), size=40, mono=True, weight=700, t=at(sid, "score", default=8), color=GRN)
        label(sc, "il", f"real next-word probabilities from Qwen2.5-3B for Rafi's message ({REAL['qwen_next']['prompt_tokens']}-token prompt)", L, H * (0.805 if not P else 0.76), size=24, color=MUTE, t=at(sid, "probability", default=3), w=W * 0.88)
    elif sid == "X09":
        chapter(sc, "A SCORE IS NOT A DECISION")
        lock(sc, "lk", W * (0.70 if not P else 0.5), H * (0.50 if not P else 0.62), t_open=at(sid, "opened", default=d - 2), t_in=0.3)
        label(sc, "a", "cut-off chosen on the OPEN half", L, H * (0.28 if not P else 0.22), size=52, weight=900, t=at(sid, "chose", default=5), w=W * (0.55 if not P else 0.9))
        label(sc, "b2", "→ applied unchanged to the LOCKED half", L, H * (0.42 if not P else 0.34), size=44, color=AMB, weight=800, t=at(sid, "only", default=8), w=W * (0.55 if not P else 0.9))
    elif sid == "S21":
        chapter(sc, "TWO CONTENDERS")
        cw = W * (0.42 if not P else 0.90)
        card(sc, "t", "TigerLLM-1B-it", "1 billion parameters · built for Bangla", L, H * (0.24 if not P else 0.22), cw, at(sid, "tiger", default=1), GRN, big=60)
        card(sc, "q", "Qwen2.5-3B-Instruct", "3 billion parameters · multilingual", (L + cw + 60 * u) if not P else L, H * (0.24 if not P else 0.42), cw,
             at(sid, "3", default=6), AMB, big=60)
        label(sc, "n", "TituLM-3B was also tested: a base model (not instruction-tuned), too slow on this laptop and near random in the trial run — left out.",
              L, H * (0.66 if not P else 0.62), size=26, color=MUTE, t=at(sid, "multilingual", default=8), w=W * 0.88)
    elif sid == "S22":
        chapter(sc, "ON THE REAL MESSAGES")
        box = (L, H * (0.15 if not P else 0.16), W * (0.56 if not P else 0.90), H * (0.66 if not P else 0.40))
        X, Y, bx = chart(sc, "w", box, (0, 1), (0, 1), "recall · scams caught", "precision", ([0, .5, 1], [0, .5, 1], lambda v: f"{v:.0%}"))
        curve(sc, bx, "rb", X, Y, [0, 1], [RES["base"]["wild"]] * 2, MUTE, 0.6, dash=f"{12 * u} {9 * u}", width=4)
        cols = {"TF-IDF": "#6E8BBF", "e5 embeddings": "#8A7DBF", "XLM-RoBERTa (fine-tuned)": "#B88AA6", "TigerLLM-1B (Bangla)": GRN, "Qwen2.5-3B (multilingual)": AMB}
        tt = {"TigerLLM-1B (Bangla)": at(sid, "0.81", default=3), "Qwen2.5-3B (multilingual)": at(sid, "0.98", default=6)}
        for i, (n, c) in enumerate(cols.items()):
            w_ = RES["wild"][n]
            curve(sc, bx, f"c{i}", X, Y, w_["recall"], w_["precision"], c, tt.get(n, 0.5 + i * 0.2), d=1.2, width=7 if n.startswith("Qwen") else 4)
        kx, ky = (box[0] + box[2] + 50 * u, H * 0.18) if not P else (L, H * 0.60)
        for i, (n, c) in enumerate(cols.items()):
            label(sc, f"l{i}", f"{n.split(' (')[0]} · {RES['wild'][n]['ap']:.3f}", kx, ky + i * (64 if not P else 56) * u, size=34, color=c, weight=800,
                  t=tt.get(n, 0.5 + i * 0.2), w=(W - kx - L) if not P else W * .9)
    elif sid == "S23":
        chapter(sc, "THE LOCKED TEST · USED ONCE")
        lock(sc, "lk", W / 2, H * (0.42 if not P else 0.38), t_open=at(sid, "once", default=d - 1.5), t_in=0.2, size=1.4)
        label(sc, "n", "257 real messages · no model has seen them", W / 2, H * (0.66 if not P else 0.56), size=48, weight=900, t=at(sid, "257", default=3), anchor="center")
    elif sid == "S24":
        chapter(sc, "THE LOCKED TEST · RESULT")
        capture(sc, [seg(24, 0.2, d * 0.62, [("0.957", at(sid, "0.96", default=2)), ("0.886", at(sid, "89", default=5)), ("0.162", at(sid, "16", default=7))], zoom=2.4)])
        t2 = d * 0.62
        rows = [("Qwen2.5-3B", LOCKED["Qwen2.5-3B (multilingual)"]["false alarms"], GRN, t2 + .2, True),
                ("TF-IDF", LOCKED["TF-IDF"]["false alarms"], RED, t2 + .45, False),
                ("XLM-RoBERTa", LOCKED["XLM-RoBERTa (fine-tuned)"]["false alarms"], RED, t2 + .7, False)]
        label(sc, "ft", "false alarms on safe messages (locked test)", L, H * (0.20 if not P else 0.18), size=40, weight=900, t=t2, w=W * 0.88)
        hbars(sc, "fa", rows, (L, H * (0.30 if not P else 0.26), W * (0.88 if not P else 0.90), 0), 0.5, fmt="{:.1%}", rowh=(110 if not P else 120), lab_w=(0.26 if not P else 0.40))
        sc.js.append(f'tl.to("#{sc.id("cam0")}",{{opacity:0,duration:.3}},{t2 - .3:.2f});')
    elif sid == "X10":
        chapter(sc, "WHY FALSE ALARMS MATTER")
        pw, phh = (W * 0.30, H * 0.70) if not P else (W * 0.64, H * 0.46)
        px = (W * 0.06) if not P else L
        sms_phone(sc, px, H * (0.13 if not P else 0.12), pw, phh, "Bank",
                  [("a", "Salary credited: 35,000 BDT has been deposited to your account", "", 0.3), ("b", "Payment of BDT 5000 received. Thank you for your timely payment.", "", 0.6), ("c", "Your OTP is 8741, do not share it with anyone.", "", 0.9)])
        for i, k in enumerate("abc"):
            stamp(sc, f"s{i}", "SCAM?", px + pw + 18 * u, sc.ys[k] + 20 * u, RED, at(sid, "flags", default=3) + i * 0.25, size=(40 if not P else 34), rot=-6)
        kx, ky = (W * 0.56, H * 0.30) if not P else (L, H * 0.62)
        label(sc, "k1", "You stop trusting it.", kx, ky, size=64, weight=900, t=at(sid, "trusting", default=5), w=W * (0.44 if not P else 0.9))
        label(sc, "k2", "Then you miss the real one.", kx, ky + 100 * u, size=64, color=RED, weight=900, t=at(sid, "ignore", default=7), w=W * (0.44 if not P else 0.9))
    elif sid == "S25":
        aura(sc, (AMB, RED))
        rows = [("XLM-RoBERTa · lab", RES["lab"]["XLM-RoBERTa (fine-tuned)"]["ap"], MUTE, 0.2, False),
                ("XLM-RoBERTa · locked", LOCKED["XLM-RoBERTa (fine-tuned)"]["PR-AUC"], RED, 0.5, False),
                ("Qwen2.5-3B · lab", RES["lab"]["Qwen2.5-3B (multilingual)"]["ap"], MUTE, 1.0, False),
                ("Qwen2.5-3B · locked", LOCKED["Qwen2.5-3B (multilingual)"]["PR-AUC"], GRN, 1.3, True)]
        label(sc, "h", "Best in the lab ≠ best in the real world", L, H * (0.14 if not P else 0.14), size=58, weight=900, color=AMB, t=0.1, w=W * 0.88)
        hbars(sc, "lw", rows, (L, H * (0.32 if not P else 0.30), W * (0.88 if not P else 0.90), 0), 1.0, fmt="{:.3f}", rowh=(110 if not P else 120), lab_w=(0.32 if not P else 0.52))
    elif sid in ("S26", "S27"):
        chapter(sc, "RAFI'S MESSAGES · REAL SCORES · CELL [16]")
        txt, gloss = (MISTAKE, "“I sent it by mistake, please send it back.”") if sid == "S26" else (CASHIN, "a fake notice, sent from an ordinary number")
        pw, phh = (W * 0.36, H * 0.46) if not P else (W * 0.90, H * 0.28)
        sms_phone(sc, L, H * (0.18 if not P else 0.15), pw, phh, "01712XXXXXX", [("x", txt, gloss, 0.3)])
        scores = ([("TF-IDF", 0.14), ("XLM-RoBERTa", 0.00), ("Qwen2.5-3B", 1.00)] if sid == "S26" else [("TF-IDF", 0.44), ("XLM-RoBERTa", 1.00), ("Qwen2.5-3B", 0.54)])
        t0 = at(sid, "qwen", default=at(sid, "kwen", default=3)) if sid == "S26" else at(sid, "unsure", default=2)
        mx = (L + pw + 70 * u) if not P else L
        meters(sc, "m", [(n, s, t0 - 0.6 + i * 0.35) for i, (n, s) in enumerate(scores)], mx, H * (0.22 if not P else 0.48), (W - mx - L) if not P else W * 0.9)
        if sid == "S27":
            label(sc, "n", "XLM-R flags almost anything about money: 45% false alarms on the locked test", mx, H * (0.58 if not P else 0.70), size=26, color=MUTE,
                  t=t0 + 2, w=(W - mx - L) if not P else W * 0.9)
            stamp(sc, "st", "THE CLUE IS THE SENDER", (mx) if not P else L, H * (0.66 if not P else 0.62), AMB, at(sid, "sender", default=8), size=44, rot=-4)
    elif sid == "S28":
        aura(sc, (GRN, AMB))
        kinetic(sc, [("Check the payment", 0.3, INK), ("in your own app.", at(sid, "app", default=3), GRN),
                     ("Never share an OTP or a PIN.", at(sid, "never", nth=1, default=8), AMB)], top=H * (0.18 if not P else 0.20), size=96)
        src_line(sc, "bKash: “bKash staff will not ask for your PIN” · verify only via the bKash helpline 16247 (bkash.com, security tips)", at(sid, "itself", default=5))
    elif sid == "X11":
        chapter(sc, "NEXT STEP (NOT BUILT YET)")
        boxes = [("on the phone", "small, fast model", 0.5), ("uncertain?", "send to the larger LLM", at(sid, "uncertain", default=8)), ("verdict", "scam or safe", at(sid, "larger", default=10))]
        for i, (a_, b2, t) in enumerate(boxes):
            card(sc, f"b{i}", a_, b2, (L + i * W * 0.31) if not P else L, H * (0.30 if not P else 0.20 + i * 0.14), W * (0.28 if not P else 0.90), t, AMB if i == 1 else INK, big=48)
        label(sc, "n", "a design idea for the next episode · not measured here", L, H * (0.62 if not P else 0.66), size=30, color=MUTE, t=at(sid, "built", default=12))
    elif sid == "S29":
        chapter(sc, "HONEST LIMITS")
        items = [("Small datasets", at(sid, "small", default=2)), ("Some labels are noisy", at(sid, "noisy", default=4)), ("A 3B model is heavy for a phone", at(sid, "heavy", default=6))]
        for i, (t_, t) in enumerate(items):
            label(sc, f"i{i}", "— " + t_, L, H * (0.26 if not P else 0.24) + i * 110 * u, size=60, weight=900, t=t, w=W * 0.88)
    elif sid == "S30":
        aura(sc, (RED, GRN))
        label(sc, "a", "Scam<span style='color:#F3F0E8'> or </span><span style='color:#3DDC97'>safe?</span>", L, H * (0.24 if not P else 0.24), size=130, color=RED, weight=900, t=at(sid, "scam", default=2))
        label(sc, "b2", "Comment your answer.", L, H * (0.24 if not P else 0.24) + 180 * u, size=64, weight=900, t=at(sid, "comment", default=3.5))
        label(sc, "c", "Send this to someone who needs it.", L, H * (0.24 if not P else 0.24) + 270 * u, size=56, color=AMB, weight=800, t=at(sid, "send", default=4.5), w=W * 0.88)
    return sc


# ---------------------------------------------------------------- code excerpt for the TF-IDF explanation (real code + real output)
b.CODES = {"X03": {"cell": 6, "title": "Model 1 · characters + words", "excerpt": True,
                   "code": ["tfidf = make_pipeline(make_union(",
                            "    TfidfVectorizer(analyzer=\"char_wb\", ngram_range=(2, 5),",
                            "                    min_df=2, sublinear_tf=True),",
                            "    TfidfVectorizer(analyzer=\"word\", ngram_range=(1, 2),",
                            "                    sublinear_tf=True)),",
                            "    LogisticRegression(C=8, max_iter=4000, class_weight=\"balanced\"))",
                            "tfidf.fit(TR[\"text\"].map(norm), TR[\"label\"])"],
                   "hl": [[1, 2, "character"], [3, 4, "words"], [5, 5, "logistic"]],
                   "out": ["              precision    recall  f1-score   support",
                           "      normal      0.984     0.978     0.981       498",
                           "       promo      0.979     0.953     0.966       342",
                           "       smish      0.963     0.984     0.974       562"],
                   "out_hl": "0.984     0.974", "out_t": "weight"}}


# ---------------------------------------------------------------- order, reels, outro, badge
ORDER = ["S01", "S02", "S03", "S04", "S05", "S06", "X01", "S07", "S08", "X02", "S09", "X03", "T5", "X04", "S10",
         "S11", "S12", "S13", "X05", "S14", "S15", "X06", "S16", "T1", "T2", "T3", "T4", "X07", "S17", "X08", "S18",
         "S19", "S20", "X09", "S21", "S22", "S23", "S24", "X10", "S25", "S26", "S27", "S28", "X11", "S29", "S30"]
REELS = {1: ("SCAM OR SAFE?", ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "T5", "X04", "S10"]),
         2: ("98% IN THE LAB", ["H2", "S11", "S13", "S14", "S16", "T1", "T2", "T3", "T4", "S17", "S18"]),
         3: ("BANGLA LLM vs GLOBAL LLM", ["H3", "S19", "S20", "S21", "S22", "S23", "S24", "S25", "S26", "S27", "S28", "S29", "S30"])}
b.S, b.ORDER, b.REELS = S3, ORDER, REELS


SHORTS = False   # YouTube Shorts end card instead of the Instagram/Facebook one


def outro3(rid, W, H, reel):
    sc = b.Scene(rid, W, H); u = sc.u; L = W * 0.07
    n = int(rid[1])
    if SHORTS and n == 3:
        label(sc, "nx", "FULL EPISODE ON YOUTUBE", L, H * 0.30, size=44, color=AMB, t=0.2, weight=800)
        label(sc, "hk", "▶ tap the related video above", L, H * 0.36, size=72, t=0.4, weight=900, w=W - 2 * L)
    elif n < 3:
        label(sc, "nx", f"ScamGuard · PART {n + 1}/3", L, H * 0.30, size=40, color=AMB, t=0.2, weight=800)
        label(sc, "hk", b.OUTROS[rid]["card"], L, H * 0.36, size=72, t=0.4, weight=900, w=W - 2 * L)
    else:
        label(sc, "nx", "FULL EPISODE ON YOUTUBE", L, H * 0.30, size=44, color=AMB, t=0.2, weight=800)
        label(sc, "hk", "▶ @csfunda.official", L, H * 0.36, size=84, t=0.4, weight=800)
    label(sc, "h1", "Follow CS Funda", L, H * 0.62, size=48, t=b.dur(rid) - 0.1, weight=800)
    label(sc, "h2", "Subscribe · YouTube @csfunda.official" if SHORTS else "IG @csfunda.official_  ·  YT @csfunda.official", L, H * 0.62 + 70 * u, size=34,
          color="#B8B5AE", t=b.dur(rid) - 0.1, mono=True, w=W - 2 * L)
    return sc


def badge3(out, W, H, reel, total):
    """No part counter on screen (it costs the first 3 s). A small brand chip appears after 3 s."""
    u = min(W, H) / 1080
    (out / "compositions/badge.html").write_text(f"""<template>
<style>#root{{position:absolute;inset:0;}}
#root #bd{{position:absolute;left:{W * 0.05}px;top:{H * 0.025}px;font-family:Inter,sans-serif;font-weight:800;color:#F3F0E8;font-size:{30 * u}px;
 padding:{8 * u}px {18 * u}px;border-radius:{12 * u}px;background:rgba(20,21,23,.8);opacity:0;}}#root #bd b{{color:{AMB}}}</style>
<div id="root" data-composition-id="badge" data-width="{W}" data-height="{H}"><div id="bd">CS Funda · <b>ScamGuard</b></div></div>
<script>const tl=gsap.timeline({{paused:true}});tl.fromTo("#bd",{{opacity:0}},{{opacity:1,duration:.5}},3.0);window.__timelines["badge"]=tl;</script></template>""")
    return (f'<div id="badge" data-composition-id="badge" data-composition-src="compositions/badge.html" data-start="0" data-duration="{total}" '
            f'data-track-index="6" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:6"></div>')


b.outro, b.part_badge = outro3, badge3


def add_extra_audio(out):
    idx = out / "index.html"; h = idx.read_text()
    starts = {s.upper(): float(a) for s, a in re.findall(r'compositions/([shxtabcd]\d+)\.html" data-start="([\d.]+)"', h)}
    lines = []
    for sid, evs in EXTRA.items():
        if sid not in starts:
            continue
        for k, (t, name, vol) in enumerate(evs):
            lines.append(f'<audio id="x-{sid.lower()}-{k}" class="clip" src="assets/sfx/{name}.mp3" data-start="{starts[sid] + t:.2f}" '
                         f'data-duration="{b.SFXLEN[name]}" data-track-index="{30 + k % 6}" data-volume="{vol}"></audio>')
    idx.write_text(h.replace("</div>\n<script>", "\n".join(lines) + "\n</div>\n<script>", 1))


if __name__ == "__main__":
    b.SFXLEN = {f.stem: round(float(__import__("subprocess").run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                capture_output=True, text=True).stdout), 2) for f in (HERE / "assets/sfx").glob("*.mp3")}
    if len(sys.argv) > 1 and sys.argv[1] == "full":     # the whole episode in 9:16, posted as one long Reel
        b.LEAD, b.TAIL = 0.1, 0.25
        out = VID / "full_vertical"
        shutil.rmtree(out, ignore_errors=True)
        b.project(out, 1080, 1920, ORDER + ["R3"], reel=3)
        add_extra_audio(out)
    elif len(sys.argv) > 1 and sys.argv[1] == "explain":   # technical Shorts: how each model works
        b.LEAD, b.TAIL = 0.1, 0.3
        b.HOLD.update({"A6": 1.0, "A7": 1.2, "B3": 0.6, "B5": 1.2, "C9": 1.4, "D3": 1.0, "D4": 1.6, "A5": 0.6})
        dst = VID / "explain"
        shutil.rmtree(dst, ignore_errors=True)
        EXPLAIN = {"1_tfidf": ["A1", "A2", "A3", "A4", "A5", "A6", "A7"], "2_embeddings": ["B1", "B2", "B3", "B4", "B5"],
                   "3_transformer": ["C1", "T1", "T2", "T3", "T4", "C9"], "4_llm": ["D1", "S19", "D2", "S20", "D3", "D4"]}
        for name, ids in EXPLAIN.items():
            EXTRA.clear()
            out = dst / name
            b.project(out, 1080, 1920, ids, reel=1)
            add_extra_audio(out)
    elif len(sys.argv) > 1 and sys.argv[1] in ("reels", "shorts"):
        SHORTS = sys.argv[1] == "shorts"
        b.LEAD, b.TAIL = 0.1, 0.25
        dst = VID / sys.argv[1]
        shutil.rmtree(dst, ignore_errors=True)
        for n, (_, ids) in REELS.items():
            EXTRA.clear()
            out = dst / f"part{n}"
            b.project(out, 1080, 1920, ids + [f"R{n}"], reel=n)
            add_extra_audio(out)
    elif False:
        b.LEAD, b.TAIL = 0.1, 0.25
        shutil.rmtree(VID / "reels", ignore_errors=True)
        for n, (_, ids) in REELS.items():
            EXTRA.clear()
            out = VID / f"reels/part{n}"
            b.project(out, 1080, 1920, ids + [f"R{n}"], reel=n)
            add_extra_audio(out)
    else:
        b.project(HERE, 1920, 1080, ORDER)
        add_extra_audio(HERE)
