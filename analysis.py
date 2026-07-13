"""Reproducible growth analysis and slide-deck generator.

Run from this folder:
  /Users/malynka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis.py
"""
from pathlib import Path
import math
import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
NAVY, BLUE, TEAL, ORANGE, RED, GREY, LIGHT = (
    "132238", "3366CC", "00A6A6", "F59E0B", "DC4C64", "64748B", "F3F6FA"
)

def rgb(h): return RGBColor.from_string(h)
def money(x): return f"${x/1_000_000:.2f}m" if abs(x) >= 1_000_000 else f"${x/1_000:.0f}k"
def pct(x): return f"{x:.1%}"

def load_data():
    ads = pd.read_csv(ROOT / "paid_ads.csv", parse_dates=["date"])
    crm = pd.read_csv(ROOT / "crm_pipeline.csv", parse_dates=["created_at", "opportunity_created_at", "close_date", "trial_start_at", "trial_end_at"])
    usage = pd.read_csv(ROOT / "product_usage_events.csv", parse_dates=["event_time"])
    return ads, crm, usage

def build_metrics(ads, crm, usage):
    crm = crm.copy()
    crm["is_opportunity"] = crm.opportunity_id.notna()
    crm["is_won"] = crm.close_status.eq("Won")
    campaign = crm.dropna(subset=["campaign_id"]).groupby("campaign_id").agg(
        leads=("lead_id", "size"), opportunities=("is_opportunity", "sum"), won=("is_won", "sum"),
        pipeline=("amount", "sum"), won_arr=("amount", lambda s: s[crm.loc[s.index, "is_won"]].sum()),
    )
    paid = ads.groupby("campaign_id").agg(
        campaign_name=("campaign_name", "first"), channel=("channel", "first"), impressions=("impressions", "sum"),
        clicks=("clicks", "sum"), spend=("cost", "sum")
    ).join(campaign).fillna({"leads":0, "opportunities":0, "won":0, "pipeline":0, "won_arr":0})
    paid["ctr"] = paid.clicks / paid.impressions
    paid["cpl"] = paid.spend / paid.leads.replace(0, pd.NA)
    paid["cac"] = paid.spend / paid.won.replace(0, pd.NA)
    paid["roas"] = paid.won_arr / paid.spend
    channel = paid.groupby("channel").agg(spend=("spend","sum"), leads=("leads","sum"), opportunities=("opportunities","sum"), won=("won","sum"), won_arr=("won_arr","sum"))
    channel["roas"] = channel.won_arr / channel.spend
    channel["cpl"] = channel.spend / channel.leads
    channel["cac"] = channel.spend / channel.won

    account_usage = usage.groupby("company_id").agg(
        events=("event_type", "size"), active_days=("event_time", lambda x: x.dt.date.nunique()),
        users=("user_id", "nunique"), logins=("event_type", lambda x: (x == "login").sum()),
        feature_x=("event_type", lambda x: (x == "feature_x_used").sum()),
        feature_y=("event_type", lambda x: (x == "feature_y_used").sum()),
        plan_tiers=("plan_tier", "nunique")
    )
    accounts = crm.set_index("company_id").join(account_usage)
    accounts["activated_30d"] = accounts.active_days.ge(30).fillna(False)
    return paid.reset_index(), channel.reset_index(), accounts.reset_index()

def add_text(slide, text, x, y, w, h, size=16, color=NAVY, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text
    p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = rgb(color); p.font.name = "Aptos"
    return box

def rect(slide, x, y, w, h, fill=LIGHT, line=None, radius=False):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    s.line.color.rgb = rgb(line or fill)
    return s

def title(slide, heading, subtitle=None):
    add_text(slide, heading, .6, .35, 12.0, .45, 25, NAVY, True)
    if subtitle: add_text(slide, subtitle, .62, .84, 12, .28, 10, GREY)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.6), Inches(1.15), Inches(1.0), Inches(.04))
    line.fill.solid(); line.fill.fore_color.rgb = rgb(TEAL); line.line.color.rgb = rgb(TEAL)

def bullets(slide, items, x, y, w, size=15):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(5.2)); tf=box.text_frame; tf.clear(); tf.word_wrap=True
    for i, item in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=item; p.level=0; p.font.size=Pt(size); p.font.color.rgb=rgb(NAVY); p.space_after=Pt(14); p.font.name="Aptos"
    return box

