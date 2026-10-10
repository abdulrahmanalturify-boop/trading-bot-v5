"""
tasi.py - The Saudi market (Tadawul main market): companies, their Arabic and English names, the exchange's industry groups
and the sectors above them. Yahoo Finance symbols are the 4-digit code + '.SR' (Saudi Aramco = 2222.SR).

The list is the exchange's own (codes, trading names, industry groups) with the listings since then; approximate market caps
(SAR billions) only size the heat map until live quotes arrive.
"""

# industry group -> (sector, English, Arabic)
GROUPS = {
    "energy": ("Energy", "Energy", "الطاقة"),
    "materials": ("Materials", "Materials", "المواد الأساسية"),
    "capital": ("Industrials", "Capital Goods", "السلع الرأسمالية"),
    "commercial": ("Industrials", "Commercial & Professional Services", "الخدمات التجارية والمهنية"),
    "transport": ("Industrials", "Transportation", "النقل"),
    "durables": ("Consumer Discretionary", "Consumer Durables & Apparel", "السلع طويلة الأجل"),
    "services": ("Consumer Discretionary", "Consumer Services", "الخدمات الاستهلاكية"),
    "media": ("Communication Services", "Media & Entertainment", "الإعلام والترفيه"),
    "discretionary": ("Consumer Discretionary", "Discretionary Distribution & Retail", "توزيع السلع الكمالية وتجزئتها"),
    "staples": ("Consumer Staples", "Staples Distribution & Retail", "توزيع السلع الاستهلاكية وتجزئتها"),
    "food": ("Consumer Staples", "Food & Beverages", "إنتاج الأغذية"),
    "household": ("Consumer Staples", "Household & Personal Products", "المنتجات المنزلية والشخصية"),
    "health": ("Health Care", "Health Care Equipment & Services", "الرعاية الصحية"),
    "pharma": ("Health Care", "Pharma & Biotech", "الأدوية"),
    "banks": ("Financials", "Banks", "البنوك"),
    "finserv": ("Financials", "Financial Services", "الخدمات المالية"),
    "insurance": ("Financials", "Insurance", "التأمين"),
    "software": ("Information Technology", "Software & Services", "التطبيقات وخدمات التقنية"),
    "telecom": ("Communication Services", "Telecommunication Services", "الاتصالات"),
    "utilities": ("Utilities", "Utilities", "المرافق العامة"),
    "reits": ("Real Estate", "REITs", "الصناديق العقارية المتداولة"),
    "realestate": ("Real Estate", "Real Estate Management & Development", "إدارة وتطوير العقارات"),
}
SECTOR_AR = {"Energy": "الطاقة", "Materials": "المواد الأساسية", "Industrials": "الصناعات", "Consumer Discretionary": "السلع الكمالية",
             "Consumer Staples": "السلع الاستهلاكية الأساسية", "Health Care": "الرعاية الصحية", "Financials": "القطاع المالي",
             "Information Technology": "تقنية المعلومات", "Communication Services": "خدمات الاتصالات", "Utilities": "المرافق العامة",
             "Real Estate": "العقارات"}

