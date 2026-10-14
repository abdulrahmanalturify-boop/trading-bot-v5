"""Short bilingual lessons and offline exercises. Stable course IDs are permanent."""
ACADEMY_REVISION = "2026-10-14.2"
# The exact catalog order used by the previous index-based progress format.
LEGACY_IDS = ('money_foundations','goals','basics','broker_safety','diversification_basics','funds','compounding','returns_costs','inflation','execution','statements','behaviour','candles','levels','risk','allocation','quality','bonds','ma','momentum','value','macro','options','valuation_scenarios','robustness')
MICRO_COURSES = []

def add(cid, title, tagline, art, lessons, quiz, lab=None):
    MICRO_COURSES.append(dict(id=cid,title=title,tagline=tagline,art=art,
        level=('Beginner','مبتدئ'),icon='school',mins=4,new=True,micro=True,
        sections=[(*heading,*body,*takeaway,lab if i==1 else None)
                  for i,(heading,body,takeaway) in enumerate(lessons)],quiz=quiz))

def q(en,ar,options,correct,why_en,why_ar):
    return (en,ar,options,correct,why_en,why_ar)

add('price_value',('Price Is Not Value','السعر مو هو القيمة'),('Separate the share price from what the business is worth.','فرّق بين سعر السهم وقيمة الشركة.'),'value',[
(('A small price tag','سعر صغير'),('A share at 5 is not automatically cheaper than one at 500. The number of shares and the earnings behind each share matter. Compare what you receive for the price.','سهم بخمسة مو بالضرورة أرخص من سهم بخمسمية. عدد الأسهم والأرباح وراء كل سهم تفرق. قارن وش تحصل عليه مقابل اللي تدفعه.'),('Low share price does not mean low valuation.','سعر السهم المنخفض ما يعني تقييم رخيص.')),
(('Compare the whole company','قارن الشركة كاملة'),('Company A has 1,000 shares at 5: equity market value is 5,000. Company B has 5 shares at 500: equity market value is 2,500. Despite the lower share price, A has the larger equity value.','شركة عندها ألف سهم بسعر خمسة: قيمتها السوقية خمسة آلاف. شركة ثانية عندها خمسة أسهم بسعر خمسمية: قيمتها ألفين وخمسمية. الأولى سعر سهمها أقل، لكن قيمتها السوقية أكبر.'),('Market value = price × shares outstanding.','القيمة السوقية = السعر × عدد الأسهم القائمة.')),
(('Value needs assumptions','القيمة تحتاج افتراضات'),('An estimated value depends on future cash flows, growth and risk. Different assumptions produce different values. Write a range and what would change your view before deciding.','القيمة المقدرة تعتمد على التدفقات النقدية والنمو والمخاطر. تغيير الافتراضات يغيّر النتيجة. اكتب نطاق للقيمة ووش يغيّر رأيك قبل القرار.'),('A value estimate is not a guaranteed future price.','التقييم تقدير مو سعر مستقبلي مضمون.'))], [
q('Which share is automatically cheaper?','أي سهم أرخص بالضرورة؟',[('The 5 share','السهم بخمسة'),('The 500 share','السهم بخمسمية'),('Neither from price alone','ما نعرف من السعر لحاله')],2,'Price alone cannot establish value.','السعر لحاله ما يكفي لتحديد القيمة.'),
q('1,000 shares at 5 have market value…','ألف سهم بسعر خمسة، قيمتها السوقية…',[('5,000','5,000'),('1,000','1,000'),('500','500')],0,'Multiply shares by price.','نضرب الأسهم في السعر.'),
q('What can change an estimated value?','وش ممكن يغيّر التقييم؟',[('Only the ticker','رمز الشركة فقط'),('Growth and risk assumptions','افتراضات النمو والمخاطر'),('Nothing','ولا شيء')],1,'Valuation depends on assumptions.','التقييم يعتمد على الافتراضات.')], 'micro_marketcap')

