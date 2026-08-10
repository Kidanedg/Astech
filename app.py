import streamlit as st
import sqlite3, hashlib, secrets, random
from datetime import datetime, date
from pathlib import Path

st.set_page_config(page_title="IDFS | Equb & Iddir", page_icon="🏦", layout="wide")

DB = Path("idfs_demo.db")
MODULES = ["Equb", "Iddir"]
ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]

st.markdown("""<style>
.main{background:#f7f9fc}.block-container{padding-top:1rem}
.idfs{padding:18px;border-radius:14px;background:linear-gradient(135deg,#0B5CAD,#243447);color:white;margin-bottom:18px}
.card{padding:18px;border:1px solid #e2e7ee;border-radius:12px;background:white}
</style>""", unsafe_allow_html=True)

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def conn():
    c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; return c

def sql(q,p=(),fetch=False,many=False):
    c=conn(); x=c.cursor()
    if many: x.executemany(q,p)
    else: x.execute(q,p)
    r=x.fetchall() if fetch else None; c.commit(); c.close(); return r

def pwd_hash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    h=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()
    return salt+"$"+h

def check_pwd(password,stored):
    try:
        salt,h=stored.split("$",1)
        x=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()
        return secrets.compare_digest(x,h)
    except: return False

def audit(action,module="Portal",details=""):
    sql("INSERT INTO audit_log(username,action,module,details,timestamp) VALUES(?,?,?,?,?)",
        (st.session_state.get("username","anonymous"),action,module,details,now()))