# code: (English trading name, Arabic trading name, industry group)
_C = {
    # Energy
    "2030": ("SARCO", "المصافي", "energy"), "2222": ("Saudi Aramco", "أرامكو السعودية", "energy"), "2380": ("Petro Rabigh", "بترو رابغ", "energy"),
    "2381": ("Arabian Drilling", "الحفر العربية", "energy"), "2382": ("ADES", "أديس", "energy"), "4030": ("Bahri", "البحري", "energy"),
    "4200": ("Aldrees", "الدريس", "energy"),
    # Materials
    "1201": ("Takween", "تكوين", "materials"), "1202": ("MEPCO", "مبكو", "materials"), "1210": ("BCI", "بي سي آي", "materials"),
    "1211": ("Maaden", "معادن", "materials"), "1301": ("Aslak", "أسلاك", "materials"), "1304": ("Alyamamah Steel", "اليمامة للحديد", "materials"),
    "1320": ("SSP", "أنابيب السعودية", "materials"), "1321": ("East Pipes", "أنابيب الشرق", "materials"), "1322": ("AMAK", "أماك", "materials"),
    "2001": ("Chemanol", "كيمانول", "materials"), "2010": ("SABIC", "سابك", "materials"),
    "2020": ("SABIC Agri-Nutrients", "سابك للمغذيات الزراعية", "materials"), "2060": ("Tasnee", "التصنيع", "materials"),
    "2090": ("NGC", "جبسكو", "materials"), "2150": ("Zoujaj", "زجاج", "materials"), "2170": ("Alujain", "اللجين", "materials"),
    "2180": ("FIPCO", "فيبكو", "materials"), "2200": ("APC", "أنابيب", "materials"), "2220": ("Maadaniyah", "معدنية", "materials"), "2223": ("Luberef", "لوبريف", "materials"), "2240": ("Zamil Industrial", "الزامل للصناعة", "materials"),
    "2250": ("SIIG", "المجموعة السعودية", "materials"), "2290": ("Yansab", "ينساب", "materials"), "2300": ("SPM", "صناعة الورق", "materials"),
    "2310": ("Sipchem", "سبكيم العالمية", "materials"), "2330": ("Advanced", "المتقدمة", "materials"), "2350": ("Saudi Kayan", "كيان السعودية", "materials"),
    "2360": ("SVCP", "الفخارية", "materials"), "3002": ("Najran Cement", "أسمنت نجران", "materials"),
    "3003": ("City Cement", "أسمنت المدينة", "materials"), "3004": ("Northern Cement", "أسمنت الشمالية", "materials"),
    "3005": ("UACC", "أسمنت أم القرى", "materials"), "3007": ("Oasis", "الواحة", "materials"), "3008": ("Alkathiri", "الكثيري", "materials"),
    "3010": ("ACC", "أسمنت العربية", "materials"), "3020": ("YSCC", "أسمنت اليمامة", "materials"), "3030": ("Saudi Cement", "أسمنت السعودية", "materials"),
    "3040": ("QACCO", "أسمنت القصيم", "materials"), "3050": ("SPCC", "أسمنت الجنوب", "materials"), "3060": ("YCC", "أسمنت ينبع", "materials"),
    "3080": ("EPCCO", "أسمنت الشرقية", "materials"), "3090": ("TCC", "أسمنت تبوك", "materials"), "3091": ("Jouf Cement", "أسمنت الجوف", "materials"),
    "3092": ("Riyadh Cement", "أسمنت الرياض", "materials"),
    # Capital goods
    "1212": ("Astra Industrial", "أسترا الصناعية", "capital"), "1214": ("Shaker", "شاكر", "capital"), "1302": ("Bawan", "بوان", "capital"),
    "1303": ("EIC", "الصناعات الكهربائية", "capital"), "2040": ("Saudi Ceramics", "الخزف السعودي", "capital"),
    "2110": ("Saudi Cable", "الكابلات السعودية", "capital"), "2160": ("Amiantit", "أميانتيت", "capital"), "2320": ("Albabtain", "البابطين", "capital"),
    "2370": ("MESC", "مسك", "capital"), "4110": ("BATIC", "باتك", "capital"), "4140": ("SIECO", "صادرات", "capital"),
    "4141": ("Alomran", "العمران", "capital"), "4142": ("Riyadh Cables", "كابلات الرياض", "capital"),
    # Commercial & professional services
    "1831": ("Maharah", "مهارة", "commercial"), "1832": ("Sadr", "صدر", "commercial"), "1833": ("Almawarid", "الموارد", "commercial"),
    "1834": ("SMASCO", "سماسكو", "commercial"), "4270": ("SPPC", "طباعة وتغليف", "commercial"), "6004": ("Catrion", "كاتريون", "commercial"),
    # Transportation
    "2190": ("SISCO Holding", "سيسكو القابضة", "transport"), "4031": ("SGS", "الخدمات الأرضية", "transport"), "4040": ("SAPTCO", "سابتكو", "transport"),
    "4260": ("Budget Saudi", "بدجت السعودية", "transport"), "4261": ("Theeb", "ذيب", "transport"), "4262": ("Lumi", "لومي", "transport"),
    "4263": ("SAL", "سال", "transport"), "4264": ("flynas", "طيران ناس", "transport"),
    # Consumer durables & apparel
    "1213": ("Naseej", "نسيج", "durables"), "2130": ("SIDC", "صدق", "durables"), "2340": ("Alabdullatif", "العبداللطيف", "durables"),
    "4011": ("Lazurde", "لازوردي", "durables"), "4012": ("Alaseel", "الأصيل", "durables"), "4180": ("Fitaihi Group", "مجموعة فتيحي", "durables"),
    # Consumer services
    "1810": ("Seera", "سيرا", "services"), "1820": ("Alhokair Group", "مجموعة الحكير", "services"), "1830": ("Leejam Sports", "لجام للرياضة", "services"),
    "4170": ("TECO", "شمس", "services"), "4290": ("Alkhaleej Training", "الخليج للتدريب", "services"),
    "4291": ("NCLE", "الوطنية للتعليم", "services"), "4292": ("Ataa", "عطاء", "services"), "6002": ("Herfy Foods", "هرفي للأغذية", "services"),
    "6012": ("Raydan", "ريدان", "services"), "6013": ("DWF", "التطويرية الغذائية", "services"), "6014": ("Alamar", "الآمار", "services"),
    "6015": ("Americana", "أمريكانا", "services"), "6017": ("Jahez", "جاهز", "services"),
    # Media & entertainment
    "4070": ("Tihama", "تهامة", "media"), "4071": ("Alarabia", "العربية", "media"), "4072": ("MBC Group", "مجموعة إم بي سي", "media"),
    "4210": ("SRMG", "الأبحاث والإعلام", "media"),
    # Discretionary distribution & retail
    "4003": ("Extra", "إكسترا", "discretionary"), "4008": ("SACO", "ساكو", "discretionary"), "4050": ("SASCO", "ساسكو", "discretionary"),
    "4051": ("Baazeem", "باعظيم", "discretionary"), "4190": ("Jarir", "جرير", "discretionary"), "4191": ("Abo Moati", "أبو معطي", "discretionary"),
    "4192": ("Alsaif Gallery", "السيف غاليري", "discretionary"), "4193": ("Nice One", "نايس ون", "discretionary"),
    "4240": ("Cenomi Retail", "سينومي ريتيل", "discretionary"),
    # Staples distribution & retail
    "4001": ("A.Othaim Market", "أسواق ع العثيم", "staples"), "4006": ("Farm Superstores", "أسواق المزرعة", "staples"),
    "4061": ("Anaam Holding", "أنعام القابضة", "staples"), "4160": ("Thimar", "ثمار", "staples"), "4161": ("BinDawood", "بن داود", "staples"),
    "4162": ("Almunajem", "المنجم", "staples"), "4163": ("Aldawaa", "الدواء", "staples"), "4164": ("Nahdi", "النهدي", "staples"),
    # Food & beverages
    "2050": ("Savola Group", "مجموعة صافولا", "food"), "2100": ("Wafrah", "وفرة", "food"), "2270": ("SADAFCO", "سدافكو", "food"),
    "2280": ("Almarai", "المراعي", "food"), "2281": ("Tanmiah", "تنمية", "food"), "2282": ("Naqi", "نقي", "food"),
    "2283": ("First Mills", "المطاحن الأولى", "food"), "2284": ("Modern Mills", "المطاحن الحديثة", "food"),
    "2285": ("Arabian Mills", "المطاحن العربية", "food"), "2286": ("Fourth Milling", "المطاحن الرابعة", "food"),
    "4080": ("Sinad Holding", "سناد القابضة", "food"), "6001": ("Halwani Bros", "حلواني إخوان", "food"), "6010": ("NADEC", "نادك", "food"),
    "6020": ("GACO", "جاكو", "food"), "6040": ("TADCO", "تبوك الزراعية", "food"), "6050": ("SFICO", "الأسماك", "food"),
    "6060": ("Sharqiyah Dev", "الشرقية للتنمية", "food"), "6070": ("Aljouf", "الجوف", "food"), "6090": ("Jazadco", "جازادكو", "food"),
    "2084": ("Miahona", "مياهنا", "utilities"),
    # Health care
    "2140": ("Ayyan", "أيان", "health"), "2230": ("Chemical", "الكيميائية", "health"), "4002": ("Mouwasat", "المواساة", "health"),
    "4004": ("Dallah Health", "دله الصحية", "health"), "4005": ("Care", "رعاية", "health"), "4007": ("Alhammadi", "الحمادي", "health"),
    "4009": ("Saudi German Health", "السعودي الألماني الصحية", "health"), "4013": ("Sulaiman Alhabib", "سليمان الحبيب", "health"),
    "4014": ("Equipment House", "دار المعدات", "health"), "4017": ("Fakeeh Care", "فقيه الطبية", "health"), "4018": ("Almoosa Health", "الموسى", "health"),
    # Pharma
    "2070": ("SPIMACO", "الدوائية", "pharma"), "4015": ("Jamjoom Pharma", "جمجوم فارما", "pharma"), "4016": ("Avalon Pharma", "أفالون فارما", "pharma"),
    # Banks
    "1010": ("Riyad Bank", "الرياض", "banks"), "1020": ("Bank AlJazira", "الجزيرة", "banks"), "1030": ("SAIB", "الإستثمار", "banks"),
    "1050": ("BSF", "بي اس اف", "banks"), "1060": ("SAB", "الأول", "banks"), "1080": ("ANB", "العربي", "banks"),
    "1120": ("Al Rajhi Bank", "الراجحي", "banks"), "1140": ("Bank Albilad", "البلاد", "banks"), "1150": ("Alinma Bank", "الإنماء", "banks"),
    "1180": ("SNB", "الأهلي", "banks"),
    # Financial services
    "1111": ("Tadawul Group", "مجموعة تداول", "finserv"), "1182": ("Amlak", "أملاك", "finserv"), "1183": ("SHL", "سهل", "finserv"),
    "2120": ("SAIC", "المتطورة", "finserv"), "4081": ("Nayifat", "النايفات", "finserv"), "4082": ("MRNA", "مرنة", "finserv"),
    "4084": ("Derayah", "دراية", "finserv"), "4130": ("Albaha", "الباحة", "finserv"), "4280": ("Kingdom Holding", "المملكة", "finserv"),
    # Insurance
    "8010": ("Tawuniya", "التعاونية", "insurance"), "8012": ("Jazira Takaful", "الجزيرة تكافل", "insurance"), "8020": ("Malath", "ملاذ للتأمين", "insurance"),
    "8030": ("Medgulf", "ميدغلف للتأمين", "insurance"), "8040": ("Allianz SF", "أليانز إس إف", "insurance"), "8050": ("Salama", "سلامة", "insurance"),
    "8060": ("Walaa", "ولاء", "insurance"), "8070": ("Arabian Shield", "الدرع العربي", "insurance"), "8100": ("SAICO", "سايكو", "insurance"),
    "8120": ("Gulf Union Alahlia", "إتحاد الخليج الأهلية", "insurance"), "8150": ("ACIG", "أسيج", "insurance"),
    "8160": ("AICC", "التأمين العربية", "insurance"), "8170": ("Aletihad", "الاتحاد", "insurance"), "8180": ("Alsagr", "الصقر للتأمين", "insurance"),
    "8200": ("Saudi Re", "الإعادة السعودية", "insurance"), "8210": ("Bupa Arabia", "بوبا العربية", "insurance"),
    "8230": ("Al Rajhi Takaful", "تكافل الراجحي", "insurance"), "8240": ("Chubb Arabia", "تشب", "insurance"), "8250": ("GIG", "جي آي جي", "insurance"),
    "8260": ("Gulf General", "الخليجية العامة", "insurance"), "8280": ("Liva", "ليفا", "insurance"),
    "8300": ("Wataniya", "الوطنية", "insurance"), "8310": ("Amana Insurance", "أمانة للتأمين", "insurance"), "8311": ("Enaya", "عناية", "insurance"),
    "8313": ("Rasan", "رسن", "insurance"),
    # Software & services
    "7200": ("MIS", "ام آي اس", "software"), "7201": ("Arab Sea", "بحر العرب", "software"), "7202": ("Solutions", "سلوشنز", "software"),
    "7203": ("Elm", "علم", "software"), "7204": ("2P", "توبي", "software"),
    # Telecom
    "7010": ("stc", "اس تي سي", "telecom"), "7020": ("Mobily", "إتحاد إتصالات", "telecom"), "7030": ("Zain KSA", "زين السعودية", "telecom"),
    "7040": ("GO Telecom", "قو للإتصالات", "telecom"),
    # Utilities
    "2080": ("GASCO", "الغاز", "utilities"), "2081": ("Alkhorayef Water", "الخريف", "utilities"), "2082": ("ACWA Power", "أكوا", "utilities"),
    "2083": ("Marafiq", "مرافق", "utilities"), "5110": ("Saudi Electricity", "السعودية للطاقة", "utilities"),
    # REITs
    "4330": ("Riyad REIT", "الرياض ريت", "reits"), "4331": ("Aljazira REIT", "الجزيرة ريت", "reits"),
    "4332": ("Jadwa REIT Alharamain", "جدوى ريت الحرمين", "reits"), "4333": ("Taleem REIT", "تعليم ريت", "reits"),
    "4334": ("Al Maather REIT", "المعذر ريت", "reits"), "4335": ("Musharaka REIT", "مشاركة ريت", "reits"), "4336": ("Mulkia REIT", "ملكية ريت", "reits"),
    "4337": ("SICO Saudi REIT", "سيكو السعودية ريت", "reits"), "4338": ("Alahli REIT 1", "الأهلي ريت 1", "reits"),
    "4339": ("Derayah REIT", "دراية ريت", "reits"), "4340": ("Al Rajhi REIT", "الراجحي ريت", "reits"),
    "4342": ("Jadwa REIT Saudi", "جدوى ريت السعودية", "reits"), "4344": ("SEDCO Capital REIT", "سدكو كابيتال ريت", "reits"),
    "4345": ("Alinma Retail REIT", "الإنماء ريت للتجزئة", "reits"), "4346": ("MEFIC REIT", "ميفك ريت", "reits"),
    "4347": ("Bonyan REIT", "بنيان ريت", "reits"), "4348": ("Alkhabeer REIT", "الخبير ريت", "reits"),
    "4349": ("Alinma Hospitality REIT", "الإنماء ريت الفندقي", "reits"),
    # Real estate management & development
    "4020": ("Alakaria", "العقارية", "realestate"), "4090": ("Taiba", "طيبة", "realestate"), "4100": ("Makkah Construction", "مكة", "realestate"),
    "4150": ("ARDCO", "التعمير", "realestate"), "4220": ("Emaar EC", "إعمار", "realestate"), "4230": ("Red Sea", "البحر الأحمر", "realestate"),
    "4250": ("Jabal Omar", "جبل عمر", "realestate"), "4300": ("Dar Alarkan", "دار الأركان", "realestate"),
    "4310": ("Knowledge Economic City", "مدينة المعرفة", "realestate"), "4320": ("Alandalus", "الأندلس", "realestate"),
    "4321": ("Cenomi Centers", "سينومي سنترز", "realestate"), "4322": ("Retal", "رتال", "realestate"), "4323": ("Sumou", "سمو", "realestate"),
    "4325": ("Umm Al Qura", "مسار", "realestate"),
    # listed since (Yahoo Finance's list, October 2026)
    "1323": ("United Carton", "الكرتون المتحدة", "materials"), "1324": ("Al Rashed & Sons", "صالح الراشد", "capital"),
    "1325": ("Watani Steel", "الوطني للحديد", "materials"), "1835": ("Tamkeen", "تمكين", "commercial"),
    "2287": ("Entaj", "إنتاج", "food"), "2288": ("Nofoth", "نفوذ", "food"), "4019": ("SMC Healthcare", "اس ام سي للرعاية الصحية", "health"),
    "4021": ("Canadian Medical Center", "المركز الكندي الطبي", "health"), "4083": ("Tasheel", "تسهيل", "finserv"),
    "4143": ("Talco", "تالكو", "materials"), "4144": ("Raoom", "رؤوم", "capital"), "4145": ("Obeikan Glass", "العبيكان للزجاج", "capital"),
    "4146": ("GAS", "جاز", "energy"), "4147": ("CGS", "سي جي إس", "capital"), "4148": ("Alwasail", "الوسائل الصناعية", "materials"),
    "4165": ("Almajed Oud", "الماجد للعود", "household"), "4194": ("Marketing Home", "بيت التسويق", "capital"),
    "4265": ("Cherry", "شيري", "commercial"), "4324": ("Banan", "بنان", "realestate"), "4326": ("Dar Al Majed", "الماجدية", "realestate"),
    "4327": ("Alramz", "الرمز", "realestate"), "4328": ("Ladun", "لدن", "realestate"), "4350": ("Alistithmar REIT", "الاستثمار ريت", "reits"),
    "6016": ("Shatirah House", "بيت الشطيرة", "services"), "6018": ("Sport Clubs", "الأندية للرياضة", "services"),
    "6019": ("Almasar Alshamil", "المسار الشامل", "services"), "6022": ("Armah Sports", "أرماح", "services"),
    "7205": ("Dar Albalad", "دار البلد", "software"), "7211": ("Azm", "عزم", "software"),
}