add('total_return',('Your Real Profit in Numbers','كم ربحت فعليًا؟'),('Include dividends and costs in a simple return calculation.','احسب التوزيعات والتكاليف مع الربح.'),'growth',[
(('More than the chart','أكثر من حركة السعر'),('Buying at 100 and selling at 110 creates a price gain of 10 per share. If you also received 2 in cash dividends, the gross gain is 12, before fees and taxes.','اشتريت بمية وبعت بمية وعشرة: ربح السعر عشرة للسهم. لو استلمت توزيعات بريالين، الربح الإجمالي يصير 12 قبل الرسوم والضرائب.'),('Total return includes price change and distributions.','العائد الكلي يشمل تغير السعر والتوزيعات.')),
(('Subtract costs','اطرح التكاليف'),('For one share, pay 100 plus a 1 purchase fee. Sell at 110, pay a 1 sale fee and receive 2 dividends. Ending proceeds are 111 versus 101 invested: a gain of 10 and a return of 9.90%.','لسهم واحد دفعت 100 ورسوم شراء 1. بعت بـ110 ودفعت رسوم بيع 1 واستلمت توزيعات 2. اللي رجع لك 111 مقابل 101 دفعتها: ربح 10 وعائد 9.90%.'),('Use the full cash outlay as the denominator.','احسب العائد على كامل المبلغ اللي دفعته.')),
(('Compare the same period','قارن نفس المدة'),('A 10% return in one month and 10% in three years are not equivalent. Compare equal periods and similar risks. Taxes and currency changes can further change your own result.','عائد 10% بشهر يختلف عن 10% بثلاث سنوات. قارن مدد ومخاطر متشابهة. الضرائب وتغير العملة ممكن يغيّرون نتيجتك بعد.'),('Always label the period and whether costs are included.','وضّح المدة وهل حسبت التكاليف.'))],[
q('100 becomes 110 plus 2 dividends: gross gain?','100 صارت 110 ومعها توزيعات 2، الربح الإجمالي؟',[('10','10'),('12','12'),('2','2')],1,'110 − 100 + 2 = 12.','110 − 100 + 2 = 12.'),
q('What is the full initial outlay with a 1 fee?','كم المبلغ المدفوع لو السعر 100 ورسوم الشراء 1؟',[('100','100'),('99','99'),('101','101')],2,'The purchase fee is part of the initial outlay.','رسوم الشراء ضمن المبلغ المدفوع.'),
q('Which comparison is meaningful?','أي مقارنة أوضح؟',[('Same period and similar risk','نفس المدة ومخاطر متشابهة'),('Any two percentages','أي نسبتين'),('Price changes only','تغير السعر فقط')],0,'Period and risk affect interpretation.','المدة والمخاطر تؤثر على المقارنة.')], 'micro_return')

add('loss_recovery',('Why Losses Need Bigger Gains','ليش تعويض الخسارة أصعب؟'),('Try a drawdown and calculate the gain needed to recover.','جرّب الهبوط واحسب الارتفاع المطلوب للتعويض.'),'risk',[
(('A smaller base','المبلغ صار أصغر'),('Start with 1,000. A 20% loss leaves 800. A later 20% gain adds only 160, taking you to 960. The same percentage now applies to a smaller amount.','معك ألف وخسرت 20%، يبقى 800. ارتفاع 20% بعدها يضيف 160 فقط وتوصل 960. النسبة نفسها صارت محسوبة على مبلغ أصغر.'),('Equal loss and gain percentages do not cancel.','نسبة هبوط وارتفاع متساوية ما تلغي بعض.')),
(('Calculate recovery','احسب التعويض'),('Required gain = loss percentage ÷ (100 − loss percentage) × 100. A 20% loss needs 25%; a 50% loss needs 100%. Try changing the loss in the exercise.','الارتفاع المطلوب = نسبة الخسارة ÷ (100 ناقص نسبة الخسارة) × 100. خسارة 20% تحتاج 25%، وخسارة 50% تحتاج 100%. غيّر الخسارة بالتطبيق.'),('Deep losses require disproportionately larger gains.','الخسائر الكبيرة تحتاج مكاسب أكبر بكثير.')),
(('Control exposure','اضبط حجم المخاطرة'),('Position size and diversification influence the damage a single holding can do. A stop order can execute below its trigger after a gap; it does not guarantee the planned loss.','حجم المركز والتنويع يحددون أثر سهم واحد على محفظتك. أمر الوقف ممكن يتنفذ تحت سعر التفعيل بعد فجوة؛ ما يضمن الخسارة المخطط لها.'),('Plan for worse outcomes as well as the expected one.','احسب احتمال نتيجة أسوأ من المتوقع.'))],[
q('1,000 falls 20% then rises 20%. Final value?','ألف نزلت 20% ثم ارتفعت 20%، كم تصير؟',[('1,000','1,000'),('960','960'),('1,040','1,040')],1,'800 × 1.2 = 960.','800 × 1.2 = 960.'),
q('A 50% loss needs which gain to recover?','خسارة 50% تحتاج كم للتعويض؟',[('50%','50%'),('25%','25%'),('100%','100%')],2,'The remaining half must double.','النصف المتبقي يحتاج يتضاعف.'),
q('Does a stop guarantee its trigger price?','هل أمر الوقف يضمن سعر التفعيل؟',[('No','لا'),('Always','دائمًا'),('Only in gaps','وقت الفجوات فقط')],0,'Execution may slip, especially after gaps.','سعر التنفيذ ممكن يختلف خصوصًا بعد فجوة.')], 'micro_recovery')

