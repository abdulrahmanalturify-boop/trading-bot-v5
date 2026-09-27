"""Twelve bilingual mini-courses; original worked examples, not investment recommendations."""
ACADEMY_REVISION = "2026-09-27.5"
LEVEL_AR = {"Beginner": "مبتدئ", "Essential": "أساسي", "Advanced": "متقدم"}
EXTRA_COURSES = []

def course(cid, level, title, tagline, art, lessons, questions, lab=None):
    sections = [(h[0], h[1], b[0], b[1], t[0], t[1], lab if i == len(lessons)-1 else None)
                for i, (h,b,t) in enumerate(lessons)]
    EXTRA_COURSES.append(dict(id=cid, level=(level, LEVEL_AR[level]), title=title, tagline=tagline,
                             art=art, icon="account_balance", mins=6 if level=="Beginner" else 8,
                             sections=sections, quiz=questions, new=True))

def q(en, ar, options, correct, why, why_ar):
    return (en, ar, options, correct, why, why_ar)

course("goals", "Beginner", ("Build Your Investment Plan", "ابنِ خطتك الاستثمارية"),
       ("Turn a vague ambition into a goal, horizon and risk budget.", "حوّل طموحك لهدف ومدة وميزانية مخاطرة."), "plan", [
(("Start with the goal", "ابدأ بالهدف"), ("Write the amount you need, the date you need it and the currency you will spend. A tuition payment in one year and retirement in twenty years are different liabilities, even if both accounts start with 10,000.", "اكتب المبلغ اللي تحتاجه وموعده والعملة اللي بتصرف فيها. رسوم دراسة بعد سنة تختلف عن تقاعد بعد عشرين سنة، حتى لو الاثنين يبدأون بعشرة آلاف."), ("Match the investment horizon to the spending date.", "اربط مدة الاستثمار بموعد احتياجك للمال.")),
(("Capacity versus comfort", "القدرة غير الراحة"), ("Risk capacity is your financial ability to withstand a loss. Risk tolerance is how you feel about it. Someone with unstable income may have low capacity even if they enjoy taking risks. Keep near-term essential spending separate from volatile investments.", "القدرة على المخاطرة تعني قدرتك المالية تتحمل خسارة؛ تقبّل المخاطرة يعني شعورك تجاهها. لو دخلك متذبذب ممكن قدرتك تكون ضعيفة حتى لو تحب المغامرة. افصل مصاريفك الضرورية القريبة عن الاستثمارات المتقلبة."), ("Willingness to take risk does not create financial capacity.", "رغبتك بالمخاطرة ما تعني أنك قادر تتحملها.")),
(("Write review rules", "اكتب قواعد المراجعة"), ("Define contributions, maximum concentration and a review schedule before buying. Review when your income, goal or time horizon changes. A hypothetical 20% loss on 10,000 leaves 8,000: decide whether your plan remains feasible before facing that scenario.", "حدد الإضافات وحدّ التركز وموعد المراجعة قبل الشراء. راجع الخطة إذا تغير دخلك أو هدفك أو المدة. خسارة افتراضية 20% من عشرة آلاف تترك ثمانية آلاف؛ اسأل نفسك هل خطتك تظل ممكنة قبل ما تعيش السيناريو."), ("A written process is easier to follow than a price prediction.", "العملية المكتوبة أسهل بالالتزام من توقع السعر."))], [
q("Which goal has the shortest horizon?", "أي هدف مدته أقصر؟", [("Tuition next year", "دراسة السنة الجاية"),("Retirement in 20 years", "تقاعد بعد 20 سنة"),("A distant legacy", "إرث بعيد")],0,"The spending date determines the horizon.","موعد الصرف يحدد المدة."),
q("What is risk capacity?", "وش القدرة على المخاطرة؟", [("Enjoying volatility", "الاستمتاع بالتذبذب"),("Financial ability to absorb loss", "القدرة المالية على تحمل الخسارة"),("Expected return", "العائد المتوقع")],1,"Capacity depends on finances, not excitement.","القدرة مرتبطة بالوضع المالي مو الحماس."),
q("10,000 falls 20%. What remains?", "عشرة آلاف نزلت 20%، كم يبقى؟", [("9,800", "9,800"),("12,000", "12,000"),("8,000", "8,000")],2,"10,000 × 0.8 = 8,000.","10,000 × 0.8 = 8,000.")])

course("compounding", "Beginner", ("The Power of Compounding", "قوة العائد المركب"),
       ("Explore how time, contributions and reinvestment work together.", "جرّب أثر الوقت والإضافات وإعادة الاستثمار."), "growth", [
(("Returns on returns", "عائد على العائد"), ("With a constant hypothetical annual return of 10%, 1,000 becomes 1,100 after one year and 1,210 after two. The second year's 110 includes 10 earned on the first year's gain. Real investment returns fluctuate and can be negative.", "بعائد سنوي افتراضي ثابت 10%، الألف تصير 1,100 بعد سنة و1,210 بعد سنتين. ربح السنة الثانية 110، منها عشرة على ربح السنة الأولى. العوائد الحقيقية تتغير وقد تكون سالبة."), ("Compounding requires gains to remain invested.", "التراكم يحتاج بقاء الأرباح مستثمرة.")),
(("Contributions have their own clock", "كل إضافة لها مدة"), ("A deposit made today compounds longer than one made next year. In the lab, monthly deposits occur at month-end and annual returns are converted to an equivalent monthly rate. The final deposit earns no return during its deposit month.", "الإضافة اليوم تتراكم أكثر من الإضافة بعد سنة. في المختبر نضيف المبلغ نهاية الشهر ونحوّل العائد السنوي لمعدل شهري مكافئ. آخر إضافة ما تكسب عائد خلال شهر إضافتها."), ("Deposit timing matters when comparing calculators.", "توقيت الإضافة مهم عند مقارنة الحاسبات.")),
(("Read the result honestly", "اقرأ النتيجة بواقعية"), ("Separate your own contributions from investment gains. A high ending balance may mostly come from savings. Use different return assumptions rather than treating one smooth growth curve as a forecast. Fees, taxes and inflation can reduce what you keep.", "افصل مبالغك المدفوعة عن أرباح الاستثمار. الرصيد الكبير ممكن يكون أغلبه من الادخار. جرّب أكثر من افتراض عائد ولا تعتبر المنحنى الناعم توقعًا مضمونًا. الرسوم والضرائب والتضخم تقلل اللي يبقى لك."), ("A scenario is an assumption, not a promised outcome.", "السيناريو افتراض مو وعد."))], [
q("1,000 at 10% for two years becomes?", "ألف بعائد 10% لسنتين تصير؟", [("1,200", "1,200"),("1,210", "1,210"),("1,100", "1,100")],1,"1,000 × 1.1² = 1,210.","1,000 × 1.1² = 1,210."),
q("Which deposit compounds longer?", "أي إضافة تتراكم مدة أطول؟", [("Today's deposit", "إضافة اليوم"),("Next year's deposit", "إضافة السنة الجاية"),("Both equally", "نفس المدة")],0,"The earlier deposit has more time invested.","الإضافة المبكرة تقعد مستثمرة أطول."),
q("A constant-return chart is…", "الرسم بعائد ثابت يعتبر…", [("A guarantee", "ضمان"),("Actual market history", "تاريخ السوق الفعلي"),("An illustrative scenario", "سيناريو توضيحي")],2,"Markets do not deliver a fixed return every month.","السوق ما يعطي عائد ثابت كل شهر.")], "compound")

