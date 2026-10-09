"""
terms.py - a small "?" next to every trading term on the site; pressing it explains the term in the page's language.

TERMS holds each term once: its key, its name in both languages, the ways the site writes it (English and Arabic
patterns) and a short explanation in both languages. Two places use it:

- annotate(html): every HTML block the site sends (st.markdown / st.html, hooked in lightmode) gets a
  <span class="gq" data-g="KEY">?</span> right after the first time each term appears in it (not inside links, buttons,
  icons, the landing, the top bar or the assistant);
- client(): the same list for the page script (theme.FX_JS), which opens the explanation when a "?" is pressed and adds
  the "?" to the text Streamlit draws itself (labels, captions, plain text).

Patterns: plain = case-insensitive English, "=..." = case-sensitive English (RSI, Stop, CALL), anything with Arabic letters
= Arabic (a leading و / ف / ب / ل / ك is allowed in front, and ال where written as (?:ال)?). The list order decides
which term wins when two start at the same place (the more specific first).
"""
import re
from functools import lru_cache

_AR = re.compile("[؀-ۿ]")

# (key, English name, Arabic name, [patterns], English explanation, Arabic explanation)
TERMS = [
    # ---- trade plan and risk
    ("trailing_stop", "Trailing stop", "الوقف المتحرك",
     [r"trailing[- ]stops?", r"(?:ال)?وقف (?:ال)?متحرك"],
     "A stop loss that moves up as the price rises and never moves down, so it locks in part of the gain while the trade keeps running.",
     "وقف خسارة يرتفع مع ارتفاع السعر ولا ينزل أبداً، فيحفظ جزء من الربح والصفقة مستمرة."),
    ("time_stop", "Time stop", "الوقف الزمني",
     [r"time[- ]stops?", r"(?:ال)?وقف (?:ال)?زمني"],
     "Closing a trade after a set number of sessions if it hasn't worked yet, so the money is free for better ideas.",
     "إغلاق الصفقة بعد عدد جلسات محدد إذا ما اشتغلت، عشان تتحرر الفلوس لفرص أفضل."),
    ("stop_loss", "Stop loss", "وقف الخسارة",
     [r"stop[- ]?loss(?:es)?", "~=Stops?", "~=STOP", r"وقف (?:ال)?خسارة", r"~(?:ال)?وقف(?! (?:إطلاق|ال?نار|ال?حرب|ال?عمل|ال?تصعيد|ال?قتال|ال?هجمات|ال?عدوان|ال?إنتاج|ال?تصدير|ال?ضخ|ال?مساعدات|ال?دعم|ال?تمويل))"],
     "An exit price set in advance: if the price falls to it, the position is sold so the loss stays small. The site's bots set "
     "it from the ATR, e.g. 'Stop 3 ATR' = three average daily moves below the entry.",
     "سعر خروج تحدده مسبقاً: إذا نزل السعر له يُباع المركز عشان تبقى الخسارة صغيرة. بوتات الموقع تحدده من ATR، مثلاً "
     "«وقف 3 ATR» يعني تحت سعر الدخول بثلاث مرات متوسط الحركة اليومية."),
    ("take_profit", "Take profit", "جني الأرباح",
     [r"take[- ]profits?", r"profit[- ]targets?", r"جني (?:ال)?(?:أرباح|ربح)"],
     "A price set in advance where the position is sold to lock in the gain.",
     "سعر تحدده مسبقاً يُباع عنده المركز عشان تثبّت الربح."),
    ("price_target", "Price target", "السعر المستهدف",
     [r"price targets?", r"(?:ال)?(?:سعر|أسعار) (?:ال)?مستهدف(?:ة)?"],
     "The price analysts expect the stock to reach in about 12 months.",
     "السعر اللي يتوقع المحللون يوصل له السهم خلال 12 شهر تقريباً."),
    ("target", "Target", "الهدف",
     ["~=Targets?(?! Corp)", "~=TARGETS?", r"~(?:ال)?هدف"],
     "The price where the trade plan takes profit. The distance from the entry to the target, against the distance from the "
     "entry to the stop, gives the reward-to-risk.",
     "السعر اللي تجني عنده خطة الصفقة الربح. المسافة من الدخول للهدف مقارنة بالمسافة من الدخول للوقف تعطيك نسبة العائد إلى المخاطرة."),
    ("entry", "Entry", "سعر الدخول",
     ["~=Entry", "~=ENTRY", r"entry price", r"(?:سعر|نقطة) (?:ال)?دخول"],
     "The price at which a trade is opened, the buy price.",
     "السعر اللي تنفتح عنده الصفقة، يعني سعر الشراء."),
    ("rr", "Reward-to-risk (R:R)", "العائد إلى المخاطرة",
     ["R:R", r"reward[- ]to[- ]risk", r"risk[- /]reward", r"reward/risk",
      r"(?:ال)?عائد (?:إلى (?:ال)?مخاطرة|للمخاطرة|مقابل (?:ال)?مخاطرة)", r"(?:ال)?عائد/(?:ال)?مخاطرة"],
     "How much a trade can make for each $1 it risks: (target − entry) ÷ (entry − stop). 2.5 means the target is 2.5 times "
     "farther away than the stop.",
     "كم ممكن تربح الصفقة مقابل كل دولار تخاطر فيه: (الهدف − الدخول) ÷ (الدخول − الوقف). 2.5 يعني الهدف أبعد من الوقف بمرتين ونص."),
    ("risk_per_trade", "Risk per trade", "المخاطرة لكل صفقة",
     [r"risk (?:\d+(?:\.\d+)?% )?per trade", r"(?:ال)?مخاطرة (?:\d+(?:\.\d+)?% )?(?:لكل|في كل|بكل) صفقة", r"مخاطرة (?:ال)?صفقة"],
     "The part of the account you accept to lose if a trade hits its stop, e.g. 1% of $10,000 = $100.",
     "النسبة من الحساب اللي تقبل تخسرها إذا ضربت الصفقة الوقف، مثلاً 1% من 10,000 دولار = 100 دولار."),
    ("position_size", "Position size", "حجم الصفقة",
     [r"position[- ]siz(?:e|es|ing)", r"حجم (?:ال)?(?:صفقة|مركز)"],
     "How much money goes into one trade. Sizing by risk keeps every loss small: shares = money at risk ÷ (entry − stop).",
     "كم مبلغ يدخل في الصفقة الوحدة. لما تحدده حسب المخاطرة تبقى كل خسارة صغيرة: عدد الأسهم = المبلغ اللي تخاطر فيه ÷ (الدخول − الوقف)."),
    ("pnl", "P&L (profit and loss)", "الربح والخسارة",
     [r"P(?:&amp;|&)L", r"profit (?:and|&amp;|&) loss", r"(?:ال)?ربح وال?خسارة", r"(?:ال)?أرباح وال?خسائر"],
     "How much a trade or an account made or lost, in dollars. Realized = closed trades; unrealized = trades still open.",
     "كم ربحت أو خسرت الصفقة أو الحساب بالدولار. المحقق = صفقات مغلقة، وغير المحقق = صفقات لسا مفتوحة."),
    ("slippage", "Slippage", "الانزلاق السعري",
     [r"slippage", r"(?:ال)?انزلاق(?: (?:ال)?سعري)?"],
     "The difference between the price you expected and the price you actually got, mostly in fast markets.",
     "الفرق بين السعر اللي توقعته والسعر اللي فعلاً تنفذت عليه، غالباً في السوق السريع."),
    ("orders", "Market / limit order", "أمر السوق والأمر المحدد",
     [r"(?:limit|market|stop) orders?", r"(?:ال)?أمر (?:ال)?محدد", r"أمر (?:ال)?سوق"],
     "Market order: buy or sell now at the best price available. Limit order: only at your price or better, so it may not fill.",
     "أمر السوق: شراء أو بيع فوراً بأفضل سعر متاح. الأمر المحدد: فقط بسعرك أو أفضل، فممكن ما يتنفذ."),

    ("buying_power", "Buying power", "القوة الشرائية",
     [r"buying power", r"(?:ال)?قوة (?:ال)?شرائية"],
     "How much more you can buy, or sell short, right now with the cash and margin left in the account. Open orders keep their share of it.",
     "كم تقدر تشتري أو تبيع على المكشوف الحين بالكاش والهامش المتبقي في الحساب. الأوامر المفتوحة تحجز نصيبها منه."),
    ("margin_call", "Margin and margin call", "الهامش ونداء الهامش",
     [r"margin calls?", r"maintenance (?:margin|requirement)", r"margin (?:account|used|cushion|requirement)s?", r"نداء (?:ال)?هامش",
      r"حساب (?:ال)?هامش", r"(?:ال)?هامش (?:ال)?(?:مستخدم|آمن|المطلوب)"],
     "In a margin account the broker lends money (to buy) or shares (to sell short). The rules: a short needs 150% of its value in the "
     "account, and equity must stay above 25% of the longs and 30% of the shorts. Below that comes a margin call: add money or close positions.",
     "في حساب الهامش الوسيط يقرضك فلوس (للشراء) أو أسهم (للبيع على المكشوف). القواعد: المكشوف يحتاج 150% من قيمته في الحساب، وقيمة الحساب "
     "لازم تبقى فوق 25% من الشراء و30% من المكشوف. تحت كذا يجي نداء الهامش: تضيف فلوس أو تسكّر مراكز."),
    ("borrow_fee", "Borrow fee", "رسوم الاقتراض",
     [r"borrow(?:ing)? fees?", r"hard[- ]to[- ]borrow", r"رسوم (?:ال)?(?:اقتراض|استلاف)"],
     "What a short seller pays every night to borrow the shares, as a yearly %. Easy-to-borrow stocks cost well under 1%; heavily shorted "
     "ones can cost 10% or more.",
     "اللي يدفعه البائع على المكشوف كل ليلة عشان يستلف الأسهم، كنسبة سنوية. الأسهم السهلة أقل من 1%، والمبيوعة على المكشوف بكثرة ممكن 10% أو أكثر."),
    ("bracket", "Bracket order (OCO)", "الأمر المرفق (OCO)",
     [r"bracket(?: orders?| legs?)?", "=OCO", r"(?:ال)?أمر (?:ال)?مرفق"],
     "A new position sent with its stop loss and take profit attached. When one of the two fills, the other is cancelled (one cancels the other).",
     "مركز جديد ينرسل ومعه وقف الخسارة وجني الأرباح. لما يتنفذ واحد منهم ينلغي الثاني تلقائياً."),
    ("cover", "Buy to cover", "الشراء للتغطية",
     [r"buy to cover", r"short cover(?:ing)?", r"(?:ال)?شراء للتغطية", r"تغطية (?:ال)?(?:مكشوف|مركز (?:ال)?مكشوف)"],
     "Closing a short: buying back the borrowed shares and returning them. The profit is the sale price minus the buy-back price, minus fees.",
     "إغلاق المكشوف: تشتري الأسهم المستلفة وترجعها. ربحك = سعر البيع ناقص سعر الشراء، ناقص الرسوم."),
    ("leverage", "Leverage", "الرافعة المالية",
     [r"leverage", r"(?:ال)?رافعة(?: (?:ال)?مالية)?"],
     "Positions worth more than the account itself (long + short ÷ equity). 2× doubles the gains and the losses.",
     "مراكز قيمتها أكبر من الحساب نفسه (الشراء + المكشوف ÷ قيمة الحساب). 2× تضاعف الأرباح والخسائر."),
    ("var", "Value at Risk (VaR)", "القيمة المعرضة للخطر (VaR)",
     ["=VaR", r"value at risk", r"(?:ال)?قيمة (?:ال)?معرضة للخطر"],
     "The loss of a bad day: 95% VaR is the amount lost on the worst 1 day in 20, measured on past returns.",
     "خسارة يوم سيء: VaR بنسبة 95% هي الخسارة في أسوأ يوم من كل 20 يوم، محسوبة من العوائد السابقة."),
    ("exposure", "Exposure (long, short, net, gross)", "الانكشاف (شراء، مكشوف، صافي، إجمالي)",
     [r"(?:gross|net|long|short) exposure", r"~exposure", r"(?:ال)?انكشاف(?: (?:ال)?(?:إجمالي|صافي))?"],
     "How much money rides on the market, as % of equity: long minus short is the net (the bet on the market's direction), long plus short the gross.",
     "قد إيش فلوسك معرضة للسوق كنسبة من الحساب: الشراء ناقص المكشوف = الصافي (رهانك على اتجاه السوق)، والشراء زائد المكشوف = الإجمالي."),

    # ---- results of a strategy
    ("sharpe", "Sharpe ratio", "نسبة شارب",
     [r"sharpe(?: ratio)?", r"(?:نسبة )?شارب"],
     "Return per unit of risk (yearly return ÷ yearly volatility). Above 1 is good, above 2 very good; it compares strategies fairly.",
     "العائد لكل وحدة مخاطرة (العائد السنوي ÷ التذبذب السنوي). فوق 1 جيد وفوق 2 ممتاز، ويقارن الاستراتيجيات بعدل."),
    ("drawdown", "Max drawdown (max drop)", "أكبر هبوط",
     [r"max(?:imum)?\\.? (?:drops?|drawdowns?)", r"worst drops?", r"~drawdowns?", r"(?:أكبر|أقصى|أسوأ) (?:هبوط|تراجع|انخفاض)"],
     "The biggest fall from a peak to the low that followed, in %. It shows the worst stretch you would have lived through.",
     "أكبر نزول من قمة لأدنى نقطة بعدها، بالنسبة المئوية. يبين أسوأ فترة كنت بتعيشها."),
    ("cagr", "Yearly return (CAGR)", "العائد السنوي",
     ["=CAGR", r"~yearly(?: returns?)?", r"annual(?:ized)? returns?", r"(?:ال)?عائد (?:ال)?سنوي", r"~سنوياً"],
     "The steady growth per year that turns the starting value into the final value (compound annual growth rate).",
     "النمو السنوي الثابت اللي يحوّل القيمة في البداية للقيمة في النهاية (معدل النمو السنوي المركب)."),
    ("win_rate", "Win rate", "نسبة الصفقات الرابحة",
     [r"win(?:ning)? rate", r"hit rate", r"\d+% winners", r"نسبة (?:ال)?(?:فوز|نجاح|صفقات (?:ال)?رابحة)", r"\d+% (?:منها )?رابحة"],
     "The share of closed trades that made money. A low win rate can still be profitable when the winners are much bigger than the losers.",
     "نسبة الصفقات المغلقة اللي ربحت. نسبة منخفضة ممكن تكون مربحة إذا الأرباح أكبر بكثير من الخسائر."),
    ("buy_hold", "Buy and hold", "الشراء والاحتفاظ",
     [r"buy[- ](?:and|&amp;|&)[- ]hold", r"(?:ال)?شراء وال?احتفاظ"],
     "Buying and simply keeping the stocks, with no selling. The site compares every bot with it: a bot is only worth it if it "
     "beats doing nothing.",
     "تشتري الأسهم وتخليها بدون بيع. الموقع يقارن كل بوت فيه: البوت ما يستاهل إلا إذا تفوق على إنك ما تسوي شي."),
    ("paper", "Paper trading", "التداول الافتراضي",
     [r"paper[- ]trad(?:ing|es?)", r"paper bots?", r"virtual money", r"(?:ال)?تداول (?:ال)?افتراضي", r"(?:فلوس|أموال) افتراضية",
      r"(?:ال)?بوتات (?:ال)?افتراضية"],
     "Trading with pretend money on real prices: you learn and test strategies without risking real money.",
     "تداول بفلوس وهمية على أسعار حقيقية: تتعلم وتجرّب الاستراتيجيات بدون ما تخاطر بفلوس حقيقية."),
    ("forward_test", "Forward test", "الاختبار الأمامي",
     [r"forward[- ]test(?:s|ing|ed)?", r"(?:ال)?اختبار (?:ال)?أمامي"],
     "Running a strategy from today on and recording each signal as it happens. Unlike a backtest it can't be tuned to the past, "
     "so it is the honest proof.",
     "تشغيل الاستراتيجية من اليوم ورايح وتسجيل كل إشارة وقت ما تصير. بعكس الاختبار التاريخي ما ينفع تفصّله على الماضي، فهو الدليل الصادق."),
    ("backtest", "Backtest", "الاختبار التاريخي",
     [r"back[- ]?test(?:s|ing|ed)?", r"historical simulation", r"(?:ال)?اختبار (?:ال)?تاريخي", r"(?:ال)?محاكاة (?:ال)?تاريخية"],
     "Testing a strategy on past prices to see how it would have done. Useful, but a strategy tuned too closely to the past "
     "often fails later.",
     "اختبار الاستراتيجية على أسعار سابقة عشان تعرف كيف كان أداؤها. مفيد، بس الاستراتيجية المفصّلة على الماضي كثير تفشل بعدين."),
    ("oos", "Out-of-sample", "خارج العينة",
     [r"out[- ]of[- ]sample", r"خارج (?:ال)?عينة"],
     "Data a strategy was not built on (here: 2020 to now, after building on 2010–2019). Results there are the realistic ones.",
     "بيانات ما انبنت عليها الاستراتيجية (هنا: من 2020 لين اليوم بعد ما انبنت على 2010–2019). نتائجها هي الواقعية."),
    ("regime", "Market regime", "حالة السوق",
     [r"market regimes?", r"~regimes?", r"حال(?:ة|ات) (?:ال)?سوق"],
     "The market's state: bull, sideways, bear or panic. The site's bots size their trades by it, trading smaller (or not at "
     "all) in a panic.",
     "حالة السوق: صاعد أو عرضي أو هابط أو ذعر. بوتات الموقع تحدد حجم صفقاتها حسبها، وتصغّرها أو توقف وقت الذعر."),

    # ---- indicators
    ("atr", "ATR (Average True Range)", "متوسط المدى الحقيقي",
     ["=ATR", r"average true range", r"متوسط (?:ال)?مدى (?:ال)?حقيقي"],
     "The average size of a stock's daily move (over 14 days), in dollars. Used to place stops: wider for jumpy stocks, tighter "
     "for calm ones.",
     "متوسط حجم حركة السهم اليومية (خلال 14 يوم) بالدولار. يُستخدم لتحديد الوقف: أوسع للأسهم كثيرة الحركة، وأضيق للهادية."),
    ("rsi", "RSI", "مؤشر القوة النسبية",
     ["=RSI", r"relative strength index", r"مؤشر (?:ال)?قوة (?:ال)?نسبية"],
     "Relative Strength Index: momentum from 0 to 100 over the last 14 days. Above 70 is often called overbought, below 30 oversold.",
     "مؤشر القوة النسبية: يقيس الزخم من 0 إلى 100 خلال آخر 14 يوم. فوق 70 يُعتبر تشبع شرائي، وتحت 30 تشبع بيعي."),
    ("rs", "RS rating (relative strength)", "القوة النسبية",
     ["~=RS(?: rating)?", r"relative strength(?: rating)?", r"(?:ال)?قوة (?:ال)?نسبية"],
     "How a stock did against the whole market over the past months, ranked from 1 to 99. 90 means it beat 90% of stocks.",
     "أداء السهم مقارنة بالسوق كله خلال الشهور الماضية، مرتب من 1 إلى 99. 90 يعني تفوق على 90% من الأسهم."),
    ("macd", "MACD", "الماكد",
     ["=MACD", r"(?:ال)?ماكد"],
     "The gap between the 12- and 26-day exponential averages, with a 9-day signal line. Crossing above the signal hints that "
     "momentum is turning up.",
     "الفرق بين المتوسطين الأسيين 12 و26 يوم، مع خط إشارة 9 أيام. لما يقطع خط الإشارة لفوق يلمّح إن الزخم بدأ يصعد."),
    ("golden_cross", "Golden cross / death cross", "التقاطع الذهبي",
     [r"golden cross(?:es)?", r"death cross(?:es)?", r"(?:ال)?تقاطع (?:ال)?ذهبي", r"تقاطع (?:ال)?موت"],
     "Golden cross: the 50-day average crosses above the 200-day, a long-term bullish sign. Death cross: the opposite.",
     "التقاطع الذهبي: متوسط 50 يوم يقطع فوق متوسط 200 يوم، إشارة صعود طويلة. تقاطع الموت: العكس."),
    ("moving_average", "Moving average (SMA / EMA)", "المتوسط المتحرك",
     [r"moving averages?", "=(?:SMA|EMA)s?(?: ?\d+)?", r"(?:9|10|20|21|50|100|150|200)[- ]day (?:(?:moving )?average|SMA|EMA|MA)", r"~(?:9|10|20|21|50|100|150|200)[- ]day", r"(?:ال)?متوسط(?:ات)? (?:ال)?متحرك(?:ة)?", r"~(?:ال)?متوسط (?:الـ ?)?\\d+(?: يوم(?:اً)?)?"],
     "The average closing price of the last N days, redrawn every day. The 50-day shows the medium trend, the 200-day the long "
     "one; an SMA weighs every day the same, an EMA weighs recent days more.",
     "متوسط أسعار الإغلاق لآخر N يوم، ويتحدث كل يوم. متوسط 50 يوم يبين الاتجاه المتوسط و200 يوم الاتجاه الطويل؛ SMA يعطي "
     "كل الأيام نفس الوزن، وEMA يعطي الأيام الأخيرة وزن أكبر."),
    ("bollinger", "Bollinger Bands", "نطاقات بولينجر",
     [r"bollinger(?: bands?)?", r"(?:نطاقات|حزم|باندات) بول?ينجر", r"بول?ينجر"],
     "Bands two standard deviations above and below the 20-day average. A price near the upper band is stretched; bands "
     "squeezing together often come before a big move.",
     "نطاقات فوق وتحت متوسط 20 يوم بانحرافين معياريين. السعر قرب النطاق العلوي ممتد، وتضيّق النطاقات غالباً يسبق حركة قوية."),
    ("vwap", "VWAP", "متوسط السعر المرجح بالحجم",
     ["=VWAP", r"متوسط (?:ال)?سعر (?:ال)?مرجح بال?حجم"],
     "Volume-weighted average price: the average price paid today, each trade weighted by its size. Above the VWAP, buyers "
     "have the upper hand for the day.",
     "متوسط السعر المرجّح بالحجم: متوسط السعر اللي انشرى فيه السهم اليوم مع وزن كل صفقة بحجمها. فوقه يعني المشترين مسيطرين في اليوم."),
    ("adx", "ADX", "مؤشر قوة الاتجاه",
     ["=ADX", r"average directional index"],
     "Average Directional Index: how strong a trend is (not its direction), from 0 to 100. Above 25 is a real trend, below 20 a "
     "sideways market.",
     "مؤشر متوسط الاتجاه: يقيس قوة الاتجاه (مو اتجاهه) من 0 إلى 100. فوق 25 اتجاه حقيقي، وتحت 20 سوق عرضي."),
    ("obv", "OBV (On-Balance Volume)", "حجم التوازن",
     ["=OBV", r"on[- ]balance volume", r"حجم (?:ال)?توازن"],
     "Adds the day's volume on up days and subtracts it on down days. A rising OBV suggests money is flowing into the stock.",
     "يضيف حجم اليوم في أيام الصعود ويطرحه في أيام النزول. ارتفاعه يلمّح إن الفلوس داخلة على السهم."),
    ("mfi", "MFI (Money Flow Index)", "مؤشر تدفق الأموال",
     ["=MFI", r"money flow index", r"مؤشر تدفق (?:ال)?(?:أموال|سيولة)"],
     "Like the RSI but with volume in it, from 0 to 100. Above 80 is overbought, below 20 oversold.",
     "مثل RSI بس يدخل الحجم في الحساب، من 0 إلى 100. فوق 80 تشبع شرائي، وتحت 20 تشبع بيعي."),
    ("cci", "CCI", "مؤشر قناة السلع",
     ["=CCI", r"commodity channel index"],
     "Commodity Channel Index: how far the price is from its average, in units of its usual move. Above +100 is strong, below −100 weak.",
     "مؤشر قناة السلع: كم السعر بعيد عن متوسطه مقارنة بحركته المعتادة. فوق +100 قوة، وتحت −100 ضعف."),
    ("stochastic", "Stochastic", "مؤشر الستوكاستك",
     [r"stochastic(?: oscillator)?", r"(?:ال)?ستوكاستك"],
     "Where today's close sits inside the range of the last 14 days, from 0 to 100. Above 80 is near the top of the range, below "
     "20 near the bottom.",
     "وين إغلاق اليوم من مدى آخر 14 يوم، من 0 إلى 100. فوق 80 قريب من أعلى المدى، وتحت 20 قريب من أسفله."),
    ("overbought", "Overbought / oversold", "التشبع الشرائي والبيعي",
     [r"overbought", r"oversold", r"(?:ال)?تشبع (?:ال)?(?:شرائي|بيعي)"],
     "Overbought: the price rose so fast it may pause or dip (RSI above 70). Oversold: it fell so fast it may bounce (RSI below 30).",
     "تشبع شرائي: السعر صعد بسرعة لدرجة ممكن يرتاح أو ينزل (RSI فوق 70). تشبع بيعي: نزل بسرعة لدرجة ممكن يرتد (RSI تحت 30)."),
    ("pivot", "Pivot points", "نقاط الارتكاز",
     [r"pivot points?", r"~pivots?", r"(?:نقاط|نقطة) (?:ال)?ارتكاز"],
     "Levels worked out from yesterday's high, low and close that traders watch as possible support and resistance today.",
     "مستويات محسوبة من أعلى وأدنى وإغلاق أمس، يراقبها المتداولين كدعم ومقاومة محتملة اليوم."),
    ("heikin", "Heikin Ashi", "هايكن آشي",
     [r"heikin[- ]ashi", r"هايكن آشي"],
     "Smoothed candles built from averages, which make a trend easier to see as a string of same-colour candles.",
     "شموع منعّمة مبنية على متوسطات، تسهّل رؤية الاتجاه كسلسلة شموع بنفس اللون."),
    ("candle", "Candlestick", "الشمعة",
     [r"candlesticks?", r"~candles?", r"(?:ال)?شم(?:عة|وع) (?:ال)?يابانية", r"~(?:ال)?شم(?:عة|وع)"],
     "A bar that shows one period's open, high, low and close. Green = it closed higher than it opened, red = lower.",
     "شكل يبين الافتتاح والأعلى والأدنى والإغلاق لفترة وحدة. الأخضر يعني أغلق أعلى من افتتاحه، والأحمر أقل."),

    # ---- setups and price action
    ("donchian", "Donchian breakout (Turtle)", "اختراق دونشيان",
     [r"donchian(?: breakout| channel)?", r"~turtles?", r"دونشيان", r"~(?:ال)?سلاحف"],
     "Buying when the price closes above its highest high of the last 20 (or 55) days, the famous 'Turtle' rule, and exiting on "
     "a new low.",
     "الشراء لما يغلق السعر فوق أعلى قمة لآخر 20 (أو 55) يوم، وهي قاعدة «السلاحف» المشهورة، والخروج على قاع جديد."),
    ("orb", "Opening range breakout", "اختراق نطاق الافتتاح",
     [r"opening[- ]range(?: breakout)?", "~=ORB", r"(?:ال)?نطاق (?:ال)?افتتاحي", r"(?:نطاق|اختراق) (?:ال)?افتتاح"],
     "Mark the high and low of the first minutes after the open, then trade the break out of that range.",
     "تحدد أعلى وأدنى سعر في أول دقائق بعد الافتتاح، وتتداول على كسر هذا النطاق."),
    ("breakout", "Breakout", "الاختراق",
     [r"~break[- ]?outs?", r"~breaking out", r"~(?:ال)?اختراق(?:ات)?"],
     "The price pushing above a recent high or a resistance, best on strong volume; often the start of a new move up.",
     "دفع السعر فوق قمة قريبة أو مقاومة، والأفضل بحجم قوي، وغالباً يكون بداية موجة صعود جديدة."),
    ("pullback", "Pullback", "الارتداد",
     [r"~pull[- ]?backs?", r"~(?:ال)?ارتداد(?:ات)?"],
     "A short dip inside an uptrend. Buying a pullback means entering a strong stock after it rests, at a better price.",
     "نزول قصير داخل اتجاه صاعد. شراء الارتداد يعني تدخل سهم قوي بعد ما يرتاح، بسعر أفضل."),
    ("mean_reversion", "Mean reversion", "العودة للمتوسط",
     [r"mean[- ]reversion", r"(?:ال)?عودة (?:إلى |لل)(?:ال)?متوسط"],
     "The idea that a price stretched far from its average tends to come back toward it, so you buy sharp dips and sell sharp jumps.",
     "فكرة إن السعر لما يبتعد كثير عن متوسطه يميل يرجع له، فتشتري النزول الحاد وتبيع الصعود الحاد."),
    ("trend", "Trend (uptrend / downtrend)", "الاتجاه",
     [r"trend[- ]following", r"up[- ]?trends?", r"down[- ]?trends?", r"long[- ]term trend", r"(?:ال)?اتجاه (?:ال)?(?:صاعد|هابط|طويل)",
      r"تتبع (?:ال)?اتجاه"],
     "The general direction of a price over time: higher highs and higher lows = an uptrend. Trend following buys strength and "
     "rides it until it ends.",
     "الاتجاه العام للسعر مع الوقت: قمم وقيعان أعلى = اتجاه صاعد. تتبع الاتجاه يشتري القوة ويركبها لين تنتهي."),
    ("momentum", "Momentum", "الزخم",
     [r"~momentum", r"~(?:ال)?زخم"],
     "The speed of a price move. Stocks that rose strongly in recent months tend to keep beating the market for a while.",
     "سرعة حركة السعر. الأسهم اللي صعدت بقوة في الشهور الأخيرة تميل تستمر متفوقة على السوق لفترة."),
    ("support", "Support", "الدعم",
     [r"support (?:levels?|zones?|lines?)", "~=Support", "~=SUPPORT", r"~(?:ال)?دعم"],
     "A price area where falls have stopped before because buyers stepped in. A clear break below it is a warning sign.",
     "منطقة سعرية توقف عندها النزول قبل لأن المشترين دخلوا. كسرها بوضوح لتحت علامة تحذير."),
    ("resistance", "Resistance", "المقاومة",
     [r"resistance (?:levels?|zones?|lines?)", r"~resistance", r"~(?:ال)?مقاومة"],
     "A price area where rises have stalled before because sellers stepped in. A break above it on strong volume is a breakout.",
     "منطقة سعرية توقف عندها الصعود قبل لأن البائعين دخلوا. اختراقها لفوق بحجم قوي يسمى اختراق."),
    ("gap", "Gap", "الفجوة السعرية",
     [r"~gap[- ]?(?:up|down)s?", "~=Gaps?", "~=GAPS?", r"~(?:ال)?فجو(?:ة|ات)(?: (?:ال)?سعرية)?"],
     "When a stock opens well above or below the previous close and leaves an empty space on the chart, usually after news.",
     "لما يفتح السهم أعلى أو أقل بوضوح من إغلاق أمس ويترك فراغ في الشارت، وغالباً بعد خبر."),
    ("squeeze", "Squeeze", "الضغط",
     [r"(?:short|gamma|volatility) squeezes?", r"~squeezes?", r"(?:ال)?ضغط (?:ال)?قسري", r"موجة شراء قسرية"],
     "Short squeeze: a rising price forces short sellers to buy back, which pushes it higher still. A volatility squeeze is when "
     "the price range narrows before a big move.",
     "موجة الضغط: صعود السعر يجبر البائعين على المكشوف يشترون، فيرتفع أكثر. وضغط التذبذب يعني ضيق نطاق السعر قبل حركة كبيرة."),
    ("accumulation", "Accumulation", "التجميع",
     [r"~accumulation(?:/distribution)?", r"~(?:ال)?تجميع"],
     "Big investors quietly buying a stock, seen as more volume on up days than on down days.",
     "مستثمرين كبار يشترون السهم بهدوء، ويبان من حجم أكبر في أيام الصعود مقارنة بأيام النزول."),
    ("correction", "Correction", "التصحيح",
     [r"(?:market|stock) corrections?", r"~corrections?", r"~(?:ال)?تصحيح"],
     "A fall of 10% or more from a recent high, short of a bear market (20%).",
     "نزول 10% أو أكثر من قمة قريبة، أقل من السوق الهابط (20%)."),
    ("high52", "52-week high / low", "قمة وقاع 52 أسبوع",
     [r"52[- ]?(?:weeks?|wks?|w)(?: (?:highs?|lows?))?", r"(?:أعلى|أدنى|قمة|قاع) (?:سعر في )?52 أسبوع(?:اً)?", r"52 أسبوع(?:اً)?"],
     "The highest (or lowest) price of the past year. Stocks near their 52-week high are usually the market's leaders.",
     "أعلى (أو أدنى) سعر خلال السنة الماضية. الأسهم القريبة من قمة 52 أسبوع غالباً تكون قيادية."),

    # ---- trading activity
    ("rel_volume", "Relative volume", "الحجم النسبي",
     [r"rel(?:\.|ative)? ?vol(?:ume)?", "=RVOL", r"(?:ال)?حجم (?:ال)?نسبي"],
     "Today's volume ÷ the stock's usual volume. 2× means twice the normal trading: something is drawing attention.",
     "حجم تداول اليوم ÷ حجم السهم المعتاد. 2× يعني ضعف التداول الطبيعي، يعني فيه شي جاذب الانتباه."),
    ("volume", "Volume", "حجم التداول",
     [r"trading volume", r"~volume", r"حجم (?:ال)?تداول"],
     "How many shares traded in a period. A big move on high volume is more trustworthy than one on thin volume.",
     "عدد الأسهم المتداولة خلال فترة. الحركة القوية مع حجم عالي أوثق من حركة بحجم ضعيف."),
    ("liquidity", "Liquidity", "السيولة",
     [r"~liquidity", r"~(?:ال)?سيولة"],
     "How easily you can buy or sell without moving the price. Big, heavily traded stocks are liquid.",
     "سهولة الشراء والبيع بدون ما تحرك السعر. الأسهم الكبيرة كثيرة التداول سيولتها عالية."),
    ("spread", "Bid / ask spread", "السبريد",
     [r"bid[- /]ask(?: spread)?", "~=Spread", "~=Bid", "~=BID", "~=ASK", r"(?:ال)?سبريد"],
     "The bid is the best price buyers offer, the ask the best price sellers want; the gap between them (the spread) is a hidden "
     "cost, wide in thinly traded stocks and options.",
     "سعر العرض (Bid) أفضل سعر يدفعه المشترين، وسعر الطلب (Ask) أفضل سعر يبيع فيه البائعين؛ والفرق بينهم (السبريد) تكلفة خفية، "
     "وتكون واسعة في الأسهم والخيارات قليلة التداول."),
    ("short", "Short selling", "البيع على المكشوف",
     [r"short[- ](?:interest|selling|sales?|sellers?)", r"(?:most |heavily )?shorted", r"(?:ال)?بيع على (?:ال)?مكشوف"],
     "Selling borrowed shares to profit if the price falls. High short interest means many bet on a drop, and a rise can force "
     "them to buy back fast (a squeeze).",
     "بيع أسهم مستلفة عشان تربح إذا نزل السعر. لما يكون البيع على المكشوف عالي يعني كثير يراهنون على النزول، وأي صعود ممكن "
     "يجبرهم يشترون بسرعة (موجة ضغط)."),
    ("volatility", "Volatility", "التذبذب",
     [r"volatility", r"~volatile", r"(?:ال)?تذبذب(?! (?:ال)?ضمني)", r"~(?:ال)?تقلب(?:ات)?"],
     "", ""),   # placeholder, replaced below (implied volatility must be tried before plain volatility)

    # ---- market gauges
    ("fear_greed", "Fear & Greed index", "مؤشر الخوف والطمع",
     [r"fear\s*(?:&amp;|&|and)\s*greed", r"(?:ال)?خوف وال?طمع"],
     "A 0–100 reading of the market's mood from several signals (momentum, volatility, demand for safe assets…). Near 0 = extreme "
     "fear, near 100 = extreme greed.",
     "قراءة من 0 إلى 100 لمزاج السوق من عدة إشارات (الزخم، التذبذب، الطلب على الملاذات الآمنة…). قرب الصفر خوف شديد، وقرب 100 طمع شديد."),
    ("vix", "VIX (the fear gauge)", "مؤشر الخوف VIX",
     ["=VIX", r"fear gauge", r"مؤشر (?:ال)?خوف(?! وال?طمع)"],
     "The S&P 500 swings options traders expect over the next 30 days. Below 15 = calm, above 20 = nervous, above 30 = fearful.",
     "التذبذب اللي يتوقعه متداولو الخيارات لمؤشر إس آند بي 500 خلال 30 يوم. تحت 15 هدوء، فوق 20 توتر، وفوق 30 خوف."),
    ("breadth", "Market breadth", "اتساع السوق",
     [r"market breadth", r"~breadth", r"اتساع (?:ال)?سوق"],
     "How many stocks take part in a move. An index rising while most stocks fall is a weak rally.",
     "كم سهم مشارك في حركة السوق. لو المؤشر يصعد وأغلب الأسهم تنزل فالصعود ضعيف."),
    ("bull_bear", "Bull / bear market", "السوق الصاعد والهابط",
     [r"bull(?:ish)? markets?", r"bear(?:ish)? markets?", "=Bullish", "=Bearish", "=bullish", "=bearish", "=BULLISH", "=BEARISH",
      r"(?:ال)?سوق (?:ال)?(?:صاعد|هابط)", r"(?:ال)?(?:صعودي|هبوطي)(?:ة)?"],
     "Bull market: prices rising for months (20% or more from a low). Bear market: falling 20% or more from a high. "
     "Bullish / bearish = expecting a rise / a fall.",
     "السوق الصاعد: ارتفاع مستمر لشهور (20% أو أكثر من القاع). السوق الهابط: نزول 20% أو أكثر من القمة. صعودي أو هبوطي = توقع صعود أو نزول."),
    ("sentiment", "Sentiment", "معنويات السوق",
     [r"(?:market|investor) sentiment", r"~sentiment", r"~(?:ال)?معنويات", r"مزاج (?:ال)?سوق"],
     "Whether investors feel optimistic or fearful. Extremes often come before a turn: too much fear near lows, too much greed "
     "near highs.",
     "هل المستثمرين متفائلين ولا خايفين. الحالات المتطرفة غالباً تسبق انعكاس: خوف زايد قرب القيعان وطمع زايد قرب القمم."),
    ("seasonality", "Seasonality", "الموسمية",
     [r"seasonality", r"(?:ال)?موسمية"],
     "Patterns that repeat at the same time each year, e.g. some months are usually stronger. A tendency, not a rule.",
     "أنماط تتكرر في نفس الوقت من كل سنة، مثلاً بعض الشهور غالباً أقوى. ميل مو قاعدة."),

    # ---- indexes and products
    ("sp500", "S&P 500", "إس آند بي 500",
     [r"S(?:&amp;|&)P(?: 500)?", r"إس آند بي(?: 500)?"],
     "The index of about 500 of the largest US companies, weighted by size: the main gauge of the US stock market.",
     "مؤشر لحوالي 500 من أكبر الشركات الأمريكية، موزون حسب الحجم: المقياس الرئيسي لسوق الأسهم الأمريكي."),
    ("nasdaq", "Nasdaq", "ناسداك",
     [r"nasdaq(?:[- ]100| composite)?", r"(?:ال)?ناسداك"],
     "The US exchange home to most tech companies; the Nasdaq Composite and Nasdaq-100 indexes lean heavily on tech.",
     "البورصة الأمريكية اللي فيها أغلب شركات التقنية، ومؤشرات ناسداك تعتمد كثير على التقنية."),
    ("dow", "Dow Jones", "داو جونز",
     [r"=Dow(?: Jones)?(?: Industrial Average)?(?! Inc)", "=DJIA", r"داو(?: جونز)?"],
     "The Dow Jones Industrial Average: 30 large US companies, weighted by share price. The oldest US index.",
     "مؤشر داو جونز الصناعي: 30 شركة أمريكية كبيرة، موزون حسب سعر السهم. أقدم مؤشر أمريكي."),
    ("russell", "Russell 2000", "راسل 2000",
     [r"russell 2000", r"~russell", r"راسل 2000", r"~راسل"],
     "An index of 2,000 small US companies, a gauge of how riskier, more domestic businesses are doing.",
     "مؤشر لـ 2000 شركة أمريكية صغيرة، يقيس أداء الشركات المحلية الأعلى مخاطرة."),
    ("etf", "ETF", "الصندوق المتداول",
     ["=ETFs?", r"exchange[- ]traded funds?", r"صناديق? (?:ال)?مؤشرات", r"صناديق? (?:ال)?متداول(?:ة)?"],
     "Exchange-traded fund: a basket of stocks (or bonds, gold…) that trades like a single stock, e.g. SPY holds the S&P 500.",
     "صندوق متداول: سلة أسهم (أو سندات أو ذهب…) تتداول مثل سهم واحد، مثلاً SPY فيه أسهم إس آند بي 500."),
    ("cap_size", "Small / mid / large caps", "الشركات الصغيرة والكبيرة",
     [r"(?:small|mid|large|mega|micro)[- ]caps?", r"(?:ال)?شركات (?:ال)?(?:صغيرة|متوسطة|كبيرة|عملاقة)"],
     "Companies grouped by market value: small caps roughly $300M–$2B, mid caps $2–10B, large caps above $10B. Smaller usually "
     "means bigger swings.",
     "تصنيف الشركات حسب قيمتها السوقية: الصغيرة تقريباً 300 مليون–2 مليار دولار، المتوسطة 2–10 مليار، والكبيرة فوق 10 مليار. الأصغر غالباً حركتها أعنف."),

    # ---- options and futures
    ("futures", "Futures", "العقود الآجلة",
     [r"futures(?: contracts?)?", r"(?:ال)?عقود (?:ال)?آجلة"],
     "Contracts to buy or sell something (an index, oil, gold) at a set price on a future date. They trade almost around the "
     "clock and hint at how stocks will open.",
     "عقود لشراء أو بيع شي (مؤشر، نفط، ذهب) بسعر محدد في تاريخ قادم. تتداول تقريباً طول اليوم وتلمّح كيف بتفتح الأسهم."),
    ("call_put", "Call / put option", "خيار الشراء وخيار البيع",
     ["~=CALLS?", "~=PUTS?", "~=Calls?", "~=Puts?", r"(?:call|put) options?", r"خيار(?:ات)? (?:ال)?(?:شراء|بيع)"],
     "A call gains when the stock rises above the strike; a put gains when it falls below it. A buyer can lose at most what he paid.",
     "خيار الشراء (Call) يربح إذا صعد السهم فوق سعر التنفيذ، وخيار البيع (Put) يربح إذا نزل تحته. المشتري أقصى خسارته اللي دفعه."),
    ("options", "Options", "عقود الخيارات",
     [r"options? (?:chains?|contracts?|markets?|trading)", "~=Options", r"(?:عقود|سلسلة|سلاسل|سوق) (?:ال)?خيارات"],
     "Contracts that give the right, not the duty, to buy (a call) or sell (a put) 100 shares at a set price before a set date.",
     "عقود تعطيك الحق (مو الإلزام) تشتري (Call) أو تبيع (Put) 100 سهم بسعر محدد قبل تاريخ محدد."),
    ("strike", "Strike price", "سعر التنفيذ",
     [r"strike prices?", "~=Strikes?", "~=STRIKES?", r"سعر (?:ال)?تنفيذ"],
     "The fixed price at which an option lets you buy or sell the stock.",
     "السعر الثابت اللي يسمح لك الخيار تشتري أو تبيع عنده السهم."),
    ("expiry", "Expiration", "تاريخ الانتهاء",
     [r"expiration dates?", r"~expir(?:ation|y|ies)", r"~(?:تاريخ )?(?:ال)?انتهاء"],
     "The last day of an option. After it, the option is worth only what it pays at that day's price, or nothing.",
     "آخر يوم للخيار. بعده ما يسوى إلا اللي يستحقه على سعر ذاك اليوم، أو صفر."),
    ("open_interest", "Open interest", "العقود المفتوحة",
     [r"open interest", "~=OI", r"(?:ال)?عقود (?:ال)?مفتوحة"],
     "How many option contracts are still open at a strike. Large numbers mark prices many traders care about.",
     "عدد عقود الخيارات اللي لسا مفتوحة عند سعر تنفيذ. الأرقام الكبيرة تحدد أسعار يهتم فيها متداولين كثير."),

    # ---- company numbers
    ("eps", "EPS (earnings per share)", "ربحية السهم",
     ["=EPS", r"earnings per share", r"ربحية (?:ال)?سهم"],
     "The company's net profit divided by its number of shares. Companies report it every quarter.",
     "صافي ربح الشركة مقسوم على عدد أسهمها. تعلنه الشركات كل ربع سنة."),
    ("surprise", "Earnings surprise", "مفاجأة الأرباح",
     [r"(?:earnings|eps|revenue) surprises?", r"~surprises?", r"~(?:ال)?مفاجأ(?:ة|ت)"],
     "How far the reported results came above (a beat) or below (a miss) what analysts expected, in %. Stocks often jump on big surprises.",
     "قد إيش النتائج المعلنة طلعت أعلى (تجاوز) أو أقل (إخفاق) من توقعات المحللين بالنسبة. الأسهم كثير تقفز مع المفاجآت الكبيرة."),
    ("earnings", "Earnings", "إعلان الأرباح",
     [r"earnings(?: reports?| seasons?| calls?| dates?| results)?", r"(?:إعلان|إعلانات|نتائج|موسم) (?:ال)?أرباح"],
     "A company's quarterly results: revenue, profit and outlook. Prices often move sharply on the day they come out.",
     "نتائج الشركة الفصلية: الإيرادات والأرباح والتوقعات. الأسعار كثير تتحرك بقوة يوم إعلانها."),
    ("estimate", "Analyst estimate", "توقعات المحللين",
     [r"(?:analysts?'?|consensus) estimates?", r"~consensus", r"~estimates?", r"توقعات (?:ال)?محللين", r"متوسط (?:ال)?توقعات", r"~(?:ال)?تقديرات"],
     "The average forecast of analysts for a company's earnings or revenue. Results are judged against it.",
     "متوسط توقعات المحللين لأرباح أو إيرادات الشركة. النتائج تنقاس مقارنة فيه."),
    ("analyst_rating", "Analyst rating", "تقييم المحللين",
     [r"strong buy", r"strong sell", r"analysts?'? (?:ratings?|recommendations?)", r"(?:تقييم|توصي)(?:ة|ات)? (?:ال)?محللين", r"شراء قوي"],
     "What Wall Street analysts advise: strong buy, buy, hold, sell or strong sell. Useful context, not a guarantee.",
     "نصيحة محللي وول ستريت: شراء قوي، شراء، احتفاظ، بيع أو بيع قوي. معلومة مفيدة مو ضمان."),
    ("guidance", "Guidance", "التوجيهات المستقبلية",
     [r"(?:forward|company|earnings|full[- ]year) guidance", r"~guidance", r"(?:ال)?توجيهات (?:ال)?مستقبلية", r"~(?:ال)?توجيهات", r"(?:ال)?توقعات (?:ال)?مستقبلية"],
     "The company's own forecast for the coming quarters. Raising it often moves the stock more than the results themselves.",
     "توقعات الشركة نفسها للأرباع الجاية. رفعها كثير يحرك السهم أكثر من النتائج نفسها."),
    ("revenue", "Revenue", "الإيرادات",
     [r"revenues?", r"(?:ال)?إيرادات"],
     "All the money a company takes in from its sales, before costs.",
     "كل الفلوس اللي تدخل الشركة من مبيعاتها قبل المصاريف."),
    ("margin", "Profit margin", "هامش الربح",
     [r"(?:gross|net|operating|profit|ebitda) margins?", r"هامش (?:ال)?(?:ربح|إجمالي|صافي|تشغيلي)(?: (?:ال)?(?:إجمالي|صافي|تشغيلي))?"],
     "The share of revenue kept as profit: gross (after direct costs), operating (after running costs) or net (after everything).",
     "النسبة من الإيرادات اللي تبقى ربح: الإجمالي (بعد التكاليف المباشرة)، التشغيلي (بعد مصاريف التشغيل)، والصافي (بعد كل شي)."),
    ("fcf", "Free cash flow", "التدفق النقدي الحر",
     [r"free cash flows?", "=FCF", r"(?:ال)?تدفق(?:ات)? (?:ال)?نقدي(?:ة)? (?:ال)?حر(?:ة)?"],
     "The cash left after running the business and investing in it; it pays dividends, buybacks and debt.",
     "الكاش اللي يبقى بعد تشغيل الشركة والاستثمار فيها، ومنه تُدفع التوزيعات وإعادة الشراء والديون."),
    ("market_cap", "Market cap", "القيمة السوقية",
     [r"(?:mkt|market)\.? cap(?:italization)?", r"(?:ال)?قيمة (?:ال)?سوقية"],
     "Share price × number of shares: what the market values the whole company at.",
     "سعر السهم × عدد الأسهم: قيمة الشركة كاملة في السوق."),
    ("pe", "P/E ratio", "مكرر الربحية",
     [r"P/E(?: ratio)?", r"price[- ]to[- ]earnings", r"مكرر (?:ال)?ربحية"],
     "Price ÷ earnings per share: how many dollars you pay for $1 of yearly profit. A high P/E means the market expects strong growth.",
     "السعر ÷ ربحية السهم: كم دولار تدفع مقابل دولار ربح سنوي. المكرر العالي يعني السوق يتوقع نمو قوي."),
    ("peg", "PEG ratio", "مكرر الربحية إلى النمو",
     [r"=PEG(?: ratio)?"],
     "The P/E divided by the expected yearly earnings growth. Around 1 is fair; below 1 can mean the growth is cheap.",
     "مكرر الربحية مقسوم على نمو الأرباح السنوي المتوقع. حوالي 1 سعر عادل، وأقل من 1 ممكن يعني النمو رخيص."),
    ("valuation", "P/B, P/S, EV/EBITDA", "مكررات التقييم",
     ["=P/B", "=P/S", "=EV/EBITDA", r"price[- ]to[- ](?:book|sales)", r"مكرر (?:ال)?(?:قيمة (?:ال)?دفترية|مبيعات)"],
     "Other price tags: price ÷ book value (P/B), price ÷ sales (P/S) and company value ÷ operating profit (EV/EBITDA). Lower usually means cheaper.",
     "مقاييس سعر ثانية: السعر ÷ القيمة الدفترية (P/B)، السعر ÷ المبيعات (P/S)، وقيمة الشركة ÷ الربح التشغيلي (EV/EBITDA). الأقل غالباً أرخص."),
    ("roe", "ROE (return on equity)", "العائد على حقوق الملكية",
     ["=ROE", r"return on equity", r"(?:ال)?عائد على حقوق (?:ال)?(?:ملكية|مساهمين)"],
     "Net profit ÷ shareholders' equity: how well a company turns its owners' money into profit. Above 15% is strong.",
     "صافي الربح ÷ حقوق المساهمين: قد إيش الشركة تحوّل فلوس ملاكها لربح. فوق 15% قوي."),
    ("debt_equity", "Debt to equity", "الديون إلى حقوق الملكية",
     [r"debt[- /]to[- /]equity", "=D/E", r"(?:ال)?ديون (?:إلى|على) حقوق (?:ال)?ملكية"],
     "Total debt ÷ shareholders' equity: how much the company runs on borrowed money. Above 2 is heavy for most businesses.",
     "إجمالي الديون ÷ حقوق المساهمين: قد إيش الشركة معتمدة على فلوس مقترضة. فوق 2 ثقيل لأغلب الشركات."),
    ("beta", "Beta", "بيتا",
     ["~=Beta", "~=beta", "~=BETA", r"~بيتا"],
     "How much a stock moves with the market: 1.5 ≈ moves 50% bigger than the S&P 500, 0.5 ≈ half as big.",
     "قد إيش السهم يتحرك مع السوق: 1.5 يعني تقريباً حركة أكبر من إس آند بي 500 بـ 50%، و0.5 تقريباً نصها."),
    ("dividend_yield", "Dividend yield", "عائد التوزيعات",
     [r"dividend yields?", r"عائد (?:ال)?توزيعات"],
     "Yearly dividends ÷ share price, in %. 3% means $3 a year for every $100 invested, if the dividend holds.",
     "التوزيعات السنوية ÷ سعر السهم بالنسبة المئوية. 3% يعني 3 دولار سنوياً لكل 100 دولار مستثمرة، إذا استمرت التوزيعات."),
    ("ex_dividend", "Ex-dividend date", "تاريخ الأحقية",
     [r"ex[- ]dividend(?: dates?)?", r"ex[- ]dates?", r"تاريخ (?:ال)?(?:استحقاق|أحقية)"],
     "You must own the stock before this date to get the next dividend. On that day the price usually drops by about the dividend.",
     "لازم تملك السهم قبل هذا التاريخ عشان تاخذ التوزيعات الجاية. وفي هذا اليوم السعر غالباً ينزل بقدر التوزيعات تقريباً."),
    ("dividend", "Dividend", "التوزيعات",
     [r"dividends?", r"(?:ال)?توزيعات(?: (?:ال)?نقدية)?"],
     "Cash a company pays its shareholders out of its profits, usually every quarter.",
     "مبلغ نقدي تدفعه الشركة لمساهميها من أرباحها، عادة كل ربع سنة."),
    ("buyback", "Buyback", "إعادة شراء الأسهم",
     [r"(?:share |stock )?buy[- ]?backs?", r"(?:share |stock )repurchases?", r"إعادة شراء (?:ال)?أسهم"],
     "A company buying back its own shares, which lowers the share count and lifts earnings per share.",
     "الشركة تشتري أسهمها، فيقل عدد الأسهم وترتفع ربحية السهم."),
    ("split", "Stock split", "تقسيم الأسهم",
     [r"(?:stock|reverse) splits?", r"~splits?", r"تقسيم (?:ال)?أسهم", r"~(?:ال)?تقسيم(?:ات)?", r"~(?:ال)?تجزئة"],
     "A company divides each share into several (e.g. 4-for-1): more shares at a lower price, same total value. A reverse split does the opposite.",
     "الشركة تقسم كل سهم لعدة أسهم (مثلاً 4 مقابل 1): أسهم أكثر بسعر أقل ونفس القيمة الإجمالية. التقسيم العكسي يسوي العكس."),
    ("ipo", "IPO", "الاكتتاب العام",
     ["=IPOs?", r"initial public offerings?", r"(?:ال)?اكتتاب(?:ات)?(?: (?:ال)?عام(?:ة)?)?"],
     "Initial public offering: the first time a company sells its shares to the public and lists on the stock market.",
     "الطرح العام الأولي: أول مرة تبيع الشركة أسهمها للعامة وتنزل في سوق الأسهم."),
    ("insider", "Insiders", "المطّلعين",
     [r"insider (?:trades?|trading|transactions?|buying|selling|purchases?)", r"~insiders?", r"~(?:ال)?مطّ?لع(?:ين|ون)"],
     "A company's executives, directors and big owners. Their buying with their own money is often read as confidence.",
     "مدراء الشركة وأعضاء مجلسها وكبار ملاكها. شراؤهم بفلوسهم غالباً يُقرأ كثقة."),
    ("catalyst", "Catalyst", "المحفز",
     [r"~catalysts?", r"~(?:ال)?محفز(?:ات)?"],
     "An event that can move a stock: earnings, a product launch, a regulator's decision, a rate decision…",
     "حدث ممكن يحرك السهم: إعلان أرباح، إطلاق منتج، قرار جهة رقابية، قرار فائدة…"),
    ("materiality", "Materiality", "الأهمية الجوهرية",
     [r"materiality", r"(?:ال)?أهمية (?:ال)?جوهرية"],
     "How much a news item can change a company's value or outlook, from 0 to 10.",
     "قد إيش الخبر ممكن يغيّر قيمة الشركة أو توقعاتها، من 0 إلى 10."),
    ("sharia", "Sharia check", "الفحص الشرعي",
     [r"shariah?(?:[- ]compliant| compliance| check| screen(?:ing)?)?", r"~halal", r"(?:ال)?فحص (?:ال)?شرعي", r"متوافق(?:ة)? مع (?:ال)?شريعة", r"(?:ال)?ضوابط (?:ال)?شرعية"],
     "A check that a company's business is allowed in Islam and that its debt and interest income stay under set limits.",
     "فحص إن نشاط الشركة مباح شرعاً وإن ديونها ودخلها من الفوائد تحت حدود معينة."),

    # ---- the economy
    ("bond_yield", "Bond yield (10-year Treasury)", "عائد السندات",
     [r"(?:10|ten|2|two|30)[- ]year (?:treasury )?yields?", r"treasury yields?", r"bond yields?", r"yield curve",
      r"(?:عائد|عوائد) (?:ال)?سندات(?: (?:ال)?خزانة)?"],
     "The yearly interest the US government pays to borrow, the base rate for the whole economy. Rising yields usually weigh on "
     "stocks, especially growth stocks.",
     "الفائدة السنوية اللي تدفعها الحكومة الأمريكية لما تقترض، وهي الأساس لكل الاقتصاد. ارتفاعها غالباً يضغط على الأسهم وخصوصاً أسهم النمو."),
    ("bps", "Basis points (bps)", "نقاط الأساس",
     ["=bps", r"basis points?", r"نقط(?:ة|ات) (?:ال)?أساس"],
     "One basis point = 0.01%. A yield moving from 4.20% to 4.45% rose 25 bps.",
     "نقطة الأساس = 0.01%. العائد لما يتحرك من 4.20% لـ 4.45% ارتفع 25 نقطة أساس."),
    ("fed", "The Fed", "الاحتياطي الفيدرالي",
     ["=Fed", "=FOMC", r"federal reserve", r"(?:ال)?احتياطي (?:ال)?فيدرالي", r"~(?:ال)?فيدرالي"],
     "The US central bank. It sets interest rates: cutting them tends to lift stocks, raising them tends to cool them.",
     "البنك المركزي الأمريكي. يحدد أسعار الفائدة: خفضها غالباً يرفع الأسهم، ورفعها يبردها."),
    ("rates", "Interest rates", "أسعار الفائدة",
     [r"interest rates?", r"rate (?:cuts?|hikes?)", r"(?:أسعار|سعر|خفض|رفع|قرار|قرارات) (?:ال)?فائدة"],
     "The cost of borrowing money. Lower rates make borrowing cheaper and usually support stock prices.",
     "تكلفة اقتراض الفلوس. الفائدة المنخفضة تخلي الاقتراض أرخص وغالباً تدعم أسعار الأسهم."),
    ("inflation", "Inflation (CPI)", "التضخم",
     [r"inflation", "=CPI", "=PCE", "=PPI", r"(?:ال)?تضخم", r"مؤشر أسعار (?:ال)?(?:مستهلك|منتجين)"],
     "Prices rising across the economy; the CPI measures it every month. Hot inflation can mean higher rates, which markets dislike.",
     "ارتفاع الأسعار في الاقتصاد؛ ومؤشر CPI يقيسه كل شهر. التضخم الحار ممكن يعني فائدة أعلى، وهذا ما يحبه السوق."),
    ("gdp", "GDP", "الناتج المحلي الإجمالي",
     ["=GDP", r"(?:ال)?ناتج (?:ال)?محلي(?: (?:ال)?إجمالي)?"],
     "Gross domestic product: the value of everything the economy produces; its growth shows whether the economy is expanding.",
     "قيمة كل اللي ينتجه الاقتصاد، ونموه يبين إذا الاقتصاد يتوسع."),
]