add('spread_basics',('The Hidden Cost of the Spread','تكلفة الفرق بين البيع والشراء'),('See why buying and immediately selling can lose money.','شف ليش الشراء والبيع مباشرة ممكن يخسّرك.'),'orders',[
(('Two prices','سعرين مو سعر واحد'),('The bid is the price a buyer currently offers. The ask is what a seller currently requests. With a bid of 99 and ask of 101, an immediate buyer generally pays 101, subject to available size and changing quotes.','سعر الشراء المعروض من المشترين 99 وسعر البيع المطلوب 101. لو بتشتري فورًا غالبًا تدفع 101، حسب الكمية المتاحة وتغير الأسعار.'),('The spread is ask minus bid.','السبريد هو سعر الطلب ناقص سعر العرض.')),
(('A round trip','شراء ثم بيع'),('Buy one share at 101 and immediately sell at 99, assuming unchanged quotes. You lose 2 before commissions. A narrow spread reduces this particular cost but does not remove investment risk.','اشتريت سهم بـ101 وبعته مباشرة بـ99 مع ثبات الأسعار. خسرت 2 قبل العمولة. الفرق الضيق يقلل هالتكلفة لكنه ما يلغي مخاطر الاستثمار.'),('Execution costs exist even with zero commission.','فيه تكلفة تنفيذ حتى لو العمولة صفر.')),
(('Liquidity changes','السيولة تتغير'),('Spreads can widen when trading is thin or news arrives. A limit order controls your worst acceptable price, but may not fill. Check the quote and available size before confirming.','الفرق ممكن يتسع مع ضعف التداول أو الأخبار. الأمر المحدد يضبط أسوأ سعر تقبله لكنه ممكن ما يتنفذ. راجع السعر والكمية قبل التأكيد.'),('Check the spread, not only the last traded price.','راجع الفرق، مو بس آخر سعر تداول.'))],[
q('Bid 99, ask 101: spread?','العرض 99 والطلب 101، الفرق؟',[('2','2'),('100','100'),('0','0')],0,'101 − 99 = 2.','101 − 99 = 2.'),
q('Immediate purchase usually uses which side?','الشراء الفوري عادة بأي جهة؟',[('Bid','عرض المشترين'),('Ask','طلب البائعين'),('Yesterday close','إغلاق أمس')],1,'You buy from a willing seller.','تشتري من البائع المتاح.'),
q('Zero commission means zero trading costs?','عمولة صفر تعني تكاليف تداول صفر؟',[('Yes','نعم'),('Only at noon','وقت الظهر فقط'),('No, the spread still matters','لا، فرق السعر يظل مهم')],2,'The spread is an implicit cost.','فرق السعر تكلفة غير مباشرة.')], 'micro_spread')

add('limit_practice',('Place Your First Limit Order','جرّب أول أمر محدد'),('Practise price control before placing a real order.','تدرّب على تحديد السعر قبل تنفيذ أمر حقيقي.'),'orders',[
(('Set your boundary','حدد حدّك'),('A buy limit of 50 means pay 50 or less. It is not an instruction to buy at any price. Check quantity, symbol and order expiry as well as price.','أمر شراء محدد بـ50 يعني تدفع 50 أو أقل. مو أمر شراء بأي سعر. راجع الكمية والرمز وصلاحية الأمر مع السعر.'),('A buy limit sets the maximum acceptable purchase price.','حد الشراء يحدد أعلى سعر تقبله.')),
(('Will it fill?','هل يتنفذ؟'),('If the lowest ask is 51, a buy limit at 50 is not immediately executable. If the ask becomes 49, it may execute at 49 or another available price up to 50, depending on quantity and queue priority.','لو أقل طلب بيع 51 وأمرك شراء بـ50، ما يتنفذ فورًا. لو الطلب صار 49، ممكن يتنفذ بـ49 أو سعر متاح حتى 50 حسب الكمية وأولوية الدور.'),('Touching a price does not guarantee a complete fill.','وصول السعر للحد ما يضمن تنفيذ الكمية كاملة.')),
(('Review before confirming','راجع قبل التأكيد'),('A sell limit sets a minimum sale price. An order can be partly filled or expire unfilled. Check the broker’s status instead of assuming the whole order executed.','أمر البيع المحدد يحدد أقل سعر بيع تقبله. ممكن يتنفذ جزء أو تنتهي الصلاحية بدون تنفيذ. راجع حالة الأمر عند الوسيط ولا تفترض أنه تنفذ كامل.'),('Price control comes with execution uncertainty.','التحكم بالسعر معه احتمال عدم التنفيذ.'))],[
q('Buy limit 50 allows a fill at…','شراء محدد بـ50 يسمح بتنفيذ عند…',[('52','52'),('49','49'),('Any price','أي سعر')],1,'49 is below the maximum.','49 أقل من الحد الأعلى.'),
q('Ask 51, buy limit 50: immediately executable?','طلب البيع 51 وحد شراءك 50، يتنفذ فورًا؟',[('No','لا'),('Yes','نعم'),('Always partly','دائمًا جزئيًا')],0,'The ask exceeds your limit.','طلب البائع أعلى من حدك.'),
q('A sell limit sets…','الأمر المحدد للبيع يحدد…',[('Maximum purchase price','أعلى سعر شراء'),('Guaranteed completion time','وقت تنفيذ مضمون'),('Minimum sale price','أقل سعر بيع')],2,'Sell limits protect a minimum sale price.','الحد يحدد أقل سعر تقبله للبيع.')])