course("funds", "Beginner", ("Funds and Index Investing", "الصناديق والاستثمار بالمؤشرات"),
       ("Look inside the fund before judging its name or performance.", "افهم وش داخل الصندوق قبل تحكم على اسمه أو عائده."), "fund", [
(("A wrapper around assets", "وعاء يجمع أصول"), ("An Exchange-Traded Fund (ETF) holds assets and trades on an exchange. An index fund follows a specified index, while an active fund uses manager decisions. A fund can be broad or concentrated; owning a fund does not automatically mean broad diversification.", "الصندوق المتداول يجمع أصول ويتداول بالبورصة. صندوق المؤشر يتبع مؤشر محدد، والنشط يعتمد على قرارات مديره. الصندوق ممكن يكون واسع أو متركز؛ مجرد امتلاكه ما يعني تنويع واسع."), ("Read holdings and concentration, not just the label.", "اقرأ المكونات والتركيز مو الاسم بس.")),
(("Costs accumulate", "التكاليف تتراكم"), ("An annual expense ratio of 0.20% is about 20 per year on a constant 10,000 balance; 1.00% is about 100. Actual charges depend on asset values. Trading spreads and commissions can add costs beyond the fund's stated expense ratio.", "رسوم سنوية 0.20% تقارب عشرين على رصيد ثابت عشرة آلاف؛ ورسوم 1% تقارب مئة. التكلفة الفعلية تعتمد على قيمة الأصول. السبريد وعمولة التداول ممكن تزيد فوق رسوم إدارة الصندوق."), ("Compare total cost for the way you actually invest.", "قارن إجمالي التكلفة حسب طريقة استثمارك.")),
(("Compare like with like", "قارن المتشابه"), ("Compare funds with the same mandate and benchmark. Check holdings, tracking difference, liquidity and distribution policy. Two funds with different sector exposure can have different returns because they take different risks, not because one manager is necessarily better.", "قارن صناديق لها نفس الهدف والمؤشر المرجعي. راجع المكونات وفرق التتبع والسيولة وسياسة التوزيع. اختلاف العائد بين صندوقين بقطاعات مختلفة ممكن سببه اختلاف المخاطر، مو تفوق المدير بالضرورة."), ("The benchmark should match the fund's opportunity set.", "المؤشر المرجعي لازم يناسب استثمارات الصندوق."))], [
q("Does every fund provide broad diversification?", "هل كل صندوق يوفر تنويع واسع؟", [("Yes", "نعم"),("No; holdings may be concentrated", "لا؛ مكوناته ممكن تكون متركزة"),("Only on Mondays", "فقط يوم الاثنين")],1,"A sector fund may concentrate in one industry.","صندوق القطاع ممكن يتركز في صناعة وحدة."),
q("0.20% of 10,000 is?", "كم 0.20% من عشرة آلاف؟", [("20", "20"),("200", "200"),("2,000", "2,000")],0,"10,000 × 0.002 = 20.","10,000 × 0.002 = 20."),
q("A useful comparison starts with…", "المقارنة المفيدة تبدأ بـ…", [("The logo", "الشعار"),("Last week's winner", "أفضل عائد الأسبوع الماضي"),("The same mandate", "نفس الهدف الاستثماري")],2,"Different mandates imply different risks.","اختلاف الأهداف يعني اختلاف المخاطر.")])

course("execution", "Beginner", ("Orders, Spreads and Slippage", "الأوامر والسبريد والانزلاق"),
       ("Understand the difference between a quoted price and a fill.", "افهم الفرق بين السعر المعروض وسعر التنفيذ."), "orders", [
(("Two sides of the quote", "طرفا التسعير"), ("If the best bid is 99.90 and ask is 100.10, their spread is 0.20. An immediate buyer typically trades at the ask and an immediate seller at the bid, subject to available size and price changes. The last traded price is not a guaranteed executable quote.", "إذا أفضل عرض شراء 99.90 وأفضل طلب بيع 100.10، الفرق 0.20. المشتري الفوري غالبًا ينفذ عند طلب البيع والبائع الفوري عند عرض الشراء، حسب الكمية وتغير السعر. آخر صفقة مو سعر تنفيذ مضمون."), ("The spread is a trading friction.", "السبريد من تكاليف التداول.")),
(("Price control versus execution", "التحكم بالسعر مقابل التنفيذ"), ("A buy limit at 100 cannot execute above 100, but may remain unfilled. A market order prioritizes execution rather than price. A stop order typically becomes a market order when triggered; gaps can make the fill worse than the stop level.", "أمر شراء محدد بمئة ما يتنفذ فوق مئة، لكنه ممكن ما يتنفذ أصلًا. أمر السوق يعطي أولوية للتنفيذ بدل السعر. أمر الوقف غالبًا يصير أمر سوق إذا تفعّل؛ الفجوة ممكن تخلي التنفيذ أسوأ من الوقف."), ("A stop level is not a guaranteed loss limit.", "سعر الوقف مو ضمان لحد الخسارة.")),
(("Model the friction", "احسب أثر التكلفة"), ("For 100 shares, buying at 100.10 and immediately selling at 99.90 costs 20 before commissions. Larger orders may move through several price levels. Compare strategy results after spreads, slippage and fees, not only at chart closing prices.", "شراء مئة سهم عند 100.10 وبيعها فورًا عند 99.90 يكلف عشرين قبل العمولة. الأوامر الكبيرة ممكن تتنفذ على أكثر من مستوى. قارن الاستراتيجيات بعد السبريد والانزلاق والرسوم مو بس أسعار الإغلاق."), ("Small costs can matter when trading frequently.", "التكلفة الصغيرة تفرق مع كثرة التداول."))], [
q("Bid 99.90, ask 100.10: spread?", "عرض 99.90 وطلب 100.10، كم السبريد؟", [("0.10", "0.10"),("0.20", "0.20"),("2.00", "2.00")],1,"100.10 − 99.90 = 0.20.","100.10 − 99.90 = 0.20."),
q("A buy limit at 100 can…", "أمر شراء محدد بمئة ممكن…", [("Remain unfilled", "ما يتنفذ"),("Fill at 105", "يتنفذ عند 105"),("Guarantee profit", "يضمن الربح")],0,"The limit constrains price, not execution.","الحد يقيد السعر مو يضمن التنفيذ."),
q("Does a stop guarantee its trigger price?", "هل الوقف يضمن سعر التفعيل؟", [("Always", "دائمًا"),("For every liquid stock", "لكل سهم عالي السيولة"),("No, gaps can cause slippage", "لا، الفجوات قد تسبب انزلاق")],2,"Trigger price and execution price can differ.","سعر التفعيل ممكن يختلف عن التنفيذ.")])