# implied volatility before plain volatility (the same place in the list decides which wins)
_VOL_I = next(i for i, t in enumerate(TERMS) if t[0] == "volatility")
TERMS[_VOL_I:_VOL_I + 1] = [
    ("implied_vol", "Implied volatility", "التذبذب الضمني",
     [r"implied vol(?:atility)?", "~=IV", r"(?:ال)?تذبذب (?:ال)?ضمني"],
     "The future volatility that option prices imply. It rises before events like earnings, when traders expect a big move.",
     "التذبذب المستقبلي اللي تعكسه أسعار الخيارات. يرتفع قبل الأحداث مثل إعلان الأرباح لما يتوقع المتداولون حركة كبيرة."),
    ("volatility", "Volatility", "التذبذب",
     [r"volatility", r"volatile", r"(?:ال)?تذبذب(?! (?:ال)?ضمني)", r"(?:ال)?تقلب(?:ات)?"],
     "How much and how fast a price swings. High volatility means bigger gains and bigger losses, so smaller positions.",
     "مقدار وسرعة تحرك السعر. التذبذب العالي يعني أرباح أكبر وخسائر أكبر، فتحتاج صفقات أصغر."),
]

BY_KEY = {t[0]: t for t in TERMS}

# ---------------------------------------------------------------- patterns
_EN_B, _EN_A = r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])"
_AR_B, _AR_A = "(?<![ء-ي])(?:[وفبلك]{1,2})?", "(?![ء-ي])"


