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
# IDFS WEB PLATFORM
# Indigenous Digital Financial System
#
# Enhanced Demonstration Version
#
# Modules:
# 1. Executive Dashboard
# 2. Branch Management
# 3. Member Management
# 4. IDFS Equb
# 5. IDFS Iddir
# 6. Transactions
# 7. Reports and Analytics
# 8. Manuals
# 9. Audit Trail
# 10. User Administration
#
# Equb statistical model:
# - Planned contribution
# - Historical paid contribution
# - Payment consistency
# - Fixed contribution weights
# - Fixed trust weight
# - Trust-adjusted score
# - Normalized selection probability
# - Monte Carlo demonstration
#
# IMPORTANT:
# This is a demonstration/prototype system.
# Actual financial, legal, governance and community rules
# must be approved by the relevant Equb/Iddir organization.
# ============================================================


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IDFS Web Platform",
    page_icon="IDFS",
    layout="wide",
    initial_sidebar_state="expanded",
)


DB = Path("idfs_demo.db")

MODULES = ["Equb", "Iddir"]

ROLES = [
    "Administrator",
    "Branch Manager",
    "Finance Officer",
    "Member",
]

EVENT_TYPES = [
    "Funeral",
    "Wedding",
    "Holiday",
    "Emergency",
    "Medical Support",
    "Family Support",
    "Other",
]

PROPERTY_TYPES = [
    "Land",
    "Building",
    "Vehicle",
    "Equipment",
    "Furniture",
    "Office Asset",
    "Other",
]