course("statements", "Beginner", ("Meet the Three Financial Statements", "تعرّف على القوائم المالية الثلاث"),
       ("Connect profit, cash and the balance sheet.", "اربط الربح بالكاش والمركز المالي."), "statements", [
(("Performance over a period", "الأداء خلال فترة"), ("The income statement records revenue and expenses over a period. Revenue of 100 less cost of sales of 60 gives gross profit of 40, not net income. Operating costs, interest and taxes still need to be considered.", "قائمة الدخل تسجل الإيراد والمصروف خلال فترة. إيراد مئة ناقص تكلفة مبيعات ستين يعطي ربح إجمالي أربعين، مو صافي ربح. باقي المصاريف التشغيلية والفوائد والضرائب."), ("Know which profit level you are comparing.", "اعرف أي مستوى ربح قاعد تقارن.")),
(("A snapshot of resources", "صورة للمركز المالي"), ("The balance sheet describes assets, liabilities and equity at a date. Assets of 150 financed by liabilities of 90 leave equity of 60. Equity is an accounting residual, not necessarily the company's market value.", "الميزانية تعرض الأصول والالتزامات وحقوق الملكية بتاريخ محدد. أصول 150 والتزامات 90 تعني حقوق ملكية ستين. حقوق الملكية قيمة محاسبية متبقية، مو بالضرورة القيمة السوقية للشركة."), ("Assets = liabilities + equity.", "الأصول = الالتزامات + حقوق الملكية.")),
(("Follow the cash", "تتبّع النقد"), ("Cash flows are grouped into operating, investing and financing activities. A credit sale can increase revenue before cash arrives. Buying equipment consumes cash but is normally expensed over time through depreciation rather than fully in the purchase period.", "التدفقات النقدية تنقسم لتشغيلية واستثمارية وتمويلية. البيع الآجل يرفع الإيراد قبل وصول الكاش. شراء معدة يستهلك نقد، لكن تكلفتها غالبًا تتوزع كمصروف إهلاك بدل تحميلها كاملة وقت الشراء."), ("Profit and cash flow answer different questions.", "الربح والتدفق النقدي يجاوبون على سؤالين مختلفين."))], [
q("Revenue 100 minus cost of sales 60 gives…", "إيراد مئة ناقص تكلفة مبيعات ستين يعطي…", [("Gross profit 40", "ربح إجمالي 40"),("Net income 100", "صافي ربح 100"),("Equity 60", "حقوق ملكية 60")],0,"Other expenses still follow gross profit.","باقي مصاريف بعد الربح الإجمالي."),
q("Assets 150 and liabilities 90 imply equity of…", "أصول 150 والتزامات 90، حقوق الملكية؟", [("240", "240"),("60", "60"),("90", "90")],1,"Equity = 150 − 90.","حقوق الملكية = 150 − 90."),
q("Can revenue rise before cash is collected?", "هل الإيراد يرتفع قبل تحصيل الكاش؟", [("Never", "مستحيل"),("Only with dividends", "فقط مع التوزيعات"),("Yes, through credit sales", "نعم، بالبيع الآجل")],2,"Accrual revenue and cash receipt can occur at different times.","توقيت إثبات الإيراد ممكن يختلف عن التحصيل.")])

course("inflation", "Beginner", ("Inflation and Real Returns", "التضخم والعائد الحقيقي"),
       ("Measure growth in purchasing power, not just account balances.", "قِس نمو القوة الشرائية مو الرصيد بس."), "inflation", [
(("Money versus purchasing power", "المال مقابل القوة الشرائية"), ("If a basket costs 100 today and 105 next year, inflation is 5%. An unchanged cash balance buys fewer baskets. Inflation describes a price index; your personal spending basket can experience a different rate.", "إذا سلة تكلف مئة اليوم و105 السنة الجاية، التضخم 5%. الرصيد النقدي الثابت يشتري سلال أقل. التضخم يقيس مؤشر أسعار؛ سلة مصاريفك الشخصية ممكن ترتفع بمعدل مختلف."), ("A growing balance can still lose purchasing power.", "الرصيد ممكن ينمو وقوته الشرائية تنخفض.")),
(("Calculate the real return", "احسب العائد الحقيقي"), ("The exact one-period real return is (1 + nominal return) ÷ (1 + inflation) − 1. With 8% return and 3% inflation it is about 4.85%. Subtracting inflation gives a convenient 5% approximation, not the exact result.", "العائد الحقيقي الدقيق للفترة هو (1 + العائد الاسمي) ÷ (1 + التضخم) ناقص واحد. عائد 8% وتضخم 3% يعطي تقريبًا 4.85%. طرح التضخم يعطي تقريب 5% مو النتيجة الدقيقة."), ("Use consistent periods for return and inflation.", "استخدم نفس الفترة للعائد والتضخم.")),
(("Scenario discipline", "انضباط السيناريو"), ("Try a 2% investment return against 4% inflation: the real return is negative even though the balance rises. The lab ignores taxes and fees, so its output is an illustration of purchasing power rather than a personal net-return forecast.", "جرّب عائد استثمار 2% مع تضخم 4%: العائد الحقيقي سالب رغم ارتفاع الرصيد. المختبر يستبعد الضرائب والرسوم؛ نتيجته توضيح للقوة الشرائية مو توقع لعائدك الصافي الشخصي."), ("Compare results after inflation when judging long-term goals.", "قارن النتائج بعد التضخم عند تقييم الأهداف الطويلة."))], [
q("8% return and 3% inflation give approximately…", "عائد 8% وتضخم 3% يعطي تقريبًا…", [("11% real", "11% حقيقي"),("4.85% real", "4.85% حقيقي"),("8% real", "8% حقيقي")],1,"1.08 ÷ 1.03 − 1 ≈ 4.85%.","1.08 ÷ 1.03 − 1 ≈ 4.85%."),
q("With 2% return and 4% inflation…", "مع عائد 2% وتضخم 4%…", [("Purchasing power falls", "القوة الشرائية تنخفض"),("Purchasing power rises", "القوة الشرائية ترتفع"),("No change", "ما تتغير")],0,"1.02 ÷ 1.04 is below one.","1.02 ÷ 1.04 أقل من واحد."),
q("Which periods should be compared?", "أي فترات نقارن؟", [("Monthly return with annual inflation", "شهري مع سنوي"),("Unrelated dates", "تواريخ مختلفة"),("Matching periods", "نفس الفترة")],2,"Units and periods must match.","الوحدات والفترات لازم تتطابق.")], "inflation")

course("behaviour", "Beginner", ("Investor Psychology and Journaling", "نفسية المستثمر وسجل القرارات"),
       ("Build a repeatable decision process around common biases.", "ابنِ قرارات منضبطة وتعرّف على تحيزاتك."), "mind", [
(("Recognise the bias", "تعرّف على التحيّز"), ("Confirmation bias means giving more weight to evidence that supports your existing view. Before buying, write one fact that would contradict your thesis. Read the opposing case using the same standard you apply to supporting evidence.", "تحيز التأكيد يعني تعطي وزن أكبر للمعلومة اللي توافق رأيك. قبل الشراء اكتب معلومة ممكن تنقض فرضيتك. اقرأ الرأي المضاد بنفس المعيار اللي تستخدمه للأدلة المؤيدة."), ("Actively search for disconfirming evidence.", "دور على دليل يخالف فكرتك.")),
(("Separate outcome from process", "افصل النتيجة عن العملية"), ("A profitable trade can come from luck and a sound decision can lose money. Judge whether the information, valuation, position size and exit rules were reasonable when the decision was made. Do not rewrite the original thesis after seeing the outcome.", "الصفقة الرابحة ممكن تكون حظ، والقرار الجيد ممكن يخسر. قيّم المعلومات والتقييم والحجم وقواعد الخروج وقت القرار. لا تعيد كتابة فرضيتك القديمة بعد ما تشوف النتيجة."), ("One outcome cannot prove the quality of a process.", "نتيجة وحدة ما تثبت جودة العملية.")),
(("Use a decision journal", "استخدم سجل قرارات"), ("Record the thesis, expected range of outcomes, contrary evidence and review date. On review, compare observations with the original entry. In the lab you can write and download a practice journal; it does not place trades or send your notes anywhere.", "سجل الفرضية ونطاق النتائج المتوقع والدليل المضاد وتاريخ المراجعة. يوم تراجع قارن الواقع مع تدوينتك الأصلية. في المختبر تقدر تكتب وتحمل سجل تدريبي؛ ما ينفذ تداول ولا يرسل ملاحظاتك لأحد."), ("Write the reasoning before the result is known.", "اكتب السبب قبل ما تعرف النتيجة."))], [
q("Seeking only supportive news is…", "البحث عن الأخبار المؤيدة فقط هو…", [("Diversification", "تنويع"),("Confirmation bias", "تحيز التأكيد"),("Rebalancing", "إعادة توازن")],1,"You are filtering evidence toward an existing belief.","أنت تنتقي الأدلة لصالح رأيك."),
q("One winning trade proves…", "صفقة رابحة وحدة تثبت…", [("Very little about repeatability", "القليل عن قابلية تكرار النجاح"),("A strategy always works", "الاستراتيجية تنجح دائمًا"),("Risk is zero", "المخاطرة صفر")],0,"Luck can dominate one outcome.","الحظ ممكن يهيمن على نتيجة وحدة."),
q("When should the thesis be recorded?", "متى تسجل الفرضية؟", [("Only after profit", "بعد الربح فقط"),("After changing the story", "بعد تغيير القصة"),("Before the outcome", "قبل النتيجة")],2,"An original record limits hindsight bias.","التسجيل المسبق يقلل تحيز الإدراك المتأخر.")], "journal")

