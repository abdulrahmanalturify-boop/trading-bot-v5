"""
newspics.py - A photo for every headline.

1) The story's own photo: the picture its article page shows when the link is shared (og:image / twitter:image). The news bot
   looks it up in the background for every story whose feed sent no picture (Google News links are first turned into the
   publisher's own link), so the pages never wait for it.
2) When the article has none (or the outlet blocks readers): a free photo of the story's topic from Wikimedia Commons
   (public domain or Creative Commons; the photographer and the licence show on hover). The photos of each topic are
   looked up once a week, kept on disk, and the same story always gets the same photo.
3) If a photo cannot load in the browser, the next one takes its place (theme.FX_JS), and last the topic's coloured card.
"""
import hashlib
import html as _html
import json
import os
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from urllib.parse import quote, urljoin, urlparse

import requests

# commons asks every tool to say who it is
UA_WIKI = {"User-Agent": "TURAPro/1.0 (https://abdulrahman.streamlit.app; market-news pictures)"}
BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}

# the searches behind each topic's photos: (search, what the photo's file name or its categories must say). A search inside one
# Commons category is precise on its own (None); a free-text search must be confirmed, or "semiconductor wafer" brings back
# a plate of wafer biscuits. "street" is the general market picture.
def _cat(name):
    return (f'incategory:"{name}"', None)


