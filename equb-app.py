import streamlit as st
import sqlite3, hashlib, secrets, hmac, random
from datetime import datetime, date
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Equb App Management System", page_icon="E", layout="wide")
DB = Path("equb_demo.db")
ROLES = ["Administrator","Branch Manager","Finance Officer","Member"]

st.markdown("""<style>
.main-title{font-size:2rem;font-weight:700;color:#163A5F}
.sub-title{color:#64748B;margin-bottom:1rem}
.section-card{padding:1rem 1.2rem;border:1px solid #E2E8F0;border-radius:12px;background:#F8FAFC;margin-bottom:1rem}
.module-label{color:#0B5CAD;font-weight:700;font-size:.82rem;text-transform:uppercase}
.manual-card{padding:1rem 1.2rem;border:1px solid #CBD5E1;border-radius:10px;background:white;margin-bottom:1rem}
</style>""",unsafe_allow_html=True)

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def money(x):
    try:return f"{float(x):,.2f} ETB"
    except:return "0.00 ETB"
def sql(q,p=(),fetch=False):
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; cur=c.cursor()
    cur.execute(q,p); r=[dict(x) for x in cur.fetchall()] if fetch else None
    c.commit(); c.close(); return r
def df(q,p=()): return pd.DataFrame(sql(q,p,True))
def download(x,name):
    if not x.empty: st.download_button("Download CSV",x.to_csv(index=False).encode(),name,"text/csv",use_container_width=True)
def pwd_hash(p):
    s=secrets.token_hex(16); d=hashlib.pbkdf2_hmac("sha256",p.encode(),s.encode(),120000).hex()
    return f"{s}${d}"
def check_pwd(p,v):
    try:
        s,d=v.split("$",1); t=hashlib.pbkdf2_hmac("sha256",p.encode(),s.encode(),120000).hex()
        return hmac.compare_digest(t,d)
    except:return False
def audit(action,module="Portal",details=""):
    sql("INSERT INTO audit_log(username,module,action,details,timestamp) VALUES(?,?,?,?,?)",
        (st.session_state.get("username","system"),module,action,details,now()))
def header(a,b=""):
    st.markdown(f'<div class="main-title">{a}</div>',unsafe_allow_html=True)
    if b: st.markdown(f'<div class="sub-title">{b}</div>',unsafe_allow_html=True)

