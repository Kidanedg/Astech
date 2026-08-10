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
# ============================================================

st.set_page_config(
    page_title="IDFS Web Platform",
    page_icon="IDFS",
    layout="wide",
)

DB = Path("idfs_demo.db")

MODULES = ["Equb", "Iddir"]
ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]

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
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }

    .subtitle {
        color: #667085;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .module-card {
        border: 1px solid #E4E7EC;
        border-radius: 12px;
        padding: 1.1rem;
        background: #FFFFFF;
        min-height: 145px;
    }

    .module-card h3 {
        margin-top: 0;
    }

    .info-box {
        border-left: 4px solid #0B5CAD;
        padding: 0.8rem 1rem;
        background: #F7F9FC;
        border-radius: 6px;
        margin: 0.5rem 0 1rem 0;
    }

    .login-box {
        max-width: 500px;
        margin: 3rem auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL UTILITIES
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
    c = conn()
    cur = c.cursor()

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
    rows = sql(q, p, fetch=True)
    return pd.DataFrame([dict(x) for x in rows])


def pwd_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000,
    ).hex()
    return salt + "$" + h


def check_pwd(password, stored):
    try:
        salt, h = stored.split("$", 1)
        x = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000,
        ).hex()
        return hmac.compare_digest(x, h)
    except Exception:
        return False


def audit(action, module="Portal", details=""):
    sql(
        """
        INSERT INTO audit_log
        (username,module,action,details,timestamp)
        VALUES(?,?,?,?,?)
        """,
        (
            st.session_state.get("username", "anonymous"),
            module,
            action,
            details,
            now(),
        ),
    )


def header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="main-title">{title}</div>
        <div class="subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def download(data, filename):
    if data is not None and not data.empty:
        st.download_button(
            "Download CSV",
            data.to_csv(index=False).encode("utf-8"),
            filename,
            "text/csv",
            use_container_width=True,
        )


# ============================================================
# DATABASE INITIALIZATION
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
            created_at TEXT NOT NULL,
            UNIQUE(branch_id, round_no)
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
            UNIQUE(member_id, round_id)
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


def ensure_column(table, column, definition):
    rows = sql(f"PRAGMA table_info({table})", fetch=True)
    columns = [r["name"] for r in rows]

    if column not in columns:
        sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def migrate_database():
    # Users
    ensure_column("users", "branch_id", "INTEGER")
    ensure_column("users", "active", "INTEGER DEFAULT 1")

    # Branches
    ensure_column("branches", "phone", "TEXT")
    ensure_column("branches", "status", "TEXT DEFAULT 'Active'")

    # Members
    ensure_column("members", "regular_contribution", "REAL DEFAULT 0")
    ensure_column("members", "trust_score", "REAL DEFAULT 0.5")
    ensure_column("members", "status", "TEXT DEFAULT 'Active'")
    ensure_column("members", "address", "TEXT")
    ensure_column("members", "notes", "TEXT")

    # Equb
    ensure_column("equb_rounds", "total_pool", "REAL DEFAULT 0")
    ensure_column("equb_rounds", "winner_member_id", "INTEGER")
    ensure_column("equb_rounds", "status", "TEXT DEFAULT 'Open'")

    # Contributions
    ensure_column("contributions", "status", "TEXT DEFAULT 'Paid'")
    ensure_column("contributions", "reference", "TEXT")
    ensure_column("contributions", "payment_method", "TEXT")
    ensure_column("contributions", "notes", "TEXT")

    # Iddir
    ensure_column("iddir_events", "requested_amount", "REAL DEFAULT 0")
    ensure_column("iddir_events", "approved_amount", "REAL DEFAULT 0")
    ensure_column("iddir_events", "status", "TEXT DEFAULT 'Pending'")
    ensure_column("iddir_events", "payment_date", "TEXT")
    ensure_column("iddir_events", "reference", "TEXT")

    # Properties
    ensure_column("properties", "acquisition_cost", "REAL DEFAULT 0")
    ensure_column("properties", "current_value", "REAL DEFAULT 0")
    ensure_column("properties", "status", "TEXT DEFAULT 'Active'")
    ensure_column("properties", "custodian", "TEXT")
    ensure_column("properties", "notes", "TEXT")