add('marketcap_split',('Market Value and Stock Splits','القيمة السوقية وتجزئة الأسهم'),('Understand what changes when one share becomes two.','افهم وش يتغير لما السهم يصير سهمين.'),'market',[
(('The whole equity value','قيمة الملكية كاملة'),('Multiply shares outstanding by the share price to get market capitalization. This is equity value, not enterprise value; debt and cash also matter when valuing the operating business.','اضرب الأسهم القائمة في سعر السهم عشان تطلع القيمة السوقية لحقوق المساهمين. هذي غير قيمة المنشأة؛ الديون والكاش لهم دور بتقييم النشاط.'),('Share count is as important as share price.','عدد الأسهم مهم مثل السعر.')),
(('A two-for-one split','تجزئة اثنين لواحد'),('Before a two-for-one split you own 10 shares at 100. Mechanically you then own 20 at an adjusted price of 50: the same 1,000 total. Actual trading can still move the price.','قبل التجزئة عندك عشرة أسهم بسعر مية. بعدها يصيرون عشرين بسعر معدل خمسين: نفس الألف. التداول الفعلي ممكن يحرّك السعر طبعًا.'),('A split alone creates no extra ownership value.','التجزئة بحد ذاتها ما تزيد قيمة ملكيتك.')),
(('Watch dilution','انتبه للتخفيف'),('Issuing new shares is different from a proportional split. If you hold 10 of 100 shares, your ownership is 10%. If total shares rise to 125 while you still hold 10, your stake becomes 8%. The cash raised also matters for value.','إصدار أسهم جديدة يختلف عن التجزئة المتناسبة. لو تملك 10 من 100، حصتك 10%. إذا صارت الأسهم 125 وأنت باقي عندك 10، حصتك تصير 8%. الكاش اللي جمعته الشركة مهم للقيمة بعد.'),('Track your percentage ownership, not just share count.','تابع نسبة ملكيتك مو عدد أسهمك بس.'))],[
q('20 shares at 50 are worth…','عشرين سهم بسعر خمسين، قيمتها…',[('1,000','1,000'),('2,000','2,000'),('500','500')],0,'20 × 50 = 1,000.','20 × 50 = 1,000.'),
q('Does a proportional split alone make you richer?','التجزئة المتناسبة لحالها تزيد ثروتك؟',[('Yes','نعم'),('No','لا'),('Always doubles it','تضاعفها دائمًا')],1,'Share count and adjusted price offset.','عدد الأسهم والسعر المعدل يعوضون بعض.'),
q('10 out of 125 shares represent…','عشرة أسهم من 125 تمثل…',[('10%','10%'),('12.5%','12.5%'),('8%','8%')],2,'10 ÷ 125 = 8%.','10 ÷ 125 = 8%.')], 'micro_marketcap')

add('dividend_basics',('Dividends Without the Hype','التوزيعات بدون مبالغة'),('Distinguish cash income from a guaranteed return.','فرّق بين الدخل النقدي والعائد المضمون.'),'fund',[
(('Cash from the company','كاش من الشركة'),('A dividend distributes cash to shareholders when declared. It is not guaranteed: a company may reduce or suspend payments. Cash leaving the business is no longer available for reinvestment there.','التوزيعات مبلغ تدفعه الشركة للمساهمين بعد إعلانه. مو مضمون؛ الشركة ممكن تقلله أو توقفه. الكاش اللي طلع ما عاد متاح لإعادة الاستثمار داخل الشركة.'),('Dividends are one part of total return.','التوزيعات جزء من العائد الكلي.')),
(('Calculate the yield','احسب العائد'),('An annual dividend of 4 on a price of 100 gives a 4% yield. If price falls to 50 and the dividend stays 4, yield becomes 8%. The increase may reflect a falling price, not a healthier business.','توزيع سنوي أربعة وسعر السهم مية يعطي 4%. لو السعر نزل لخمسين والتوزيع ثابت، العائد يصير 8%. ارتفاع النسبة ممكن سببه هبوط السعر مو تحسن الشركة.'),('High yield can be a warning, not a bargain.','العائد العالي ممكن يكون تنبيه مو فرصة.')),
(('No free money','مو فلوس مجانية'),('All else equal, a share’s price adjusts for the distribution on the ex-dividend date. Check payment sustainability and total return rather than buying only to collect the next payment.','مع ثبات العوامل الثانية، السعر يتعدل بأثر التوزيع في يوم التداول بدون أحقية. راجع استدامة التوزيع والعائد الكلي بدل الشراء بس عشان الدفعة الجاية.'),('Assess the business behind the distribution.','قيّم النشاط اللي يمول التوزيع.'))],[
q('4 annual dividend ÷ 100 price equals…','توزيع سنوي 4 وسعر 100 يعطي…',[('25%','25%'),('4%','4%'),('40%','40%')],1,'4 ÷ 100 = 4%.','4 ÷ 100 = 4%.'),
q('Yield can rise because…','عائد التوزيع ممكن يرتفع لأن…',[('Price falls','السعر نزل'),('It is guaranteed','صار مضمون'),('Risk disappeared','المخاطر اختفت')],0,'Yield divides the dividend by price.','نقسم التوزيع على السعر.'),
q('Can a company cut dividends?','تقدر الشركة تخفض التوزيعات؟',[('Never','أبدًا'),('Only after a split','بعد التجزئة فقط'),('Yes','نعم')],2,'Payments depend on company decisions and capacity.','الدفع يعتمد على قرار الشركة وقدرتها.')])