def init_db():
    c=sqlite3.connect(DB); x=c.cursor()
    x.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,password_hash TEXT,full_name TEXT,role TEXT,module TEXT,branch_id INTEGER,active INTEGER DEFAULT 1,created_at TEXT);
    CREATE TABLE IF NOT EXISTS branches(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE,name TEXT,module TEXT DEFAULT 'Equb',location TEXT,manager TEXT,phone TEXT,status TEXT DEFAULT 'Active',created_at TEXT);
    CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY AUTOINCREMENT,member_no TEXT UNIQUE,full_name TEXT,phone TEXT,sex TEXT,join_date TEXT,module TEXT DEFAULT 'Equb',branch_id INTEGER,regular_contribution REAL DEFAULT 0,contribution_frequency TEXT DEFAULT 'Monthly',target_round_contribution REAL DEFAULT 0,trust_score REAL DEFAULT .5,status TEXT DEFAULT 'Active',address TEXT,notes TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS equb_rounds(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER,round_no INTEGER,contribution_amount REAL DEFAULT 0,start_date TEXT,draw_date TEXT,expected_members INTEGER DEFAULT 0,total_pool REAL DEFAULT 0,winner_member_id INTEGER,status TEXT DEFAULT 'Open',created_at TEXT);
    CREATE TABLE IF NOT EXISTS contributions(id INTEGER PRIMARY KEY AUTOINCREMENT,member_id INTEGER,module TEXT DEFAULT 'Equb',round_id INTEGER,amount REAL DEFAULT 0,contribution_date TEXT,status TEXT DEFAULT 'Paid',reference TEXT,payment_method TEXT,notes TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,module TEXT DEFAULT 'Equb',branch_id INTEGER,member_id INTEGER,transaction_type TEXT,amount REAL,reference TEXT,transaction_date TEXT,description TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,module TEXT,action TEXT,details TEXT,timestamp TEXT);
    """); c.commit(); c.close()
    if not sql("SELECT id FROM users WHERE username='admin'",fetch=True):
        sql("INSERT INTO users(username,password_hash,full_name,role,module,active,created_at) VALUES(?,?,?,?,?,?,?)",
            ("admin",pwd_hash("admin123"),"Equb Administrator","Administrator","Portal",1,now()))
    for z in [("EQB-001","Equb Central Branch","Aksum"),("EQB-002","Equb North Branch","Shire")]:
        if not sql("SELECT id FROM branches WHERE code=?",(z[0],),True):
            sql("INSERT INTO branches(code,name,module,location,manager,phone,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (z[0],z[1],"Equb",z[2],"Branch Manager","","Active",now()))

def branches():
    return sql("SELECT * FROM branches WHERE module='Equb' ORDER BY name",fetch=True)
def members():
    return sql("""SELECT m.*,b.code branch_code,b.name branch_name FROM members m LEFT JOIN branches b ON m.branch_id=b.id WHERE m.module='Equb' ORDER BY m.full_name""",fetch=True)
def history(mid,rid=None):
    w=["c.member_id=?","c.module='Equb'"]; p=[mid]
    if rid is not None:w.append("c.round_id=?");p.append(rid)
    return df(f"""SELECT c.id Contribution_ID,c.round_id Round_ID,COALESCE(r.round_no,0) Round_No,c.amount Amount,c.contribution_date Date,c.status Status,CASE WHEN COALESCE(r.contribution_amount,0)>0 THEN MIN(c.amount/r.contribution_amount,1) ELSE 0 END Payment_Rate,c.payment_method Payment_Method,c.reference Reference FROM contributions c LEFT JOIN equb_rounds r ON c.round_id=r.id WHERE {' AND '.join(w)} ORDER BY c.id DESC""",p)

def probability(round_id=None,pw=.5,aw=.3,cw=.2,tw=.2):
    ms=members()
    if not ms:return pd.DataFrame()
    rows=[]
    for m in ms:
        h=history(m["id"],round_id)
        planned=float(m["target_round_contribution"] or m["regular_contribution"] or 0)
        paid=float(h.Amount.sum()) if not h.empty else 0
        cons=float(h.Payment_Rate.mean()) if not h.empty else 0
        rows.append(dict(Member_ID=m["id"],Member_No=m["member_no"],Member=m["full_name"],Planned_Contribution=planned,Total_Paid=paid,Payment_Consistency=cons,Trust_Score=float(m["trust_score"] or 0)))
    x=pd.DataFrame(rows); mp=x.Planned_Contribution.max(); ma=x.Total_Paid.max()
    x["Planned_Component"]=x.Planned_Contribution/mp if mp else 0
    x["Paid_Component"]=x.Total_Paid/ma if ma else 0
    x["Contribution_Weighted_Mean"]=pw*x.Planned_Component+aw*x.Paid_Component+cw*x.Payment_Consistency
    x["Adjusted_Score"]=(1-tw)*x.Contribution_Weighted_Mean+tw*x.Trust_Score
    s=x.Adjusted_Score.sum(); x["Probability"]=x.Adjusted_Score/s if s else 1/len(x)
    x["Cumulative_Probability"]=x.Probability.cumsum()
    return x

def login():
    header("Equb App Management System","Secure access to the Equb management prototype.")
    with st.form("login"):
        u=st.text_input("Username"); p=st.text_input("Password",type="password")
        ok=st.form_submit_button("Sign in",type="primary",use_container_width=True)
    if ok:
        r=sql("SELECT * FROM users WHERE username=? AND active=1",(u.strip(),),True)
        if r and check_pwd(p,r[0]["password_hash"]):
            z=r[0]; st.session_state.update(authenticated=True,username=z["username"],full_name=z["full_name"],role=z["role"],branch_id=z["branch_id"]); audit("Successful login"); st.rerun()
        else: st.error("Invalid username or password.")
    st.info("Demonstration account: admin / admin123")

def dashboard():
    header("Equb Executive Dashboard","Branch, member, contribution, round and statistical management.")
    vals=[
        sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND status='Active'",fetch=True)[0]["n"],
        sql("SELECT COUNT(*) n FROM branches WHERE module='Equb' AND status='Active'",fetch=True)[0]["n"],
        sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"],
        sql("SELECT COALESCE(SUM(total_pool),0) n FROM equb_rounds",fetch=True)[0]["n"]]
    a,b,c,d=st.columns(4);a.metric("Active Members",vals[0]);b.metric("Active Branches",vals[1]);c.metric("Equb Savings",money(vals[2]));d.metric("Recorded Pools",money(vals[3]))
    st.markdown("""<div class="section-card"><div class="module-label">Equb App Management System</div>Digital rotating savings management with contribution plans, monthly or round contributions, contribution history, payment consistency, weighted contribution scoring, trust-adjusted probability, round administration, transactions and transparent statistical simulation.</div>""",unsafe_allow_html=True)
    p=probability()
    if not p.empty:
        a,b,c,d=st.columns(4);a.metric("Equb Members",len(p));b.metric("Planned Contribution",money(p.Planned_Contribution.sum()));c.metric("Actual Paid",money(p.Total_Paid.sum()));d.metric("Average Payment Rate",f"{p.Payment_Consistency.mean():.1%}")
    x=df("SELECT timestamp Timestamp,username User,module Module,action Action,details Details FROM audit_log ORDER BY id DESC LIMIT 15")
    if not x.empty:st.dataframe(x,use_container_width=True,hide_index=True)

def branch_page():
    header("Module 2: Branch Management","Bank-style branch structure for Equb.")
    t1,t2=st.tabs(["Branch Directory","Register Branch"])
    with t1:
        x=df("SELECT code Branch_Code,name Branch_Name,module Module,location Location,manager Manager,phone Phone,status Status FROM branches WHERE module='Equb' ORDER BY name");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_branches.csv")
    with t2:
        with st.form("bf"):
            a,b=st.columns(2);code=a.text_input("Branch Code");name=b.text_input("Branch Name");loc=a.text_input("Location");man=b.text_input("Manager");phone=a.text_input("Phone");status=b.selectbox("Status",["Active","Inactive"]);ok=st.form_submit_button("Register Branch",type="primary",use_container_width=True)
        if ok:
            try:sql("INSERT INTO branches(code,name,module,location,manager,phone,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(code.strip(),name.strip(),"Equb",loc,man,phone,status,now()));audit("Created branch","Equb",code);st.success("Branch registered.");st.rerun()
            except sqlite3.IntegrityError:st.error("Branch code already exists.")

def member_page():
    header("Module 3: Member Management","Registration, contribution planning and member profiles.")
    t1,t2,t3=st.tabs(["Directory","Register Member","Member Profile"])
    with t1:
        x=df("""SELECT m.member_no Member_No,m.full_name Full_Name,COALESCE(b.name,'') Branch,m.phone Phone,m.join_date Join_Date,m.regular_contribution Planned_Contribution,m.contribution_frequency Frequency,m.target_round_contribution Round_Contribution,m.trust_score Trust_Score,m.status Status FROM members m LEFT JOIN branches b ON m.branch_id=b.id WHERE m.module='Equb' ORDER BY m.full_name""");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_members.csv")
    with t2:
        bl=branches(); opts=[f"{z['code']} | {z['name']}" for z in bl]
        with st.form("mf"):
            a,b,c=st.columns(3);no=a.text_input("Member Number");name=b.text_input("Full Name");phone=c.text_input("Phone");sex=a.selectbox("Sex",["Not Specified","Male","Female"]);bo=b.selectbox("Branch",opts or ["No branch"]);jd=c.date_input("Join Date",date.today());rc=a.number_input("Regular Contribution (ETB)",0.0,step=50.0,value=1000.0);freq=b.selectbox("Contribution Frequency",["Monthly","Per Round","Weekly","Custom"]);rt=c.number_input("Target Round Contribution (ETB)",0.0,step=50.0);trust=a.number_input("Initial Trust Score (%)",0.0,100.0,50.0,step=1.0);status=b.selectbox("Status",["Active","Inactive","Suspended"]);addr=c.text_input("Address");notes=st.text_area("Notes");ok=st.form_submit_button("Register Member",type="primary",use_container_width=True)
        if ok:
            if not no.strip() or not name.strip():st.error("Member number and full name are required.")
            else:
                bid=bl[opts.index(bo)]["id"] if bo!="No branch" else None
                try:sql("""INSERT INTO members(member_no,full_name,phone,sex,join_date,module,branch_id,regular_contribution,contribution_frequency,target_round_contribution,trust_score,status,address,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(no,name,phone,sex,str(jd),"Equb",bid,rc,freq,rt,trust/100,status,addr,notes,now()));audit("Registered member","Equb",no);st.success("Member registered.");st.rerun()
                except sqlite3.IntegrityError:st.error("Member number already exists.")
    with t3:
        ms=members()
        if not ms:st.info("No members registered yet.");return
        labs=[f"{z['member_no']} | {z['full_name']}" for z in ms];sel=st.selectbox("Select Member",labs);m=ms[labs.index(sel)];h=history(m["id"]);a,b,c,d=st.columns(4);a.metric("Module","Equb");b.metric("Planned Contribution",money(m["regular_contribution"]));c.metric("Total Paid",money(h.Amount.sum() if not h.empty else 0));d.metric("Trust Score",f"{m['trust_score']:.0%}");st.dataframe(pd.DataFrame([{"Member Number":m["member_no"],"Full Name":m["full_name"],"Branch":m["branch_name"] or "","Phone":m["phone"] or "","Frequency":m["contribution_frequency"],"Planned Contribution":m["regular_contribution"],"Round Contribution":m["target_round_contribution"],"Trust Score":f"{m['trust_score']:.2%}","Status":m["status"]}]),use_container_width=True,hide_index=True);st.subheader("Contribution History");st.dataframe(h,use_container_width=True,hide_index=True)

