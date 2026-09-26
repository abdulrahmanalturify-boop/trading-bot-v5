"""
insight.py - Articles for the Insight section (bilingual, plain language, with live charts from the site's data).
Body blocks: ("h", en, ar) heading · ("p", en, ar) paragraph · ("list", [(en, ar), ...]) bullets ·
("chart", key, (caption_en, caption_ar)) live chart · ("note", en, ar) tip box
"""

CATEGORIES = {"macro": ("Economy & the Fed", "الاقتصاد والفيدرالي", "#1D4ED8", "#7C3AED"),
              "markets": ("How markets work", "كيف تعمل الأسواق", "#0F766E", "#1D4ED8"),
              "investing": ("Investing wisely", "الاستثمار بحكمة", "#7C2D12", "#B45309"),
              "trading": ("Trading & risk", "التداول والمخاطر", "#831843", "#6D28D9")}

ARTICLES = [
    {"id": "fed", "cat": "macro", "icon": "account_balance", "mins": 6,
     "title": ("How the Federal Reserve Moves the Stock Market", "كيف يحرّك الاحتياطي الفيدرالي سوق الأسهم"),
     "dek": ("Eight meetings a year shape the price of money, and with it the value of every stock. Here is how the chain works.",
             "ثمانية اجتماعات في السنة تحدد سعر المال، ومعه قيمة كل سهم. إليك كيف تعمل هذه السلسلة."),
     "takeaways": [("The Fed's job is stable prices (2% inflation) and maximum employment.", "مهمة الفيدرالي: استقرار الأسعار (تضخم 2%) وأقصى توظيف ممكن."),
                   ("Lower rates usually lift valuations; higher rates pressure growth stocks the most.", "خفض الفائدة يرفع التقييمات عادة، ورفعها يضغط على أسهم النمو أكثر من غيرها."),
                   ("Markets move on the surprise versus expectations, not on the decision itself.", "السوق يتحرك على المفاجأة مقارنة بالتوقعات، وليس على القرار نفسه.")],
     "body": [
         ("h", "What the Fed actually controls", "ما الذي يتحكم فيه الفيدرالي فعلاً"),
         ("p", "The Federal Reserve sets a target range for the federal funds rate, the rate banks charge each other for overnight loans. That single number "
               "ripples through the economy: it influences mortgage rates, credit cards, corporate borrowing and the yield on Treasury bills. The Fed's "
               "policy committee, the FOMC, meets eight times a year and publishes its decision at 2:00 PM New York time, followed by a press conference.",
          "يحدد الاحتياطي الفيدرالي نطاقاً مستهدفاً لسعر الفائدة على الأموال الفيدرالية، وهو السعر الذي تقرض به البنوك بعضها لليلة واحدة. هذا الرقم الواحد يمتد "
          "أثره في الاقتصاد كله: يؤثر على فوائد الرهن العقاري وبطاقات الائتمان واقتراض الشركات وعوائد أذونات الخزانة. تجتمع لجنة السياسة النقدية (FOMC) ثماني "
          "مرات في السنة وتعلن قرارها الساعة 2:00 ظهراً بتوقيت نيويورك، يتبعه مؤتمر صحفي."),
         ("chart", "fed", ("Live: the Fed's target range and the effective rate.", "مباشر: النطاق المستهدف للفيدرالي والفائدة الفعلية.")),
         ("h", "Why rates change what stocks are worth", "لماذا تغيّر الفائدة قيمة الأسهم"),
         ("p", "A stock is worth the profits it will earn in the future, translated into today's money. When interest rates rise, future dollars are worth less "
               "today, so investors pay less for the same earnings. The effect is strongest for fast-growing companies whose profits are far in the future, "
               "which is why technology stocks often react most to rate expectations. Higher rates also raise borrowing costs and can slow the economy, "
               "which hurts earnings themselves.",
          "قيمة السهم هي الأرباح التي سيحققها مستقبلاً محوّلة إلى قيمة اليوم. عندما ترتفع الفائدة تقل قيمة الدولار المستقبلي اليوم، فيدفع المستثمرون أقل مقابل "
          "نفس الأرباح. ويكون الأثر أقوى في الشركات سريعة النمو التي تأتي أرباحها بعد سنوات، ولهذا تتفاعل أسهم التقنية غالباً أكثر من غيرها مع توقعات الفائدة. "
          "كما أن ارتفاع الفائدة يرفع تكلفة الاقتراض وقد يبطئ الاقتصاد، وهذا يضغط على الأرباح نفسها."),
         ("h", "Expectations are everything", "التوقعات هي كل شيء"),
         ("p", "By the time the Fed announces a decision, markets have usually priced it in. Traders use futures contracts to estimate the odds of each outcome "
               "days in advance. What moves prices is the surprise: a cut that was fully expected may do little, while a hint that fewer cuts are coming can "
               "push stocks down even on the day rates are lowered. Pay attention to the statement's wording, the 'dot plot' of officials' projections "
               "(published four times a year) and the chair's tone in the press conference.",
          "حين يعلن الفيدرالي قراره يكون السوق غالباً قد سعّره مسبقاً، إذ يستخدم المتداولون العقود الآجلة لتقدير احتمالات كل نتيجة قبلها بأيام. ما يحرك "
          "الأسعار هو المفاجأة: خفض متوقع بالكامل قد لا يغير شيئاً، بينما تلميح بأن مرات الخفض القادمة ستكون أقل قد يهبط بالأسهم حتى في يوم خفض الفائدة. "
          "انتبه لصياغة البيان، ولمخطط النقاط (Dot Plot) الذي يعرض توقعات الأعضاء أربع مرات في السنة، ولنبرة الرئيس في المؤتمر الصحفي."),
         ("h", "A simple checklist for Fed days", "قائمة مختصرة ليوم قرار الفيدرالي"),
         ("list", [("Know what the market expects before the announcement (the probabilities are widely reported).",
                    "اعرف توقعات السوق قبل الإعلان (الاحتمالات تُنشر على نطاق واسع)."),
                   ("Compare the decision and the new projections with those expectations.", "قارن القرار والتوقعات الجديدة بما كان متوقعاً."),
                   ("Watch the 2-year Treasury yield: it reacts fastest to changes in the rate outlook.",
                    "راقب عائد سندات السنتين: هو الأسرع تفاعلاً مع تغير توقعات الفائدة."),
                   ("Avoid big new positions in the minutes around 2:00 PM ET, when spreads widen and moves are erratic.",
                    "تجنب فتح صفقات كبيرة في الدقائق القريبة من الساعة 2:00 ظهراً بتوقيت نيويورك حيث تتسع الفروق وتضطرب الحركة.")]),
         ("note", "Follow the live rates, the yield curve and the Fed's path on the Economy page.",
          "تابع أسعار الفائدة ومنحنى العائد ومسار الفيدرالي مباشرة في صفحة الاقتصاد.")],
     "related": ["economy", "brief"]},

    {"id": "curve", "cat": "macro", "icon": "timeline", "mins": 5,
     "title": ("The Yield Curve: Wall Street's Favorite Recession Signal", "منحنى العائد: إشارة الركود المفضلة في وول ستريت"),
     "dek": ("When short-term Treasuries pay more than long-term ones, investors take notice. What an inverted curve means, and what it doesn't.",
             "عندما تدفع السندات قصيرة الأجل عائداً أعلى من طويلة الأجل ينتبه المستثمرون. ماذا يعني المنحنى المقلوب، وما الذي لا يعنيه."),
     "takeaways": [("Normally, lending for longer pays more: the curve slopes upward.", "في الوضع الطبيعي يعطي الإقراض لمدة أطول عائداً أعلى، فيكون المنحنى صاعداً."),
                   ("An inverted curve (10-year below 2-year) has come before most US recessions of the past 50 years.",
                    "المنحنى المقلوب (عائد 10 سنوات أقل من سنتين) سبق أغلب حالات الركود الأمريكية في آخر 50 سنة."),
                   ("The timing is vague and false alarms happen, so treat it as a warning light, not a trading signal.",
                    "التوقيت غير دقيق والإنذارات الكاذبة واردة، فتعامل معه كضوء تحذير وليس كإشارة تداول.")],
     "body": [
         ("h", "What the yield curve is", "ما هو منحنى العائد"),
         ("p", "The yield curve plots the interest rates on US Treasury bonds from the shortest maturities (a few months) to the longest (30 years). Because "
               "investors usually want extra compensation for tying up money longer, long-term yields are normally higher than short-term ones. That upward "
               "slope is considered healthy.",
          "منحنى العائد رسم يوضح أسعار الفائدة على سندات الخزانة الأمريكية من أقصر الآجال (بضعة أشهر) إلى أطولها (30 سنة). ولأن المستثمر يطلب عادة تعويضاً "
          "إضافياً مقابل ربط أمواله لمدة أطول، تكون العوائد طويلة الأجل في العادة أعلى من القصيرة، وهذا الميل الصاعد يعتبر علامة صحية."),
         ("h", "Why an inversion worries investors", "لماذا يقلق الانقلاب المستثمرين"),
         ("p", "Short-term yields follow the Fed's policy rate, while long-term yields reflect what investors expect for growth and inflation over many years. "
               "When the 2-year yield rises above the 10-year, the market is saying that today's rates are high and likely to fall, usually because the "
               "economy is expected to weaken. Banks, which borrow short and lend long, also earn less, which can tighten credit.",
          "العوائد قصيرة الأجل تتبع سعر فائدة الفيدرالي، بينما تعكس العوائد طويلة الأجل توقعات المستثمرين للنمو والتضخم على مدى سنوات. فإذا ارتفع عائد "
          "السنتين فوق عائد العشر سنوات، فالسوق يقول إن الفائدة الحالية مرتفعة ومن المرجح أن تنخفض، وغالباً لأن الاقتصاد متوقع أن يضعف. كما أن البنوك التي "
          "تقترض قصيراً وتقرض طويلاً تربح أقل، وهذا قد يشدد الإقراض."),
         ("chart", "curve", ("Live: the 10-year minus 2-year spread. Below zero = inverted.", "مباشر: الفرق بين عائد 10 سنوات وسنتين. تحت الصفر = مقلوب.")),
         ("h", "A good alarm with a bad clock", "منبّه جيد لكن ساعته غير دقيقة"),
         ("p", "Inversions have appeared before most US recessions since the 1970s, but the lag has ranged from several months to about two years, and stocks "
               "have often kept rising for a while after the curve inverted. The long inversion of 2022 to 2024 was not followed by an immediate recession, "
               "a reminder that no single indicator is perfect. Many analysts also watch the moment the curve turns positive again, which has historically "
               "come close to the start of downturns.",
          "ظهر الانقلاب قبل أغلب حالات الركود الأمريكية منذ السبعينيات، لكن الفارق الزمني تراوح بين عدة أشهر ونحو سنتين، وكثيراً ما واصلت الأسهم الصعود "
          "لفترة بعد انقلاب المنحنى. والانقلاب الطويل بين 2022 و2024 لم يتبعه ركود فوري، وهذا تذكير بأنه لا يوجد مؤشر واحد مثالي. ويراقب كثير من المحللين "
          "أيضاً لحظة عودة المنحنى إلى الوضع الطبيعي، إذ جاءت تاريخياً قريبة من بداية فترات التراجع."),
         ("h", "How to use it", "كيف تستخدمه"),
         ("list", [("Use the curve to set your level of caution, not to time exact entries or exits.",
                    "استخدم المنحنى لتحديد مستوى حذرك، وليس لتوقيت الدخول والخروج بدقة."),
                   ("Confirm with other data: jobless claims, earnings trends and credit spreads.",
                    "أكّد الإشارة ببيانات أخرى: طلبات إعانة البطالة واتجاه الأرباح وفروق الائتمان."),
                   ("Defensive sectors such as utilities, health care and staples have tended to hold up better in slowdowns.",
                    "القطاعات الدفاعية مثل المرافق والرعاية الصحية والسلع الأساسية تميل للصمود أفضل في فترات التباطؤ.")])],
     "related": ["economy", "sentiment"]},

    {"id": "inflation", "cat": "macro", "icon": "trending_up", "mins": 5,
     "title": ("Inflation and Your Portfolio", "التضخم ومحفظتك الاستثمارية"),
     "dek": ("Rising prices quietly shrink cash and shape what the Fed does next. How to read CPI and PCE, and what they mean for stocks.",
             "ارتفاع الأسعار يأكل قيمة النقد بهدوء ويحدد خطوة الفيدرالي التالية. كيف تقرأ مؤشري CPI وPCE وما تأثيرهما على الأسهم."),
     "takeaways": [("At 3% inflation, cash loses about a quarter of its buying power in 10 years.", "مع تضخم 3% يفقد النقد نحو ربع قوته الشرائية خلال 10 سنوات."),
                   ("The Fed targets 2% inflation measured by the PCE index; CPI gets the headlines.",
                    "يستهدف الفيدرالي تضخماً عند 2% بحسب مؤشر PCE، بينما يتصدر مؤشر CPI العناوين."),
                   ("Core inflation (excluding food and energy) shows the underlying trend.", "التضخم الأساسي (بدون الغذاء والطاقة) يوضح الاتجاه الحقيقي.")],
     "body": [
         ("h", "Two measures, one target", "مقياسان وهدف واحد"),
         ("p", "The Consumer Price Index (CPI) is published monthly by the Bureau of Labor Statistics and tracks the prices of a basket of goods and services. "
               "The Personal Consumption Expenditures (PCE) price index, from the Commerce Department, is broader and is the one the Federal Reserve targets "
               "at 2%. Both are reported as headline (everything) and core (excluding volatile food and energy). Economists focus on core because it moves "
               "more slowly and better reflects the trend.",
          "يصدر مؤشر أسعار المستهلك (CPI) شهرياً عن مكتب إحصاءات العمل، ويتتبع أسعار سلة من السلع والخدمات. أما مؤشر أسعار نفقات الاستهلاك الشخصي (PCE) "
          "الصادر عن وزارة التجارة فهو أشمل، وهو الذي يستهدف الفيدرالي إبقاءه عند 2%. ويُعلن كلاهما بصيغتين: الإجمالي (كل شيء) والأساسي (بدون الغذاء "
          "والطاقة المتقلبين)، ويركز الاقتصاديون على الأساسي لأنه أبطأ حركة ويعكس الاتجاه بشكل أفضل."),
         ("chart", "cpi", ("Live: US inflation, year over year (headline and core CPI).", "مباشر: التضخم الأمريكي على أساس سنوي (CPI الإجمالي والأساسي).")),
         ("h", "Why stocks care", "لماذا تهتم الأسهم"),
         ("p", "Hot inflation reports push up bond yields because investors expect the Fed to keep rates higher for longer. That lowers the value of future "
               "profits and hits expensive growth stocks hardest. Cooling inflation does the opposite. Over long periods, however, stocks have been one of the "
               "better protections against inflation, because companies can raise prices and grow earnings along with the economy.",
          "تقارير التضخم المرتفعة ترفع عوائد السندات لأن المستثمرين يتوقعون إبقاء الفيدرالي الفائدة مرتفعة لفترة أطول، وهذا يخفض قيمة الأرباح المستقبلية "
          "ويضرب أسهم النمو مرتفعة التقييم أكثر من غيرها، وتباطؤ التضخم يفعل العكس. ومع ذلك كانت الأسهم على المدى الطويل من أفضل وسائل الحماية من التضخم، "
          "لأن الشركات تستطيع رفع أسعارها وتنمية أرباحها مع نمو الاقتصاد."),
         ("h", "Who wins and who loses", "من يستفيد ومن يتضرر"),
         ("list", [("Usually hurt: long-term bonds, cash savings, and companies without pricing power.",
                    "المتضررون عادة: السندات طويلة الأجل، والمدخرات النقدية، والشركات التي لا تستطيع رفع أسعارها."),
                   ("Often resilient: energy and materials producers, and companies with strong brands.",
                    "الأكثر صموداً غالباً: شركات الطاقة والمواد الأولية، والشركات ذات العلامات التجارية القوية."),
                   ("Watch the surprise: the report versus economists' forecasts drives the day's move.",
                    "راقب المفاجأة: الرقم الفعلي مقارنة بتوقعات الاقتصاديين هو ما يحرك السوق في ذلك اليوم.")]),
         ("note", "The Economy page shows the latest CPI, core CPI and PCE readings: green when improving and red when worsening.",
          "صفحة الاقتصاد تعرض آخر قراءات CPI والتضخم الأساسي وPCE: أخضر عند التحسن وأحمر عند التراجع.")],
     "related": ["economy", "news"]},

    {"id": "earnings", "cat": "markets", "icon": "request_quote", "mins": 6,
     "title": ("Earnings Season Decoded: What Really Moves a Stock", "موسم الأرباح: ما الذي يحرك السهم فعلاً"),
     "dek": ("Four times a year, companies open their books. A beat is not always good news; here is how professionals read a report.",
             "أربع مرات في السنة تكشف الشركات دفاترها، وتجاوز التوقعات ليس دائماً خبراً جيداً. إليك كيف يقرأ المحترفون التقرير."),
     "takeaways": [("The market compares results with analysts' estimates, not with last year.", "السوق يقارن النتائج بتقديرات المحللين، وليس بالعام الماضي."),
                   ("Guidance for the next quarter often matters more than the quarter just reported.", "التوقعات للربع القادم غالباً أهم من الربع المعلن."),
                   ("Options prices show the move the market expects; big surprises can exceed it.",
                    "أسعار الخيارات توضح حجم الحركة التي يتوقعها السوق، والمفاجآت الكبيرة قد تتجاوزها.")],
     "body": [
         ("h", "The calendar", "التقويم"),
         ("p", "Most large US companies report within about six weeks after each quarter ends, so earnings seasons cluster in January to February, April to "
               "May, July to August and October to November. Big banks usually go first, and the mega-cap technology names follow a couple of weeks later. "
               "Reports come before the market opens or after it closes, so the biggest moves often happen as gaps at the next open.",
          "تعلن أغلب الشركات الأمريكية الكبرى نتائجها خلال نحو ستة أسابيع بعد نهاية كل ربع، لذلك تتركز مواسم الأرباح في يناير-فبراير وأبريل-مايو ويوليو-أغسطس "
          "وأكتوبر-نوفمبر. تبدأ البنوك الكبرى عادة، ثم تتبعها شركات التقنية العملاقة بعد أسبوعين تقريباً. وتصدر التقارير قبل افتتاح السوق أو بعد إغلاقه، "
          "لذلك تحدث أكبر الحركات غالباً كفجوات سعرية عند الافتتاح التالي."),
         ("h", "Four numbers to check", "أربعة أرقام تستحق التدقيق"),
         ("list", [("Revenue versus estimates: are customers really buying more?", "الإيرادات مقارنة بالتقديرات: هل يشتري العملاء أكثر فعلاً؟"),
                   ("Earnings per share (EPS) versus estimates, and the quality of the beat (any one-time items?).",
                    "ربحية السهم مقارنة بالتقديرات، وجودة هذا التجاوز (هل فيه بنود لمرة واحدة؟)."),
                   ("Margins: is the company keeping more of each dollar of sales?", "الهوامش: هل تحتفظ الشركة بجزء أكبر من كل دولار مبيعات؟"),
                   ("Guidance: management's forecast for the next quarter or year.", "التوجيهات: توقعات الإدارة للربع أو العام القادم.")]),
         ("h", "Why good results can sink a stock", "لماذا قد يهبط السهم رغم نتائج جيدة"),
         ("p", "Around three quarters of S&P 500 companies typically beat their earnings estimates, partly because companies guide analysts toward numbers they "
               "can beat. So a small beat is often already priced in. What surprises investors is a large beat combined with raised guidance ('beat and "
               "raise'), or a miss and a cut. When expectations are sky-high, even strong results can trigger selling if growth is slowing.",
          "عادة ما يتجاوز نحو ثلاثة أرباع شركات مؤشر S&P 500 تقديرات الأرباح، ويرجع ذلك جزئياً إلى أن الشركات توجّه المحللين نحو أرقام تستطيع تجاوزها، لذلك "
          "يكون التجاوز الصغير غالباً مسعّراً مسبقاً. ما يفاجئ المستثمرين هو تجاوز كبير مع رفع التوقعات، أو إخفاق مع خفضها. وعندما تكون التوقعات مرتفعة جداً "
          "قد تؤدي حتى النتائج القوية إلى البيع إذا كان النمو يتباطأ."),
         ("h", "The expected move", "الحركة المتوقعة"),
         ("p", "Before a report, options become more expensive because traders pay up for protection. The price of an at-the-money straddle (a call plus a put) "
               "roughly equals the move the market expects. If a stock usually moves 4% on earnings and options imply 8%, the market is nervous. After the "
               "report implied volatility usually collapses, which is why buying options just before earnings is often a losing trade even when you guess "
               "the direction right.",
          "قبل التقرير ترتفع أسعار الخيارات لأن المتداولين يدفعون أكثر مقابل الحماية، وسعر عقدي الشراء والبيع عند سعر السهم الحالي (Straddle) يساوي تقريباً "
          "حجم الحركة التي يتوقعها السوق. فإذا كان السهم يتحرك عادة 4% مع النتائج بينما تشير الخيارات إلى 8% فالسوق متوتر. وبعد التقرير ينهار التذبذب "
          "الضمني غالباً، ولهذا يخسر كثيرون عند شراء الخيارات قبل النتائج مباشرة حتى لو أصابوا الاتجاه."),
         ("note", "Every stock page shows its earnings history and analyst estimates, and the Options page shows implied volatility.",
          "كل صفحة سهم تعرض تاريخ أرباحه وتقديرات المحللين، وصفحة الخيارات تعرض التذبذب الضمني.")],
     "related": ["stock", "options"]},

    {"id": "drawdowns", "cat": "investing", "icon": "trending_down", "mins": 5,
     "title": ("Market Drawdowns: How Often Stocks Fall and How They Recover", "تراجعات السوق: كم مرة تهبط الأسهم وكيف تتعافى"),
     "dek": ("Declines are the price of admission for long-term returns. Knowing how normal they are makes them easier to sit through.",
             "التراجعات هي ثمن الدخول لعوائد المدى الطويل، ومعرفة أنها طبيعية تجعل تحمّلها أسهل."),
     "takeaways": [("Pullbacks of 5% or more happen several times in a typical year.", "التراجعات بنسبة 5% أو أكثر تحدث عدة مرات في السنة المعتادة."),
                   ("Bear markets (20% or more) have come roughly every five to six years on average.",
                    "الأسواق الهابطة (20% أو أكثر) جاءت في المتوسط مرة كل خمس إلى ست سنوات تقريباً."),
                   ("Missing the best recovery days can cut long-term returns dramatically.", "تفويت أفضل أيام التعافي قد يخفض العائد طويل الأجل بشكل كبير.")],
     "body": [
         ("h", "Drops are normal", "الهبوط أمر طبيعي"),
         ("p", "Even in years that end with strong gains, the S&P 500 usually suffers a meaningful dip along the way. Historically, 5% pullbacks have occurred "
               "several times a year, 10% corrections roughly once every year or two, and bear markets of 20% or more about once every five to six years on "
               "average. None of this means something is broken; it is how markets price uncertainty.",
          "حتى في السنوات التي تنتهي بمكاسب قوية، يمر مؤشر S&P 500 عادة بهبوط ملحوظ خلال السنة. تاريخياً حدثت تراجعات بنسبة 5% عدة مرات في السنة، "
          "وتصحيحات بنسبة 10% تقريباً مرة كل سنة أو سنتين، وأسواق هابطة بنسبة 20% أو أكثر نحو مرة كل خمس إلى ست سنوات في المتوسط. هذا لا يعني أن شيئاً ما "
          "قد انكسر؛ هكذا يسعّر السوق عدم اليقين."),
         ("chart", "drawdown", ("Live: how far the S&P 500 was below its previous record high on each day.", "مباشر: كم كان مؤشر S&P 500 تحت أعلى قمة سابقة له في كل يوم.")),
         ("h", "Recoveries", "التعافي"),
         ("p", "Recovery times vary enormously. Shallow corrections have often been recovered within a few months, while deep bear markets tied to recessions or "
               "financial crises took years: after the 2000 and 2008 crashes the index needed several years to regain its old peak. Diversification, "
               "rebalancing and investing steadily through the decline are what shorten the wait for an individual investor.",
          "تختلف مدة التعافي كثيراً؛ فالتصحيحات البسيطة كثيراً ما تُعوَّض خلال بضعة أشهر، أما الأسواق الهابطة العميقة المرتبطة بالركود أو الأزمات المالية "
          "فاحتاجت سنوات، فبعد انهيار 2000 و2008 احتاج المؤشر عدة سنوات ليستعيد قمته السابقة. والتنويع وإعادة التوازن والاستمرار في الاستثمار أثناء الهبوط "
          "هي ما يقصّر فترة الانتظار على المستثمر الفرد."),
         ("h", "The cost of panic", "تكلفة الذعر"),
         ("p", "The best days in the market tend to cluster near the worst ones, often in the middle of a sell-off. Investors who sell in fear and wait for "
               "clarity frequently miss the sharp rebounds. Several well-known industry studies have shown that missing just the ten best days over two "
               "decades can cut the total return roughly in half.",
          "تميل أفضل أيام السوق إلى التجمع قرب أسوأ أيامه، وغالباً في منتصف موجة البيع. والمستثمرون الذين يبيعون خوفاً وينتظرون وضوح الرؤية كثيراً ما "
          "تفوتهم الارتدادات الحادة. وقد أظهرت عدة دراسات معروفة في القطاع أن تفويت أفضل عشرة أيام فقط على مدى عقدين قد يخفض العائد الإجمالي إلى النصف تقريباً."),
         ("h", "What to do in a drawdown", "ماذا تفعل أثناء التراجع"),
         ("list", [("Revisit your plan, not the price chart.", "راجع خطتك، وليس رسم السعر."),
                   ("Keep an emergency fund so you are never forced to sell.", "احتفظ بصندوق طوارئ حتى لا تضطر للبيع."),
                   ("If you invest monthly, keep going: you buy more shares at lower prices.", "إذا كنت تستثمر شهرياً فاستمر: ستشتري أسهماً أكثر بأسعار أقل.")])],
     "related": ["sentiment", "seasonality"]},

    {"id": "vix", "cat": "markets", "icon": "speed", "mins": 4,
     "title": ("The VIX: Reading Wall Street's Fear Gauge", "مؤشر VIX: كيف تقرأ مقياس الخوف في وول ستريت"),
     "dek": ("One number tells you how nervous options traders are about the next 30 days.", "رقم واحد يخبرك بمدى قلق متداولي الخيارات بشأن الثلاثين يوماً القادمة."),
     "takeaways": [("The VIX measures the expected 30-day volatility of the S&P 500 from options prices.",
                    "مؤشر VIX يقيس التذبذب المتوقع لمؤشر S&P 500 خلال 30 يوماً من أسعار الخيارات."),
                   ("Its long-run average is around 19 to 20; above 30 signals real fear.", "متوسطه على المدى الطويل حول 19 إلى 20، وفوق 30 يعني خوفاً حقيقياً."),
                   ("Spikes are usually short-lived, and extreme fear has often come near market lows.",
                    "القفزات عادة قصيرة الأجل، والخوف الشديد جاء غالباً قرب قيعان السوق.")],
     "body": [
         ("h", "What it measures", "ماذا يقيس"),
         ("p", "The Cboe Volatility Index is calculated from the prices of S&P 500 options. When investors rush to buy protection, those options get expensive "
               "and the VIX rises. A VIX of 20 means the market expects the S&P 500 to move about 20% over a year on an annualized basis, or roughly 1.25% "
               "per day (20 divided by the square root of 252 trading days).",
          "يُحسب مؤشر التذبذب من بورصة Cboe من أسعار خيارات مؤشر S&P 500. عندما يتسابق المستثمرون لشراء الحماية ترتفع أسعار هذه الخيارات فيرتفع VIX. "
          "وقراءة 20 تعني أن السوق يتوقع حركة سنوية لمؤشر S&P 500 بنحو 20%، أي حوالي 1.25% يومياً (20 مقسوماً على الجذر التربيعي لـ 252 يوم تداول)."),
         ("chart", "vix", ("Live: the VIX over the past two years, with the calm (below 15) and fear (above 30) zones.",
                           "مباشر: مؤشر VIX خلال آخر سنتين مع منطقتي الهدوء (أقل من 15) والخوف (أعلى من 30).")),
         ("h", "How to read the levels", "كيف تقرأ المستويات"),
         ("list", [("Below 15: calm, confident markets. Complacency can build.", "أقل من 15: سوق هادئ وواثق، وقد يتراكم الاطمئنان الزائد."),
                   ("15 to 25: the normal range for most of history.", "من 15 إلى 25: النطاق الطبيعي في أغلب الأوقات."),
                   ("25 to 35: stress. Daily swings of 2% or more become common.", "من 25 إلى 35: توتر، وتصبح الحركات اليومية بنسبة 2% أو أكثر شائعة."),
                   ("Above 35: panic, usually during crashes or crises.", "أعلى من 35: ذعر، يحدث عادة خلال الانهيارات والأزمات.")]),
         ("h", "Using it wisely", "استخدمه بحكمة"),
         ("p", "The VIX tends to rise when stocks fall, so it works as a thermometer for fear. Because fear fades faster than it builds, the index usually drops "
               "back after spikes, and extreme readings have often appeared near market bottoms. It is not a buy signal by itself, but it is a useful reminder "
               "that the moments that feel worst are often when long-term opportunities are best. Note that VIX-linked products (ETFs and futures) behave very "
               "differently from the index and are not suited to long-term holding.",
          "يميل VIX للارتفاع عندما تهبط الأسهم، فهو بمثابة ميزان حرارة للخوف. ولأن الخوف يتلاشى أسرع مما يتكوّن، يعود المؤشر للانخفاض عادة بعد القفزات، "
          "وظهرت القراءات القصوى كثيراً قرب قيعان السوق. ليس إشارة شراء بحد ذاته، لكنه تذكير مفيد بأن اللحظات الأصعب نفسياً كثيراً ما تكون أفضل فرص المدى "
          "الطويل. وانتبه إلى أن المنتجات المرتبطة بمؤشر VIX (الصناديق والعقود الآجلة) تتصرف بشكل مختلف تماماً عن المؤشر ولا تناسب الاحتفاظ طويل الأجل.")],
     "related": ["sentiment", "options"]},

    {"id": "diversify", "cat": "investing", "icon": "donut_small", "mins": 5,
     "title": ("Diversification and Sector Rotation", "التنويع ودوران القطاعات"),
     "dek": ("No sector leads forever. Spreading your bets is the closest thing to a free lunch in investing.",
             "لا يوجد قطاع يقود إلى الأبد، وتوزيع استثماراتك هو أقرب شيء إلى الوجبة المجانية في الاستثمار."),
     "takeaways": [("Sector leadership changes with the economic cycle and interest rates.", "قيادة القطاعات تتغير مع الدورة الاقتصادية وأسعار الفائدة."),
                   ("Owning assets that don't move together lowers risk without necessarily lowering returns.",
                    "امتلاك أصول لا تتحرك معاً يخفض المخاطر دون أن يخفض العائد بالضرورة."),
                   ("A broad index fund gives instant diversification across hundreds of companies.", "صندوق المؤشر الواسع يمنحك تنويعاً فورياً على مئات الشركات.")],
     "body": [
         ("h", "The 11 sectors", "القطاعات الإحدى عشرة"),
         ("p", "The S&P 500 is divided into 11 sectors, from technology and health care to energy and utilities, and each reacts differently to the economy. "
               "Cyclical sectors such as technology, consumer discretionary, industrials and financials tend to lead during expansions. Defensive sectors such "
               "as utilities, consumer staples and health care sell things people need in any economy, so they tend to hold up better in slowdowns. Energy "
               "and materials often follow commodity prices and inflation.",
          "ينقسم مؤشر S&P 500 إلى 11 قطاعاً، من التقنية والرعاية الصحية إلى الطاقة والمرافق، ولكل قطاع رد فعل مختلف تجاه الاقتصاد. فالقطاعات الدورية مثل "
          "التقنية والسلع الكمالية والصناعة والمالية تميل للقيادة في فترات التوسع، بينما تبيع القطاعات الدفاعية مثل المرافق والسلع الأساسية والرعاية الصحية "
          "منتجات يحتاجها الناس في أي ظرف، لذلك تصمد أفضل في فترات التباطؤ. وتتبع الطاقة والمواد الأساسية غالباً أسعار السلع والتضخم."),
         ("chart", "sectors", ("Live: 1-year performance of the sector ETFs. The gap between the best and the worst shows why concentration is risky.",
                               "مباشر: أداء صناديق القطاعات خلال سنة. الفرق بين الأفضل والأسوأ يوضح لماذا التركيز محفوف بالمخاطر.")),
         ("h", "Why diversification works", "لماذا ينجح التنويع"),
         ("p", "When assets do not move in lockstep, losses in one are partly offset by gains, or smaller losses, in another. The portfolio's swings shrink, and "
               "a smoother ride makes it easier to stay invested. Nobel laureate Harry Markowitz called diversification the only free lunch in investing. The "
               "key is correlation: ten technology stocks are not the same as ten stocks from different sectors, regions and asset classes.",
          "عندما لا تتحرك الأصول معاً في نفس الاتجاه، تعوّض مكاسب أحدها أو خسائره الأقل جزءاً من خسائر الآخر، فتقل تقلبات المحفظة، والرحلة الأهدأ تجعل "
          "الاستمرار في الاستثمار أسهل. وقد وصف هاري ماركويتز الحائز على جائزة نوبل التنويع بأنه الوجبة المجانية الوحيدة في الاستثمار. والمفتاح هو الارتباط: "
          "عشرة أسهم تقنية ليست مثل عشرة أسهم من قطاعات ومناطق وفئات أصول مختلفة."),
         ("h", "Practical rules", "قواعد عملية"),
         ("list", [("Keep any single stock to a small share of your portfolio (many advisers suggest 5% or less).",
                    "اجعل وزن أي سهم منفرد صغيراً في محفظتك (كثير من المستشارين يقترحون 5% أو أقل)."),
                   ("Check your sector weights once or twice a year and rebalance if one has grown too large.",
                    "راجع أوزان القطاعات مرة أو مرتين في السنة وأعد التوازن إذا كبر أحدها أكثر من اللازم."),
                   ("Remember that the S&P 500 itself has become concentrated in a handful of giant technology companies.",
                    "تذكّر أن مؤشر S&P 500 نفسه أصبح مركّزاً في عدد قليل من شركات التقنية العملاقة.")])],
     "related": ["overview", "screener"]},

    {"id": "dca", "cat": "investing", "icon": "savings", "mins": 5,
     "title": ("Dollar-Cost Averaging vs. Lump Sum", "الاستثمار الدوري مقابل الدفعة الواحدة"),
     "dek": ("Should you invest everything today or spread it out? The math and the psychology point in different directions.",
             "هل تستثمر المبلغ كله اليوم أم توزعه على فترات؟ الحسابات والنفسية تشيران إلى اتجاهين مختلفين."),
     "takeaways": [("Dollar-cost averaging (DCA) means investing a fixed amount on a schedule.", "الاستثمار الدوري يعني استثمار مبلغ ثابت على فترات منتظمة."),
                   ("Historically a lump sum has won about two-thirds of the time, because markets usually rise.",
                    "تاريخياً تفوقت الدفعة الواحدة في نحو ثلثي الحالات، لأن الأسواق ترتفع في أغلب الأوقات."),
                   ("DCA reduces regret and the risk of investing everything right before a drop.",
                    "الاستثمار الدوري يقلل الندم وخطر استثمار كل المبلغ قبل هبوط مباشرة.")],
     "body": [
         ("h", "How DCA works", "كيف يعمل الاستثمار الدوري"),
         ("p", "With dollar-cost averaging you invest the same amount, say $500, every month regardless of the price. When prices are low your $500 buys more "
               "shares; when prices are high it buys fewer. Over time your average cost per share ends up below the average price over the period. It is also "
               "how most people invest naturally, from each paycheck.",
          "في الاستثمار الدوري تستثمر نفس المبلغ، مثلاً 500 دولار، كل شهر بغض النظر عن السعر. عندما تنخفض الأسعار يشتري مبلغك أسهماً أكثر، وعندما ترتفع "
          "يشتري أقل، ومع الوقت يصبح متوسط تكلفتك للسهم أقل من متوسط السعر خلال الفترة. وهذه هي الطريقة التي يستثمر بها أغلب الناس بشكل طبيعي من رواتبهم."),
         ("chart", "dca", ("Try it: a monthly plan in the S&P 500 (SPY) versus investing the same total on day one.",
                           "جرّبها: خطة شهرية في S&P 500 (SPY) مقابل استثمار نفس المبلغ الإجمالي من اليوم الأول.")),
         ("h", "What the research says", "ماذا تقول الدراسات"),
         ("p", "A widely cited Vanguard study found that investing a lump sum immediately beat spreading it over the following 12 months about two-thirds of "
               "the time in the US, UK and Australian markets. The reason is simple: markets rise more often than they fall, so money invested earlier has "
               "more time to grow. But in the other third of cases, usually just before a big decline, DCA protected investors from painful losses.",
          "وجدت دراسة شهيرة لشركة Vanguard أن استثمار المبلغ دفعة واحدة فوراً تفوق على توزيعه على الـ 12 شهراً التالية في نحو ثلثي الحالات في الأسواق "
          "الأمريكية والبريطانية والأسترالية. والسبب بسيط: الأسواق ترتفع أكثر مما تنخفض، فالمال المستثمر مبكراً يحصل على وقت أطول للنمو. لكن في الثلث الآخر "
          "من الحالات، وعادة قبل هبوط كبير مباشرة، حمى الاستثمار الدوري المستثمرين من خسائر مؤلمة."),
         ("h", "Which should you choose?", "أيهما تختار؟"),
         ("list", [("Investing from your salary? DCA is automatic and excellent: just keep it going.", "تستثمر من راتبك؟ الاستثمار الدوري تلقائي وممتاز: فقط استمر عليه."),
                   ("Received a windfall and can tolerate swings? The odds favor investing it sooner.",
                    "حصلت على مبلغ كبير وتتحمل التقلبات؟ الاحتمالات في صالح استثماره مبكراً."),
                   ("Worried you would panic after a drop? Spreading it over 6 to 12 months is a reasonable compromise.",
                    "تخشى أن تفزع بعد هبوط؟ توزيعه على 6 إلى 12 شهراً حل وسط معقول.")])],
     "related": ["academy", "seasonality"]},

    {"id": "mistakes", "cat": "trading", "icon": "report", "mins": 5,
     "title": ("Seven Costly Mistakes New Traders Make", "سبعة أخطاء مكلفة يقع فيها المتداولون الجدد"),
     "dek": ("Most losses come from a short list of avoidable habits. Fix these first and you are ahead of most beginners.",
             "أغلب الخسائر تأتي من قائمة قصيرة من العادات التي يمكن تجنبها. عالجها أولاً وستسبق أغلب المبتدئين."),
     "takeaways": [("Decide your exit before you enter, and size positions so one loss stays small.", "حدد مخرجك قبل الدخول، واجعل حجم الصفقة بحيث تبقى الخسارة الواحدة صغيرة."),
                   ("Trade less, write down why, and review your results every month.", "تداول أقل، ودوّن سبب كل صفقة، وراجع نتائجك كل شهر."),
                   ("Treat tips and social-media hype with extreme caution.", "تعامل بحذر شديد مع التوصيات وضجيج مواقع التواصل.")],
     "body": [
         ("h", "The seven mistakes", "الأخطاء السبعة"),
         ("list", [("No plan: entering without a reason, a target and a stop. Write all three down first.",
                    "بلا خطة: الدخول بدون سبب وهدف ووقف خسارة. اكتب الثلاثة أولاً."),
                   ("Oversized positions: risking 10% or more on one idea. Professionals typically risk 1 to 2% per trade.",
                    "صفقات أكبر من اللازم: المخاطرة بـ 10% أو أكثر على فكرة واحدة، بينما يخاطر المحترفون عادة بـ 1 إلى 2% للصفقة."),
                   ("Moving the stop: widening a stop loss to avoid taking a loss turns small losses into big ones.",
                    "تحريك الوقف: إبعاد وقف الخسارة لتجنب الخسارة يحوّل الخسائر الصغيرة إلى كبيرة."),
                   ("Averaging down on losers: adding to a falling position without a plan compounds the mistake.",
                    "التعزيز في الصفقات الخاسرة: الإضافة لصفقة هابطة بدون خطة يضاعف الخطأ."),
                   ("Overtrading: fees, spreads and taxes eat returns, and more trades rarely mean more profit.",
                    "الإفراط في التداول: العمولات والفروق والضرائب تأكل العوائد، وكثرة الصفقات نادراً ما تعني ربحاً أكبر."),
                   ("Chasing hype: buying after a stock has already surged on social-media buzz.",
                    "ملاحقة الضجيج: الشراء بعد أن يكون السهم قد قفز بسبب ضجة مواقع التواصل."),
                   ("Revenge trading: trying to win back a loss immediately with a bigger, riskier bet.",
                    "تداول الانتقام: محاولة تعويض الخسارة فوراً بصفقة أكبر وأخطر.")]),
         ("h", "Build good habits instead", "ابنِ عادات جيدة بدلاً منها"),
         ("p", "Keep a trading journal: the date, the reason, the entry, the stop, the target and what happened. After 20 or 30 trades patterns appear: the "
               "setups that work for you, the times of day you trade badly, the mistakes you repeat. Practise new strategies with paper trading or small sizes "
               "first, and backtest rules before trusting them with real money.",
          "احتفظ بسجل تداول: التاريخ والسبب والدخول والوقف والهدف وما حدث. بعد 20 أو 30 صفقة تظهر الأنماط: الإعدادات التي تنجح معك، والأوقات التي يسوء "
          "فيها تداولك، والأخطاء التي تكررها. جرّب الاستراتيجيات الجديدة بحساب تجريبي أو بمبالغ صغيرة أولاً، واختبر القواعد تاريخياً قبل أن تثق بها بأموال حقيقية."),
         ("note", "The Strategy Lab backtests rules on real data, and the Trade Journal keeps score of the bot's trades.",
          "مختبر الاستراتيجيات يختبر القواعد على بيانات حقيقية، وسجل الصفقات يتابع نتائج صفقات البوت.")],
     "related": ["lab", "trades", "academy"]},
]


