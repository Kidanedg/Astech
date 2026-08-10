import streamlit as st
import sqlite3
import hashlib
import secrets
import hmac
import random
from datetime import datetime, date
from pathlib import Path
import pandas as pd

# ============================================================
# IDFS WEB PLATFORM - SINGLE FILE DEMONSTRATION
# Indigenous Digital Financial System
# Aksum University | Technology Transfer Project Team | 2026
# ============================================================

st.set_page_config(
    page_title="IDFS Web Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = Path("idfs_demo.db")

MODULES = ["Equb", "Iddir"]
ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]

EVENT_TYPES = [
    "Funeral", "Wedding", "Holiday", "Emergency",
    "Medical Support", "Family Support", "Other"
]

PROPERTY_TYPES = [
    "Land", "Building", "Vehicle", "Equipment",
    "Furniture", "Office Asset", "Other"
]

# ============================================================
# APPLICATION STYLE
# ============================================================

st.markdown("""
<style>
/* ---------- Global ---------- */
.stApp {
    background: linear-gradient(135deg, #F7F9FC 0%, #EEF4FA 100%);
}
.main-title {
    font-size: 2rem;
    font-weight: 750;
    color: #163A5F;
    margin-bottom: .15rem;
}
.sub-title {
    font-size: .95rem;
    color: #64748B;
    margin-bottom: 1.2rem;
}
.section-card {
    padding: 1.1rem 1.3rem;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    background: #FFFFFF;
    margin-bottom: 1rem;
    box-shadow: 0 4px 16px rgba(15,35,55,.04);
}
.module-label {
    color: #0B5CAD;
    font-weight: 750;
    font-size: .82rem;
    text-transform: uppercase;
    letter-spacing: .06em;
}
.metric-note {
    color: #64748B;
    font-size: .82rem;
}
.footer-note {
    text-align: center;
    color: #64748B;
    font-size: .76rem;
    margin-top: 1.8rem;
}

/* ---------- Login ---------- */
.login-shell {
    max-width: 1080px;
    margin: 3vh auto 0 auto;
}
.login-brand-panel {
    background: linear-gradient(145deg, #0B5CAD 0%, #163A5F 72%, #243447 100%);
    border-radius: 24px;
    padding: 3.0rem 3.0rem 2.5rem 3.0rem;
    color: white;
    min-height: 510px;
    box-shadow: 0 20px 55px rgba(11,92,173,.20);
    position: relative;
    overflow: hidden;
}
.login-brand-panel:after {
    content: "";
    position: absolute;
    width: 300px;
    height: 300px;
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 50%;
    right: -120px;
    bottom: -130px;
}
.login-brand-panel:before {
    content: "";
    position: absolute;
    width: 180px;
    height: 180px;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 50%;
    right: 40px;
    top: -90px;
}
.idfs-emblem {
    width: 78px;
    height: 78px;
    border-radius: 20px;
    background: rgba(255,255,255,.14);
    border: 1px solid rgba(255,255,255,.25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.35rem;
    margin-bottom: 1.4rem;
}
.login-brand {
    font-size: 2.8rem;
    font-weight: 850;
    letter-spacing: .08em;
    margin: 0;
}
.login-expansion {
    font-size: 1rem;
    font-weight: 650;
    margin-top: .25rem;
    opacity: .96;
}
.login-tagline {
    font-size: 1.05rem;
    line-height: 1.65;
    margin-top: 1.5rem;
    color: rgba(255,255,255,.88);
}
.login-feature {
    margin-top: 1.35rem;
    padding-top: 1.2rem;
    border-top: 1px solid rgba(255,255,255,.18);
    font-size: .88rem;
    line-height: 1.8;
    color: rgba(255,255,255,.84);
}
.login-right {
    background: rgba(255,255,255,.98);
    border: 1px solid #D9E2EC;
    border-radius: 24px;
    padding: 2.5rem 2.7rem;
    min-height: 510px;
    box-shadow: 0 20px 55px rgba(15,35,55,.10);
}
.login-heading {
    color: #163A5F;
    font-size: 1.75rem;
    font-weight: 800;
    margin-bottom: .25rem;
}
.login-caption {
    color: #64748B;
    font-size: .9rem;
    margin-bottom: 1.5rem;
}
.login-security {
    margin-top: 1.15rem;
    padding: .75rem 1rem;
    background: #F1F7FC;
    border: 1px solid #DCEAF7;
    border-radius: 10px;
    color: #496274;
    font-size: .78rem;
}
.login-copyright {
    text-align: center;
    color: #64748B;
    font-size: .74rem;
    margin-top: 1.2rem;
    line-height: 1.6;
}
.login-demo {
    margin-top: .75rem;
    padding: .65rem .85rem;
    border-radius: 9px;
    background: #FFF8E8;
    border: 1px solid #F2D58A;
    color: #765C16;
    font-size: .78rem;
}
.stButton > button[kind="primary"] {
    border-radius: 10px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE UTILITIES
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    try:
        return f"ETB {float(value or 0):,.2f}"
    except Exception:
        return "ETB 0.00"


def conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def sql(query, params=(), fetch=False, many=False):
    c = conn()
    cur = c.cursor()
    try:
        if many:
            cur.executemany(query, params)
        else:
            cur.execute(query, params)
        rows = cur.fetchall() if fetch else None
        c.commit()
        return rows
    finally:
        c.close()


def df(query, params=()):
    rows = sql(query, params, fetch=True)
    return pd.DataFrame([dict(row) for row in rows])


def pwd_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()
    return salt + "$" + h


def check_pwd(password, stored):
    try:
        salt, stored_hash = stored.split("$", 1)
        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000,
        ).hex()
        return hmac.compare_digest(calculated, stored_hash)
    except Exception:
        return False


def audit(action, module="Portal", details=""):
    try:
        username = st.session_state.get("username", "anonymous")
        sql(
            """INSERT INTO audit_log
               (username,module,action,details,timestamp)
               VALUES(?,?,?,?,?)""",
            (username, module, action, details, now()),
        )
    except Exception:
        pass


def table_exists(table_name):
    row = sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
        fetch=True,
    )
    return bool(row)


def existing_columns(table_name):
    if not table_exists(table_name):
        return set()
    return {
        row["name"]
        for row in sql(f"PRAGMA table_info({table_name})", fetch=True)
    }


def ensure_column(table_name, column, definition):
    if column not in existing_columns(table_name):
        sql(f"ALTER TABLE {table_name} ADD COLUMN {column} {definition}")


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
        contribution_amount REAL,
        start_date TEXT,
        draw_date TEXT,
        expected_members INTEGER,
        total_pool REAL DEFAULT 0,
        winner_member_id INTEGER,
        status TEXT DEFAULT 'Open',
        created_at TEXT NOT NULL
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
        created_at TEXT NOT NULL
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
    c.commit()
    c.close()

    migrations = {
        "users": {
            "password_hash": "TEXT", "full_name": "TEXT", "role": "TEXT",
            "module": "TEXT", "branch_id": "INTEGER",
            "active": "INTEGER DEFAULT 1", "created_at": "TEXT",
        },
        "branches": {
            "code": "TEXT", "name": "TEXT", "module": "TEXT",
            "location": "TEXT", "manager": "TEXT", "phone": "TEXT",
            "status": "TEXT DEFAULT 'Active'", "created_at": "TEXT",
        },
        "members": {
            "member_no": "TEXT", "full_name": "TEXT", "phone": "TEXT",
            "sex": "TEXT", "join_date": "TEXT", "module": "TEXT",
            "branch_id": "INTEGER",
            "regular_contribution": "REAL DEFAULT 0",
            "trust_score": "REAL DEFAULT 0.5",
            "status": "TEXT DEFAULT 'Active'",
            "address": "TEXT", "notes": "TEXT", "created_at": "TEXT",
        },
        "equb_rounds": {
            "branch_id": "INTEGER", "round_no": "INTEGER",
            "contribution_amount": "REAL DEFAULT 0",
            "start_date": "TEXT", "draw_date": "TEXT",
            "expected_members": "INTEGER DEFAULT 0",
            "total_pool": "REAL DEFAULT 0",
            "winner_member_id": "INTEGER", "status": "TEXT DEFAULT 'Open'",
            "created_at": "TEXT",
        },
        "contributions": {
            "member_id": "INTEGER", "module": "TEXT", "round_id": "INTEGER",
            "amount": "REAL DEFAULT 0", "contribution_date": "TEXT",
            "status": "TEXT DEFAULT 'Paid'", "reference": "TEXT",
            "payment_method": "TEXT", "notes": "TEXT", "created_at": "TEXT",
        },
        "iddir_events": {
            "branch_id": "INTEGER", "event_type": "TEXT",
            "member_id": "INTEGER", "event_date": "TEXT",
            "description": "TEXT", "requested_amount": "REAL DEFAULT 0",
            "approved_amount": "REAL DEFAULT 0",
            "status": "TEXT DEFAULT 'Pending'", "payment_date": "TEXT",
            "reference": "TEXT", "created_at": "TEXT",
        },
        "properties": {
            "branch_id": "INTEGER", "property_code": "TEXT",
            "property_type": "TEXT", "description": "TEXT",
            "location": "TEXT", "acquisition_date": "TEXT",
            "acquisition_cost": "REAL DEFAULT 0",
            "current_value": "REAL DEFAULT 0",
            "status": "TEXT DEFAULT 'Active'", "custodian": "TEXT",
            "notes": "TEXT", "created_at": "TEXT",
        },
        "transactions": {
            "module": "TEXT", "branch_id": "INTEGER", "member_id": "INTEGER",
            "transaction_type": "TEXT", "amount": "REAL DEFAULT 0",
            "reference": "TEXT", "transaction_date": "TEXT",
            "description": "TEXT", "created_at": "TEXT",
        },
        "audit_log": {
            "username": "TEXT", "module": "TEXT", "action": "TEXT",
            "details": "TEXT", "timestamp": "TEXT",
        },
    }

    for table, columns in migrations.items():
        for column, definition in columns.items():
            ensure_column(table, column, definition)

    for statement in [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_branches_code ON branches(code)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_members_member_no ON members(member_no)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_properties_code ON properties(property_code)",
        "CREATE INDEX IF NOT EXISTS idx_members_module_branch ON members(module,branch_id)",
        "CREATE INDEX IF NOT EXISTS idx_contributions_round ON contributions(round_id)",
    ]:
        try:
            sql(statement)
        except sqlite3.IntegrityError:
            pass

    admin = sql(
        "SELECT id FROM users WHERE username=?",
        ("admin",),
        fetch=True,
    )
    if not admin:
        sql(
            """INSERT INTO users
            (username,password_hash,full_name,role,module,branch_id,active,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (
                "admin", pwd_hash("admin123"), "IDFS Administrator",
                "Administrator", "Portal", None, 1, now()
            ),
        )

    seed = [
        ("EQB-001", "IDFS Equb Central Branch", "Equb", "Aksum", "Branch Manager"),
        ("EQB-002", "IDFS Equb North Branch", "Equb", "Shire", "Branch Manager"),
        ("IDR-001", "IDFS Iddir Central Branch", "Iddir", "Aksum", "Branch Manager"),
        ("IDR-002", "IDFS Iddir Community Branch", "Iddir", "Shire", "Branch Manager"),
    ]

    for code, name, module, location, manager in seed:
        existing = sql(
            "SELECT id FROM branches WHERE code=?",
            (code,), fetch=True
        )
        if not existing:
            sql(
                """INSERT INTO branches
                (code,name,module,location,manager,phone,status,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (code, name, module, location, manager, "", "Active", now()),
            )


def header(title, subtitle=""):
    st.markdown(
        f'<div class="main-title">{title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div class="sub-title">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def branches(module=None):
    if module:
        return sql(
            "SELECT * FROM branches WHERE module=? ORDER BY name",
            (module,), fetch=True
        )
    return sql(
        "SELECT * FROM branches ORDER BY module,name",
        fetch=True
    )


def members(module=None, branch=None):
    where = []
    params = []
    if module:
        where.append("m.module=?")
        params.append(module)
    if branch:
        where.append("m.branch_id=?")
        params.append(branch)
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    return sql(
        """SELECT m.*, b.code AS branch_code, b.name AS branch_name
           FROM members m
           LEFT JOIN branches b ON m.branch_id=b.id"""
        + where_sql + " ORDER BY m.full_name",
        tuple(params), fetch=True
    )


def download(data, filename):
    st.download_button(
        "Download CSV",
        data.to_csv(index=False).encode("utf-8"),
        filename,
        "text/csv",
        use_container_width=True,
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def login():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)

    left, right = st.columns([1.08, 0.92], gap="large")

    with left:
        st.markdown("""
        <div class="login-brand-panel">
            <div class="idfs-emblem">🏦</div>
            <div class="login-brand">IDFS</div>
            <div class="login-expansion">
                Indigenous Digital Financial System
            </div>
            <div class="login-tagline">
                A digital platform for transparent, secure and
                community-centered financial administration.
            </div>
            <div class="login-feature">
                ✓ Equb savings and rotating rounds<br>
                ✓ Contribution and payment management<br>
                ✓ Contribution-weighted probability demonstration<br>
                ✓ Iddir community risk-sharing and support<br>
                ✓ Branch, member, property and transaction management<br>
                ✓ Reports, analytics and audit trail
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="login-right">
            <div class="login-heading">Welcome back</div>
            <div class="login-caption">
                Sign in to access the IDFS management platform.
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )
            submitted = st.form_submit_button(
                "Sign in securely  →",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            username_clean = username.strip()
            row = sql(
                "SELECT * FROM users WHERE username=? AND active=1",
                (username_clean,), fetch=True
            )

            if row and check_pwd(password, row[0]["password_hash"]):
                user = row[0]
                st.session_state.update(
                    authenticated=True,
                    user_id=user["id"],
                    username=user["username"],
                    full_name=user["full_name"],
                    role=user["role"],
                    module=user["module"],
                    branch_id=user["branch_id"],
                )
                audit("Successful login")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("""
        <div class="login-security">
            🔒 Passwords are stored using PBKDF2-HMAC-SHA256 hashing.
            This prototype is intended for technology-transfer
            demonstration and controlled development use.
        </div>
        <div class="login-demo">
            <b>Demo access:</b> admin / admin123
        </div>
        <div class="login-copyright">
            © 2026 Aksum University<br>
            Technology Transfer Project Team<br>
            Indigenous Digital Financial System (IDFS)<br>
            All rights reserved.
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():
    header(
        "IDFS Executive Dashboard",
        "Integrated Equb savings and Iddir community risk-sharing platform",
    )

    active_members = sql(
        "SELECT COUNT(*) AS n FROM members WHERE status='Active'",
        fetch=True
    )[0]["n"]
    active_branches = sql(
        "SELECT COUNT(*) AS n FROM branches WHERE status='Active'",
        fetch=True
    )[0]["n"]
    equb_savings = sql(
        """SELECT COALESCE(SUM(amount),0) AS n FROM contributions
           WHERE module='Equb' AND status='Paid'""",
        fetch=True
    )[0]["n"]
    iddir_property = sql(
        """SELECT COALESCE(SUM(current_value),0) AS n FROM properties
           WHERE status='Active'""",
        fetch=True
    )[0]["n"]

    a, b, c, d = st.columns(4)
    a.metric("Active Members", active_members)
    b.metric("Active Branches", active_branches)
    c.metric("Equb Savings", money(equb_savings))
    d.metric("Iddir Property Value", money(iddir_property))

    st.divider()

    x, y = st.columns(2)
    with x:
        st.markdown("""
        <div class="section-card">
            <div class="module-label">IDFS Equb</div>
            Community savings, regular contributions, rounds,
            payment records and contribution-weighted probability
            demonstration.
        </div>
        """, unsafe_allow_html=True)
    with y:
        st.markdown("""
        <div class="section-card">
            <div class="module-label">IDFS Iddir</div>
            Community risk sharing for funeral, wedding, holiday,
            emergency, medical and family support, together with
            property management.
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Recent Activity")
    activity = df("""
        SELECT timestamp AS Timestamp, username AS User,
               module AS Module, action AS Action, details AS Details
        FROM audit_log ORDER BY id DESC LIMIT 15
    """)
    if activity.empty:
        st.info("No activity has been recorded yet.")
    else:
        st.dataframe(activity, use_container_width=True, hide_index=True)


# ============================================================
# BRANCH MANAGEMENT
# ============================================================

def branch_page():
    header(
        "Module 4: Branch Management",
        "Bank-style branch structure for Equb and Iddir",
    )
    t1, t2 = st.tabs(["Branch Directory", "Register Branch"])

    with t1:
        x = df("""
            SELECT code AS Branch_Code, name AS Branch_Name,
                   module AS Module, location AS Location,
                   manager AS Manager, phone AS Phone, status AS Status
            FROM branches ORDER BY module,name
        """)
        st.dataframe(x, use_container_width=True, hide_index=True)
        if not x.empty:
            download(x, "idfs_branches.csv")

    with t2:
        with st.form("branch_form"):
            a, b = st.columns(2)
            code = a.text_input("Branch Code", placeholder="EQB-003")
            name = b.text_input("Branch Name")
            module = a.selectbox("Module", MODULES)
            location = b.text_input("Location")
            manager = a.text_input("Manager")
            phone = b.text_input("Phone")
            status = b.selectbox("Status", ["Active", "Inactive"])
            submitted = st.form_submit_button(
                "Register Branch", type="primary",
                use_container_width=True
            )
            if submitted:
                if not code.strip() or not name.strip():
                    st.error("Branch code and branch name are required.")
                else:
                    try:
                        sql(
                            """INSERT INTO branches
                            (code,name,module,location,manager,phone,status,created_at)
                            VALUES(?,?,?,?,?,?,?,?)""",
                            (code.strip(), name.strip(), module,
                             location.strip(), manager.strip(),
                             phone.strip(), status, now())
                        )
                        audit("Created branch", module, code.strip())
                        st.success("Branch registered.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Branch code already exists.")


# ============================================================
# MEMBER MANAGEMENT
# ============================================================

def member_page():
    header(
        "Module 5: Member Management",
        "Registration, regular contribution and membership monitoring",
    )
    t1, t2, t3 = st.tabs(
        ["Directory", "Register Member", "Member Profile"]
    )

    with t1:
        module_filter = st.selectbox("Module Filter", ["All"] + MODULES)
        base = """
            SELECT m.member_no AS Member_No, m.full_name AS Full_Name,
                   m.module AS Module, COALESCE(b.name,'') AS Branch,
                   COALESCE(m.phone,'') AS Phone, m.join_date AS Join_Date,
                   COALESCE(m.regular_contribution,0) AS Regular_Contribution,
                   COALESCE(m.trust_score,0.5) AS Trust_Score,
                   m.status AS Status
            FROM members m LEFT JOIN branches b ON m.branch_id=b.id
        """
        x = df(
            base + (" ORDER BY m.module,m.full_name"
                     if module_filter == "All"
                     else " WHERE m.module=? ORDER BY m.full_name"),
            () if module_filter == "All" else (module_filter,)
        )
        st.dataframe(x, use_container_width=True, hide_index=True)
        if not x.empty:
            download(x, "idfs_members.csv")

    with t2:
        with st.form("member_form"):
            a, b = st.columns(2)
            member_no = a.text_input("Member Number", placeholder="M-0001")
            full_name = b.text_input("Full Name")
            phone = a.text_input("Phone")
            sex = b.selectbox("Sex", ["Not specified", "Female", "Male", "Other"])
            module = a.selectbox("Module", MODULES)
            branch_list = branches(module)
            branch_options = [f"{q['code']} | {q['name']}" for q in branch_list]
            selected_branch = b.selectbox("Branch", branch_options) if branch_options else None
            contribution = a.number_input(
                "Regular Contribution / Monthly Amount (ETB)",
                min_value=0.0, value=0.0, step=50.0
            )
            trust_score = b.slider("Initial Trust Score", 0.0, 1.0, 0.5, 0.01)
            join_date = a.date_input("Join Date", date.today())
            status = b.selectbox("Status", ["Active", "Inactive", "Suspended"])
            address = a.text_input("Address")
            notes = b.text_area("Notes")
            submitted = st.form_submit_button(
                "Register Member", type="primary",
                use_container_width=True
            )
            if submitted:
                if not member_no.strip() or not full_name.strip():
                    st.error("Member number and full name are required.")
                else:
                    branch_id = None
                    if branch_options and selected_branch:
                        branch_id = branch_list[branch_options.index(selected_branch)]["id"]
                    try:
                        sql(
                            """INSERT INTO members
                            (member_no,full_name,phone,sex,join_date,module,branch_id,
                             regular_contribution,trust_score,status,address,notes,created_at)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (member_no.strip(), full_name.strip(), phone, sex,
                             str(join_date), module, branch_id, contribution,
                             trust_score, status, address, notes, now())
                        )
                        audit("Registered member", module, member_no.strip())
                        st.success("Member registered.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Member number already exists.")

    with t3:
        member_list = members()
        if not member_list:
            st.info("No members registered yet.")
        else:
            labels = [f"{q['member_no']} | {q['full_name']}" for q in member_list]
            selected = st.selectbox("Select Member", labels)
            member = member_list[labels.index(selected)]
            a, b, c = st.columns(3)
            a.metric("Module", member["module"])
            b.metric("Regular Contribution", money(member["regular_contribution"]))
            c.metric("Trust Score", f"{float(member['trust_score'] or .5):.2f}")
            profile = pd.DataFrame([{
                "Member Number": member["member_no"],
                "Full Name": member["full_name"],
                "Module": member["module"],
                "Branch": member["branch_name"] or "",
                "Phone": member["phone"] or "",
                "Join Date": member["join_date"] or "",
                "Status": member["status"],
                "Address": member["address"] or "",
                "Notes": member["notes"] or "",
            }])
            st.dataframe(profile, use_container_width=True, hide_index=True)


# ============================================================
# EQUb
# ============================================================

def probability_table():
    member_list = members("Equb")
    if not member_list:
        return pd.DataFrame()
    values = [max(float(q["regular_contribution"] or 0), 0) for q in member_list]
    total = sum(values)
    probabilities = (
        [1 / len(member_list)] * len(member_list)
        if total <= 0 else [v / total for v in values]
    )
    return pd.DataFrame([{
        "Member_No": q["member_no"],
        "Member": q["full_name"],
        "Regular_Contribution": values[i],
        "Trust_Score": float(q["trust_score"] or .5),
        "Probability": probabilities[i],
    } for i, q in enumerate(member_list)])


def equb():
    header(
        "Module 6: IDFS Equb",
        "Digital rotating savings, contributions, rounds and transparent selection",
    )
    tabs = st.tabs([
        "Overview", "Rounds", "Contributions",
        "Weighted Probability", "Draw History"
    ])
    with tabs[0]:
        equb_overview()
    with tabs[1]:
        equb_rounds()
    with tabs[2]:
        equb_contributions()
    with tabs[3]:
        equb_probability()
    with tabs[4]:
        equb_history()


def equb_overview():
    active_members = sql(
        "SELECT COUNT(*) AS n FROM members WHERE module='Equb' AND status='Active'",
        fetch=True
    )[0]["n"]
    total_contributions = sql(
        """SELECT COALESCE(SUM(amount),0) AS n FROM contributions
           WHERE module='Equb' AND status='Paid'""", fetch=True
    )[0]["n"]
    rounds = sql("SELECT COUNT(*) AS n FROM equb_rounds", fetch=True)[0]["n"]
    pools = sql(
        "SELECT COALESCE(SUM(total_pool),0) AS n FROM equb_rounds",
        fetch=True
    )[0]["n"]
    a, b, c, d = st.columns(4)
    a.metric("Active Members", active_members)
    b.metric("Total Contributions", money(total_contributions))
    c.metric("Rounds", rounds)
    d.metric("Recorded Pools", money(pools))
    st.markdown("""
    <div class="section-card">
        <div class="module-label">Equb Operating Model</div>
        Each Equb group or branch can define a regular contribution.
        Members make payments for rounds. The platform records the
        round pool and demonstrates a contribution-weighted selection
        model. Production governance can later add formal eligibility,
        independent randomization, approvals and reconciliation.
    </div>
    """, unsafe_allow_html=True)


def equb_rounds():
    st.subheader("Equb Round Management")
    branch_list = branches("Equb")
    if not branch_list:
        st.warning("Create an Equb branch first.")
        return
    names = [f"{q['code']} | {q['name']}" for q in branch_list]
    with st.form("round_form"):
        branch_choice = st.selectbox("Equb Branch", names)
        a, b = st.columns(2)
        round_no = a.number_input("Round Number", min_value=1, value=1, step=1)
        amount = b.number_input("Contribution per Member (ETB)", min_value=0.0, value=1000.0, step=100.0)
        expected_members = a.number_input("Expected Members", min_value=1, value=10, step=1)
        start_date = b.date_input("Start Date", date.today())
        draw_date = a.date_input("Expected Draw Date", date.today())
        status = b.selectbox("Status", ["Open", "Closed", "Completed", "Cancelled"])
        submitted = st.form_submit_button("Create Round", type="primary", use_container_width=True)
        if submitted:
            branch = branch_list[names.index(branch_choice)]
            try:
                sql(
                    """INSERT INTO equb_rounds
                    (branch_id,round_no,contribution_amount,start_date,draw_date,
                     expected_members,total_pool,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (branch["id"], int(round_no), amount, str(start_date),
                     str(draw_date), int(expected_members), 0, status, now())
                )
                audit("Created Equb round", "Equb", f"{branch['code']} round {round_no}")
                st.success("Round created.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("That round already exists for this branch.")
    x = df("""
        SELECT r.round_no AS Round_No, b.code AS Branch,
               r.contribution_amount AS Contribution,
               r.expected_members AS Expected_Members,
               r.total_pool AS Total_Pool, r.start_date AS Start_Date,
               r.draw_date AS Draw_Date, r.status AS Status,
               COALESCE(m.full_name,'') AS Winner
        FROM equb_rounds r JOIN branches b ON r.branch_id=b.id
        LEFT JOIN members m ON r.winner_member_id=m.id
        ORDER BY r.id DESC
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)


def equb_contributions():
    st.subheader("Equb Contribution Recording")
    rounds = sql("""
        SELECT r.*, b.code AS branch_code
        FROM equb_rounds r JOIN branches b ON r.branch_id=b.id
        WHERE r.status IN ('Open','Closed') ORDER BY r.id DESC
    """, fetch=True)
    if not rounds:
        st.info("Create an open Equb round first.")
        return
    labels = [
        f"{q['branch_code']} | Round {q['round_no']} | {money(q['contribution_amount'])}"
        for q in rounds
    ]
    with st.form("contribution_form"):
        round_choice = st.selectbox("Round", labels)
        current_round = rounds[labels.index(round_choice)]
        member_list = members("Equb", current_round["branch_id"])
        if not member_list:
            st.warning("No Equb members are registered in this branch.")
            st.form_submit_button("Record Contribution", disabled=True)
            return
        member_labels = [f"{q['member_no']} | {q['full_name']}" for q in member_list]
        member_choice = st.selectbox("Member", member_labels)
        amount = st.number_input(
            "Amount (ETB)", min_value=0.0,
            value=float(current_round["contribution_amount"] or 0),
            step=50.0
        )
        contribution_date = st.date_input("Contribution Date", date.today())
        payment_method = st.selectbox(
            "Payment Method",
            ["Cash", "Bank Transfer", "Mobile Money", "Other"]
        )
        reference = st.text_input("Payment Reference")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button(
            "Record Contribution", type="primary", use_container_width=True
        )
        if submitted:
            member = member_list[member_labels.index(member_choice)]
            try:
                sql(
                    """INSERT INTO contributions
                    (member_id,module,round_id,amount,contribution_date,status,
                     reference,payment_method,notes,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (member["id"], "Equb", current_round["id"], amount,
                     str(contribution_date), "Paid", reference,
                     payment_method, notes, now())
                )
                total = sql(
                    """SELECT COALESCE(SUM(amount),0) AS n FROM contributions
                       WHERE round_id=? AND status='Paid'""",
                    (current_round["id"],), fetch=True
                )[0]["n"]
                sql("UPDATE equb_rounds SET total_pool=? WHERE id=?",
                    (total, current_round["id"]))
                audit("Recorded Equb contribution", "Equb",
                      f"{member['member_no']} {amount}")
                st.success("Contribution recorded.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Contribution could not be recorded.")
    x = df("""
        SELECT c.contribution_date AS Date, m.member_no AS Member_No,
               m.full_name AS Member, b.code AS Branch,
               r.round_no AS Round, c.amount AS Amount,
               c.status AS Status, c.reference AS Reference,
               c.payment_method AS Payment_Method
        FROM contributions c JOIN members m ON c.member_id=m.id
        JOIN equb_rounds r ON c.round_id=r.id
        JOIN branches b ON r.branch_id=b.id
        WHERE c.module='Equb' ORDER BY c.id DESC LIMIT 500
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)
    if not x.empty:
        download(x, "idfs_equb_contributions.csv")


def equb_probability():
    st.subheader("Contribution-Weighted Probability Engine")
    x = probability_table()
    if x.empty:
        st.info("Register Equb members first.")
        return
    if x["Regular_Contribution"].sum() <= 0:
        st.warning("All regular contributions are zero; equal probabilities are used.")
    display = x.copy()
    display["Regular_Contribution"] = display["Regular_Contribution"].map(lambda v: f"{v:,.2f}")
    display["Trust_Score"] = display["Trust_Score"].map(lambda v: f"{v:.2f}")
    display["Probability"] = display["Probability"].map(lambda v: f"{v:.2%}")
    st.dataframe(display, use_container_width=True, hide_index=True)
    a, b = st.columns(2)
    a.metric("Total Regular Contribution", money(x["Regular_Contribution"].sum()))
    b.metric("Equb Members", len(x))
    if st.button("Run Weighted Demonstration", type="primary", use_container_width=True):
        member_list = members("Equb")
        selected = random.choices(member_list, weights=x["Probability"].tolist(), k=1)[0]
        st.success(
            f"Selected demonstration member: {selected['full_name']} ({selected['member_no']})"
        )
        audit("Executed weighted probability demonstration",
              "Equb", selected["member_no"])
    st.markdown("""
    <div class="section-card">
        <div class="module-label">Model Note</div>
        For member i, the demonstration probability is proportional
        to positive regular contribution Cᵢ: pᵢ = Cᵢ / ΣCⱼ.
        If all contributions are zero, equal probabilities are assigned.
        This is a research prototype and does not by itself define the
        governance rules of every Equb.
    </div>
    """, unsafe_allow_html=True)


def equb_history():
    x = df("""
        SELECT r.round_no AS Round_No, b.code AS Branch,
               r.total_pool AS Pool, r.draw_date AS Draw_Date,
               COALESCE(m.member_no,'') AS Winner_No,
               COALESCE(m.full_name,'') AS Winner, r.status AS Status
        FROM equb_rounds r JOIN branches b ON r.branch_id=b.id
        LEFT JOIN members m ON r.winner_member_id=m.id
        ORDER BY r.id DESC
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)
    if not x.empty:
        download(x, "idfs_equb_rounds.csv")


# ============================================================
# IDDIR
# ============================================================

def iddir():
    header(
        "Module 7: IDFS Iddir",
        "Community risk sharing for funeral, wedding, holiday, emergency and other approved needs",
    )
    tabs = st.tabs([
        "Overview", "Community Events", "Property Management",
        "Transactions", "Member History"
    ])
    with tabs[0]:
        iddir_overview()
    with tabs[1]:
        iddir_events()
    with tabs[2]:
        iddir_properties()
    with tabs[3]:
        iddir_transaction_view()
    with tabs[4]:
        iddir_history()


def iddir_overview():
    active_members = sql(
        "SELECT COUNT(*) AS n FROM members WHERE module='Iddir' AND status='Active'",
        fetch=True
    )[0]["n"]
    approved_benefits = sql(
        """SELECT COALESCE(SUM(approved_amount),0) AS n FROM iddir_events
           WHERE status IN ('Approved','Paid')""", fetch=True
    )[0]["n"]
    property_value = sql(
        "SELECT COALESCE(SUM(current_value),0) AS n FROM properties WHERE status='Active'",
        fetch=True
    )[0]["n"]
    pending_cases = sql(
        "SELECT COUNT(*) AS n FROM iddir_events WHERE status='Pending'",
        fetch=True
    )[0]["n"]
    a, b, c, d = st.columns(4)
    a.metric("Active Members", active_members)
    b.metric("Approved Support", money(approved_benefits))
    c.metric("Active Property Value", money(property_value))
    d.metric("Pending Cases", pending_cases)
    st.markdown("""
    <div class="section-card">
        <div class="module-label">Iddir Operating Scope</div>
        The platform records community support cases for funeral,
        wedding, holiday, emergency, medical, family and other
        approved purposes. It also maintains community and
        operational property such as land, buildings, vehicles,
        equipment and furniture.
    </div>
    """, unsafe_allow_html=True)


def iddir_events():
    st.subheader("Community Event and Benefit Management")
    member_list = members("Iddir")
    if not member_list:
        st.info("Register Iddir members first.")
        return
    member_labels = [f"{q['member_no']} | {q['full_name']}" for q in member_list]
    with st.form("iddir_event"):
        member_choice = st.selectbox("Member / Beneficiary", member_labels)
        event_type = st.selectbox("Event Type", EVENT_TYPES)
        event_date = st.date_input("Event Date", date.today())
        requested = st.number_input("Requested Amount (ETB)", min_value=0.0, value=0.0, step=100.0)
        approved = st.number_input("Approved Amount (ETB)", min_value=0.0, value=0.0, step=100.0)
        status = st.selectbox("Status", ["Pending", "Approved", "Rejected", "Paid"])
        reference = st.text_input("Case / Payment Reference")
        description = st.text_area("Description")
        submitted = st.form_submit_button(
            "Record Community Support Case",
            type="primary", use_container_width=True
        )
        if submitted:
            member = member_list[member_labels.index(member_choice)]
            payment_date = str(date.today()) if status == "Paid" else None
            sql(
                """INSERT INTO iddir_events
                (branch_id,event_type,member_id,event_date,description,
                 requested_amount,approved_amount,status,payment_date,reference,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (member["branch_id"], event_type, member["id"], str(event_date),
                 description, requested, approved, status, payment_date,
                 reference, now())
            )
            if status == "Paid" and approved > 0:
                sql(
                    """INSERT INTO transactions
                    (module,branch_id,member_id,transaction_type,amount,reference,
                     transaction_date,description,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    ("Iddir", member["branch_id"], member["id"],
                     "Community Benefit Payment", approved, reference,
                     str(event_date), event_type + " support", now())
                )
            audit("Recorded Iddir support case", "Iddir",
                  f"{event_type} for {member['member_no']}")
            st.success("Support case recorded.")
            st.rerun()
    x = df("""
        SELECT e.event_date AS Event_Date, e.event_type AS Event_Type,
               m.member_no AS Member_No, m.full_name AS Member,
               e.requested_amount AS Requested,
               e.approved_amount AS Approved, e.status AS Status,
               e.reference AS Reference, e.description AS Description
        FROM iddir_events e JOIN members m ON e.member_id=m.id
        ORDER BY e.id DESC
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)


def iddir_properties():
    st.subheader("Iddir Property Management")
    branch_list = branches("Iddir")
    if not branch_list:
        st.warning("Create an Iddir branch first.")
        return
    branch_names = [f"{q['code']} | {q['name']}" for q in branch_list]
    with st.form("property_form"):
        branch_choice = st.selectbox("Iddir Branch", branch_names)
        a, b = st.columns(2)
        property_code = a.text_input("Property Code", placeholder="PROP-001")
        property_type = b.selectbox("Property Type", PROPERTY_TYPES)
        description = a.text_input("Description")
        location = b.text_input("Location")
        acquisition_date = a.date_input("Acquisition Date", date.today())
        acquisition_cost = b.number_input("Acquisition Cost (ETB)", min_value=0.0, value=0.0, step=1000.0)
        current_value = a.number_input("Current Estimated Value (ETB)", min_value=0.0, value=0.0, step=1000.0)
        status = b.selectbox("Status", ["Active", "Under Maintenance", "Disposed", "Transferred"])
        custodian = a.text_input("Custodian")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button(
            "Register Property", type="primary", use_container_width=True
        )
        if submitted:
            if not property_code.strip():
                st.error("Property code is required.")
            else:
                branch = branch_list[branch_names.index(branch_choice)]
                try:
                    sql(
                        """INSERT INTO properties
                        (branch_id,property_code,property_type,description,location,
                         acquisition_date,acquisition_cost,current_value,status,custodian,notes,created_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (branch["id"], property_code.strip(), property_type,
                         description, location, str(acquisition_date),
                         acquisition_cost, current_value, status, custodian,
                         notes, now())
                    )
                    audit("Registered Iddir property", "Iddir", property_code.strip())
                    st.success("Property registered.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Property code already exists.")
    x = df("""
        SELECT p.property_code AS Property_Code, p.property_type AS Property_Type,
               p.description AS Description, COALESCE(b.name,'') AS Branch,
               p.location AS Location, p.acquisition_date AS Acquisition_Date,
               p.acquisition_cost AS Acquisition_Cost, p.current_value AS Current_Value,
               p.status AS Status, p.custodian AS Custodian
        FROM properties p LEFT JOIN branches b ON p.branch_id=b.id
        ORDER BY p.id DESC
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)
    if not x.empty:
        download(x, "idfs_iddir_properties.csv")


def iddir_transaction_view():
    x = df("""
        SELECT transaction_date AS Date, transaction_type AS Type,
               amount AS Amount, reference AS Reference,
               description AS Description
        FROM transactions WHERE module='Iddir' ORDER BY id DESC
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)


def iddir_history():
    x = df("""
        SELECT e.event_date AS Date, e.event_type AS Event,
               m.member_no AS Member_No, m.full_name AS Member,
               e.requested_amount AS Requested, e.approved_amount AS Approved,
               e.status AS Status, e.reference AS Reference
        FROM iddir_events e JOIN members m ON e.member_id=m.id
        ORDER BY e.id DESC
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)


# ============================================================
# TRANSACTIONS
# ============================================================

def transactions():
    header(
        "Module 8: Transactions",
        "Unified financial transaction register for the prototype",
    )
    with st.form("transaction_form"):
        a, b = st.columns(2)
        module = a.selectbox("Module", MODULES)
        transaction_type = b.selectbox(
            "Transaction Type",
            ["Deposit", "Contribution", "Community Benefit Payment", "Adjustment", "Other"]
        )
        amount = a.number_input("Amount (ETB)", min_value=0.0, value=0.0, step=100.0)
        reference = b.text_input("Reference")
        transaction_date = a.date_input("Transaction Date", date.today())
        description = b.text_area("Description")
        submitted = st.form_submit_button(
            "Record Transaction", type="primary", use_container_width=True
        )
        if submitted:
            sql(
                """INSERT INTO transactions
                (module,transaction_type,amount,reference,transaction_date,description,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (module, transaction_type, amount, reference,
                 str(transaction_date), description, now())
            )
            audit("Recorded transaction", module, f"{transaction_type}: {amount}")
            st.success("Transaction recorded.")
            st.rerun()
    x = df("""
        SELECT transaction_date AS Date, module AS Module,
               transaction_type AS Type, amount AS Amount,
               reference AS Reference, description AS Description
        FROM transactions ORDER BY id DESC LIMIT 1000
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)
    if not x.empty:
        download(x, "idfs_transactions.csv")


# ============================================================
# REPORTS
# ============================================================

def reports():
    header(
        "Module 9: Reports and Analytics",
        "Management information for the IDFS technology-transfer prototype",
    )
    report_type = st.selectbox(
        "Report",
        [
            "Module Summary", "Equb Contributions", "Equb Rounds",
            "Equb Probability", "Iddir Community Support",
            "Iddir Properties", "Transactions"
        ]
    )

    if report_type == "Module Summary":
        query = """
            SELECT module AS Module, COUNT(*) AS Members,
                   ROUND(AVG(regular_contribution),2) AS Average_Regular_Contribution,
                   ROUND(AVG(trust_score),3) AS Average_Trust
            FROM members WHERE status='Active' GROUP BY module
        """
    elif report_type == "Equb Contributions":
        query = """
            SELECT m.member_no AS Member_No, m.full_name AS Member,
                   COUNT(c.id) AS Payments,
                   COALESCE(SUM(c.amount),0) AS Total_Paid
            FROM members m LEFT JOIN contributions c
              ON m.id=c.member_id AND c.module='Equb' AND c.status='Paid'
            WHERE m.module='Equb' GROUP BY m.id ORDER BY Total_Paid DESC
        """
    elif report_type == "Equb Rounds":
        query = """
            SELECT r.round_no AS Round_No, b.code AS Branch,
                   r.contribution_amount AS Contribution,
                   r.expected_members AS Members, r.total_pool AS Total_Pool,
                   r.start_date AS Start_Date, r.draw_date AS Draw_Date,
                   r.status AS Status, COALESCE(m.full_name,'') AS Winner
            FROM equb_rounds r JOIN branches b ON r.branch_id=b.id
            LEFT JOIN members m ON r.winner_member_id=m.id
            ORDER BY r.id DESC
        """
    elif report_type == "Equb Probability":
        x = probability_table()
        if x.empty:
            st.info("Register Equb members first.")
        else:
            st.dataframe(x, use_container_width=True, hide_index=True)
            download(x, "idfs_equb_probability.csv")
        return
    elif report_type == "Iddir Community Support":
        query = """
            SELECT event_type AS Event_Type, COUNT(*) AS Cases,
                   COALESCE(SUM(requested_amount),0) AS Requested,
                   COALESCE(SUM(approved_amount),0) AS Approved
            FROM iddir_events GROUP BY event_type ORDER BY Approved DESC
        """
    elif report_type == "Iddir Properties":
        query = """
            SELECT property_type AS Property_Type, COUNT(*) AS Assets,
                   COALESCE(SUM(acquisition_cost),0) AS Acquisition_Cost,
                   COALESCE(SUM(current_value),0) AS Current_Value
            FROM properties GROUP BY property_type ORDER BY Current_Value DESC
        """
    else:
        query = """
            SELECT module AS Module, transaction_type AS Transaction_Type,
                   COUNT(*) AS Transactions,
                   COALESCE(SUM(amount),0) AS Total_Amount
            FROM transactions GROUP BY module,transaction_type
            ORDER BY module,Total_Amount DESC
        """

    x = df(query)
    st.dataframe(x, use_container_width=True, hide_index=True)
    if not x.empty:
        download(x, "idfs_report.csv")


# ============================================================
# AUDIT TRAIL
# ============================================================

def audit_page():
    header(
        "Module 10: Audit Trail",
        "Traceable record of important system activities",
    )
    x = df("""
        SELECT timestamp AS Timestamp, username AS Username,
               module AS Module, action AS Action, details AS Details
        FROM audit_log ORDER BY id DESC LIMIT 2000
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)
    if not x.empty:
        download(x, "idfs_audit.csv")


# ============================================================
# USER ADMINISTRATION
# ============================================================

def users_page():
    header(
        "Module 11: User Administration",
        "Role-based demonstration accounts",
    )
    x = df("""
        SELECT username AS Username, full_name AS Full_Name,
               role AS Role, module AS Module, active AS Active,
               created_at AS Created_At
        FROM users ORDER BY username
    """)
    st.dataframe(x, use_container_width=True, hide_index=True)

    with st.form("user_form"):
        a, b = st.columns(2)
        username = a.text_input("Username")
        full_name = b.text_input("Full Name")
        password = a.text_input("Password", type="password")
        role = b.selectbox("Role", ROLES)
        module = a.selectbox("Module", ["Portal"] + MODULES)
        branch_list = branches(module) if module in MODULES else []
        branch_options = ["No branch"] + [
            f"{q['code']} | {q['name']}" for q in branch_list
        ]
        branch_choice = b.selectbox("Branch", branch_options)
        submitted = st.form_submit_button(
            "Create User", type="primary", use_container_width=True
        )
        if submitted:
            if not username.strip():
                st.error("Username is required.")
            elif not full_name.strip():
                st.error("Full name is required.")
            elif len(password) < 6:
                st.error("Password must contain at least six characters.")
            else:
                branch_id = None
                if branch_choice != "No branch":
                    branch_id = branch_list[
                        branch_options.index(branch_choice) - 1
                    ]["id"]
                try:
                    sql(
                        """INSERT INTO users
                        (username,password_hash,full_name,role,module,branch_id,active,created_at)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (username.strip(), pwd_hash(password),
                         full_name.strip(), role, module, branch_id, 1, now())
                    )
                    audit("Created user", "Portal", username.strip())
                    st.success("User created.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    init_db()

    if not st.session_state.get("authenticated", False):
        login()
        return

    with st.sidebar:
        st.markdown("## 🏦 IDFS")
        st.caption("Indigenous Digital Financial System")
        st.write(f"**User:** {st.session_state.get('full_name','')}")
        st.write(f"**Role:** {st.session_state.get('role','')}")

        if st.button("Sign out", use_container_width=True):
            audit("Logout")
            st.session_state.clear()
            st.rerun()

        st.divider()

        navigation = [
            "Dashboard",
            "Branch Management",
            "Member Management",
            "IDFS Equb",
            "IDFS Iddir",
            "Transactions",
            "Reports and Analytics",
            "Audit Trail",
        ]
        if st.session_state.get("role") == "Administrator":
            navigation.append("User Administration")

        page = st.radio("Navigation", navigation)

        st.divider()
        st.caption("Aksum University")
        st.caption("Technology Transfer Project Team • 2026")

    pages = {
        "Dashboard": dashboard,
        "Branch Management": branch_page,
        "Member Management": member_page,
        "IDFS Equb": equb,
        "IDFS Iddir": iddir,
        "Transactions": transactions,
        "Reports and Analytics": reports,
        "Audit Trail": audit_page,
        "User Administration": users_page,
    }
    pages[page]()


if __name__ == "__main__":
    main()
