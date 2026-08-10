import streamlit as st
import sqlite3, hashlib, secrets, hmac, random
from datetime import datetime, date
from pathlib import Path
import pandas as pd

# ============================================================
# IDFS WEB PLATFORM - SINGLE FILE DEMONSTRATION
# Indigenous Digital Financial System
# Modules: Portal, Branches, Members, Equb, Iddir,
# Transactions, Reports, Audit, User Administration
# ============================================================

st.set_page_config(page_title="IDFS Web Platform", page_icon="IDFS", layout="wide")
DB = Path("idfs_demo.db")
MODULES = ["Equb", "Iddir"]
ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]
EVENT_TYPES = ["Funeral", "Wedding", "Holiday", "Emergency", "Medical Support", "Family Support", "Other"]
PROPERTY_TYPES = ["Land", "Building", "Vehicle", "Equipment", "Furniture", "Office Asset", "Other"]

st.markdown("""
<style>
.block-container{padding-top:1.1rem;padding-bottom:2rem}
.idfs-header{padding:22px 26px;border-radius:14px;background:linear-gradient(135deg,#0B5CAD,#243447);color:white;margin-bottom:20px;box-shadow:0 8px 24px rgba(20,50,80,.12)}
.idfs-header h1{margin:0;font-size:2rem}.idfs-header p{margin:.35rem 0 0;opacity:.9}
.card{padding:18px;border:1px solid #dfe6ee;border-radius:12px;background:white;margin-bottom:14px}
.card h3{color:#0B5CAD;margin-top:0}.login-card{max-width:560px;margin:4rem auto 0;padding:30px;border:1px solid #dbe4ee;border-radius:18px;background:white;box-shadow:0 16px 40px rgba(25,55,85,.12)}
.brand{font-size:2.7rem;font-weight:800;color:#0B5CAD}.muted{color:#64748b}.small{font-size:.88rem;color:#64748b}
</style>
""", unsafe_allow_html=True)

# ============================================================
# MODULE 1: DATABASE AND CONFIGURATION
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def money(x):
    return f"ETB {float(x or 0):,.2f}"

def conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def sql(q, p=(), fetch=False, many=False):
    c = conn(); cur = c.cursor()
    try:
        if many:
            cur.executemany(q, p)
        else:
            cur.execute(q, p)
        rows = cur.fetchall() if fetch else None
        c.commit()
        return rows
    finally:
        c.close()

def df(q, p=()):
    return pd.DataFrame([dict(x) for x in sql(q, p, fetch=True)])

def pwd_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return salt + "$" + h

def check_pwd(password, stored):
    try:
        salt, h = stored.split("$", 1)
        x = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return hmac.compare_digest(x, h)
    except Exception:
        return False

def audit(action, module="Portal", details=""):
    sql("INSERT INTO audit_log(username,module,action,details,timestamp) VALUES(?,?,?,?,?)",
        (st.session_state.get("username", "anonymous"), module, action, details, now()))