def article(aid):
    return next((a for a in ARTICLES if a["id"] == aid), None)


def art_svg(cat, uid, h=150):
    """Cover art: category gradient and a soft chart line (the icon badge is drawn on top in HTML)."""
    c1, c2 = CATEGORIES[cat][2], CATEGORIES[cat][3]
    return (f'<svg viewBox="0 0 400 {h}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><linearGradient id="ag{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<rect width="400" height="{h}" fill="url(#ag{uid})"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity=".07"/>' for x, y, r in ((350, 10, 80), (40, h, 70), (230, h + 20, 50)))
            + f'<polyline points="0,{h - 30} 60,{h - 48} 110,{h - 38} 170,{h - 70} 230,{h - 58} 290,{h - 92} 340,{h - 80} 400,{h - 112}" fill="none" '
              f'stroke="#fff" stroke-width="3" opacity=".35" stroke-linejoin="round"/>'
            + "</svg>")


# ---------------------------------------------------------------- one picture per article (drawn scenes, no outside images needed)
def _bg(uid, c1, c2):
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="220" stroke="#fff" stroke-opacity=".06"/>' for x in range(0, 401, 40))
    grid += "".join(f'<line x1="0" y1="{y}" x2="400" y2="{y}" stroke="#fff" stroke-opacity=".05"/>' for y in range(0, 221, 40))
    return (f'<defs><linearGradient id="bg{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
            f'<radialGradient id="gl{uid}" cx=".78" cy=".12" r=".7"><stop offset="0" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="wf{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity=".78"/></linearGradient>'
            f'</defs><rect width="400" height="220" fill="url(#bg{uid})"/><rect width="400" height="220" fill="url(#gl{uid})"/>{grid}')