course("allocation", "Essential", ("Portfolio Allocation and Correlation", "توزيع المحفظة والارتباط"),
       ("See why combining assets changes portfolio risk.", "شوف كيف جمع الأصول يغيّر مخاطرة المحفظة."), "allocation", [
(("Weights define exposure", "الأوزان تحدد التعرض"), ("A 60% allocation to asset A and 40% to B produces an expected return of 0.6 × return A + 0.4 × return B. If expected returns are 8% and 4%, the portfolio expectation is 6.4%. Expected return is an estimate, not a realized result.", "توزيع 60% للأصل الأول و40% للثاني يعطي عائد متوقع يساوي مجموع الأوزان مضروبة بالعوائد. إذا العوائد المتوقعة 8% و4%، توقع المحفظة 6.4%. المتوقع تقدير مو نتيجة فعلية."), ("Weights sum to 100% in this unlevered example.", "الأوزان مجموعها 100% بالمثال بدون اقتراض.")),
(("Correlation changes risk", "الارتباط يغيّر المخاطرة"), ("Portfolio volatility depends on individual volatility and correlation. Two assets with 20% volatility, equal weights and zero correlation give portfolio volatility of about 14.14%. With correlation +1, volatility remains 20%. Correlations can change during stress.", "تذبذب المحفظة يعتمد على تذبذب الأصول وارتباطها. أصلان تذبذب كل واحد 20% وأوزان متساوية وارتباط صفر يعطون تذبذب محفظة 14.14% تقريبًا. مع ارتباط موجب واحد يبقى 20%. الارتباط ممكن يتغير وقت الأزمات."), ("More holdings do not guarantee independent risks.", "زيادة عدد المراكز ما تضمن اختلاف المخاطر.")),
(("Rebalancing and constraints", "إعادة التوازن والقيود"), ("If one asset rises faster, weights drift from their targets. Rebalancing restores the chosen exposure; it is not a guarantee of higher returns. Consider transaction costs, taxes and concentration limits. The two-asset lab uses assumed annual returns and volatility, not live market estimates.", "إذا أصل ارتفع أسرع، الأوزان تبتعد عن المستهدف. إعادة التوازن ترجع التعرض المختار، وما تضمن عائد أعلى. راعِ الرسوم والضرائب وحدود التركز. مختبر الأصلين يستخدم افتراضات سنوية مو تقديرات مباشرة من السوق."), ("Diversification reduces some risks, not all losses.", "التنويع يقلل بعض المخاطر، مو كل الخسائر."))], [
q("60% at 8% and 40% at 4% yields an expectation of…", "60% بعائد 8% و40% بعائد 4%، المتوقع؟", [("12%", "12%"),("6.4%", "6.4%"),("4%", "4%")],1,"0.6 × 8 + 0.4 × 4 = 6.4%.","0.6 × 8 + 0.4 × 4 = 6.4%."),
q("Which correlation offers less diversification?", "أي ارتباط يعطي تنويع أقل؟", [("+1", "+1"),("0", "0"),("−1", "−1")],0,"Perfect positive correlation removes the correlation benefit.","الارتباط الموجب الكامل يلغي فائدة اختلاف الحركة."),
q("Rebalancing primarily restores…", "إعادة التوازن ترجع أساسًا…", [("Guaranteed gains", "أرباح مضمونة"),("Yesterday's price", "سعر أمس"),("Target exposures", "التعرضات المستهدفة")],2,"It manages allocation drift.","تعالج ابتعاد الأوزان عن المستهدف.")], "allocation")

course("quality", "Essential", ("Earnings Quality and Cash Conversion", "جودة الأرباح والتحول إلى نقد"),
       ("Investigate the gap between reported earnings and cash.", "افحص الفرق بين الربح المعلن والكاش."), "quality", [
(("Profit is a starting point", "الربح نقطة بداية"), ("Reported net income can include nonrecurring items and accounting estimates. Separate recurring operating performance from one-off gains. A gain on selling a building may raise this year's profit without improving the core business's future earnings power.", "صافي الربح المعلن ممكن يتضمن بنود غير متكررة وتقديرات محاسبية. افصل الأداء التشغيلي المستمر عن المكاسب الاستثنائية. ربح بيع مبنى يرفع ربح السنة بدون ما يحسن قدرة النشاط الأساسي على تحقيق أرباح مستقبلية."), ("Identify what can realistically recur.", "حدد وش ممكن يتكرر بواقعية.")),
(("Working capital absorbs cash", "رأس المال العامل يسحب نقد"), ("When receivables or inventory grow, cash can lag earnings. Operating cash flow of 70 against net income of 100 gives a cash-conversion ratio of 0.70 for this definition. One weak year is not proof of manipulation: examine growth, seasonality and collection trends.", "إذا زادت الذمم المدينة أو المخزون، النقد ممكن يتأخر عن الربح. تدفق تشغيلي سبعين وصافي ربح مئة يعطي نسبة تحول نقدي 0.70 بهذا التعريف. سنة ضعيفة مو دليل تلاعب؛ افحص النمو والموسمية والتحصيل."), ("Study several periods and the reason behind the gap.", "افحص عدة فترات وسبب الفرق.")),
(("Reinvestment still matters", "إعادة الاستثمار مهمة"), ("A simple free-cash-flow measure is operating cash flow minus capital expenditure. Cash flow of 70 and equipment spending of 30 leave 40. Distinguish maintenance from growth investment where disclosed, and reconcile management's adjusted measures to financial statements.", "مقياس مبسط للتدفق الحر هو التدفق التشغيلي ناقص الإنفاق الرأسمالي. سبعين تدفق وثلاثين معدات تترك أربعين. فرّق بين استثمار المحافظة على النشاط والتوسع إذا توفر الإفصاح، وطابق المقاييس المعدلة للإدارة مع القوائم."), ("State your cash-flow definition before comparing companies.", "حدد تعريف التدفق النقدي قبل مقارنة الشركات."))], [
q("Selling a building at a gain is always recurring?", "ربح بيع مبنى دائمًا متكرر؟", [("Yes", "نعم"),("No", "لا"),("Only if profit rose", "إذا ارتفع الربح فقط")],1,"A disposal gain may not recur.","مكسب البيع ممكن ما يتكرر."),
q("Operating cash 70, capital expenditure 30: simple free cash?", "تدفق تشغيلي 70 وإنفاق رأسمالي 30، التدفق الحر المبسط؟", [("40", "40"),("100", "100"),("70", "70")],0,"70 − 30 = 40.","70 − 30 = 40."),
q("One year of low cash conversion proves fraud?", "سنة تحول نقدي ضعيف تثبت احتيال؟", [("Always", "دائمًا"),("If sales grew", "إذا نمت المبيعات"),("No; investigate the cause", "لا؛ افحص السبب")],2,"Working capital and seasonality can explain a gap.","رأس المال العامل والموسمية ممكن يفسرون الفرق.")])