def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        module TEXT NOT NULL,
        branch_id INTEGER,
        active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS branches(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        module TEXT NOT NULL,
        location TEXT,
        manager TEXT,
        phone TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_no TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        sex TEXT,
        join_date TEXT,
        module TEXT NOT NULL,
        branch_id INTEGER,
        regular_contribution REAL DEFAULT 0,
        trust_score REAL DEFAULT .5,
        status TEXT DEFAULT 'Active',
        address TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS equb_rounds(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        round_no INTEGER,
        contribution_amount REAL,
        start_date TEXT,
        draw_date TEXT,
        expected_members INTEGER,
        total_pool REAL DEFAULT 0,
        winner_member_id INTEGER,
        status TEXT DEFAULT 'Open',
        created_at TEXT NOT NULL,
        UNIQUE(branch_id,round_no)
    );
    CREATE TABLE IF NOT EXISTS contributions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        module TEXT,
        round_id INTEGER,
        amount REAL,
        contribution_date TEXT,
        status TEXT DEFAULT 'Paid',
        reference TEXT,
        payment_method TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(member_id,round_id)
    );
    CREATE TABLE IF NOT EXISTS iddir_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        event_type TEXT,
        member_id INTEGER,
        event_date TEXT,
        description TEXT,
        requested_amount REAL DEFAULT 0,
        approved_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        payment_date TEXT,
        reference TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS properties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        property_code TEXT UNIQUE,
        property_type TEXT,
        description TEXT,
        location TEXT,
        acquisition_date TEXT,
        acquisition_cost REAL DEFAULT 0,
        current_value REAL DEFAULT 0,
        status TEXT DEFAULT 'Active',
        custodian TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module TEXT,
        branch_id INTEGER,
        member_id INTEGER,
        transaction_type TEXT,
        amount REAL,
        reference TEXT,
        transaction_date TEXT,
        description TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        module TEXT,
        action TEXT,
        details TEXT,
        timestamp TEXT
    );
    """)
    c.commit(); c.close()

    # -----------------------------------------------------------------
    # DATABASE COMPATIBILITY / MIGRATION
    # -----------------------------------------------------------------
    # Supports both a fresh database and databases created by earlier
    # versions of the IDFS prototype.
    def ensure_column(table, column, definition):
        cols = [r["name"] for r in sql(f"PRAGMA table_info({table})", fetch=True)]
        if column not in cols:
            sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    ensure_column("branches", "phone", "TEXT")
    ensure_column("branches", "status", "TEXT DEFAULT 'Active'")
    ensure_column("users", "branch_id", "INTEGER")
    ensure_column("users", "active", "INTEGER DEFAULT 1")

    # -----------------------------------------------------------------
    # DEFAULT ADMINISTRATOR
    # -----------------------------------------------------------------
    # username is UNIQUE; INSERT OR IGNORE prevents duplicate-key errors.
    sql(
        """INSERT OR IGNORE INTO users
           (username,password_hash,full_name,role,module,created_at)
           VALUES(?,?,?,?,?,?)""",
        (
            "admin",
            pwd_hash("admin123"),
            "IDFS Administrator",
            "Administrator",
            "Portal",
            now()
        )
    )

    # -----------------------------------------------------------------
    # DEFAULT EQUb AND IDDIR BRANCHES
    # -----------------------------------------------------------------
    # These six columns are compatible with the original prototype schema.
    seed = [
        ("EQB-001", "IDFS Equb Central Branch", "Equb", "Aksum", "Branch Manager"),
        ("EQB-002", "IDFS Equb North Branch", "Equb", "Shire", "Branch Manager"),
        ("IDR-001", "IDFS Iddir Central Branch", "Iddir", "Aksum", "Branch Manager"),
        ("IDR-002", "IDFS Iddir Community Branch", "Iddir", "Shire", "Branch Manager"),
    ]

    for code, name, module, location, manager in seed:
        sql(
            """INSERT OR IGNORE INTO branches
               (code,name,module,location,manager,created_at)
               VALUES(?,?,?,?,?,?)""",
            (code, name, module, location, manager, now())
        )

    for code, *_ in seed:
        sql(
            """UPDATE branches
               SET phone=COALESCE(phone,''),
                   status=COALESCE(status,'Active')
               WHERE code=?""",
            (code,)
        )


def header(title, subtitle=""):
    st.markdown(f'<div class="idfs-header"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def branches(module=None):
    if module:
        return sql("SELECT * FROM branches WHERE module=? ORDER BY name", (module,), True)
    return sql("SELECT * FROM branches ORDER BY module,name", fetch=True)

def members(module=None, branch=None):
    where=[]; p=[]
    if module: where.append("m.module=?"); p.append(module)
    if branch: where.append("m.branch_id=?"); p.append(branch)
    w=(" WHERE " + " AND ".join(where)) if where else ""
    return sql("SELECT m.*,b.code branch_code,b.name branch_name FROM members m LEFT JOIN branches b ON m.branch_id=b.id"+w+" ORDER BY m.full_name", tuple(p), True)

def active_member_options(module):
    ms = members(module)
    return {f"{m['member_no']} | {m['full_name']}": m for m in ms if m['status']=='Active'}

def download(data, filename):
    st.download_button("Download CSV", data.to_csv(index=False).encode("utf-8"), filename, "text/csv", use_container_width=True)

# ============================================================
# MODULE 2: AUTHENTICATION
# ============================================================

def login():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="brand">IDFS</div>', unsafe_allow_html=True)
    st.markdown("### Indigenous Digital Financial System")
    st.markdown('<p class="muted">Secure demonstration platform for Equb savings and Iddir community risk sharing.</p>', unsafe_allow_html=True)
    st.divider()
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        row = sql("SELECT * FROM users WHERE username=? AND active=1", (username.strip(),), True)
        if row and check_pwd(password, row[0]["password_hash"]):
            u=row[0]
            st.session_state.update(authenticated=True,user_id=u["id"],username=u["username"],full_name=u["full_name"],role=u["role"],module=u["module"],branch_id=u["branch_id"])
            audit("Successful login")
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.info("Demonstration account: admin / admin123")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# MODULE 3: DASHBOARD
# ============================================================

def dashboard():
    header("IDFS Executive Dashboard", "Integrated Equb saving and Iddir community risk-sharing platform")
    m=sql("SELECT COUNT(*) n FROM members WHERE status='Active'",fetch=True)[0]["n"]
    b=sql("SELECT COUNT(*) n FROM branches WHERE status='Active'",fetch=True)[0]["n"]
    c=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"]
    p=sql("SELECT COALESCE(SUM(current_value),0) n FROM properties WHERE status='Active'",fetch=True)[0]["n"]
    a,bx,cx,d=st.columns(4)
    a.metric("Active Members",m); bx.metric("Active Branches",b); cx.metric("Equb Savings",money(c)); d.metric("Iddir Property",money(p))
    st.divider()
    x,y=st.columns(2)
    x.markdown('<div class="card"><h3>IDFS Equb</h3><p>Community savings, regular contributions, rounds, payment records and contribution-weighted probability demonstration.</p></div>',unsafe_allow_html=True)
    y.markdown('<div class="card"><h3>IDFS Iddir</h3><p>Community risk sharing for funeral, wedding, holiday, emergency, medical and other approved support, together with property management.</p></div>',unsafe_allow_html=True)
    st.subheader("Recent Activity")
    st.dataframe(df("SELECT timestamp Timestamp,username User,module Module,action Action,details Details FROM audit_log ORDER BY id DESC LIMIT 15"),use_container_width=True,hide_index=True)

# ============================================================
# MODULE 4: BRANCH MANAGEMENT
# ============================================================

def branch_page():
    header("Module 4: Branch Management", "Bank-style branch structure for Equb and Iddir")
    t1,t2=st.tabs(["Branch Directory","Register Branch"])
    with t1:
        x=df("SELECT code Branch_Code,name Branch_Name,module Module,location Location,manager Manager,phone Phone,status Status FROM branches ORDER BY module,name")
        st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_branches.csv")
    with t2:
        with st.form("branch_form"):
            a,b=st.columns(2)
            code=a.text_input("Branch Code",placeholder="EQB-003")
            name=b.text_input("Branch Name")
            mod=a.selectbox("Module",MODULES)
            loc=b.text_input("Location")
            mgr=a.text_input("Manager")
            phone=b.text_input("Phone")
            status=b.selectbox("Status",["Active","Inactive"])
            ok=st.form_submit_button("Register Branch",type="primary")
        if ok:
            if not code.strip() or not name.strip(): st.error("Branch code and name are required."); return
            try:
                sql("INSERT INTO branches(code,name,module,location,manager,phone,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(code.strip(),name.strip(),mod,loc.strip(),mgr.strip(),phone.strip(),status,now()))
                audit("Created branch",mod,code); st.success("Branch registered."); st.rerun()
            except sqlite3.IntegrityError: st.error("Branch code already exists.")

# ============================================================
# MODULE 5: MEMBER MANAGEMENT
# ============================================================

def member_page():
    header("Module 5: Member Management", "Registration, regular contribution and membership monitoring")
    t1,t2,t3=st.tabs(["Directory","Register Member","Member Profile"])
    with t1:
        f=st.selectbox("Module Filter",["All"]+MODULES)
        if f=="All": x=df("SELECT m.member_no Member_No,m.full_name Full_Name,m.module Module,b.name Branch,m.phone Phone,m.join_date Join_Date,m.regular_contribution Regular_Contribution,m.trust_score Trust_Score,m.status Status FROM members m LEFT JOIN branches b ON m.branch_id=b.id ORDER BY m.module,m.full_name")
        else: x=df("SELECT m.member_no Member_No,m.full_name Full_Name,m.module Module,b.name Branch,m.phone Phone,m.join_date Join_Date,m.regular_contribution Regular_Contribution,m.trust_score Trust_Score,m.status Status FROM members m LEFT JOIN branches b ON m.branch_id=b.id WHERE m.module=? ORDER BY m.full_name",(f,))
        st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_members.csv")
    with t2:
        with st.form("member_form"):
            a,b=st.columns(2)
            no=a.text_input("Member Number",placeholder="M-0001")
            name=b.text_input("Full Name")
            phone=a.text_input("Phone")
            sex=b.selectbox("Sex",["Not specified","Female","Male","Other"])
            mod=a.selectbox("Module",MODULES)
            bs=branches(mod); opts=[f"{x['code']} | {x['name']}" for x in bs]
            branch=b.selectbox("Branch",opts) if opts else None
            contribution=a.number_input("Regular Contribution / Monthly Amount (ETB)",min_value=0.0,value=0.0,step=50.0)
            trust=b.slider("Initial Trust Score",0.0,1.0,0.5,0.01)
            join=a.date_input("Join Date",date.today())
            status=b.selectbox("Status",["Active","Inactive","Suspended"])
            address=a.text_input("Address")
            notes=b.text_area("Notes")
            ok=st.form_submit_button("Register Member",type="primary",use_container_width=True)
        if ok:
            if not no.strip() or not name.strip(): st.error("Member number and full name are required."); return
            bid=bs[opts.index(branch)]["id"] if opts and branch else None
            try:
                sql("""INSERT INTO members(member_no,full_name,phone,sex,join_date,module,branch_id,regular_contribution,trust_score,status,address,notes,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(no.strip(),name.strip(),phone,sex,str(join),mod,bid,contribution,trust,status,address,notes,now()))
                audit("Registered member",mod,no); st.success("Member registered."); st.rerun()
            except sqlite3.IntegrityError: st.error("Member number already exists.")
    with t3:
        ms=members()
        if not ms: st.info("No members registered yet."); return
        labels=[f"{x['member_no']} | {x['full_name']}" for x in ms]
        pick=st.selectbox("Select Member",labels); m=ms[labels.index(pick)]
        a,b,c=st.columns(3); a.metric("Module",m["module"]); b.metric("Regular Contribution",money(m["regular_contribution"])); c.metric("Trust Score",f"{float(m['trust_score']):.2f}")
        st.write({"Member Number":m["member_no"],"Full Name":m["full_name"],"Branch":m["branch_name"],"Phone":m["phone"],"Join Date":m["join_date"],"Status":m["status"]})