def _scene_fed(u):          # the central bank building, a rate dial and arrows
    cols = "".join(f'<rect x="{x}" y="92" width="11" height="70" rx="2" fill="url(#wf{u})"/>' for x in range(136, 265, 24))
    return (f'<polygon points="118,88 200,48 282,88" fill="url(#wf{u})"/><rect x="118" y="86" width="164" height="8" fill="#fff" opacity=".9"/>{cols}'
            f'<rect x="110" y="162" width="180" height="8" rx="2" fill="#fff" opacity=".9"/><rect x="98" y="170" width="204" height="9" rx="2" fill="#fff" opacity=".7"/>'
            f'<circle cx="200" cy="70" r="9" fill="none" stroke="#1E3A8A" stroke-width="3" opacity=".6"/>'
            f'<g transform="translate(318 70)"><circle r="30" fill="#fff" opacity=".18"/><circle r="30" fill="none" stroke="#fff" stroke-width="3" opacity=".85"/>'
            f'<text y="11" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="800" fill="#fff">%</text></g>'
            f'<path d="M318 118 v38 M306 144 l12 12 l12 -12" stroke="#FCA5A5" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M62 150 v-40 M50 122 l12 -12 l12 12" stroke="#86EFAC" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<polyline points="20,196 80,188 140,192 200,176 260,182 320,160 380,166" fill="none" stroke="#fff" stroke-width="2.5" opacity=".35"/>')