TOPIC_Q = {
    "fed": [_cat("Marriner S. Eccles Federal Reserve Board Building"), ("Eccles Building Federal Reserve", r"eccles|federal reserve"),
            ("Federal Reserve Bank building", r"federal reserve")],
    "inflation": [("supermarket aisle", r"supermarket|grocer|aisle|shelves|store"), ("grocery store shelves", r"grocer|supermarket|shelves|store")],
    "jobs": [("construction workers building site", r"worker|construction|builder"), ("factory assembly line", r"assembly|factory|production|plant")],
    "economy": [("Manhattan skyline", r"skyline"), ("shoppers shopping mall", r"shopping|mall|shoppers")],
    "bonds": [_cat("Treasury Building (Washington, D.C.)"), ("Treasury Building Washington", r"treasury"),
              ("United States Department of the Treasury building", r"treasury")],
    "trade": [_cat("Container ships"), ("container ship port", r"container"), ("container terminal cranes", r"container|terminal|port|crane")],
    "geo": [_cat("United Nations Headquarters"), ("United Nations headquarters flags", r"united nations|\bun\b|flags"),
            ("oil tanker at sea", r"tanker")],
    "policy": [_cat("United States Capitol"), ("United States Capitol", r"capitol"), ("White House Washington", r"white house")],
    "earnings": [("stock market quotes screen", r"stock|quote|ticker|exchange|trading|market"),
                 ("corporate headquarters skyscraper", r"headquarters|skyscraper|tower|office|building")],
    "guidance": [("stock exchange display board", r"stock|board|display|ticker|exchange"), ("trading screens", r"trading|screen|monitor|terminal")],
    "analyst": [("stock market display board", r"stock|board|display|ticker|exchange"), ("trading screens", r"trading|screen|monitor|terminal")],
    "payout": [("stack of coins", r"coins?"), ("United States dollar banknotes", r"dollar|banknote|bills?|currency")],
    "mna": [("office towers skyscrapers", r"office|tower|skyscraper|building"), ("conference room table", r"conference|meeting|board ?room")],
    "ipo": [_cat("New York Stock Exchange Building"), ("New York Stock Exchange facade", r"stock exchange|nyse"),
            ("Nasdaq MarketSite Times Square", r"nasdaq")],
    "legal": [_cat("Supreme Court of the United States Building"), ("Supreme Court of the United States building", r"supreme court|court"),
              ("courthouse columns", r"court")],
    "health": [("laboratory pipette", r"laborator\w*|pipette|lab\b|science"), ("pills tablets medicine", r"pills?|tablets?|capsules?|medic\w*|drug|pharma\w*")],
    "distress": [("store closing sign", r"clos\w+|store|sign|shop"), ("abandoned shopping mall", r"mall|abandon\w*|dead|vacant|empty")],
    "layoffs": [("empty office", r"office|desk|cubicle|workplace"), ("office cubicles", r"office|cubicle|desk")],
    "product": [("smartphones", r"smartphone|phone|iphone|android|mobile"), ("consumer electronics store", r"electronic|store|shop|retail")],
    "ai": [_cat("Silicon wafers"), _cat("Data centers"),
           ("semiconductor wafer", r"silicon|semiconductor|integrated circuit|microchip|microprocessor|photolithograph\w*|\bdie\b|cleanroom|\bfab\b"),
           ("data center servers", r"servers?|data ?cent(?:er|re)|rack|server room"),
           ("integrated circuit chip", r"integrated circuit|microchip|microprocessor|processor|\bcpu\b|\bgpu\b|semiconductor|silicon")],
    "crypto": [("bitcoin coins", r"bitcoin|crypto"), ("cryptocurrency coins", r"crypto|bitcoin|coin")],
    "oil": [_cat("Pumpjacks"), ("pumpjack oil field", r"pump ?jack|oil|well"), ("oil refinery", r"refiner\w*|oil|petro\w*")],
    "metals": [("gold bars", r"gold"), ("gold bullion", r"gold|bullion")],
    "fx": [("euro dollar banknotes", r"euro|dollar|banknotes?|currenc\w*"), ("currency exchange office", r"currency|exchange|bureau|change")],
    "move": [_cat("New York Stock Exchange trading floor"), ("New York Stock Exchange trading floor", r"stock exchange|nyse|trading floor|trader"),
             ("stock ticker board", r"ticker|stock|board")],
    "street": [_cat("Wall Street"), ("Wall Street New York", r"wall street|stock exchange|nyse|financial district"),
               ("New York Stock Exchange", r"stock exchange|nyse|wall street")],
}
# photos picked by hand for each topic from the contact sheet the site check draws (scripts/site_check.py, pics_*.jpg): they come
# first, and the searches only add a couple more (a topic with few picks gets more from its searches)
PINS = {
    "fed": ["Eccles Building (26088200676).jpg", "Marriner S. Eccles Federal Reserve Board Building.jpg",
            "Washington D.C. - Federal Reserve 0001-0003 HDR.jpg", "Eccles Building 2013.JPG", "Eccles Building - north side.JPG",
            "Federal reserve building 1160435.jpg"],
    "inflation": ["99 Ranch Market San Jose June 2011 001.jpg", "Aisle in L Intermarche supermarket in Quebec City.jpg",
                  "Grocery Store Aisle, vermont.jpg", "Langenstein's Supermarket Uptown New Orleans, Center aisle, March 2021 02.jpg",
                  "Langenstein's Supermarket Uptown New Orleans, Center aisle, March 2021 01.jpg", "Rimi supermarket at Kaunas Mega mall, 2025 aisle.jpg"],
    "jobs": ["Construction Photography of Workers on Site by Construction Photographer Daniel Mekis.jpg",
             "Construction worker on a building site in Tulaghi, Central Province. (10690383443).jpg",
             "Male labour working at Building construction site.jpg", "Building construction Moira Close Broadwater Farm Haringey 2025 01.jpg"],
    "economy": ["Lower Manhattan skyline from New York Harbor, New York.jpg",
                "NYC – Financial District - Lower Manhattan in the early morning - panoramio.jpg", "Brooklyn Bridge At Sunset (21745657).jpeg",
                "Lower Manhattan from Jersey City September 2020 panorama.jpg",
                "Brooklyn Bridge and the Lower Manhattan skyline from Pebble Beach, New York.jpg",
                "Manhattan skyline from Upper New York Bay, 20231001 1043 0903.jpg"],
    "bonds": ["Us-treasury-building.jpg", "United States Treasury Washington DC 5383075936 o.jpg", "United States Treasury Building.JPG",
              "U.S. Treasury Building and Albert Gallatin Statue.jpg", "Washington (31119786125).jpg"],
    "trade": ["Aerial photograph of a cargo ship.jpg", "Peel Ports Dublin. Marine Terminals Ltd MTL Dublin 5148.jpg", "Le Verdon Container ships.jpg",
              "Taking Back The Empties.jpg", "Río Saigón, Ciudad Ho Chi Minh, Vietnam, 2013-08-14, DD 11.JPG",
              "Maersk Sealand Vessel Hull Hold Hatch Crane Container Brazil.jpg", "Containership in gulf of Finland.jpg",
              "Container Ship pulling into Honolulu (5318008892).jpg"],
    "geo": ["Flags at the United Nations headquarters 2.jpg", "United Nations Headquarters (5013024600).jpg", "United Nations Flags - cropped.jpg",
            "Flags at United Nations.jpg", "United Nations HQ.jpg", "The United Nations Secretariat Building (cropped).jpg"],
    "policy": ["View of the U.S. Capitol's East Front Before Dawn (51749291999).jpg", "The Capitol Building 5 (27697846732).jpg",
               "United States Capitol Washington 01.jpg", "United States Capitol 13.jpg", "United States Capitol Washington 02.jpg", "US CAPITOL.jpg"],
    "earnings": ["The headquarters of DNP.jpg", "Kobe harborland08s3200.jpg", "Willis Tower, Chicago, Illinois (9179399743).jpg",
                 "Bonn, Post-Tower -- 2017 -- 2125.jpg", "Highlight Towers Munich, February 2017 -01.jpg", "London, Canary Wharf -- 2016 -- 4751.jpg"],
    "guidance": ["Electronic stock board in Yaesu, Tokyo 2007.jpg",
                 "Shinko Securities's electronic stock board nearby Yaesu side of Tokyo Station in March 2009.jpg",
                 "Trading apps on an iPhone screen.jpg", "Willis Tower, Chicago, Illinois (9179399743).jpg", "The headquarters of DNP.jpg"],
    "analyst": ["Electronic stock board in Yaesu, Tokyo 2007.jpg",
                "Shinko Securities's electronic stock board nearby Yaesu side of Tokyo Station in March 2009.jpg",
                "Trading apps on an iPhone screen.jpg",
                "Tech equipment on display at an industrial trade show with screens showing data and a busy environment.jpg"],
    "payout": ["Stack of pennies.jpg", "Stacks of Canadian Coins (16269886909).jpg", "A stack of coins from the hoard (7460123178).jpg",
               "Toy Plane Between Stack Of Coins (45418154314).jpg", "Stacks of Coins.jpg"],
    "mna": ["Highlight Towers Munich, February 2017 -01.jpg", "Seattle (WA, USA), Hochhäuser -- 2022 -- 1494.jpg",
            "London, Canary Wharf -- 2016 -- 4751.jpg", "Bonn, Post-Tower -- 2017 -- 2125.jpg", "London MMB O9 Cabot Square.jpg"],
    "ipo": ["New York City Stock Exchange NYSE 01.jpg", "New York Stock Exchange 02010.JPG", "Nova iorque (17397145305).jpg",
            "Is there a new way on Wall Street? (8235905065).jpg", "NYSE Institute-Photo-MW-20240215-0069.jpg",
            "New York Stock Exchange (6214361043).jpg", "New York Stock Exchange - Wall Street, New York, NY, USA - August 19, 2015 - panoramio.jpg"],
    "legal": ["US Supreme Court.JPG", "Panorama of United States Supreme Court Building at Dusk.jpg", "US Supreme Court - corrected.jpg",
              "Exterior of Supreme Court Building 20240601.jpg", "Supreme Court of the United States (Washington D.C.).jpg",
              "The United States Supreme Court Building.jpg"],
    "health": ["Tablets pills medicine medical waste.jpg", "Gfp-medicine-container-and-medicine-tablet.jpg", "Sandoz.Methylprednisolone.4mg.jpg",
               "Pipette gallery.jpg", "Disposable Pipette Tips in Laboratory Tip Boxes.jpg", "Laboratory pipettes.jpg"],
    "distress": ["Boswells of Oxford - store closing signs 2.jpg", "Store Closing Flags.jpg", "Hudson's Bay - Store closing sale - 20250524 - 05.jpg",
                 "Hudson's Bay - Store closing sale - 20250524 - 01.jpg", "Store Closing etc. (4079485053).jpg"],
    "layoffs": ["Empty office.jpg", "Empty office in a coworking building.jpg",
                "Empty office building, off Kirkstall Road, Leeds - geograph.org.uk - 4627332.jpg", "Empty Office Real Estate (22789285225).jpg"],
    "product": ["Xiaomi Redmi Note 10 Pro.jpg", "Huawei P10.jpg", "Smartphone display screen.jpg", "5 different Smartphones.jpg",
                "Smartphones - MediaMarkt - HUMA Einkaufspark 2025 - 07.jpg", "Girl listening to music with a smartphone.jpg"],
    "ai": ["Silicon Wafer 20190210.jpg", "IMaGe 31116R+ HDR – Silicon Wafer 20120926.jpg", "IMaGe 31000R – Silicon Wafer 20120926.jpg",
           "A semiconductor wafer being removed from processing equipment.jpg", "IMaGe 30961R+ HDR – Silicon Wafer 20120926.jpg",
           "5C2A5961R – Silicon Wafer 20200519.jpg"],
    "crypto": ["Bitcoin BTC golden coin with the symbol.jpg", "Bitcoin on Laptop Keyboard.jpg", "Bitcoin \"challenge coin\".jpg",
               "Close-up of a Bitcoin physical coin in a womans hand and a laptop on her lap.jpg", "Holding Bitcoin cryptocurrency coin.jpg",
               "Coinbank BitCoin (38461155220).jpg"],
    "oil": ["Pumpjacks.JPG", "Sunniland Oil Field preserved pumpjack.jpg", "Pumpjack, Glenn Pool oil field OK.jpg", "Brunei Pumpjack-2.jpg",
            "Pumpjack in Seria.jpg", "Signal Hill pumpjack, 2011.jpg"],
    "metals": ["Gold ingot and bar of Banque de France.jpg", "Gold Ingots on white background.jpg",
               "Bullion Gold bar at Swiss Money Museum (Ank Kumar, Infosys).jpg", "Gold bar of Banque de France.jpg", "Gold bullion bars.jpg",
               "Gold bullion 1.jpg"],
    "fx": ["One stands out 002 2025 01 01.jpg", "Currencies on White Background.jpg",
           "International Currency Exchange (ICE) office at Toronto Pearson (YYZ) Terminal 3.jpg"],
    "move": ["Gaming-Wall-Street BTS Prodigium-266.jpg", "NYSE Advanced Trading Floor.jpg", "Peter Tuchman in NYSE, 2021.jpg",
             "NYSE Institute-Photo-MW-20240215-0051.jpg"],
    "street": ["New York Stock Exchange August 2017 02.jpg", "NYSE - panoramio - Bekim D..jpg", "New York City Stock Exchange NYSE 01.jpg",
               "New York Stock Exchange 02010.JPG", "Nova iorque (17397145305).jpg", "Is there a new way on Wall Street? (8235905065).jpg",
               "New York City (New York, USA), Wall Street -- 2012 -- 6614.jpg", "Wall Street - New York Stock Exchange.jpg",
               "Gaming-Wall-Street BTS Prodigium-266.jpg"],
}
_MUST = {}            # search -> compiled "must say"
# never a painting, a drawing, a diagram or a map, an old black-and-white print or a museum's catalogue photo
_NOT_PHOTO = re.compile(r"\b(paintings?|drawings?|diagrams?|charts?|graphs?|maps?|illustrations?|engravings?|lithographs?|artworks?|"
                        r"infographics?|statistics|black and white|monochrome|b&w|sculptures?|statues?|reliefs?|mascarons?|"
                        r"museum objects?|dpla)\b|\(bw\)|\(am [\d.\-]+|\b1[5-9][0-8]\d\b", re.I)