def _variants(pats, strict=False):
    """[(kind, wrapped)] with kind 'ci' (case-insensitive English or Arabic) or 'cs' (case-sensitive English).
    strict: leave out the "~" patterns (everyday words: strikes, support, pullback, وقف ...), as in news text."""
    out = []
    for p in sorted(pats, key=lambda x: -len(x.lstrip("~="))):
        if p.startswith("~"):
            if strict:
                continue
            p = p[1:]
        cs = p.startswith("=")
        p = p[1:] if cs else p
        if _AR.search(p):
            out.append(("ci", f"{_AR_B}(?:{p}){_AR_A}"))
        else:
            out.append(("cs" if cs else "ci", f"{_EN_B}(?:{p}){_EN_A}"))
    return out


def _compile():
    parts, names = [], {}
    for i, (key, *_r) in enumerate(TERMS):
        for j, (kind, w) in enumerate(_variants(_r[2])):
            g = f"g{i}_{j}"
            names[g] = key
            parts.append(f"(?P<{g}>{'(?-i:' + w + ')' if kind == 'cs' else w})")
    return re.compile("|".join(parts), re.I), names


RX, _GROUP_KEY = _compile()
_WORD = re.compile(r"[A-Za-z0-9ء-ي]")


# ---- speed: at each word only the terms that can start with that word's first letter are tried (one regex per letter)
try:
    from re import _constants as _sc, _parser as _sp