# approximate market caps, SAR billions (Yahoo Finance, October 2026): heat map sizes before live quotes arrive
_CAP = {"2222": 6226.7, "1120": 373.8, "1211": 242.2, "1180": 224.7, "7010": 212.6, "2010": 137.4, "2082": 126.3, "4013": 80, "1010": 77.7,
        "1150": 71.6, "1060": 70.2, "5110": 63.6, "2020": 55.6, "4280": 50.7, "7020": 49, "1050": 48.8, "2280": 44.2, "7203": 44.2,
        "1080": 43.7, "2380": 36.7, "1140": 34.3, "4030": 32.4, "7202": 23.9, "4325": 23.4, "2223": 21.7, "8210": 21.3, "6015": 20.5,
        "4300": 20.2, "4250": 19.9, "8010": 19.5, "4190": 19.2, "2290": 18.1, "2382": 18.1, "1030": 17.5, "4142": 15.9, "4100": 15.4,
        "1303": 14.8, "1020": 14.5, "1111": 14.3, "4263": 13.9, "4002": 12.4, "4164": 11.8, "4200": 11.7, "8313": 10.8, "2083": 10.4,
        "8230": 10, "1212": 9.9, "4004": 9.4, "4090": 9.1, "7200": 9.1, "4015": 9, "2310": 8.7, "2381": 8.7, "7030": 8.7, "4220": 8.3,
        "4017": 7.9, "2250": 7.8, "4310": 7.4, "4264": 7.3, "2050": 7.2, "2350": 7.2, "4321": 7.2, "4072": 6.4, "2230": 6.1, "1322": 6,
        "2270": 5.8, "2330": 5.6, "4020": 5.6, "1321": 5.5, "4291": 5.4, "1810": 5.3, "2060": 5.2, "4018": 5.2, "4161": 5.1, "3040": 4.9,
        "4005": 4.9, "6004": 4.9, "4084": 4.7, "8200": 4.7, "2080": 4.3, "3020": 4.3, "4322": 4.3, "4003": 4.2, "4210": 4.2, "3030": 4.1,
        "4031": 4, "6010": 4, "6050": 4, "1830": 3.8, "4150": 3.8, "4001": 3.7, "4019": 3.7, "2070": 3.6, "4007": 3.6, "2320": 3.4,
        "4162": 3.4, "2081": 3.1, "2190": 3, "4163": 2.9, "4165": 2.9, "2283": 2.8, "7040": 2.8, "1320": 2.7, "4050": 2.7, "4260": 2.7,
        "3050": 2.6, "4009": 2.5, "4146": 2.5, "3092": 2.4, "4071": 2.4, "6017": 2.4, "6019": 2.4, "1831": 2.3, "3060": 2.3, "4327": 2.3,
        "2040": 2.2, "4016": 2.2, "1834": 2.1, "2284": 2.1, "2300": 2.1, "4192": 2.1, "4340": 2.1, "8030": 2.1, "1302": 2, "2285": 2,
        "2286": 2, "3010": 2, "3080": 2, "1833": 1.9, "2170": 1.8, "4083": 1.8, "4326": 1.8, "7211": 1.8, "1304": 1.7, "4240": 1.6,
        "4292": 1.6, "4342": 1.6, "8250": 1.6, "2084": 1.5, "2240": 1.5, "4347": 1.5, "7204": 1.5, "1202": 1.4, "2370": 1.4, "3003": 1.4,
        "8060": 1.4, "1183": 1.3, "2200": 1.3, "4012": 1.3, "4040": 1.3, "4143": 1.3, "4261": 1.3, "4262": 1.3, "4320": 1.3, "4344": 1.3,
        "2110": 1.2, "2282": 1.2, "3004": 1.2, "4193": 1.2, "4323": 1.2, "1820": 1.1, "1835": 1.1, "2150": 1.1, "2281": 1.1, "4081": 1.1,
        "4110": 1.1, "6070": 1.1, "1323": 1, "3002": 1, "4080": 1, "4144": 1, "4230": 1, "6001": 1, "6014": 1, "8070": 1, "2120": 0.9,
        "2140": 0.9, "4328": 0.9, "4338": 0.9, "6002": 0.9, "6018": 0.9, "1182": 0.8, "1324": 0.8, "2030": 0.8, "2340": 0.8, "4014": 0.8,
        "4145": 0.8, "4290": 0.8, "4348": 0.8, "7205": 0.8, "1214": 0.7, "4148": 0.7, "4170": 0.7, "4191": 0.7, "4330": 0.7, "4349": 0.7,
        "1210": 0.6, "2287": 0.6, "2288": 0.6, "3005": 0.6, "3007": 0.6, "3090": 0.6, "4082": 0.6, "4147": 0.6, "4180": 0.6, "4194": 0.6,
        "4265": 0.6, "4324": 0.6, "4339": 0.6, "8012": 0.6, "8040": 0.6, "8120": 0.6, "8240": 0.6, "1301": 0.5, "2100": 0.5, "2160": 0.5,
        "3091": 0.5, "4006": 0.5, "4008": 0.5, "4011": 0.5, "4051": 0.5, "4333": 0.5, "4334": 0.5, "4336": 0.5, "4345": 0.5, "8280": 0.5,
        "8300": 0.5, "1325": 0.4, "1832": 0.4, "2001": 0.4, "2090": 0.4, "2130": 0.4, "2180": 0.4, "2220": 0.4, "4021": 0.4, "4061": 0.4,
        "4070": 0.4, "4130": 0.4, "4140": 0.4, "4270": 0.4, "4350": 0.4, "6016": 0.4, "6020": 0.4, "6060": 0.4, "6090": 0.4, "7201": 0.4,
        "8020": 0.4, "8160": 0.4, "1201": 0.3, "1213": 0.3, "2360": 0.3, "4332": 0.3, "4335": 0.3, "6040": 0.3, "8100": 0.3, "8170": 0.3,
        "8180": 0.3, "8310": 0.3, "3008": 0.2, "4141": 0.2, "4160": 0.2, "4337": 0.2, "4346": 0.2, "6013": 0.2, "8050": 0.2, "8150": 0.2,
        "8311": 0.2, "4331": 0.1, "6012": 0.1, "8260": 0.1}