# never a dish, a snack or a drink (an inflation story keeps its supermarket shelves)
_OFF = re.compile(r"\b(foods?|cuisine|cookies?|biscuits?|waffles?|wafers? \(food\)|confection\w*|snacks?|desserts?|cakes?|pastr(?:y|ies)|"
                  r"bakery|bakeries|candy|candies|chocolates?|potato chips|crisps|dish(?:es)?|meals?|recipes?|restaurants?|drinks?|"
                  r"beverages?|cooking|kitchen|fruit|vegetables?|animals?|dogs?|cats?|birds?|flowers?)\b", re.I)
_OFF_FREE = {"inflation"}                 # the topics whose photos may show food
# files that slipped through once and are never shown again (by their Commons file name)
_NEVER = {"Triton face on US Botanic Garden Conservatory (8371514546).jpg", "Flickr - USCapitol - National Garden.jpg",
          "Guy on a scooter (44759596865).jpg", "FRED-US Dollar.jpg", "Riding crop.jpeg", "Washington Times bag.jpg",
          "Alliances of container ship companies.jpg", "Tiefgänge einlaufend.jpg", "17-jewel-lady-watch-inside-view-01.jpg",
          "1969 AMC SC-Rambler at Summit display in Georgia 3of7.jpg", "2017-09-01 22-49-53 laiterie-belfort.jpg"}