except ImportError:                                   # Python before 3.11
    import sre_constants as _sc
    import sre_parse as _sp

_ZERO = (_sc.ASSERT, _sc.ASSERT_NOT, _sc.AT)


def _nullable(items):
    """True when a parsed pattern can match the empty string."""
    for op, av in items:
        if op in _ZERO:
            continue
        if op in (_sc.MAX_REPEAT, _sc.MIN_REPEAT):
            if av[0] > 0 and not _nullable(av[2].data):
                return False
        elif op is _sc.SUBPATTERN:
            if not _nullable(av[-1].data):
                return False
        elif op is _sc.BRANCH:
            if not any(_nullable(b.data) for b in av[1]):
                return False
        else:
            return False
    return True


def _first(items):
    """The characters a parsed pattern can start with (None = could be anything)."""
    out = set()
    for op, av in items:
        if op in _ZERO:
            continue
        if op is _sc.LITERAL:
            out.add(chr(av))
            return out
        if op is _sc.IN:
            for o, a in av:
                if o is _sc.LITERAL:
                    out.add(chr(a))
                elif o is _sc.RANGE:
                    out.update(chr(c) for c in range(a[0], a[1] + 1))
                elif o is _sc.CATEGORY and a is _sc.CATEGORY_DIGIT:
                    out.update("0123456789")
                else:
                    return None
            return out
        if op is _sc.SUBPATTERN:
            sub = av[-1].data
        elif op is _sc.BRANCH:
            sub = None
            for b in av[1]:
                f = _first(b.data)
                if f is None:
                    return None
                out |= f
            if not any(_nullable(b.data) for b in av[1]):
                return out
            continue
        elif op in (_sc.MAX_REPEAT, _sc.MIN_REPEAT):
            sub = av[2].data
            f = _first(sub)
            if f is None:
                return None
            out |= f
            if av[0] > 0 and not _nullable(sub):
                return out
            continue
        else:
            return None
        f = _first(sub)
        if f is None:
            return None
        out |= f
        if not _nullable(sub):
            return out
    return out