add('fees_drag',('Small Fees, Long-Term Impact','رسوم صغيرة وأثر طويل'),('Compare outcomes after recurring fees.','قارن النتائج بعد الرسوم المتكررة.'),'inflation',[
(('Know each cost','اعرف كل تكلفة'),('Separate trading commissions, fund expenses, custody fees and currency conversion charges. A zero-commission label covers only one part of the cost picture.','فرّق بين عمولة التداول ومصاريف الصندوق والحفظ وتحويل العملة. عبارة عمولة صفر تتكلم عن جزء واحد من التكلفة.'),('Read the fee schedule and fund documents.','اقرأ جدول الرسوم ومستندات الصندوق.')),
(('A simple annual example','مثال سنوي بسيط'),('Start with 1,000, earn a hypothetical 7%, then pay an annual fee of 1% of the ending balance. You keep 1,070 × 0.99 = 1,059.30. The net return is 5.93%, not exactly 6%. Real charging methods vary.','ابدأ بألف، اكسب 7% افتراضيًا، ثم ادفع رسم سنوي 1% من رصيد نهاية السنة. يبقى 1,070 × 0.99 = 1,059.30. العائد الصافي 5.93% مو 6% بالضبط. طرق احتساب الرسوم الفعلية تختلف.'),('Fee timing and calculation base matter.','توقيت الرسم والمبلغ المحسوب عليه يفرقون.')),
(('Long-term comparison','مقارنة طويلة'),('Repeat that annual process for ten years with no deposits: 1,000 × (1.07 × 0.99)^10. Compare it with 1,000 × 1.07^10. The difference includes fees and the returns those fees could have earned.','كرر العملية عشر سنوات بدون إضافات: ألف × (1.07 × 0.99) أس عشرة. قارنها بألف × 1.07 أس عشرة. الفرق يشمل الرسوم والعائد اللي كان ممكن تكسبه عليها.'),('Compare net outcomes using the same assumptions.','قارن النتائج الصافية بنفس الافتراضات.'))],[
q('Zero commission rules out all costs?','عمولة صفر تلغي كل التكاليف؟',[('No','لا'),('Yes','نعم'),('Only for funds','للصناديق فقط')],0,'Other expenses can still apply.','ممكن تبقى مصاريف ثانية.'),
q('1% of 1,070 is…','واحد بالمية من 1,070 يساوي…',[('10','10'),('10.70','10.70'),('107','107')],1,'1,070 × 0.01 = 10.70.','1,070 × 0.01 = 10.70.'),
q('Why can the long-term gap exceed fees paid?','ليش الفرق طويل المدى ممكن يتجاوز الرسوم المدفوعة؟',[('Fees create shares','الرسوم تنشئ أسهم'),('Returns are guaranteed','العوائد مضمونة'),('Lost compounding on the fees','فقدان العائد المركب على الرسوم')],2,'Money paid in fees cannot remain invested.','اللي دفعته رسوم ما يبقى مستثمر.')], 'micro_fees')

add('currency_return',('Your Return in Your Currency','عائدك بعملتك'),('Separate investment performance from exchange-rate changes.','افصل أداء الاستثمار عن تغير العملة.'),'macro',[
(('Two moving parts','عاملين يتحركون'),('A foreign investment can change in price and in exchange value. Define the quote clearly: units of your home currency per one unit of the foreign currency.','الاستثمار الأجنبي يتغير سعره وتتغير قيمته بالتحويل. عرّف سعر الصرف بوضوح: كم وحدة من عملتك مقابل وحدة من العملة الأجنبية.'),('Your spending currency is the reference.','عملة مصاريفك هي المرجع.')),
(('Combine the changes','اجمع الأثر صح'),('If the asset gains 10% in foreign currency and that currency loses 5% against yours, the home-currency return is 1.10 × 0.95 − 1 = 4.5%, before costs. Adding 10% and −5% is only an approximation.','لو الأصل ربح 10% بعملته والعمله ضعفت 5% مقابل عملتك، العائد عندك 1.10 × 0.95 ناقص واحد = 4.5% قبل التكاليف. جمع النسب يعطي تقريب فقط.'),('Multiply growth factors, then subtract one.','اضرب عوامل النمو ثم اطرح واحد.')),
(('Check your exposure','راجع تعرضك'),('Trading currency alone does not describe all currency risk: a fund may hold foreign assets and a company may earn abroad. Currency hedging also has costs and limitations.','عملة التداول لحالها ما توضح كل مخاطر العملة: الصندوق قد يمسك أصول أجنبية والشركة قد تربح من الخارج. التحوط للعملة له تكلفة وحدود بعد.'),('Look through to the underlying assets and revenues.','شف الأصول والإيرادات اللي وراء الاستثمار.'))],[
q('A foreign asset has which return drivers in your currency?','وش يحرك عائد الأصل الأجنبي بعملتك؟',[('Price only','السعر فقط'),('Exchange rate only','الصرف فقط'),('Both','الاثنين')],2,'Both changes affect converted value.','الاثنين يؤثرون على القيمة بعد التحويل.'),
q('Asset +10%, currency −5%: home return?','الأصل +10% والعملة −5%، عائدك؟',[('4.5%','4.5%'),('5% exactly','5% بالضبط'),('15%','15%')],0,'1.10 × 0.95 − 1 = 4.5%.','1.10 × 0.95 ناقص واحد = 4.5%.'),
q('Does listing currency reveal all exposure?','عملة الإدراج تكشف كل التعرض للعملات؟',[('Yes','نعم'),('No','لا'),('Only for big companies','للشركات الكبيرة فقط')],1,'Underlying assets and revenues also matter.','الأصول والإيرادات الأساسية تفرق بعد.')])