def sym(code):
    return f"{code}.SR"


SA = {sym(c): v for c, v in _C.items()}               # 'XXXX.SR': (English, Arabic, group)
SYMBOLS = sorted(SA)


def known(s):
    return s in SA


# the Tadawul funds and indices the site shows (the Saudi Robo Advisor's funds, the market's indices)
FUNDS = {"9400.SR": ("YAQEEN Saudi Equity", "يقين للأسهم السعودية"), "9403.SR": ("Albilad Sukuk", "البلاد للصكوك"),
         "9404.SR": ("Alinma Sukuk", "الإنماء للصكوك"), "9405.SR": ("Albilad Gold", "البلاد للذهب"),
         "9406.SR": ("Albilad US Equity", "البلاد للأسهم الأمريكية")}
INDICES = {"^TASI.SR": ("TASI", "تاسي"), "^TASI": ("TASI", "تاسي"), "^NOMUC.SR": ("Nomu", "نمو")}


def label(s, ar=False, default=None):
    """How the site shows a Saudi symbol: the company's (or fund's, or index's) name, not its number. Any other symbol as it is;
    a Saudi code the site doesn't know: `default` (a name from the data) or its number."""
    s = str(s or "")
    r = SA.get(s) or FUNDS.get(s) or INDICES.get(s)
    if r:
        return r[1] if ar else r[0]
    if default:
        return str(default)
    return s[:-3] if s.endswith(".SR") else s