def _dispatch(strict=False):
    by, anyc = {}, []
    for i, (key, *_r) in enumerate(TERMS):
        for j, (kind, w) in enumerate(_variants(_r[2])):
            if strict and (kind, w) not in _variants(_r[2], True):
                continue
            part = f"(?P<g{i}_{j}>{'(?-i:' + w + ')' if kind == 'cs' else w})"
            try:
                f = _first(_sp.parse(w, re.I if kind == "ci" else 0).data)
            except Exception:
                f = None
            if not f:
                anyc.append(part)
                continue
            for c in {c.lower() for c in f}:
                by.setdefault(c, []).append(part)
    return {c: re.compile("|".join(v + anyc), re.I) for c, v in by.items()}, (re.compile("|".join(anyc), re.I) if anyc else None)


_BY_CHAR, _ANY = _dispatch()
_BY_CHAR_S, _ANY_S = _dispatch(strict=True)          # inside news text: only the plainly financial words
_START = re.compile(r"(?<![A-Za-z0-9\u0621-\u064A])[A-Za-z0-9\u0621-\u064A]")


# ---------------------------------------------------------------- the "?" in the site's HTML
# links are fine: pressing the "?" opens its explanation and stops the link (theme.FX_JS)
_SKIP_TAGS = {"button", "script", "style", "svg", "textarea", "select", "option", "code", "pre", "title", "head", "kbd", "math"}
_SKIP_CLASS = {"gq", "nogq", "ms", "material-symbols-rounded", "navbtn", "navhd", "langbtn", "lopt", "tape", "t-row", "brand", "flag",
               "status", "dot", "lg", "lgo", "ini", "nth", "rank",
               # tickers and company names (CCI, ATR, ADX, OI, DOW are also symbols) and the sidebar's watchlist rows
               "as", "tk", "tkc", "lnk", "co", "mchip", "mvr", "wlr", "hm"}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)([^>]*)>")