course("bonds", "Essential", ("Bonds, Yields and Duration", "السندات والعوائد والمدة"),
       ("Understand the price sensitivity behind fixed income.", "افهم حساسية السعر في الدخل الثابت."), "bonds", [
(("Coupon is not yield", "الكوبون مو العائد"), ("A bond paying 50 annually on face value 1,000 has a 5% coupon rate. If its market price is 900, current yield is 50 ÷ 900 = 5.56%. Yield to maturity also reflects repayment, timing and price; it is not the same as current yield.", "سند يدفع خمسين سنويًا وقيمته الاسمية ألف، كوبونه 5%. لو سعره بالسوق تسعمئة، العائد الجاري 50 ÷ 900 = 5.56%. العائد حتى الاستحقاق يأخذ السداد والتوقيت والسعر بالحسبان؛ مو نفس العائد الجاري."), ("Always name the yield measure.", "حدد أي عائد تقصد.")),
(("Rates and prices", "الفائدة والأسعار"), ("For a standard fixed-rate bond with unchanged promised cash flows, higher required yields lower present value. Credit deterioration can also raise required yields. Bondholders face interest-rate, credit and liquidity risk, even when coupon payments are fixed.", "للسند التقليدي ثابت الكوبون مع تدفقات موعودة ثابتة، ارتفاع العائد المطلوب يقلل القيمة الحالية. تدهور الجدارة الائتمانية ممكن يرفع العائد المطلوب أيضًا. حامل السند يواجه مخاطر الفائدة والائتمان والسيولة حتى لو الكوبون ثابت."), ("Fixed coupons do not imply fixed market prices.", "ثبات الكوبون ما يعني ثبات سعر السوق.")),
(("Duration approximation", "تقريب المدة المعدلة"), ("For small parallel yield changes, percentage price change is approximately minus modified duration times yield change. Duration 5 and a +1 percentage-point yield move imply roughly −5%. Convexity and nonparallel curve changes can make actual results differ.", "للتغيرات الصغيرة والمتوازية بالعائد، تغير السعر النسبي يقارب سالب المدة المعدلة مضروبة بتغير العائد. مدة خمسة وارتفاع العائد نقطة مئوية تعني هبوط تقريبي 5%. التحدب والتغيرات غير المتوازية بمنحنى العائد تخلي النتيجة الفعلية تختلف."), ("Duration is a sensitivity estimate, not an exact forecast.", "المدة تقدير حساسية مو توقع دقيق."))], [
q("Coupon 50 and market price 900: current yield?", "كوبون 50 وسعر سوق 900، العائد الجاري؟", [("5%", "5%"),("5.56%", "5.56%"),("9%", "9%")],1,"50 ÷ 900 ≈ 5.56%.","50 ÷ 900 ≈ 5.56%."),
q("Required yield rises, fixed bond cash flows unchanged: price…", "العائد المطلوب يرتفع والتدفقات ثابتة: السعر…", [("Falls", "ينخفض"),("Rises", "يرتفع"),("Cannot change", "ما يتغير")],0,"Higher discount rates reduce present values.","معدل الخصم الأعلى يقلل القيمة الحالية."),
q("Duration 5, yields rise 1 percentage point: approximate price move?", "مدة خمسة والعائد يرتفع نقطة مئوية، تغير السعر التقريبي؟", [("+5%", "+5%"),("−1%", "−1%"),("−5%", "−5%")],2,"−5 × 0.01 = −0.05.","−5 × 0.01 = −0.05.")], "duration")

course("valuation_scenarios", "Advanced", ("Valuation Scenarios and Sensitivity", "سيناريوهات التقييم والحساسية"),
       ("Move from a single target price to a defensible range.", "انتقل من سعر مستهدف واحد لنطاق مبني على افتراضات."), "valuation", [
(("Match cash flow and discount rate", "طابق التدفق ومعدل الخصم"), ("Discount cash flows available to equity holders at the cost of equity. Cash flows available to all capital providers use a weighted average cost of capital and produce enterprise value. Mixing the two gives inconsistent values before you even choose growth assumptions.", "اخصم التدفقات المتاحة للمساهمين بتكلفة حقوق الملكية. التدفقات المتاحة لكل ممولي الشركة تستخدم المتوسط المرجح لتكلفة رأس المال وتعطي قيمة المنشأة. خلط النوعين يعطي تقييم غير متسق قبل حتى تختار النمو."), ("Define whose cash flow is being valued.", "حدد التدفق تابع لأي ممول.")),
(("A deliberately simple model", "نموذج مبسط بوضوح"), ("The lab values a constant-growth stream: next year's cash flow ÷ (discount rate − growth). Cash flow 100, discount rate 10% and growth 3% give 1,428.57. This is a steady-state teaching model, not a full valuation for a rapidly changing company.", "المختبر يقيّم تدفق ينمو بمعدل ثابت: تدفق السنة الجاية ÷ (معدل الخصم ناقص النمو). تدفق مئة وخصم 10% ونمو 3% يعطي 1,428.57. هذا نموذج تعليمي لحالة مستقرة، مو تقييم كامل لشركة سريعة التغير."), ("The discount rate must exceed perpetual growth.", "معدل الخصم لازم يتجاوز النمو الدائم.")),
(("Challenge the assumptions", "اختبر الافتراضات"), ("Build downside, base and upside cases from business drivers such as sales growth, margins and reinvestment. Sensitivity changes one assumption while holding others fixed; a scenario changes a coherent group. A probability-weighted value still depends on subjective assumptions.", "ابنِ حالة هبوط وأساسية وصعود من محركات مثل نمو المبيعات والهوامش وإعادة الاستثمار. الحساسية تغيّر افتراض وتثبت الباقي؛ السيناريو يغيّر مجموعة مترابطة. القيمة المرجحة بالاحتمالات تظل معتمدة على افتراضات تقديرية."), ("Explain the business assumptions behind the range.", "اشرح افتراضات النشاط اللي وراء النطاق."))], [
q("Equity cash flows should be discounted at…", "تدفقات المساهمين تنخصم بـ…", [("Inflation only", "التضخم فقط"),("Cost of equity", "تكلفة حقوق الملكية"),("Revenue growth", "نمو الإيرادات")],1,"Match equity cash flows with equity risk.","طابق تدفق المساهمين مع مخاطرتهم."),
q("100 ÷ (10% − 3%) is approximately…", "100 ÷ (10% ناقص 3%) يساوي تقريبًا…", [("1,428.57", "1,428.57"),("769.23", "769.23"),("100", "100")],0,"The denominator is 0.07.","المقام 0.07."),
q("If perpetual growth exceeds the discount rate…", "إذا النمو الدائم تجاوز معدل الخصم…", [("Value is reliable", "القيمة موثوقة"),("Profit is guaranteed", "الربح مضمون"),("The model is invalid", "النموذج غير صالح")],2,"The growing perpetuity requires discount rate above growth.","نموذج التدفق الدائم النامي يشترط الخصم أعلى من النمو.")], "valuation")