def add_bar(slide, df, category, series, x, y, w, h, title_text, percent=False):
    cd=CategoryChartData(); cd.categories=df[category].astype(str).tolist(); cd.add_series(title_text, df[series].tolist())
    chart=slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    chart.has_legend=False; chart.value_axis.has_major_gridlines=False; chart.category_axis.tick_labels.font.size=Pt(9); chart.value_axis.tick_labels.font.size=Pt(8)
    chart.series[0].format.fill.solid(); chart.series[0].format.fill.fore_color.rgb=rgb(TEAL)
    chart.has_title=True; chart.chart_title.text_frame.paragraphs[0].text=title_text; chart.chart_title.text_frame.paragraphs[0].font.size=Pt(11)
    return chart

def deck(ads, crm, usage, paid, channel, accounts):
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    blank=prs.slide_layouts[6]
    # 1
    s=prs.slides.add_slide(blank); rect(s,0,0,13.333,7.5,NAVY); add_text(s,"Growth analytics: from spend to durable adoption",.75,1.35,11.8,.8,31,"FFFFFF",True); add_text(s,"Sr. Growth Analyst take-home | Fictional deskbird datasets | Jan–Sep 2025 acquisition; product events through Jan 2026",.78,2.3,11.6,.5,15,"C9D7E5"); rect(s,.78,3.25,1.4,.08,TEAL); add_text(s,"A scalable model, five decision metrics, and actions to improve efficient growth.",.78,3.6,10.8,.55,20,"FFFFFF")
    # 2
    s=prs.slides.add_slide(blank); title(s,"Executive takeaways","Attribution connects $1.56m in paid spend to 467 attributed leads, 68 matched-campaign wins and $1.39m in won ARR.")
    top=channel.sort_values("roas",ascending=False).iloc[0]; search=channel[channel.channel.eq("Paid Search")].iloc[0]
    cards=[("6.6x", "Display ROAS", "Highest channel efficiency"),(f"{search.roas:.1f}x", "Paid Search ROAS", "29% return on $451k spend"),("84.5%", "30-day activation", "Among closed-won accounts")]
    for i,(a,b,c) in enumerate(cards):
        x=.7+i*4.15; rect(s,x,1.65,3.7,1.55,"EAF7F7",radius=True); add_text(s,a,x+.25,1.88,3.2,.4,25,TEAL,True); add_text(s,b,x+.25,2.35,3.2,.25,13,NAVY,True); add_text(s,c,x+.25,2.66,3.2,.3,11,GREY)
    bullets(s,["Reallocate experimental budget away from the two Paid Search campaigns until conversion quality is fixed.","Make 30-day product activation an early leading indicator for trial conversion and sales prioritisation.","Repair channel taxonomy and plan-tier history before using channel or retention cuts for executive reporting."],.85,3.65,11.7,17)
    #3 model
    s=prs.slides.add_slide(blank); title(s,"Scalable customer-journey data model","Conformed campaign and account keys enable spend → lead → revenue → adoption analysis.")
    nodes=[("stg_paid_ads","Daily campaign performance\nPK: date + campaign_id",.7,1.7,2.55,1.0,BLUE),("stg_crm_leads","Lead & opportunity lifecycle\nPK: lead_id | account key",.7,4.4,2.55,1.0,ORANGE),("dim_campaign","Campaign / UTM\nSCD attributes & taxonomy",4.1,1.8,2.35,1.0,TEAL),("dim_account","Account identity\ncompany_id + domain",4.1,4.3,2.35,1.0,TEAL),("fct_growth_funnel","Campaign-day funnel\nspend, leads, pipeline, ARR",7.4,1.8,2.6,1.0,NAVY),("fct_account_adoption","Account-day adoption\nactive users, features, seats",7.4,4.3,2.6,1.0,NAVY),("mart_growth_scorecard","Growth scorecard\nCAC, win, activation, ROAS",10.55,3.05,2.15,1.1,RED)]
    for name,desc,x,y,w,h,c in nodes:
        rect(s,x,y,w,h,c,radius=True); add_text(s,name,x+.14,y+.14,w-.25,.22,12,"FFFFFF",True); add_text(s,desc,x+.14,y+.43,w-.25,.4,10,"FFFFFF")
    for x1,y1,x2,y2 in [(3.25,2.2,4.1,2.2),(3.25,4.9,4.1,4.8),(6.45,2.3,7.4,2.3),(6.45,4.8,7.4,4.8),(10,2.3,10.55,3.35),(10,4.8,10.55,3.8)]:
        line=s.shapes.add_connector(1,Inches(x1),Inches(y1),Inches(x2),Inches(y2)); line.line.color.rgb=rgb(GREY)
    add_text(s,"Grain discipline: preserve daily campaign rows and event-level usage; aggregate only in marts. dbt tests: key uniqueness, referential integrity, accepted taxonomy values, and event-time validity.",.75,6.15,11.9,.55,12,GREY)
    #4 metrics
    s=prs.slides.add_slide(blank); title(s,"Five decision metrics across the funnel","Each metric has a denominator, owner, and action—not just a dashboard tile.")
    metrics=[("1  Marketing-sourced leads","Attributed leads / period","Acquisition volume; Growth"),("2  Cost per lead (CPL)","Paid spend ÷ attributed leads","Media efficiency; Growth"),("3  Lead → opportunity rate","Opportunities ÷ leads","Lead quality; Marketing + Sales"),("4  CAC / won ARR ROAS","Spend ÷ wins; won ARR ÷ spend","Economic efficiency; Finance"),("5  30-day activation rate","Accounts with ≥30 active days ÷ eligible accounts","Retention signal; Product + CS")]
    for i,(a,b,c) in enumerate(metrics):
        y=1.45+i*1.02; rect(s,.75,y,11.85,.78,"F3F6FA",radius=True); add_text(s,a,1.0,y+.13,3.7,.25,14,NAVY,True); add_text(s,b,4.75,y+.13,3.5,.25,13,BLUE); add_text(s,c,8.45,y+.13,3.8,.25,12,GREY)
    #5 funnel
    s=prs.slides.add_slide(blank); title(s,"The conversion funnel has a sharp post-opportunity drop","14.2% of all leads close won; opportunity-to-win is 43.8%.")
    total=len(crm); opp=int(crm.opportunity_id.notna().sum()); won=int(crm.close_status.eq("Won").sum()); trial=int(crm.trial_start_at.notna().sum())
    vals=[("Leads",total), ("Trials",trial), ("Opportunities",opp), ("Won",won)]
    maxv=max(v for _,v in vals)
    for i,(lab,val) in enumerate(vals):
        y=1.65+i*1.05; width=6.1*val/maxv; rect(s,.85,y,width,.65,[BLUE,TEAL,ORANGE,RED][i],radius=True); add_text(s,f"{lab}: {val} ({val/total:.1%})",1.0,y+.16,4.5,.25,14,"FFFFFF",True)
    add_text(s,"Interpretation",8.15,1.55,3,.3,17,NAVY,True); bullets(s,["62% of leads start a trial (311 / 500).","32% become opportunities (162 / 500).","Prioritise trial activation and opportunity progression; these are the levers closest to revenue."],8.15,2.05,4.35,14)
    #6 economics
    s=prs.slides.add_slide(blank); title(s,"Display produces the strongest observed return, while Paid Search is inefficient","Channel names are raw fields; taxonomy issues on slide 8 mean this is directional pending cleanup.")
    chart_df=channel.sort_values("roas",ascending=True); add_bar(s,chart_df,"channel","roas",.7,1.55,6.35,4.6,"Won ARR / spend (ROAS)")
    tab=channel.set_index("channel").loc[["Display","Paid Social","Paid Search"]]
    for i,(ch,row) in enumerate(tab.iterrows()):
        y=1.65+i*1.32; rect(s,7.55,y,5.0,1.05,"F3F6FA",radius=True); add_text(s,ch,7.8,y+.16,1.8,.24,14,NAVY,True); add_text(s,f"{money(row.spend)} spend | {int(row.won)} wins | {money(row.cac)} CAC",7.8,y+.48,4.35,.22,11,GREY); add_text(s,f"{row.roas:.1f}x",11.35,y+.25,1.0,.28,20,TEAL,True)
    add_text(s,"Action: protect Display volume while running incrementality/quality validation; cap Paid Search and audit intent, landing page, and lead routing.",.8,6.55,11.8,.35,13,NAVY,True)
    #7 adoption
    s=prs.slides.add_slide(blank); title(s,"30-day activity is a high-signal conversion indicator","Account activity strongly separates closed-won from closed-lost outcomes in this sample.")
    grp=accounts[accounts.close_status.isin(["Won","Lost"])].groupby("close_status").agg(median_events=("events","median"), median_active_days=("active_days","median"), activated_30d=("activated_30d","mean")).reindex(["Won","Lost"]).reset_index()
    add_bar(s,grp,"close_status","median_active_days",.7,1.55,5.9,4.5,"Median active days per account")
    for i,row in grp.iterrows():
        x=7.25+i*2.65; rect(s,x,1.85,2.25,2.2,"EAF7F7" if row.close_status=="Won" else "FFF3E0",radius=True); add_text(s,row.close_status,x+.2,2.1,1.8,.3,16,NAVY,True); add_text(s,pct(row.activated_30d),x+.2,2.6,1.8,.35,24,TEAL if row.close_status=="Won" else ORANGE,True); add_text(s,"activated ≥30d",x+.2,3.03,1.8,.24,11,GREY)
    bullets(s,["Closed-won median: 80.5 active days and 323.5 events.","Closed-lost median: 15 active days and 52.5 events; none reach 30 active days.","Operationalise: trigger onboarding intervention at day 7; route activated trials to Sales at day 14."],7.25,4.4,5.0,14)
    #8 quality
    s=prs.slides.add_slide(blank); title(s,"Data anomalies that would mislead a production scorecard","These are solvable modeling and instrumentation gaps, not reasons to defer decisions.")
    anomalies=[("Channel taxonomy conflict","Campaign name suffix conflicts with channel label across 3,003 / 5,187 ad rows (e.g., *_Search marked Paid Social).","Derive a governed channel from source/medium; retain raw fields and test accepted values."),("Plan-tier history is unstable","Every observed account has 3–4 plan tiers across its usage events; 60 of 71 wins have 3 tiers, while 75 of 91 losses have 4.","Use a subscription SCD / effective-dated plan table—do not infer current plan from events."),("Coverage and time-window gap","33 of 500 CRM leads (6.6%) are unattributed; usage runs to Jan 2026, while acquisition data ends Sep 2025.","Create an Organic/Unknown channel and set an as-of date / cohort maturity rule.")]
    for i,(a,b,c) in enumerate(anomalies):
        y=1.45+i*1.65; rect(s,.75,y,12.0,1.38,"FDF2F3" if i==0 else "F3F6FA",radius=True); add_text(s,a,1.0,y+.14,3.2,.26,14,RED if i==0 else NAVY,True); add_text(s,b,4.15,y+.13,4.0,.56,11,NAVY); add_text(s,c,8.4,y+.13,3.95,.58,11,TEAL)
    #9 recommendations
    s=prs.slides.add_slide(blank); title(s,"90-day action plan","Turn the analysis into an operating cadence with controlled measurement.")
    actions=[("0–30 days | Fix measurement","Govern campaign taxonomy and Organic/Unknown; build dim_campaign, dim_account, funnel and adoption marts; reconcile spend and CRM IDs."),("31–60 days | Improve conversion","Implement trial health score (login, active days, feature use); day-7 onboarding triggers and day-14 sales routing; diagnose Paid Search query/landing-page flow."),("61–90 days | Scale proven demand","Run a geo/audience holdout for Display; reallocate budget only after incremental CAC validation; review weekly by cohort maturity and 30-day activation.")]
    for i,(a,b) in enumerate(actions):
        y=1.5+i*1.55; rect(s,.85,y,11.65,1.12,"EAF7F7" if i==0 else "F3F6FA",radius=True); add_text(s,a,1.15,y+.18,3.7,.3,15,NAVY,True); add_text(s,b,4.7,y+.18,7.3,.5,13,NAVY)
    add_text(s,"Success criterion: decision-ready reporting where every metric has a grain, owner, lineage, quality test, and action threshold.",.9,6.35,11.5,.35,14,TEAL,True)
    prs.save(OUT / "growth_analytics_take_home.pptx")

def main():
    ads, crm, usage = load_data()
    paid, channel, accounts = build_metrics(ads, crm, usage)
    paid.sort_values("roas", ascending=False).to_csv(OUT / "campaign_economics.csv", index=False)
    channel.sort_values("roas", ascending=False).to_csv(OUT / "channel_economics.csv", index=False)
    accounts.to_csv(OUT / "account_adoption.csv", index=False)
    deck(ads, crm, usage, paid, channel, accounts)
    print(f"Created {OUT / 'growth_analytics_take_home.pptx'}")

if __name__ == "__main__": main()