# ============================================================
# APPLICATION STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #163A5F;
        margin-bottom: 0.15rem;
    }

    .sub-title {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }

    .section-card {
        padding: 1.1rem 1.3rem;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background: #F8FAFC;
        margin-bottom: 1rem;
    }

    .module-label {
        color: #0B5CAD;
        font-weight: 700;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .manual-card {
        padding: 1.2rem 1.4rem;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        background: white;
        margin-bottom: 1rem;
    }

    .warning-card {
        padding: 1rem 1.2rem;
        border-left: 5px solid #C89B3C;
        background: #FFFBEB;
        margin-bottom: 1rem;
    }

    .footer-note {
        text-align: center;
        color: #64748B;
        font-size: 0.78rem;
        margin-top: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COMMON FUNCTIONS
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

        return hmac.compare_digest(
            calculated,
            stored_hash,
        )

    except Exception:
        return False


def audit(action, module="Portal", details=""):
    try:
        username = st.session_state.get(
            "username",
            "anonymous",
        )

        sql(
            """
            INSERT INTO audit_log
            (username,module,action,details,timestamp)
            VALUES(?,?,?,?,?)
            """,
            (
                username,
                module,
                action,
                details,
                now(),
            ),
        )

    except Exception:
        pass


def table_exists(table_name):
    row = sql(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (table_name,),
        fetch=True,
    )

    return bool(row)


def existing_columns(table_name):
    if not table_exists(table_name):
        return set()

    return {
        row["name"]
        for row in sql(
            f"PRAGMA table_info({table_name})",
            fetch=True,
        )
    }


def ensure_column(table_name, column, definition):
    if column not in existing_columns(table_name):
        sql(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column} {definition}"
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


def download(data, filename):
    st.download_button(
        "Download CSV",
        data.to_csv(index=False).encode("utf-8"),
        filename,
        "text/csv",
        use_container_width=True,
    )


# ============================================================
# DATABASE
# ============================================================

def init_db():

    c = conn()

    c.executescript(
        """

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

        """
    )

    c.commit()
    c.close()

    migrations = {

        "members": {
            "regular_contribution": "REAL DEFAULT 0",
            "contribution_frequency": "TEXT DEFAULT 'Monthly'",
            "target_round_contribution": "REAL DEFAULT 0",
            "trust_score": "REAL DEFAULT 0.5",
            "status": "TEXT DEFAULT 'Active'",
            "address": "TEXT",
            "notes": "TEXT",
            "created_at": "TEXT",
        },

        "equb_rounds": {
            "branch_id": "INTEGER",
            "round_no": "INTEGER",
            "contribution_amount": "REAL DEFAULT 0",
            "start_date": "TEXT",
            "draw_date": "TEXT",
            "expected_members": "INTEGER DEFAULT 0",
            "total_pool": "REAL DEFAULT 0",
            "winner_member_id": "INTEGER",
            "status": "TEXT DEFAULT 'Open'",
            "created_at": "TEXT",
        },

        "contributions": {
            "member_id": "INTEGER",
            "module": "TEXT",
            "round_id": "INTEGER",
            "amount": "REAL DEFAULT 0",
            "contribution_date": "TEXT",
            "status": "TEXT DEFAULT 'Paid'",
            "reference": "TEXT",
            "payment_method": "TEXT",
            "notes": "TEXT",
            "created_at": "TEXT",
        },

        "users": {
            "password_hash": "TEXT",
            "full_name": "TEXT",
            "role": "TEXT",
            "module": "TEXT",
            "branch_id": "INTEGER",
            "active": "INTEGER DEFAULT 1",
            "created_at": "TEXT",
        },

        "branches": {
            "code": "TEXT",
            "name": "TEXT",
            "module": "TEXT",
            "location": "TEXT",
            "manager": "TEXT",
            "phone": "TEXT",
            "status": "TEXT DEFAULT 'Active'",
            "created_at": "TEXT",
        },

        "iddir_events": {
            "branch_id": "INTEGER",
            "event_type": "TEXT",
            "member_id": "INTEGER",
            "event_date": "TEXT",
            "description": "TEXT",
            "requested_amount": "REAL DEFAULT 0",
            "approved_amount": "REAL DEFAULT 0",
            "status": "TEXT DEFAULT 'Pending'",
            "payment_date": "TEXT",
            "reference": "TEXT",
            "created_at": "TEXT",
        },

        "properties": {
            "branch_id": "INTEGER",
            "property_code": "TEXT",
            "property_type": "TEXT",
            "description": "TEXT",
            "location": "TEXT",
            "acquisition_date": "TEXT",
            "acquisition_cost": "REAL DEFAULT 0",
            "current_value": "REAL DEFAULT 0",
            "status": "TEXT DEFAULT 'Active'",
            "custodian": "TEXT",
            "notes": "TEXT",
            "created_at": "TEXT",
        },

        "transactions": {
            "module": "TEXT",
            "branch_id": "INTEGER",
            "member_id": "INTEGER",
            "transaction_type": "TEXT",
            "amount": "REAL DEFAULT 0",
            "reference": "TEXT",
            "transaction_date": "TEXT",
            "description": "TEXT",
            "created_at": "TEXT",
        },

        "audit_log": {
            "username": "TEXT",
            "module": "TEXT",
            "action": "TEXT",
            "details": "TEXT",
            "timestamp": "TEXT",
        },
    }

    for table, columns in migrations.items():
        for column, definition in columns.items():
            ensure_column(
                table,
                column,
                definition,
            )

    indexes = [

        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_users_username ON users(username)",

        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_branches_code ON branches(code)",

        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_members_member_no ON members(member_no)",

        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_properties_code ON properties(property_code)",

        "CREATE INDEX IF NOT EXISTS "
        "idx_members_module_branch ON members(module,branch_id)",

        "CREATE INDEX IF NOT EXISTS "
        "idx_contributions_round ON contributions(round_id)",

        "CREATE INDEX IF NOT EXISTS "
        "idx_contributions_member ON contributions(member_id)",
    ]

    for statement in indexes:
        try:
            sql(statement)
        except sqlite3.IntegrityError:
            pass

    # --------------------------------------------------------
    # DEFAULT ADMINISTRATOR
    # --------------------------------------------------------

    admin = sql(
        "SELECT id FROM users WHERE username=?",
        ("admin",),
        fetch=True,
    )

    if not admin:

        sql(
            """
            INSERT INTO users
            (
                username,
                password_hash,
                full_name,
                role,
                module,
                branch_id,
                active,
                created_at
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                "admin",
                pwd_hash("admin123"),
                "IDFS Administrator",
                "Administrator",
                "Portal",
                None,
                1,
                now(),
            ),
        )

    # --------------------------------------------------------
    # DEFAULT BRANCHES
    # --------------------------------------------------------

    seed = [

        (
            "EQB-001",
            "IDFS Equb Central Branch",
            "Equb",
            "Aksum",
            "Branch Manager",
        ),

        (
            "EQB-002",
            "IDFS Equb North Branch",
            "Equb",
            "Shire",
            "Branch Manager",
        ),

        (
            "IDR-001",
            "IDFS Iddir Central Branch",
            "Iddir",
            "Aksum",
            "Branch Manager",
        ),

        (
            "IDR-002",
            "IDFS Iddir Community Branch",
            "Iddir",
            "Shire",
            "Branch Manager",
        ),
    ]

    for code, name, module, location, manager in seed:

        exists = sql(
            "SELECT id FROM branches WHERE code=?",
            (code,),
            fetch=True,
        )

        if not exists:

            sql(
                """
                INSERT INTO branches
                (
                    code,
                    name,
                    module,
                    location,
                    manager,
                    phone,
                    status,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    code,
                    name,
                    module,
                    location,
                    manager,
                    "",
                    "Active",
                    now(),
                ),
            )


# ============================================================
# BRANCH HELPERS
# ============================================================

def branches(module=None):

    if module:

        return sql(
            """
            SELECT *
            FROM branches
            WHERE module=?
            ORDER BY name
            """,
            (module,),
            fetch=True,
        )

    return sql(
        """
        SELECT *
        FROM branches
        ORDER BY module,name
        """,
        fetch=True,
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

    where_sql = (
        " WHERE " + " AND ".join(where)
        if where
        else ""
    )

    return sql(
        """
        SELECT
            m.*,
            b.code AS branch_code,
            b.name AS branch_name
        FROM members m
        LEFT JOIN branches b
            ON m.branch_id=b.id
        """
        + where_sql
        + " ORDER BY m.full_name",
        tuple(params),
        fetch=True,
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def login():

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:40px;
            margin-bottom:30px;
        ">
            <h1>IDFS</h1>
            <p>Indigenous Digital Financial System</p>
            <p>Secure Web Platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 2, 1])

    with center:

        st.markdown("### Sign in")

        with st.form("login_form"):

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            row = sql(
                """
                SELECT *
                FROM users
                WHERE username=?
                AND active=1
                """,
                (username.strip(),),
                fetch=True,
            )

            if row and check_pwd(
                password,
                row[0]["password_hash"],
            ):

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

                st.error(
                    "Invalid username or password."
                )

        st.info(
            "Demonstration account: admin / admin123"
        )


# ============================================================
# EQUb STATISTICAL ENGINE
# ============================================================

def member_contribution_history(
    member_id,
    round_id=None,
):

    where = [
        "c.member_id=?",
        "c.module='Equb'",
    ]

    params = [member_id]

    if round_id is not None:

        where.append(
            "c.round_id=?"
        )

        params.append(round_id)

    return df(
        f"""
        SELECT
            c.id AS Contribution_ID,
            c.round_id AS Round_ID,
            COALESCE(r.round_no,0) AS Round_No,
            c.amount AS Amount,
            c.contribution_date AS Date,
            c.status AS Status,

            CASE
                WHEN COALESCE(
                    r.contribution_amount,0
                ) > 0
                THEN MIN(
                    c.amount /
                    r.contribution_amount,
                    1.0
                )
                ELSE 0
            END AS Payment_Rate,

            c.payment_method AS Payment_Method,
            c.reference AS Reference

        FROM contributions c

        LEFT JOIN equb_rounds r
            ON c.round_id=r.id

        WHERE {' AND '.join(where)}

        ORDER BY c.id DESC
        """,
        tuple(params),
    )


def equb_probability_table(
    round_id=None,
    planned_weight=0.50,
    paid_weight=0.30,
    consistency_weight=0.20,
    trust_weight=0.20,
):

    member_list = members("Equb")

    if not member_list:
        return pd.DataFrame()

    rows = []

    for m in member_list:

        hist = member_contribution_history(
            m["id"],
            round_id,
        )

        planned = float(
            m["target_round_contribution"]
            or m["regular_contribution"]
            or 0
        )

        total_paid = (
            float(hist["Amount"].sum())
            if not hist.empty
            else 0.0
        )

        if not hist.empty:

            consistency = float(
                hist["Payment_Rate"].mean()
            )

            rounds_paid = int(
                (hist["Status"] == "Paid").sum()
            )

        else:

            consistency = 0.0
            rounds_paid = 0

        rows.append(
            {
                "Member_ID": m["id"],
                "Member_No": m["member_no"],
                "Member": m["full_name"],
                "Planned_Contribution": planned,
                "Total_Paid": total_paid,
                "Payment_Consistency": consistency,
                "Rounds_Paid": rounds_paid,
                "Trust_Score": float(
                    m["trust_score"] or 0.5
                ),
            }
        )

    x = pd.DataFrame(rows)

    def normalize(s):

        s = pd.to_numeric(
            s,
            errors="coerce",
        ).fillna(0)

        total = s.sum()

        if total > 0:
            return s / total

        return pd.Series(
            [1 / len(s)] * len(s),
            index=s.index,
        )

    x["Planned_Share"] = normalize(
        x["Planned_Contribution"]
    )

    x["Paid_Share"] = normalize(
        x["Total_Paid"]
    )

    # --------------------------------------------------------
    # WEIGHTED CONTRIBUTION SCORE
    # --------------------------------------------------------

    x["Contribution_Weighted_Mean"] = (

        planned_weight
        * x["Planned_Share"]

        + paid_weight
        * x["Paid_Share"]

        + consistency_weight
        * x["Payment_Consistency"]
    )

    # --------------------------------------------------------
    # TRUST-ADJUSTED SCORE
    # --------------------------------------------------------

    x["Adjusted_Score"] = (

        (1 - trust_weight)
        * x["Contribution_Weighted_Mean"]

        + trust_weight
        * x["Trust_Score"]
    )

    score_total = x["Adjusted_Score"].sum()

    if score_total > 0:

        x["Probability"] = (
            x["Adjusted_Score"]
            / score_total
        )

    else:

        x["Probability"] = (
            1 / len(x)
        )

    x["Cumulative_Probability"] = (
        x["Probability"].cumsum()
    )

    return (
        x.sort_values(
            "Probability",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# ============================================================
# MODULE 1: EXECUTIVE DASHBOARD
# ============================================================

def dashboard():

    header(
        "IDFS Executive Dashboard",
        "Integrated Equb savings, contribution analytics and Iddir community risk-sharing platform",
    )

    active_members = sql(
        """
        SELECT COUNT(*) AS n
        FROM members
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    active_branches = sql(
        """
        SELECT COUNT(*) AS n
        FROM branches
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    equb_savings = sql(
        """
        SELECT COALESCE(SUM(amount),0) AS n
        FROM contributions
        WHERE module='Equb'
        AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    iddir_property = sql(
        """
        SELECT COALESCE(SUM(current_value),0) AS n
        FROM properties
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric(
        "Active Members",
        active_members,
    )

    b.metric(
        "Active Branches",
        active_branches,
    )

    c.metric(
        "Equb Savings",
        money(equb_savings),
    )

    d.metric(
        "Iddir Property Value",
        money(iddir_property),
    )

    st.divider()

    x, y = st.columns(2)

    with x:

        st.markdown(
            """
            <div class="section-card">

            <div class="module-label">
            IDFS Equb
            </div>

            Digital rotating savings with:

            <ul>
            <li>Member contribution plans</li>
            <li>Monthly or round contributions</li>
            <li>Contribution history</li>
            <li>Payment consistency</li>
            <li>Weighted contribution score</li>
            <li>Trust-adjusted probability</li>
            <li>Transparent statistical demonstration</li>
            </ul>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with y:

        st.markdown(
            """
            <div class="section-card">

            <div class="module-label">
            IDFS Iddir
            </div>

            Community risk-sharing system covering:

            <ul>
            <li>Funeral support</li>
            <li>Emergency support</li>
            <li>Medical support</li>
            <li>Family support</li>
            <li>Community events</li>
            <li>Property management</li>
            <li>Benefit and transaction records</li>
            </ul>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader(
        "Equb Statistical Indicators"
    )

    p = equb_probability_table()

    if not p.empty:

        a, b, c, d = st.columns(4)

        a.metric(
            "Equb Members",
            len(p),
        )

        b.metric(
            "Planned Contribution",
            money(
                p[
                    "Planned_Contribution"
                ].sum()
            ),
        )

        c.metric(
            "Actual Paid",
            money(
                p[
                    "Total_Paid"
                ].sum()
            ),
        )

        d.metric(
            "Average Payment Rate",
            f"{p['Payment_Consistency'].mean():.1%}",
        )

    st.subheader(
        "Recent Activity"
    )

    activity = df(
        """
        SELECT
            timestamp AS Timestamp,
            username AS User,
            module AS Module,
            action AS Action,
            details AS Details
        FROM audit_log
        ORDER BY id DESC
        LIMIT 15
        """
    )

    if activity.empty:
        st.info(
            "No activity has been recorded yet."
        )

    else:

        st.dataframe(
            activity,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# MODULE 2: BRANCH MANAGEMENT
# ============================================================

def branch_page():

    header(
        "Module 2: Branch Management",
        "Bank-style branch structure for Equb and Iddir",
    )

    t1, t2 = st.tabs(
        [
            "Branch Directory",
            "Register Branch",
        ]
    )

    with t1:

        x = df(
            """
            SELECT
                code AS Branch_Code,
                name AS Branch_Name,
                module AS Module,
                location AS Location,
                manager AS Manager,
                phone AS Phone,
                status AS Status
            FROM branches
            ORDER BY module,name
            """
        )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        if not x.empty:
            download(
                x,
                "idfs_branches.csv",
            )

    with t2:

        with st.form("branch_form"):

            a, b = st.columns(2)

            code = a.text_input(
                "Branch Code",
                placeholder="EQB-003",
            )

            name = b.text_input(
                "Branch Name"
            )

            module = a.selectbox(
                "Module",
                MODULES,
            )

            location = b.text_input(
                "Location"
            )

            manager = a.text_input(
                "Manager"
            )

            phone = b.text_input(
                "Phone"
            )

            status = b.selectbox(
                "Status",
                [
                    "Active",
                    "Inactive",
                ],
            )

            submitted = st.form_submit_button(
                "Register Branch",
                type="primary",
                use_container_width=True,
            )

            if submitted:

                if (
                    not code.strip()
                    or not name.strip()
                ):

                    st.error(
                        "Branch code and branch name are required."
                    )

                else:

                    try:

                        sql(
                            """
                            INSERT INTO branches
                            (
                                code,
                                name,
                                module,
                                location,
                                manager,
                                phone,
                                status,
                                created_at
                            )
                            VALUES(?,?,?,?,?,?,?,?)
                            """,
                            (
                                code.strip(),
                                name.strip(),
                                module,
                                location.strip(),
                                manager.strip(),
                                phone.strip(),
                                status,
                                now(),
                            ),
                        )

                        audit(
                            "Created branch",
                            module,
                            code.strip(),
                        )

                        st.success(
                            "Branch registered."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Branch code already exists."
                        )


# ============================================================
# MODULE 3: MEMBER MANAGEMENT
# ============================================================

def member_page():

    header(
        "Module 3: Member Management",
        "Member registration, contribution planning and profile management",
    )

    t1, t2, t3 = st.tabs(
        [
            "Directory",
            "Register Member",
            "Member Profile",
        ]
    )

    with t1:

        module_filter = st.selectbox(
            "Module Filter",
            ["All"] + MODULES,
        )

        base_query = """
            SELECT
                m.member_no AS Member_No,
                m.full_name AS Full_Name,
                m.module AS Module,
                COALESCE(b.name,'') AS Branch,
                COALESCE(m.phone,'') AS Phone,
                m.join_date AS Join_Date,
                COALESCE(
                    m.regular_contribution,0
                ) AS Planned_Contribution,
                COALESCE(
                    m.contribution_frequency,
                    'Monthly'
                ) AS Frequency,
                COALESCE(
                    m.target_round_contribution,0
                ) AS Round_Contribution,
                COALESCE(
                    m.trust_score,0.5
                ) AS Trust_Score,
                m.status AS Status

            FROM members m

            LEFT JOIN branches b
                ON m.branch_id=b.id
        """

        if module_filter == "All":

            x = df(
                base_query
                + " ORDER BY m.module,m.full_name"
            )

        else:

            x = df(
                base_query
                + """
                WHERE m.module=?
                ORDER BY m.full_name
                """,
                (module_filter,),
            )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        if not x.empty:

            download(
                x,
                "idfs_members.csv",
            )

    with t2:

        with st.form("member_form"):

            a, b = st.columns(2)

            member_no = a.text_input(
                "Member Number",
                placeholder="M-0001",
            )

            full_name = b.text_input(
                "Full Name"
            )

            phone = a.text_input(
                "Phone"
            )

            sex = b.selectbox(
                "Sex",
                [
                    "Not specified",
                    "Female",
                    "Male",
                    "Other",
                ],
            )

            module = a.selectbox(
                "Module",
                MODULES,
            )

            branch_list = branches(
                module
            )

            branch_options = [
                f"{item['code']} | "
                f"{item['name']}"
                for item in branch_list
            ]

            if branch_options:

                selected_branch = b.selectbox(
                    "Branch",
                    branch_options,
                )

            else:

                selected_branch = None

                b.info(
                    "No branch exists for this module yet."
                )

            st.markdown(
                "#### Contribution Plan"
            )

            c1, c2, c3 = st.columns(3)

            contribution = c1.number_input(
                "Regular Contribution Amount (ETB)",
                min_value=0.0,
                value=(
                    1000.0
                    if module == "Equb"
                    else 0.0
                ),
                step=50.0,
            )

            frequency = c2.selectbox(
                "Contribution Frequency",
                [
                    "Monthly",
                    "Per Round",
                    "Weekly",
                    "Custom",
                ],
            )

            round_contribution = c3.number_input(
                "Target Round Contribution (ETB)",
                min_value=0.0,
                value=0.0,
                step=50.0,
                help=(
                    "Expected contribution for "
                    "one Equb round. If zero, "
                    "the regular contribution "
                    "is used."
                ),
            )

            # ------------------------------------------------
            # FIXED SCORE INPUT
            # ------------------------------------------------

            st.markdown(
                "#### Initial Trust Score"
            )

            trust_score_rate = st.number_input(
                "Initial Trust Score Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
                step=1.0,
                format="%.0f",
                help=(
                    "Enter the initial trust score "
                    "as a fixed percentage. "
                    "Example: 50 means 0.50."
                ),
            )

            trust_score = (
                trust_score_rate / 100.0
            )

            join_date = a.date_input(
                "Join Date",
                date.today(),
            )

            status = b.selectbox(
                "Status",
                [
                    "Active",
                    "Inactive",
                    "Suspended",
                ],
            )

            address = a.text_input(
                "Address"
            )

            notes = b.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Register Member",
                type="primary",
                use_container_width=True,
            )

            if submitted:

                if (
                    not member_no.strip()
                    or not full_name.strip()
                ):

                    st.error(
                        "Member number and full name are required."
                    )

                else:

                    branch_id = None

                    if (
                        branch_options
                        and selected_branch
                    ):

                        branch_id = (
                            branch_list[
                                branch_options.index(
                                    selected_branch
                                )
                            ]["id"]
                        )

                    try:

                        sql(
                            """
                            INSERT INTO members
                            (
                                member_no,
                                full_name,
                                phone,
                                sex,
                                join_date,
                                module,
                                branch_id,
                                regular_contribution,
                                contribution_frequency,
                                target_round_contribution,
                                trust_score,
                                status,
                                address,
                                notes,
                                created_at
                            )
                            VALUES(
                                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                            )
                            """,
                            (
                                member_no.strip(),
                                full_name.strip(),
                                phone,
                                sex,
                                str(join_date),
                                module,
                                branch_id,
                                contribution,
                                frequency,
                                round_contribution,
                                trust_score,
                                status,
                                address,
                                notes,
                                now(),
                            ),
                        )

                        audit(
                            "Registered member",
                            module,
                            member_no.strip(),
                        )

                        st.success(
                            "Member registered."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Member number already exists."
                        )

    with t3:

        member_list = members()

        if not member_list:

            st.info(
                "No members registered yet."
            )

            return

        labels = [
            f"{item['member_no']} | "
            f"{item['full_name']}"
            for item in member_list
        ]

        selected = st.selectbox(
            "Select Member",
            labels,
        )

        member = member_list[
            labels.index(selected)
        ]

        history = member_contribution_history(
            member["id"]
        )

        a, b, c, d = st.columns(4)

        a.metric(
            "Module",
            member["module"],
        )

        b.metric(
            "Planned Contribution",
            money(
                member[
                    "regular_contribution"
                ]
            ),
        )

        c.metric(
            "Total Paid",
            money(
                history["Total_Paid"].sum()
                if not history.empty
                else 0
            ),
        )

        d.metric(
            "Trust Score",
            f"{float(member['trust_score'] or 0):.0%}",
        )

        profile = pd.DataFrame(
            [
                {
                    "Member Number":
                        member["member_no"],

                    "Full Name":
                        member["full_name"],

                    "Module":
                        member["module"],

                    "Branch":
                        member["branch_name"] or "",

                    "Phone":
                        member["phone"] or "",

                    "Join Date":
                        member["join_date"] or "",

                    "Frequency":
                        member[
                            "contribution_frequency"
                        ] or "Monthly",

                    "Planned Contribution":
                        member[
                            "regular_contribution"
                        ] or 0,

                    "Target Round Contribution":
                        member[
                            "target_round_contribution"
                        ] or 0,

                    "Trust Score":
                        f"{float(member['trust_score'] or 0):.2%}",

                    "Status":
                        member["status"],
                }
            ]
        )

        st.dataframe(
            profile,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader(
            "Contribution History"
        )

        if history.empty:

            st.info(
                "No contribution records yet."
            )

        else:

            st.dataframe(
                history,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# MODULE 4: IDFS EQUB
# ============================================================

def equb():

    header(
        "Module 4: IDFS Equb",
        "Digital rotating savings, member contributions, rounds and transparent statistical selection",
    )

    tabs = st.tabs(
        [
            "Overview",
            "Rounds",
            "Contributions",
            "Weighted Probability",
            "Simulation",
            "Draw History",
        ]
    )

    with tabs[0]:
        equb_overview()

    with tabs[1]:
        equb_rounds()

    with tabs[2]:
        equb_contributions()

    with tabs[3]:
        equb_probability()

    with tabs[4]:
        equb_simulation()

    with tabs[5]:
        equb_history()


def equb_overview():

    active_members = sql(
        """
        SELECT COUNT(*) AS n
        FROM members
        WHERE module='Equb'
        AND status='Active'
        """,
        fetch=True,
    )[0]["n"]

    total_contributions = sql(
        """
        SELECT COALESCE(SUM(amount),0) AS n
        FROM contributions
        WHERE module='Equb'
        AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    rounds = sql(
        """
        SELECT COUNT(*) AS n
        FROM equb_rounds
        """,
        fetch=True,
    )[0]["n"]

    pools = sql(
        """
        SELECT COALESCE(SUM(total_pool),0) AS n
        FROM equb_rounds
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric(
        "Active Members",
        active_members,
    )

    b.metric(
        "Total Contributions",
        money(total_contributions),
    )

    c.metric(
        "Rounds",
        rounds,
    )

    d.metric(
        "Recorded Pools",
        money(pools),
    )

    st.subheader(
        "Member Contribution Plan"
    )

    plan = df(
        """
        SELECT
            m.member_no AS Member_No,
            m.full_name AS Member,
            m.contribution_frequency AS Frequency,
            m.regular_contribution AS Planned_Contribution,
            m.target_round_contribution AS Round_Target,
            COALESCE(
                SUM(c.amount),0
            ) AS Total_Paid

        FROM members m

        LEFT JOIN contributions c
            ON m.id=c.member_id
            AND c.module='Equb'
            AND c.status='Paid'

        WHERE m.module='Equb'

        GROUP BY m.id

        ORDER BY m.full_name
        """
    )

    if not plan.empty:

        st.dataframe(
            plan,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        """
        <div class="section-card">

        <div class="module-label">
        Equb Operating Model
        </div>

        The member record stores the intended
        contribution amount.

        The round stores the standard contribution
        for the round.

        Actual payments are recorded separately.

        The statistical layer uses planned contribution,
        realized contribution, payment consistency and
        an optional trust component.

        All model rates are entered as fixed numeric
        percentages rather than draggable controls.

        </div>
        """,
        unsafe_allow_html=True,
    )


def equb_rounds():

    st.subheader(
        "Equb Round Management"
    )

    branch_list = branches("Equb")

    if not branch_list:

        st.warning(
            "Create an Equb branch first."
        )

        return

    branch_names = [
        f"{x['code']} | {x['name']}"
        for x in branch_list
    ]

    with st.form("round_form"):

        branch_choice = st.selectbox(
            "Equb Branch",
            branch_names,
        )

        a, b = st.columns(2)

        round_no = a.number_input(
            "Round Number",
            min_value=1,
            value=1,
            step=1,
        )

        amount = b.number_input(
            "Standard Contribution per Member / Round (ETB)",
            min_value=0.0,
            value=1000.0,
            step=100.0,
        )

        expected_members = a.number_input(
            "Expected Members",
            min_value=1,
            value=10,
            step=1,
        )

        start_date = b.date_input(
            "Start Date",
            date.today(),
        )

        draw_date = a.date_input(
            "Expected Draw Date",
            date.today(),
        )

        status = b.selectbox(
            "Status",
            [
                "Open",
                "Closed",
                "Completed",
                "Cancelled",
            ],
        )

        submitted = st.form_submit_button(
            "Create Round",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            branch = branch_list[
                branch_names.index(
                    branch_choice
                )
            ]

            existing = sql(
                """
                SELECT id
                FROM equb_rounds
                WHERE branch_id=?
                AND round_no=?
                """,
                (
                    branch["id"],
                    int(round_no),
                ),
                fetch=True,
            )

            if existing:

                st.error(
                    "That round number already exists for this branch."
                )

            else:

                sql(
                    """
                    INSERT INTO equb_rounds
                    (
                        branch_id,
                        round_no,
                        contribution_amount,
                        start_date,
                        draw_date,
                        expected_members,
                        total_pool,
                        status,
                        created_at
                    )
                    VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        branch["id"],
                        int(round_no),
                        amount,
                        str(start_date),
                        str(draw_date),
                        int(expected_members),
                        0,
                        status,
                        now(),
                    ),
                )

                audit(
                    "Created Equb round",
                    "Equb",
                    f"{branch['code']} round {round_no}",
                )

                st.success(
                    "Round created."
                )

                st.rerun()

    x = df(
        """
        SELECT
            r.round_no AS Round_No,
            b.code AS Branch,
            r.contribution_amount
                AS Contribution_Per_Round,
            r.expected_members
                AS Expected_Members,
            r.total_pool AS Total_Pool,
            r.start_date AS Start_Date,
            r.draw_date AS Draw_Date,
            r.status AS Status,
            COALESCE(
                m.full_name,''
            ) AS Winner

        FROM equb_rounds r

        JOIN branches b
            ON r.branch_id=b.id

        LEFT JOIN members m
            ON r.winner_member_id=m.id

        ORDER BY r.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )


def equb_contributions():

    st.subheader(
        "Equb Contribution Recording"
    )

    rounds = sql(
        """
        SELECT
            r.*,
            b.code AS branch_code

        FROM equb_rounds r

        JOIN branches b
            ON r.branch_id=b.id

        WHERE r.status IN
            ('Open','Closed')

        ORDER BY r.id DESC
        """,
        fetch=True,
    )

    if not rounds:

        st.info(
            "Create an open Equb round first."
        )

        return

    round_labels = [
        f"{r['branch_code']} | "
        f"Round {r['round_no']} | "
        f"{money(r['contribution_amount'])}"
        for r in rounds
    ]

    with st.form(
        "contribution_form"
    ):

        round_choice = st.selectbox(
            "Round",
            round_labels,
        )

        current_round = rounds[
            round_labels.index(
                round_choice
            )
        ]

        member_list = members(
            "Equb",
            current_round["branch_id"],
        )

        if not member_list:

            st.warning(
                "No Equb members are registered in this branch."
            )

            st.form_submit_button(
                "Record Contribution",
                disabled=True,
            )

            return

        member_labels = [
            f"{m['member_no']} | "
            f"{m['full_name']}"
            for m in member_list
        ]

        member_choice = st.selectbox(
            "Member",
            member_labels,
        )

        member = member_list[
            member_labels.index(
                member_choice
            )
        ]

        suggested = float(
            member[
                "target_round_contribution"
            ]
            or member[
                "regular_contribution"
            ]
            or current_round[
                "contribution_amount"
            ]
            or 0
        )

        amount = st.number_input(
            "Actual Contribution Amount (ETB)",
            min_value=0.0,
            value=suggested,
            step=50.0,
        )

        contribution_date = st.date_input(
            "Contribution Date",
            date.today(),
        )

        payment_method = st.selectbox(
            "Payment Method",
            [
                "Cash",
                "Bank Transfer",
                "Mobile Money",
                "Other",
            ],
        )

        reference = st.text_input(
            "Payment Reference"
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Record Contribution",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            duplicate = sql(
                """
                SELECT id
                FROM contributions
                WHERE member_id=?
                AND round_id=?
                """,
                (
                    member["id"],
                    current_round["id"],
                ),
                fetch=True,
            )

            if duplicate:

                st.error(
                    "This member already has a contribution record for this round."
                )

            else:

                sql(
                    """
                    INSERT INTO contributions
                    (
                        member_id,
                        module,
                        round_id,
                        amount,
                        contribution_date,
                        status,
                        reference,
                        payment_method,
                        notes,
                        created_at
                    )
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        member["id"],
                        "Equb",
                        current_round["id"],
                        amount,
                        str(contribution_date),
                        "Paid",
                        reference,
                        payment_method,
                        notes,
                        now(),
                    ),
                )

                total = sql(
                    """
                    SELECT
                        COALESCE(
                            SUM(amount),0
                        ) AS n
                    FROM contributions
                    WHERE round_id=?
                    AND status='Paid'
                    """,
                    (
                        current_round["id"],
                    ),
                    fetch=True,
                )[0]["n"]

                sql(
                    """
                    UPDATE equb_rounds
                    SET total_pool=?
                    WHERE id=?
                    """,
                    (
                        total,
                        current_round["id"],
                    ),
                )

                audit(
                    "Recorded Equb contribution",
                    "Equb",
                    (
                        f"{member['member_no']} | "
                        f"round {current_round['round_no']} | "
                        f"{amount}"
                    ),
                )

                st.success(
                    "Contribution recorded."
                )

                st.rerun()

    x = df(
        """
        SELECT

            c.contribution_date AS Date,

            m.member_no AS Member_No,

            m.full_name AS Member,

            b.code AS Branch,

            r.round_no AS Round,

            r.contribution_amount
                AS Planned_Round_Amount,

            c.amount AS Actual_Paid,

            CASE

                WHEN r.contribution_amount > 0

                THEN MIN(
                    c.amount /
                    r.contribution_amount,
                    1.0
                )

                ELSE 0

            END AS Payment_Rate,

            c.status AS Status,

            c.reference AS Reference,

            c.payment_method
                AS Payment_Method

        FROM contributions c

        JOIN members m
            ON c.member_id=m.id

        JOIN equb_rounds r
            ON c.round_id=r.id

        JOIN branches b
            ON r.branch_id=b.id

        WHERE c.module='Equb'

        ORDER BY c.id DESC

        LIMIT 500
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_equb_contributions.csv",
        )


def equb_probability():

    st.subheader(
        "Contribution-Weighted Probability Engine"
    )

    st.markdown(
        """
        <div class="section-card">

        <div class="module-label">
        Fixed Statistical Model Rates
        </div>

        Enter the model rates directly as percentages.
        The rates must sum to 100%.

        The system does not use a draggable slider.

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FIXED MODEL RATE BOXES
    # --------------------------------------------------------

    r1, r2, r3, r4 = st.columns(4)

    planned_rate = r1.number_input(
        "Planned Contribution Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
    )

    paid_rate = r2.number_input(
        "Historical Paid Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
    )

    consistency_rate = r3.number_input(
        "Payment Consistency Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=20.0,
        step=1.0,
    )

    trust_rate = r4.number_input(
        "Trust Rate (%)",
        min_value=0.0,
        max_value=50.0,
        value=20.0,
        step=1.0,
    )

    contribution_total = (
        planned_rate
        + paid_rate
        + consistency_rate
    )

    if abs(
        contribution_total - 100
    ) > 0.001:

        st.error(
            "Planned contribution, historical paid contribution and payment consistency rates must sum to 100%."
        )

        return

    trust_weight = (
        trust_rate / 100.0
    )

    planned_weight = (
        planned_rate / 100.0
    )

    paid_weight = (
        paid_rate / 100.0
    )

    consistency_weight = (
        consistency_rate / 100.0
    )

    round_rows = sql(
        """
        SELECT
            r.*,
            b.code AS branch_code
        FROM equb_rounds r
        JOIN branches b
            ON r.branch_id=b.id
        ORDER BY r.id DESC
        """,
        fetch=True,
    )

    options = [
        "All recorded Equb contributions"
    ] + [
        f"{r['branch_code']} | "
        f"Round {r['round_no']} | "
        f"{money(r['contribution_amount'])}"
        for r in round_rows
    ]

    selected = st.selectbox(
        "Probability Basis",
        options,
    )

    round_id = None

    if selected != options[0]:

        round_id = round_rows[
            options.index(selected) - 1
        ]["id"]

    x = equb_probability_table(
        round_id=round_id,
        planned_weight=planned_weight,
        paid_weight=paid_weight,
        consistency_weight=consistency_weight,
        trust_weight=trust_weight,
    )

    if x.empty:

        st.info(
            "Register Equb members first."
        )

        return

    a, b, c, d = st.columns(4)

    a.metric(
        "Members",
        len(x),
    )

    b.metric(
        "Planned Contribution",
        money(
            x[
                "Planned_Contribution"
            ].sum()
        ),
    )

    c.metric(
        "Total Paid",
        money(
            x["Total_Paid"].sum()
        ),
    )

    d.metric(
        "Average Consistency",
        f"{x['Payment_Consistency'].mean():.1%}",
    )

    display = x.copy()

    for col in [
        "Planned_Contribution",
        "Total_Paid",
    ]:

        display[col] = display[
            col
        ].map(
            lambda v:
            f"{v:,.2f}"
        )

    for col in [
        "Payment_Consistency",
        "Trust_Score",
        "Contribution_Weighted_Mean",
        "Adjusted_Score",
        "Probability",
        "Cumulative_Probability",
    ]:

        display[col] = display[
            col
        ].map(
            lambda v:
            f"{float(v):.2%}"
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        f"""
        <div class="section-card">

        <div class="module-label">
        Current Mathematical Specification
        </div>

        Planned contribution weight:
        <b>{planned_rate:.0f}%</b>

        <br>

        Historical paid contribution weight:
        <b>{paid_rate:.0f}%</b>

        <br>

        Payment consistency weight:
        <b>{consistency_rate:.0f}%</b>

        <br>

        Trust weight:
        <b>{trust_rate:.0f}%</b>

        <br><br>

        Contribution score:

        <br>

        Planned contribution component +
        Historical paid contribution component +
        Payment consistency component.

        <br><br>

        Final adjusted score:

        <br>

        Contribution performance is combined
        with the fixed trust rate.

        <br><br>

        Final probability:

        <br>

        Each eligible member's adjusted score
        is divided by the sum of all eligible
        members' adjusted scores.

        </div>
        """,
        unsafe_allow_html=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_equb_weighted_probability.csv",
        )


def equb_simulation():

    st.subheader(
        "Weighted Selection Simulation"
    )

    x = equb_probability_table()

    if x.empty:

        st.info(
            "Register Equb members first."
        )

        return

    n = st.number_input(
        "Number of Simulations",
        min_value=1,
        max_value=10000,
        value=1000,
        step=100,
    )

    if st.button(
        "Run Monte Carlo Demonstration",
        type="primary",
        use_container_width=True,
    ):

        members_list = (
            x["Member"].tolist()
        )

        weights = (
            x["Probability"].tolist()
        )

        results = random.choices(
            members_list,
            weights=weights,
            k=int(n),
        )

        counts = pd.Series(
            results
        ).value_counts()

        sim = x[
            [
                "Member_No",
                "Member",
                "Probability",
            ]
        ].copy()

        sim[
            "Expected_Probability"
        ] = sim["Probability"]

        sim[
            "Observed_Probability"
        ] = sim["Member"].map(
            lambda m:
            counts.get(m, 0) / n
        )

        sim["Difference"] = (
            sim[
                "Observed_Probability"
            ]
            - sim[
                "Expected_Probability"
            ]
        )

        st.dataframe(
            sim.sort_values(
                "Observed_Probability",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Monte Carlo frequencies should approach the model probabilities as the number of simulations increases."
        )

        audit(
            "Executed Equb Monte Carlo simulation",
            "Equb",
            f"{n} simulations",
        )


def equb_history():

    x = df(
        """
        SELECT

            r.round_no AS Round_No,

            b.code AS Branch,

            r.total_pool AS Pool,

            r.draw_date AS Draw_Date,

            COALESCE(
                m.member_no,''
            ) AS Winner_No,

            COALESCE(
                m.full_name,''
            ) AS Winner,

            r.status AS Status

        FROM equb_rounds r

        JOIN branches b
            ON r.branch_id=b.id

        LEFT JOIN members m
            ON r.winner_member_id=m.id

        ORDER BY r.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_equb_rounds.csv",
        )


# ============================================================
# MODULE 5: IDFS IDDIR
# ============================================================

def iddir():

    header(
        "Module 5: IDFS Iddir",
        "Community risk sharing, benefit management, property and financial records",
    )

    tabs = st.tabs(
        [
            "Overview",
            "Community Events",
            "Property Management",
            "Transactions",
            "Member History",
        ]
    )

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
        """
        SELECT COUNT(*) AS n
        FROM members
        WHERE module='Iddir'
        AND status='Active'
        """,
        fetch=True,
    )[0]["n"]

    approved_benefits = sql(
        """
        SELECT
            COALESCE(
                SUM(approved_amount),0
            ) AS n
        FROM iddir_events
        WHERE status IN
            ('Approved','Paid')
        """,
        fetch=True,
    )[0]["n"]

    property_value = sql(
        """
        SELECT
            COALESCE(
                SUM(current_value),0
            ) AS n
        FROM properties
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    pending_cases = sql(
        """
        SELECT COUNT(*) AS n
        FROM iddir_events
        WHERE status='Pending'
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric(
        "Active Members",
        active_members,
    )

    b.metric(
        "Approved Support",
        money(approved_benefits),
    )

    c.metric(
        "Active Property Value",
        money(property_value),
    )

    d.metric(
        "Pending Cases",
        pending_cases,
    )

    st.markdown(
        """
        <div class="section-card">

        <div class="module-label">
        Iddir Operating Scope
        </div>

        The platform records community support
        cases for funeral, wedding, holiday,
        emergency, medical, family and other
        approved purposes.

        It also maintains community property
        and operational assets such as land,
        buildings, vehicles, equipment and
        furniture.

        </div>
        """,
        unsafe_allow_html=True,
    )


def iddir_events():

    st.subheader(
        "Community Event and Benefit Management"
    )

    member_list = members("Iddir")

    if not member_list:

        st.info(
            "Register Iddir members first."
        )

        return

    member_labels = [
        f"{m['member_no']} | "
        f"{m['full_name']}"
        for m in member_list
    ]

    with st.form("iddir_event"):

        member_choice = st.selectbox(
            "Member / Beneficiary",
            member_labels,
        )

        event_type = st.selectbox(
            "Event Type",
            EVENT_TYPES,
        )

        event_date = st.date_input(
            "Event Date",
            date.today(),
        )

        requested = st.number_input(
            "Requested Amount (ETB)",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

        approved = st.number_input(
            "Approved Amount (ETB)",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

        status = st.selectbox(
            "Status",
            [
                "Pending",
                "Approved",
                "Rejected",
                "Paid",
            ],
        )

        reference = st.text_input(
            "Case / Payment Reference"
        )

        description = st.text_area(
            "Description"
        )

        submitted = st.form_submit_button(
            "Record Community Support Case",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            member = member_list[
                member_labels.index(
                    member_choice
                )
            ]

            payment_date = (
                str(date.today())
                if status == "Paid"
                else None
            )

            if approved > requested:
                st.error(
                    "Approved amount cannot exceed requested amount."
                )
                return

            sql(
                """
                INSERT INTO iddir_events
                (
                    branch_id,
                    event_type,
                    member_id,
                    event_date,
                    description,
                    requested_amount,
                    approved_amount,
                    status,
                    payment_date,
                    reference,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    member["branch_id"],
                    event_type,
                    member["id"],
                    str(event_date),
                    description,
                    requested,
                    approved,
                    status,
                    payment_date,
                    reference,
                    now(),
                ),
            )

            if (
                status == "Paid"
                and approved > 0
            ):

                sql(
                    """
                    INSERT INTO transactions
                    (
                        module,
                        branch_id,
                        member_id,
                        transaction_type,
                        amount,
                        reference,
                        transaction_date,
                        description,
                        created_at
                    )
                    VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        "Iddir",
                        member["branch_id"],
                        member["id"],
                        "Community Benefit Payment",
                        approved,
                        reference,
                        str(event_date),
                        event_type
                        + " support",
                        now(),
                    ),
                )

            audit(
                "Recorded Iddir support case",
                "Iddir",
                (
                    f"{event_type} "
                    f"for {member['member_no']}"
                ),
            )

            st.success(
                "Support case recorded."
            )

            st.rerun()

    x = df(
        """
        SELECT

            e.event_date AS Event_Date,

            e.event_type AS Event_Type,

            m.member_no AS Member_No,

            m.full_name AS Member,

            e.requested_amount AS Requested,

            e.approved_amount AS Approved,

            e.status AS Status,

            e.reference AS Reference,

            e.description AS Description

        FROM iddir_events e

        JOIN members m
            ON e.member_id=m.id

        ORDER BY e.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )


def iddir_properties():

    st.subheader(
        "Iddir Property Management"
    )

    branch_list = branches("Iddir")

    if not branch_list:

        st.warning(
            "Create an Iddir branch first."
        )

        return

    branch_names = [
        f"{x['code']} | {x['name']}"
        for x in branch_list
    ]

    with st.form("property_form"):

        branch_choice = st.selectbox(
            "Iddir Branch",
            branch_names,
        )

        a, b = st.columns(2)

        property_code = a.text_input(
            "Property Code",
            placeholder="PROP-001",
        )

        property_type = b.selectbox(
            "Property Type",
            PROPERTY_TYPES,
        )

        description = a.text_input(
            "Description"
        )

        location = b.text_input(
            "Location"
        )

        acquisition_date = a.date_input(
            "Acquisition Date",
            date.today(),
        )

        acquisition_cost = b.number_input(
            "Acquisition Cost (ETB)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
        )

        current_value = a.number_input(
            "Current Estimated Value (ETB)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
        )

        status = b.selectbox(
            "Status",
            [
                "Active",
                "Under Maintenance",
                "Disposed",
                "Transferred",
            ],
        )

        custodian = a.text_input(
            "Custodian"
        )

        notes = b.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Register Property",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not property_code.strip():

                st.error(
                    "Property code is required."
                )

            else:

                branch = branch_list[
                    branch_names.index(
                        branch_choice
                    )
                ]

                try:

                    sql(
                        """
                        INSERT INTO properties
                        (
                            branch_id,
                            property_code,
                            property_type,
                            description,
                            location,
                            acquisition_date,
                            acquisition_cost,
                            current_value,
                            status,
                            custodian,
                            notes,
                            created_at
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            branch["id"],
                            property_code.strip(),
                            property_type,
                            description,
                            location,
                            str(acquisition_date),
                            acquisition_cost,
                            current_value,
                            status,
                            custodian,
                            notes,
                            now(),
                        ),
                    )

                    audit(
                        "Registered Iddir property",
                        "Iddir",
                        property_code.strip(),
                    )

                    st.success(
                        "Property registered."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Property code already exists."
                    )

    x = df(
        """
        SELECT

            p.property_code AS Property_Code,

            p.property_type AS Property_Type,

            p.description AS Description,

            COALESCE(
                b.name,''
            ) AS Branch,

            p.location AS Location,

            p.acquisition_date
                AS Acquisition_Date,

            p.acquisition_cost
                AS Acquisition_Cost,

            p.current_value
                AS Current_Value,

            p.status AS Status,

            p.custodian AS Custodian

        FROM properties p

        LEFT JOIN branches b
            ON p.branch_id=b.id

        ORDER BY p.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_iddir_properties.csv",
        )


def iddir_transaction_view():

    x = df(
        """
        SELECT
            transaction_date AS Date,
            transaction_type AS Type,
            amount AS Amount,
            reference AS Reference,
            description AS Description

        FROM transactions

        WHERE module='Iddir'

        ORDER BY id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )


def iddir_history():

    x = df(
        """
        SELECT

            e.event_date AS Date,

            e.event_type AS Event,

            m.member_no AS Member_No,

            m.full_name AS Member,

            e.requested_amount AS Requested,

            e.approved_amount AS Approved,

            e.status AS Status,

            e.reference AS Reference

        FROM iddir_events e

        JOIN members m
            ON e.member_id=m.id

        ORDER BY e.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MODULE 6: TRANSACTIONS
# ============================================================

def transactions():

    header(
        "Module 6: Transactions",
        "Unified financial transaction register",
    )

    with st.form(
        "transaction_form"
    ):

        a, b = st.columns(2)

        module = a.selectbox(
            "Module",
            MODULES,
        )

        transaction_type = b.selectbox(
            "Transaction Type",
            [
                "Deposit",
                "Contribution",
                "Community Benefit Payment",
                "Adjustment",
                "Other",
            ],
        )

        amount = a.number_input(
            "Amount (ETB)",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

        reference = b.text_input(
            "Reference"
        )

        transaction_date = a.date_input(
            "Transaction Date",
            date.today(),
        )

        description = b.text_area(
            "Description"
        )

        submitted = st.form_submit_button(
            "Record Transaction",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            sql(
                """
                INSERT INTO transactions
                (
                    module,
                    transaction_type,
                    amount,
                    reference,
                    transaction_date,
                    description,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    module,
                    transaction_type,
                    amount,
                    reference,
                    str(transaction_date),
                    description,
                    now(),
                ),
            )

            audit(
                "Recorded transaction",
                module,
                f"{transaction_type}: {amount}",
            )

            st.success(
                "Transaction recorded."
            )

            st.rerun()

    x = df(
        """
        SELECT
            transaction_date AS Date,
            module AS Module,
            transaction_type AS Type,
            amount AS Amount,
            reference AS Reference,
            description AS Description

        FROM transactions

        ORDER BY id DESC

        LIMIT 1000
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_transactions.csv",
        )


# ============================================================
# MODULE 7: REPORTS AND ANALYTICS
# ============================================================

def reports():

    header(
        "Module 7: Reports and Analytics",
        "Management information and statistical analysis",
    )

    report_type = st.selectbox(
        "Report",
        [
            "Module Summary",
            "Member Contribution Plans",
            "Equb Contributions",
            "Equb Rounds",
            "Equb Probability",
            "Equb Simulation",
            "Iddir Community Support",
            "Iddir Properties",
            "Transactions",
        ],
    )

    if report_type == "Module Summary":

        x = df(
            """
            SELECT

                module AS Module,

                COUNT(*) AS Members,

                ROUND(
                    AVG(
                        regular_contribution
                    ),2
                ) AS Average_Planned_Contribution,

                ROUND(
                    AVG(trust_score),3
                ) AS Average_Trust

            FROM members

            WHERE status='Active'

            GROUP BY module
            """
        )

    elif report_type == "Member Contribution Plans":

        x = df(
            """
            SELECT

                m.member_no AS Member_No,

                m.full_name AS Member,

                m.module AS Module,

                b.code AS Branch,

                m.contribution_frequency
                    AS Frequency,

                m.regular_contribution
                    AS Planned_Contribution,

                m.target_round_contribution
                    AS Round_Target,

                COALESCE(
                    SUM(c.amount),0
                ) AS Total_Paid

            FROM members m

            LEFT JOIN branches b
                ON m.branch_id=b.id

            LEFT JOIN contributions c
                ON m.id=c.member_id

            GROUP BY m.id

            ORDER BY
                m.module,
                m.full_name
            """
        )

    elif report_type == "Equb Contributions":

        x = df(
            """
            SELECT

                m.member_no AS Member_No,

                m.full_name AS Member,

                COUNT(c.id) AS Payments,

                COALESCE(
                    SUM(c.amount),0
                ) AS Total_Paid,

                COALESCE(
                    AVG(c.amount),0
                ) AS Average_Payment

            FROM members m

            LEFT JOIN contributions c
                ON m.id=c.member_id

            AND c.module='Equb'

            AND c.status='Paid'

            WHERE m.module='Equb'

            GROUP BY m.id

            ORDER BY Total_Paid DESC
            """
        )

    elif report_type == "Equb Rounds":

        x = df(
            """
            SELECT

                r.round_no AS Round_No,

                b.code AS Branch,

                r.contribution_amount
                    AS Contribution,

                r.expected_members
                    AS Members,

                r.total_pool AS Total_Pool,

                r.start_date AS Start_Date,

                r.draw_date AS Draw_Date,

                r.status AS Status,

                COALESCE(
                    m.full_name,''
                ) AS Winner

            FROM equb_rounds r

            JOIN branches b
                ON r.branch_id=b.id

            LEFT JOIN members m
                ON r.winner_member_id=m.id

            ORDER BY r.id DESC
            """
        )

    elif report_type == "Equb Probability":

        x = equb_probability_table()

        if x.empty:

            st.info(
                "Register Equb members first."
            )

            return

    elif report_type == "Equb Simulation":

        x = equb_probability_table()

        if x.empty:

            st.info(
                "Register Equb members first."
            )

            return

        n = st.number_input(
            "Simulation Runs",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
        )

        if st.button(
            "Generate Simulation Report",
            type="primary",
        ):

            results = random.choices(
                x["Member"].tolist(),
                weights=x["Probability"].tolist(),
                k=int(n),
            )

            counts = pd.Series(
                results
            ).value_counts()

            x = x[
                [
                    "Member_No",
                    "Member",
                    "Probability",
                ]
            ].copy()

            x[
                "Observed_Probability"
            ] = x["Member"].map(
                lambda m:
                counts.get(m, 0) / n
            )

            x[
                "Simulation_Difference"
            ] = (
                x["Observed_Probability"]
                - x["Probability"]
            )

        else:

            st.info(
                "Click Generate Simulation Report."
            )

            return

    elif report_type == "Iddir Community Support":

        x = df(
            """
            SELECT

                event_type AS Event_Type,

                COUNT(*) AS Cases,

                COALESCE(
                    SUM(requested_amount),0
                ) AS Requested,

                COALESCE(
                    SUM(approved_amount),0
                ) AS Approved

            FROM iddir_events

            GROUP BY event_type

            ORDER BY Approved DESC
            """
        )

    elif report_type == "Iddir Properties":

        x = df(
            """
            SELECT

                property_type AS Property_Type,

                COUNT(*) AS Assets,

                COALESCE(
                    SUM(acquisition_cost),0
                ) AS Acquisition_Cost,

                COALESCE(
                    SUM(current_value),0
                ) AS Current_Value

            FROM properties

            GROUP BY property_type

            ORDER BY Current_Value DESC
            """
        )

    else:

        x = df(
            """
            SELECT

                module AS Module,

                transaction_type
                    AS Transaction_Type,

                COUNT(*) AS Transactions,

                COALESCE(
                    SUM(amount),0
                ) AS Total_Amount

            FROM transactions

            GROUP BY
                module,
                transaction_type

            ORDER BY
                module,
                Total_Amount DESC
            """
        )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_report.csv",
        )


# ============================================================
# MODULE 8: MANUALS
# ============================================================

def manuals():

    header(
        "Module 8: IDFS Manuals",
        "Rules, principles, operating procedures and user instructions for IDFS Equb and IDFS Iddir",
    )

    manual = st.selectbox(
        "Manual",
        [
            "IDFS General Principles",
            "IDFS Equb Manual",
            "Equb Statistical Model Manual",
            "IDFS Iddir Manual",
            "Iddir Benefit and Event Procedure",
            "Roles and Responsibilities",
            "Financial and Audit Controls",
        ],
    )

    # ========================================================
    # GENERAL PRINCIPLES
    # ========================================================

    if manual == "IDFS General Principles":

        st.markdown(
            """
            <div class="manual-card">

            <h2>IDFS General Principles</h2>

            <h3>1. Purpose</h3>

            IDFS is designed as a digital platform for
            organizing indigenous financial practices,
            including rotating savings, community support,
            risk sharing and community property management.

            <h3>2. Transparency</h3>

            Financial transactions, contributions, benefits,
            rounds, assets and important administrative
            activities should be recorded and traceable.

            <h3>3. Accountability</h3>

            Each important financial action should have a
            responsible user, date, amount and reference.

            <h3>4. Member-Centered Governance</h3>

            The software supports community governance.
            It does not replace the approved constitution,
            bylaws, assembly decisions or community rules.

            <h3>5. Fairness</h3>

            Equb selection mechanisms should be transparent,
            reproducible and approved by the relevant
            organization.

            <h3>6. Data Integrity</h3>

            Records should not be silently deleted or altered.
            Corrections should be traceable through appropriate
            administrative procedures.

            <h3>7. Privacy</h3>

            Member information should only be accessed by
            authorized users for legitimate organizational
            purposes.

            <h3>8. Separation of Responsibilities</h3>

            Registration, financial recording, approval,
            payment and auditing should be separated where
            organizational capacity permits.

            <h3>9. Community Ownership</h3>

            The system is intended to strengthen indigenous
            financial institutions rather than replace their
            social and governance structures.

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # EQUB MANUAL
    # ========================================================

    elif manual == "IDFS Equb Manual":

        st.markdown(
            """
            <div class="manual-card">

            <h2>IDFS Equb Operating Manual</h2>

            <h3>1. Definition</h3>

            Equb is a rotating savings arrangement in which
            participating members contribute according to an
            agreed contribution plan and members receive the
            accumulated pool according to an agreed rotation
            or selection mechanism.

            <h3>2. Member Registration</h3>

            Every Equb member should have:

            <ul>
            <li>Unique member number</li>
            <li>Full name</li>
            <li>Contact information</li>
            <li>Branch</li>
            <li>Joining date</li>
            <li>Regular contribution amount</li>
            <li>Contribution frequency</li>
            <li>Target round contribution</li>
            <li>Approved membership status</li>
            </ul>

            <h3>3. Contribution Plan</h3>

            The contribution plan should be agreed before
            participation.

            The system supports:

            <ul>
            <li>Monthly contribution</li>
            <li>Per-round contribution</li>
            <li>Weekly contribution</li>
            <li>Custom contribution arrangements</li>
            </ul>

            <h3>4. Round Formation</h3>

            Each round should define:

            <ul>
            <li>Branch</li>
            <li>Round number</li>
            <li>Standard contribution</li>
            <li>Expected number of members</li>
            <li>Opening date</li>
            <li>Expected draw date</li>
            <li>Round status</li>
            </ul>

            <h3>5. Contribution Recording</h3>

            Actual payments should be recorded independently
            from the planned contribution.

            Each payment should include:

            <ul>
            <li>Member</li>
            <li>Round</li>
            <li>Amount</li>
            <li>Date</li>
            <li>Payment method</li>
            <li>Reference</li>
            <li>Status</li>
            </ul>

            <h3>6. Contribution Consistency</h3>

            Payment consistency is calculated from recorded
            contribution performance.

            Members with missing records should not be assumed
            to have made payments.

            <h3>7. Selection</h3>

            Selection may use:

            <ul>
            <li>Conventional rotation</li>
            <li>Approved random selection</li>
            <li>Statistical demonstration</li>
            <li>Other community-approved methods</li>
            </ul>

            The method must be approved by the Equb's governing
            body.

            <h3>8. Pool Management</h3>

            The round pool should be reconciled against actual
            recorded contributions.

            <h3>9. Winner Recording</h3>

            Once an official winner is determined, the winner,
            date, round and relevant authorization should be
            recorded.

            <h3>10. Dispute Resolution</h3>

            Member disputes should follow the approved Equb
            constitution and community dispute-resolution
            procedures.

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # EQUB STATISTICAL MODEL MANUAL
    # ========================================================

    elif manual == "Equb Statistical Model Manual":

        st.markdown(
            """
            <div class="manual-card">

            <h2>Equb Statistical Model Manual</h2>

            <h3>1. Objective</h3>

            The statistical engine provides a transparent
            mathematical demonstration for contribution-based
            selection probabilities.

            It is not automatically a mandatory Equb rule.

            <h3>2. Model Components</h3>

            The model uses four main concepts:

            <ol>
            <li>Planned contribution</li>
            <li>Historical paid contribution</li>
            <li>Payment consistency</li>
            <li>Trust score</li>
            </ol>

            <h3>3. Fixed Contribution Rates</h3>

            The contribution score is constructed from:

            <ul>
            <li>Planned contribution rate</li>
            <li>Historical paid contribution rate</li>
            <li>Payment consistency rate</li>
            </ul>

            These three rates must sum to 100%.

            <h3>4. Trust Rate</h3>

            The trust rate determines the proportion of the
            final score influenced by the trust score.

            The current prototype allows the trust rate to be
            entered as a fixed percentage.

            <h3>5. Why Fixed Rates?</h3>

            Fixed numeric rates provide:

            <ul>
            <li>Reproducibility</li>
            <li>Transparency</li>
            <li>Auditability</li>
            <li>Easy documentation</li>
            <li>Consistent model governance</li>
            </ul>

            <h3>6. Probability Interpretation</h3>

            The probability displayed by the system is a
            model-based demonstration probability.

            A higher adjusted score produces a higher normalized
            probability.

            <h3>7. Important Governance Rule</h3>

            A statistical probability should not be interpreted
            automatically as a legal entitlement.

            The Equb organization must decide whether the
            statistical engine is:

            <ul>
            <li>Informational only</li>
            <li>A recommendation mechanism</li>
            <li>An approved selection mechanism</li>
            </ul>

            <h3>8. Monte Carlo Simulation</h3>

            The simulation repeatedly samples members using the
            calculated probabilities.

            Increasing the number of simulations normally causes
            observed frequencies to approach the model
            probabilities.

            <h3>9. Recommended Governance</h3>

            Before operational use:

            <ol>
            <li>Approve the model rates.</li>
            <li>Approve eligibility criteria.</li>
            <li>Approve treatment of late payments.</li>
            <li>Approve treatment of missed payments.</li>
            <li>Approve trust-score governance.</li>
            <li>Document the official selection procedure.</li>
            <li>Require audit records for official draws.</li>
            </ol>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # IDDIR MANUAL
    # ========================================================

    elif manual == "IDFS Iddir Manual":

        st.markdown(
            """
            <div class="manual-card">

            <h2>IDFS Iddir Operating Manual</h2>

            <h3>1. Definition</h3>

            Iddir is a community-based mutual support and
            risk-sharing institution.

            IDFS provides digital infrastructure for recording
            membership, events, support decisions, property and
            transactions.

            <h3>2. Core Principles</h3>

            <ul>
            <li>Mutual assistance</li>
            <li>Community solidarity</li>
            <li>Fair treatment</li>
            <li>Transparency</li>
            <li>Accountability</li>
            <li>Responsible resource management</li>
            <li>Community participation</li>
            </ul>

            <h3>3. Membership</h3>

            Members should be registered with:

            <ul>
            <li>Unique member number</li>
            <li>Full name</li>
            <li>Contact information</li>
            <li>Branch</li>
            <li>Joining date</li>
            <li>Status</li>
            </ul>

            <h3>4. Eligible Events</h3>

            The prototype supports:

            <ul>
            <li>Funeral</li>
            <li>Wedding</li>
            <li>Holiday</li>
            <li>Emergency</li>
            <li>Medical support</li>
            <li>Family support</li>
            <li>Other approved events</li>
            </ul>

            <h3>5. Benefit Governance</h3>

            The organization should establish:

            <ul>
            <li>Eligibility criteria</li>
            <li>Maximum benefit limits</li>
            <li>Required evidence</li>
            <li>Approval authority</li>
            <li>Payment procedures</li>
            <li>Appeal procedures</li>
            </ul>

            <h3>6. Community Property</h3>

            Property should be registered with:

            <ul>
            <li>Property code</li>
            <li>Type</li>
            <li>Description</li>
            <li>Location</li>
            <li>Acquisition date</li>
            <li>Acquisition cost</li>
            <li>Current estimated value</li>
            <li>Custodian</li>
            <li>Status</li>
            </ul>

            <h3>7. Property Control</h3>

            Community property should be physically verified
            periodically and its condition documented.

            <h3>8. Financial Records</h3>

            Every benefit payment should have an appropriate
            financial transaction record.

            <h3>9. Community Decision Making</h3>

            Major benefit policies, property decisions and
            financial rules should be approved according to the
            organization's constitution.

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # IDDIR BENEFIT PROCEDURE
    # ========================================================

    elif manual == "Iddir Benefit and Event Procedure":

        st.markdown(
            """
            <div class="manual-card">

            <h2>Iddir Benefit and Event Procedure</h2>

            <h3>Step 1: Case Registration</h3>

            Record:

            <ul>
            <li>Beneficiary</li>
            <li>Event type</li>
            <li>Event date</li>
            <li>Description</li>
            <li>Requested amount</li>
            <li>Supporting reference</li>
            </ul>

            <h3>Step 2: Verification</h3>

            The responsible committee verifies the event
            according to the organization's rules.

            <h3>Step 3: Approval</h3>

            The authorized body determines the approved amount.

            The approved amount should not exceed the requested
            amount unless an approved policy explicitly permits
            otherwise.

            <h3>Step 4: Payment</h3>

            Once approved, payment should be made using an
            authorized financial method.

            <h3>Step 5: Transaction Recording</h3>

            A corresponding financial transaction should be
            recorded.

            <h3>Step 6: Closure</h3>

            The case should be marked as Paid after the payment
            has actually occurred.

            <h3>Step 7: Audit</h3>

            Important actions should remain traceable through
            the audit trail.

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # ROLES
    # ========================================================

    elif manual == "Roles and Responsibilities":

        st.markdown(
            """
            <div class="manual-card">

            <h2>Roles and Responsibilities</h2>

            <h3>Administrator</h3>

            Responsible for:

            <ul>
            <li>User administration</li>
            <li>System configuration</li>
            <li>Branch administration</li>
            <li>Access control</li>
            <li>System-level audit supervision</li>
            </ul>

            <h3>Branch Manager</h3>

            Responsible for:

            <ul>
            <li>Branch operations</li>
            <li>Member supervision</li>
            <li>Round supervision</li>
            <li>Community event administration</li>
            <li>Operational reporting</li>
            </ul>

            <h3>Finance Officer</h3>

            Responsible for:

            <ul>
            <li>Contribution records</li>
            <li>Payments</li>
            <li>Financial reconciliation</li>
            <li>Transaction records</li>
            <li>Financial reports</li>
            </ul>

            <h3>Member</h3>

            Members may:

            <ul>
            <li>View their approved information</li>
            <li>Participate in Equb</li>
            <li>Make contributions</li>
            <li>Receive approved Iddir support</li>
            </ul>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # FINANCIAL CONTROLS
    # ========================================================

    else:

        st.markdown(
            """
            <div class="manual-card">

            <h2>Financial and Audit Controls</h2>

            <h3>1. Unique References</h3>

            Important payments should have unique references.

            <h3>2. Reconciliation</h3>

            Recorded contributions should be reconciled against
            actual collections.

            <h3>3. Round Reconciliation</h3>

            The Equb pool should be compared with the sum of
            recorded paid contributions.

            <h3>4. Benefit Reconciliation</h3>

            Iddir approved and paid benefits should be reconciled
            with transaction records.

            <h3>5. Property Reconciliation</h3>

            Community assets should be periodically checked
            against the property register.

            <h3>6. Audit Trail</h3>

            Administrative and financial actions should be
            traceable.

            <h3>7. Access Control</h3>

            Users should only have access appropriate to their
            organizational role.

            <h3>8. Corrections</h3>

            Financial corrections should be documented rather
            than silently overwritten.

            <h3>9. Reporting</h3>

            Management reports should be generated regularly.

            <h3>10. Prototype Limitation</h3>

            This demonstration system is not a production banking
            core system. Before production deployment it would
            require additional security, encryption, backup,
            recovery, regulatory, authorization and financial
            control mechanisms.

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MODULE 9: AUDIT TRAIL
# ============================================================

def audit_page():

    header(
        "Module 9: Audit Trail",
        "Traceable record of important system activities",
    )

    x = df(
        """
        SELECT

            timestamp AS Timestamp,

            username AS Username,

            module AS Module,

            action AS Action,

            details AS Details

        FROM audit_log

        ORDER BY id DESC

        LIMIT 2000
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    if not x.empty:

        download(
            x,
            "idfs_audit.csv",
        )


# ============================================================
# MODULE 10: USER ADMINISTRATION
# ============================================================

def users_page():

    header(
        "Module 10: User Administration",
        "Role-based demonstration accounts",
    )

    x = df(
        """
        SELECT

            username AS Username,

            full_name AS Full_Name,

            role AS Role,

            module AS Module,

            active AS Active,

            created_at AS Created_At

        FROM users

        ORDER BY username
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    with st.form("user_form"):

        a, b = st.columns(2)

        username = a.text_input(
            "Username"
        )

        full_name = b.text_input(
            "Full Name"
        )

        password = a.text_input(
            "Password",
            type="password",
        )

        role = b.selectbox(
            "Role",
            ROLES,
        )

        module = a.selectbox(
            "Module",
            ["Portal"] + MODULES,
        )

        branch_list = (
            branches(module)
            if module in MODULES
            else []
        )

        branch_options = (
            ["No branch"]
            + [
                f"{x['code']} | "
                f"{x['name']}"
                for x in branch_list
            ]
        )

        branch_choice = b.selectbox(
            "Branch",
            branch_options,
        )

        submitted = st.form_submit_button(
            "Create User",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not username.strip():

                st.error(
                    "Username is required."
                )

            elif not full_name.strip():

                st.error(
                    "Full name is required."
                )

            elif len(password) < 6:

                st.error(
                    "Password must contain at least six characters."
                )

            else:

                branch_id = None

                if branch_choice != "No branch":

                    index = (
                        branch_options.index(
                            branch_choice
                        ) - 1
                    )

                    branch_id = (
                        branch_list[index]["id"]
                    )

                try:

                    sql(
                        """
                        INSERT INTO users
                        (
                            username,
                            password_hash,
                            full_name,
                            role,
                            module,
                            branch_id,
                            active,
                            created_at
                        )
                        VALUES(?,?,?,?,?,?,?,?)
                        """,
                        (
                            username.strip(),
                            pwd_hash(password),
                            full_name.strip(),
                            role,
                            module,
                            branch_id,
                            1,
                            now(),
                        ),
                    )

                    audit(
                        "Created user",
                        "Portal",
                        username.strip(),
                    )

                    st.success(
                        "User created."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Username already exists."
                    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    init_db()

    if not st.session_state.get(
        "authenticated",
        False,
    ):

        login()

        return

    with st.sidebar:

        st.markdown(
            "## IDFS"
        )

        st.caption(
            "Indigenous Digital Financial System"
        )

        st.write(
            f"User: "
            f"**{st.session_state.get('full_name','')}**"
        )

        st.write(
            f"Role: "
            f"**{st.session_state.get('role','')}**"
        )

        if st.button(
            "Sign out",
            use_container_width=True,
        ):

            audit(
                "Logout"
            )

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

            "Manuals",

            "Audit Trail",
        ]

        if (
            st.session_state.get("role")
            == "Administrator"
        ):

            navigation.append(
                "User Administration"
            )

        page = st.radio(
            "Navigation",
            navigation,
        )

    pages = {

        "Dashboard":
            dashboard,

        "Branch Management":
            branch_page,

        "Member Management":
            member_page,

        "IDFS Equb":
            equb,

        "IDFS Iddir":
            iddir,

        "Transactions":
            transactions,

        "Reports and Analytics":
            reports,

        "Manuals":
            manuals,

        "Audit Trail":
            audit_page,

        "User Administration":
            users_page,
    }

    pages[page]()


# ============================================================
# APPLICATION ENTRY
# ============================================================

if __name__ == "__main__":
    main()
