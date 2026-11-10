"""Count the verses that name each shared figure, and write data/counts.json.

Sources (all downloaded from GitHub):
  Bible:          Theographic Bible Metadata (KJV, people disambiguated per verse)
                  https://github.com/robertrouse/theographic-bible-metadata
  Quran:          Quranic Arabic Corpus morphology, word-by-word lemmas
                  https://github.com/mustafa0x/quran-morphology
  Book of Mormon: https://github.com/bcbooks/scriptures-json

Run:  python3 scripts/count_names.py
The numbers it prints go into the REAL table in index.html.
"""
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "..", "data", "sources")
OUT = os.path.join(HERE, "..", "data", "counts.json")
RAW = "https://raw.githubusercontent.com/"
SOURCES = {
    "people.json": RAW + "robertrouse/theographic-bible-metadata/master/json/people.json",
    "verses.json": RAW + "robertrouse/theographic-bible-metadata/master/json/verses.json",
    "quran-morphology.txt": RAW + "mustafa0x/quran-morphology/master/quran-morphology.txt",
    "book-of-mormon.json": RAW + "bcbooks/scriptures-json/master/book-of-mormon.json",
}


def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print("downloading", name)
        urllib.request.urlretrieve(SOURCES[name], path)
    return path


# ---------------------------------------------------------------- Bible
# Theographic person records: one per distinct person, with the verses naming them.
BIBLE_PEOPLE = {
    "adam": ["adam_78"], "eve": ["eve_1231"], "cain": ["cain_533"], "noah": ["noah_2210"],
    "abraham": ["abraham_58"], "lot": ["lot_1830"], "ishmael": ["ishmael_630"], "isaac": ["isaac_616"],
    "joseph": ["joseph_1710"], "moses": ["moses_2108"], "aaron": ["aaron_1"],
    "pharaoh": ["pharaoh_%d" % i for i in range(2328, 2337)],
    "david": ["david_994"], "solomon": ["solomon_2762"], "job": ["job_1639"], "jonah": ["jonah_1689"],
    "elijah": ["elijah_1131"], "john": ["john_1676"], "mary": ["mary_1938"], "jesus": ["jesus_905"],
    "gabriel": ["gabriel_1261"], "satan": ["satan_2476"],
}


def count_bible():
    people = {p["fields"]["slug"]: p["fields"] for p in json.load(open(fetch("people.json")))}
    verses = json.load(open(fetch("verses.json")))
    book, text = {}, {}
    for v in verses:
        f = v["fields"]
        book[v["id"]] = int(f["verseID"][:2])          # 1-5 = Torah
        text[v["id"]] = f.get("verseText", "")
    split = lambda ids: [sum(1 for r in ids if book.get(r, 99) <= 5), sum(1 for r in ids if book.get(r, 0) > 5)]
    out = {}
    for fig, slugs in BIBLE_PEOPLE.items():
        ids = set()
        for s in slugs:
            ids |= set(people[s].get("verses", []))
        out[fig] = ids
    # Jacob is merged with "Israel" (the nation) in Theographic, so count the name itself.
    out["jacob"] = {r for r, t in text.items() if re.search(r"\bJacob\b", t)}
    # Satan also as "the devil", leaving out demon-possession stories.
    out["satan"] |= {r for r, t in text.items()
                     if re.search(r"\bthe devil\b", t, re.I) and not re.search(r"cast out|possessed|dumb|vexed", t, re.I)}
    res = {k: split(v) for k, v in out.items()}
    res["jesus"][0] = 0   # Theographic tags three Torah prophecies; Jesus is not named there.
    totals = split(set(book))
    return res, totals


# ---------------------------------------------------------------- Quran
QURAN_LEMMAS = {
    "adam": ["آدَم"], "noah": ["نُوح"], "abraham": ["إِبْرٰهِيم", "إِبْراهِيم"], "lot": ["لُوط"],
    "ishmael": ["إِسْمٰعِيل", "إِسْماعِيل"], "isaac": ["إِسْحٰق", "إِسْحاق"], "jacob": ["يَعْقُوب"],
    "joseph": ["يُوسُف"], "moses": ["مُوسَىٰ", "مُوسَى"], "aaron": ["هٰرُون", "هارُون"], "pharaoh": ["فِرْعَوْن"],
    "david": ["دَاوُۥد", "داوُد", "دَاوُد"], "solomon": ["سُلَيْمٰن", "سُلَيْمان"], "job": ["أَيُّوب"],
    "jonah": ["يُونُس"], "elijah": ["إِلْيَاس"], "john": ["يَحْيَىٰ", "يَحْيَى"], "mary": ["مَرْيَم"],
    "jesus": ["عِيسَى", "عِيسَىٰ", "مَسِيح"], "gabriel": ["جِبْرِيل"], "satan": ["إِبْلِيس", "شَيْطان"],
}
DIACRITICS = re.compile(r"[ً-ٰٟۖ-ۭـ]")