def is_sa(s):
    return str(s or "").endswith(".SR") or str(s or "") in INDICES


def name_of(s, ar=False):
    r = SA.get(s)
    return (r[1] if ar else r[0]) if r else ""


def group_of(s):
    r = SA.get(s)
    return r[2] if r else ""


def sector_of(s):
    """The sector (English key, as GROUPS[...][0]) of a Saudi symbol, '' if unknown."""
    g = group_of(s)
    return GROUPS[g][0] if g else ""


def industry_of(s):
    """The exchange's industry group (English name), '' if unknown."""
    g = group_of(s)
    return GROUPS[g][1] if g else ""


def industry_ar(name):
    for g in GROUPS.values():
        if g[1] == name:
            return g[2]
    return name


def sector_ar(name):
    return SECTOR_AR.get(name, name)


def cap_b(s):
    """Approximate market cap in SAR billions (1 if unknown)."""
    return float(_CAP.get(s.split(".")[0], 1.0))


SECTORS = sorted({g[0] for g in GROUPS.values()})


def by_sector():
    out = {}
    for s in SYMBOLS:
        out.setdefault(sector_of(s), []).append(s)
    return out


def industries(sector=None):
    """Industry groups (English names) of a sector, or all."""
    return sorted({g[1] for g in GROUPS.values() if sector is None or g[0] == sector})