GENERAL = "street"
WEEK = 7 * 86400
_DISK = os.path.join(tempfile.gettempdir(), "alturaifi_newspics_v3.json")     # v2: the confirmed searches
_POOLS = {}                 # topic -> {"at": time, "pics": [{"u": 500px url, "b": 960px url, "c": credit}]}
_LOCK = threading.Lock()
_FILLING = threading.Lock()
_STATE = {"tried": 0.0, "loaded": False, "rest": 0.0}

# never shown, whatever the search brings back
_BAD_WORDS = re.compile(r"\b(nude|naked|nsfw|sex\w*|erotic|porn\w*|lingerie|bikini|corpse|dead|death|blood\w*|gore|injur\w*|war|weapons?|guns?|"
                        r"rifles?|soldiers?|army|military|protest\w*|riot\w*|fire|burn\w*|accident|crash\w*|child\w*|kids?|bab(?:y|ies)|"
                        r"portrait|selfie|logo|diagram|chart|graph|map|svg|icon|flag of)\b", re.I)
_TAGS = re.compile(r"<[^>]+>")
_PX = re.compile(r"/(\d+)px-")             # the width in a thumbnail link


# ---------------------------------------------------------------- topic photos (Wikimedia Commons)
def _credit(meta):
    def v(k):
        return _html.unescape(_TAGS.sub("", str((meta.get(k) or {}).get("value") or ""))).strip()
    who = re.sub(r"\s+", " ", v("Artist"))[:70]
    lic = v("LicenseShortName")
    return " · ".join(x for x in (f"Photo: {who}" if who else "Photo", lic, "Wikimedia Commons") if x)