def _scene_curve(u):        # normal vs inverted yield curve on a chart
    return (f'<rect x="70" y="36" width="260" height="150" rx="14" fill="#0B1020" opacity=".35"/>'
            f'<line x1="92" y1="166" x2="312" y2="166" stroke="#fff" stroke-width="2" opacity=".7"/><line x1="92" y1="56" x2="92" y2="166" stroke="#fff" stroke-width="2" opacity=".7"/>'
            f'<path d="M100 150 C150 110 210 92 305 84" fill="none" stroke="#86EFAC" stroke-width="4" stroke-dasharray="8 7" stroke-linecap="round"/>'
            f'<path d="M100 76 C150 92 220 124 305 136" fill="none" stroke="#FCA5A5" stroke-width="5" stroke-linecap="round"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#fff" stroke="#EF4444" stroke-width="3"/>' for x, y in ((100, 76), (185, 104), (305, 136)))
            + f'<text x="100" y="186" font-family="Arial" font-size="12" font-weight="700" fill="#fff" opacity=".85">3M</text>'
              f'<text x="178" y="186" font-family="Arial" font-size="12" font-weight="700" fill="#fff" opacity=".85">2Y</text>'
              f'<text x="290" y="186" font-family="Arial" font-size="12" font-weight="700" fill="#fff" opacity=".85">10Y</text>'
              f'<g transform="translate(346 56)"><rect x="-22" y="-18" width="44" height="54" rx="6" fill="url(#wf{u})"/>'
              f'<line x1="-12" y1="-4" x2="12" y2="-4" stroke="#1D4ED8" stroke-width="3"/><line x1="-12" y1="6" x2="12" y2="6" stroke="#1D4ED8" stroke-width="3" opacity=".6"/>'
              f'<line x1="-12" y1="16" x2="4" y2="16" stroke="#1D4ED8" stroke-width="3" opacity=".6"/></g>')