_CLS = re.compile(r"""class\s*=\s*["']([^"']*)["']""")
_STYLE_BLOCK = re.compile(r"(<style[^>]*>.*?</style>)", re.S | re.I)
_BODY_SKIP = ('class="ixp', "class='ixp", 'class="ai-', 'data-nogq')
# news headlines and summaries are everyday language ("strikes on Iran", "a pullback of troops", "وقف إطلاق النار"): inside them
# only the plainly financial words get a "?"
_NEWS_CLASS = {"news", "story", "nie-card", "nb", "bstory", "sum"}


def _skip_open(name, attrs):
    if name in _SKIP_TAGS or 'aria-hidden="true"' in attrs or 'translate="no"' in attrs or 'role="img"' in attrs:
        return True                                   # icons are words drawn by the icon font: a "?" inside one breaks it
    m = _CLS.search(attrs)
    if m:
        for c in m.group(1).split():
            if c in _SKIP_CLASS or c.startswith(("ai-", "ix")):
                return True
    return False


def mark(key, ar=False):
    t = BY_KEY[key]
    label = (f"ما معنى {t[2]}؟" if ar else f"What does {t[1]} mean?")
    return f'<span class="gq" role="button" tabindex="0" data-g="{key}" aria-label="{label}">?</span>'


def _annotate_text(text, seen, strict=False):
    if not _WORD.search(text):
        return text
    out, last, pos, n = [], 0, 0, len(text)
    while pos < n:
        w = _START.search(text, pos)
        if not w:
            break
        at = w.start()
        rx = (_BY_CHAR_S.get(text[at].lower(), _ANY_S) if strict else _BY_CHAR.get(text[at].lower(), _ANY))
        m = rx.match(text, at) if rx else None
        if not m:
            pos = at + 1
            continue
        pos = max(m.end(), at + 1)
        key = _GROUP_KEY.get(m.lastgroup)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(text[last:m.end()])
        out.append(mark(key, bool(_AR.search(m.group()))))
        last = m.end()
    if not out:
        return text
    out.append(text[last:])
    return "".join(out)