def _free(meta):
    lic = str((meta.get("LicenseShortName") or {}).get("value") or "").lower()
    return lic.startswith(("public domain", "pd", "cc0", "cc by", "cc-by"))


def _search(q, quality=True, n=40, must=None, food_ok=False):
    """Landscape JPEG photos with a free licence for one search (the photos rated 'quality images' first). must: a pattern the
    file's name or one of its categories has to match (a free-text search is confirmed by it); never a photo of food unless
    food_ok."""
    params = {"action": "query", "format": "json", "formatversion": "2", "generator": "search", "gsrnamespace": "6",
              "gsrsearch": f"{q} filetype:bitmap" + (" incategory:Quality_images" if quality else ""), "gsrlimit": str(n),
              "prop": "imageinfo|categories", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "960", "cllimit": "max",
              "clshow": "!hidden", "iiextmetadatafilter": "LicenseShortName|Artist", "maxlag": "5"}
    if must and q not in _MUST:
        _MUST[q] = re.compile(must, re.I)
    r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=UA_WIKI, timeout=12)
    r.raise_for_status()
    pages = (r.json().get("query") or {}).get("pages") or []
    if isinstance(pages, dict):                      # the older answer shape
        pages = list(pages.values())
    out = []
    for p in sorted(pages, key=lambda p: p.get("index", 999)):
        ii = (p.get("imageinfo") or [{}])[0]
        title, meta = str(p.get("title") or ""), ii.get("extmetadata") or {}
        w, h, big = ii.get("width") or 0, ii.get("height") or 0, str(ii.get("thumburl") or "")
        px = _PX.search(big)
        if ii.get("mime") != "image/jpeg" or not big.startswith("https://") or not px:
            continue
        if w < 1200 or not (1.2 * h <= w <= 3.2 * h) or _BAD_WORDS.search(title) or not _free(meta):
            continue
        if title.split(":", 1)[-1] in _NEVER:
            continue
        cats = " ".join(str(c.get("title") or "").split(":", 1)[-1] for c in (p.get("categories") or []))
        said = title.split(":", 1)[-1].rsplit(".", 1)[0].replace("_", " ") + " | " + cats
        if not food_ok and _OFF.search(said):
            continue
        if _NOT_PHOTO.search(said):
            continue
        if must and not _MUST[q].search(said):
            continue
        small = big[:px.start()] + "/500px-" + big[px.end():] if int(px.group(1)) > 500 else big
        out.append({"u": small, "b": big, "c": _credit(meta), "f": title.split(":", 1)[-1][:200]})
    return out


