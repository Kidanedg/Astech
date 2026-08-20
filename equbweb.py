import streamlit as st
import sqlite3
import hashlib
import secrets
import hmac
import random
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# EQUB APP MANAGEMENT SYSTEM
# Standalone Streamlit prototype
# ============================================================

st.set_page_config(
    page_title="Equb App Management System",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = Path("equb_demo.db")

ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]
FREQUENCIES = ["Monthly", "Round-based", "Weekly", "Other"]
PAYMENT_METHODS = ["Cash", "Bank Transfer", "Mobile Money", "Other"]
ROUND_STATUS = ["Open", "Closed", "Completed", "Cancelled"]
MEMBER_STATUS = ["Active", "Inactive", "Suspended"]

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
.main-title{font-size:2rem;font-weight:700;color:#163A5F;margin-bottom:.15rem}
.sub-title{font-size:.95rem;color:#64748B;margin-bottom:1.2rem}
.section-card{padding:1.1rem 1.3rem;border:1px solid #E2E8F0;border-radius:12px;background:#F8FAFC;margin-bottom:1rem}
.module-label{color:#0B5CAD;font-weight:700;font-size:.82rem;text-transform:uppercase;letter-spacing:.06em}
.manual-card{padding:1.2rem 1.4rem;border:1px solid #CBD5E1;border-radius:10px;background:white;margin-bottom:1rem}
.warning-card{padding:1rem 1.2rem;border-left:5px solid #C89B3C;background:#FFFBEB;margin-bottom:1rem}
.footer-note{text-align:center;color:#64748B;font-size:.78rem;margin-top:2rem}
</style>
""", unsafe_allow_html=True)

# ============================================================
# COMMON
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def sql(query, params=(), fetch=False):
    c = conn()
    try:
        cur = c.execute(query, params)
        if fetch:
            return [dict(x) for x in cur.fetchall()]
        c.commit()
        return cur.lastrowid
    finally:
        c.close()

def df(query, params=()):
    return pd.DataFrame(sql(query, params, fetch=True))

def money(x):
    try:
        return f"{float(x):,.2f} ETB"
    except Exception:
        return "0.00 ETB"

def download(data, filename):
    if isinstance(data, pd.DataFrame):
        payload = data.to_csv(index=False).encode("utf-8")
    else:
        payload = str(data).encode("utf-8")
    st.download_button(
        "Download CSV",
        payload,
        filename,
        "text/csv",
        use_container_width=True,
    )

def pwd_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120000
    ).hex()
    return f"{salt}${digest}"

def check_pwd(password, stored):
    try:
        salt, digest = stored.split("$", 1)
        test = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 120000
        ).hex()
        return hmac.compare_digest(test, digest)
    except Exception:
        return False

def audit(action, module="Equb", details=""):
    try:
        sql(
            """INSERT INTO audit_log
            (username,module,action,details,timestamp)
            VALUES(?,?,?,?,?)""",
            (
                st.session_state.get("username", "system"),
                module,
                action,
                details,
                now(),
            ),
        )
    except Exception:
        pass

def header(title, subtitle=""):
    st.markdown(f'<div class="main-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sub-title">{subtitle}</div>', unsafe_allow_html=True)

# ============================================================
# DATABASE
# ============================================================

def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        module TEXT DEFAULT 'Equb',
        branch_id INTEGER,
        active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS branches(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        module TEXT DEFAULT 'Equb',
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
        module TEXT DEFAULT 'Equb',
        branch_id INTEGER,
        regular_contribution REAL DEFAULT 0,
        contribution_frequency TEXT DEFAULT 'Monthly',
        target_round_contribution REAL DEFAULT 0,
        trust_score REAL DEFAULT 0.5,
        status TEXT DEFAULT 'Active',
        address TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS equb_rounds(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        round_no INTEGER,
        contribution_amount REAL DEFAULT 0,
        start_date TEXT,
        draw_date TEXT,
        expected_members INTEGER DEFAULT 0,
        total_pool REAL DEFAULT 0,
        winner_member_id INTEGER,
        status TEXT DEFAULT 'Open',
        created_at TEXT NOT NULL,
        UNIQUE(branch_id,round_no)
    );

    CREATE TABLE IF NOT EXISTS contributions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        module TEXT DEFAULT 'Equb',
        round_id INTEGER,
        amount REAL DEFAULT 0,
        contribution_date TEXT,
        status TEXT DEFAULT 'Paid',
        reference TEXT,
        payment_method TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module TEXT DEFAULT 'Equb',
        branch_id INTEGER,
        member_id INTEGER,
        transaction_type TEXT,
        amount REAL DEFAULT 0,
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
    c.commit()
    c.close()

    if not sql("SELECT id FROM users WHERE username='admin'", fetch=True):
        sql(
            """INSERT INTO users
            (username,password_hash,full_name,role,module,active,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (
                "admin",
                pwd_hash("admin123"),
                "Equb Administrator",
                "Administrator",
                "Equb",
                1,
                now(),
            ),
        )

    seed = [
        ("EQB-001", "Equb Central Branch", "Aksum"),
        ("EQB-002", "Equb North Branch", "Shire"),
    ]
    for code, name, location in seed:
        if not sql("SELECT id FROM branches WHERE code=?", (code,), fetch=True):
            sql(
                """INSERT INTO branches
                (code,name,module,location,manager,phone,status,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (code,name,"Equb",location,"Branch Manager","","Active",now()),
            )

def branches():
    return sql(
        "SELECT * FROM branches WHERE module='Equb' ORDER BY name",
        fetch=True,
    )

def members(branch_id=None):
    if branch_id:
        return sql(
            """SELECT m.*,b.code branch_code,b.name branch_name
            FROM members m LEFT JOIN branches b ON m.branch_id=b.id
            WHERE m.module='Equb' AND m.branch_id=?
            ORDER BY m.full_name""",
            (branch_id,),
            fetch=True,
        )
    return sql(
        """SELECT m.*,b.code branch_code,b.name branch_name
        FROM members m LEFT JOIN branches b ON m.branch_id=b.id
        WHERE m.module='Equb' ORDER BY m.full_name""",
        fetch=True,
    )

# ============================================================
# AUTHENTICATION
# ============================================================

def login():
    st.markdown("""
    <div style="text-align:center;margin-top:40px;margin-bottom:30px">
        <h1>Equb</h1>
        <p>Equb App Management System</p>
        <p>Secure Web Prototype</p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1,2,1])
    with center:
        st.markdown("### Sign in")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in", type="primary", use_container_width=True
            )
        if submitted:
            row = sql(
                "SELECT * FROM users WHERE username=? AND active=1",
                (username.strip(),),
                fetch=True,
            )
            if row and check_pwd(password, row[0]["password_hash"]):
                u = row[0]
                st.session_state.update(
                    authenticated=True,
                    user_id=u["id"],
                    username=u["username"],
                    full_name=u["full_name"],
                    role=u["role"],
                    branch_id=u["branch_id"],
                )
                audit("Successful login")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.info("Demonstration account: admin / admin123")

# ============================================================
# STATISTICAL ENGINE
# ============================================================

def member_history(member_id, round_id=None):
    clauses = ["c.member_id=?", "c.module='Equb'"]
    params = [member_id]
    if round_id is not None:
        clauses.append("c.round_id=?")
        params.append(round_id)
    return df(
        f"""SELECT c.id Contribution_ID,
            c.round_id Round_ID,
            COALESCE(r.round_no,0) Round_No,
            c.amount Amount,
            c.contribution_date Date,
            c.status Status,
            CASE
                WHEN COALESCE(r.contribution_amount,0)>0
                THEN MIN(c.amount/r.contribution_amount,1)
                ELSE 0
            END Payment_Rate,
            c.payment_method Payment_Method,
            c.reference Reference
            FROM contributions c
            LEFT JOIN equb_rounds r ON c.round_id=r.id
            WHERE {' AND '.join(clauses)}
            ORDER BY c.id DESC""",
        params,
    )

def probability(round_id=None, pw=.5, aw=.3, cw=.2, tw=.2):
    ms = members()
    if not ms:
        return pd.DataFrame()

    rows = []
    for m in ms:
        h = member_history(m["id"], round_id)
        planned = float(
            m["target_round_contribution"]
            or m["regular_contribution"]
            or 0
        )
        paid = float(h["Amount"].sum()) if not h.empty else 0
        consistency = (
            float(h["Payment_Rate"].mean())
            if not h.empty else 0
        )
        trust = float(m["trust_score"] or 0)
        rows.append({
            "Member_ID": m["id"],
            "Member_No": m["member_no"],
            "Member": m["full_name"],
            "Planned_Contribution": planned,
            "Total_Paid": paid,
            "Payment_Consistency": consistency,
            "Trust_Score": trust,
        })

    x = pd.DataFrame(rows)
    max_planned = x["Planned_Contribution"].max()
    max_paid = x["Total_Paid"].max()

    x["Planned_Component"] = (
        x["Planned_Contribution"] / max_planned
        if max_planned else 0
    )
    x["Paid_Component"] = (
        x["Total_Paid"] / max_paid
        if max_paid else 0
    )
    x["Contribution_Weighted_Mean"] = (
        pw*x["Planned_Component"]
        + aw*x["Paid_Component"]
        + cw*x["Payment_Consistency"]
    )
    x["Adjusted_Score"] = (
        (1-tw)*x["Contribution_Weighted_Mean"]
        + tw*x["Trust_Score"]
    )

    total = x["Adjusted_Score"].sum()
    if total > 0:
        x["Probability"] = x["Adjusted_Score"] / total
    else:
        x["Probability"] = 1 / len(x)

    x["Cumulative_Probability"] = x["Probability"].cumsum()
    return x

# ============================================================
# MODULE 1: DASHBOARD
# ============================================================

def dashboard():
    header(
        "Equb Executive Dashboard",
        "Branch, member, contribution, round and statistical management.",
    )

    vals = [
        sql(
            "SELECT COUNT(*) n FROM members WHERE module='Equb' AND status='Active'",
            fetch=True,
        )[0]["n"],
        sql(
            "SELECT COUNT(*) n FROM branches WHERE module='Equb' AND status='Active'",
            fetch=True,
        )[0]["n"],
        sql(
            "SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",
            fetch=True,
        )[0]["n"],
        sql(
            "SELECT COALESCE(SUM(total_pool),0) n FROM equb_rounds",
            fetch=True,
        )[0]["n"],
    ]

    a,b,c,d = st.columns(4)
    a.metric("Active Members", vals[0])
    b.metric("Active Branches", vals[1])
    c.metric("Equb Savings", money(vals[2]))
    d.metric("Recorded Pools", money(vals[3]))

    st.markdown("""
    <div class="section-card">
    <div class="module-label">Equb App Management System</div>
    Digital rotating savings management with member registration,
    monthly or round contribution planning, contribution history,
    payment consistency, weighted contribution scoring,
    trust-adjusted probability, round administration,
    transactions and transparent statistical simulation.
    </div>
    """, unsafe_allow_html=True)

    p = probability()
    if not p.empty:
        a,b,c,d = st.columns(4)
        a.metric("Equb Members", len(p))
        b.metric("Planned Contribution", money(p["Planned_Contribution"].sum()))
        c.metric("Actual Paid", money(p["Total_Paid"].sum()))
        d.metric("Average Payment Rate", f"{p['Payment_Consistency'].mean():.1%}")

    st.subheader("Recent Activity")
    x = df("""
        SELECT timestamp Timestamp, username User, module Module,
               action Action, details Details
        FROM audit_log ORDER BY id DESC LIMIT 15
    """)
    if not x.empty:
        st.dataframe(x, use_container_width=True, hide_index=True)

# ============================================================
# MODULE 2: BRANCH MANAGEMENT
# ============================================================

def branch_page():
    header("Module 2: Branch Management", "Bank-style branch structure for Equb.")

    t1,t2 = st.tabs(["Branch Directory","Register Branch"])

    with t1:
        x = df("""
            SELECT code Branch_Code,name Branch_Name,module Module,
                   location Location,manager Manager,phone Phone,status Status
            FROM branches WHERE module='Equb' ORDER BY name
        """)
        st.dataframe(x, use_container_width=True, hide_index=True)
        if not x.empty:
            download(x, "equb_branches.csv")

    with t2:
        with st.form("branch_form"):
            a,b = st.columns(2)
            code = a.text_input("Branch Code", placeholder="EQB-003")
            name = b.text_input("Branch Name")
            loc = a.text_input("Location")
            manager = b.text_input("Manager")
            phone = a.text_input("Phone")
            status = b.selectbox("Status", ["Active","Inactive"])
            ok = st.form_submit_button(
                "Register Branch", type="primary", use_container_width=True
            )

        if ok:
            if not code.strip() or not name.strip():
                st.error("Branch code and branch name are required.")
            else:
                try:
                    sql(
                        """INSERT INTO branches
                        (code,name,module,location,manager,phone,status,created_at)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (
                            code.strip(), name.strip(), "Equb",
                            loc.strip(), manager.strip(),
                            phone.strip(), status, now()
                        ),
                    )
                    audit("Created branch","Equb",code.strip())
                    st.success("Branch registered.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Branch code already exists.")

# ============================================================
# MODULE 3: MEMBER MANAGEMENT
# ============================================================

def member_page():
    header(
        "Module 3: Member Management",
        "Registration, contribution planning and member profiles.",
    )

    t1,t2,t3 = st.tabs(["Directory","Register Member","Member Profile"])

    with t1:
        x = df("""
            SELECT m.member_no Member_No,m.full_name Full_Name,
                   b.code Branch,m.phone Phone,m.sex Sex,
                   m.join_date Join_Date,
                   m.contribution_frequency Frequency,
                   m.regular_contribution Planned_Contribution,
                   m.target_round_contribution Round_Contribution,
                   m.trust_score Trust_Score,m.status Status
            FROM members m
            LEFT JOIN branches b ON m.branch_id=b.id
            WHERE m.module='Equb'
            ORDER BY m.full_name
        """)
        st.dataframe(x, use_container_width=True, hide_index=True)
        if not x.empty:
            download(x, "equb_members.csv")

    with t2:
        bl = branches()
        if not bl:
            st.warning("Register an Equb branch first.")
        else:
            opts = [f"{b['code']} | {b['name']}" for b in bl]
            with st.form("member_form"):
                a,b = st.columns(2)
                member_no = a.text_input("Member Number", placeholder="EQB-M001")
                full_name = b.text_input("Full Name")
                phone = a.text_input("Phone")
                sex = b.selectbox("Sex", ["Not specified","Male","Female"])
                join_date = a.date_input("Join Date", date.today())
                branch_choice = b.selectbox("Branch", opts)
                frequency = a.selectbox("Contribution Frequency", FREQUENCIES)
                regular = b.number_input(
                    "Monthly / Regular Contribution (ETB)",
                    min_value=0.0, step=50.0, value=1000.0
                )
                target = a.number_input(
                    "Target Round Contribution (ETB)",
                    min_value=0.0, step=50.0, value=1000.0
                )
                trust = b.slider("Initial Trust Score",0.0,1.0,0.5,0.01)
                status = a.selectbox("Status", MEMBER_STATUS)
                address = b.text_input("Address")
                notes = st.text_area("Notes")
                ok = st.form_submit_button(
                    "Register Member", type="primary", use_container_width=True
                )

            if ok:
                if not member_no.strip() or not full_name.strip():
                    st.error("Member number and full name are required.")
                else:
                    branch = bl[opts.index(branch_choice)]
                    try:
                        sql(
                            """INSERT INTO members
                            (member_no,full_name,phone,sex,join_date,module,branch_id,
                             regular_contribution,contribution_frequency,
                             target_round_contribution,trust_score,status,address,notes,created_at)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (
                                member_no.strip(), full_name.strip(), phone.strip(),
                                sex, str(join_date), "Equb", branch["id"],
                                regular, frequency, target, trust, status,
                                address.strip(), notes.strip(), now()
                            ),
                        )
                        audit("Registered member","Equb",member_no.strip())
                        st.success("Member registered.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Member number already exists.")

    with t3:
        ml = members()
        if not ml:
            st.info("No Equb members registered yet.")
        else:
            labels = [f"{m['member_no']} | {m['full_name']}" for m in ml]
            choice = st.selectbox("Select Member", labels)
            m = ml[labels.index(choice)]
            h = member_history(m["id"])

            a,b,c,d = st.columns(4)
            a.metric("Branch", m["branch_name"] or "")
            b.metric("Planned Contribution", money(m["regular_contribution"]))
            c.metric("Total Paid", money(h["Amount"].sum() if not h.empty else 0))
            d.metric("Trust Score", f"{float(m['trust_score'] or 0):.1%}")

            profile = pd.DataFrame([{
                "Member Number":m["member_no"],
                "Full Name":m["full_name"],
                "Phone":m["phone"] or "",
                "Sex":m["sex"] or "",
                "Branch":m["branch_name"] or "",
                "Join Date":m["join_date"] or "",
                "Frequency":m["contribution_frequency"] or "",
                "Planned Contribution":m["regular_contribution"] or 0,
                "Round Contribution":m["target_round_contribution"] or 0,
                "Trust Score":f"{float(m['trust_score'] or 0):.2%}",
                "Status":m["status"],
                "Address":m["address"] or "",
            }])
            st.dataframe(profile, use_container_width=True, hide_index=True)

            st.subheader("Contribution History")
            if h.empty:
                st.info("No contribution records yet.")
            else:
                st.dataframe(h, use_container_width=True, hide_index=True)

# ============================================================
# MODULE 4: EQUB MANAGEMENT
# ============================================================

def equb():
    header(
        "Module 4: Equb",
        "Digital rotating savings, rounds, contributions and transparent statistical selection.",
    )

    tabs = st.tabs([
        "Overview","Rounds","Contributions",
        "Weighted Probability","Simulation","Draw History"
    ])

    with tabs[0]:
        equb_overview()
    with tabs[1]:
        round_page()
    with tabs[2]:
        contribution_page()
    with tabs[3]:
        probability_page()
    with tabs[4]:
        simulation_page()
    with tabs[5]:
        history_page()

def equb_overview():
    a,b,c,d = st.columns(4)
    a.metric(
        "Active Members",
        sql("SELECT COUNT(*) n FROM members WHERE module='Equb' AND status='Active'",fetch=True)[0]["n"]
    )
    a2 = sql(
        "SELECT COALESCE(SUM(amount),0) n FROM contributions WHERE module='Equb' AND status='Paid'",
        fetch=True
    )[0]["n"]
    b.metric("Total Contributions", money(a2))
    c.metric("Rounds", sql("SELECT COUNT(*) n FROM equb_rounds",fetch=True)[0]["n"])
    d.metric(
        "Recorded Pools",
        money(sql("SELECT COALESCE(SUM(total_pool),0) n FROM equb_rounds",fetch=True)[0]["n"])
    )

    st.subheader("Member Contribution Plan")
    x = df("""
        SELECT m.member_no Member_No,m.full_name Member,
               m.contribution_frequency Frequency,
               m.regular_contribution Planned_Contribution,
               m.target_round_contribution Round_Target,
               COALESCE(SUM(c.amount),0) Total_Paid
        FROM members m
        LEFT JOIN contributions c
          ON m.id=c.member_id AND c.module='Equb' AND c.status='Paid'
        WHERE m.module='Equb'
        GROUP BY m.id
        ORDER BY m.full_name
    """)
    if not x.empty:
        st.dataframe(x,use_container_width=True,hide_index=True)

    st.markdown("""
    <div class="section-card">
    <div class="module-label">Equb Operating Model</div>
    The member record stores the intended contribution amount;
    the round stores the standard contribution for the cycle;
    actual payments are recorded separately. The statistical layer
    uses planned contribution, realized contribution, payment
    consistency and an optional trust component.
    </div>
    """, unsafe_allow_html=True)

def round_page():
    bl = branches()
    opts = [f"{b['code']} | {b['name']}" for b in bl]

    if not bl:
        st.warning("Create an Equb branch first.")
        return

    with st.form("round_form"):
        a,b,c = st.columns(3)
        branch_choice = a.selectbox("Branch", opts)
        round_no = b.number_input("Round Number", min_value=1, value=1, step=1)
        amount = c.number_input(
            "Standard Contribution per Member / Round (ETB)",
            min_value=0.0, value=1000.0, step=50.0
        )
        start_date = a.date_input("Start Date", date.today())
        draw_date = b.date_input("Expected Draw Date", date.today())
        expected = c.number_input(
            "Expected Members", min_value=1, value=10, step=1
        )
        status = c.selectbox("Status", ROUND_STATUS)
        ok = st.form_submit_button(
            "Create Equb Round", type="primary", use_container_width=True
        )

    if ok:
        br = bl[opts.index(branch_choice)]
        existing = sql(
            "SELECT id FROM equb_rounds WHERE branch_id=? AND round_no=?",
            (br["id"],int(round_no)),fetch=True
        )
        if existing:
            st.error("That round number already exists for this branch.")
        else:
            sql(
                """INSERT INTO equb_rounds
                (branch_id,round_no,contribution_amount,start_date,draw_date,
                 expected_members,total_pool,status,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    br["id"],int(round_no),amount,str(start_date),str(draw_date),
                    int(expected),0,status,now()
                )
            )
            audit("Created Equb round","Equb",f"{br['code']} round {round_no}")
            st.success("Round created.")
            st.rerun()

    x = df("""
        SELECT r.round_no Round_No,b.code Branch,
               r.contribution_amount Contribution_Per_Round,
               r.expected_members Expected_Members,
               r.total_pool Total_Pool,r.start_date Start_Date,
               r.draw_date Draw_Date,r.status Status,
               COALESCE(m.full_name,'') Winner
        FROM equb_rounds r
        JOIN branches b ON r.branch_id=b.id
        LEFT JOIN members m ON r.winner_member_id=m.id
        ORDER BY r.id DESC
    """)
    st.dataframe(x,use_container_width=True,hide_index=True)

def contribution_page():
    st.subheader("Equb Contribution Recording")

    rounds = sql("""
        SELECT r.*,b.code branch_code,b.name branch_name
        FROM equb_rounds r JOIN branches b ON r.branch_id=b.id
        WHERE r.status IN ('Open','Closed')
        ORDER BY r.id DESC
    """,fetch=True)

    if not rounds:
        st.info("Create an open Equb round first.")
        return

    labels = [
        f"{r['branch_code']} | Round {r['round_no']} | {money(r['contribution_amount'])}"
        for r in rounds
    ]

    with st.form("contribution_form"):
        choice = st.selectbox("Round", labels)
        r = rounds[labels.index(choice)]
        ml = members(r["branch_id"])

        if not ml:
            st.warning("No Equb members are registered in this branch.")
            st.form_submit_button("Record Contribution", disabled=True)
            return

        mlabels = [f"{m['member_no']} | {m['full_name']}" for m in ml]
        mchoice = st.selectbox("Member", mlabels)
        m = ml[mlabels.index(mchoice)]

        suggested = float(
            m["target_round_contribution"]
            or m["regular_contribution"]
            or r["contribution_amount"]
            or 0
        )
        amount = st.number_input(
            "Actual Contribution Amount (ETB)",
            min_value=0.0,value=suggested,step=50.0
        )
        contribution_date = st.date_input("Contribution Date",date.today())
        status = st.selectbox("Status",["Paid","Pending","Cancelled"])
        payment_method = st.selectbox("Payment Method",PAYMENT_METHODS)
        reference = st.text_input("Reference")
        notes = st.text_area("Notes")
        ok = st.form_submit_button(
            "Record Contribution",type="primary",use_container_width=True
        )

    if ok:
        if amount <= 0:
            st.error("Contribution amount must be greater than zero.")
            return

        contribution_id = sql(
            """INSERT INTO contributions
            (member_id,module,round_id,amount,contribution_date,status,
             reference,payment_method,notes,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                m["id"],"Equb",r["id"],amount,str(contribution_date),status,
                reference.strip(),payment_method,notes.strip(),now()
            )
        )

        if status == "Paid":
            sql(
                "UPDATE equb_rounds SET total_pool=COALESCE(total_pool,0)+? WHERE id=?",
                (amount,r["id"])
            )
            sql(
                """INSERT INTO transactions
                (module,branch_id,member_id,transaction_type,amount,
                 reference,transaction_date,description,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    "Equb",r["branch_id"],m["id"],"Contribution",
                    amount,reference.strip(),str(contribution_date),
                    f"Contribution for Round {r['round_no']}",now()
                )
            )

        audit(
            "Recorded Equb contribution",
            "Equb",
            f"Contribution {contribution_id}; member {m['member_no']}; round {r['round_no']}"
        )
        st.success("Contribution recorded.")
        st.rerun()

def probability_page():
    st.subheader("Weighted Contribution Probability")

    st.markdown("""
    <div class="section-card">
    <div class="module-label">Prototype Statistical Model</div>
    The model combines normalized planned contribution,
    normalized realized contribution, payment consistency and
    a trust component. The resulting score is normalized into
    a comparative probability. This is a decision-support
    demonstration and does not replace the approved Equb rules.
    </div>
    """, unsafe_allow_html=True)

    a,b,c,d = st.columns(4)
    pw = a.number_input("Planned Weight",0.0,1.0,0.50,0.05)
    aw = b.number_input("Actual Paid Weight",0.0,1.0,0.30,0.05)
    cw = c.number_input("Consistency Weight",0.0,1.0,0.20,0.05)
    tw = d.number_input("Trust Weight",0.0,1.0,0.20,0.05)

    if abs((pw+aw+cw)-1) > 0.001:
        st.warning("Planned, actual-paid and consistency weights should sum to 1.")
        return

    x = probability(pw=pw,aw=aw,cw=cw,tw=tw)

    if x.empty:
        st.info("Register Equb members first.")
        return

    display = x.copy()
    for col in [
        "Payment_Consistency","Trust_Score",
        "Probability","Cumulative_Probability"
    ]:
        display[col] = display[col].map(lambda v:f"{float(v):.2%}")

    st.dataframe(display,use_container_width=True,hide_index=True)
    download(x,"equb_weighted_probability.csv")

    st.markdown("""
    **Model components**

    Planned contribution component = planned contribution / maximum planned contribution.

    Actual payment component = realized paid amount / maximum realized paid amount.

    Payment consistency = average payment rate across recorded contributions.

    Weighted score = 0.50(Planned) + 0.30(Paid) + 0.20(Consistency).

    Trust adjustment = (1 − trust weight) × weighted score + trust weight × trust score.

    Probability = adjusted score / sum of adjusted scores.
    """)

def simulation_page():
    st.subheader("Weighted Selection Simulation")
    x = probability()

    if x.empty:
        st.info("Register Equb members first.")
        return

    n = st.number_input(
        "Number of Simulations",1,10000,1000,100
    )

    if st.button("Run Monte Carlo Demonstration",type="primary",use_container_width=True):
        names = x["Member"].tolist()
        weights = x["Probability"].tolist()
        results = random.choices(names,weights=weights,k=int(n))
        counts = pd.Series(results).value_counts()

        sim = x[["Member_No","Member","Probability"]].copy()
        sim["Expected_Probability"] = sim["Probability"]
        sim["Observed_Probability"] = sim["Member"].map(
            lambda m: counts.get(m,0)/n
        )
        sim["Difference"] = (
            sim["Observed_Probability"]-sim["Expected_Probability"]
        )

        st.dataframe(
            sim.sort_values("Observed_Probability",ascending=False),
            use_container_width=True,hide_index=True
        )
        st.caption(
            "Monte Carlo frequencies should approach model probabilities as simulations increase."
        )
        audit(
            "Executed Equb Monte Carlo simulation",
            "Equb",f"{n} simulations"
        )

def history_page():
    st.subheader("Draw and Round History")
    x = df("""
        SELECT r.round_no Round_No,b.code Branch,
               r.total_pool Pool,r.draw_date Draw_Date,
               COALESCE(m.member_no,'') Winner_No,
               COALESCE(m.full_name,'') Winner,
               r.status Status
        FROM equb_rounds r
        JOIN branches b ON r.branch_id=b.id
        LEFT JOIN members m ON r.winner_member_id=m.id
        ORDER BY r.id DESC
    """)
    st.dataframe(x,use_container_width=True,hide_index=True)
    if not x.empty:
        download(x,"equb_round_history.csv")

    st.divider()
    st.subheader("Authorize / Record Round Winner")

    rounds = sql("""
        SELECT r.*,b.code branch_code
        FROM equb_rounds r JOIN branches b ON r.branch_id=b.id
        WHERE r.status IN ('Open','Closed')
        ORDER BY r.id DESC
    """,fetch=True)

    if not rounds:
        st.info("No open or closed rounds available.")
        return

    labels = [
        f"{r['branch_code']} | Round {r['round_no']}"
        for r in rounds
    ]
    rc = st.selectbox("Round",labels)
    r = rounds[labels.index(rc)]
    ml = members(r["branch_id"])

    if not ml:
        st.info("No members available for this branch.")
        return

    mlabels = [f"{m['member_no']} | {m['full_name']}" for m in ml]
    wc = st.selectbox("Winner / Recipient",mlabels)

    if st.button("Record Round Winner",type="primary"):
        m = ml[mlabels.index(wc)]
        sql(
            "UPDATE equb_rounds SET winner_member_id=?,status='Completed' WHERE id=?",
            (m["id"],r["id"])
        )
        sql(
            """INSERT INTO transactions
            (module,branch_id,member_id,transaction_type,amount,
             reference,transaction_date,description,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                "Equb",r["branch_id"],m["id"],"Payout",
                float(r["total_pool"] or 0),
                f"ROUND-{r['round_no']}",
                str(r["draw_date"] or date.today()),
                f"Equb payout for Round {r['round_no']}",now()
            )
        )
        audit(
            "Recorded Equb round winner",
            "Equb",
            f"Round {r['round_no']}; winner {m['member_no']}"
        )
        st.success("Round winner recorded and round marked Completed.")
        st.rerun()

# ============================================================
# MODULE 5: TRANSACTIONS
# ============================================================

def transactions():
    header("Module 5: Transactions","Unified Equb financial transaction register.")

    t1,t2 = st.tabs(["Transaction Register","Record Transaction"])

    with t1:
        x = df("""
            SELECT t.transaction_date Date,t.transaction_type Type,
                   t.amount Amount,t.reference Reference,
                   COALESCE(m.member_no,'') Member_No,
                   COALESCE(m.full_name,'') Member,
                   COALESCE(b.code,'') Branch,
                   t.description Description
            FROM transactions t
            LEFT JOIN members m ON t.member_id=m.id
            LEFT JOIN branches b ON t.branch_id=b.id
            WHERE t.module='Equb'
            ORDER BY t.id DESC
        """)
        st.dataframe(x,use_container_width=True,hide_index=True)
        if not x.empty:
            download(x,"equb_transactions.csv")

    with t2:
        bl=branches()
        ml=members()
        with st.form("transaction_form"):
            a,b=st.columns(2)
            typ=a.selectbox(
                "Transaction Type",
                ["Contribution","Payout","Adjustment","Other"]
            )
            amount=b.number_input("Amount (ETB)",min_value=0.0,step=50.0)
            branch_choice=a.selectbox(
                "Branch",
                ["No branch"]+[f"{z['code']} | {z['name']}" for z in bl]
            )
            member_choice=b.selectbox(
                "Member",
                ["No member"]+[f"{z['member_no']} | {z['full_name']}" for z in ml]
            )
            reference=a.text_input("Reference")
            transaction_date=b.date_input("Transaction Date",date.today())
            description=st.text_area("Description")
            ok=st.form_submit_button(
                "Record Transaction",type="primary",use_container_width=True
            )

        if ok:
            bid=None
            mid=None
            if branch_choice!="No branch":
                opts=[f"{z['code']} | {z['name']}" for z in bl]
                bid=bl[opts.index(branch_choice)]["id"]
            if member_choice!="No member":
                opts=[f"{z['member_no']} | {z['full_name']}" for z in ml]
                mid=ml[opts.index(member_choice)]["id"]

            sql(
                """INSERT INTO transactions
                (module,branch_id,member_id,transaction_type,amount,
                 reference,transaction_date,description,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    "Equb",bid,mid,typ,amount,reference.strip(),
                    str(transaction_date),description.strip(),now()
                )
            )
            audit("Created transaction","Equb",reference.strip())
            st.success("Transaction recorded.")
            st.rerun()

# ============================================================
# MODULE 6: REPORTS
# ============================================================

def reports():
    header("Module 6: Reports and Analytics","Equb management information and statistical analysis.")

    report = st.selectbox(
        "Report",
        [
            "Module Summary",
            "Member Contribution Plans",
            "Equb Contributions",
            "Equb Rounds",
            "Equb Probability",
            "Transactions",
            "Member Payment Performance",
        ],
    )

    queries = {
        "Module Summary": """
            SELECT 'Equb' Module,
                   COUNT(*) Members,
                   ROUND(AVG(regular_contribution),2) Average_Planned_Contribution,
                   ROUND(AVG(trust_score),3) Average_Trust
            FROM members
            WHERE module='Equb' AND status='Active'
        """,
        "Member Contribution Plans": """
            SELECT m.member_no Member_No,m.full_name Member,
                   b.code Branch,m.contribution_frequency Frequency,
                   m.regular_contribution Planned_Contribution,
                   m.target_round_contribution Round_Target,
                   COALESCE(SUM(c.amount),0) Total_Paid
            FROM members m
            LEFT JOIN branches b ON m.branch_id=b.id
            LEFT JOIN contributions c
              ON m.id=c.member_id AND c.module='Equb' AND c.status='Paid'
            WHERE m.module='Equb'
            GROUP BY m.id ORDER BY m.full_name
        """,
        "Equb Contributions": """
            SELECT c.contribution_date Date,m.member_no Member_No,
                   m.full_name Member,b.code Branch,
                   r.round_no Round,r.contribution_amount Planned,
                   c.amount Actual_Paid,c.status Status,
                   c.reference Reference,c.payment_method Payment_Method
            FROM contributions c
            JOIN members m ON c.member_id=m.id
            LEFT JOIN equb_rounds r ON c.round_id=r.id
            LEFT JOIN branches b ON m.branch_id=b.id
            WHERE c.module='Equb'
            ORDER BY c.id DESC
        """,
        "Equb Rounds": """
            SELECT r.round_no Round,b.code Branch,
                   r.contribution_amount Contribution,
                   r.expected_members Expected_Members,
                   r.total_pool Pool,r.start_date Start_Date,
                   r.draw_date Draw_Date,r.status Status,
                   COALESCE(m.full_name,'') Winner
            FROM equb_rounds r
            JOIN branches b ON r.branch_id=b.id
            LEFT JOIN members m ON r.winner_member_id=m.id
            ORDER BY r.id DESC
        """,
        "Transactions": """
            SELECT transaction_date Date,transaction_type Type,
                   amount Amount,reference Reference,
                   description Description
            FROM transactions WHERE module='Equb'
            ORDER BY id DESC
        """,
    }

    if report == "Equb Probability":
        x = probability()
    elif report == "Member Payment Performance":
        x = probability()
        if not x.empty:
            x = x[
                [
                    "Member_No","Member","Planned_Contribution",
                    "Total_Paid","Payment_Consistency","Trust_Score"
                ]
            ]
    else:
        x = df(queries[report])

    st.dataframe(x,use_container_width=True,hide_index=True)
    if not x.empty:
        download(x,"equb_report.csv")

# ============================================================
# MODULE 7: MANUALS
# ============================================================

def manuals():
    header("Module 7: Manuals","Equb operating guidance and model documentation.")

    sections = [
        (
            "Equb Operating Manual",
            """Register branches and members, define recurring contribution plans,
            create Equb rounds, record actual payments, reconcile pools,
            authorize round outcomes and retain transaction history."""
        ),
        (
            "Contribution Management",
            """Each member may have a regular contribution and a target
            round contribution. A round may define its own standard
            contribution. Actual payments are recorded separately with
            date, reference, method and status."""
        ),
        (
            "Statistical Selection Model",
            """The prototype combines normalized planned contribution,
            historical paid contribution and payment consistency,
            followed by an optional trust adjustment and normalized
            comparative probability. Monte Carlo simulation is provided
            only as a transparent statistical demonstration."""
        ),
        (
            "Financial and Audit Controls",
            """Important payments should have unique references. Recorded
            contributions should be reconciled against actual collections.
            Round pools should be reconciled with paid contributions.
            Administrative actions should remain traceable through the audit trail."""
        ),
        (
            "Prototype Limitation",
            """This application is a technology-transfer and demonstration
            prototype. Production deployment would require additional
            security controls, encryption, backup and recovery, stronger
            authorization, regulatory review, independent financial controls
            and formal Equb governance approval."""
        ),
    ]

    for title,text in sections:
        st.markdown(
            f'<div class="manual-card"><h2>{title}</h2><p>{text}</p></div>',
            unsafe_allow_html=True
        )

# ============================================================
# MODULE 8: AUDIT
# ============================================================

def audit_page():
    header("Module 8: Audit Trail","Traceable record of important Equb system activities.")
    x = df("""
        SELECT timestamp Timestamp,username Username,module Module,
               action Action,details Details
        FROM audit_log ORDER BY id DESC LIMIT 2000
    """)
    st.dataframe(x,use_container_width=True,hide_index=True)
    if not x.empty:
        download(x,"equb_audit.csv")

# ============================================================
# MODULE 9: USER ADMINISTRATION
# ============================================================

def users_page():
    header("Module 9: User Administration","Role-based Equb management accounts.")

    x = df("""
        SELECT username Username,full_name Full_Name,role Role,
               module Module,active Active,created_at Created_At
        FROM users ORDER BY username
    """)
    st.dataframe(x,use_container_width=True,hide_index=True)

    bl=branches()
    opts=[f"{b['code']} | {b['name']}" for b in bl]

    with st.form("user_form"):
        a,b=st.columns(2)
        username=a.text_input("Username")
        full_name=b.text_input("Full Name")
        password=a.text_input("Password",type="password")
        role=b.selectbox("Role",ROLES)
        branch_choice=a.selectbox("Branch",["No branch"]+opts)
        active=b.selectbox("Active",[1,0])
        ok=st.form_submit_button(
            "Create User",type="primary",use_container_width=True
        )

    if ok:
        if not username.strip() or not full_name.strip():
            st.error("Username and full name are required.")
            return
        if len(password)<6:
            st.error("Password must contain at least six characters.")
            return

        bid=None
        if branch_choice!="No branch":
            bid=bl[opts.index(branch_choice)]["id"]

        try:
            sql(
                """INSERT INTO users
                (username,password_hash,full_name,role,module,branch_id,active,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    username.strip(),pwd_hash(password),full_name.strip(),
                    role,"Equb",bid,active,now()
                )
            )
            audit("Created user","Equb",username.strip())
            st.success("User created.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("Username already exists.")

# ============================================================
# MAIN
# ============================================================

def main():
    init_db()

    if not st.session_state.get("authenticated",False):
        login()
        return

    with st.sidebar:
        st.markdown("## Equb")
        st.caption("Equb App Management System")
        st.write(f"User: **{st.session_state.get('full_name','')}**")
        st.write(f"Role: **{st.session_state.get('role','')}**")

        if st.button("Sign out",use_container_width=True):
            audit("Logout")
            st.session_state.clear()
            st.rerun()

        st.divider()

        nav = [
            "Dashboard",
            "Branch Management",
            "Member Management",
            "Equb",
            "Transactions",
            "Reports and Analytics",
            "Manuals",
            "Audit Trail",
        ]

        if st.session_state.get("role")=="Administrator":
            nav.append("User Administration")

        page=st.radio("Navigation",nav)

    pages={
        "Dashboard":dashboard,
        "Branch Management":branch_page,
        "Member Management":member_page,
        "Equb":equb,
        "Transactions":transactions,
        "Reports and Analytics":reports,
        "Manuals":manuals,
        "Audit Trail":audit_page,
        "User Administration":users_page,
    }

    pages[page]()

if __name__=="__main__":
    main()