def by_industry():
    out = {}
    for s in SYMBOLS:
        out.setdefault(industry_of(s), []).append(s)
    return out


def top(n=30):
    """The n biggest companies by approximate market cap."""
    return sorted(SYMBOLS, key=lambda s: -cap_b(s))[:n]


def search(q):
    """Saudi symbols whose code, English or Arabic name contains q (for the search box)."""
    q = str(q or "").strip().lower()
    if not q:
        return []
    return [s for s in SYMBOLS if q in s.lower() or q in SA[s][0].lower() or q in SA[s][1]]


# ---------------------------------------------------------------- companies named in a headline
# Names that are words on their own (الرياض, الأول, العربي, الجزيرة, علم, سهل...) are only taken in a longer form.
_ALIASES = {
    "2222": ["أرامكو", "Aramco"], "1120": ["مصرف الراجحي", "بنك الراجحي", "الراجحي المصرفية", "Al Rajhi Bank", "Alrajhi Bank"],
    "1180": ["البنك الأهلي السعودي", "الأهلي السعودي", "Saudi National Bank", "SNB"], "1010": ["بنك الرياض", "Riyad Bank"],
    "1150": ["مصرف الإنماء", "بنك الإنماء", "Alinma"], "1140": ["بنك البلاد", "Bank Albilad"], "1020": ["بنك الجزيرة", "Bank AlJazira"],
    "1060": ["البنك السعودي الأول", "ساب", "Saudi Awwal Bank"], "1080": ["البنك العربي الوطني", "Arab National Bank"],
    "1050": ["البنك السعودي الفرنسي", "Banque Saudi Fransi"], "1030": ["البنك السعودي للاستثمار", "Saudi Investment Bank"],
    "2010": ["سابك", "SABIC"], "2020": ["سابك للمغذيات", "SABIC Agri"], "1211": ["معادن", "Maaden", "Ma'aden"], "7010": ["إس تي سي", "اس تي سي", "stc group", "stc"],
    "7020": ["موبايلي", "اتحاد اتصالات", "إتحاد إتصالات", "Mobily"], "7030": ["زين السعودية", "Zain KSA"], "2082": ["أكوا باور", "أكوا", "ACWA Power"],
    "5110": ["السعودية للكهرباء", "الشركة السعودية للكهرباء", "Saudi Electricity"], "4013": ["سليمان الحبيب", "Sulaiman Al Habib"],
    "2280": ["المراعي", "Almarai"], "4190": ["جرير", "Jarir"], "7203": ["شركة علم", "Elm Company"], "8210": ["بوبا العربية", "Bupa Arabia"],
    "1111": ["مجموعة تداول", "Saudi Tadawul Group"], "4030": ["البحري", "Bahri"], "4300": ["دار الأركان", "Dar Al Arkan"],
    "4250": ["جبل عمر", "Jabal Omar"], "4264": ["طيران ناس", "فلاي ناس", "flynas"], "4164": ["النهدي", "Nahdi"], "4002": ["المواساة", "Mouwasat"],
    "2050": ["صافولا", "Savola"], "4280": ["المملكة القابضة", "Kingdom Holding"], "2290": ["ينساب", "Yansab"], "2310": ["سبكيم", "Sipchem"],
    "2380": ["بترو رابغ", "Petro Rabigh"], "2223": ["لوبريف", "Luberef"], "6015": ["أمريكانا", "Americana"], "8010": ["التعاونية للتأمين", "Tawuniya"],
    "4142": ["كابلات الرياض", "Riyadh Cables"], "4263": ["سال السعودية", "SAL Saudi Logistics"], "1810": ["سيرا القابضة", "Seera"],
    "2381": ["الحفر العربية", "Arabian Drilling"], "2382": ["أديس", "ADES Holding"], "4200": ["الدريس", "Aldrees"], "2350": ["كيان السعودية", "Saudi Kayan"],
    "2060": ["التصنيع الوطنية", "Tasnee"], "4220": ["إعمار المدينة الاقتصادية", "Emaar Economic City"], "4321": ["سينومي سنترز", "Cenomi Centers"],
    "4240": ["سينومي ريتيل", "Cenomi Retail"], "4322": ["رتال", "Retal"], "4090": ["طيبة القابضة", "Taiba"], "4100": ["مكة للإنشاء", "Makkah Construction"],
    "7202": ["سلوشنز", "solutions by stc"], "7200": ["ام آي اس", "Al Moammar Information"], "4072": ["إم بي سي", "MBC Group"], "4210": ["الأبحاث والإعلام", "SRMG"],
    "2081": ["الخريف", "Alkhorayef"], "2083": ["مرافق", "Marafiq"], "1303": ["الصناعات الكهربائية", "Electrical Industries"], "8313": ["رسن", "Rasan"],
    "4017": ["فقيه", "Fakeeh"], "4084": ["دراية المالية", "Derayah"], "4325": ["أم القرى للتنمية", "Umm Al Qura"], "6017": ["جاهز", "Jahez"],
    "4193": ["نايس ون", "Nice One"], "1830": ["لجام للرياضة", "Leejam"], "4161": ["بن داود", "BinDawood"], "4001": ["العثيم", "Othaim"],
    "4003": ["إكسترا", "eXtra"], "4008": ["ساكو", "SACO"], "6004": ["كاتريون", "Catrion"], "4031": ["الخدمات الأرضية", "Saudi Ground Services"],
    "4004": ["دله الصحية", "Dallah Healthcare"], "4009": ["السعودي الألماني", "Saudi German Health"], "4015": ["جمجوم فارما", "Jamjoom Pharma"],
    "2070": ["الدوائية", "SPIMACO"], "3030": ["أسمنت السعودية", "Saudi Cement"], "3020": ["أسمنت اليمامة", "Yamama Cement"], "3040": ["أسمنت القصيم", "Qassim Cement"],
    "1212": ["أسترا الصناعية", "Astra Industrial"], "1321": ["أنابيب الشرق", "East Pipes"], "1322": ["أماك", "AMAK"], "4291": ["الوطنية للتعليم", "National Company for Learning"],
    "1182": ["أملاك العالمية", "Amlak"], "1183": ["سهل للتمويل", "Saudi Home Loans"], "4081": ["النايفات", "Nayifat"], "4082": ["مرنة", "MRNA"],
    "4340": ["الراجحي ريت", "Al Rajhi REIT"], "8230": ["تكافل الراجحي", "Al Rajhi Takaful"],
}


