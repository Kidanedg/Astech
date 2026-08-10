import streamlit as st
import sqlite3, hashlib, secrets, hmac, random
from datetime import datetime, date
from pathlib import Path
import pandas as pd

# ============================================================
# IDFS WEB PLATFORM
# Single-file Streamlit prototype
# MODULE 1: Configuration and database
# MODULE 2: Authentication and access control
# MODULE 3: Branch management
# MODULE 4: Member management
# MODULE 5: IDFS Equb savings and rounds
# MODULE 6: Equb contribution-weighted probability engine
# MODULE 7: IDFS Iddir community risk sharing
# MODULE 8: Iddir property management
# MODULE 9: Transactions
# MODULE 10: Reports and analytics
# MODULE 11: Audit trail
# MODULE 12: User administration
# ============================================================

st.set_page_config(page_title="IDFS Web Platform", layout="wide")
DB = Path("idfs_demo.db")
MODULES = ["Equb", "Iddir"]
ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]
EVENT_TYPES = ["Funeral", "Wedding", "Holiday", "Emergency", "Medical Support", "Family Support", "Other"]
PROPERTY_TYPES = ["Land", "Building", "Vehicle", "Equipment", "Furniture", "Office Asset", "Other"]

st.markdown("""
<style>
.main{background:#f7f9fc}.block-container{padding-top:1rem}
.idfs-header{padding:18px 22px;border-radius:9px;background:#0B5CAD;color:white;margin-bottom:18px}
.idfs-header h1{margin:0;font-size:2rem}.idfs-header p{margin:4px 0 0}
.box{padding:16px;border:1px solid #d9e0e8;border-radius:8px;background:white;margin-bottom:12px}
.title{color:#0B5CAD;font-size:1.3rem;font-weight:700}
</style>
""", unsafe_allow_html=True)


def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def money(x): return f"ETB {float(x or 0):,.2f}"

def conn():
    c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

def sql(q,p=(),fetch=False,many=False):
    c=conn(); cur=c.cursor()
    try:
        cur.executemany(q,p) if many else cur.execute(q,p)
        r=cur.fetchall() if fetch else None; c.commit(); return r
    finally: c.close()

def df(q,p=()): return pd.DataFrame([dict(x) for x in sql(q,p,fetch=True)])

# ============================================================
# MODULE 1: DATABASE
# ============================================================

def pwd_hash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    h=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()
    return salt+"$"+h

def check_pwd(password,stored):
    try:
        salt,h=stored.split("$",1)
        x=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()
        return hmac.compare_digest(x,h)
    except Exception: return False

def audit(action,module="Portal",details=""):
    sql("INSERT INTO audit_log(username,module,action,details,timestamp) VALUES(?,?,?,?,?)",
        (st.session_state.get("username","anonymous"),module,action,details,now()))

