import streamlit as st
import sqlite3
import hashlib
import secrets
import hmac
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# IDFS — IDDIR APP MANAGEMENT SYSTEM
# Enterprise Demonstration Version
# Indigenous Digital Financial System
# ============================================================

st.set_page_config(
    page_title="IDFS Iddir App",
    page_icon="I",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = Path("iddir_demo.db")

ROLES = [
    "Administrator",
    "Branch Manager",
    "Finance Officer",
    "Member",
]

MODULE = "Iddir"


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2rem;
        font-weight: 750;
        color: #163A5F;
        margin-bottom: .15rem;
    }

    .sub-title {
        color: #64748B;
        margin-bottom: 1.1rem;
        font-size: .98rem;
    }

    .section-card {
        padding: 1.15rem 1.35rem;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        background: #F8FAFC;
        margin-bottom: 1rem;
    }

    .module-label {
        color: #0B5CAD;
        font-weight: 750;
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .04em;
    }

    .manual-card {
        padding: 1.1rem 1.3rem;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        background: white;
        margin-bottom: 1rem;
    }

    .metric-card {
        padding: .9rem;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background: white;
    }

    .success-card {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
    }

    .warning-card {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        background: #FFFBEB;
        border: 1px solid #FDE68A;
    }

    .danger-card {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        background: #FEF2F2;
        border: 1px solid #FECACA;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #E2E8F0;
        padding: .65rem;
        border-radius: 10px;
        background: white;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# UTILITIES
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    try:
        return f"{float(value):,.2f} ETB"
    except Exception:
        return "0.00 ETB"


def sql(query, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute(query, params)

        if fetch:
            result = [dict(row) for row in cur.fetchall()]
        else:
            result = None

        conn.commit()
        return result

    finally:
        conn.close()


def df(query, params=()):
    return pd.DataFrame(sql(query, params, fetch=True))


def download(data, filename):
    if data is not None and not data.empty:
        st.download_button(
            "Download CSV",
            data.to_csv(index=False).encode("utf-8"),
            filename,
            "text/csv",
            use_container_width=True,
        )


def pwd_hash(password):
    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000,
    ).hex()

    return f"{salt}${digest}"


def check_pwd(password, stored):
    try:
        salt, digest = stored.split("$", 1)

        test = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000,
        ).hex()

        return hmac.compare_digest(test, digest)

    except Exception:
        return False