add('rebalance_basics',('Bring Your Portfolio Back to Plan','رجّع محفظتك للخطة'),('Understand portfolio drift and rebalancing.','افهم تغير الأوزان وإعادة التوازن.'),'allocation',[
(('Weights drift','الأوزان تتحرك'),('Start with 600 in stocks and 400 in bonds: 60% and 40%. If stocks rise to 800 and bonds stay 400, total value is 1,200 and stocks now represent 66.7%.','ابدأ بـ600 أسهم و400 سندات: 60% و40%. لو الأسهم صارت 800 والسندات بقيت 400، الإجمالي 1,200 ووزن الأسهم صار 66.7%.'),('Different returns change your portfolio mix.','اختلاف العوائد يغيّر توزيع المحفظة.')),
(('Restore a target','ارجع للوزن المستهدف'),('At a 1,200 total and a 60% stock target, the stock allocation would be 720. Moving 80 from stocks to bonds restores 720/480 before costs and taxes. This is an arithmetic example, not a recommended mix.','بإجمالي 1,200 وهدف أسهم 60%، مبلغ الأسهم يصير 720. نقل 80 من الأسهم للسندات يرجع التوزيع 720 و480 قبل الرسوم والضرائب. هذا مثال حسابي مو توزيع موصى به.'),('Target value = total value × target weight.','المبلغ المستهدف = الإجمالي × الوزن المستهدف.')),
(('Choose a review rule','حدد قاعدة مراجعة'),('Rebalancing can follow dates or drift thresholds. New contributions may reduce trading. Consider costs, taxes and whether your original target still matches your goals before acting.','تقدر تراجع بمواعيد أو إذا انحرف الوزن عن حد معين. الإضافات الجديدة قد تقلل البيع والشراء. راجع التكاليف والضرائب وهل الهدف ما زال مناسب قبل التنفيذ.'),('Rebalancing manages exposure; it does not guarantee returns.','إعادة التوازن تضبط التعرض وما تضمن العائد.'))],[
q('800 stocks out of 1,200 total is about…','800 أسهم من إجمالي 1,200، الوزن تقريبًا…',[('60%','60%'),('66.7%','66.7%'),('40%','40%')],1,'800 ÷ 1,200 = 66.7%.','800 ÷ 1,200 = 66.7%.'),
q('60% of 1,200 equals…','60% من 1,200 يساوي…',[('720','720'),('800','800'),('600','600')],0,'1,200 × 0.60 = 720.','1,200 × 0.60 = 720.'),
q('Rebalancing guarantees profit?','إعادة التوازن تضمن الربح؟',[('Always','دائمًا'),('After every rise','بعد كل ارتفاع'),('No','لا')],2,'It adjusts exposure, not future market outcomes.','تعدّل التعرض مو نتيجة السوق المستقبلية.')], 'allocation')