def equb():
    header("Module 4: Equb","Digital rotating savings, rounds, contributions and transparent statistical selection.")
    t=st.tabs(["Overview","Rounds","Contributions","Weighted Probability","Simulation","Draw History"])
    with t[0]: equb_overview()
    with t[1]: round_page()
    with t[2]: contribution_page()
    with t[3]: probability_page()
    with t[4]: simulation_page()
    with t[5]: history_page()

def equb_overview():
    a,b,c,d=st.columns(4);a.metric("Active Members",sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND status='Active'",fetch=True)[0]["n"]);b.metric("Total Contributions",money(sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"]));c.metric("Rounds",sql("SELECT COUNT(*) n FROM equb_rounds",fetch=True)[0]["n"]);d.metric("Recorded Pools",money(sql("SELECT COALESCE(SUM(total_pool),0) n FROM equb_rounds",fetch=True)[0]["n"]))
    x=df("""SELECT m.member_no Member_No,m.full_name Member,m.contribution_frequency Frequency,m.regular_contribution Planned_Contribution,m.target_round_contribution Round_Target,COALESCE(SUM(c.amount),0) Total_Paid FROM members m LEFT JOIN contributions c ON m.id=c.member_id AND c.module='Equb' AND c.status='Paid' WHERE m.module='Equb' GROUP BY m.id ORDER BY m.full_name""");st.dataframe(x,use_container_width=True,hide_index=True)

