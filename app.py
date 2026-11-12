import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import BytesIO
import tempfile
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage
from reportlab.lib.units import mm

st.set_page_config(page_title="Saranya Transport Invoice", page_icon="🚚", layout="wide")
P = {
 "AK TEMPO SERVICE":{"address":"1/42, SENGATHURAI ROAD, SULUR, COIMBATORE, TAMIL NADU - 641402","mobile":"9443263166","alt":"9842263166","bank":"State Bank of India (SBI)","account":"AK TEMPO SERVICE","accent":"#1760F5"},
 "SARANYA TRANSPORTS":{"address":"4/29 B, MUTHUGOUNDANPUDHUR, KALIYAPURAM, SULUR, COIMBATORE - 641406","mobile":"9965508319","alt":"","bank":"Canara Bank / SBI","account":"SARANYA TRANSPORTS","accent":"#F07800"}
}
def rupee(x): return f"₹{float(x or 0):,.2f}"
def img_path(upload):
    if not upload: return None
    from PIL import Image
    im=Image.open(upload).convert("RGBA")
    f=tempfile.NamedTemporaryFile(delete=False,suffix=".png")
    im.save(f.name); return f.name

def pdf_invoice(d):
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=10*mm,rightMargin=10*mm,topMargin=9*mm,bottomMargin=9*mm)
    navy=colors.HexColor("#101B35"); accent=colors.HexColor(d["accent"]); pale=colors.HexColor("#F3F6FB"); line=colors.HexColor("#D6DFEC")
    sty=getSampleStyleSheet()
    sm=ParagraphStyle("sm",parent=sty["Normal"],fontName="Helvetica",fontSize=7.4,leading=9)
    tiny=ParagraphStyle("tiny",parent=sm,fontSize=6.5,leading=7.5)
    story=[]
    head=Table([[Paragraph(f"<font color='{d['accent']}'><b>{d['company']}</b></font><br/><font color='white' size='7'>{d['tagline']}</font><br/><font color='white' size='7'>{d['sender_address'].replace(chr(10),'<br/>')}<br/>Mobile: {d['sender_mobile']}</font>",sm),
                Paragraph(f"<font color='{d['accent']}'><b>{d['bill_title'].upper()}</b></font><br/><font color='white' size='7'>INVOICE NO.</font><br/><font color='{d['accent']}' size='15'><b>{d['invoice_no']}</b></font><br/><font color='white' size='7'>Month: {d['month']}<br/>Date: {d['inv_date'].strftime('%d/%m/%Y')}<br/>Due: {d['due'].strftime('%d/%m/%Y')}</font>",sm)]],colWidths=[118*mm,70*mm])
    head.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),navy),("BOX",(0,0),(-1,-1),1,accent),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9)]))
    story += [head,Spacer(1,6)]
    parties=Table([[Paragraph(f"<font color='{d['accent']}'><b>FROM / SENDER</b></font><br/><b>{d['sender_name']}</b><br/>{d['sender_address'].replace(chr(10),'<br/>')}<br/>Mobile: {d['sender_mobile']}",sm),
                    Paragraph(f"<font color='{d['accent']}'><b>BILL TO / CONSIGNEE</b></font><br/><b>{d['to_name']}</b><br/>{d['to_address'].replace(chr(10),'<br/>')}<br/>Mobile: {d['to_mobile']}",sm)]],colWidths=[94*mm,94*mm])
    parties.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),pale),("BOX",(0,0),(-1,-1),.5,line),("INNERGRID",(0,0),(-1,-1),.5,line),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),8)]))
    story += [parties,Spacer(1,6)]
    rows=[["S.NO","DATE","VEHICLE NO.","BILL NO.","DESCRIPTION","WEIGHT","TIMING","AMOUNT (₹)"]]
    for i,r in enumerate(d["trips"],1):
        timing=f"{r['From Time']} - {r['To Time']}<br/><font color='{d['accent']}'>({r['Duration']})</font>"
        rows.append([str(i),r["Date"],r["Vehicle No."],r["Bill No."],r["Description"],f"{r['Weight']} {r['Unit']}",Paragraph(timing,tiny),rupee(r["Amount"])])
    tb=Table(rows,colWidths=[10*mm,19*mm,27*mm,16*mm,39*mm,20*mm,30*mm,27*mm],repeatRows=1)
    tb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,line),("FONTSIZE",(0,0),(-1,-1),6.8),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(3,-1),"CENTER"),("ALIGN",(-1,1),(-1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),5)]))
    story += [tb,Spacer(1,5)]
    total=Table([[f"TRIPS: {len(d['trips'])}  •  TOTAL WEIGHT: {d['weight_total']}",f"GRAND TOTAL: {rupee(d['total'])}"]],colWidths=[95*mm,93*mm])
    total.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),navy),("TEXTCOLOR",(0,0),(-1,-1),colors.white),("TEXTCOLOR",(1,0),(1,0),accent),("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),("ALIGN",(1,0),(1,0),"RIGHT"),("PADDING",(0,0),(-1,-1),8)]))
    story += [total,Spacer(1,5),Paragraph(f"<b>PAYMENT DETAILS:</b> {d['bank']} &nbsp; | &nbsp; A/C: {d['account_no']} &nbsp; | &nbsp; IFSC: {d['ifsc']} &nbsp; | &nbsp; UPI/GPay: {d['upi']}",tiny),Spacer(1,8)]
    sig=PDFImage(d["sig"],width=30*mm,height=13*mm,kind="proportional") if d["sig"] else Paragraph("<br/><br/>",sm)
    stamp=PDFImage(d["stamp"],width=22*mm,height=22*mm,kind="proportional") if d["stamp"] else Paragraph("",sm)
    signs=Table([[Paragraph("Consignee Sign / Stamp",tiny),sig,stamp,Paragraph(f"<b>For {d['company']}</b><br/><br/>Authorised Signatory",sm)],
                 [Paragraph("Receiver's Signature<br/>Materials received in good condition",tiny),"","",""]],colWidths=[45*mm,45*mm,35*mm,63*mm],rowHeights=[25*mm,12*mm])
    signs.setStyle(TableStyle([("LINEABOVE",(0,1),(-1,1),.5,line),("LINEABOVE",(3,0),(3,0),.5,line),("VALIGN",(0,0),(-1,-1),"BOTTOM"),("ALIGN",(3,0),(3,-1),"RIGHT")]))
    story.append(signs)
    doc.build(story); out.seek(0); return out.getvalue()

st.markdown("""<style>
.stApp{background:#eef3f9;color:#14213d}.block-container{max-width:1500px;padding-top:1rem}
.top{background:#101b35;color:white;padding:15px 20px;border-radius:12px;margin-bottom:14px}
.top h2{color:white!important;margin:0}.top p{color:#c6d3e6;margin:2px 0 0}
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea,div[data-testid="stNumberInput"] input,div[data-testid="stDateInput"] input{background:white!important;color:#14213d!important;border:1px solid #c8d5e5!important;border-radius:7px!important}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:white!important;border-color:#c8d5e5!important}
div[data-testid="stMetric"]{background:white;border:1px solid #d7e0ee;border-radius:10px;padding:12px}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="top"><h2>🚚 TRANSPORT INVOICE GENERATOR</h2><p>Dual company billing • Editable trip details • E-signature • A4 PDF</p></div>',unsafe_allow_html=True)
company=st.radio("Select billing company",list(P),horizontal=True)
p=P[company]; accent=p["accent"]
if "trips_by_company" not in st.session_state: st.session_state.trips_by_company={}
if company not in st.session_state.trips_by_company:
    st.session_state.trips_by_company[company]=[{"Date":date.today(),"Vehicle No.":"","Bill No.":"","Description":"","Weight":0.0,"Unit":"KG","From Time":"10:00 AM","To Time":"03:00 PM","Duration":"2 DAYS","Amount":0.0}]
if "counter" not in st.session_state: st.session_state.counter={"AK TEMPO SERVICE":42,"SARANYA TRANSPORTS":463}
with st.sidebar:
    st.markdown("### E-sign & company stamp")
    sig_upload=st.file_uploader("Upload authorised signature",type=["png","jpg","jpeg"],key=f"sig{company}")
    stamp_upload=st.file_uploader("Upload company stamp (optional)",type=["png","jpg","jpeg"],key=f"stamp{company}")
    st.caption("PNG with transparent background is recommended.")
left,right=st.columns([.9,1.1],gap="medium")
with left:
    tabs=st.tabs(["Trips","Parties","Bank details"])
    with tabs[0]:
        prefix="AK-INV" if company=="AK TEMPO SERVICE" else "ST-INV"
        invoice_no=st.text_input("Invoice number",f"{prefix}-{date.today():%Y%m}-{st.session_state.counter[company]:03d}")
        c1,c2=st.columns(2)
        with c1: inv_date=st.date_input("Invoice date",date.today())
        with c2: due=st.date_input("Due date",date.today()+timedelta(days=15))
        month=st.text_input("Billing month",date.today().strftime("%B %Y"))
        bill_title=st.text_input("Bill title","MONTHLY TRANSPORT BILL")
        st.markdown("#### Consignment & trip rows")
        if st.button("＋ Add another trip row",use_container_width=True):
            st.session_state.trips_by_company[company].append({"Date":date.today(),"Vehicle No.":"","Bill No.":"","Description":"","Weight":0.0,"Unit":"KG","From Time":"10:00 AM","To Time":"03:00 PM","Duration":"1 DAY","Amount":0.0})
        trips=[]
        for i,r in enumerate(st.session_state.trips_by_company[company]):
            with st.expander(f"Trip #{i+1}",expanded=i==0):
                a,b=st.columns(2)
                with a:
                    dt=st.date_input("Trip date",r["Date"],key=f"{company}dt{i}")
                    vehicle=st.text_input("Vehicle number",r["Vehicle No."],key=f"{company}v{i}")
                    bill=st.text_input("Bill number",r["Bill No."],key=f"{company}b{i}")
                    desc=st.text_input("Description",r["Description"],key=f"{company}d{i}")
                    weight=st.number_input("Weight",min_value=0.0,value=float(r["Weight"]),step=.5,key=f"{company}w{i}")
                with b:
                    unit=st.selectbox("Weight unit",["KG","TON"],index=["KG","TON"].index(r["Unit"]),key=f"{company}u{i}")
                    from_time=st.selectbox("From time",["06:00 AM","07:00 AM","08:00 AM","09:00 AM","10:00 AM","11:00 AM","12:00 PM","01:00 PM","02:00 PM","03:00 PM"],index=4,key=f"{company}f{i}")
                    to_time=st.selectbox("To time",["09:00 AM","10:00 AM","11:00 AM","12:00 PM","01:00 PM","02:00 PM","03:00 PM","04:00 PM","05:00 PM","06:00 PM"],index=6,key=f"{company}t{i}")
                    duration=st.selectbox("Duration",["SAME DAY","1 DAY","2 DAYS","3 DAYS","4 DAYS","5 DAYS","6 DAYS"],index=2,key=f"{company}du{i}")
                    amount=st.number_input("Trip amount (₹)",min_value=0.0,value=float(r["Amount"]),step=100.0,key=f"{company}am{i}")
                trips.append({"Date":dt.strftime("%d/%m/%Y"),"Vehicle No.":vehicle,"Bill No.":bill,"Description":desc,"Weight":weight,"Unit":unit,"From Time":from_time,"To Time":to_time,"Duration":duration,"Amount":amount})
                if len(st.session_state.trips_by_company[company])>1 and st.button("Delete trip",key=f"{company}del{i}"):
                    st.session_state.trips_by_company[company].pop(i); st.rerun()
    with tabs[1]:
        st.markdown("#### Sender / From details")
        sender_name=st.text_input("Sender name",company)
        sender_address=st.text_area("From address",p["address"],height=90)
        sender_mobile=st.text_input("Sender mobile",p["mobile"])
        st.markdown("---")
        st.markdown("#### Consignee / To details")
        to_name=st.text_input("Consignee name","")
        to_address=st.text_area("To address","",height=90)
        to_mobile=st.text_input("Consignee mobile","")
    with tabs[2]:
        bank=st.text_input("Bank name",p["bank"])
        account_name=st.text_input("Account name",p["account"])
        account_no=st.text_input("Account number","")
        ifsc=st.text_input("IFSC code","")
        upi=st.text_input("UPI / GPay","")
        tagline=st.text_input("Company tagline","FAST • SAFE • RELIABLE TRANSPORT")

total=sum(t["Amount"] for t in trips)
weight_total=sum(t["Weight"] for t in trips)
units={t["Unit"] for t in trips}
weight_text=f"{weight_total:,.2f} {next(iter(units)) if len(units)==1 else 'MIXED UNITS'}"
sig=img_path(sig_upload); stamp=img_path(stamp_upload)
data={"company":company,"accent":accent,"tagline":tagline,"bill_title":bill_title,"invoice_no":invoice_no,"inv_date":inv_date,"due":due,"month":month,
"sender_name":sender_name,"sender_address":sender_address,"sender_mobile":sender_mobile,"to_name":to_name,"to_address":to_address,"to_mobile":to_mobile,
"bank":bank,"account_no":account_no,"ifsc":ifsc,"upi":upi,"trips":trips,"total":total,"weight_total":weight_text,"sig":sig,"stamp":stamp}
with right:
    st.markdown("### Live invoice preview")
    st.markdown(f"""<div style="background:#101b35;border:2px solid {accent};border-radius:11px;padding:16px;color:white">
    <div style="display:flex;justify-content:space-between;gap:10px"><div><b style="font-size:20px;color:{accent}">{company}</b><br><small>{sender_address.replace(chr(10),'<br>')}<br>Mobile: {sender_mobile}</small></div>
    <div style="text-align:right"><b style="color:{accent}">{bill_title}</b><br><b style="font-size:20px">{invoice_no}</b><br><small>{month} • {inv_date.strftime('%d/%m/%Y')}</small></div></div></div>""",unsafe_allow_html=True)
    x,y=st.columns(2)
    with x: st.markdown(f"**FROM / SENDER**  \n{sender_name}  \n{sender_address}  \nMobile: {sender_mobile}")
    with y: st.markdown(f"**BILL TO / CONSIGNEE**  \n{to_name or 'Consignee name'}  \n{to_address or 'Consignee address'}  \nMobile: {to_mobile}")
    view=pd.DataFrame([{"S.No":i+1,"Date":t["Date"],"Vehicle":t["Vehicle No."],"Bill":t["Bill No."],"Description":t["Description"],"Weight":f"{t['Weight']:g} {t['Unit']}","Timing":f"{t['From Time']} - {t['To Time']} ({t['Duration']})","Amount":rupee(t["Amount"])} for i,t in enumerate(trips)])
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.markdown(f"""<div style="background:#101b35;color:white;padding:13px;border-radius:9px;display:flex;justify-content:space-between">
    <b>TRIPS: {len(trips)} • TOTAL WEIGHT: {weight_text}</b><b style="font-size:19px;color:{accent}">GRAND TOTAL: {rupee(total)}</b></div>
    <div style="background:white;border:1px solid #d6dfec;padding:10px;border-radius:8px;margin-top:8px"><b>PAYMENT DETAILS:</b> {bank} | A/C: {account_no or 'Editable'} | IFSC: {ifsc or 'Editable'} | UPI: {upi or 'Editable'}</div>""",unsafe_allow_html=True)
    pdf=pdf_invoice(data)
    st.download_button("⬇ Save PDF / Print",pdf,file_name=f"{invoice_no}.pdf",mime="application/pdf",type="primary",use_container_width=True)
    if st.button("Generate next invoice number",use_container_width=True):
        st.session_state.counter[company]+=1
        st.rerun()
    st.caption("Invoice records are not yet stored in a permanent database. Save the PDF after generating each bill.")