def _alias_re():
    import re
    pairs = []
    for code, names in _ALIASES.items():
        for n in names:
            pairs.append((n, sym(code)))
    pairs.sort(key=lambda x: -len(x[0]))                  # the longest name wins (تكافل الراجحي before مصرف الراجحي)
    words = []
    for n, s in pairs:
        latin = n.isascii()
        pat = re.escape(n)
        words.append((re.compile(r"(?<![\w])" + pat + r"(?![\w])", 0 if (latin and n.isupper() and len(n) <= 5) else re.I), s))
    return words


_ALIAS_RE = []


def tickers_in(text):
    """The Saudi companies a headline names (by their Arabic or English names, or a '2222.SR' / '(2222)' code)."""
    import re
    if not _ALIAS_RE:
        _ALIAS_RE.extend(_alias_re())
    text = str(text or "")
    found, taken = [], []
    for rx, s in _ALIAS_RE:
        for m in rx.finditer(text):
            if any(a <= m.start() < b for a, b in taken):
                continue
            taken.append((m.start(), m.end()))
            found.append(s)
    for m in re.finditer(r"\b(\d{4})(?:\.SR\b|\))", text):
        if sym(m.group(1)) in SA:
            found.append(sym(m.group(1)))
    return list(dict.fromkeys(found))[:6]


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.4"
