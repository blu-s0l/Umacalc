"""Rebuild data.js from GameTora's public JSON.

Usage:  py -I tools/build_data.py <download-dir>

Downloads the current files into <download-dir> (kept apart from this script,
since it is untrusted input) and writes data.js next to index.html. Run it when
new trainees or cards reach Global; the app filters on release_en at runtime,
so nothing else needs to change.
"""
import json, os, re, sys, urllib.request, datetime

BASE = "https://gametora.com/data"
UA = {"User-Agent": "Mozilla/5.0 (Umacalc data build)"}
# Book / Textbook of Hints, Rare Book / Rare Textbook of Hints: used for potential-skill hint levels.
HINT_BOOKS = [160, 161, 162, 163]
FILES = ["character-cards", "characters", "support-cards", "support_effects", "skills",
         "db-files/support_card_level", "db-files/card_talent_upgrade",
         "en/db-files/card_talent_upgrade", "items", "gacha/support_banners",
         "gacha/char_banners", "factors"]


TAGS = (("distance_type", 1, 4), ("running_style", 1, 4), ("ground_type", 1, 2))


def skill_tags(k):
    """What a skill is tied to, read from its activation conditions: [distances, styles, grounds].
    distance_type 1-4 = Sprint/Mile/Medium/Long, running_style 1-4 = Front/Pace/Late/End,
    ground_type 1-2 = Turf/Dirt. An empty list means "any". Only equality tests count; a skill
    with several condition groups is tied to the union of what its groups name."""
    text = " ".join(g.get("precondition", "") + " " + g.get("condition", "") for g in k.get("condition_groups", []))
    return [sorted({int(v) for v in re.findall(name + r"==(\d)", text) if lo <= int(v) <= hi}) for name, lo, hi in TAGS]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def main(dl):
    os.makedirs(dl, exist_ok=True)
    man = json.loads(get(BASE + "/manifests/umamusume.json"))
    raw = {}
    for f in FILES:
        path = os.path.join(dl, f.replace("/", "_") + ".json")
        body = get(f"{BASE}/umamusume/{f}.{man[f]}.json")
        with open(path, "wb") as fh:
            fh.write(body)
        raw[f] = json.loads(body)

    chars = {c["char_id"]: c["name_en"] for c in raw["characters"]}

    # Stats by star: base_stats is at the card's own starting rarity.
    umas = []
    for c in raw["character-cards"]:
        st = [None] * 6
        st[c["rarity"]] = c["base_stats"]
        for k, i in (("two_star_stats", 2), ("three_star_stats", 3),
                     ("four_star_stats", 4), ("five_star_stats", 5)):
            if c.get(k):
                st[i] = c[k]
        umas.append({
            "id": c["card_id"], "c": c["char_id"], "n": c["name_en"], "url": c.get("url_name"),
            "t": (c.get("title_en_gl") or "[" + c.get("title", "") + "]").strip("[]"),
            "r": c["rarity"], "a": "".join(c["aptitude"]), "s": st, "g": c["stat_bonus"],
            "en": c.get("release_en"), "jp": c.get("release"), "tg": c["talent_group"],
            "u": (c.get("skills_unique") or [None])[0],
            # Potential skills, unlocked at P2..P5. Global's list where it differs from JP's.
            "aw": (c.get("skills_awakening_en") or c.get("skills_awakening") or [])[:4],
            # Innate skills: always available, and their hint levels can be raised too.
            "in": c.get("skills_innate") or [],
        })

    sups = []
    for s in raw["support-cards"]:
        ef = {e[0]: e[1:] for e in s["effects"]}
        u = s.get("unique")
        b = []
        sups.append({
            "id": s["support_id"], "c": s["char_id"], "n": s["char_name"], "url": s.get("url_name"),
            "t": (s.get("title_en") or s.get("title_ja") or "").strip("[]"),
            "r": s["rarity"], "ty": s["type"], "en": s.get("release_en"), "jp": s.get("release"),
            "ob": s.get("obtained"), "ef": ef,
            "u": {"lv": u["level"], "ef": [[x["type"], x["value"]] for x in u.get("effects", [])]} if u else None,
            "ud": s.get("unique_desc"),
            "h": s["hints"].get("hint_skills", []),
            "e": s.get("event_skills_en") or s.get("event_skills", []),
            "b": b,
        })
    byid = {s["id"]: s for s in sups}
    for row in raw["gacha/support_banners"]:
        s = byid.get(row["support_id"])
        if s:
            s["b"] = sorted([x["start"], 1 if x.get("is_estimated") else 0]
                            for x in row["banners"].get("en", []))

    uma_ban, uma_ban_jp = {}, {}
    for row in raw["gacha/char_banners"]:
        cid = row.get("card_id") or row.get("char_card_id")
        if cid:
            uma_ban[cid] = sorted([x["start"], 1 if x.get("is_estimated") else 0]
                                  for x in row["banners"].get("en", []))
            uma_ban_jp[cid] = sorted(x["start"] for x in row["banners"].get("ja", []))
    for u in umas:
        u["b"] = uma_ban.get(u["id"], [])
        u["bj"] = uma_ban_jp.get(u["id"], [])

    used = set()
    for s in sups:
        used.update(s["h"]); used.update(s["e"])
    for u in umas:
        if u["u"]:
            used.add(u["u"])
        used.update(u["aw"])
        used.update(u["in"])
    skills = {}
    for k in raw["skills"]:
        if k["id"] in used:
            skills[k["id"]] = [k.get("name_en") or k.get("enname") or k.get("jpname"), k.get("rarity", 1)] + skill_tags(k)

    # White sparks that can actually be inherited: GameTora's factor list, not every skill (a
    # trainee's own evolved skills, e.g. "Best in Japan", have no spark; nor do gold skills: the
    # spark is the white base, Focus for Concentration). A skill spark names the skill it grants
    # (effect type 41); one with no Global name takes that skill's name when it, or its gold
    # version (id - 1), is in the data above. Race sparks drop story-only races; scenarios keep
    # named ones.
    fac = raw["factors"]
    skname = {k["id"]: k.get("name_en") or k.get("enname") for k in raw["skills"]}
    def fname(x):
        return x.get("name_en_gl") or x.get("name_en")
    wsk, base = [], {}
    rar = {k["id"]: k.get("rarity", 1) for k in raw["skills"]}
    for x in fac["skill"]:
        sid = next((e["value_1"][0] for e in x.get("effects", []) if e.get("type") == 41), None)
        n = x.get("name_en_gl") or (skname.get(sid) if sid in used or (sid and sid - 1 in used) else None)
        if n:
            wsk.append(n.strip())
            # gold skill id -> the white spark that hints its base (Concentration -> Focus)
            if sid and sid - 1 in used and rar.get(sid - 1) == 2:
                base[sid - 1] = n.strip()
    wrace = [fname(x).strip() for x in fac["race"]
             if fname(x) and fname(x).isascii() and "Story Race" not in fname(x)]
    wscen = [fname(x).strip() for x in fac["scenario"] if fname(x)]
    wf = {"skill": sorted(set(wsk)), "race": wrace, "scen": wscen, "base": base}

    effects = {e["id"]: e.get("name_en") or e.get("name_en_eon") for e in raw["support_effects"]}

    exp = {1: {}, 2: {}, 3: {}}
    for l in raw["db-files/support_card_level"]:
        exp[l["rarity"]][l["level"]] = l["total_exp"]

    # Global costs where Global has published them; JP otherwise.
    talent, items_used = {}, set()
    for src in ("db-files/card_talent_upgrade", "en/db-files/card_talent_upgrade"):
        per = {}
        for t in raw[src]:
            cost = [[t[f"item_id_{i}"], t[f"item_num_{i}"]] for i in range(1, 7) if t[f"item_id_{i}"]]
            per.setdefault(t["talent_group_id"], {})[t["talent_level"]] = cost
        for g, lv in per.items():
            talent[g] = [lv.get(i, []) for i in range(2, 6)]
    for g in talent.values():
        for cost in g:
            items_used.update(i for i, _ in cost)
    items_used.update(HINT_BOOKS)
    items = {i["id"]: i.get("name_en_gl") if i.get("name_en_gl") not in (None, "Unused") else i.get("name_en")
             for i in raw["items"] if i["id"] in items_used}

    out = {"built": datetime.date.today().isoformat(), "chars": chars, "umas": umas, "sups": sups,
           "skills": skills, "effects": effects, "exp": exp, "talent": talent, "items": items, "wf": wf}
    js = "window.UMA_DATA=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.js")
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(js)
    print(f"data.js: {len(umas)} trainees, {len(sups)} supports, {len(skills)} skills, {len(js)//1024} KB")
    print(f"white sparks: {len(wf['skill'])} skills, {len(wf['race'])} races, {len(wf['scen'])} scenarios")
    # index.html loads data.js?v=<built>, so a browser never pairs a new page with a cached old data.js.
    page = os.path.join(os.path.dirname(dest), "index.html")
    with open(page, encoding="utf-8", newline="") as fh:
        html = fh.read()
    html2, n = re.subn(r'src="data\.js(\?v=[^"]*)?"', f'src="data.js?v={out["built"]}"', html)
    if n == 1 and html2 != html:
        with open(page, "w", encoding="utf-8", newline="") as fh:
            fh.write(html2)
    print(f"index.html data.js tag: v={out['built']}" + ("" if n == 1 else " (tag not found!)"))
    fetch_portraits(umas)


# 128px outfit portraits, one per trainee card, kept in img/umas/<card_id>.png.
# Existing files are skipped, so a refresh only fetches new releases.
IMG = BASE.replace("/data", "/images") + "/umamusume/characters/thumb/chara_stand_{c}_{id}.png"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fetch_portraits(umas):
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img", "umas")
    os.makedirs(dest, exist_ok=True)
    got = missing = 0
    for u in umas:
        path = os.path.join(dest, f"{u['id']}.png")
        if os.path.exists(path):
            continue
        try:
            body = get(IMG.format(c=u["c"], id=u["id"]))
        except Exception:
            missing += 1
            continue
        if not body.startswith(PNG_MAGIC):   # an HTML error page, not an image
            missing += 1
            continue
        with open(path, "wb") as fh:
            fh.write(body)
        got += 1
    print(f"portraits: {got} fetched, {missing} unavailable")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