def round_page():
    bl=branches();opts=[f"{z['code']} | {z['name']}" for z in bl]
    with st.form("rf"):
        a,b,c=st.columns(3);bo=a.selectbox("Branch",opts or ["No branch"]);rn=b.number_input("Round Number",1,step=1);amt=c.number_input("Round Contribution (ETB)",0.0,step=50.0,value=1000.0);sd=a.date_input("Start Date",date.today());dd=b.date_input("Draw Date",date.today());status=c.selectbox("Status",["Open","Closed","Completed"]);ok=st.form_submit_button("Create Equb Round",type="primary",use_container_width=True)
    if ok and bo!="No branch":
        br=bl[opts.index(bo)];n=sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND branch_id=? AND status='Active'",(br["id"],),True)[0]["n"];sql("INSERT INTO equb_rounds(branch_id,round_no,contribution_amount,start_date,draw_date,expected_members,total_pool,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(br["id"],rn,amt,str(sd),str(dd),n,0,status,now()));audit("Created Equb round","Equb",f"{br['code']} Round {rn}");st.success("Round created.");st.rerun()
    x=df("""SELECT r.round_no Round_No,b.code Branch,r.contribution_amount Contribution_Amount,r.expected_members Expected_Members,r.total_pool Total_Pool,r.start_date Start_Date,r.draw_date Draw_Date,r.status Status FROM equb_rounds r JOIN branches b ON r.branch_id=b.id ORDER BY r.id DESC""");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_rounds.csv")