def init():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY,username TEXT UNIQUE,password_hash TEXT,full_name TEXT,
      role TEXT,module TEXT,branch_id INTEGER,active INTEGER DEFAULT 1,created_at TEXT);
    CREATE TABLE IF NOT EXISTS branches(
      id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT,module TEXT,location TEXT,
      manager TEXT,status TEXT DEFAULT 'Active',created_at TEXT);
    CREATE TABLE IF NOT EXISTS members(
      id INTEGER PRIMARY KEY,member_no TEXT UNIQUE,full_name TEXT,phone TEXT,sex TEXT,
      join_date TEXT,module TEXT,branch_id INTEGER,contribution_amount REAL DEFAULT 0,
      trust_score REAL DEFAULT .5,status TEXT DEFAULT 'Active',created_at TEXT);
    CREATE TABLE IF NOT EXISTS equb_rounds(
      id INTEGER PRIMARY KEY,branch_id INTEGER,round_no INTEGER,contribution REAL,
      start_date TEXT,draw_date TEXT,status TEXT,winner_member_id INTEGER,total_pool REAL,
      created_at TEXT);
    CREATE TABLE IF NOT EXISTS contributions(
      id INTEGER PRIMARY KEY,member_id INTEGER,module TEXT,round_id INTEGER,amount REAL,
      contribution_date TEXT,status TEXT,reference TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS iddir_events(
      id INTEGER PRIMARY KEY,branch_id INTEGER,event_type TEXT,member_id INTEGER,
      event_date TEXT,description TEXT,approved_amount REAL,status TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS properties(
      id INTEGER PRIMARY KEY,branch_id INTEGER,property_code TEXT UNIQUE,property_type TEXT,
      description TEXT,location TEXT,acquisition_date TEXT,value REAL,status TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS transactions(
      id INTEGER PRIMARY KEY,module TEXT,branch_id INTEGER,member_id INTEGER,
      transaction_type TEXT,amount REAL,reference TEXT,transaction_date TEXT,
      description TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_log(
      id INTEGER PRIMARY KEY,username TEXT,action TEXT,module TEXT,details TEXT,timestamp TEXT);
    """); c.commit(); c.close()
    if not sql("SELECT id FROM users WHERE username='admin'",fetch=True):
        sql("INSERT INTO users(username,password_hash,full_name,role,module,created_at) VALUES(?,?,?,?,?,?)",
            ("admin",pwd_hash("admin123"),"IDFS Administrator","Administrator","Portal",now()))
    if not sql("SELECT id FROM branches LIMIT 1",fetch=True):
        rows=[("EQB-001","IDFS Equb Central Branch","Equb","Aksum","Branch Manager"),
              ("EQB-002","IDFS Equb North Branch","Equb","Shire","Branch Manager"),
              ("IDR-001","IDFS Iddir Central Branch","Iddir","Aksum","Branch Manager"),
              ("IDR-002","IDFS Iddir Community Branch","Iddir","Shire","Branch Manager")]
        sql("INSERT INTO branches(code,name,module,location,manager,created_at) VALUES(?,?,?,?,?,?)",
            [(a,b,c,d,e,now()) for a,b,c,d,e in rows],many=True)

def df(q,p=()):
    import pandas as pd
    return pd.DataFrame([dict(x) for x in sql(q,p,fetch=True)])

def money(x): return f"ETB {float(x or 0):,.2f}"

def login():
    st.markdown('<div class="idfs"><h1>🏦 IDFS</h1><p>Indigenous Digital Financial System</p><p>Equb Saving • Iddir Risk Sharing • Community Finance</p></div>',unsafe_allow_html=True)
    _,c,_=st.columns([1,1.2,1])
    with c:
        st.subheader("Secure Demo Login")
        with st.form("login"):
            u=st.text_input("Username"); p=st.text_input("Password",type="password")
            ok=st.form_submit_button("Sign in",type="primary",use_container_width=True)
        if ok:
            r=sql("SELECT * FROM users WHERE username=? AND active=1",(u.strip(),),True)
            if r and check_pwd(p,r[0]["password_hash"]):
                x=r[0]
                for k in ["authenticated","user_id","username","full_name","role","module","branch_id"]:
                    st.session_state[k]=x["id"] if k=="user_id" else (True if k=="authenticated" else x[k])
                audit("Login successful"); st.rerun()
            else: st.error("Invalid username or password.")
        st.info("Demo login: admin / admin123")

def header(title,sub=""):
    st.markdown(f'<div class="idfs"><h1>{title}</h1><p>{sub}</p></div>',unsafe_allow_html=True)

def branches(module=None):
    return sql("SELECT * FROM branches "+("WHERE module=? " if module else "")+"ORDER BY name",
               (module,) if module else (),True)

def members(module=None,branch=None):
    w=[]; p=[]
    if module:w.append("module=?");p.append(module)
    if branch:w.append("branch_id=?");p.append(branch)
    return sql("SELECT * FROM members"+((" WHERE "+" AND ".join(w)) if w else "")+" ORDER BY full_name",tuple(p),True)

def dashboard():
    header("IDFS Executive Dashboard","Integrated Equb saving and Iddir community risk-sharing platform")
    m=sql("SELECT COUNT(*) n FROM members",fetch=True)[0]["n"]
    b=sql("SELECT COUNT(*) n FROM branches",fetch=True)[0]["n"]
    c=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE status='Paid'",fetch=True)[0]["n"]
    p=sql("SELECT COALESCE(SUM(value),0) n FROM properties WHERE status='Active'",fetch=True)[0]["n"]
    a,bx,cx,d=st.columns(4); a.metric("Members",m); bx.metric("Branches",b); cx.metric("Contributions",money(c)); d.metric("Iddir Property",money(p))
    st.divider()
    x,y=st.columns(2)
    x.markdown('<div class="card"><h2>💰 IDFS Equb</h2><p>Community savings, regular contributions, rounds and transparent weighted participation probability.</p></div>',unsafe_allow_html=True)
    y.markdown('<div class="card"><h2>🤝 IDFS Iddir</h2><p>Mutual risk sharing for funeral, wedding, holiday, emergency and other approved community support, plus property management.</p></div>',unsafe_allow_html=True)
    st.subheader("Recent activity")
    st.dataframe(df("SELECT timestamp,username,module,action,details FROM audit_log ORDER BY id DESC LIMIT 10"),use_container_width=True,hide_index=True)

def branch_page():
    header("Branch Management","Bank-style Equb and Iddir branch structure")
    t1,t2=st.tabs(["Directory","Register"])
    with t1: st.dataframe(df("SELECT code,name,module,location,manager,status FROM branches ORDER BY module,name"),use_container_width=True,hide_index=True)
    with t2:
        with st.form("branch"):
            a,b=st.columns(2); code=a.text_input("Branch Code"); name=b.text_input("Branch Name")
            mod=a.selectbox("Module",MODULES); loc=b.text_input("Location"); mgr=a.text_input("Manager")
            ok=st.form_submit_button("Create Branch",type="primary")
        if ok:
            try:
                sql("INSERT INTO branches(code,name,module,location,manager,created_at) VALUES(?,?,?,?,?,?)",(code,name,mod,loc,mgr,now()))
                audit("Created branch",mod,code); st.success("Created."); st.rerun()
            except: st.error("Branch code already exists.")

def member_page():
    header("Member Management","Register and monitor Equb and Iddir members")
    t1,t2=st.tabs(["Directory","Register"])
    with t1:
        st.dataframe(df("""SELECT m.member_no,m.full_name,m.phone,m.module,b.name branch,
                          m.contribution_amount,m.trust_score,m.status
                          FROM members m LEFT JOIN branches b ON m.branch_id=b.id
                          ORDER BY m.module,m.full_name"""),use_container_width=True,hide_index=True)
    with t2:
        with st.form("member"):
            a,b=st.columns(2); no=a.text_input("Member Number"); name=b.text_input("Full Name")
            phone=a.text_input("Phone"); sex=b.selectbox("Sex",["Not specified","Female","Male"])
            mod=a.selectbox("Module",MODULES); bs=branches(mod); bn=[f"{x['code']} | {x['name']}" for x in bs]
            bc=b.selectbox("Branch",bn or ["No branch"]); contrib=a.number_input("Regular Contribution (ETB)",min_value=0.,step=100.)
            jd=b.date_input("Join Date",date.today()); ok=st.form_submit_button("Register Member",type="primary")
        if ok and no and name and bs:
            bid=bs[bn.index(bc)]["id"]
            try:
                sql("""INSERT INTO members(member_no,full_name,phone,sex,join_date,module,branch_id,contribution_amount,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?)""",(no,name,phone,sex,str(jd),mod,bid,contrib,now()))
                audit("Registered member",mod,no); st.success("Registered."); st.rerun()
            except: st.error("Member number already exists.")

def weighted(ms):
    vals=[max(0,float(x["contribution_amount"] or 0)) for x in ms]; total=sum(vals)
    return ([1/len(ms)]*len(ms)) if total==0 else [v/total for v in vals]

def equb():
    header("IDFS Equb","Community saving, contribution and rotating payout demonstration")
    t=st.tabs(["Overview","Rounds","Contributions","Probability Engine"])
    with t[0]:
        n=sql("SELECT COUNT(*) n FROM members WHERE module='Equb'",fetch=True)[0]["n"]
        pool=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"]
        r=sql("SELECT COUNT(*) n FROM equb_rounds",fetch=True)[0]["n"]
        a,b,c=st.columns(3);a.metric("Members",n);b.metric("Contribution Pool",money(pool));c.metric("Rounds",r)
        st.write("The prototype records a fixed contribution plan per member/round and uses contribution-weighted participation probability.")
        st.latex(r"w_i=\\frac{C_i}{\\sum_{j=1}^{n}C_j},\\qquad P_i=w_i")
    with t[1]:
        bs=branches("Equb")
        if bs:
            with st.form("round"):
                names=[f"{x['code']} | {x['name']}" for x in bs]; bc=st.selectbox("Branch",names)
                rn=st.number_input("Round Number",1,1000,1); amount=st.number_input("Round Contribution (ETB)",1.,step=100.,value=1000.)
                sd=st.date_input("Start",date.today()); dd=st.date_input("Draw/Payout",date.today()); status=st.selectbox("Status",["Open","Completed","Cancelled"])
                ok=st.form_submit_button("Create Round",type="primary")
            if ok:
                bid=bs[names.index(bc)]["id"]; pool=len(members("Equb",bid))*amount
                sql("""INSERT INTO equb_rounds(branch_id,round_no,contribution,start_date,draw_date,status,total_pool,created_at)
                       VALUES(?,?,?,?,?,?,?,?)""",(bid,rn,amount,str(sd),str(dd),status,pool,now()))
                audit("Created Equb round","Equb",f"Round {rn}");st.success("Round created.");st.rerun()
            st.dataframe(df("""SELECT r.round_no,b.code,b.name,r.contribution,r.start_date,r.draw_date,r.status,r.total_pool
                               FROM equb_rounds r LEFT JOIN branches b ON r.branch_id=b.id ORDER BY r.id DESC"""),use_container_width=True,hide_index=True)
    with t[2]:
        ms=members("Equb")
        if ms:
            with st.form("contrib"):
                names=[f"{x['member_no']} | {x['full_name']}" for x in ms]; mc=st.selectbox("Member",names)
                amount=st.number_input("Amount (ETB)",0.,step=100.); cd=st.date_input("Date",date.today()); ref=st.text_input("Payment Reference")
                ok=st.form_submit_button("Record Contribution",type="primary")
            if ok:
                m=ms[names.index(mc)]
                sql("""INSERT INTO contributions(member_id,module,amount,contribution_date,status,reference,created_at)
                       VALUES(?,?,?,?,?,?,?)""",(m["id"],"Equb",amount,str(cd),"Paid",ref,now()))
                sql("UPDATE members SET contribution_amount=? WHERE id=?",(amount,m["id"]))
                audit("Recorded Equb contribution","Equb",f"{m['member_no']} {amount}");st.success("Recorded.");st.rerun()
            st.dataframe(df("""SELECT c.contribution_date,m.member_no,m.full_name,c.amount,c.status,c.reference
                               FROM contributions c JOIN members m ON c.member_id=m.id
                               WHERE c.module='Equb' ORDER BY c.id DESC LIMIT 100"""),use_container_width=True,hide_index=True)
    with t[3]:
        ms=members("Equb")
        if len(ms)>=2:
            ps=weighted(ms)
            import pandas as pd
            out=pd.DataFrame([{"Member":m["full_name"],"Member No":m["member_no"],"Contribution":float(m["contribution_amount"] or 0),"Probability":p} for m,p in zip(ms,ps)])
            st.dataframe(out.style.format({"Probability":"{:.2%}","Contribution":"{:,.2f}"}),use_container_width=True,hide_index=True)
            if st.button("🎯 Demonstration Winner",type="primary"):
                w=random.choices(ms,weights=ps,k=1)[0]
                st.success(f"Demonstration winner: {w['full_name']} ({w['member_no']})")
                audit("Weighted winner demonstration","Equb",w["member_no"])
        else: st.info("Register at least two Equb members.")

def iddir():
    header("IDFS Iddir","Community risk sharing, benefits and property management")
    t=st.tabs(["Overview","Community Events","Property Management","Transactions"])
    with t[0]:
        n=sql("SELECT COUNT(*) n FROM members WHERE module='Iddir'",fetch=True)[0]["n"]
        ben=sql("SELECT COALESCE(SUM(approved_amount),0) n FROM iddir_events WHERE status IN ('Approved','Paid')",fetch=True)[0]["n"]
        pv=sql("SELECT COALESCE(SUM(value),0) n FROM properties WHERE status='Active'",fetch=True)[0]["n"]
        a,b,c=st.columns(3);a.metric("Members",n);b.metric("Approved Support",money(ben));c.metric("Property Value",money(pv))
        st.write("Common uses include funeral, wedding, holiday, emergency, medical and other community-defined support.")
    with t[1]:
        ms=members("Iddir")
        if ms:
            with st.form("event"):
                names=[f"{x['member_no']} | {x['full_name']}" for x in ms]; mc=st.selectbox("Member / Beneficiary",names)
                typ=st.selectbox("Event Type",["Funeral","Wedding","Holiday","Emergency","Medical Support","Family Support","Other"])
                ed=st.date_input("Event Date",date.today()); amount=st.number_input("Approved/Requested Amount (ETB)",0.,step=100.)
                desc=st.text_area("Description"); status=st.selectbox("Status",["Pending","Approved","Rejected","Paid"])
                ok=st.form_submit_button("Record Event",type="primary")
            if ok:
                m=ms[names.index(mc)]
                sql("""INSERT INTO iddir_events(branch_id,event_type,member_id,event_date,description,approved_amount,status,created_at)
                       VALUES(?,?,?,?,?,?,?,?)""",(m["branch_id"],typ,m["id"],str(ed),desc,amount,status,now()))
                audit("Recorded Iddir event","Iddir",f"{typ} - {m['full_name']}");st.success("Event recorded.");st.rerun()
            st.dataframe(df("""SELECT e.event_date,e.event_type,m.member_no,m.full_name,e.approved_amount,e.status,e.description
                               FROM iddir_events e JOIN members m ON e.member_id=m.id ORDER BY e.id DESC"""),use_container_width=True,hide_index=True)
        else: st.info("Register Iddir members first.")
    with t[2]:
        bs=branches("Iddir")
        if bs:
            with st.form("property"):
                names=[f"{x['code']} | {x['name']}" for x in bs]; bc=st.selectbox("Branch",names)
                code=st.text_input("Property Code"); typ=st.selectbox("Type",["Land","Building","Vehicle","Equipment","Furniture","Other"])
                desc=st.text_input("Description"); loc=st.text_input("Location"); ad=st.date_input("Acquisition Date",date.today())
                value=st.number_input("Value (ETB)",0.,step=1000.); status=st.selectbox("Status",["Active","Under Maintenance","Disposed","Transferred"]); notes=st.text_area("Notes")
                ok=st.form_submit_button("Register Property",type="primary")
            if ok:
                try:
                    sql("""INSERT INTO properties(branch_id,property_code,property_type,description,location,acquisition_date,value,status,notes)
                           VALUES(?,?,?,?,?,?,?,?,?)""",(bs[names.index(bc)]["id"],code,typ,desc,loc,str(ad),value,status,notes))
                    audit("Registered Iddir property","Iddir",code);st.success("Property registered.");st.rerun()
                except: st.error("Property code already exists.")
        st.dataframe(df("""SELECT p.property_code,p.property_type,p.description,b.name branch,p.location,p.acquisition_date,p.value,p.status,p.notes
                           FROM properties p LEFT JOIN branches b ON p.branch_id=b.id ORDER BY p.id DESC"""),use_container_width=True,hide_index=True)
    with t[3]:
        st.dataframe(df("SELECT transaction_date,transaction_type,amount,description,reference FROM transactions WHERE module='Iddir' ORDER BY id DESC"),use_container_width=True,hide_index=True)

def reports():
    header("Reports & Analytics","Management information for the IDFS technology-transfer prototype")
    typ=st.selectbox("Report",["Module Summary","Equb Contributions","Iddir Benefits","Iddir Properties","Transactions","Audit"])
    if typ=="Module Summary": q="SELECT module,COUNT(*) members,ROUND(AVG(contribution_amount),2) avg_contribution,ROUND(AVG(trust_score),3) avg_trust FROM members GROUP BY module"
    elif typ=="Equb Contributions": q="""SELECT m.member_no,m.full_name,SUM(c.amount) total_contribution,COUNT(c.id) payments FROM contributions c JOIN members m ON c.member_id=m.id WHERE c.module='Equb' GROUP BY m.id ORDER BY total_contribution DESC"""
    elif typ=="Iddir Benefits": q="SELECT event_type,COUNT(*) cases,SUM(approved_amount) total_amount FROM iddir_events WHERE status IN ('Approved','Paid') GROUP BY event_type"
    elif typ=="Iddir Properties": q="SELECT property_type,COUNT(*) assets,SUM(value) total_value FROM properties GROUP BY property_type"
    elif typ=="Transactions": q="SELECT module,transaction_type,COUNT(*) transactions,SUM(amount) total_amount FROM transactions GROUP BY module,transaction_type"
    else: q="SELECT timestamp,username,module,action,details FROM audit_log ORDER BY id DESC LIMIT 500"
    x=df(q);st.dataframe(x,use_container_width=True,hide_index=True)
    if not x.empty: st.download_button("⬇️ Download CSV",x.to_csv(index=False).encode(), "idfs_report.csv","text/csv")

def users_page():
    header("User Management","Role-based demo access")
    st.dataframe(df("SELECT username,full_name,role,module,active,created_at FROM users ORDER BY username"),use_container_width=True,hide_index=True)
    with st.form("user"):
        a,b=st.columns(2); u=a.text_input("Username"); n=b.text_input("Full Name"); p=a.text_input("Password",type="password")
        r=b.selectbox("Role",ROLES); m=a.selectbox("Module",["Portal"]+MODULES); ok=st.form_submit_button("Create User",type="primary")
    if ok and len(p)>=6:
        try:
            sql("INSERT INTO users(username,password_hash,full_name,role,module,created_at) VALUES(?,?,?,?,?,?)",(u,pwd_hash(p),n,r,m,now()))
            audit("Created user","Portal",u);st.success("User created.");st.rerun()
        except: st.error("Username already exists.")

def main():
    init()
    if not st.session_state.get("authenticated",False):
        login(); return
    st.sidebar.title("🏦 IDFS")
    st.sidebar.caption("Single-app demonstration • Equb + Iddir")
    st.sidebar.write(f"**{st.session_state.full_name}**")
    if st.sidebar.button("🚪 Logout",use_container_width=True):
        audit("Logout"); st.session_state.clear(); st.rerun()
    nav=["🏠 Dashboard","👥 Members","🏢 Branches","💰 Equb","🤝 Iddir","📊 Reports","🔐 Audit Log"]
    if st.session_state.role=="Administrator": nav+=["⚙️ User Management"]
    page=st.sidebar.radio("Navigation",nav)
    if page=="🏠 Dashboard":dashboard()
    elif page=="👥 Members":member_page()
    elif page=="🏢 Branches":branch_page()
    elif page=="💰 Equb":equb()
    elif page=="🤝 Iddir":iddir()
    elif page=="📊 Reports":reports()
    elif page=="🔐 Audit Log":
        header("Audit Log","Traceable prototype activity")
        st.dataframe(df("SELECT timestamp,username,module,action,details FROM audit_log ORDER BY id DESC LIMIT 1000"),use_container_width=True,hide_index=True)
    elif page=="⚙️ User Management":users_page()

if __name__=="__main__": main()