# ============================================================
# MODULE 6: EQUb SAVINGS AND ROUNDS
# ============================================================

def equb():
    header("Module 6: IDFS Equb", "Digital rotating savings, contributions, rounds and transparent selection")
    tabs=st.tabs(["Overview","Rounds","Contributions","Weighted Probability","Draw History"])
    with tabs[0]: equb_overview()
    with tabs[1]: equb_rounds()
    with tabs[2]: equb_contributions()
    with tabs[3]: equb_probability()
    with tabs[4]: equb_history()

def equb_overview():
    n=sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND status='Active'",fetch=True)[0]["n"]
    s=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",fetch=True)[0]["n"]
    r=sql("SELECT COUNT(*) n FROM equb_rounds",fetch=True)[0]["n"]
    p=sql("SELECT COALESCE(SUM(total_pool),0) n FROM equb_rounds",fetch=True)[0]["n"]
    a,b,c,d=st.columns(4); a.metric("Active Members",n); b.metric("Total Contributions",money(s)); c.metric("Rounds",r); d.metric("Recorded Pools",money(p))
    st.markdown('<div class="card"><h3>Equb operating model</h3><p>Each Equb group or branch can define a regular contribution. Members make payments for rounds. The platform records the round pool and demonstrates a contribution-weighted selection model. Production governance can later add formal eligibility, independent randomization, approvals and reconciliation.</p></div>',unsafe_allow_html=True)