def _pinned(names):
    """The hand-picked photos (PINS) by their Commons file names, in that order (the ones Commons no longer has are skipped)."""
    names = [n for n in names if n][:50]
    if not names:
        return []
    params = {"action": "query", "format": "json", "formatversion": "2", "titles": "|".join("File:" + n for n in names),
              "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "960",
              "iiextmetadatafilter": "LicenseShortName|Artist", "maxlag": "5"}
    r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=UA_WIKI, timeout=12)
    r.raise_for_status()
    js = r.json().get("query") or {}
    norm = {x.get("from"): x.get("to") for x in js.get("normalized") or []}
    pages = js.get("pages") or []
    if isinstance(pages, dict):
        pages = list(pages.values())
    by = {str(p.get("title") or ""): p for p in pages}
    out = []
    for n in names:
        t = "File:" + n
        p = by.get(norm.get(t, t)) or by.get(t)
        ii = ((p or {}).get("imageinfo") or [{}])[0]
        big = str(ii.get("thumburl") or "")
        px = _PX.search(big)
        if not p or p.get("missing") or not big.startswith("https://") or not px or not _free(ii.get("extmetadata") or {}):
            continue
        small = big[:px.start()] + "/500px-" + big[px.end():] if int(px.group(1)) > 500 else big
        out.append({"u": small, "b": big, "c": _credit(ii.get("extmetadata") or {}), "f": n})
    return out


def _series(name):
    """Photos of one shoot share a name but its number ("Fossil Creek Planning - Public Meeting (33272908506)"): one of each."""
    return re.sub(r"[\W\d_]+", " ", str(name or "")).strip().lower()[:28]


def _load():
    if _STATE["loaded"]:
        return
    _STATE["loaded"] = True
    try:
        with open(_DISK, encoding="utf-8") as f:
            saved = json.load(f)
        with _LOCK:
            for k, v in saved.items():
                if k in TOPIC_Q and isinstance(v, dict) and v.get("pics"):
                    _POOLS.setdefault(k, v)
    except Exception:
        pass