def _scene_inflation(u):    # a shopping cart with rising price tags
    tags = "".join(f'<g transform="translate({x} {y}) rotate({r})"><path d="M0 0 h38 l10 12 l-10 12 h-38 z" fill="url(#wf{u})"/>'
                   f'<circle cx="38" cy="12" r="3" fill="#B45309"/><text x="17" y="17" text-anchor="middle" font-family="Arial" font-size="13" font-weight="800" '
                   f'fill="#B91C1C">{t}</text></g>' for x, y, r, t in ((250, 50, -12, "$4"), (292, 84, -8, "$7"), (236, 104, 6, "$9")))
    return (f'<path d="M70 70 h26 l22 78 h112 l18 -58 h-138" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<rect x="112" y="98" width="30" height="34" rx="4" fill="#fff" opacity=".85"/><rect x="148" y="86" width="26" height="46" rx="4" fill="#FDE68A"/>'
            f'<rect x="180" y="104" width="34" height="28" rx="4" fill="#fff" opacity=".7"/>'
            f'<circle cx="130" cy="170" r="11" fill="#fff"/><circle cx="214" cy="170" r="11" fill="#fff"/>{tags}'
            f'<path d="M318 170 L352 128 L372 144 L386 110" fill="none" stroke="#FCA5A5" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M372 110 h14 v14" fill="none" stroke="#FCA5A5" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')