def norm(s):
    s = DIACRITICS.sub("", s)
    for a, b in (("ٱ", "ا"), ("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ء", ""), ("ۥ", "")):
        s = s.replace(a, b)
    return s


def count_quran():
    want = {norm(l): fig for fig, ls in QURAN_LEMMAS.items() for l in ls}
    hits = {fig: set() for fig in QURAN_LEMMAS}
    ayahs = set()
    for line in open(fetch("quran-morphology.txt"), encoding="utf8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        sura, aya = parts[0].split(":")[:2]
        ayahs.add((sura, aya))
        feats = parts[3].split("|")
        lem = next((f[4:] for f in feats if f.startswith("LEM:")), None)
        if not lem:
            continue
        fig = want.get(norm(lem))
        if fig == "satan" and "MP" in feats:      # shayatin, the plural, is not the figure
            continue
        if fig:
            hits[fig].add((sura, aya))
    res = {k: len(v) for k, v in hits.items()}
    res["jonah"] += 2   # "Dhu al-Nun" (21:87) and "the companion of the fish" (68:48)
    return res, len(ayahs)


# ---------------------------------------------------------------- Book of Mormon
# The Book of Mormon has its own Jacob, Joseph, Aaron, Noah and Ishmael, so those
# only count when the verse's wording points to the biblical figure.
BOM_RULES = {
    "adam": (r"\bAdam\b", None), "eve": (r"\bEve\b", None), "cain": (r"\bCain\b", None),
    "noah": (r"\bNoah\b", r"flood|ark|waters|days of Noah"),
    "abraham": (r"\bAbraham\b", None), "isaac": (r"\bIsaac\b", None),
    "jacob": (r"\bJacob\b", r"Abraham|Isaac|house of Jacob|God of Jacob|seed of Jacob|O Jacob|Jacob shall|remnant of Jacob|Israel"),
    "joseph": (r"\bJoseph\b", r"Egypt|seed of Joseph|Joseph who|tribe of Joseph|house of Joseph"),
    "moses": (r"\bMoses\b", None), "aaron": (r"\bAaron\b", r"Moses"),
    "pharaoh": (r"\bPharaoh\b", None), "david": (r"\bDavid\b", None), "solomon": (r"\bSolomon\b", None),
    "elijah": (r"\bElijah\b", None), "mary": (r"\bMary\b", None), "jesus": (r"\bJesus\b|\bChrist\b", None),
    "satan": (r"\bSatan\b|\bthe devil\b", None), "gabriel": (r"\bGabriel\b", None),
    "ishmael": (r"\bIshmael\b", r"Abraham|Hagar"), "john": (r"\bJohn\b", r"baptiz"),
}
# 2 Nephi 3: Lehi quotes Joseph of Egypt's prophecy; verses 1, 3 and 25 address Lehi's son Joseph.
BOM_JOSEPH_EXTRA = {"2 Nephi 3:%d" % n for n in (5, 6, 7, 14, 16, 22)}


def count_bom():
    data = json.load(open(fetch("book-of-mormon.json")))
    verses = [(v["reference"], v["text"]) for b in data["books"] for c in b["chapters"] for v in c["verses"]]
    res = {}
    for fig, (pat, ctx) in BOM_RULES.items():
        flags = re.I if fig == "satan" else 0
        refs = {r for r, t in verses if re.search(pat, t, flags) and (ctx is None or re.search(ctx, t))}
        if fig == "joseph":
            refs |= BOM_JOSEPH_EXTRA
        res[fig] = len(refs)
    return res, len(verses)


if __name__ == "__main__":
    bible, (torah_total, bible_total) = count_bible()
    quran, quran_total = count_quran()
    bom, bom_total = count_bom()
    figures = sorted(set(bible) | set(quran) | set(bom))
    counts = {f: {"torah": bible.get(f, [0, 0])[0], "bible": bible.get(f, [0, 0])[1],
                  "quran": quran.get(f, 0), "mormon": bom.get(f, 0)} for f in figures}
    out = {"unit": "verses that name the figure",
           "totals": {"torah": torah_total, "bible": bible_total, "quran": quran_total, "mormon": bom_total},
           "counts": counts}
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out["totals"]))
    for f in figures:
        print(f"{f:9s}", counts[f])