def _save():
    try:
        with _LOCK:
            snap = dict(_POOLS)
        tmp = _DISK + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snap, f)
        os.replace(tmp, _DISK)
    except Exception:
        pass


def fill(budget=90):
    """Looks up the photos of every topic that has none, or whose photos are a week old (the news bot calls this)."""
    _load()
    if time.time() < _STATE["rest"] or not _FILLING.acquire(blocking=False):
        return
    try:
        end = time.time() + budget
        now = time.time()
        todo = [t for t in TOPIC_Q if now - (_POOLS.get(t) or {}).get("at", 0) > WEEK or not (_POOLS.get(t) or {}).get("pics")]
        todo.sort(key=lambda t: t != GENERAL)          # the general picture first: it stands in for every other topic
        changed = False
        for t in todo:
            if time.time() > end:
                break
            pics, seen, shoots = [], set(), set()
            try:
                pics = _pinned(PINS.get(t, []))
            except Exception:
                pics = []
            for p in pics:
                seen.add(p["b"])
            want = 12 if len(pics) < 3 else len(pics)         # a topic with hand-picked photos shows only those
            for q, must in TOPIC_Q[t]:
                for quality in (True, False):
                    if len(pics) >= want:
                        break
                    try:
                        found = _search(q, quality, must=must, food_ok=t in _OFF_FREE)
                    except requests.HTTPError as e:
                        if getattr(e.response, "status_code", 0) in (403, 429):
                            _STATE["rest"] = time.time() + 1800
                            return
                        found = []
                    except Exception:
                        found = []
                    for p in found:
                        sh = _series(p.get("f"))
                        if p["b"] not in seen and sh not in shoots and len(pics) < want:
                            seen.add(p["b"])
                            shoots.add(sh)
                            pics.append(p)
                    time.sleep(0.3)
            if pics:
                with _LOCK:
                    _POOLS[t] = {"at": time.time(), "pics": pics[:12]}
                changed = True
        if changed:
            _save()
    finally:
        _FILLING.release()


def _fill_soon():
    """Starts a background lookup when a page needs a topic photo that is not there yet (at most every 10 minutes)."""
    if time.time() - _STATE["tried"] < 600:
        return
    _STATE["tried"] = time.time()
    try:
        threading.Thread(target=fill, daemon=True, name="news-pics").start()
    except RuntimeError:
        pass


def topic_photo(topic, key, big=False):
    """{"u": url, "c": credit} of the topic's photo for this story (the same story always gets the same one), or None."""
    _load()
    pool = (_POOLS.get(topic) or {}).get("pics") or (_POOLS.get(GENERAL) or {}).get("pics")
    if not pool or (topic in TOPIC_Q and not (_POOLS.get(topic) or {}).get("pics")):
        _fill_soon()
    if not pool:
        return None
    i = int(hashlib.md5(str(key or "").encode("utf-8")).hexdigest()[:8], 16) % len(pool)
    p = pool[i]
    return {"u": p["b"] if big else p["u"], "c": p.get("c") or ""}


def topic_of(n, known=None):
    """The story's topic for its photo (as theme.news_thumb picks it): what the headline names first ("Gold steadies as ...
    Fed ..." is a gold story), else its strongest topic."""
    iq = n.get("iq") or {}
    pic = iq.get("pic")
    if pic in TOPIC_Q and (known is None or pic in known):
        return pic
    return next((t for t in iq.get("topics", []) if t in TOPIC_Q and (known is None or t in known)), GENERAL)


# ---------------------------------------------------------------- the article's own photo
_META = re.compile(r"<meta\b[^>]*>", re.I)
_ATTR = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
_LOGOISH = re.compile(r"(logo|favicon|sprite|placeholder|default[-_]?(?:image|img|og|share|social)|og[-_]default|social[-_]default|"
                      r"share[-_]default|fallback|blank\.|spacer|1x1|pixel\.)", re.I)
_PREF = ("og:image:secure_url", "og:image", "og:image:url", "twitter:image", "twitter:image:src")