def _scene_earnings(u):     # a quarterly report with bars, a magnifier and a "beat" check
    bars = "".join(f'<rect x="{x}" y="{y}" width="18" height="{150 - y}" rx="3" fill="{c}"/>'
                   for x, y, c in ((142, 118, "#93C5FD"), (166, 104, "#93C5FD"), (190, 96, "#93C5FD"), (214, 78, "#34D399")))
    return (f'<rect x="120" y="34" width="150" height="160" rx="12" fill="url(#wf{u})"/>'
            f'<rect x="138" y="50" width="70" height="8" rx="4" fill="#0F766E"/><rect x="138" y="64" width="46" height="6" rx="3" fill="#94A3B8"/>'
            f'<line x1="138" y1="150" x2="248" y2="150" stroke="#CBD5E1" stroke-width="2"/>{bars}'
            f'<text x="138" y="176" font-family="Arial" font-size="13" font-weight="800" fill="#0F766E">EPS  +12%</text>'
            f'<g transform="translate(292 118)"><circle r="34" fill="#fff" opacity=".15"/><circle r="26" fill="none" stroke="#fff" stroke-width="7"/>'
            f'<line x1="19" y1="19" x2="44" y2="44" stroke="#fff" stroke-width="9" stroke-linecap="round"/></g>'
            f'<g transform="translate(88 70)"><circle r="24" fill="#22C55E"/><path d="M-11 0 l7 8 l14 -15" fill="none" stroke="#fff" stroke-width="5" '
            f'stroke-linecap="round" stroke-linejoin="round"/></g>')