def _is_news(attrs):
    m = _CLS.search(attrs)
    return bool(m and _NEWS_CLASS.intersection(m.group(1).split()))


def _annotate_html(html):
    seen, out, pos = set(), [], 0
    stack = []                      # (tag, skips, news)
    skipping = news = 0
    for m in _TAG.finditer(html):
        text = html[pos:m.start()]
        if text:
            out.append(text if skipping else _annotate_text(text, seen, news > 0))
        closing, name, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3)
        if closing:
            for k in range(len(stack) - 1, -1, -1):          # close back to the matching open tag
                if stack[k][0] == name:
                    for _t, sk, nw in stack[k:]:
                        skipping -= sk
                        news -= nw
                    del stack[k:]
                    break
        elif name not in _VOID and not attrs.rstrip().endswith("/"):
            sk = 1 if (skipping or _skip_open(name, attrs)) else 0
            nw = 1 if _is_news(attrs) else 0
            stack.append((name, sk, nw))
            skipping += sk
            news += nw
        out.append(m.group(0))
        pos = m.end()
    tail = html[pos:]
    if tail:
        out.append(tail if skipping else _annotate_text(tail, seen, news > 0))
    return "".join(out)


@lru_cache(maxsize=1024)
def _annotate_cached(html):
    return _annotate(html)