def contribution_page():
    rr=sql("SELECT r.*,b.code branch_code FROM equb_rounds r JOIN branches b ON r.branch_id=b.id WHERE r.status='Open' ORDER BY r.id DESC",fetch=True);ms=members()
    if not rr or not ms:st.info("Create an open round and register members first.");return
    ro=[f"{r['branch_code']} | Round {r['round_no']} | {money(r['contribution_amount'])}" for r in rr];mo=[f"{m['member_no']} | {m['full_name']}" for m in ms]
    with st.form("cf"):
        a,b=st.columns(2);mc=a.selectbox("Member",mo);rc=b.selectbox("Round",ro);m=ms[mo.index(mc)];r=rr[ro.index(rc)];amt=a.number_input("Actual Contribution (ETB)",0.0,value=float(r["contribution_amount"]),step=50.0);dt=b.date_input("Contribution Date",date.today());pm=a.selectbox("Payment Method",["Cash","Bank Transfer","Mobile Money","Other"]);ref=b.text_input("Reference");notes=st.text_area("Notes");ok=st.form_submit_button("Record Contribution",type="primary",use_container_width=True)
    if ok and amt>0:
        sql("INSERT INTO contributions(member_id,module,round_id,amount,contribution_date,status,reference,payment_method,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(m["id"],"Equb",r["id"],amt,str(dt),"Paid",ref,pm,notes,now()));tot=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE round_id=? AND status='Paid'",(r["id"],),True)[0]["n"];sql("UPDATE equb_rounds SET total_pool=? WHERE id=?",(tot,r["id"]));audit("Recorded Equb contribution","Equb",f"{m['member_no']} | {amt}");st.success("Contribution recorded.");st.rerun()
    x=df("""SELECT c.contribution_date Date,m.member_no Member_No,m.full_name Member,b.code Branch,r.round_no Round,r.contribution_amount Planned_Round_Amount,c.amount Actual_Paid,c.status Status,c.reference Reference,c.payment_method Payment_Method FROM contributions c JOIN members m ON c.member_id=m.id JOIN equb_rounds r ON c.round_id=r.id JOIN branches b ON r.branch_id=b.id WHERE c.module='Equb' ORDER BY c.id DESC""");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_contributions.csv")

def probability_page():
    a,b,c,d=st.columns(4);pw=a.number_input("Planned Contribution Rate (%)",0.,100.,50.,1.);aw=b.number_input("Historical Paid Rate (%)",0.,100.,30.,1.);cw=c.number_input("Payment Consistency Rate (%)",0.,100.,20.,1.);tw=d.number_input("Trust Rate (%)",0.,50.,20.,1.)
    if abs(pw+aw+cw-100)>.001:st.error("The three contribution rates must sum to 100%.");return
    x=probability(pw=pw/100,aw=aw/100,cw=cw/100,tw=tw/100)
    if x.empty:st.info("Register Equb members first.");return
    y=x.copy()
    for z in ["Planned_Contribution","Total_Paid"]:y[z]=y[z].map(lambda v:f"{v:,.2f}")
    for z in ["Payment_Consistency","Trust_Score","Contribution_Weighted_Mean","Adjusted_Score","Probability","Cumulative_Probability"]:y[z]=y[z].map(lambda v:f"{v:.2%}")
    st.dataframe(y,use_container_width=True,hide_index=True);download(y,"equb_weighted_probability.csv")