def page_image(url, timeout=7, limit=400_000):
    """The photo an article page shows when it is shared (its og:image), '' when it has none or cannot be read."""
    if not url or not url.startswith("http"):
        return ""
    try:
        with requests.get(url, headers=BROWSER, timeout=timeout, stream=True, allow_redirects=True) as r:
            if r.status_code >= 400 or "html" not in r.headers.get("Content-Type", "html").lower():
                return ""
            buf, size = [], 0
            for chunk in r.iter_content(16384):
                buf.append(chunk)
                size += len(chunk)
                if size >= limit or b"</head>" in chunk.lower():
                    break
            page = b"".join(buf).decode(r.encoding or "utf-8", "ignore")
            base = r.url
    except Exception:
        return ""
    head = page.split("</head>", 1)[0] if "</head>" in page else page
    found = {}
    for tag in _META.findall(head):
        at = {k.lower(): (a or b) for k, a, b in _ATTR.findall(tag)}
        key = (at.get("property") or at.get("name") or at.get("itemprop") or "").lower()
        if key in _PREF or key == "image":
            found.setdefault(key, at.get("content") or "")
    for key in _PREF + ("image",):
        u = _html.unescape(found.get(key) or "").strip()
        if not u:
            continue
        u = "https:" + u if u.startswith("//") else urljoin(base, u)
        if u.startswith("http://"):
            u = "https://" + u[7:]
        if u.startswith("https://") and not _LOGOISH.search(urlparse(u).path):
            return u
    return ""


# ---------------------------------------------------------------- Google News links -> the publisher's link
_GN_ID = re.compile(r"/(?:rss/)?articles/([^/?#]+)")
_GN = {"rest": 0.0}


def gn_decode(link, timeout=7):
    """The publisher's own link behind a news.google.com link ('' when it cannot be found)."""
    m = _GN_ID.search(urlparse(link or "").path)
    if not m or time.time() < _GN["rest"]:
        return ""
    gid = m.group(1)
    try:
        r = requests.get(f"https://news.google.com/rss/articles/{gid}", headers=BROWSER, timeout=timeout)
        if r.status_code == 429:
            _GN["rest"] = time.time() + 900
            return ""
        sg = re.search(r'data-n-a-sg="([^"]+)"', r.text)
        ts = re.search(r'data-n-a-ts="([^"]+)"', r.text)
        if not (sg and ts):
            return ""
        req = [[["Fbv4je", '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,'
                           f'null,0,0,null,0],"{gid}",{ts.group(1)},"{sg.group(1)}"]', None, "generic"]]]
        r = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute", timeout=timeout,
                          headers={**BROWSER, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                          data=f"f.req={quote(json.dumps(req))}")
        if r.status_code == 429:
            _GN["rest"] = time.time() + 900
            return ""
        r.raise_for_status()
        rows = json.loads(r.text.split("\n\n")[1])
        for row in rows:
            if isinstance(row, list) and len(row) > 2 and isinstance(row[2], str) and "garturlres" in row[2]:
                real = json.loads(row[2])[1]
                return real if isinstance(real, str) and real.startswith("http") else ""
    except Exception:
        pass
    return ""


def find_images(stories, budget=60, workers=8):
    """{link: photo url} for the stories given (dicts with "link"), each looked up on its article page; Google News links
    are turned into the publisher's link first. Never raises; stops waiting after `budget` seconds."""
    def one(link):
        url = gn_decode(link) if "news.google.com" in link else link
        return link, page_image(url) if url else ""
    links = list(dict.fromkeys(s.get("link") or "" for s in stories if s.get("link")))
    if not links:
        return {}
    ex = ThreadPoolExecutor(max_workers=workers)
    futs = [ex.submit(one, u) for u in links]
    wait(futs, timeout=budget)
    ex.shutdown(wait=False, cancel_futures=True)
    out = {}
    for f in futs:
        if f.done() and not f.cancelled() and f.exception() is None:
            link, img = f.result()
            if img:
                out[link] = img
    return out


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.5.1"