def init_db():
    c=conn(); c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,password_hash TEXT,full_name TEXT,role TEXT,module TEXT,branch_id INTEGER,active INTEGER DEFAULT 1,created_at TEXT);
    CREATE TABLE IF NOT EXISTS branches(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE,name TEXT,module TEXT,location TEXT,manager TEXT,phone TEXT,status TEXT DEFAULT 'Active',created_at TEXT);
    CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY AUTOINCREMENT,member_no TEXT UNIQUE,full_name TEXT,phone TEXT,sex TEXT,join_date TEXT,module TEXT,branch_id INTEGER,regular_contribution REAL DEFAULT 0,trust_score REAL DEFAULT .5,status TEXT DEFAULT 'Active',address TEXT,notes TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS equb_rounds(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER,round_no INTEGER,contribution_amount REAL,start_date TEXT,draw_date TEXT,expected_members INTEGER,total_pool REAL DEFAULT 0,winner_member_id INTEGER,status TEXT DEFAULT 'Open',created_at TEXT);
    CREATE TABLE IF NOT EXISTS contributions(id INTEGER PRIMARY KEY AUTOINCREMENT,member_id INTEGER,module TEXT,round_id INTEGER,amount REAL,contribution_date TEXT,status TEXT DEFAULT 'Paid',reference TEXT,payment_method TEXT,notes TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS iddir_events(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER,event_type TEXT,member_id INTEGER,event_date TEXT,description TEXT,requested_amount REAL DEFAULT 0,approved_amount REAL DEFAULT 0,status TEXT DEFAULT 'Pending',payment_date TEXT,reference TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS properties(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER,property_code TEXT UNIQUE,property_type TEXT,description TEXT,location TEXT,acquisition_date TEXT,acquisition_cost REAL DEFAULT 0,current_value REAL DEFAULT 0,status TEXT DEFAULT 'Active',custodian TEXT,notes TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,module TEXT,branch_id INTEGER,member_id INTEGER,transaction_type TEXT,amount REAL,reference TEXT,transaction_date TEXT,description TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,module TEXT,action TEXT,details TEXT,timestamp TEXT);
    """); c.commit(); c.close()
    if not sql("SELECT id FROM users WHERE username='admin'",fetch=True):
        sql("INSERT INTO users(username,password_hash,full_name,role,module,created_at) VALUES(?,?,?,?,?,?)",
            ("admin",pwd_hash("admin123"),"IDFS Administrator","Administrator","Portal",now()))
    if not sql("SELECT id FROM branches LIMIT 1",fetch=True):
        rows=[("EQB-001","IDFS Equb Central Branch","Equb","Aksum","Branch Manager"),("EQB-002","IDFS Equb North Branch","Equb","Shire","Branch Manager"),("IDR-001","IDFS Iddir Central Branch","Iddir","Aksum","Branch Manager"),("IDR-002","IDFS Iddir Community Branch","Iddir","Shire","Branch Manager")]
        sql("INSERT INTO branches(code,name,module,location,manager,created_at) VALUES(?,?,?,?,?,?)",[(a,b,c,d,e,now()) for a,b,c,d,e in rows],many=True)

def header(title,sub=""):
    st.markdown(f'<div class="idfs-header"><h1>{title}</h1><p>{sub}</p></div>',unsafe_allow_html=True)

def branches(module=None):
    return sql("SELECT * FROM branches "+("WHERE module=? " if module else "")+"ORDER BY name",(module,) if module else (),True)

def members(module=None,branch=None):
    w=[]; p=[]
    if module:w.append("m.module=?");p.append(module)
    if branch:w.append("m.branch_id=?");p.append(branch)
    where=(" WHERE "+" AND ".join(w)) if w else ""
    return sql("SELECT m.*,b.code branch_code,b.name branch_name FROM members m LEFT JOIN branches b ON m.branch_id=b.id"+where+" ORDER BY m.full_name",tuple(p),True)

# ============================================================
# MODULE 2: AUTHENTICATION
# ============================================================

def login():
    header("Indigenous Digital Financial System","IDFS Web Platform: Equb savings and Iddir community risk sharing")
    _,c,_=st.columns([1,1.2,1])
    with c:
        st.subheader("System Login")
        with st.form("login"):
            u=st.text_input("Username"); p=st.text_input("Password",type="password")
            ok=st.form_submit_button("Sign in",type="primary",use_container_width=True)
        if ok:
            r=sql("SELECT * FROM users WHERE username=? AND active=1",(u.strip(),),True)
            if r and check_pwd(p,r[0]["password_hash"]):
                x=r[0]
                for k in ["authenticated","user_id","username","full_name","role","module","branch_id"]:
                    st.session_state[k]=x["id"] if k=="user_id" else (True if k=="authenticated" else x[k])
                audit("Successful login"); st.rerun()
            else: st.error("Invalid username or password.")
        st.info("Demonstration account: admin / admin123")

# ============================================================
# MODULE 3: BRANCH MANAGEMENT
# ============================================================

def branch_page():
    header("Module 3: Branch Management","Bank-style branch structure for Equb and Iddir")
    t1,t2=st.tabs(["Branch Directory","Register Branch"])
    with t1:
        st.dataframe(df("SELECT code Branch_Code,name Branch_Name,module Module,location Location,manager Manager,phone Phone,status Status FROM branches ORDER BY module,name"),use_container_width=True,hide_index=True)
    with t2:
        with st.form("branch"):
            a,b=st.columns(2); code=a.text_input("Branch Code"); name=b.text_input("Branch Name")
            mod=a.selectbox("Module",MODULES); loc=b.text_input("Location"); mgr=a.text_input("Manager"); phone=b.text_input("Phone")
            status=a.selectbox("Status",["Active","Inactive"]); ok=st.form_submit_button("Register Branch",type="primary")
        if ok:
            try:
                sql("INSERT INTO branches(code,name,module,location,manager,phone,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(code.strip(),name.strip(),mod,loc.strip(),mgr.strip(),phone.strip(),status,now()))
                audit("Created branch",mod,code); st.success("Branch registered."); st.rerun()
            except sqlite3.IntegrityError: st.error("Branch code already exists.")

# ============================================================
# MODULE 4: MEMBER MANAGEMENT
# ============================================================

def member_page():
    header("Module 4: Member Management","Registration, regular contribution and membership monitoring")
    t1,t2,t3=st.tabs(["Directory","Register Member","Member Profile"])
    with t1:
        f=st.selectbox("Module Filter",["All"]+MODULES)
        if f=="All": q="SELECT m.member_no Member_No,m.full_name Full_Name,m.module Module,b.name Branch,m.phone Phone,m.join_date Join_Date,m.regular_contribution Regular_Contribution,m.trust_score Trust_Score,m.status Status FROM members m LEFT JOIN branches b ON m.branch_id=b.id ORDER BY m.module,m.full_name"; x=df(q)
        else: x=df("SELECT m.member_no Member_No,m.full_name Full_Name,m.module Module,b.name Branch,m.phone Phone,m.join_date Join_Date,m.regular_contribution Regular_Contribution,m.trust_score Trust_Score,m.status Status FROM members m LEFT JOIN branches b ON m.branch_id=b.id WHERE m.module=? ORDER BY m.full_name",(f,))
        st.dataframe(x,use_container_width=True,hide_index=True)
    with t2:
        with st.form("member"):
            a,b=st.columns(2); no=a.text_input("Member Number"); name=b.text_input("Full Name"); phone=a.text_input("Phone"); sex=b.selectbox("Sex",["Not specified","Female","Male"])
            mod=a.selectbox("Module",MODULES); bs=branches(mod); bn=[f"{x['code']} | {x['name']}" for x in bs]; bc=b.selectbox("Branch",bn or ["No branch"])
            contrib=a.number_input("Regular Contribution per Round or Period (ETB)",0.,step=100.,value=0.); jd=b.date_input("Join Date",date.today()); trust=a.number_input("Initial Trust Score",0.,1.,.5,.05); address=b.text_input("Address"); notes=st.text_area("Notes")
            ok=st.form_submit_button("Register Member",type="primary")
        if ok:
            if not no.strip() or not name.strip(): st.error("Member number and full name are required.")
            elif not bs: st.error("Create a branch for this module first.")
            else:
                bid=bs[bn.index(bc)]["id"]
                try:
                    sql("INSERT INTO members(member_no,full_name,phone,sex,join_date,module,branch_id,regular_contribution,trust_score,address,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(no.strip(),name.strip(),phone,sex,str(jd),mod,bid,contrib,trust,address,notes,now()))
                    audit("Registered member",mod,no); st.success("Member registered."); st.rerun()
                except sqlite3.IntegrityError: st.error("Member number already exists.")
    with t3:
        ms=members()
        if not ms: st.info("No members registered."); return
        opts=[f"{m['member_no']} | {m['full_name']} | {m['module']}" for m in ms]; pick=st.selectbox("Select Member",opts); m=ms[opts.index(pick)]
        a,b,c,d=st.columns(4); a.metric("Member",m["member_no"]); b.metric("Module",m["module"]); c.metric("Regular Contribution",money(m["regular_contribution"])); d.metric("Trust Score",f"{float(m['trust_score']):.2f}")
        st.write({"Full Name":m["full_name"],"Phone":m["phone"],"Branch":m["branch_name"],"Join Date":m["join_date"],"Status":m["status"],"Address":m["address"],"Notes":m["notes"]})

# ============================================================
# MODULE 5: EQUB SAVINGS AND ROUNDS
# ============================================================

def equb():
    header("Module 5: IDFS Equb","Community savings, fixed contributions, rounds and rotating payout")
    t=st.tabs(["Overview","Round Management","Contribution Management","Probability Engine"])
    with t[0]:
        n=sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND status='Active'",fetch=True)[0]["n"]
        pool=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"]
        r=sql("SELECT COUNT(*) n FROM equb_rounds",fetch=True)[0]["n"]
        a,b,c=st.columns(3); a.metric("Active Members",n); b.metric("Savings Recorded",money(pool)); c.metric("Rounds",r)
        st.markdown('<div class="box"><div class="title">Equb savings model</div><p>Each member has a regular contribution amount. Contributions are recorded by date, round and payment reference. The probability engine is a mathematical demonstration and can be replaced by a governance-approved fixed rotation.</p></div>',unsafe_allow_html=True)
        st.dataframe(df("SELECT r.round_no Round_No,b.code Branch,r.contribution_amount Contribution,r.expected_members Members,r.total_pool Total_Pool,r.start_date Start_Date,r.draw_date Draw_Date,r.status Status,COALESCE(m.full_name,'') Winner FROM equb_rounds r LEFT JOIN branches b ON r.branch_id=b.id LEFT JOIN members m ON r.winner_member_id=m.id ORDER BY r.id DESC"),use_container_width=True,hide_index=True)
    with t[1]: equb_rounds()
    with t[2]: equb_contributions()
    with t[3]: equb_probability()

def equb_rounds():
    st.subheader("Round Management"); bs=branches("Equb")
    if not bs: st.warning("Create an Equb branch first."); return
    opts=[f"{x['code']} | {x['name']}" for x in bs]
    with st.form("round"):
        a,b=st.columns(2); bc=a.selectbox("Equb Branch",opts); rn=b.number_input("Round Number",1,100000,1); amount=a.number_input("Fixed Round Contribution (ETB)",1.,step=100.,value=1000.); sd=b.date_input("Start Date",date.today()); dd=a.date_input("Payout or Draw Date",date.today()); status=b.selectbox("Status",["Open","Completed","Cancelled"]); ok=st.form_submit_button("Create Equb Round",type="primary")
    if ok:
        branch=bs[opts.index(bc)]; n=sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND branch_id=? AND status='Active'",(branch["id"],),True)[0]["n"]; pool=n*amount
        sql("INSERT INTO equb_rounds(branch_id,round_no,contribution_amount,start_date,draw_date,expected_members,total_pool,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(branch["id"],rn,amount,str(sd),str(dd),n,pool,status,now())); audit("Created Equb round","Equb",f"Round {rn}"); st.success("Equb round created."); st.rerun()

def update_pool(rid):
    x=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE round_id=? AND status='Paid'",(rid,),True)[0]["n"]; sql("UPDATE equb_rounds SET total_pool=? WHERE id=?",(x,rid))

def equb_contributions():
    st.subheader("Contribution Management"); ms=members("Equb")
    if not ms: st.info("Register Equb members first."); return
    rs=sql("SELECT r.id,r.round_no,b.code FROM equb_rounds r JOIN branches b ON r.branch_id=b.id WHERE r.status<>'Cancelled' ORDER BY r.id DESC",fetch=True)
    mo=[f"{m['member_no']} | {m['full_name']}" for m in ms]; ro=[f"{r['id']} | Round {r['round_no']} | {r['code']}" for r in rs]
    with st.form("contrib"):
        mc=st.selectbox("Member",mo); rc=st.selectbox("Equb Round",ro or ["No round available"]); amount=st.number_input("Contribution Amount (ETB)",0.,step=100.); cd=st.date_input("Contribution Date",date.today()); status=st.selectbox("Payment Status",["Pending","Paid","Cancelled"]); method=st.selectbox("Payment Method",["Cash","Bank Transfer","Mobile Money","Other"]); ref=st.text_input("Payment Reference"); notes=st.text_area("Notes"); ok=st.form_submit_button("Record Contribution",type="primary")
    if ok:
        if amount<=0: st.error("Amount must be greater than zero."); return
        m=ms[mo.index(mc)]; rid=int(rc.split("|")[0]) if rs and rc!="No round available" else None
        sql("INSERT INTO contributions(member_id,module,round_id,amount,contribution_date,status,reference,payment_method,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(m["id"],"Equb",rid,amount,str(cd),status,ref,method,notes,now()))
        if status=="Paid": sql("UPDATE members SET regular_contribution=? WHERE id=?",(amount,m["id"]))
        if rid: update_pool(rid)
        audit("Recorded Equb contribution","Equb",f"{m['member_no']} {money(amount)}"); st.success("Contribution recorded."); st.rerun()
    st.dataframe(df("SELECT c.contribution_date Date,m.member_no Member_No,m.full_name Member,c.amount Amount,c.status Status,c.payment_method Payment_Method,c.reference Reference,c.notes Notes FROM contributions c JOIN members m ON c.member_id=m.id WHERE c.module='Equb' ORDER BY c.id DESC LIMIT 500"),use_container_width=True,hide_index=True)

# ============================================================
# MODULE 6: WEIGHTED PROBABILITY ENGINE
# ============================================================

def probability_table():
    ms=members("Equb"); rows=[]
    for m in ms:
        paid=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE member_id=? AND module='Equb' AND status='Paid'",(m["id"],),True)[0]["n"]
        rows.append({"Member_No":m["member_no"],"Member":m["full_name"],"Branch":m["branch_name"],"Regular_Contribution":float(m["regular_contribution"] or 0),"Historical_Paid":float(paid or 0),"Trust_Score":float(m["trust_score"] or 0)})
    x=pd.DataFrame(rows)
    if x.empty:return x
    total=x.Regular_Contribution.sum(); x["Contribution_Weight"]=(x.Regular_Contribution/total if total>0 else 1/len(x)); x["Probability"]=x["Contribution_Weight"]; return x

def equb_probability():
    st.subheader("Contribution-Weighted Probability Engine"); x=probability_table()
    if x.empty: st.info("Register Equb members first."); return
    if x.Regular_Contribution.sum()<=0: st.warning("All regular contributions are zero; equal probabilities are used.")
    st.dataframe(x,use_container_width=True,hide_index=True)
    a,b=st.columns(2); a.metric("Total Regular Contribution",money(x.Regular_Contribution.sum()))
    if b.button("Run Weighted Demonstration",type="primary",use_container_width=True):
        ms=members("Equb"); i=random.choices(range(len(ms)),weights=x.Probability.tolist(),k=1)[0]; w=ms[i]
        st.success(f"Selected demonstration member: {w['full_name']} ({w['member_no']})"); audit("Executed weighted probability demonstration","Equb",w["member_no"])
    st.markdown('<div class="box"><div class="title">Model note</div><p>For member i, the demonstration weight is proportional to the positive regular contribution C_i. Thus w_i = C_i / sum(C_j). If all contributions are zero, equal probabilities are assigned. This is a research prototype rather than a mandatory Equb governance rule.</p></div>',unsafe_allow_html=True)

# ============================================================
# MODULE 7: IDDIR RISK SHARING
# ============================================================

def iddir():
    header("Module 7: IDFS Iddir","Community risk sharing for funeral, wedding, holiday, emergency and other approved needs")
    t=st.tabs(["Overview","Community Events","Property Management","Transactions","Member Support History"])
    with t[0]: iddir_overview()
    with t[1]: iddir_events()
    with t[2]: iddir_properties()
    with t[3]: iddir_transaction_view()
    with t[4]: iddir_history()

def iddir_overview():
    n=sql("SELECT COUNT(*) n FROM members WHERE module='Iddir' AND status='Active'",fetch=True)[0]["n"]
    ben=sql("SELECT COALESCE(SUM(approved_amount),0) n FROM iddir_events WHERE status IN ('Approved','Paid')",fetch=True)[0]["n"]
    pv=sql("SELECT COALESCE(SUM(current_value),0) n FROM properties WHERE status='Active'",fetch=True)[0]["n"]
    pending=sql("SELECT COUNT(*) n FROM iddir_events WHERE status='Pending'",fetch=True)[0]["n"]
    a,b,c,d=st.columns(4); a.metric("Active Members",n); b.metric("Approved Support",money(ben)); c.metric("Active Property Value",money(pv)); d.metric("Pending Cases",pending)
    st.markdown('<div class="box"><div class="title">Iddir operating scope</div><p>The platform records community support cases for funeral, wedding, holiday, emergency, medical, family and other approved purposes. The same module maintains community property such as land, buildings, vehicles, equipment and furniture.</p></div>',unsafe_allow_html=True)

def iddir_events():
    st.subheader("Community Event and Benefit Management"); ms=members("Iddir")
    if not ms: st.info("Register Iddir members first."); return
    mo=[f"{m['member_no']} | {m['full_name']}" for m in ms]
    with st.form("event"):
        mc=st.selectbox("Member or Beneficiary",mo); typ=st.selectbox("Event Type",EVENT_TYPES); ed=st.date_input("Event Date",date.today()); requested=st.number_input("Requested Amount (ETB)",0.,step=100.); approved=st.number_input("Approved Amount (ETB)",0.,step=100.); status=st.selectbox("Status",["Pending","Approved","Rejected","Paid"]); ref=st.text_input("Case or Payment Reference"); desc=st.text_area("Description"); ok=st.form_submit_button("Record Community Support Case",type="primary")
    if ok:
        m=ms[mo.index(mc)]; paid_date=str(date.today()) if status=="Paid" else None
        sql("INSERT INTO iddir_events(branch_id,event_type,member_id,event_date,description,requested_amount,approved_amount,status,payment_date,reference,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(m["branch_id"],typ,m["id"],str(ed),desc,requested,approved,status,paid_date,ref,now()))
        if status=="Paid" and approved>0: sql("INSERT INTO transactions(module,branch_id,member_id,transaction_type,amount,reference,transaction_date,description,created_at) VALUES(?,?,?,?,?,?,?,?,?)",("Iddir",m["branch_id"],m["id"],"Community Benefit Payment",approved,ref,str(ed),typ+" support",now()))
        audit("Recorded Iddir support case","Iddir",f"{typ} for {m['member_no']}"); st.success("Support case recorded."); st.rerun()
    st.dataframe(df("SELECT e.event_date Event_Date,e.event_type Event_Type,m.member_no Member_No,m.full_name Member,e.requested_amount Requested,e.approved_amount Approved,e.status Status,e.reference Reference,e.description Description FROM iddir_events e JOIN members m ON e.member_id=m.id ORDER BY e.id DESC"),use_container_width=True,hide_index=True)

# ============================================================
# MODULE 8: IDDIR PROPERTY MANAGEMENT
# ============================================================

def iddir_properties():
    st.subheader("Iddir Property Management"); bs=branches("Iddir")
    if not bs: st.warning("Create an Iddir branch first."); return
    bo=[f"{b['code']} | {b['name']}" for b in bs]
    with st.form("property"):
        bc=st.selectbox("Iddir Branch",bo); a,b=st.columns(2); code=a.text_input("Property Code"); typ=b.selectbox("Property Type",PROPERTY_TYPES); desc=a.text_input("Description"); loc=b.text_input("Location"); ad=a.date_input("Acquisition Date",date.today()); cost=b.number_input("Acquisition Cost (ETB)",0.,step=1000.); value=a.number_input("Current Estimated Value (ETB)",0.,step=1000.); status=b.selectbox("Status",["Active","Under Maintenance","Disposed","Transferred"]); cust=a.text_input("Custodian"); notes=st.text_area("Notes"); ok=st.form_submit_button("Register Property",type="primary")
    if ok:
        if not code.strip(): st.error("Property code is required."); return
        branch=bs[bo.index(bc)]
        try:
            sql("INSERT INTO properties(branch_id,property_code,property_type,description,location,acquisition_date,acquisition_cost,current_value,status,custodian,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(branch["id"],code,typ,desc,loc,str(ad),cost,value,status,cust,notes,now())); audit("Registered Iddir property","Iddir",code); st.success("Property registered."); st.rerun()
        except sqlite3.IntegrityError: st.error("Property code already exists.")
    st.dataframe(df("SELECT p.property_code Property_Code,p.property_type Type,p.description Description,b.code Branch,p.location Location,p.acquisition_date Acquisition_Date,p.acquisition_cost Acquisition_Cost,p.current_value Current_Value,p.status Status,p.custodian Custodian,p.notes Notes FROM properties p LEFT JOIN branches b ON p.branch_id=b.id ORDER BY p.id DESC"),use_container_width=True,hide_index=True)

def iddir_transaction_view():
    st.subheader("Iddir Transactions"); st.dataframe(df("SELECT transaction_date Date,transaction_type Transaction_Type,amount Amount,reference Reference,description Description FROM transactions WHERE module='Iddir' ORDER BY id DESC"),use_container_width=True,hide_index=True)

def iddir_history():
    ms=members("Iddir")
    if not ms: st.info("No Iddir members registered."); return
    mo=[f"{m['member_no']} | {m['full_name']}" for m in ms]; pick=st.selectbox("Select Member",mo); m=ms[mo.index(pick)]
    st.dataframe(df("SELECT event_date Event_Date,event_type Event_Type,requested_amount Requested,approved_amount Approved,status Status,reference Reference,description Description FROM iddir_events WHERE member_id=? ORDER BY id DESC",(m["id"],)),use_container_width=True,hide_index=True)

# ============================================================
# MODULE 9: TRANSACTIONS
# ============================================================

def transactions():
    header("Module 9: Transactions","Centralized transaction register for Equb and Iddir")
    t1,t2=st.tabs(["Record Transaction","Transaction Register"])
    with t1:
        bs=branches(); ms=members(); bo=[f"{b['code']} | {b['name']}" for b in bs]; mo=["No member"]+[f"{m['member_no']} | {m['full_name']}" for m in ms]
        with st.form("tx"):
            module=st.selectbox("Module",MODULES); bc=st.selectbox("Branch",bo); mc=st.selectbox("Member",mo); typ=st.selectbox("Transaction Type",["Contribution","Savings Receipt","Payout","Community Benefit Payment","Asset Purchase","Asset Sale","Other"]); amount=st.number_input("Amount (ETB)",0.,step=100.); td=st.date_input("Transaction Date",date.today()); ref=st.text_input("Reference"); desc=st.text_area("Description"); ok=st.form_submit_button("Record Transaction",type="primary")
        if ok:
            branch=bs[bo.index(bc)]; member_id=None if mc=="No member" else ms[mo.index(mc)-1]["id"]
            sql("INSERT INTO transactions(module,branch_id,member_id,transaction_type,amount,reference,transaction_date,description,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(module,branch["id"],member_id,typ,amount,ref,str(td),desc,now())); audit("Recorded transaction",module,f"{typ}: {money(amount)}"); st.success("Transaction recorded."); st.rerun()
    with t2: st.dataframe(df("SELECT t.transaction_date Date,t.module Module,b.code Branch,COALESCE(m.member_no,'') Member_No,t.transaction_type Type,t.amount Amount,t.reference Reference,t.description Description FROM transactions t LEFT JOIN branches b ON t.branch_id=b.id LEFT JOIN members m ON t.member_id=m.id ORDER BY t.id DESC LIMIT 1000"),use_container_width=True,hide_index=True)

# ============================================================
# MODULE 10: REPORTS
# ============================================================

def download(x,name):
    if not x.empty: st.download_button("Download CSV",x.to_csv(index=False).encode(),name,"text/csv")

def reports():
    header("Module 10: Reports and Analytics","Management information and downloadable records")
    typ=st.selectbox("Report",["Executive Summary","Member Register","Equb Contributions","Equb Rounds","Equb Probability","Iddir Community Support","Iddir Properties","Transactions"])
    if typ=="Executive Summary": q="SELECT module Module,COUNT(*) Active_Members,ROUND(AVG(regular_contribution),2) Average_Contribution,ROUND(AVG(trust_score),3) Average_Trust FROM members WHERE status='Active' GROUP BY module"; name="idfs_summary.csv"
    elif typ=="Member Register": q="SELECT m.member_no Member_No,m.full_name Full_Name,m.module Module,b.name Branch,m.phone Phone,m.join_date Join_Date,m.regular_contribution Regular_Contribution,m.trust_score Trust_Score,m.status Status FROM members m LEFT JOIN branches b ON m.branch_id=b.id ORDER BY m.module,m.full_name"; name="idfs_members.csv"
    elif typ=="Equb Contributions": q="SELECT m.member_no Member_No,m.full_name Member,COUNT(c.id) Payments,COALESCE(SUM(c.amount),0) Total_Paid FROM members m LEFT JOIN contributions c ON m.id=c.member_id AND c.module='Equb' AND c.status='Paid' WHERE m.module='Equb' GROUP BY m.id ORDER BY Total_Paid DESC"; name="idfs_equb_contributions.csv"
    elif typ=="Equb Rounds": q="SELECT r.round_no Round_No,b.code Branch,r.contribution_amount Contribution,r.expected_members Members,r.total_pool Total_Pool,r.start_date Start_Date,r.draw_date Draw_Date,r.status Status,COALESCE(m.full_name,'') Winner FROM equb_rounds r JOIN branches b ON r.branch_id=b.id LEFT JOIN members m ON r.winner_member_id=m.id ORDER BY r.id DESC"; name="idfs_equb_rounds.csv"
    elif typ=="Equb Probability": x=probability_table(); st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_equb_probability.csv"); return
    elif typ=="Iddir Community Support": q="SELECT event_type Event_Type,COUNT(*) Cases,COALESCE(SUM(requested_amount),0) Requested,COALESCE(SUM(approved_amount),0) Approved FROM iddir_events GROUP BY event_type ORDER BY Approved DESC"; name="idfs_iddir_support.csv"
    elif typ=="Iddir Properties": q="SELECT property_type Property_Type,COUNT(*) Assets,COALESCE(SUM(acquisition_cost),0) Acquisition_Cost,COALESCE(SUM(current_value),0) Current_Value FROM properties GROUP BY property_type ORDER BY Current_Value DESC"; name="idfs_iddir_properties.csv"
    else: q="SELECT module Module,transaction_type Transaction_Type,COUNT(*) Transactions,COALESCE(SUM(amount),0) Total_Amount FROM transactions GROUP BY module,transaction_type ORDER BY module,Total_Amount DESC"; name="idfs_transactions.csv"
    x=df(q); st.dataframe(x,use_container_width=True,hide_index=True); download(x,name)

# ============================================================
# MODULE 11: AUDIT TRAIL
# ============================================================

def audit_page():
    header("Module 11: Audit Trail","Traceable record of important system activities")
    x=df("SELECT timestamp Timestamp,username Username,module Module,action Action,details Details FROM audit_log ORDER BY id DESC LIMIT 2000"); st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_audit.csv")

# ============================================================
# MODULE 12: USER ADMINISTRATION
# ============================================================

def users_page():
    header("Module 12: User Administration","Role-based demonstration accounts")
    st.dataframe(df("SELECT username Username,full_name Full_Name,role Role,module Module,active Active,created_at Created_At FROM users ORDER BY username"),use_container_width=True,hide_index=True)
    with st.form("user"):
        a,b=st.columns(2); u=a.text_input("Username"); n=b.text_input("Full Name"); p=a.text_input("Password",type="password"); r=b.selectbox("Role",ROLES); m=a.selectbox("Module",["Portal"]+MODULES); bs=branches(m if m in MODULES else None); bo=["No branch"]+[f"{x['code']} | {x['name']}" for x in bs]; bc=a.selectbox("Branch",bo); ok=st.form_submit_button("Create User",type="primary")
    if ok:
        if len(p)<6: st.error("Password must contain at least six characters."); return
        bid=None if bc=="No branch" else bs[bo.index(bc)-1]["id"]
        try:
            sql("INSERT INTO users(username,password_hash,full_name,role,module,branch_id,created_at) VALUES(?,?,?,?,?,?,?)",(u,pwd_hash(p),n,r,m,bid,now())); audit("Created user","Portal",u); st.success("User created."); st.rerun()
        except sqlite3.IntegrityError: st.error("Username already exists.")

# ============================================================
# MODULE 1: DASHBOARD
# ============================================================

def dashboard():
    header("IDFS Executive Dashboard","Integrated Equb savings and Iddir community risk-sharing platform")
    m=sql("SELECT COUNT(*) n FROM members WHERE status='Active'",fetch=True)[0]["n"]; b=sql("SELECT COUNT(*) n FROM branches WHERE status='Active'",fetch=True)[0]["n"]; c=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"]; p=sql("SELECT COALESCE(SUM(current_value),0) n FROM properties WHERE status='Active'",fetch=True)[0]["n"]
    a,bx,cx,d=st.columns(4); a.metric("Active Members",m); bx.metric("Active Branches",b); cx.metric("Equb Savings",money(c)); d.metric("Iddir Property",money(p))
    a,b=st.columns(2)
    with a: st.markdown('<div class="box"><div class="title">IDFS Equb</div><p>Community savings, regular contributions, rounds, payment records and contribution-weighted probability demonstration.</p></div>',unsafe_allow_html=True)
    with b: st.markdown('<div class="box"><div class="title">IDFS Iddir</div><p>Community risk sharing for funeral, wedding, holiday, emergency, medical and other approved support, together with property management.</p></div>',unsafe_allow_html=True)
    st.subheader("Recent Activity"); st.dataframe(df("SELECT timestamp Timestamp,username User,module Module,action Action,details Details FROM audit_log ORDER BY id DESC LIMIT 15"),use_container_width=True,hide_index=True)

# ============================================================
# MAIN
# ============================================================

def main():
    init_db()
    if not st.session_state.get("authenticated",False): login(); return
    st.sidebar.title("IDFS Web Platform")
    st.sidebar.caption("Indigenous Digital Financial System")
    st.sidebar.write(f"User: {st.session_state.get('full_name','')}")
    st.sidebar.write(f"Role: {st.session_state.get('role','')}")
    if st.sidebar.button("Sign out",use_container_width=True): audit("Logout"); st.session_state.clear(); st.rerun()
    nav=["Dashboard","Branch Management","Member Management","IDFS Equb","IDFS Iddir","Transactions","Reports and Analytics","Audit Trail"]
    if st.session_state.get("role")=="Administrator": nav.append("User Administration")
    page=st.sidebar.radio("Navigation",nav)
    if page=="Dashboard": dashboard()
    elif page=="Branch Management": branch_page()
    elif page=="Member Management": member_page()
    elif page=="IDFS Equb": equb()
    elif page=="IDFS Iddir": iddir()
    elif page=="Transactions": transactions()
    elif page=="Reports and Analytics": reports()
    elif page=="Audit Trail": audit_page()
    elif page=="User Administration": users_page()

if __name__=="__main__": main()