course("robustness", "Advanced", ("Backtest Robustness and Expectancy", "متانة الاختبار التاريخي والتوقع الرياضي"),
       ("Distinguish an attractive backtest from a repeatable process.", "فرّق بين اختبار جذاب وعملية قابلة للتكرار."), "research", [
(("Only use available information", "استخدم المعلومة المتاحة وقتها"), ("A backtest must use information that was available at each simulated decision. Selecting today's surviving companies introduces survivorship bias. Using a daily candle's high to raise a stop before that same candle's low can introduce look-ahead because daily data does not reveal their order.", "الاختبار لازم يستخدم المعلومات اللي كانت متاحة عند كل قرار افتراضي. اختيار الشركات الباقية اليوم يدخل تحيز البقاء. استخدام قمة الشمعة اليومية لرفع الوقف قبل قاع نفس الشمعة ممكن يدخل تحيز استشراف؛ البيانات اليومية ما تكشف ترتيب القمة والقاع."), ("Time alignment is part of correctness.", "تطابق التوقيت جزء من صحة الاختبار.")),
(("Expected result per trade", "النتيجة المتوقعة لكل صفقة"), ("Expected profit equals win probability times average win minus loss probability times average loss, minus average trading costs. A 40% win rate, average win 300, average loss 100 and cost 10 produce +50 per trade. This does not describe drawdown or guarantee the next trade.", "التوقع يساوي احتمال الفوز مضروب بمتوسط الربح، ناقص احتمال الخسارة مضروب بمتوسط الخسارة، ناقص متوسط التكلفة. نجاح 40% وربح متوسط 300 وخسارة 100 وتكلفة عشرة تعطي موجب خمسين للصفقة. هذا ما يصف التراجع ولا يضمن الصفقة الجاية."), ("Win rate alone cannot establish profitability.", "نسبة النجاح وحدها ما تثبت الربحية.")),
(("Test beyond the fitted sample", "اختبر خارج عينة التطوير"), ("Keep a chronological holdout that was not used for parameter selection. Include realistic costs, delisted securities when relevant, and checks across market regimes. Repeatedly inspecting the holdout turns it into part of the training process; preserve a final untouched test and consider paper trading.", "احتفظ بعينة زمنية لاحقة ما استخدمتها لاختيار الإعدادات. أضف تكاليف واقعية والشركات المشطوبة عند الحاجة وافحص ظروف سوق مختلفة. تكرار النظر لعينة الاختبار يدخلها في التطوير؛ احتفظ باختبار نهائي ما لمسته وفكر بالتداول التجريبي."), ("Robustness is evidence from multiple checks, not one perfect chart.", "المتانة دليل من عدة فحوص مو رسم مثالي واحد."))], [
q("Using information unavailable at the decision date is…", "استخدام معلومة ما كانت متاحة وقت القرار هو…", [("Diversification", "تنويع"),("Look-ahead bias", "تحيز استشراف"),("A transaction cost", "تكلفة تداول")],1,"The simulation is using future information.","المحاكاة تستخدم معلومات مستقبلية."),
q("40% win, 300 gain, 100 loss, 10 cost: expectancy?", "نجاح 40% وربح 300 وخسارة 100 وتكلفة 10، التوقع؟", [("50", "50"),("120", "120"),("−50", "−50")],0,"0.4 × 300 − 0.6 × 100 − 10 = 50.","0.4 × 300 − 0.6 × 100 − 10 = 50."),
q("Repeated tuning on the holdout…", "تكرار تعديل الإعدادات على عينة الاختبار…", [("Keeps it independent", "يخليها مستقلة"),("Eliminates all bias", "يلغي كل تحيز"),("Compromises independence", "يضعف استقلاليتها")],2,"The holdout becomes part of model selection.","العينة تصير جزء من اختيار النموذج.")], "expectancy")