def equb_rounds():
    st.subheader("Equb Round Management")
    bs=branches("Equb")
    if not bs: st.warning("Create an Equb branch first."); return
    names=[f"{x['code']} | {x['name']}" for x in bs]
    with st.form("round_form"):
        bc=st.selectbox("Equb Branch",names)
        a,b=st.columns(2)
        round_no=a.number_input("Round Number",min_value=1,value=1,step=1)
        amount=b.number_input("Contribution per Member (ETB)",min_value=0.0,value=1000.0,step=100.0)
        expected=a.number_input("Expected Members",min_value=1,value=10,step=1)
        start=b.date_input("Start Date",date.today())
        draw=a.date_input("Expected Draw Date",date.today())
        status=b.selectbox("Status",["Open","Closed","Completed","Cancelled"])
        ok=st.form_submit_button("Create Round",type="primary")
    if ok:
        branch=bs[names.index(bc)]
        try:
            sql("INSERT INTO equb_rounds(branch_id,round_no,contribution_amount,start_date,draw_date,expected_members,total_pool,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(branch["id"],round_no,amount,str(start),str(draw),expected,0,status,now()))
            audit("Created Equb round","Equb",f"{branch['code']} round {round_no}"); st.success("Round created."); st.rerun()
        except sqlite3.IntegrityError: st.error("That round already exists for this branch.")
    x=df("SELECT r.round_no Round_No,b.code Branch,r.contribution_amount Contribution,r.expected_members Expected_Members,r.total_pool Total_Pool,r.start_date Start_Date,r.draw_date Draw_Date,r.status Status,COALESCE(m.full_name,'') Winner FROM equb_rounds r JOIN branches b ON r.branch_id=b.id LEFT JOIN members m ON r.winner_member_id=m.id ORDER BY r.id DESC")
    st.dataframe(x,use_container_width=True,hide_index=True)

def equb_contributions():
    st.subheader("Equb Contribution Recording")
    rounds=sql("SELECT r.*,b.code branch_code FROM equb_rounds r JOIN branches b ON r.branch_id=b.id WHERE r.status IN ('Open','Closed') ORDER BY r.id DESC",fetch=True)
    if not rounds: st.info("Create an open Equb round first."); return
    labels=[f"{r['branch_code']} | Round {r['round_no']} | {money(r['contribution_amount'])}" for r in rounds]
    with st.form("contribution_form"):
        rr=st.selectbox("Round",labels); r=rounds[labels.index(rr)]
        ms=members("Equb",r["branch_id"])
        if not ms:
            st.warning("No Equb members are registered in this branch.")
            st.form_submit_button("Record Contribution",disabled=True)
            return
        ml=[f"{m['member_no']} | {m['full_name']}" for m in ms]
        mc=st.selectbox("Member",ml)
        amount=st.number_input("Amount (ETB)",min_value=0.0,value=float(r["contribution_amount"] or 0),step=50.0)
        cd=st.date_input("Contribution Date",date.today())
        method=st.selectbox("Payment Method",["Cash","Bank Transfer","Mobile Money","Other"])
        ref=st.text_input("Payment Reference")
        notes=st.text_area("Notes")
        ok=st.form_submit_button("Record Contribution",type="primary")
    if ok:
        m=ms[ml.index(mc)]
        try:
            sql("INSERT INTO contributions(member_id,module,round_id,amount,contribution_date,status,reference,payment_method,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(m["id"],"Equb",r["id"],amount,str(cd),"Paid",ref,method,notes,now()))
            total=sql("SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE round_id=? AND status='Paid'",(r["id"],),True)[0]["n"]
            sql("UPDATE equb_rounds SET total_pool=? WHERE id=?",(total,r["id"]))
            audit("Recorded Equb contribution","Equb",f"{m['member_no']} {amount}"); st.success("Contribution recorded."); st.rerun()
        except sqlite3.IntegrityError: st.error("This member already has a contribution for this round.")
    x=df("""SELECT c.contribution_date Date,m.member_no Member_No,m.full_name Member,
              b.code Branch,r.round_no Round,c.amount Amount,c.status Status,c.reference Reference,c.payment_method Payment_Method
              FROM contributions c JOIN members m ON c.member_id=m.id JOIN equb_rounds r ON c.round_id=r.id JOIN branches b ON r.branch_id=b.id
              WHERE c.module='Equb' ORDER BY c.id DESC LIMIT 500""")
    st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_equb_contributions.csv")

def probability_table():
    ms=members("Equb")
    if not ms: return pd.DataFrame()
    values=[max(float(m["regular_contribution"] or 0),0) for m in ms]
    if sum(values)<=0: probs=[1/len(ms)]*len(ms)
    else: probs=[v/sum(values) for v in values]
    return pd.DataFrame([{"Member_No":m["member_no"],"Member":m["full_name"],"Regular_Contribution":values[i],"Trust_Score":float(m["trust_score"] or .5),"Probability":probs[i]} for i,m in enumerate(ms)])

def equb_probability():
    st.subheader("Contribution-Weighted Probability Engine")
    x=probability_table()
    if x.empty: st.info("Register Equb members first."); return
    if x.Regular_Contribution.sum()<=0: st.warning("All regular contributions are zero; equal probabilities are used.")
    st.dataframe(x.style.format({"Regular_Contribution":"{:,.2f}","Trust_Score":"{:.2f}","Probability":"{:.2%}"}),use_container_width=True,hide_index=True)
    a,b=st.columns(2); a.metric("Total Regular Contribution",money(x.Regular_Contribution.sum())); b.metric("Members",len(x))
    if st.button("Run Weighted Demonstration",type="primary",use_container_width=True):
        ms=members("Equb"); weights=x.Probability.tolist(); w=random.choices(ms,weights=weights,k=1)[0]
        st.success(f"Selected demonstration member: {w['full_name']} ({w['member_no']})")
        audit("Executed weighted probability demonstration","Equb",w["member_no"])
    st.markdown('<div class="card"><h3>Model note</h3><p>For member i, the demonstration probability is proportional to positive regular contribution C_i: p_i = C_i / sum(C_j). If all contributions are zero, equal probabilities are assigned. This is a research prototype, not a claim that this rule must govern every Equb.</p></div>',unsafe_allow_html=True)

def equb_history():
    x=df("""SELECT r.round_no Round_No,b.code Branch,r.total_pool Pool,r.draw_date Draw_Date,
             COALESCE(m.member_no,'') Winner_No,COALESCE(m.full_name,'') Winner,r.status Status
             FROM equb_rounds r JOIN branches b ON r.branch_id=b.id LEFT JOIN members m ON r.winner_member_id=m.id
             ORDER BY r.id DESC""")
    st.dataframe(x,use_container_width=True,hide_index=True)
    if not x.empty: download(x,"idfs_equb_rounds.csv")

# ============================================================
# MODULE 7: IDDIR RISK SHARING AND PROPERTY
# ============================================================

def iddir():
    header("Module 7: IDFS Iddir", "Community risk sharing for funeral, wedding, holiday, emergency and other approved needs")
    t=st.tabs(["Overview","Community Events","Property Management","Transactions","Member History"])
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
    st.markdown('<div class="card"><h3>Iddir operating scope</h3><p>The platform records community support cases for funeral, wedding, holiday, emergency, medical, family and other approved purposes. It also maintains community and operational property such as land, buildings, vehicles, equipment and furniture.</p></div>',unsafe_allow_html=True)

def iddir_events():
    st.subheader("Community Event and Benefit Management")
    ms=members("Iddir")
    if not ms: st.info("Register Iddir members first."); return
    labels=[f"{m['member_no']} | {m['full_name']}" for m in ms]
    with st.form("iddir_event"):
        mc=st.selectbox("Member / Beneficiary",labels)
        typ=st.selectbox("Event Type",EVENT_TYPES)
        ed=st.date_input("Event Date",date.today())
        requested=st.number_input("Requested Amount (ETB)",min_value=0.0,value=0.0,step=100.0)
        approved=st.number_input("Approved Amount (ETB)",min_value=0.0,value=0.0,step=100.0)
        status=st.selectbox("Status",["Pending","Approved","Rejected","Paid"])
        ref=st.text_input("Case / Payment Reference")
        desc=st.text_area("Description")
        ok=st.form_submit_button("Record Community Support Case",type="primary")
    if ok:
        m=ms[labels.index(mc)]; paid=str(date.today()) if status=="Paid" else None
        sql("INSERT INTO iddir_events(branch_id,event_type,member_id,event_date,description,requested_amount,approved_amount,status,payment_date,reference,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(m["branch_id"],typ,m["id"],str(ed),desc,requested,approved,status,paid,ref,now()))
        if status=="Paid" and approved>0:
            sql("INSERT INTO transactions(module,branch_id,member_id,transaction_type,amount,reference,transaction_date,description,created_at) VALUES(?,?,?,?,?,?,?,?,?)",("Iddir",m["branch_id"],m["id"],"Community Benefit Payment",approved,ref,str(ed),typ+" support",now()))
        audit("Recorded Iddir support case","Iddir",f"{typ} for {m['member_no']}"); st.success("Support case recorded."); st.rerun()
    x=df("""SELECT e.event_date Event_Date,e.event_type Event_Type,m.member_no Member_No,m.full_name Member,
             e.requested_amount Requested,e.approved_amount Approved,e.status Status,e.reference Reference,e.description Description
             FROM iddir_events e JOIN members m ON e.member_id=m.id ORDER BY e.id DESC""")
    st.dataframe(x,use_container_width=True,hide_index=True)

def iddir_properties():
    st.subheader("Iddir Property Management")
    bs=branches("Iddir")
    if not bs: st.warning("Create an Iddir branch first."); return
    names=[f"{b['code']} | {b['name']}" for b in bs]
    with st.form("property_form"):
        bc=st.selectbox("Iddir Branch",names)
        a,b=st.columns(2)
        code=a.text_input("Property Code",placeholder="PROP-001")
        typ=b.selectbox("Property Type",PROPERTY_TYPES)
        desc=a.text_input("Description")
        loc=b.text_input("Location")
        ad=a.date_input("Acquisition Date",date.today())
        cost=b.number_input("Acquisition Cost (ETB)",min_value=0.0,value=0.0,step=1000.0)
        value=a.number_input("Current Estimated Value (ETB)",min_value=0.0,value=0.0,step=1000.0)
        status=b.selectbox("Status",["Active","Under Maintenance","Disposed","Transferred"])
        cust=a.text_input("Custodian")
        notes=st.text_area("Notes")
        ok=st.form_submit_button("Register Property",type="primary")
    if ok:
        if not code.strip(): st.error("Property code is required."); return
        branch=bs[names.index(bc)]
        try:
            sql("INSERT INTO properties(branch_id,property_code,property_type,description,location,acquisition_date,acquisition_cost,current_value,status,custodian,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(branch["id"],code.strip(),typ,desc,loc,str(ad),cost,value,status,cust,notes,now()))
            audit("Registered Iddir property","Iddir",code); st.success("Property registered."); st.rerun()
        except sqlite3.IntegrityError: st.error("Property code already exists.")
    x=df("SELECT p.property_code Property_Code,p.property_type Property_Type,p.description Description,b.name Branch,p.location Location,p.acquisition_date Acquisition_Date,p.acquisition_cost Acquisition_Cost,p.current_value Current_Value,p.status Status,p.custodian Custodian FROM properties p LEFT JOIN branches b ON p.branch_id=b.id ORDER BY p.id DESC")
    st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_iddir_properties.csv")

def iddir_transaction_view():
    x=df("SELECT transaction_date Date,transaction_type Type,amount Amount,reference Reference,description Description FROM transactions WHERE module='Iddir' ORDER BY id DESC")
    st.dataframe(x,use_container_width=True,hide_index=True)

def iddir_history():
    x=df("""SELECT e.event_date Date,e.event_type Event,m.member_no Member_No,m.full_name Member,e.requested_amount Requested,
             e.approved_amount Approved,e.status Status,e.reference Reference FROM iddir_events e JOIN members m ON e.member_id=m.id ORDER BY e.id DESC""")
    st.dataframe(x,use_container_width=True,hide_index=True)

# ============================================================
# MODULE 8: TRANSACTIONS
# ============================================================

def transactions():
    header("Module 8: Transactions", "Unified financial transaction register for the prototype")
    with st.form("transaction_form"):
        a,b=st.columns(2)
        module=a.selectbox("Module",MODULES)
        typ=b.selectbox("Transaction Type",["Deposit","Contribution","Community Benefit Payment","Adjustment","Other"])
        amount=a.number_input("Amount (ETB)",min_value=0.0,value=0.0,step=100.0)
        reference=b.text_input("Reference")
        td=a.date_input("Transaction Date",date.today())
        desc=b.text_area("Description")
        ok=st.form_submit_button("Record Transaction",type="primary")
    if ok:
        sql("INSERT INTO transactions(module,transaction_type,amount,reference,transaction_date,description,created_at) VALUES(?,?,?,?,?,?,?)",(module,typ,amount,reference,str(td),desc,now()))
        audit("Recorded transaction",module,f"{typ}: {amount}"); st.success("Transaction recorded."); st.rerun()
    x=df("SELECT transaction_date Date,module Module,transaction_type Type,amount Amount,reference Reference,description Description FROM transactions ORDER BY id DESC LIMIT 1000")
    st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_transactions.csv")

# ============================================================
# MODULE 9: REPORTS AND ANALYTICS
# ============================================================

def reports():
    header("Module 9: Reports and Analytics", "Management information for the IDFS technology-transfer prototype")
    typ=st.selectbox("Report",["Module Summary","Equb Contributions","Equb Rounds","Equb Probability","Iddir Community Support","Iddir Properties","Transactions"])
    if typ=="Module Summary": q="SELECT module Module,COUNT(*) Members,ROUND(AVG(regular_contribution),2) Average_Regular_Contribution,ROUND(AVG(trust_score),3) Average_Trust FROM members WHERE status='Active' GROUP BY module"
    elif typ=="Equb Contributions": q="SELECT m.member_no Member_No,m.full_name Member,COUNT(c.id) Payments,COALESCE(SUM(c.amount),0) Total_Paid FROM members m LEFT JOIN contributions c ON m.id=c.member_id AND c.module='Equb' AND c.status='Paid' WHERE m.module='Equb' GROUP BY m.id ORDER BY Total_Paid DESC"
    elif typ=="Equb Rounds": q="SELECT r.round_no Round_No,b.code Branch,r.contribution_amount Contribution,r.expected_members Members,r.total_pool Total_Pool,r.start_date Start_Date,r.draw_date Draw_Date,r.status Status,COALESCE(m.full_name,'') Winner FROM equb_rounds r JOIN branches b ON r.branch_id=b.id LEFT JOIN members m ON r.winner_member_id=m.id ORDER BY r.id DESC"
    elif typ=="Equb Probability":
        x=probability_table(); st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_equb_probability.csv"); return
    elif typ=="Iddir Community Support": q="SELECT event_type Event_Type,COUNT(*) Cases,COALESCE(SUM(requested_amount),0) Requested,COALESCE(SUM(approved_amount),0) Approved FROM iddir_events GROUP BY event_type ORDER BY Approved DESC"
    elif typ=="Iddir Properties": q="SELECT property_type Property_Type,COUNT(*) Assets,COALESCE(SUM(acquisition_cost),0) Acquisition_Cost,COALESCE(SUM(current_value),0) Current_Value FROM properties GROUP BY property_type ORDER BY Current_Value DESC"
    else: q="SELECT module Module,transaction_type Transaction_Type,COUNT(*) Transactions,COALESCE(SUM(amount),0) Total_Amount FROM transactions GROUP BY module,transaction_type ORDER BY module,Total_Amount DESC"
    x=df(q); st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_report.csv")

# ============================================================
# MODULE 10: AUDIT TRAIL
# ============================================================

def audit_page():
    header("Module 10: Audit Trail", "Traceable record of important system activities")
    x=df("SELECT timestamp Timestamp,username Username,module Module,action Action,details Details FROM audit_log ORDER BY id DESC LIMIT 2000")
    st.dataframe(x,use_container_width=True,hide_index=True); download(x,"idfs_audit.csv")

# ============================================================
# MODULE 11: USER ADMINISTRATION
# ============================================================

def users_page():
    header("Module 11: User Administration", "Role-based demonstration accounts")
    x=df("SELECT username Username,full_name Full_Name,role Role,module Module,active Active,created_at Created_At FROM users ORDER BY username")
    st.dataframe(x,use_container_width=True,hide_index=True)
    with st.form("user_form"):
        a,b=st.columns(2)
        u=a.text_input("Username")
        n=b.text_input("Full Name")
        p=a.text_input("Password",type="password")
        r=b.selectbox("Role",ROLES)
        m=a.selectbox("Module",["Portal"]+MODULES)
        bs=branches(m if m in MODULES else None)
        bo=["No branch"]+[f"{x['code']} | {x['name']}" for x in bs]
        bc=b.selectbox("Branch",bo)
        ok=st.form_submit_button("Create User",type="primary")
    if ok:
        if len(p)<6: st.error("Password must contain at least six characters."); return
        bid=None if bc=="No branch" else bs[bo.index(bc)-1]["id"]
        try:
            sql("INSERT INTO users(username,password_hash,full_name,role,module,branch_id,created_at) VALUES(?,?,?,?,?,?,?)",(u.strip(),pwd_hash(p),n.strip(),r,m,bid,now()))
            audit("Created user","Portal",u); st.success("User created."); st.rerun()
        except sqlite3.IntegrityError: st.error("Username already exists.")

# ============================================================
# MAIN
# ============================================================

def main():
    init_db()
    if not st.session_state.get("authenticated",False):
        login(); return
    with st.sidebar:
        st.markdown("## IDFS")
        st.caption("Indigenous Digital Financial System")
        st.write(f"User: **{st.session_state.get('full_name','')}**")
        st.write(f"Role: **{st.session_state.get('role','')}**")
        if st.button("Sign out",use_container_width=True):
            audit("Logout"); st.session_state.clear(); st.rerun()
        st.divider()
        nav=["Dashboard","Branch Management","Member Management","IDFS Equb","IDFS Iddir","Transactions","Reports and Analytics","Audit Trail"]
        if st.session_state.get("role")=="Administrator": nav.append("User Administration")
        page=st.radio("Navigation",nav)
    pages={"Dashboard":dashboard,"Branch Management":branch_page,"Member Management":member_page,"IDFS Equb":equb,"IDFS Iddir":iddir,"Transactions":transactions,"Reports and Analytics":reports,"Audit Trail":audit_page,"User Administration":users_page}
    pages[page]()

if __name__ == "__main__":
    main()