def simulation_page():
    x=probability()
    if x.empty:st.info("Register Equb members first.");return
    n=st.number_input("Number of Simulations",1,10000,1000,100)
    if st.button("Run Monte Carlo Demonstration",type="primary",use_container_width=True):
        r=random.choices(x.Member.tolist(),weights=x.Probability.tolist(),k=int(n));cnt=pd.Series(r).value_counts();y=x[["Member_No","Member","Probability"]].copy();y["Expected_Probability"]=y.Probability;y["Observed_Probability"]=y.Member.map(lambda m:cnt.get(m,0)/n);y["Difference"]=y.Observed_Probability-y.Expected_Probability;st.dataframe(y.sort_values("Observed_Probability",ascending=False),use_container_width=True,hide_index=True);download(y,"equb_monte_carlo.csv");audit("Executed Equb Monte Carlo simulation","Equb",str(n))

def history_page():
    x=df("""SELECT r.round_no Round_No,b.code Branch,r.total_pool Pool,r.draw_date Draw_Date,COALESCE(m.member_no,'') Winner_No,COALESCE(m.full_name,'') Winner,r.status Status FROM equb_rounds r JOIN branches b ON r.branch_id=b.id LEFT JOIN members m ON r.winner_member_id=m.id ORDER BY r.id DESC""");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_draw_history.csv")

def transactions():
    header("Module 6: Transactions","Equb financial transaction recording and history.")
    bl=branches();opts=[f"{z['code']} | {z['name']}" for z in bl]
    with st.form("tf"):
        a,b=st.columns(2);bo=a.selectbox("Branch",opts or ["No branch"]);typ=b.selectbox("Transaction Type",["Deposit","Contribution","Payout","Adjustment","Other"]);amt=a.number_input("Amount (ETB)",0.,step=100.);ref=b.text_input("Reference");dt=a.date_input("Transaction Date",date.today());desc=b.text_area("Description");ok=st.form_submit_button("Record Transaction",type="primary",use_container_width=True)
    if ok:
        bid=bl[opts.index(bo)]["id"] if bo!="No branch" else None;sql("INSERT INTO transactions(module,branch_id,transaction_type,amount,reference,transaction_date,description,created_at) VALUES(?,?,?,?,?,?,?,?)",("Equb",bid,typ,amt,ref,str(dt),desc,now()));audit("Recorded transaction","Equb",f"{typ}: {amt}");st.success("Transaction recorded.");st.rerun()
    x=df("SELECT transaction_date Date,transaction_type Type,amount Amount,reference Reference,description Description FROM transactions WHERE module='Equb' ORDER BY id DESC");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_transactions.csv")

def reports():
    header("Module 7: Reports and Analytics","Equb management information and statistical analysis.")
    r=st.selectbox("Report",["Module Summary","Member Contribution Plans","Equb Contributions","Equb Rounds","Equb Probability","Transactions"])
    q={
    "Module Summary":"SELECT 'Equb' Module,COUNT(*) Members,ROUND(AVG(regular_contribution),2) Average_Planned_Contribution,ROUND(AVG(trust_score),3) Average_Trust FROM members WHERE module='Equb' AND status='Active'",
    "Member Contribution Plans":"SELECT m.member_no Member_No,m.full_name Member,b.code Branch,m.contribution_frequency Frequency,m.regular_contribution Planned_Contribution,m.target_round_contribution Round_Target,COALESCE(SUM(c.amount),0) Total_Paid FROM members m LEFT JOIN branches b ON m.branch_id=b.id LEFT JOIN contributions c ON m.id=c.member_id AND c.module='Equb' WHERE m.module='Equb' GROUP BY m.id ORDER BY m.full_name",
    "Equb Contributions":"SELECT c.contribution_date Date,m.member_no Member_No,m.full_name Member,b.code Branch,r.round_no Round,r.contribution_amount Planned,c.amount Actual_Paid,c.status Status,c.reference Reference,c.payment_method Payment_Method FROM contributions c JOIN members m ON c.member_id=m.id LEFT JOIN equb_rounds r ON c.round_id=r.id LEFT JOIN branches b ON m.branch_id=b.id WHERE c.module='Equb' ORDER BY c.id DESC",
    "Equb Rounds":"SELECT r.round_no Round,b.code Branch,r.contribution_amount Contribution,r.expected_members Expected_Members,r.total_pool Pool,r.start_date Start_Date,r.draw_date Draw_Date,r.status Status FROM equb_rounds r JOIN branches b ON r.branch_id=b.id ORDER BY r.id DESC",
    "Transactions":"SELECT transaction_date Date,transaction_type Type,amount Amount,reference Reference,description Description FROM transactions WHERE module='Equb' ORDER BY id DESC"} 
    x=probability() if r=="Equb Probability" else df(q[r]);st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_report.csv")