def _scene_drawdowns(u):    # a market fall, the shaded drawdown and the recovery
    pts = "20,70 70,60 110,76 150,64 190,150 220,172 250,160 290,120 330,96 380,58"
    return (f'<path d="M150 64 L190 150 L220 172 L250 160 L290 120 L330 96 L352 64 L150 64 Z" fill="#EF4444" opacity=".25"/>'
            f'<line x1="150" y1="64" x2="372" y2="64" stroke="#fff" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/>'
            f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<line x1="220" y1="70" x2="220" y2="164" stroke="#FCA5A5" stroke-width="3"/><path d="M212 154 l8 12 l8 -12" fill="#FCA5A5"/>'
            f'<rect x="232" y="100" width="62" height="26" rx="13" fill="#B91C1C"/><text x="263" y="118" text-anchor="middle" font-family="Arial" font-size="14" '
            f'font-weight="800" fill="#fff">-34%</text><circle cx="380" cy="58" r="8" fill="#22C55E" stroke="#fff" stroke-width="3"/>'
            f'<text x="316" y="46" font-family="Arial" font-size="12" font-weight="800" fill="#fff" opacity=".9">RECOVERY</text>')


def _scene_vix(u):          # a fear gauge and volatility spikes
    wave = "M20 150 L60 146 L80 132 L96 160 L112 118 L128 170 L146 96 L164 176 L180 126 L200 144 L230 140 L260 146"
    return (f'<path d="{wave}" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>'
            f'<g transform="translate(316 138)"><path d="M-64 0 A64 64 0 0 1 64 0" fill="none" stroke="#22C55E" stroke-width="14" stroke-dasharray="67 300" />'
            f'<path d="M-64 0 A64 64 0 0 1 64 0" fill="none" stroke="#F59E0B" stroke-width="14" stroke-dasharray="0 67 67 300"/>'
            f'<path d="M-64 0 A64 64 0 0 1 64 0" fill="none" stroke="#EF4444" stroke-width="14" stroke-dasharray="0 134 68 300"/>'
            f'<line x1="0" y1="0" x2="42" y2="-38" stroke="#fff" stroke-width="6" stroke-linecap="round"/><circle r="10" fill="#fff"/>'
            f'<text y="30" text-anchor="middle" font-family="Arial" font-size="16" font-weight="800" fill="#fff">VIX</text></g>')