# Beginner foundations: original bilingual lessons and worked examples.
EXTRA_COURSES.extend([{'id': 'money_foundations',
  'title': ('Before Your First Investment', 'قبل أول استثمار لك'),
  'tagline': ('Build a cash buffer and separate saving from investing.',
              'رتّب ميزانيتك وافصل فلوس الطوارئ عن الاستثمار.'),
  'art': 'plan',
  'level': ('Beginner', 'مبتدئ'),
  'icon': 'school',
  'mins': 6,
  'new': True,
  'sections': [('Know your monthly surplus',
                'اعرف فائضك الشهري',
                'Income minus essential spending and debt payments gives an initial savings budget. With '
                'income of 8,000, expenses of 5,500 and debt payments of 1,000, the remainder is 1,500. '
                'Allow for irregular annual bills before committing that full amount.',
                'دخل 8,000 ناقص مصروفات 5,500 وأقساط 1,000 يترك لك 1,500. هذا مو كله جاهز للاستثمار؛ احسب '
                'المصاريف السنوية وغير المنتظمة أول، مثل تأمين السيارة.',
                'Use money you can leave invested.',
                'استثمر بمبلغ تقدر تتركه فترة.',
                None),
               ('Create a cash buffer',
                'جهّز احتياطي للطوارئ',
                'Keep emergency money accessible and separate from volatile investments. The right amount '
                'depends on essential expenses, income stability and dependants. For practice, 4,000 of '
                'monthly essentials times four months equals a 16,000 buffer; four months is an '
                'illustration, not a universal target.',
                'خل فلوس الطوارئ سهلة الوصول وبعيدة عن الاستثمارات المتقلبة. المبلغ يعتمد على التزاماتك '
                'واستقرار دخلك ومن تعول. مثال للتدريب: مصاريف أساسية 4,000 لأربعة أشهر تعني احتياطي 16,000؛ '
                'الأربعة أشهر مثال مو قاعدة للجميع.',
                'A cash buffer reduces forced selling.',
                'الاحتياطي يقلل حاجتك للبيع بوقت غير مناسب.',
                None),
               ('Compare debt and investing',
                'قارن تكلفة الدين بالاستثمار',
                'Paying costly debt avoids financing charges under the contract; investment returns are '
                'uncertain. Check repayment terms and retain necessary liquidity. Money needed for a '
                'near-term bill has a different job from money set aside for a distant goal.',
                'سداد الدين المكلف يوفر تكلفة تمويل حسب شروط العقد، أما عائد الاستثمار مو مضمون. راجع شروط '
                'السداد واحتفظ بالسيولة الضرورية. فلوس فاتورة قريبة تختلف وظيفتها عن فلوس هدف بعيد.',
                'Compare certain costs with uncertain returns.',
                'لا تقارن تكلفة مؤكدة بربح تتمنى تحققه.',
                None)],
  'quiz': [('What remains from 8,000 after 5,500 and 1,000?',
            'كم يبقى من 8,000 بعد 5,500 و1,000؟',
            [('1,500', '1,500'), ('2,500', '2,500'), ('3,500', '3,500')],
            0,
            '8,000 − 5,500 − 1,000 = 1,500.',
            '8,000 − 5,500 − 1,000 = 1,500.'),
           ('Emergency money should prioritise…',
            'فلوس الطوارئ أولويتها…',
            [('Maximum stock returns', 'أعلى عائد أسهم'),
             ('Accessibility and stability', 'سهولة الوصول والاستقرار'),
             ('Borrowed leverage', 'الاقتراض')],
            1,
            'You may need it when markets are down.',
            'ممكن تحتاجها والسوق نازل.'),
           ('Why compare debt costs first?',
            'ليه تقارن تكلفة الدين أول؟',
            [('Stocks guarantee more', 'الأسهم تضمن أكثر'),
             ('Debt has no cost', 'الدين بلا تكلفة'),
             ('Investment returns are uncertain', 'عائد الاستثمار غير مؤكد')],
            2,
            'Avoided financing costs differ from a hoped-for market return.',
            'تكلفة التمويل اللي توفرها تختلف عن عائد سوق تتمناه.')]},
 {'id': 'diversification_basics',
  'title': ('Diversification Without the Jargon', 'التنويع بدون تعقيد'),
  'tagline': ('Understand concentration before building a portfolio.', 'افهم التركز قبل ما تبني محفظتك.'),
  'art': 'allocation',
  'level': ('Beginner', 'مبتدئ'),
  'icon': 'school',
  'mins': 6,
  'new': True,
  'sections': [('Count exposures, not tickers',
                'عدّ مصادر الخطر مو الرموز',
                'Five companies in the same industry can share the same risk. If all rely on one customer or '
                'one commodity, more names may provide little protection. Look at sectors, countries, asset '
                'classes and the economic forces behind earnings.',
                'خمس شركات بنفس الصناعة ممكن تتأثر بنفس الخطر. لو تعتمد على عميل واحد أو سلعة وحدة، زيادة '
                'الأسماء ما تكفي. شوف القطاعات والدول وفئات الأصول والعوامل اللي تحرك أرباحها.',
                'Different names can hide similar risks.',
                'الأسماء المختلفة ممكن تخفي نفس المخاطر.',
                None),
               ('Measure concentration',
                'احسب التركز',
                'A 10,000 portfolio with 6,000 in one company has 60% exposure to it. If that holding loses '
                'half its value and everything else stays flat, the portfolio loses 3,000, or 30%. This is a '
                'hypothetical stress test, not a forecast.',
                'محفظة 10,000 فيها 6,000 بشركة وحدة يعني تركز 60%. لو سهمها خسر نصف قيمته والباقي ثابت، '
                'المحفظة تخسر 3,000 يعني 30%. هذا اختبار افتراضي للمخاطرة مو توقع.',
                'Position size determines how much one mistake hurts.',
                'حجم المركز يحدد أثر الخطأ على محفظتك.',
                None),
               ('Know the limits',
                'افهم حدود التنويع',
                'Diversification can reduce company-specific risk but cannot eliminate a broad market '
                'decline. Two funds may own the same companies, so inspect their holdings. Choose a mix that '
                'fits your goal and ability to absorb losses rather than treating a fixed number of holdings '
                'as a guarantee.',
                'التنويع يقلل مخاطر الشركة الواحدة، لكنه ما يلغي هبوط السوق كله. صندوقين ممكن يملكون نفس '
                'الشركات، فراجع المكونات. اختَر توزيع يناسب هدفك وقدرتك على الخسارة، ولا تعتبر عدد معين من '
                'الأسهم ضمان.',
                'Diversification manages risk; it does not promise profits.',
                'التنويع يدير المخاطر، ما يضمن الربح.',
                None)],
  'quiz': [('Five stocks in one industry guarantee diversification?',
            'خمس شركات بنفس الصناعة تضمن التنويع؟',
            [('Yes', 'نعم'), ('No', 'لا'), ('Only if prices rise', 'إذا ارتفعت فقط')],
            1,
            'They can share the same economic risks.',
            'ممكن تشترك بنفس المخاطر الاقتصادية.'),
           ('6,000 in a 10,000 portfolio is…',
            '6,000 من محفظة 10,000 تساوي…',
            [('6%', '6%'), ('40%', '40%'), ('60%', '60%')],
            2,
            '6,000 ÷ 10,000 = 60%.',
            '6,000 ÷ 10,000 = 60%.'),
           ('What can diversification reduce?',
            'وش ممكن يقلله التنويع؟',
            [('Company-specific risk', 'مخاطر الشركة الواحدة'),
             ('Every possible loss', 'كل خسارة ممكنة'),
             ('All market risk', 'كل مخاطر السوق')],
            0,
            'Broad market risk can remain.',
            'مخاطر السوق العامة ممكن تبقى.')]},
 {'id': 'returns_costs',
  'title': ('Your Real Profit: Returns and Costs', 'ربحك الفعلي: العائد والتكاليف'),
  'tagline': ('Calculate gains, distributions and fees with simple numbers.',
              'احسب تغير السعر والتوزيعات والرسوم بأرقام بسيطة.'),
  'art': 'growth',
  'level': ('Beginner', 'مبتدئ'),
  'icon': 'school',
  'mins': 6,
  'new': True,
  'sections': [('Price return is not total return',
                'عائد السعر مو العائد الكلي',
                'Buy one share for 100, receive a cash dividend of 3, then sell for 105. Before fees and '
                'taxes, profit is 8 and holding-period return is 8%. This example assumes no other cash '
                'flows and no dividend reinvestment.',
                'اشتريت سهم بـ100 واستلمت توزيع نقدي 3 وبعته بـ105. قبل الرسوم والضرائب، ربحك 8 وعائد فترة '
                'الاحتفاظ 8%. نفترض ما فيه تدفقات ثانية ولا إعادة استثمار للتوزيع.',
                'Include distributions when measuring performance.',
                'احسب التوزيعات وأنت تقيس الأداء.',
                None),
               ('Include both sides of the trade',
                'احسب تكلفة الدخول والخروج',
                'Add a buy fee of 1 and a sell fee of 1 to that example. Initial outlay is 101 and net '
                'receipts are 107, so profit is 6 and net return is 6 ÷ 101, about 5.94%. Currency '
                'conversion and other charges may reduce it further; tax treatment depends on your '
                'situation.',
                'نضيف رسوم شراء 1 ورسوم بيع 1 لنفس المثال. دفعت 101 واستلمت صافي 107 مع التوزيع، فالربح 6 '
                'والعائد 6 ÷ 101، تقريبًا 5.94%. تحويل العملة ورسوم ثانية ممكن تقلله، والضريبة تعتمد على '
                'حالتك.',
                'Measure the return on what you actually paid.',
                'احسب العائد على اللي دفعته فعليًا.',
                None),
               ('A deposit is not a gain',
                'الإيداع مو ربح',
                'An account starts with 1,000 and receives a 500 deposit. If it ends at 1,500, it has no '
                'investment gain. Also, a 20% drop followed by a 20% rise takes 100 to 80 to 96: percentage '
                'changes compound and do not simply cancel.',
                'حساب بدأ بـ1,000 وأضفت له 500 وصار 1,500؛ ما حقق ربح استثماري. وبرضو نزول 20% ثم ارتفاع 20% '
                'يحول 100 إلى 80 ثم 96؛ النسب تتراكم وما تلغي بعض ببساطة.',
                'Separate deposits from performance.',
                'افصل الإيداعات عن أداء الاستثمار.',
                None)],
  'quiz': [('Buy at 100, sell at 105, receive 3: gross return?',
            'شراء بـ100 وبيع بـ105 وتوزيع 3: كم العائد قبل التكاليف؟',
            [('3%', '3%'), ('5%', '5%'), ('8%', '8%')],
            2,
            '(105 − 100 + 3) ÷ 100 = 8%.',
            '(105 − 100 + 3) ÷ 100 = 8%.'),
           ('A 500 deposit increases a 1,000 account to 1,500. Gain?',
            'إيداع 500 رفع حساب 1,000 إلى 1,500. كم الربح؟',
            [('Zero', 'صفر'), ('500', '500'), ('50%', '50%')],
            0,
            'The increase came entirely from your contribution.',
            'الزيادة كلها من إيداعك.'),
           ('100 falls 20%, then rises 20%. Final value?',
            '100 نزلت 20% ثم ارتفعت 20%. كم تصير؟',
            [('100', '100'), ('96', '96'), ('104', '104')],
            1,
            '100 × 0.8 × 1.2 = 96.',
            '100 × 0.8 × 1.2 = 96.')]},
 {'id': 'broker_safety',
  'title': ('Choose a Broker and Avoid Scams', 'اختيار الوسيط وتجنب الاحتيال'),
  'tagline': ('Check authorisation, account terms and warning signs.',
              'تحقق من الترخيص وشروط الحساب وعلامات الاحتيال.'),
  'art': 'research',
  'level': ('Beginner', 'مبتدئ'),
  'icon': 'school',
  'mins': 6,
  'new': True,
  'sections': [('Verify independently',
                'تحقق من جهة مستقلة',
                "Use the relevant regulator's official register to check the legal entity, its permitted "
                'activity and its contact details. Match the website and phone number independently: a '
                'copied licence image is not verification. Authorisation does not insure you against market '
                'losses.',
                'ارجع لسجل الجهة الرقابية الرسمي وتحقق من الاسم القانوني والنشاط المسموح وبيانات التواصل. '
                'طابق الموقع والرقم من مصدر مستقل؛ صورة الترخيص ما تكفي. الترخيص ما يحميك من خسائر السوق.',
                'Check the entity and the activity, not just the brand.',
                'تحقق من الكيان والنشاط مو الاسم التجاري بس.',
                None),
               ('Understand the account',
                'افهم الحساب قبل تمويله',
                'Compare dealing, currency-conversion, custody and withdrawal fees. Read how assets are held '
                'and what protections apply. A cash account uses your paid-in money; a margin account allows '
                'borrowing and adds financing costs and forced-sale risk. Do not enable borrowing just '
                'because the app offers it.',
                'قارن عمولات التداول وتحويل العملة والحفظ والسحب. اقرأ كيف تحفظ الأصول وأي حماية تنطبق '
                'عليها. الحساب النقدي يستخدم فلوسك، وحساب الهامش يسمح بالاقتراض ويضيف تكلفة تمويل واحتمال '
                'بيع إجباري. لا تفعل الاقتراض لمجرد أنه متاح.',
                'Account features create obligations as well as convenience.',
                'مزايا الحساب ممكن تضيف التزامات.',
                None),
               ('Recognise pressure and promises',
                'انتبه للضغط والوعود',
                'A promise of high guaranteed returns, pressure to transfer immediately or a request to send '
                'funds to a personal account deserves scrutiny. Stop, verify through official channels and '
                'keep records. Never give a caller your password or verification code.',
                'وعد بعائد مرتفع مضمون، أو ضغط للتحويل فورًا، أو طلب تحويل لحساب شخصي كلها إشارات تستدعي '
                'التوقف. تحقق بالقنوات الرسمية واحتفظ بالسجلات. لا تعطي المتصل كلمة المرور أو رمز التحقق.',
                'Verification comes before transferring money.',
                'التحقق قبل التحويل.',
                None)],
  'quiz': [('Best way to verify a broker?',
            'أفضل طريقة تتحقق من الوسيط؟',
            [('Its advertisement', 'إعلانه'),
             ("The regulator's official register", 'السجل الرسمي للجهة الرقابية'),
             ('A forwarded licence image', 'صورة ترخيص مرسلة')],
            1,
            'Check the legal entity and activity independently.',
            'تحقق من الكيان والنشاط بشكل مستقل.'),
           ('A margin account adds…',
            'حساب الهامش يضيف…',
            [('Guaranteed gains', 'أرباح مضمونة'),
             ('No obligations', 'بلا التزامات'),
             ('Borrowing and forced-sale risk', 'اقتراض واحتمال بيع إجباري')],
            2,
            'Borrowing can magnify losses.',
            'الاقتراض ممكن يضخم الخسائر.'),
           ('Someone asks for your verification code. You…',
            'شخص يطلب رمز التحقق. وش تسوي؟',
            [('Do not share it', 'ما تشاركه'),
             ('Share it if polite', 'تعطيه إذا كان محترم'),
             ('Send half', 'ترسل نصفه')],
            0,
            'Keep account credentials private.',
            'خل بيانات الدخول سرية.')]}])