def manuals():
    header("Module 8: Manuals","Equb operating guidance.")
    for title,text in [
        ("Equb Operating Manual","Register members, assign branches, configure contributions, create rounds, record payments, reconcile pools and retain transaction history."),
        ("Statistical Selection Model","The prototype combines normalized planned contribution, normalized historical paid contribution and payment consistency, followed by a fixed trust adjustment and normalized selection probability. Monte Carlo simulation demonstrates the resulting probability distribution."),
        ("Financial and Audit Controls","Use unique references, reconcile collections and pools, maintain transaction records, apply role-based access, document corrections and review the audit trail regularly.")]:
        st.markdown(f'<div class="manual-card"><h2>{title}</h2><p>{text}</p></div>',unsafe_allow_html=True)

def audit_page():
    header("Module 9: Audit Trail","Traceable record of important Equb system activities.")
    x=df("SELECT timestamp Timestamp,username Username,module Module,action Action,details Details FROM audit_log ORDER BY id DESC LIMIT 2000");st.dataframe(x,use_container_width=True,hide_index=True);download(x,"equb_audit.csv")

def users_page():
    header("Module 10: User Administration","Role-based Equb management accounts.")
    x=df("SELECT username Username,full_name Full_Name,role Role,module Module,active Active,created_at Created_At FROM users ORDER BY username");st.dataframe(x,use_container_width=True,hide_index=True)
    bl=branches();opts=[f"{z['code']} | {z['name']}" for z in bl]
    with st.form("uf"):
        a,b=st.columns(2);u=a.text_input("Username");n=b.text_input("Full Name");p=a.text_input("Password",type="password");role=b.selectbox("Role",ROLES);mod=a.selectbox("Module",["Portal","Equb"]);bo=b.selectbox("Branch",["No branch"]+opts);ok=st.form_submit_button("Create User",type="primary",use_container_width=True)
    if ok:
        bid=bl[opts.index(bo)]["id"] if bo!="No branch" else None
        try:sql("INSERT INTO users(username,password_hash,full_name,role,module,branch_id,active,created_at) VALUES(?,?,?,?,?,?,?,?)",(u,pwd_hash(p),n,role,mod,bid,1,now()));audit("Created user","Portal",u);st.success("User created.");st.rerun()
        except sqlite3.IntegrityError:st.error("Username already exists.")

def main():
    init_db()
    if not st.session_state.get("authenticated"):login();return
    with st.sidebar:
        st.markdown("## Equb")
        st.caption("Equb App Management System")
        st.write(f"User: **{st.session_state.get('full_name','')}**")
        st.write(f"Role: **{st.session_state.get('role','')}**")
        if st.button("Sign out",use_container_width=True):audit("Logout");st.session_state.clear();st.rerun()
        nav=["Dashboard","Branch Management","Member Management","Equb","Transactions","Reports and Analytics","Manuals","Audit Trail"]
        if st.session_state.get("role")=="Administrator":nav.append("User Administration")
        page=st.radio("Navigation",nav)
    {"Dashboard":dashboard,"Branch Management":branch_page,"Member Management":member_page,"Equb":equb,"Transactions":transactions,"Reports and Analytics":reports,"Manuals":manuals,"Audit Trail":audit_page,"User Administration":users_page}[page]()

if __name__=="__main__":main()