add('scam_signals',('Spot an Investment Scam','ميّز إشارات الاحتيال'),('Practise responding to pressure and guaranteed-return claims.','تدرّب على التعامل مع الضغط ووعود الربح المضمون.'),'mind',[
(('The tempting message','الرسالة المغرية'),('A stranger promises a fixed high monthly return with no risk and says the offer closes tonight. The combination of certainty, pressure and an unknown counterparty is a reason to stop and verify independently.','شخص ما تعرفه يوعدك بعائد شهري عالي ثابت بدون مخاطرة ويقول الفرصة تقفل الليلة. اجتماع الضمان والضغط والطرف المجهول سبب توقف وتتحقق بشكل مستقل.'),('Urgency is not evidence of a good opportunity.','الاستعجال مو دليل على جودة الفرصة.')),
(('Verify independently','تحقق بنفسك'),('Use the relevant regulator’s own register and contact details. Do not rely on a screenshot of a license or a link sent by the promoter. A copied real-company name can still hide an impersonator.','ارجع لسجل الجهة الرقابية نفسها وبيانات التواصل عندها. لا تعتمد على صورة ترخيص أو رابط من المسوّق. اسم شركة حقيقية ممكن يستخدمه منتحل.'),('Verify identity as well as the company name.','تحقق من هوية المتواصل مو اسم الشركة بس.')),
(('Protect access','احمِ الوصول'),('Never share passwords or one-time login codes with a promoter. If a suspicious party asks for another deposit to unlock withdrawals, stop and contact your financial institution through verified channels.','لا تعطي المسوّق كلمة المرور أو رمز الدخول المؤقت. لو طرف مشبوه طلب إيداع إضافي عشان يفك السحب، وقف وتواصل مع مؤسستك المالية عبر قنوات موثوقة.'),('A second payment can deepen the loss.','دفعة ثانية ممكن تزيد الخسارة.'))],[
q('High guaranteed return and pressure mean…','عائد عالي مضمون مع ضغط يعني…',[('A reason to pause and verify','سبب توقف وتتحقق'),('Proof of quality','دليل جودة'),('No risk','ما فيه مخاطرة')],0,'Pressure and certainty are warning signs.','الضغط والضمان علامات تحذير.'),
q('Where should you verify licensing?','وين تتحقق من الترخيص؟',[('Promoter screenshot','صورة المسوّق'),('Regulator’s own register','سجل الجهة الرقابية نفسها'),('Group chat','القروب')],1,'Use an independent official source.','استخدم مصدر رسمي مستقل.'),
q('Who should receive your login code?','مين تعطيه رمز دخولك؟',[('The promoter','المسوّق'),('Anyone with a logo','أي أحد معه شعار'),('Neither','ولا واحد')],2,'Do not disclose authentication codes.','لا تشارك رموز التحقق.')])

add('news_evidence',('Read News Before Reacting','اقرأ الخبر قبل تتفاعل'),('Separate a fact, an expectation and a trading conclusion.','فرّق بين الحقيقة والتوقع وقرار التداول.'),'research',[
(('Headline versus source','العنوان غير المصدر'),('A headline says profits surged. Open the company filing or official announcement, check the publication date, reporting period and units. Old news and quarterly numbers can be presented misleadingly.','العنوان يقول الأرباح قفزت. افتح إفصاح الشركة أو إعلانها الرسمي وراجع تاريخ النشر والفترة والوحدات. خبر قديم أو أرقام فصلية ممكن تنعرض بشكل مضلل.'),('Check source, date, period and units.','راجع المصدر والتاريخ والفترة والوحدات.')),
(('Growth versus expectations','النمو غير التوقعات'),('Profit rises from 100 to 120, a 20% increase. If the market expected 130, the result is still below that expectation. The share reaction also depends on guidance, valuation and other information.','الربح ارتفع من 100 إلى 120، نمو 20%. لو السوق كان يتوقع 130 فالنتيجة أقل من التوقع. حركة السهم تعتمد بعد على التوجيهات والتقييم ومعلومات ثانية.'),('Good growth does not guarantee a rising share price.','النمو الجيد ما يضمن ارتفاع السهم.')),
(('Write three lines','اكتب ثلاث جمل'),('Separate what happened, what you infer, and what remains unknown. For example: revenue grew; demand may be stronger; recurring cash generation is still unclear. Then check the missing evidence.','افصل وش صار، وش استنتجت، ووش ما تعرفه. مثلًا: الإيرادات نمت؛ يمكن الطلب أقوى؛ استمرار توليد الكاش مو واضح. بعدها دور الدليل الناقص.'),('Keep evidence separate from your interpretation.','خل الدليل منفصل عن تفسيرك.'))],[
q('What should you check first?','وش تراجع أول؟',[('Number of reposts','عدد إعادة النشر'),('Share price only','السعر فقط'),('Original source and date','المصدر الأصلي والتاريخ')],2,'Original dated evidence helps establish context.','الدليل الأصلي المؤرخ يوضح السياق.'),
q('120 profit versus 130 expected is…','ربح 120 مقابل توقع 130 يعتبر…',[('Below expectation','أقل من التوقع'),('Above expectation','أعلى من التوقع'),('Exactly in line','مطابق')],0,'120 is less than 130.','120 أقل من 130.'),
q('An inference is the same as a verified fact?','الاستنتاج نفسه الحقيقة المتحققة؟',[('Always','دائمًا'),('No','لا'),('When popular','إذا منتشر')],1,'Interpretations require additional evidence.','التفسيرات تحتاج أدلة إضافية.')])

LABS = {
 'micro_marketcap':('Price × shares','السعر × الأسهم'),
 'micro_return':('Total-return calculator','حاسبة العائد الكلي'),
 'micro_recovery':('Loss and recovery','الخسارة والتعويض'),
 'micro_spread':('Bid–ask experiment','تجربة فرق السعر'),
 'micro_fees':('Fee comparison','مقارنة الرسوم'),
}

def net_return(buy,sell,dividend,buy_fee,sell_fee,shares):
    initial=buy*shares+buy_fee
    proceeds=(sell+dividend)*shares-sell_fee
    return proceeds-initial,(proceeds/initial-1)*100

def recovery(loss):
    return loss/(100-loss)*100

