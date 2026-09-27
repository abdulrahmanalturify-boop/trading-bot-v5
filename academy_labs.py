"""Offline teaching labs with explicit assumptions and pure, testable calculations."""
import math
import pandas as pd
import streamlit as st
from i18n import L

LABS = {
 "compound": ("Compounding", "العائد المركب"), "inflation": ("Purchasing power", "القوة الشرائية"),
 "allocation": ("Portfolio mixer", "مختبر التنويع"), "expectancy": ("Trade expectancy", "التوقع الرياضي"),
 "duration": ("Bond sensitivity", "حساسية السند"), "valuation": ("Valuation sensitivity", "حساسية التقييم"),
 "journal": ("Decision journal", "سجل القرارات")}

def compound_path(initial, monthly, annual, years):
    rate=(1+annual/100)**(1/12)-1
    balance=float(initial); rows=[(0,balance,float(initial))]
    for month in range(1,int(years)*12+1):
        balance=balance*(1+rate)+monthly
        rows.append((month/12,balance,initial+monthly*month))
    return pd.DataFrame(rows,columns=["Year","Balance","Contributions"]).set_index("Year")

def real_return(nominal,inflation):
    return ((1+nominal/100)/(1+inflation/100)-1)*100

def portfolio(w,ra,rb,sa,sb,rho):
    variance=(w*sa)**2+((1-w)*sb)**2+2*w*(1-w)*sa*sb*rho
    return w*ra+(1-w)*rb, math.sqrt(max(variance,0))

def expectancy(p,win,loss,cost):
    return p*win-(1-p)*loss-cost

def perpetuity(cash,discount,growth):
    return cash/((discount-growth)/100) if discount>growth else None