def seed_defaults():
    # Default administrator
    sql(
        """
        INSERT OR IGNORE INTO users
        (
            username,
            password_hash,
            full_name,
            role,
            module,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "admin",
            pwd_hash("admin123"),
            "IDFS Administrator",
            "Administrator",
            "Portal",
            now(),
        ),
    )

    # Default branches
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
        sql(
            """
            INSERT OR IGNORE INTO branches
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
# DATABASE STARTUP
# ============================================================

init_db()
migrate_database()
seed_defaults()


# ============================================================
# DATA HELPERS
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

    w = " WHERE " + " AND ".join(where) if where else ""

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
        + w
        + """
        ORDER BY m.full_name
        """,
        tuple(params),
        fetch=True,
    )


def active_member_options(module):
    ms = members(module)

    return {
        f"{m['member_no']} | {m['full_name']}": m
        for m in ms
        if m["status"] == "Active"
    }


# ============================================================
# AUTHENTICATION
# ============================================================

def login():
    st.markdown(
        """
        <div class="login-box">
            <h1>IDFS</h1>
            <h3>Indigenous Digital Financial System</h3>
            <p>
            Secure demonstration platform for Equb savings
            and Iddir community risk sharing.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
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
            u = row[0]

            st.session_state.update(
                authenticated=True,
                user_id=u["id"],
                username=u["username"],
                full_name=u["full_name"],
                role=u["role"],
                module=u["module"],
                branch_id=u["branch_id"],
            )

            audit("Successful login")
            st.rerun()

        else:
            st.error("Invalid username or password.")

    st.info("Demonstration account: admin / admin123")


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():
    header(
        "IDFS Executive Dashboard",
        "Integrated Equb saving and Iddir community risk-sharing platform",
    )

    active_members = sql(
        """
        SELECT COUNT(*) n
        FROM members
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    active_branches = sql(
        """
        SELECT COUNT(*) n
        FROM branches
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    equb_savings = sql(
        """
        SELECT COALESCE(SUM(amount),0) n
        FROM contributions
        WHERE module='Equb'
        AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    property_value = sql(
        """
        SELECT COALESCE(SUM(current_value),0) n
        FROM properties
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric("Active Members", active_members)
    b.metric("Active Branches", active_branches)
    c.metric("Equb Savings", money(equb_savings))
    d.metric("Iddir Property", money(property_value))

    st.divider()

    x, y = st.columns(2)

    with x:
        st.markdown(
            """
            <div class="module-card">
                <h3>IDFS Equb</h3>
                <p>
                Community savings, regular contributions,
                Equb rounds, payment records and
                contribution-weighted probability demonstration.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with y:
        st.markdown(
            """
            <div class="module-card">
                <h3>IDFS Iddir</h3>
                <p>
                Community risk sharing for funeral, wedding,
                holiday, emergency, medical and family support,
                together with property management.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Recent Activity")

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
        st.info("No recent system activity.")
    else:
        st.dataframe(
            activity,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# BRANCH MANAGEMENT
# ============================================================

def branch_page():
    header(
        "Module 4: Branch Management",
        "Bank-style branch structure for Equb and Iddir",
    )

    t1, t2 = st.tabs(
        ["Branch Directory", "Register Branch"]
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

        download(x, "idfs_branches.csv")

    with t2:
        with st.form("branch_form"):
            a, b = st.columns(2)

            code = a.text_input(
                "Branch Code",
                placeholder="EQB-003",
            )

            name = b.text_input("Branch Name")

            mod = a.selectbox(
                "Module",
                MODULES,
            )

            loc = b.text_input("Location")
            mgr = a.text_input("Manager")
            phone = b.text_input("Phone")

            status = b.selectbox(
                "Status",
                ["Active", "Inactive"],
            )

            ok = st.form_submit_button(
                "Register Branch",
                type="primary",
            )

        if ok:
            if not code.strip() or not name.strip():
                st.error(
                    "Branch code and name are required."
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
                            mod,
                            loc.strip(),
                            mgr.strip(),
                            phone.strip(),
                            status,
                            now(),
                        ),
                    )

                    audit(
                        "Created branch",
                        mod,
                        code,
                    )

                    st.success("Branch registered.")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(
                        "Branch code already exists."
                    )


# ============================================================
# MEMBER MANAGEMENT
# ============================================================

def member_page():
    header(
        "Module 5: Member Management",
        "Registration, regular contribution and membership monitoring",
    )

    t1, t2, t3 = st.tabs(
        [
            "Directory",
            "Register Member",
            "Member Profile",
        ]
    )

    with t1:
        f = st.selectbox(
            "Module Filter",
            ["All"] + MODULES,
        )

        if f == "All":
            x = df(
                """
                SELECT
                    m.member_no AS Member_No,
                    m.full_name AS Full_Name,
                    m.module AS Module,
                    b.name AS Branch,
                    m.phone AS Phone,
                    m.join_date AS Join_Date,
                    m.regular_contribution
                        AS Regular_Contribution,
                    m.trust_score AS Trust_Score,
                    m.status AS Status
                FROM members m
                LEFT JOIN branches b
                    ON m.branch_id=b.id
                ORDER BY m.module,m.full_name
                """
            )
        else:
            x = df(
                """
                SELECT
                    m.member_no AS Member_No,
                    m.full_name AS Full_Name,
                    m.module AS Module,
                    b.name AS Branch,
                    m.phone AS Phone,
                    m.join_date AS Join_Date,
                    m.regular_contribution
                        AS Regular_Contribution,
                    m.trust_score AS Trust_Score,
                    m.status AS Status
                FROM members m
                LEFT JOIN branches b
                    ON m.branch_id=b.id
                WHERE m.module=?
                ORDER BY m.full_name
                """,
                (f,),
            )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        download(x, "idfs_members.csv")

    with t2:
        with st.form("member_form"):
            a, b = st.columns(2)

            no = a.text_input(
                "Member Number",
                placeholder="M-0001",
            )

            name = b.text_input("Full Name")

            phone = a.text_input("Phone")

            sex = b.selectbox(
                "Sex",
                [
                    "Not specified",
                    "Female",
                    "Male",
                    "Other",
                ],
            )

            mod = a.selectbox(
                "Module",
                MODULES,
            )

            bs = branches(mod)

            opts = [
                f"{x['code']} | {x['name']}"
                for x in bs
            ]

            if opts:
                branch = b.selectbox(
                    "Branch",
                    opts,
                )
            else:
                branch = None
                b.warning(
                    "No branch is available for this module."
                )

            contribution = a.number_input(
                "Regular Contribution / Monthly Amount (ETB)",
                min_value=0.0,
                value=0.0,
                step=50.0,
            )

            trust = b.slider(
                "Initial Trust Score",
                0.0,
                1.0,
                0.5,
                0.01,
            )

            join = a.date_input(
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

            address = a.text_input("Address")
            notes = b.text_area("Notes")

            ok = st.form_submit_button(
                "Register Member",
                type="primary",
                use_container_width=True,
            )

        if ok:
            if not no.strip() or not name.strip():
                st.error(
                    "Member number and full name are required."
                )
            elif not opts:
                st.error(
                    "Register a branch for the selected module first."
                )
            else:
                bid = bs[opts.index(branch)]["id"]

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
                            trust_score,
                            status,
                            address,
                            notes,
                            created_at
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            no.strip(),
                            name.strip(),
                            phone,
                            sex,
                            str(join),
                            mod,
                            bid,
                            contribution,
                            trust,
                            status,
                            address,
                            notes,
                            now(),
                        ),
                    )

                    audit(
                        "Registered member",
                        mod,
                        no,
                    )

                    st.success("Member registered.")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(
                        "Member number already exists."
                    )

    with t3:
        ms = members()

        if not ms:
            st.info("No members registered yet.")
            return

        labels = [
            f"{x['member_no']} | {x['full_name']}"
            for x in ms
        ]

        pick = st.selectbox(
            "Select Member",
            labels,
        )

        m = ms[labels.index(pick)]

        a, b, c = st.columns(3)

        a.metric("Module", m["module"])
        b.metric(
            "Regular Contribution",
            money(m["regular_contribution"]),
        )
        c.metric(
            "Trust Score",
            f"{float(m['trust_score'] or 0):.2f}",
        )

        st.write(
            {
                "Member Number": m["member_no"],
                "Full Name": m["full_name"],
                "Branch": m["branch_name"],
                "Phone": m["phone"],
                "Join Date": m["join_date"],
                "Status": m["status"],
            }
        )


# ============================================================
# EQUb
# ============================================================

def equb():
    header(
        "Module 6: IDFS Equb",
        "Digital rotating savings, contributions, rounds and transparent selection",
    )

    tabs = st.tabs(
        [
            "Overview",
            "Rounds",
            "Contributions",
            "Weighted Probability",
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
        equb_history()


def equb_overview():
    n = sql(
        """
        SELECT COUNT(*) n
        FROM members
        WHERE module='Equb'
        AND status='Active'
        """,
        fetch=True,
    )[0]["n"]

    s = sql(
        """
        SELECT COALESCE(SUM(amount),0) n
        FROM contributions
        WHERE module='Equb'
        AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    r = sql(
        """
        SELECT COUNT(*) n
        FROM equb_rounds
        """,
        fetch=True,
    )[0]["n"]

    p = sql(
        """
        SELECT COALESCE(SUM(total_pool),0) n
        FROM equb_rounds
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric("Active Members", n)
    b.metric("Total Contributions", money(s))
    c.metric("Rounds", r)
    d.metric("Recorded Pools", money(p))

    st.markdown(
        """
        <div class="info-box">
        <strong>Equb operating model:</strong>
        Each Equb group or branch can define a regular contribution.
        Members make payments for rounds. The platform records the
        round pool and demonstrates a contribution-weighted selection
        model. Production governance can later add formal eligibility,
        independent randomization, approvals and reconciliation.
        </div>
        """,
        unsafe_allow_html=True,
    )


def equb_rounds():
    st.subheader("Equb Round Management")

    bs = branches("Equb")

    if not bs:
        st.warning("Create an Equb branch first.")
        return

    names = [
        f"{x['code']} | {x['name']}"
        for x in bs
    ]

    with st.form("round_form"):
        bc = st.selectbox(
            "Equb Branch",
            names,
        )

        a, b = st.columns(2)

        round_no = a.number_input(
            "Round Number",
            min_value=1,
            value=1,
            step=1,
        )

        amount = b.number_input(
            "Contribution per Member (ETB)",
            min_value=0.0,
            value=1000.0,
            step=100.0,
        )

        expected = a.number_input(
            "Expected Members",
            min_value=1,
            value=10,
            step=1,
        )

        start = b.date_input(
            "Start Date",
            date.today(),
        )

        draw = a.date_input(
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

        ok = st.form_submit_button(
            "Create Round",
            type="primary",
        )

    if ok:
        branch = bs[names.index(bc)]

        try:
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
                    round_no,
                    amount,
                    str(start),
                    str(draw),
                    expected,
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

            st.success("Round created.")
            st.rerun()

        except sqlite3.IntegrityError:
            st.error(
                "That round already exists for this branch."
            )

    x = df(
        """
        SELECT
            r.round_no AS Round_No,
            b.code AS Branch,
            r.contribution_amount AS Contribution,
            r.expected_members AS Expected_Members,
            r.total_pool AS Total_Pool,
            r.start_date AS Start_Date,
            r.draw_date AS Draw_Date,
            r.status AS Status,
            COALESCE(m.full_name,'') AS Winner
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
    st.subheader("Equb Contribution Recording")

    rounds = sql(
        """
        SELECT
            r.*,
            b.code AS branch_code
        FROM equb_rounds r
        JOIN branches b
            ON r.branch_id=b.id
        WHERE r.status IN ('Open','Closed')
        ORDER BY r.id DESC
        """,
        fetch=True,
    )

    if not rounds:
        st.info(
            "Create an open Equb round first."
        )
        return

    labels = [
        f"{r['branch_code']} | Round {r['round_no']} | "
        f"{money(r['contribution_amount'])}"
        for r in rounds
    ]

    with st.form("contribution_form"):
        rr = st.selectbox("Round", labels)
        r = rounds[labels.index(rr)]

        ms = members(
            "Equb",
            r["branch_id"],
        )

        if not ms:
            st.warning(
                "No Equb members are registered in this branch."
            )
            st.form_submit_button(
                "Record Contribution",
                disabled=True,
            )
            return

        ml = [
            f"{m['member_no']} | {m['full_name']}"
            for m in ms
        ]

        mc = st.selectbox(
            "Member",
            ml,
        )

        amount = st.number_input(
            "Amount (ETB)",
            min_value=0.0,
            value=float(
                r["contribution_amount"] or 0
            ),
            step=50.0,
        )

        cd = st.date_input(
            "Contribution Date",
            date.today(),
        )

        method = st.selectbox(
            "Payment Method",
            [
                "Cash",
                "Bank Transfer",
                "Mobile Money",
                "Other",
            ],
        )

        ref = st.text_input(
            "Payment Reference"
        )

        notes = st.text_area("Notes")

        ok = st.form_submit_button(
            "Record Contribution",
            type="primary",
        )

    if ok:
        m = ms[ml.index(mc)]

        try:
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
                    m["id"],
                    "Equb",
                    r["id"],
                    amount,
                    str(cd),
                    "Paid",
                    ref,
                    method,
                    notes,
                    now(),
                ),
            )

            total = sql(
                """
                SELECT COALESCE(SUM(amount),0) n
                FROM contributions
                WHERE round_id=?
                AND status='Paid'
                """,
                (r["id"],),
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
                    r["id"],
                ),
            )

            audit(
                "Recorded Equb contribution",
                "Equb",
                f"{m['member_no']} {amount}",
            )

            st.success(
                "Contribution recorded."
            )
            st.rerun()

        except sqlite3.IntegrityError:
            st.error(
                "This member already has a contribution for this round."
            )

    x = df(
        """
        SELECT
            c.contribution_date AS Date,
            m.member_no AS Member_No,
            m.full_name AS Member,
            b.code AS Branch,
            r.round_no AS Round,
            c.amount AS Amount,
            c.status AS Status,
            c.reference AS Reference,
            c.payment_method AS Payment_Method
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

    download(
        x,
        "idfs_equb_contributions.csv",
    )


# ============================================================
# EQUb PROBABILITY ENGINE
# ============================================================

def probability_table():
    ms = members("Equb")

    if not ms:
        return pd.DataFrame()

    values = [
        max(
            float(
                m["regular_contribution"] or 0
            ),
            0,
        )
        for m in ms
    ]

    total = sum(values)

    if total <= 0:
        probs = [
            1 / len(ms)
            for _ in ms
        ]
    else:
        probs = [
            v / total
            for v in values
        ]

    return pd.DataFrame(
        [
            {
                "Member_No": m["member_no"],
                "Member": m["full_name"],
                "Regular_Contribution": values[i],
                "Trust_Score": float(
                    m["trust_score"] or 0.5
                ),
                "Probability": probs[i],
            }
            for i, m in enumerate(ms)
        ]
    )


def equb_probability():
    st.subheader(
        "Contribution-Weighted Probability Engine"
    )

    x = probability_table()

    if x.empty:
        st.info(
            "Register Equb members first."
        )
        return

    if x["Regular_Contribution"].sum() <= 0:
        st.warning(
            "All regular contributions are zero; "
            "equal probabilities are used."
        )

    display = x.copy()

    display["Regular_Contribution"] = display[
        "Regular_Contribution"
    ].map(lambda v: f"{v:,.2f}")

    display["Trust_Score"] = display[
        "Trust_Score"
    ].map(lambda v: f"{v:.2f}")

    display["Probability"] = display[
        "Probability"
    ].map(lambda v: f"{v:.2%}")

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    a, b = st.columns(2)

    a.metric(
        "Total Regular Contribution",
        money(
            x["Regular_Contribution"].sum()
        ),
    )

    b.metric(
        "Members",
        len(x),
    )

    if st.button(
        "Run Weighted Demonstration",
        type="primary",
        use_container_width=True,
    ):
        ms = members("Equb")

        weights = x["Probability"].tolist()

        selected = random.choices(
            ms,
            weights=weights,
            k=1,
        )[0]

        st.success(
            f"Selected demonstration member: "
            f"{selected['full_name']} "
            f"({selected['member_no']})"
        )

        audit(
            "Executed weighted probability demonstration",
            "Equb",
            selected["member_no"],
        )

    st.markdown(
        """
        <div class="info-box">
        <strong>Model note:</strong>
        For member <em>i</em>, the demonstration probability is
        proportional to positive regular contribution
        C<sub>i</sub>:
        p<sub>i</sub> = C<sub>i</sub> / ΣC<sub>j</sub>.
        If all contributions are zero, equal probabilities are
        assigned. This is a research and technology-transfer
        prototype, not a claim that this rule must govern every
        Equb.
        </div>
        """,
        unsafe_allow_html=True,
    )


def equb_history():
    x = df(
        """
        SELECT
            r.round_no AS Round_No,
            b.code AS Branch,
            r.total_pool AS Pool,
            r.draw_date AS Draw_Date,
            COALESCE(m.member_no,'') AS Winner_No,
            COALESCE(m.full_name,'') AS Winner,
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

    download(
        x,
        "idfs_equb_rounds.csv",
    )


# ============================================================
# IDDIR
# ============================================================

def iddir():
    header(
        "Module 7: IDFS Iddir",
        "Community risk sharing for funeral, wedding, holiday, emergency and other approved needs",
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
    n = sql(
        """
        SELECT COUNT(*) n
        FROM members
        WHERE module='Iddir'
        AND status='Active'
        """,
        fetch=True,
    )[0]["n"]

    benefit = sql(
        """
        SELECT COALESCE(SUM(approved_amount),0) n
        FROM iddir_events
        WHERE status IN ('Approved','Paid')
        """,
        fetch=True,
    )[0]["n"]

    pv = sql(
        """
        SELECT COALESCE(SUM(current_value),0) n
        FROM properties
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    pending = sql(
        """
        SELECT COUNT(*) n
        FROM iddir_events
        WHERE status='Pending'
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric("Active Members", n)
    b.metric(
        "Approved Support",
        money(benefit),
    )
    c.metric(
        "Active Property Value",
        money(pv),
    )
    d.metric(
        "Pending Cases",
        pending,
    )

    st.markdown(
        """
        <div class="info-box">
        <strong>Iddir operating scope:</strong>
        The platform records community support cases for funeral,
        wedding, holiday, emergency, medical, family and other
        approved purposes. It also maintains community and
        operational property such as land, buildings, vehicles,
        equipment and furniture.
        </div>
        """,
        unsafe_allow_html=True,
    )


def iddir_events():
    st.subheader(
        "Community Event and Benefit Management"
    )

    ms = members("Iddir")

    if not ms:
        st.info(
            "Register Iddir members first."
        )
        return

    labels = [
        f"{m['member_no']} | {m['full_name']}"
        for m in ms
    ]

    with st.form("iddir_event"):
        mc = st.selectbox(
            "Member / Beneficiary",
            labels,
        )

        typ = st.selectbox(
            "Event Type",
            EVENT_TYPES,
        )

        ed = st.date_input(
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

        ref = st.text_input(
            "Case / Payment Reference"
        )

        desc = st.text_area(
            "Description"
        )

        ok = st.form_submit_button(
            "Record Community Support Case",
            type="primary",
        )

    if ok:
        m = ms[labels.index(mc)]

        paid = (
            str(date.today())
            if status == "Paid"
            else None
        )

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
                m["branch_id"],
                typ,
                m["id"],
                str(ed),
                desc,
                requested,
                approved,
                status,
                paid,
                ref,
                now(),
            ),
        )

        if status == "Paid" and approved > 0:
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
                    m["branch_id"],
                    m["id"],
                    "Community Benefit Payment",
                    approved,
                    ref,
                    str(ed),
                    typ + " support",
                    now(),
                ),
            )

        audit(
            "Recorded Iddir support case",
            "Iddir",
            f"{typ} for {m['member_no']}",
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

    bs = branches("Iddir")

    if not bs:
        st.warning(
            "Create an Iddir branch first."
        )
        return

    names = [
        f"{b['code']} | {b['name']}"
        for b in bs
    ]

    with st.form("property_form"):
        bc = st.selectbox(
            "Iddir Branch",
            names,
        )

        a, b = st.columns(2)

        code = a.text_input(
            "Property Code",
            placeholder="PROP-001",
        )

        typ = b.selectbox(
            "Property Type",
            PROPERTY_TYPES,
        )

        desc = a.text_input(
            "Description"
        )

        loc = b.text_input(
            "Location"
        )

        ad = a.date_input(
            "Acquisition Date",
            date.today(),
        )

        cost = b.number_input(
            "Acquisition Cost (ETB)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
        )

        value = a.number_input(
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

        cust = a.text_input(
            "Custodian"
        )

        notes = st.text_area(
            "Notes"
        )

        ok = st.form_submit_button(
            "Register Property",
            type="primary",
        )

    if ok:
        if not code.strip():
            st.error(
                "Property code is required."
            )
        else:
            branch = bs[names.index(bc)]

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
                        code.strip(),
                        typ,
                        desc,
                        loc,
                        str(ad),
                        cost,
                        value,
                        status,
                        cust,
                        notes,
                        now(),
                    ),
                )

                audit(
                    "Registered Iddir property",
                    "Iddir",
                    code,
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
            b.name AS Branch,
            p.location AS Location,
            p.acquisition_date AS Acquisition_Date,
            p.acquisition_cost AS Acquisition_Cost,
            p.current_value AS Current_Value,
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
# TRANSACTIONS
# ============================================================

def transactions():
    header(
        "Module 8: Transactions",
        "Unified financial transaction register for the prototype",
    )

    with st.form("transaction_form"):
        a, b = st.columns(2)

        module = a.selectbox(
            "Module",
            MODULES,
        )

        typ = b.selectbox(
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

        td = a.date_input(
            "Transaction Date",
            date.today(),
        )

        desc = b.text_area(
            "Description"
        )

        ok = st.form_submit_button(
            "Record Transaction",
            type="primary",
        )

    if ok:
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
                typ,
                amount,
                reference,
                str(td),
                desc,
                now(),
            ),
        )

        audit(
            "Recorded transaction",
            module,
            f"{typ}: {amount}",
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

    download(
        x,
        "idfs_transactions.csv",
    )


# ============================================================
# REPORTS
# ============================================================

def reports():
    header(
        "Module 9: Reports and Analytics",
        "Management information for the IDFS technology-transfer prototype",
    )

    typ = st.selectbox(
        "Report",
        [
            "Module Summary",
            "Equb Contributions",
            "Equb Rounds",
            "Equb Probability",
            "Iddir Community Support",
            "Iddir Properties",
            "Transactions",
        ],
    )

    if typ == "Module Summary":
        q = """
        SELECT
            module AS Module,
            COUNT(*) AS Members,
            ROUND(
                AVG(regular_contribution),2
            ) AS Average_Regular_Contribution,
            ROUND(
                AVG(trust_score),3
            ) AS Average_Trust
        FROM members
        WHERE status='Active'
        GROUP BY module
        """

    elif typ == "Equb Contributions":
        q = """
        SELECT
            m.member_no AS Member_No,
            m.full_name AS Member,
            COUNT(c.id) AS Payments,
            COALESCE(SUM(c.amount),0)
                AS Total_Paid
        FROM members m
        LEFT JOIN contributions c
            ON m.id=c.member_id
            AND c.module='Equb'
            AND c.status='Paid'
        WHERE m.module='Equb'
        GROUP BY m.id
        ORDER BY Total_Paid DESC
        """

    elif typ == "Equb Rounds":
        q = """
        SELECT
            r.round_no AS Round_No,
            b.code AS Branch,
            r.contribution_amount AS Contribution,
            r.expected_members AS Members,
            r.total_pool AS Total_Pool,
            r.start_date AS Start_Date,
            r.draw_date AS Draw_Date,
            r.status AS Status,
            COALESCE(m.full_name,'') AS Winner
        FROM equb_rounds r
        JOIN branches b
            ON r.branch_id=b.id
        LEFT JOIN members m
            ON r.winner_member_id=m.id
        ORDER BY r.id DESC
        """

    elif typ == "Equb Probability":
        x = probability_table()

        if x.empty:
            st.info(
                "Register Equb members first."
            )
        else:
            st.dataframe(
                x,
                use_container_width=True,
                hide_index=True,
            )

            download(
                x,
                "idfs_equb_probability.csv",
            )

        return

    elif typ == "Iddir Community Support":
        q = """
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

    elif typ == "Iddir Properties":
        q = """
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

    else:
        q = """
        SELECT
            module AS Module,
            transaction_type AS Transaction_Type,
            COUNT(*) AS Transactions,
            COALESCE(
                SUM(amount),0
            ) AS Total_Amount
        FROM transactions
        GROUP BY module,transaction_type
        ORDER BY module,Total_Amount DESC
        """

    x = df(q)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    download(
        x,
        "idfs_report.csv",
    )


# ============================================================
# AUDIT
# ============================================================

def audit_page():
    header(
        "Module 10: Audit Trail",
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

    download(
        x,
        "idfs_audit.csv",
    )


# ============================================================
# USER ADMINISTRATION
# ============================================================

def users_page():
    header(
        "Module 11: User Administration",
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

        u = a.text_input(
            "Username"
        )

        n = b.text_input(
            "Full Name"
        )

        p = a.text_input(
            "Password",
            type="password",
        )

        r = b.selectbox(
            "Role",
            ROLES,
        )

        m = a.selectbox(
            "Module",
            ["Portal"] + MODULES,
        )

        bs = branches(
            m if m in MODULES else None
        )

        bo = ["No branch"] + [
            f"{x['code']} | {x['name']}"
            for x in bs
        ]

        bc = b.selectbox(
            "Branch",
            bo,
        )

        ok = st.form_submit_button(
            "Create User",
            type="primary",
        )

    if ok:
        if not u.strip() or not n.strip():
            st.error(
                "Username and full name are required."
            )
        elif len(p) < 6:
            st.error(
                "Password must contain at least six characters."
            )
        else:
            bid = (
                None
                if bc == "No branch"
                else bs[bo.index(bc) - 1]["id"]
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
                        created_at
                    )
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        u.strip(),
                        pwd_hash(p),
                        n.strip(),
                        r,
                        m,
                        bid,
                        now(),
                    ),
                )

                audit(
                    "Created user",
                    "Portal",
                    u,
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
    if not st.session_state.get(
        "authenticated",
        False,
    ):
        login()
        return

    with st.sidebar:
        st.markdown("## IDFS")
        st.caption(
            "Indigenous Digital Financial System"
        )

        st.write(
            f"User: **{st.session_state.get('full_name','')}**"
        )

        st.write(
            f"Role: **{st.session_state.get('role','')}**"
        )

        if st.button(
            "Sign out",
            use_container_width=True,
        ):
            audit("Logout")
            st.session_state.clear()
            st.rerun()

        st.divider()

        nav = [
            "Dashboard",
            "Branch Management",
            "Member Management",
            "IDFS Equb",
            "IDFS Iddir",
            "Transactions",
            "Reports and Analytics",
            "Audit Trail",
        ]

        if (
            st.session_state.get("role")
            == "Administrator"
        ):
            nav.append(
                "User Administration"
            )

        page = st.radio(
            "Navigation",
            nav,
        )

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