VIDEOS = [{'id': 'plan_ar',
  'title': ('Your financial plan', 'الخلطة المالية'),
  'creator': 'ثمين · هيئة السوق المالية',
  'language': 'ar',
  'url': 'https://www.youtube.com/watch?v=pn6vkahXHDk',
  'courses': ['money_foundations', 'goals'],
  'note': ('A short introduction to matching your money decisions to your '
           'goals.',
           'مقدمة قصيرة تربط قراراتك المالية بأهدافك.')},
 {'id': 'saving_ar',
  'title': ('Saving and investing', 'الادخار والاستثمار'),
  'creator': 'ثمين · هيئة السوق المالية',
  'language': 'ar',
  'url': 'https://www.youtube.com/watch?v=qP15-FXl1ro',
  'courses': ['money_foundations', 'goals', 'funds', 'diversification_basics'],
  'note': ('An introductory conversation about saving and investment choices.',
           'لقاء تمهيدي عن الادخار والخيارات الاستثمارية. شاهد على مراحل ودوّن '
           'الفرق بين الادخار والاستثمار.')},
 {'id': 'safety_ar',
  'title': ('Investor protection', 'حماية المستثمر'),
  'creator': 'ثمين · هيئة السوق المالية',
  'language': 'ar',
  'url': 'https://www.youtube.com/watch?v=F1G5z5UcJ2M',
  'courses': ['broker_safety'],
  'note': ('Broker role at 08:00; fraud cases at 13:25.',
           'دور الوسيط عند 08:00، وقضايا الاحتيال عند 13:25.')},
 {'id': 'stocks_bonds',
  'title': ('Stocks versus bonds', 'الفرق بين الأسهم والسندات'),
  'creator': 'Khan Academy',
  'language': 'en',
  'url': 'https://www.youtube.com/watch?v=rs1md3e4aYU',
  'courses': ['basics', 'diversification_basics', 'funds', 'bonds'],
  'note': ('Compare owning a part of a business with lending to it.',
           'قارن بين امتلاك جزء من الشركة وإقراضها.')},
 {'id': 'compound',
  'title': ('Compound interest introduction', 'مقدمة في العائد المركب'),
  'creator': 'Khan Academy',
  'language': 'en',
  'url': 'https://www.youtube.com/watch?v=Rm6UdfRs3gw',
  'courses': ['compounding'],
  'note': ('Follow how returns build on earlier returns.',
           'تابع كيف يتراكم العائد على العائد السابق.')},
 {'id': 'risk_return',
  'title': ('What is risk and return?', 'وش العلاقة بين المخاطرة والعائد؟'),
  'creator': 'Khan Academy',
  'language': 'en',
  'url': 'https://www.youtube.com/watch?v=7mo167ohvJw',
  'courses': ['returns_costs', 'diversification_basics', 'risk', 'allocation'],
  'note': ('An introduction to the trade-off between potential return and '
           'risk.',
           'مقدمة عن العلاقة بين العائد المحتمل والمخاطر.')},
 {'id': 'bonds_intro',
  'title': ('Introduction to bonds', 'مقدمة في السندات'),
  'creator': 'Khan Academy',
  'language': 'en',
  'url': 'https://www.youtube.com/watch?v=Qh-M3_L4xYk',
  'courses': ['bonds'],
  'note': ('Understand lending, interest payments and maturity.',
           'افهم الإقراض ودفعات الفائدة والاستحقاق.')}]
COURSE_SOURCES = {'broker_safety': [('ثمين — وعيك يحميك',
                    'https://thameen.cma.gov.sa/your-awareness-protects-you/')],
 'diversification_basics': [('Asset allocation and diversification',
                             'https://www.investor.gov/introduction-investing/getting-started/asset-allocation')],
 'money_foundations': [('Emergency savings',
                        'https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/save-rainy-day'),
                       ('High-interest debt',
                        'https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/pay-credit-cards-or-other-high-interest')],
 'returns_costs': [('Understanding fees',
                    'https://www.investor.gov/introduction-investing/getting-started/understanding-fees')]}