def _annotate(html):
    if any(s in html for s in _BODY_SKIP):
        return html
    if "<style" in html:            # styles pass through untouched; the rest is annotated
        parts = _STYLE_BLOCK.split(html)
        return "".join(p if p.lower().startswith("<style") else (_annotate_html(p) if p.strip() else p) for p in parts)
    return _annotate_html(html)


def annotate(html):
    """The HTML with a "?" right after the first time each term appears in it (see the module notes)."""
    if not html or not isinstance(html, str) or not _WORD.search(html):
        return html
    try:
        return _annotate_cached(html) if len(html) < 60000 else _annotate(html)
    except Exception:               # never let the glossary break a page
        return html


# ---------------------------------------------------------------- the glossary page
def glossary(extra=()):
    """Every term as (en name, ar name, en text, ar text): this list, then the entries of extra (the Academy's glossary)
    that none of these terms covers."""
    out = [(en, ar, den, dar) for _k, en, ar, _p, den, dar in TERMS]
    for row in extra:
        m = RX.search(row[0])
        if not (m and m.start() == 0):
            out.append(tuple(row))
    return out


# ---------------------------------------------------------------- the list for the page script
def client():
    """{"t": {key: [en name, ar name, en text, ar text]}, "p": [[key, ci, cs, strict ci, strict cs], ...]} in list order."""
    t, p = {}, []
    for key, en, ar, pats, den, dar in TERMS:
        t[key] = [en, ar, den, dar]
        v, vs = _variants(pats), _variants(pats, True)
        p.append([key, "|".join(w for k, w in v if k == "ci"), "|".join(w for k, w in v if k == "cs"),
                  "|".join(w for k, w in vs if k == "ci"), "|".join(w for k, w in vs if k == "cs")])
    return {"t": t, "p": p}


BUILD = "21.3"