def _scene_diversify(u):    # a portfolio donut with many slices and a shield
    import math
    segs, a0 = [], -90.0
    for share, col in ((28, "#60A5FA"), (22, "#34D399"), (18, "#FBBF24"), (14, "#F472B6"), (10, "#A78BFA"), (8, "#F87171")):
        a1 = a0 + share * 3.6
        r, x0, y0 = 58, 150 + 58 * math.cos(math.radians(a0)), 112 + 58 * math.sin(math.radians(a0))
        x1, y1 = 150 + r * math.cos(math.radians(a1 - 1.5)), 112 + r * math.sin(math.radians(a1 - 1.5))
        segs.append(f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 {1 if share > 50 else 0} 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{col}" stroke-width="30"/>')
        a0 = a1
    legend = "".join(f'<rect x="236" y="{y}" width="90" height="10" rx="5" fill="#fff" opacity=".{o}"/><circle cx="226" cy="{y + 5}" r="5" fill="{c}"/>'
                     for y, o, c in ((70, 85, "#60A5FA"), (92, 7, "#34D399"), (114, 6, "#FBBF24"), (136, 5, "#F472B6")))
    return ("".join(segs) + '<circle cx="150" cy="112" r="30" fill="#fff" opacity=".15"/>' + legend
            + f'<g transform="translate(350 62)"><path d="M0 -22 L20 -14 V2 C20 16 10 24 0 28 C-10 24 -20 16 -20 2 V-14 Z" fill="url(#wf{u})"/>'
              f'<path d="M-8 2 l6 6 l11 -12" fill="none" stroke="#7C2D12" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g>')


def _scene_dca(u):          # a calendar and coin stacks that grow every month
    cells = "".join(f'<rect x="{46 + (i % 4) * 22}" y="{84 + (i // 4) * 20}" width="16" height="14" rx="3" fill="#fff" opacity="{.95 if i in (2, 7, 11) else .45}"/>'
                    for i in range(12))
    stacks = ""
    for j, n in enumerate((2, 3, 5, 7, 9)):
        x = 180 + j * 40
        for k in range(n):
            stacks += f'<ellipse cx="{x}" cy="{178 - k * 10}" rx="15" ry="6" fill="#FCD34D" stroke="#B45309" stroke-width="2"/>'
    return (f'<rect x="34" y="52" width="104" height="124" rx="12" fill="#fff" opacity=".2"/><rect x="34" y="52" width="104" height="24" rx="12" fill="#fff" opacity=".85"/>'
            f'<rect x="54" y="42" width="8" height="18" rx="4" fill="#fff"/><rect x="110" y="42" width="8" height="18" rx="4" fill="#fff"/>{cells}{stacks}'
            f'<path d="M176 92 L220 76 L262 70 L302 50 L344 36" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".85"/>'
            f'<path d="M332 34 h14 v14" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>')


def _scene_mistakes(u):     # a warning sign over a falling chart and a checklist of don'ts
    candles = "".join(f'<line x1="{x}" y1="{y - 14}" x2="{x}" y2="{y + h + 14}" stroke="#fff" stroke-width="2" opacity=".6"/>'
                      f'<rect x="{x - 7}" y="{y}" width="14" height="{h}" rx="2" fill="{c}"/>'
                      for x, y, h, c in ((40, 80, 30, "#34D399"), (66, 92, 34, "#F87171"), (92, 112, 30, "#F87171"), (118, 128, 34, "#F87171"),
                                         (144, 150, 22, "#F87171")))
    lst = "".join(f'<rect x="258" y="{y}" width="92" height="10" rx="5" fill="#fff" opacity=".85"/><g transform="translate(244 {y + 5})">'
                  f'<circle r="8" fill="#EF4444"/><path d="M-4 -4 l8 8 M4 -4 l-8 8" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/></g>'
                  for y in (70, 98, 126, 154))
    return (candles + f'<g transform="translate(196 104)"><path d="M0 -50 L48 36 H-48 Z" fill="#FBBF24" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>'
            f'<rect x="-5" y="-22" width="10" height="34" rx="5" fill="#7C2D12"/><circle cy="24" r="6" fill="#7C2D12"/></g>'
            f'<rect x="230" y="54" width="136" height="128" rx="12" fill="#fff" opacity=".16"/>{lst}')


SCENES = {"fed": _scene_fed, "curve": _scene_curve, "inflation": _scene_inflation, "earnings": _scene_earnings, "drawdowns": _scene_drawdowns,
          "vix": _scene_vix, "diversify": _scene_diversify, "dca": _scene_dca, "mistakes": _scene_mistakes}


def art_scene(aid, cat, uid):
    """The article's own picture: its category colours with a drawing of the topic (the Fed building, the yield curve, a shopping cart...)."""
    c1, c2 = CATEGORIES[cat][2], CATEGORIES[cat][3]
    draw = SCENES.get(aid)
    body = draw(uid) if draw else ""
    return (f'<svg viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" role="img">{_bg(uid, c1, c2)}{body}</svg>')


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.4"