def audit(action, module="Portal", details=""):
    sql(
        """
        INSERT INTO audit_log
        (username, module, action, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            st.session_state.get("username", "system"),
            module,
            action,
            details,
            now(),
        ),
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


def get_branch_options():
    rows = sql(
        """
        SELECT *
        FROM branches
        WHERE module=?
        ORDER BY name
        """,
        (MODULE,),
        fetch=True,
    )

    return rows


def get_groups(active_only=False):
    query = """
        SELECT *
        FROM iddir_groups
    """

    if active_only:
        query += " WHERE status='Active'"

    query += " ORDER BY group_name"

    return sql(query, fetch=True)


def get_members(active_only=False):
    query = """
        SELECT
            m.*,
            b.code AS branch_code,
            b.name AS branch_name
        FROM members m
        LEFT JOIN branches b
            ON m.branch_id=b.id
        WHERE m.module=?
    """

    params = [MODULE]

    if active_only:
        query += " AND m.status='Active'"

    query += " ORDER BY m.full_name"

    return sql(query, params, fetch=True)


def member_label(member):
    return f"{member['member_no']} | {member['full_name']}"


def group_label(group):
    return f"{group['group_code']} | {group['group_name']}"


def branch_label(branch):
    return f"{branch['code']} | {branch['name']}"


# ============================================================
# DATABASE
# ============================================================

def init_db():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.executescript(
        """

        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT,
            module TEXT,
            branch_id INTEGER,
            active INTEGER DEFAULT 1,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS branches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            module TEXT DEFAULT 'Iddir',
            location TEXT,
            manager TEXT,
            phone TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_no TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            household_no TEXT,
            phone TEXT,
            sex TEXT,
            birth_date TEXT,
            join_date TEXT,
            module TEXT DEFAULT 'Iddir',
            branch_id INTEGER,

            registration_contribution REAL DEFAULT 0,
            regular_contribution REAL DEFAULT 0,
            contribution_frequency TEXT DEFAULT 'Monthly',

            trust_score REAL DEFAULT 0.50,

            status TEXT DEFAULT 'Active',
            address TEXT,
            occupation TEXT,
            notes TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS iddir_groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER,
            group_code TEXT UNIQUE NOT NULL,
            group_name TEXT NOT NULL,

            registration_contribution REAL DEFAULT 0,
            contribution_amount REAL DEFAULT 0,
            contribution_frequency TEXT DEFAULT 'Monthly',

            founding_date TEXT,
            member_capacity INTEGER DEFAULT 0,

            emergency_fund REAL DEFAULT 0,
            property_value REAL DEFAULT 0,

            status TEXT DEFAULT 'Active',
            notes TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS group_members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            member_id INTEGER,
            role TEXT DEFAULT 'Member',
            joined_date TEXT,
            status TEXT DEFAULT 'Active',

            UNIQUE(group_id, member_id)
        );

        CREATE TABLE IF NOT EXISTS contributions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            member_id INTEGER,
            group_id INTEGER,

            module TEXT DEFAULT 'Iddir',

            contribution_type TEXT DEFAULT 'Regular',

            amount_due REAL DEFAULT 0,
            amount REAL DEFAULT 0,

            contribution_period TEXT,
            contribution_date TEXT,

            status TEXT DEFAULT 'Paid',

            reference TEXT,
            payment_method TEXT,
            notes TEXT,

            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS benefits(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            group_id INTEGER,
            member_id INTEGER,

            benefit_type TEXT,

            event_date TEXT,

            requested_amount REAL DEFAULT 0,
            approved_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,

            status TEXT DEFAULT 'Requested',

            reference TEXT,
            description TEXT,

            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            group_id INTEGER,

            event_type TEXT,
            event_date TEXT,

            household_count INTEGER DEFAULT 0,

            estimated_cost REAL DEFAULT 0,
            actual_cost REAL DEFAULT 0,

            status TEXT DEFAULT 'Planned',

            location TEXT,
            notes TEXT,

            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS properties(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            group_id INTEGER,

            property_type TEXT,
            property_name TEXT,
            description TEXT,

            acquisition_date TEXT,

            acquisition_cost REAL DEFAULT 0,
            current_value REAL DEFAULT 0,

            quantity REAL DEFAULT 1,

            condition_status TEXT DEFAULT 'Good',
            ownership_status TEXT DEFAULT 'Community',

            location TEXT,
            responsible_person TEXT,

            notes TEXT,

            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS property_transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            property_id INTEGER,

            transaction_type TEXT,
            amount REAL DEFAULT 0,

            transaction_date TEXT,

            reference TEXT,
            description TEXT,

            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            module TEXT DEFAULT 'Iddir',

            branch_id INTEGER,
            group_id INTEGER,
            member_id INTEGER,

            transaction_type TEXT,

            amount REAL DEFAULT 0,

            reference TEXT,

            transaction_date TEXT,

            description TEXT,

            created_at TEXT
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

    conn.commit()
    conn.close()

    # --------------------------------------------------------
    # Database migration for older versions
    # --------------------------------------------------------

    migrate_database()

    # --------------------------------------------------------
    # Administrator
    # --------------------------------------------------------

    if not sql(
        "SELECT id FROM users WHERE username='admin'",
        fetch=True,
    ):
        sql(
            """
            INSERT INTO users
            (
                username,
                password_hash,
                full_name,
                role,
                module,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "admin",
                pwd_hash("admin123"),
                "Iddir Administrator",
                "Administrator",
                "Portal",
                1,
                now(),
            ),
        )

    # --------------------------------------------------------
    # Demonstration branches
    # --------------------------------------------------------

    demo_branches = [
        ("IDR-001", "Iddir Central Branch", "Aksum"),
        ("IDR-002", "Iddir North Branch", "Shire"),
    ]

    for code, name, location in demo_branches:

        existing = sql(
            """
            SELECT id
            FROM branches
            WHERE code=?
            """,
            (code,),
            fetch=True,
        )

        if not existing:

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    name,
                    MODULE,
                    location,
                    "Branch Manager",
                    "",
                    "Active",
                    now(),
                ),
            )


def migrate_database():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    def columns(table):
        return [
            row[1]
            for row in cur.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        ]

    member_columns = columns("members")

    if "registration_contribution" not in member_columns:

        cur.execute(
            """
            ALTER TABLE members
            ADD COLUMN registration_contribution
            REAL DEFAULT 0
            """
        )

    contribution_columns = columns("contributions")

    if "contribution_type" not in contribution_columns:

        cur.execute(
            """
            ALTER TABLE contributions
            ADD COLUMN contribution_type
            TEXT DEFAULT 'Regular'
            """
        )

    if "amount_due" not in contribution_columns:

        cur.execute(
            """
            ALTER TABLE contributions
            ADD COLUMN amount_due
            REAL DEFAULT 0
            """
        )

    if "contribution_period" not in contribution_columns:

        cur.execute(
            """
            ALTER TABLE contributions
            ADD COLUMN contribution_period
            TEXT
            """
        )

    benefit_columns = columns("benefits")

    if "requested_amount" not in benefit_columns:

        cur.execute(
            """
            ALTER TABLE benefits
            ADD COLUMN requested_amount
            REAL DEFAULT 0
            """
        )

    conn.commit()
    conn.close()


# ============================================================
# LOGIN
# ============================================================

def login():

    header(
        "IDFS — Iddir App",
        "Indigenous Digital Financial System · Community mutual-support management",
    )

    st.markdown(
        """
        <div class="section-card">
        <div class="module-label">IDDIR MANAGEMENT PLATFORM</div>

        The system supports community membership, contribution
        obligations, mutual support, community events, assets,
        financial records, analytics and transparent administration.

        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):

        username = st.text_input("Username")

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

        result = sql(
            """
            SELECT *
            FROM users
            WHERE username=?
            AND active=1
            """,
            (username.strip(),),
            fetch=True,
        )

        if result and check_pwd(
            password,
            result[0]["password_hash"],
        ):

            user = result[0]

            st.session_state.update(
                authenticated=True,
                username=user["username"],
                full_name=user["full_name"],
                role=user["role"],
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
# DASHBOARD
# ============================================================

def dashboard():

    header(
        "IDFS — Iddir Executive Dashboard",
        "Community membership, contributions, mutual support, assets and financial management.",
    )

    members_count = sql(
        """
        SELECT COUNT(*) n
        FROM members
        WHERE module='Iddir'
        AND status='Active'
        """,
        fetch=True,
    )[0]["n"]

    groups_count = sql(
        """
        SELECT COUNT(*) n
        FROM iddir_groups
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    contributions = sql(
        """
        SELECT COALESCE(SUM(amount),0) n
        FROM contributions
        WHERE module='Iddir'
        AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    properties = sql(
        """
        SELECT COALESCE(
            SUM(current_value * quantity),0
        ) n
        FROM properties
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric(
        "Active Members",
        members_count,
    )

    b.metric(
        "Active Iddir Groups",
        groups_count,
    )

    c.metric(
        "Total Contributions",
        money(contributions),
    )

    d.metric(
        "Community Property",
        money(properties),
    )

    st.markdown(
        """
        <div class="section-card">
        <div class="module-label">
        Indigenous Digital Financial System
        </div>

        <b>Iddir module</b> provides digital infrastructure for
        indigenous community mutual-support organizations.

        It connects members, contribution obligations, collective
        funds, support benefits, community events, assets,
        financial transactions and analytical indicators in one
        management environment.

        </div>
        """,
        unsafe_allow_html=True,
    )

    benefits = sql(
        """
        SELECT COALESCE(SUM(paid_amount),0) n
        FROM benefits
        WHERE status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    emergency = sql(
        """
        SELECT COALESCE(SUM(emergency_fund),0) n
        FROM iddir_groups
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    outstanding = sql(
        """
        SELECT COALESCE(
            SUM(
                CASE
                    WHEN amount_due > amount
                    THEN amount_due - amount
                    ELSE 0
                END
            ),0
        ) n
        FROM contributions
        WHERE module='Iddir'
        """,
        fetch=True,
    )[0]["n"]

    events_count = sql(
        """
        SELECT COUNT(*) n
        FROM events
        """,
        fetch=True,
    )[0]["n"]

    a, b, c, d = st.columns(4)

    a.metric(
        "Benefits Paid",
        money(benefits),
    )

    b.metric(
        "Emergency Fund",
        money(emergency),
    )

    c.metric(
        "Outstanding Contributions",
        money(outstanding),
    )

    d.metric(
        "Community Events",
        events_count,
    )

    st.subheader("Contribution Trend")

    trend = df(
        """
        SELECT
            contribution_date Date,
            SUM(amount) Amount
        FROM contributions
        WHERE module='Iddir'
        AND status='Paid'
        GROUP BY contribution_date
        ORDER BY contribution_date
        """
    )

    if not trend.empty:

        trend["Date"] = pd.to_datetime(
            trend["Date"]
        )

        st.line_chart(
            trend.set_index("Date")["Amount"]
        )

    st.subheader("Recent System Activities")

    activity = df(
        """
        SELECT
            timestamp Timestamp,
            username User,
            module Module,
            action Action,
            details Details
        FROM audit_log
        ORDER BY id DESC
        LIMIT 15
        """
    )

    if not activity.empty:

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
        "Module 2: Branch Management",
        "Manage the organizational structure of the Iddir network.",
    )

    tab1, tab2 = st.tabs(
        [
            "Branch Directory",
            "Register Branch",
        ]
    )

    with tab1:

        x = df(
            """
            SELECT
                code Branch_Code,
                name Branch_Name,
                location Location,
                manager Manager,
                phone Phone,
                status Status
            FROM branches
            WHERE module='Iddir'
            ORDER BY name
            """
        )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        download(
            x,
            "iddir_branches.csv",
        )

    with tab2:

        with st.form("branch_form"):

            a, b = st.columns(2)

            code = a.text_input(
                "Branch Code"
            )

            name = b.text_input(
                "Branch Name"
            )

            location = a.text_input(
                "Location"
            )

            manager = b.text_input(
                "Manager"
            )

            phone = a.text_input(
                "Phone"
            )

            status = b.selectbox(
                "Status",
                ["Active", "Inactive"],
            )

            submitted = st.form_submit_button(
                "Register Branch",
                type="primary",
                use_container_width=True,
            )

        if submitted:

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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            code.strip(),
                            name.strip(),
                            MODULE,
                            location,
                            manager,
                            phone,
                            status,
                            now(),
                        ),
                    )

                    audit(
                        "Created branch",
                        MODULE,
                        code,
                    )

                    st.success(
                        "Branch registered successfully."
                    )

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
        "Module 3: Member Management",
        "Register members and define their contribution obligations.",
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Member Directory",
            "Register Member",
            "Member Profile",
        ]
    )

    # --------------------------------------------------------
    # DIRECTORY
    # --------------------------------------------------------

    with tab1:

        x = df(
            """
            SELECT
                m.member_no Member_No,
                m.full_name Full_Name,
                m.household_no Household_No,
                COALESCE(b.name,'') Branch,
                m.phone Phone,

                m.registration_contribution
                    Registration_Contribution,

                m.regular_contribution
                    Regular_Contribution,

                m.contribution_frequency
                    Frequency,

                m.join_date Join_Date,
                m.trust_score Trust_Score,
                m.status Status

            FROM members m

            LEFT JOIN branches b
                ON m.branch_id=b.id

            WHERE m.module='Iddir'

            ORDER BY m.full_name
            """
        )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        download(
            x,
            "iddir_members.csv",
        )

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    with tab2:

        branches_list = get_branch_options()

        branch_options = [
            branch_label(b)
            for b in branches_list
        ]

        with st.form("member_registration"):

            st.markdown(
                "### Identity and Household Information"
            )

            a, b, c = st.columns(3)

            member_no = a.text_input(
                "Member Number *"
            )

            full_name = b.text_input(
                "Full Name *"
            )

            household_no = c.text_input(
                "Household Number"
            )

            phone = a.text_input(
                "Phone"
            )

            sex = b.selectbox(
                "Sex",
                [
                    "Not Specified",
                    "Male",
                    "Female",
                ],
            )

            birth_date = c.date_input(
                "Birth Date",
                date(1990, 1, 1),
            )

            join_date = a.date_input(
                "Join Date",
                date.today(),
            )

            branch = b.selectbox(
                "Branch",
                branch_options or ["No branch"],
            )

            occupation = c.text_input(
                "Occupation"
            )

            st.markdown(
                "### Contribution Obligation"
            )

            a, b, c = st.columns(3)

            registration_contribution = (
                a.number_input(
                    "Registration Contribution (ETB)",
                    min_value=0.0,
                    step=50.0,
                    value=0.0,
                )
            )

            regular_contribution = (
                b.number_input(
                    "Regular Contribution (ETB)",
                    min_value=0.0,
                    step=50.0,
                    value=100.0,
                )
            )

            frequency = c.selectbox(
                "Contribution Frequency",
                [
                    "Monthly",
                    "Quarterly",
                    "Weekly",
                    "Annual",
                    "Custom",
                ],
            )

            st.markdown(
                "### Membership Status"
            )

            a, b, c = st.columns(3)

            trust = a.number_input(
                "Initial Trust Score (%)",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
                step=1.0,
            )

            status = b.selectbox(
                "Status",
                [
                    "Active",
                    "Inactive",
                    "Suspended",
                ],
            )

            address = c.text_input(
                "Address"
            )

            notes = st.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Register Member",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            if not member_no.strip():

                st.error(
                    "Member number is required."
                )

            elif not full_name.strip():

                st.error(
                    "Full name is required."
                )

            else:

                branch_id = None

                if branch != "No branch":

                    branch_id = branches_list[
                        branch_options.index(branch)
                    ]["id"]

                try:

                    sql(
                        """
                        INSERT INTO members
                        (
                            member_no,
                            full_name,
                            household_no,
                            phone,
                            sex,
                            birth_date,
                            join_date,
                            module,
                            branch_id,

                            registration_contribution,
                            regular_contribution,
                            contribution_frequency,

                            trust_score,
                            status,

                            address,
                            occupation,
                            notes,

                            created_at
                        )
                        VALUES
                        (
                            ?,?,?,?,?,?,?,?,
                            ?,?,?,?,
                            ?,?,?,?,?
                        )
                        """,
                        (
                            member_no.strip(),
                            full_name.strip(),
                            household_no,
                            phone,
                            sex,
                            str(birth_date),
                            str(join_date),
                            MODULE,
                            branch_id,

                            registration_contribution,
                            regular_contribution,
                            frequency,

                            trust / 100,
                            status,

                            address,
                            occupation,
                            notes,

                            now(),
                        ),
                    )

                    audit(
                        "Registered member",
                        MODULE,
                        member_no,
                    )

                    st.success(
                        "Member registered successfully."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Member number already exists."
                    )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    with tab3:

        ms = get_members()

        if not ms:

            st.info(
                "No members registered yet."
            )

        else:

            labels = [
                member_label(m)
                for m in ms
            ]

            selected = st.selectbox(
                "Select Member",
                labels,
            )

            m = ms[
                labels.index(selected)
            ]

            history = df(
                """
                SELECT
                    contribution_date Date,
                    contribution_type Type,
                    contribution_period Period,
                    amount_due Amount_Due,
                    amount Amount_Paid,
                    status Status,
                    payment_method Payment_Method,
                    reference Reference
                FROM contributions
                WHERE member_id=?
                AND module='Iddir'
                ORDER BY id DESC
                """,
                (m["id"],),
            )

            total_paid = (
                history["Amount_Paid"].sum()
                if not history.empty
                else 0
            )

            total_due = (
                history["Amount_Due"].sum()
                if not history.empty
                else 0
            )

            outstanding = max(
                total_due - total_paid,
                0,
            )

            a, b, c, d = st.columns(4)

            a.metric(
                "Regular Obligation",
                money(
                    m["regular_contribution"]
                ),
            )

            b.metric(
                "Total Paid",
                money(total_paid),
            )

            c.metric(
                "Outstanding",
                money(outstanding),
            )

            d.metric(
                "Trust Score",
                f"{m['trust_score']:.0%}",
            )

            st.subheader(
                "Member Information"
            )

            profile = pd.DataFrame(
                [
                    {
                        "Member Number":
                            m["member_no"],

                        "Full Name":
                            m["full_name"],

                        "Household":
                            m["household_no"],

                        "Branch":
                            m["branch_name"] or "",

                        "Phone":
                            m["phone"] or "",

                        "Registration Contribution":
                            m["registration_contribution"],

                        "Regular Contribution":
                            m["regular_contribution"],

                        "Frequency":
                            m["contribution_frequency"],

                        "Join Date":
                            m["join_date"],

                        "Trust Score":
                            f"{m['trust_score']:.2%}",

                        "Status":
                            m["status"],
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
                    "No contribution records."
                )

            else:

                st.dataframe(
                    history,
                    use_container_width=True,
                    hide_index=True,
                )


# ============================================================
# IDDIR GROUP MANAGEMENT
# ============================================================

def group_page():

    header(
        "Module 4: Iddir Group Management",
        "Create groups and define collective contribution obligations.",
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Group Directory",
            "Register Group",
            "Group Membership",
        ]
    )

    with tab1:

        x = df(
            """
            SELECT
                g.group_code Group_Code,
                g.group_name Group_Name,
                b.code Branch,

                g.registration_contribution
                    Registration_Contribution,

                g.contribution_amount
                    Regular_Contribution,

                g.contribution_frequency
                    Frequency,

                g.member_capacity Capacity,

                g.emergency_fund Emergency_Fund,

                g.property_value Property_Value,

                g.founding_date Founding_Date,
                g.status Status

            FROM iddir_groups g

            LEFT JOIN branches b
                ON g.branch_id=b.id

            ORDER BY g.group_name
            """
        )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        download(
            x,
            "iddir_groups.csv",
        )

    with tab2:

        branches_list = get_branch_options()

        branch_options = [
            branch_label(b)
            for b in branches_list
        ]

        with st.form("group_registration"):

            a, b = st.columns(2)

            code = a.text_input(
                "Group Code *"
            )

            name = b.text_input(
                "Group Name *"
            )

            branch = a.selectbox(
                "Branch",
                branch_options or ["No branch"],
            )

            registration = b.number_input(
                "Registration Contribution (ETB)",
                min_value=0.0,
                step=50.0,
            )

            amount = a.number_input(
                "Regular Contribution (ETB)",
                min_value=0.0,
                step=10.0,
                value=100.0,
            )

            frequency = b.selectbox(
                "Contribution Frequency",
                [
                    "Monthly",
                    "Quarterly",
                    "Weekly",
                    "Annual",
                ],
            )

            founding = a.date_input(
                "Founding Date",
                date.today(),
            )

            capacity = b.number_input(
                "Member Capacity",
                min_value=0,
                step=1,
                value=100,
            )

            emergency = a.number_input(
                "Initial Emergency Fund (ETB)",
                min_value=0.0,
                step=100.0,
            )

            property_value = b.number_input(
                "Initial Property Value (ETB)",
                min_value=0.0,
                step=100.0,
            )

            status = a.selectbox(
                "Status",
                [
                    "Active",
                    "Inactive",
                ],
            )

            notes = st.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Register Iddir Group",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            if not code.strip():

                st.error(
                    "Group code is required."
                )

            elif not name.strip():

                st.error(
                    "Group name is required."
                )

            else:

                branch_id = None

                if branch != "No branch":

                    branch_id = branches_list[
                        branch_options.index(branch)
                    ]["id"]

                try:

                    sql(
                        """
                        INSERT INTO iddir_groups
                        (
                            branch_id,
                            group_code,
                            group_name,

                            registration_contribution,
                            contribution_amount,
                            contribution_frequency,

                            founding_date,
                            member_capacity,

                            emergency_fund,
                            property_value,

                            status,
                            notes,
                            created_at
                        )
                        VALUES
                        (
                            ?,?,?,?,
                            ?,?,?,
                            ?,?,
                            ?,?,
                            ?,?,?
                        )
                        """,
                        (
                            branch_id,
                            code.strip(),
                            name.strip(),

                            registration,
                            amount,
                            frequency,

                            str(founding),
                            capacity,

                            emergency,
                            property_value,

                            status,
                            notes,
                            now(),
                        ),
                    )

                    audit(
                        "Created Iddir group",
                        MODULE,
                        code,
                    )

                    st.success(
                        "Iddir group registered successfully."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Group code already exists."
                    )

    with tab3:

        groups = get_groups(
            active_only=True
        )

        ms = get_members(
            active_only=True
        )

        if not groups or not ms:

            st.info(
                "Create an active group and register active members first."
            )

            return

        gl = [
            group_label(g)
            for g in groups
        ]

        ml = [
            member_label(m)
            for m in ms
        ]

        with st.form("group_member_form"):

            a, b = st.columns(2)

            selected_group = a.selectbox(
                "Iddir Group",
                gl,
            )

            selected_member = b.selectbox(
                "Member",
                ml,
            )

            role = a.selectbox(
                "Role",
                [
                    "Member",
                    "Chairperson",
                    "Secretary",
                    "Treasurer",
                    "Committee Member",
                ],
            )

            joined = b.date_input(
                "Joined Date",
                date.today(),
            )

            submitted = st.form_submit_button(
                "Add Member to Group",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            group = groups[
                gl.index(selected_group)
            ]

            member = ms[
                ml.index(selected_member)
            ]

            try:

                sql(
                    """
                    INSERT INTO group_members
                    (
                        group_id,
                        member_id,
                        role,
                        joined_date,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        group["id"],
                        member["id"],
                        role,
                        str(joined),
                        "Active",
                    ),
                )

                audit(
                    "Added member to group",
                    MODULE,
                    f"{member['member_no']} -> {group['group_code']}",
                )

                st.success(
                    "Member added to group."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                st.error(
                    "This member is already in the selected group."
                )

        x = df(
            """
            SELECT
                g.group_code Group_Code,
                g.group_name Group_Name,
                m.member_no Member_No,
                m.full_name Member,
                gm.role Role,
                gm.joined_date Joined_Date,
                gm.status Status

            FROM group_members gm

            JOIN iddir_groups g
                ON gm.group_id=g.id

            JOIN members m
                ON gm.member_id=m.id

            ORDER BY
                g.group_name,
                m.full_name
            """
        )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# CONTRIBUTION MANAGEMENT
# ============================================================

def contribution_page():

    header(
        "Module 5: Contributions",
        "Record registration, regular and other community contributions.",
    )

    groups = get_groups(
        active_only=True
    )

    ms = get_members(
        active_only=True
    )

    if not groups or not ms:

        st.info(
            "Create an active group and register active members first."
        )

        return

    gl = [
        group_label(g)
        for g in groups
    ]

    ml = [
        member_label(m)
        for m in ms
    ]

    with st.form("contribution_form"):

        a, b = st.columns(2)

        selected_group = a.selectbox(
            "Iddir Group",
            gl,
        )

        selected_member = b.selectbox(
            "Member",
            ml,
        )

        group = groups[
            gl.index(selected_group)
        ]

        member = ms[
            ml.index(selected_member)
        ]

        contribution_type = a.selectbox(
            "Contribution Type",
            [
                "Registration",
                "Regular",
                "Special",
                "Emergency Fund",
                "Other",
            ],
        )

        amount_due = b.number_input(
            "Amount Due (ETB)",
            min_value=0.0,
            step=10.0,
            value=(
                float(member["regular_contribution"])
                if member["regular_contribution"]
                else float(group["contribution_amount"])
            ),
        )

        amount = a.number_input(
            "Amount Paid (ETB)",
            min_value=0.0,
            step=10.0,
        )

        contribution_period = b.text_input(
            "Contribution Period",
            value=(
                datetime.now().strftime("%Y-%m")
            ),
        )

        contribution_date = a.date_input(
            "Payment Date",
            date.today(),
        )

        payment_method = b.selectbox(
            "Payment Method",
            [
                "Cash",
                "Bank Transfer",
                "Mobile Money",
                "Other",
            ],
        )

        reference = a.text_input(
            "Reference"
        )

        status = b.selectbox(
            "Status",
            [
                "Paid",
                "Partial",
                "Pending",
                "Waived",
                "Cancelled",
            ],
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

        if amount < 0:

            st.error(
                "Payment amount cannot be negative."
            )

        else:

            sql(
                """
                INSERT INTO contributions
                (
                    member_id,
                    group_id,
                    module,

                    contribution_type,

                    amount_due,
                    amount,

                    contribution_period,
                    contribution_date,

                    status,

                    reference,
                    payment_method,
                    notes,

                    created_at
                )
                VALUES
                (
                    ?,?,?,?,
                    ?,?,
                    ?,?,
                    ?,?,?,?
                )
                """,
                (
                    member["id"],
                    group["id"],
                    MODULE,

                    contribution_type,

                    amount_due,
                    amount,

                    contribution_period,
                    str(contribution_date),

                    status,

                    reference,
                    payment_method,
                    notes,

                    now(),
                ),
            )

            audit(
                "Recorded contribution",
                MODULE,
                f"{member['member_no']} | {amount}",
            )

            st.success(
                "Contribution recorded successfully."
            )

            st.rerun()

    st.subheader(
        "Contribution Register"
    )

    x = df(
        """
        SELECT
            c.contribution_date Date,
            c.contribution_period Period,
            c.contribution_type Type,

            g.group_code Group_Code,

            m.member_no Member_No,
            m.full_name Member,

            c.amount_due Amount_Due,
            c.amount Amount_Paid,

            CASE
                WHEN c.amount_due > c.amount
                THEN c.amount_due - c.amount
                ELSE 0
            END Outstanding,

            c.status Status,
            c.payment_method Payment_Method,
            c.reference Reference

        FROM contributions c

        JOIN members m
            ON c.member_id=m.id

        LEFT JOIN iddir_groups g
            ON c.group_id=g.id

        WHERE c.module='Iddir'

        ORDER BY c.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    download(
        x,
        "iddir_contributions.csv",
    )


# ============================================================
# BENEFITS / MUTUAL SUPPORT
# ============================================================

def benefits_page():

    header(
        "Module 6: Benefits and Mutual Support",
        "Manage community support requests, approvals and payments.",
    )

    groups = get_groups()
    ms = get_members()

    if not groups or not ms:

        st.info(
            "Register groups and members first."
        )

        return

    gl = [
        group_label(g)
        for g in groups
    ]

    ml = [
        member_label(m)
        for m in ms
    ]

    with st.form("benefit_form"):

        a, b = st.columns(2)

        selected_group = a.selectbox(
            "Iddir Group",
            gl,
        )

        selected_member = b.selectbox(
            "Beneficiary Member",
            ml,
        )

        benefit_type = a.selectbox(
            "Benefit / Support Type",
            [
                "Bereavement Support",
                "Funeral Support",
                "Emergency Medical Support",
                "Emergency Household Support",
                "Natural Disaster Support",
                "Community Support",
                "Other",
            ],
        )

        event_date = b.date_input(
            "Event Date",
            date.today(),
        )

        requested = a.number_input(
            "Requested Amount (ETB)",
            min_value=0.0,
            step=100.0,
        )

        approved = b.number_input(
            "Approved Amount (ETB)",
            min_value=0.0,
            step=100.0,
        )

        paid = a.number_input(
            "Paid Amount (ETB)",
            min_value=0.0,
            step=100.0,
        )

        status = b.selectbox(
            "Status",
            [
                "Requested",
                "Reviewed",
                "Approved",
                "Paid",
                "Rejected",
            ],
        )

        reference = a.text_input(
            "Reference"
        )

        description = st.text_area(
            "Description"
        )

        submitted = st.form_submit_button(
            "Save Support Record",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        group = groups[
            gl.index(selected_group)
        ]

        member = ms[
            ml.index(selected_member)
        ]

        if paid > approved:

            st.error(
                "Paid amount cannot exceed approved amount."
            )

        else:

            sql(
                """
                INSERT INTO benefits
                (
                    group_id,
                    member_id,
                    benefit_type,
                    event_date,

                    requested_amount,
                    approved_amount,
                    paid_amount,

                    status,
                    reference,
                    description,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group["id"],
                    member["id"],
                    benefit_type,
                    str(event_date),

                    requested,
                    approved,
                    paid,

                    status,
                    reference,
                    description,
                    now(),
                ),
            )

            audit(
                "Recorded mutual support",
                MODULE,
                f"{member['member_no']} | {benefit_type} | {paid}",
            )

            st.success(
                "Support record saved."
            )

            st.rerun()

    x = df(
        """
        SELECT
            b.event_date Event_Date,

            g.group_code Group_Code,

            m.member_no Member_No,
            m.full_name Beneficiary,

            b.benefit_type Benefit_Type,

            b.requested_amount Requested,
            b.approved_amount Approved,
            b.paid_amount Paid,

            b.status Status,

            b.reference Reference

        FROM benefits b

        JOIN members m
            ON b.member_id=m.id

        LEFT JOIN iddir_groups g
            ON b.group_id=g.id

        ORDER BY b.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    download(
        x,
        "iddir_benefits.csv",
    )


# ============================================================
# COMMUNITY EVENTS
# ============================================================

def events_page():

    header(
        "Module 7: Community Events",
        "Plan and record Iddir meetings, funerals, memorials and community activities.",
    )

    groups = get_groups()

    if not groups:

        st.info(
            "Create an Iddir group first."
        )

        return

    gl = [
        group_label(g)
        for g in groups
    ]

    with st.form("event_form"):

        a, b = st.columns(2)

        selected_group = a.selectbox(
            "Iddir Group",
            gl,
        )

        event_type = b.selectbox(
            "Event Type",
            [
                "Community Meeting",
                "Funeral",
                "Memorial",
                "Social Gathering",
                "Emergency Response",
                "Annual Meeting",
                "Other",
            ],
        )

        event_date = a.date_input(
            "Event Date",
            date.today(),
        )

        household_count = b.number_input(
            "Households / Participants",
            min_value=0,
            step=1,
        )

        estimated_cost = a.number_input(
            "Estimated Cost (ETB)",
            min_value=0.0,
            step=100.0,
        )

        actual_cost = b.number_input(
            "Actual Cost (ETB)",
            min_value=0.0,
            step=100.0,
        )

        status = a.selectbox(
            "Status",
            [
                "Planned",
                "Active",
                "Completed",
                "Cancelled",
            ],
        )

        location = b.text_input(
            "Location"
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Save Event",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        group = groups[
            gl.index(selected_group)
        ]

        sql(
            """
            INSERT INTO events
            (
                group_id,
                event_type,
                event_date,
                household_count,
                estimated_cost,
                actual_cost,
                status,
                location,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group["id"],
                event_type,
                str(event_date),
                household_count,
                estimated_cost,
                actual_cost,
                status,
                location,
                notes,
                now(),
            ),
        )

        audit(
            "Recorded community event",
            MODULE,
            event_type,
        )

        st.success(
            "Community event saved."
        )

        st.rerun()

    x = df(
        """
        SELECT
            e.event_date Date,

            g.group_code Group_Code,

            e.event_type Event_Type,
            e.household_count Participants,

            e.estimated_cost Estimated_Cost,
            e.actual_cost Actual_Cost,

            e.status Status,
            e.location Location

        FROM events e

        LEFT JOIN iddir_groups g
            ON e.group_id=g.id

        ORDER BY e.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    download(
        x,
        "iddir_events.csv",
    )


# ============================================================
# PROPERTY MANAGEMENT
# ============================================================

def property_page():

    header(
        "Module 8: Community Property",
        "Register, value and monitor assets owned by Iddir communities.",
    )

    groups = get_groups()

    tab1, tab2 = st.tabs(
        [
            "Property Register",
            "Register Property",
        ]
    )

    with tab1:

        x = df(
            """
            SELECT

                p.property_name Property,
                p.property_type Type,

                g.group_code Group_Code,

                p.quantity Quantity,

                p.acquisition_cost Acquisition_Cost,
                p.current_value Current_Value,

                p.condition_status Condition,
                p.ownership_status Ownership,

                p.location Location,
                p.responsible_person Responsible

            FROM properties p

            LEFT JOIN iddir_groups g
                ON p.group_id=g.id

            ORDER BY p.property_name
            """
        )

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True,
        )

        download(
            x,
            "iddir_property_register.csv",
        )

        if not x.empty:

            acquisition = (
                x["Acquisition_Cost"] *
                x["Quantity"]
            ).sum()

            current = (
                x["Current_Value"] *
                x["Quantity"]
            ).sum()

            a, b, c = st.columns(3)

            a.metric(
                "Acquisition Cost",
                money(acquisition),
            )

            b.metric(
                "Current Value",
                money(current),
            )

            c.metric(
                "Value Change",
                money(current - acquisition),
            )

    with tab2:

        if not groups:

            st.info(
                "Create an Iddir group first."
            )

            return

        gl = [
            group_label(g)
            for g in groups
        ]

        with st.form("property_form"):

            a, b = st.columns(2)

            selected_group = a.selectbox(
                "Iddir Group",
                gl,
            )

            property_type = b.selectbox(
                "Property Type",
                [
                    "Building",
                    "Land",
                    "Vehicle",
                    "Equipment",
                    "Furniture",
                    "Funeral Equipment",
                    "Community Asset",
                    "Other",
                ],
            )

            property_name = a.text_input(
                "Property Name"
            )

            description = b.text_area(
                "Description"
            )

            acquisition_date = a.date_input(
                "Acquisition Date",
                date.today(),
            )

            acquisition_cost = b.number_input(
                "Acquisition Cost (ETB)",
                min_value=0.0,
                step=100.0,
            )

            current_value = a.number_input(
                "Current Value (ETB)",
                min_value=0.0,
                step=100.0,
            )

            quantity = b.number_input(
                "Quantity",
                min_value=0.01,
                value=1.0,
                step=1.0,
            )

            condition = a.selectbox(
                "Condition",
                [
                    "Excellent",
                    "Good",
                    "Fair",
                    "Needs Repair",
                    "Unusable",
                ],
            )

            ownership = b.selectbox(
                "Ownership",
                [
                    "Community",
                    "Group",
                    "Joint",
                    "Other",
                ],
            )

            location = a.text_input(
                "Location"
            )

            responsible = b.text_input(
                "Responsible Person"
            )

            notes = st.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Register Property",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            group = groups[
                gl.index(selected_group)
            ]

            if not property_name.strip():

                st.error(
                    "Property name is required."
                )

            else:

                sql(
                    """
                    INSERT INTO properties
                    (
                        group_id,

                        property_type,
                        property_name,
                        description,

                        acquisition_date,

                        acquisition_cost,
                        current_value,
                        quantity,

                        condition_status,
                        ownership_status,

                        location,
                        responsible_person,

                        notes,
                        created_at
                    )
                    VALUES
                    (
                        ?,?,?,?,
                        ?,
                        ?,?,?,
                        ?,?,
                        ?,?,
                        ?,?
                    )
                    """,
                    (
                        group["id"],

                        property_type,
                        property_name,
                        description,

                        str(acquisition_date),

                        acquisition_cost,
                        current_value,
                        quantity,

                        condition,
                        ownership,

                        location,
                        responsible,

                        notes,
                        now(),
                    ),
                )

                audit(
                    "Registered community property",
                    MODULE,
                    property_name,
                )

                st.success(
                    "Property registered successfully."
                )

                st.rerun()


# ============================================================
# PROPERTY ANALYTICS
# ============================================================

def property_analytics():

    header(
        "Module 9: Property Analytics",
        "Analyze community asset values, condition and prototype depreciation.",
    )

    x = df(
        """
        SELECT
            property_type Type,

            SUM(quantity) Quantity,

            SUM(
                acquisition_cost * quantity
            ) Acquisition_Cost,

            SUM(
                current_value * quantity
            ) Current_Value

        FROM properties

        GROUP BY property_type

        ORDER BY Current_Value DESC
        """
    )

    if x.empty:

        st.info(
            "No properties have been registered."
        )

        return

    x["Value_Change"] = (
        x["Current_Value"]
        - x["Acquisition_Cost"]
    )

    x["Value_Change_Percent"] = np.where(
        x["Acquisition_Cost"] > 0,
        x["Value_Change"]
        / x["Acquisition_Cost"]
        * 100,
        0,
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(
        "Straight-Line Depreciation Demonstration"
    )

    properties = sql(
        """
        SELECT *
        FROM properties
        ORDER BY property_name
        """,
        fetch=True,
    )

    if properties:

        labels = [
            f"{p['id']} | {p['property_name']}"
            for p in properties
        ]

        selected = st.selectbox(
            "Select Property",
            labels,
        )

        p = properties[
            labels.index(selected)
        ]

        a, b = st.columns(2)

        salvage = a.number_input(
            "Estimated Salvage Value (ETB)",
            min_value=0.0,
            value=min(
                float(p["current_value"]),
                float(p["acquisition_cost"]),
            ),
            step=100.0,
        )

        life = b.number_input(
            "Useful Life (Years)",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
        )

        years = a.number_input(
            "Years Elapsed",
            min_value=0.0,
            max_value=float(life),
            value=1.0,
            step=1.0,
        )

        cost = float(
            p["acquisition_cost"]
        )

        annual = max(
            (cost - salvage) / life,
            0,
        )

        book = max(
            cost - annual * years,
            salvage,
        )

        a.metric(
            "Estimated Book Value",
            money(book),
        )

        b.metric(
            "Annual Depreciation",
            money(annual),
        )

    st.markdown(
        """
        <div class="section-card">
        <b>Prototype asset model.</b><br>
        Straight-line depreciation is included for analytical
        demonstration. Actual operational accounting should follow
        the applicable accounting policy and reporting requirements.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FUND SUSTAINABILITY
# ============================================================

def fund_sustainability_model():

    contributions = df(
        """
        SELECT
            contribution_date Date,
            SUM(amount) Contributions

        FROM contributions

        WHERE module='Iddir'
        AND status='Paid'

        GROUP BY contribution_date

        ORDER BY contribution_date
        """
    )

    benefits = df(
        """
        SELECT
            event_date Date,
            SUM(paid_amount) Benefits

        FROM benefits

        WHERE status IN ('Approved','Paid')

        GROUP BY event_date

        ORDER BY event_date
        """
    )

    if contributions.empty and benefits.empty:

        return pd.DataFrame()

    if not contributions.empty:

        contributions["Date"] = pd.to_datetime(
            contributions["Date"]
        )

    if not benefits.empty:

        benefits["Date"] = pd.to_datetime(
            benefits["Date"]
        )

    if contributions.empty:

        x = benefits.copy()
        x["Contributions"] = 0

    elif benefits.empty:

        x = contributions.copy()
        x["Benefits"] = 0

    else:

        x = contributions.merge(
            benefits,
            on="Date",
            how="outer",
        )

    x = x.fillna(0)

    x = x.sort_values(
        "Date"
    )

    x["Net_Fund_Change"] = (
        x["Contributions"]
        - x["Benefits"]
    )

    x["Cumulative_Fund"] = (
        x["Net_Fund_Change"].cumsum()
    )

    return x


def fund_page():

    header(
        "Module 10: Fund Sustainability",
        "Monitor contributions, mutual-support expenditure and cumulative fund position.",
    )

    x = fund_sustainability_model()

    if x.empty:

        st.info(
            "Record contributions and benefits to generate fund analytics."
        )

        return

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    a, b, c = st.columns(3)

    a.metric(
        "Total Contributions",
        money(
            x["Contributions"].sum()
        ),
    )

    b.metric(
        "Total Benefits",
        money(
            x["Benefits"].sum()
        ),
    )

    c.metric(
        "Net Fund Change",
        money(
            x["Net_Fund_Change"].sum()
        ),
    )

    st.subheader(
        "Cumulative Fund"
    )

    st.line_chart(
        x.set_index("Date")[
            ["Cumulative_Fund"]
        ]
    )

    st.markdown(
        """
        <div class="section-card">
        <b>Fund-balance model</b>

        <br><br>

        F(t+1) = F(t) + C(t) + O(t) − B(t) − A(t)

        <br><br>

        where F is the fund balance, C is contribution income,
        O is other income, B is benefit expenditure and A is
        administrative expenditure.

        The current prototype directly records contributions and
        benefits. Other income and expenditure streams can be
        expanded in future IDFS versions.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# STATISTICAL MODELS
# ============================================================

def benefit_eligibility_score():

    ms = get_members()

    if not ms:

        return pd.DataFrame()

    rows = []

    for m in ms:

        history = df(
            """
            SELECT
                amount,
                contribution_date,
                status

            FROM contributions

            WHERE member_id=?
            AND module='Iddir'

            ORDER BY contribution_date
            """,
            (m["id"],),
        )

        if history.empty:

            total_paid = 0
            consistency = 0

        else:

            total_paid = float(
                history["amount"].sum()
            )

            consistency = (
                history["status"]
                .eq("Paid")
                .mean()
            )

        join_date = pd.to_datetime(
            m["join_date"],
            errors="coerce",
        )

        if pd.isna(join_date):

            membership_years = 0

        else:

            membership_years = max(
                0,
                (
                    pd.Timestamp.today()
                    - join_date
                ).days / 365.25,
            )

        rows.append(
            {
                "Member_ID": m["id"],
                "Member_No": m["member_no"],
                "Member": m["full_name"],

                "Planned_Contribution":
                    float(
                        m["regular_contribution"]
                        or 0
                    ),

                "Total_Paid":
                    total_paid,

                "Payment_Consistency":
                    consistency,

                "Trust_Score":
                    float(
                        m["trust_score"]
                        or 0
                    ),

                "Membership_Years":
                    membership_years,
            }
        )

    x = pd.DataFrame(rows)

    def normalize(series):

        maximum = float(
            series.max()
        )

        if maximum > 0:

            return series / maximum

        return series * 0

    x[
        "Contribution_Component"
    ] = normalize(
        x["Total_Paid"]
    )

    x[
        "Consistency_Component"
    ] = x["Payment_Consistency"]

    x[
        "Trust_Component"
    ] = x["Trust_Score"]

    x[
        "Membership_Component"
    ] = normalize(
        x["Membership_Years"]
    )

    w1 = 0.35
    w2 = 0.30
    w3 = 0.20
    w4 = 0.15

    x["Eligibility_Score"] = (
        w1 * x["Contribution_Component"]
        + w2 * x["Consistency_Component"]
        + w3 * x["Trust_Component"]
        + w4 * x["Membership_Component"]
    )

    return (
        x.sort_values(
            "Eligibility_Score",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def statistical_model_page():

    header(
        "Module 11: Statistical Models",
        "Transparent analytical indicators for Iddir planning, monitoring and research.",
    )

    st.markdown(
        """
        <div class="section-card">
        <div class="module-label">
        Analytical Prototype
        </div>

        These models are analytical demonstrations.
        They should not be interpreted as automatic legal,
        humanitarian or eligibility decisions.

        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Benefit Eligibility",
            "Fund Sustainability",
            "Contribution Risk",
        ]
    )

    with tab1:

        st.markdown(
            """
            ### Weighted member-support indicator

            A transparent prototype index can be represented as:

            **Eᵢ = w₁Cᵢ + w₂Pᵢ + w₃Tᵢ + w₄Mᵢ**

            where C is contribution level, P is payment
            consistency, T is trust score and M is membership duration.
            """
        )

        x = benefit_eligibility_score()

        if x.empty:

            st.info(
                "Register members and contributions first."
            )

        else:

            display = x.copy()

            for col in [
                "Contribution_Component",
                "Consistency_Component",
                "Trust_Component",
                "Membership_Component",
                "Eligibility_Score",
            ]:

                display[col] = display[
                    col
                ].map(
                    lambda z:
                    f"{z:.2%}"
                )

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
            )

            download(
                display,
                "iddir_eligibility_scores.csv",
            )

    with tab2:

        st.markdown(
            """
            ### Community fund sustainability

            **Fₜ₊₁ = Fₜ + Cₜ + Oₜ − Bₜ − Aₜ**

            The model provides a simple framework for monitoring
            whether contribution resources are keeping pace with
            community support obligations.
            """
        )

        x = fund_sustainability_model()

        if x.empty:

            st.info(
                "Insufficient records."
            )

        else:

            st.dataframe(
                x,
                use_container_width=True,
                hide_index=True,
            )

            st.line_chart(
                x.set_index("Date")[
                    [
                        "Contributions",
                        "Benefits",
                        "Cumulative_Fund",
                    ]
                ]
            )

    with tab3:

        st.markdown(
            """
            ### Contribution-risk indicator

            **Rᵢ = 1 − Pᵢ**

            where Pᵢ is the observed payment-consistency rate.

            This is an administrative follow-up indicator,
            not a judgement about a member.
            """
        )

        ms = get_members()

        if ms:

            rows = []

            for m in ms:

                h = df(
                    """
                    SELECT status
                    FROM contributions
                    WHERE member_id=?
                    AND module='Iddir'
                    """,
                    (m["id"],),
                )

                if h.empty:

                    consistency = 0

                else:

                    consistency = (
                        h["status"]
                        .eq("Paid")
                        .mean()
                    )

                rows.append(
                    {
                        "Member_No":
                            m["member_no"],

                        "Member":
                            m["full_name"],

                        "Payment_Consistency":
                            consistency,

                        "Contribution_Risk":
                            1 - consistency,
                    }
                )

            x = pd.DataFrame(rows)

            x["Payment_Consistency"] = x[
                "Payment_Consistency"
            ].map(
                lambda z:
                f"{z:.2%}"
            )

            x["Contribution_Risk"] = x[
                "Contribution_Risk"
            ].map(
                lambda z:
                f"{z:.2%}"
            )

            st.dataframe(
                x,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# FINANCIAL TRANSACTIONS
# ============================================================

def transactions():

    header(
        "Module 12: Financial Transactions",
        "Record and reconcile Iddir financial transactions.",
    )

    branches_list = get_branch_options()
    groups = get_groups()
    ms = get_members()

    branch_options = [
        branch_label(b)
        for b in branches_list
    ]

    group_options = [
        group_label(g)
        for g in groups
    ]

    member_options = [
        member_label(m)
        for m in ms
    ]

    with st.form("transaction_form"):

        a, b = st.columns(2)

        branch_label_selected = a.selectbox(
            "Branch",
            branch_options or ["No branch"],
        )

        group_label_selected = b.selectbox(
            "Iddir Group",
            group_options or ["No group"],
        )

        member_label_selected = a.selectbox(
            "Member",
            member_options or ["No member"],
        )

        transaction_type = b.selectbox(
            "Transaction Type",
            [
                "Contribution",
                "Benefit Payment",
                "Property Purchase",
                "Property Sale",
                "Donation",
                "Administrative Expense",
                "Emergency Fund",
                "Adjustment",
                "Other",
            ],
        )

        amount = a.number_input(
            "Amount (ETB)",
            min_value=0.0,
            step=100.0,
        )

        reference = b.text_input(
            "Reference"
        )

        transaction_date = a.date_input(
            "Transaction Date",
            date.today(),
        )

        description = st.text_area(
            "Description"
        )

        submitted = st.form_submit_button(
            "Record Transaction",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        branch_id = None
        group_id = None
        member_id = None

        if branch_label_selected != "No branch":

            branch_id = branches_list[
                branch_options.index(
                    branch_label_selected
                )
            ]["id"]

        if group_label_selected != "No group":

            group_id = groups[
                group_options.index(
                    group_label_selected
                )
            ]["id"]

        if member_label_selected != "No member":

            member_id = ms[
                member_options.index(
                    member_label_selected
                )
            ]["id"]

        sql(
            """
            INSERT INTO transactions
            (
                module,
                branch_id,
                group_id,
                member_id,

                transaction_type,
                amount,

                reference,
                transaction_date,
                description,

                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                MODULE,
                branch_id,
                group_id,
                member_id,

                transaction_type,
                amount,

                reference,
                str(transaction_date),
                description,

                now(),
            ),
        )

        audit(
            "Recorded financial transaction",
            MODULE,
            f"{transaction_type}: {amount}",
        )

        st.success(
            "Transaction recorded."
        )

        st.rerun()

    x = df(
        """
        SELECT

            t.transaction_date Date,

            b.code Branch,

            g.group_code Group_Code,

            m.member_no Member_No,

            t.transaction_type Type,

            t.amount Amount,

            t.reference Reference,

            t.description Description

        FROM transactions t

        LEFT JOIN branches b
            ON t.branch_id=b.id

        LEFT JOIN iddir_groups g
            ON t.group_id=g.id

        LEFT JOIN members m
            ON t.member_id=m.id

        WHERE t.module='Iddir'

        ORDER BY t.id DESC
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    download(
        x,
        "iddir_transactions.csv",
    )


# ============================================================
# REPORTS
# ============================================================

def reports():

    header(
        "Module 13: Reports and Analytics",
        "Management information and downloadable Iddir reports.",
    )

    report = st.selectbox(
        "Select Report",
        [
            "Module Summary",
            "Members",
            "Iddir Groups",
            "Contributions",
            "Contribution Outstanding",
            "Benefits",
            "Community Events",
            "Properties",
            "Transactions",
            "Statistical Eligibility",
        ],
    )

    queries = {

        "Module Summary":
        """
        SELECT
            'Iddir' Module,

            COUNT(*) Members,

            ROUND(
                AVG(regular_contribution),
                2
            ) Average_Regular_Contribution,

            ROUND(
                AVG(trust_score),
                3
            ) Average_Trust

        FROM members

        WHERE module='Iddir'
        AND status='Active'
        """,

        "Members":
        """
        SELECT
            m.member_no Member_No,
            m.full_name Full_Name,
            m.household_no Household_No,
            b.code Branch,

            m.registration_contribution
                Registration_Contribution,

            m.regular_contribution
                Regular_Contribution,

            m.contribution_frequency Frequency,

            m.trust_score Trust_Score,
            m.status Status

        FROM members m

        LEFT JOIN branches b
            ON m.branch_id=b.id

        WHERE m.module='Iddir'

        ORDER BY m.full_name
        """,

        "Iddir Groups":
        """
        SELECT
            group_code Group_Code,
            group_name Group_Name,

            registration_contribution
                Registration_Contribution,

            contribution_amount
                Regular_Contribution,

            contribution_frequency Frequency,

            member_capacity Capacity,

            emergency_fund Emergency_Fund,
            property_value Property_Value,

            status Status

        FROM iddir_groups

        ORDER BY group_name
        """,

        "Contributions":
        """
        SELECT
            c.contribution_date Date,
            c.contribution_period Period,
            c.contribution_type Type,

            g.group_code Group_Code,

            m.member_no Member_No,
            m.full_name Member,

            c.amount_due Amount_Due,
            c.amount Amount_Paid,

            CASE
                WHEN c.amount_due > c.amount
                THEN c.amount_due-c.amount
                ELSE 0
            END Outstanding,

            c.status Status,
            c.reference Reference

        FROM contributions c

        JOIN members m
            ON c.member_id=m.id

        LEFT JOIN iddir_groups g
            ON c.group_id=g.id

        WHERE c.module='Iddir'

        ORDER BY c.id DESC
        """,

        "Contribution Outstanding":
        """
        SELECT
            m.member_no Member_No,
            m.full_name Member,

            SUM(c.amount_due) Total_Due,
            SUM(c.amount) Total_Paid,

            CASE
                WHEN SUM(c.amount_due)
                     > SUM(c.amount)
                THEN
                    SUM(c.amount_due)
                    - SUM(c.amount)
                ELSE 0
            END Outstanding

        FROM contributions c

        JOIN members m
            ON c.member_id=m.id

        WHERE c.module='Iddir'

        GROUP BY
            m.id,
            m.member_no,
            m.full_name

        ORDER BY Outstanding DESC
        """,

        "Benefits":
        """
        SELECT
            b.event_date Event_Date,

            g.group_code Group_Code,

            m.member_no Member_No,
            m.full_name Beneficiary,

            b.benefit_type Benefit_Type,

            b.requested_amount Requested,
            b.approved_amount Approved,
            b.paid_amount Paid,

            b.status Status

        FROM benefits b

        JOIN members m
            ON b.member_id=m.id

        LEFT JOIN iddir_groups g
            ON b.group_id=g.id

        ORDER BY b.id DESC
        """,

        "Community Events":
        """
        SELECT
            e.event_date Date,

            g.group_code Group_Code,

            e.event_type Event_Type,
            e.household_count Participants,

            e.estimated_cost Estimated_Cost,
            e.actual_cost Actual_Cost,

            e.status Status

        FROM events e

        LEFT JOIN iddir_groups g
            ON e.group_id=g.id

        ORDER BY e.id DESC
        """,

        "Properties":
        """
        SELECT
            p.property_name Property,
            p.property_type Type,

            g.group_code Group_Code,

            p.acquisition_cost Acquisition_Cost,
            p.current_value Current_Value,
            p.quantity Quantity,

            p.condition_status Condition,
            p.ownership_status Ownership

        FROM properties p

        LEFT JOIN iddir_groups g
            ON p.group_id=g.id

        ORDER BY p.property_name
        """,

        "Transactions":
        """
        SELECT
            transaction_date Date,
            transaction_type Type,
            amount Amount,
            reference Reference,
            description Description

        FROM transactions

        WHERE module='Iddir'

        ORDER BY id DESC
        """,
    }

    if report == "Statistical Eligibility":

        x = benefit_eligibility_score()

    else:

        x = df(
            queries[report]
        )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    download(
        x,
        "iddir_report.csv",
    )


# ============================================================
# MANUALS
# ============================================================

def manuals():

    header(
        "Module 14: Manuals",
        "Operational guidance for the IDFS Iddir management prototype.",
    )

    manuals_data = [

        (
            "Iddir Operating Manual",
            """
            Register branches, establish Iddir groups, register
            members, define contribution obligations, record
            payments, manage mutual-support requests, administer
            community events, maintain community property and
            reconcile financial transactions.
            """,
        ),

        (
            "Member and Contribution Management",
            """
            Each member can have a registration contribution,
            regular contribution amount and contribution frequency.
            Actual payment records are maintained separately so
            obligations, payments and outstanding balances can
            be analyzed.
            """,
        ),

        (
            "Community Support Management",
            """
            Support requests should document the event, beneficiary,
            requested amount, approval status, approved amount,
            paid amount and transaction reference.
            """,
        ),

        (
            "Property Management",
            """
            Community property can be registered with acquisition
            cost, current value, quantity, condition, ownership,
            location and responsible person.
            """,
        ),

        (
            "Statistical Management",
            """
            Contribution consistency, trust indicators,
            membership duration and other variables can be
            transformed into measurable indicators for research,
            monitoring and planning.
            """,
        ),

        (
            "Audit and Financial Controls",
            """
            Important administrative activities should be recorded
            in the audit trail. Financial transactions should use
            references and should be reconciled with contribution,
            benefit and property records.
            """,
        ),
    ]

    for title, text in manuals_data:

        st.markdown(
            f"""
            <div class="manual-card">

                <h3>{title}</h3>

                <p>{text}</p>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# AUDIT
# ============================================================

def audit_page():

    header(
        "Module 15: Audit Trail",
        "Traceable record of important IDFS Iddir activities.",
    )

    x = df(
        """
        SELECT
            timestamp Timestamp,
            username Username,
            module Module,
            action Action,
            details Details

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
        "iddir_audit.csv",
    )


# ============================================================
# USER ADMINISTRATION
# ============================================================

def users_page():

    header(
        "Module 16: User Administration",
        "Manage role-based access to the Iddir management prototype.",
    )

    x = df(
        """
        SELECT

            username Username,
            full_name Full_Name,
            role Role,
            module Module,
            active Active,
            created_at Created_At

        FROM users

        ORDER BY username
        """
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
    )

    branches_list = get_branch_options()

    options = [
        branch_label(b)
        for b in branches_list
    ]

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
            [
                "Portal",
                "Iddir",
            ],
        )

        branch = b.selectbox(
            "Branch",
            ["No branch"] + options,
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

            return

        if not full_name.strip():

            st.error(
                "Full name is required."
            )

            return

        if not password:

            st.error(
                "Password is required."
            )

            return

        branch_id = None

        if branch != "No branch":

            branch_id = branches_list[
                options.index(branch)
            ]["id"]

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                username,
            )

            st.success(
                "User created successfully."
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

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.markdown(
            "## IDFS"
        )

        st.caption(
            "Indigenous Digital Financial System"
        )

        st.markdown(
            "**IDDIR MODULE**"
        )

        st.divider()

        st.write(
            f"User: **{st.session_state.get('full_name', '')}**"
        )

        st.write(
            f"Role: **{st.session_state.get('role', '')}**"
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

            "Iddir Groups",

            "Contributions",

            "Benefits and Mutual Support",

            "Community Events",

            "Property Management",

            "Property Analytics",

            "Fund Sustainability",

            "Statistical Models",

            "Financial Transactions",

            "Reports and Analytics",

            "Manuals",

            "Audit Trail",
        ]

        if st.session_state.get(
            "role"
        ) == "Administrator":

            navigation.append(
                "User Administration"
            )

        page = st.radio(
            "Navigation",
            navigation,
        )

    # ========================================================
    # PAGE ROUTER
    # ========================================================

    pages = {

        "Dashboard":
            dashboard,

        "Branch Management":
            branch_page,

        "Member Management":
            member_page,

        "Iddir Groups":
            group_page,

        "Contributions":
            contribution_page,

        "Benefits and Mutual Support":
            benefits_page,

        "Community Events":
            events_page,

        "Property Management":
            property_page,

        "Property Analytics":
            property_analytics,

        "Fund Sustainability":
            fund_page,

        "Statistical Models":
            statistical_model_page,

        "Financial Transactions":
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
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