def render(key, namespace="lesson"):
    k=lambda suffix:f"aclab_{namespace}_{key}_{suffix}"
    st.caption(L("Learning sandbox · hypothetical inputs, not a forecast or trade recommendation.","مختبر تعليمي · مدخلات افتراضية، مو توقع أو توصية تداول."))
    if key=="compound":
        a,b=st.columns(2)
        initial=a.number_input(L("Starting amount", "المبلغ الابتدائي"),0.0,10000000.0,10000.0,step=1000.0,key=k('initial'))
        monthly=b.number_input(L("Monthly deposit", "الإضافة الشهرية"),0.0,100000.0,500.0,step=100.0,key=k('monthly'))
        annual=a.slider(L("Assumed annual return %", "العائد السنوي المفترض %"),-20.0,25.0,7.0,step=.5,key=k('rate'))
        years=b.slider(L("Years", "السنوات"),1,40,10,key=k('years'))
        frame=compound_path(initial,monthly,annual,years)
        m=st.columns(3);end=frame.iloc[-1]
        m[0].metric(L("Ending balance", "الرصيد النهائي"),f"{end.Balance:,.0f}")
        m[1].metric(L("Your contributions", "إجمالي إضافاتك"),f"{end.Contributions:,.0f}")
        m[2].metric(L("Investment gain / loss", "ربح أو خسارة الاستثمار"),f"{end.Balance-end.Contributions:+,.0f}")
        st.line_chart(frame.rename(columns={"Balance":L("Balance","الرصيد"),"Contributions":L("Contributions","الإضافات")}),color=["#779EFF","#AE8DFA"])
        st.caption(L("Month-end deposits; annual effective rate converted monthly. Excludes fees, taxes and inflation.","إضافات نهاية الشهر؛ تحويل العائد السنوي الفعلي لشهري. بدون رسوم أو ضرائب أو تضخم."))
    elif key=="inflation":
        a,b=st.columns(2)
        nominal=a.slider(L("Nominal return %", "العائد الاسمي %"),-30.0,30.0,8.0,step=.5,key=k('nominal'))
        inf=b.slider(L("Inflation %", "التضخم %"),-5.0,20.0,3.0,step=.5,key=k('inflation'))
        real=real_return(nominal,inf)
        st.metric(L("Exact real return", "العائد الحقيقي الدقيق"),f"{real:+.2f}%")
        st.caption(L("(1 + nominal return) ÷ (1 + inflation) − 1. Both inputs cover the same period; before taxes and fees.","(1 + العائد الاسمي) ÷ (1 + التضخم) ناقص واحد. المدخلان لنفس الفترة، قبل الرسوم والضرائب."))
    elif key=="allocation":
        a,b=st.columns(2)
        w=a.slider(L("Asset A weight %", "وزن الأصل الأول %"),0,100,60,key=k('weight'))/100
        rho=b.slider(L("Correlation", "الارتباط"),-1.0,1.0,0.2,step=.1,key=k('rho'))
        ra=a.slider(L("A expected return %", "العائد المتوقع للأول %"),-10.0,30.0,8.0,key=k('ra'))
        rb=b.slider(L("B expected return %", "العائد المتوقع للثاني %"),-10.0,30.0,4.0,key=k('rb'))
        sa=a.slider(L("A annual volatility %", "التذبذب السنوي للأول %"),0.0,60.0,20.0,key=k('sa'))
        sb=b.slider(L("B annual volatility %", "التذبذب السنوي للثاني %"),0.0,60.0,10.0,key=k('sb'))
        ret,vol=portfolio(w,ra,rb,sa,sb,rho)
        a.metric(L("Expected portfolio return", "العائد المتوقع للمحفظة"),f"{ret:.2f}%")
        b.metric(L("Portfolio volatility", "تذبذب المحفظة"),f"{vol:.2f}%")
        frame=pd.DataFrame([(weight,*portfolio(weight/100,ra,rb,sa,sb,rho)) for weight in range(101)],columns=[L("A weight %","وزن الأول %"),L("Expected return %","العائد المتوقع %"),L("Volatility %","التذبذب %")]).set_index(L("A weight %","وزن الأول %"))
        st.line_chart(frame,color=["#779EFF","#AE8DFA"])
        st.caption(L("Two assets, no leverage; fixed annual estimates and correlation. Diversification does not eliminate losses.","أصلان بدون اقتراض؛ افتراضات سنوية وارتباط ثابت. التنويع ما يلغي الخسائر."))
    elif key=="expectancy":
        a,b=st.columns(2)
        p=a.slider(L("Win probability %", "احتمال النجاح %"),0,100,40,key=k('p'))/100
        win=b.number_input(L("Average win", "متوسط الربح"),0.0,100000.0,300.0,key=k('win'))
        loss=a.number_input(L("Average loss, positive amount", "متوسط الخسارة كمبلغ موجب"),0.0,100000.0,100.0,key=k('loss'))
        cost=b.number_input(L("Average round-trip cost", "متوسط تكلفة الدخول والخروج"),0.0,10000.0,10.0,key=k('cost'))
        st.metric(L("Expected result per trade", "التوقع لكل صفقة"),f"{expectancy(p,win,loss,cost):+,.2f}")
        breakeven=(loss+cost)/(win+loss) if win+loss else None
        st.caption(L(f"Breakeven win probability: {breakeven:.1%}",f"احتمال النجاح للتعادل: {breakeven:.1%}") if breakeven is not None and breakeven<=1 else L("No feasible breakeven win probability with these inputs.","ما فيه احتمال نجاح يحقق التعادل بهذه المدخلات."))
        st.caption(L("Assumes stable probabilities and average outcomes. Does not estimate drawdown or sequence risk.","يفترض ثبات الاحتمالات ومتوسط النتائج. ما يقدّر التراجع أو مخاطر تسلسل النتائج."))
    elif key=="duration":
        a,b=st.columns(2)
        duration=a.slider(L("Modified duration", "المدة المعدلة"),0.0,25.0,5.0,step=.5,key=k('d'))
        move=b.slider(L("Yield change (percentage points)", "تغير العائد بالنقاط المئوية"),-2.0,2.0,1.0,step=.1,key=k('move'))
        st.metric(L("Approximate price change", "تغير السعر التقريبي"),f"{-duration*move:+.2f}%")
        st.caption(L("First-order estimate for a small parallel yield shift. Excludes convexity, credit changes and coupon income.","تقريب من الدرجة الأولى لتحرك صغير ومتوازٍ بالعائد. يستبعد التحدب وتغير الائتمان ودخل الكوبون."))
    elif key=="valuation":
        a,b=st.columns(2)
        cash=a.number_input(L("Next-year cash flow", "تدفق السنة القادمة"),1.0,1000000.0,100.0,key=k('cash'))
        rate=b.slider(L("Discount rate %", "معدل الخصم %"),1.0,20.0,10.0,step=.5,key=k('discount'))
        growth=a.slider(L("Perpetual growth %", "النمو الدائم %"),-3.0,10.0,3.0,step=.5,key=k('growth'))
        value=perpetuity(cash,rate,growth)
        if value is None: st.warning(L("Discount rate must be greater than growth.","معدل الخصم لازم يكون أعلى من النمو."));return
        b.metric(L("Illustrative value", "القيمة التوضيحية"),f"{value:,.2f}")
        rates=[rate-1,rate,rate+1]; gs=[growth-1,growth,growth+1]
        frame=pd.DataFrame({f"{g:.1f}%":[perpetuity(cash,r,g) for r in rates] for g in gs},index=[f"{r:.1f}%" for r in rates])
        st.caption(L("Rows: discount rate · columns: perpetual growth. Invalid combinations are blank.","الصفوف: معدل الخصم · الأعمدة: النمو الدائم. التركيبات غير الصالحة فارغة."))
        frame.index.name=L("Discount rate", "معدل الخصم")
        import ui
        ui.table(frame, index=True, fmt={c:'{:,.2f}' for c in frame.columns})
        st.caption(L("Constant-growth perpetuity; no explicit forecast period, debt adjustment or share count. Not a full company valuation.","تدفق دائم بنمو ثابت؛ بدون فترة توقع صريحة أو تعديل ديون أو عدد أسهم. مو تقييم كامل لشركة."))
    elif key=="journal":
        thesis=st.text_area(L("My thesis", "فرضيتي"),key=k('thesis'))
        evidence=st.text_area(L("What would prove me wrong?", "وش الدليل اللي ينقض فكرتي؟"),key=k('evidence'))
        review=st.date_input(L("Review date", "موعد المراجعة"),key=k('date'))
        notes=f"Thesis / الفرضية\n{thesis}\n\nContrary evidence / الدليل المضاد\n{evidence}\n\nReview / المراجعة: {review}\n"
        st.download_button(L("Download my journal", "تحميل سجلي"),notes,file_name="investment-journal.txt",mime="text/plain",key=k('download'))
        st.caption(L("Download a copy before leaving this lab.","حمّل نسخة من ملاحظاتك قبل الخروج من هذا المختبر."))