def render(key,namespace='lesson'):
    import streamlit as st
    from i18n import L
    k=lambda suffix:f'acmicro_{namespace}_{key}_{suffix}'
    st.caption(L('Hypothetical exercise · change an input to explore the result.','تطبيق افتراضي · غيّر المدخلات وشوف النتيجة.'))
    a,b=st.columns(2)
    if key=='micro_marketcap':
        price=a.number_input(L('Price per share','سعر السهم'),min_value=0.01,value=50.0,key=k('price'))
        shares=b.number_input(L('Shares outstanding','الأسهم القائمة'),min_value=1,value=1000,key=k('shares'))
        st.metric(L('Equity market value','القيمة السوقية لحقوق المساهمين'),f'{price*shares:,.2f}')
        split=st.slider(L('Split factor','معامل التجزئة'),1,10,2,key=k('split'))
        st.info(L(f'After a {split}:1 split: {shares*split:,} shares × {price/split:,.2f}. Total remains {price*shares:,.2f}, before market movements.',f'بعد تجزئة {split} إلى 1: عدد الأسهم {shares*split:,} × سعر {price/split:,.2f}. الإجمالي يبقى {price*shares:,.2f} قبل حركة السوق.'))
    elif key=='micro_return':
        buy=a.number_input(L('Buy price','سعر الشراء'),min_value=0.01,value=100.0,key=k('buy'))
        sell=b.number_input(L('Sell price','سعر البيع'),min_value=0.0,value=110.0,key=k('sell'))
        dividend=a.number_input(L('Dividends per share','التوزيعات لكل سهم'),min_value=0.0,value=2.0,key=k('div'))
        shares=b.number_input(L('Shares','عدد الأسهم'),min_value=1,value=1,key=k('shares'))
        bf=a.number_input(L('Total purchase fee','إجمالي رسوم الشراء'),min_value=0.0,value=1.0,key=k('bf'))
        sf=b.number_input(L('Total sale fee','إجمالي رسوم البيع'),min_value=0.0,value=1.0,key=k('sf'))
        gain,ret=net_return(buy,sell,dividend,bf,sf,shares)
        a.metric(L('Net profit / loss','صافي الربح أو الخسارة'),f'{gain:+,.2f}')
        b.metric(L('Holding-period return','عائد فترة الاحتفاظ'),f'{ret:+.2f}%')
        st.caption(L('One purchase and sale; cash dividends not reinvested. Excludes taxes and currency changes.','شراء وبيع مرة واحدة، بدون إعادة استثمار التوزيعات. لا يشمل الضرائب وتغير العملة.'))
    elif key=='micro_recovery':
        loss=st.slider(L('Loss %','الخسارة %'),0,95,20,key=k('loss'))
        a.metric(L('Remaining from 1,000','المتبقي من ألف'),f'{1000*(1-loss/100):,.0f}')
        b.metric(L('Gain needed to recover','الارتفاع المطلوب للتعويض'),f'{recovery(loss):.2f}%')
        st.bar_chart({L('Loss %','الخسارة %'):[loss],L('Recovery %','التعويض %'):[recovery(loss)]})
    elif key=='micro_spread':
        bid=a.number_input(L('Bid','عرض المشترين'),min_value=0.01,value=99.0,key=k('bid'))
        ask=b.number_input(L('Ask','طلب البائعين'),min_value=0.01,value=101.0,key=k('ask'))
        if ask<bid:
            st.warning(L('Use ask ≥ bid for this simplified market.','في هالمثال المبسط خل الطلب يساوي العرض أو أعلى.'))
            return
        a.metric(L('Spread per share','الفرق لكل سهم'),f'{ask-bid:.2f}')
        b.metric(L('Immediate round-trip return','عائد الشراء والبيع مباشرة'),f'{(bid/ask-1)*100:.2f}%')
        st.caption(L('Assumes unchanged quotes and sufficient size; before commissions.','بافتراض ثبات الأسعار وتوفر الكمية، وقبل العمولات.'))
    elif key=='micro_fees':
        annual=a.slider(L('Hypothetical annual return %','العائد السنوي الافتراضي %'),-20,20,7,key=k('return'))
        fee=b.slider(L('Annual fee %','الرسم السنوي %'),0.0,5.0,1.0,step=.1,key=k('fee'))
        years=st.slider(L('Years','السنوات'),1,30,10,key=k('years'))
        no_fee=[1000*(1+annual/100)**y for y in range(years+1)]
        after=[1000*((1+annual/100)*(1-fee/100))**y for y in range(years+1)]
        a.metric(L('Without fee','بدون الرسم'),f'{no_fee[-1]:,.2f}')
        b.metric(L('After fee','بعد الرسم'),f'{after[-1]:,.2f}')
        st.line_chart({L('Without fee','بدون الرسم'):no_fee,L('After fee','بعد الرسم'):after})
        st.caption(L('Starts at 1,000; annual fee on year-end balance after return. No contributions, taxes or inflation.','البداية ألف؛ الرسم على رصيد نهاية السنة بعد العائد. بدون إضافات أو ضرائب أو تضخم.'))
