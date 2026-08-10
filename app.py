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
# Single-file Streamlit demonstration prototype
#
# Modules:
# 1. Dashboard
# 2. Authentication and access control
# 3. Branch management
# 4. Member management
# 5. IDFS Equb savings and rounds
# 6. Contribution-weighted probability engine
# 7. IDFS Iddir community risk sharing
# 8. Iddir property management
# 9. Transactions
# 10. Reports and analytics
# 11. Audit trail
# 12. User administration
# ============================================================


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IDFS Web Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Indigenous Digital Financial System"
APP_SHORT = "IDFS Web Platform"

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
# COMMON HELPERS
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(x):
    try:
        return f"ETB {float(x or 0):,.2f}"
    except (TypeError, ValueError):
        return "ETB 0.00"


def conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def sql(q, p=(), fetch=False, many=False):
    c = conn()
    cur = c.cursor()

    try:
        if many:
            cur.executemany(q, p)
        else:
            cur.execute(q, p)

        result = cur.fetchall() if fetch else None
        c.commit()
        return result

    except sqlite3.Error:
        c.rollback()
        raise

    finally:
        c.close()


def df(q, p=()):
    rows = sql(q, p, fetch=True)
    return pd.DataFrame([dict(row) for row in rows])


def safe_rerun():
    st.rerun()


# ============================================================
# PASSWORD SECURITY
# ============================================================

def pwd_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()

    return salt + "$" + hashed


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


# ============================================================
# AUDIT
# ============================================================

def audit(action, module="Portal", details=""):
    try:
        sql(
            """
            INSERT INTO audit_log
            (username, module, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                st.session_state.get("username", "anonymous"),
                module,
                action,
                details,
                now(),
            ),
        )
    except sqlite3.Error:
        # Avoid preventing normal application operation if
        # audit recording itself encounters an unexpected issue.
        pass


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Create all database tables if they do not exist.

    This function is intentionally idempotent:
    Streamlit reruns it frequently, so initialization must not
    attempt to create duplicate records.
    """

    c = conn()

    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
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

        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            module TEXT NOT NULL,
            location TEXT,
            manager TEXT,
            phone TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_no TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            sex TEXT,
            join_date TEXT,
            module TEXT,
            branch_id INTEGER,
            regular_contribution REAL DEFAULT 0,
            trust_score REAL DEFAULT 0.5,
            status TEXT DEFAULT 'Active',
            address TEXT,
            notes TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS equb_rounds (
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
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS contributions (
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
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS iddir_events (
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
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER,
            property_code TEXT UNIQUE NOT NULL,
            property_type TEXT,
            description TEXT,
            location TEXT,
            acquisition_date TEXT,
            acquisition_cost REAL DEFAULT 0,
            current_value REAL DEFAULT 0,
            status TEXT DEFAULT 'Active',
            custodian TEXT,
            notes TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT,
            branch_id INTEGER,
            member_id INTEGER,
            transaction_type TEXT,
            amount REAL,
            reference TEXT,
            transaction_date TEXT,
            description TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
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

    # --------------------------------------------------------
    # DEFAULT ADMIN
    #
    # INSERT OR IGNORE prevents the old IntegrityError caused
    # by repeatedly inserting username='admin'.
    # --------------------------------------------------------

    sql(
        """
        INSERT OR IGNORE INTO users
        (username, password_hash, full_name, role, module, created_at)
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

    # --------------------------------------------------------
    # DEFAULT BRANCHES
    # --------------------------------------------------------

    default_branches = [
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

    for code, name, module, location, manager in default_branches:
        sql(
            """
            INSERT OR IGNORE INTO branches
            (code, name, module, location, manager, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                code,
                name,
                module,
                location,
                manager,
                now(),
            ),
        )


# ============================================================
# UI HELPERS
# ============================================================

def header(title, subtitle=""):
    st.title(title)

    if subtitle:
        st.caption(subtitle)


def section_title(title, subtitle=None):
    st.subheader(title)

    if subtitle:
        st.caption(subtitle)


def metric_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def download_dataframe(data, filename):
    if data is None or data.empty:
        st.info("No records available for download.")
        return

    st.download_button(
        label="Download CSV",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=False,
    )


# ============================================================
# DATA ACCESS
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
        ORDER BY module, name
        """,
        fetch=True,
    )


def members(module=None, branch=None):
    conditions = []
    params = []

    if module:
        conditions.append("m.module=?")
        params.append(module)

    if branch:
        conditions.append("m.branch_id=?")
        params.append(branch)

    where = ""

    if conditions:
        where = " WHERE " + " AND ".join(conditions)

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
        + where
        + """
        ORDER BY m.full_name
        """,
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
            padding: 1.5rem;
            border-radius: 15px;
            background: linear-gradient(135deg,#0B5CAD,#138A36);
            color:white;
            margin-bottom:1.5rem;
        ">
            <h1 style="margin-bottom:0.2rem;">
                Indigenous Digital Financial System
            </h1>
            <p style="margin:0;">
                IDFS Web Platform — Equb and Iddir
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.subheader("System Login")

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
            username = username.strip()

            user_rows = sql(
                """
                SELECT *
                FROM users
                WHERE username=?
                  AND active=1
                """,
                (username,),
                fetch=True,
            )

            if user_rows and check_pwd(
                password,
                user_rows[0]["password_hash"],
            ):
                user = user_rows[0]

                st.session_state["authenticated"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["username"] = user["username"]
                st.session_state["full_name"] = user["full_name"]
                st.session_state["role"] = user["role"]
                st.session_state["module"] = user["module"]
                st.session_state["branch_id"] = user["branch_id"]

                audit(
                    "Successful login",
                    "Portal",
                    username,
                )

                st.rerun()

            else:
                st.error("Invalid username or password.")

        st.info(
            "Demonstration account: admin / admin123"
        )


# ============================================================
# MODULE 3: BRANCH MANAGEMENT
# ============================================================

def branch_page():
    header(
        "Branch Management",
        "Bank-style branch structure for Equb and Iddir",
    )

    tab_directory, tab_register = st.tabs(
        [
            "Branch Directory",
            "Register Branch",
        ]
    )

    with tab_directory:
        data = df(
            """
            SELECT
                code AS Branch_Code,
                name AS Branch_Name,
                module AS Module,
                location AS Location,
                manager AS Manager,
                phone AS Phone,
                status AS Status,
                created_at AS Created_At
            FROM branches
            ORDER BY module, name
            """
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

        download_dataframe(
            data,
            "idfs_branches.csv",
        )

    with tab_register:
        with st.form("branch_form"):
            col1, col2 = st.columns(2)

            code = col1.text_input(
                "Branch Code",
                placeholder="EQB-003",
            )

            name = col2.text_input(
                "Branch Name",
            )

            module = col1.selectbox(
                "Module",
                MODULES,
            )

            location = col2.text_input(
                "Location",
            )

            manager = col1.text_input(
                "Manager",
            )

            phone = col2.text_input(
                "Phone",
            )

            status = col1.selectbox(
                "Status",
                ["Active", "Inactive"],
            )

            submitted = st.form_submit_button(
                "Register Branch",
                type="primary",
            )

        if submitted:
            code = code.strip()
            name = name.strip()

            if not code or not name:
                st.error(
                    "Branch code and branch name are required."
                )
                return

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
                        code,
                        name,
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
# MODULE 4: MEMBER MANAGEMENT
# ============================================================

def member_page():
    header(
        "Member Management",
        "Registration, regular contribution and membership monitoring",
    )

    tab_directory, tab_register, tab_profile = st.tabs(
        [
            "Directory",
            "Register Member",
            "Member Profile",
        ]
    )

    # --------------------------------------------------------
    # DIRECTORY
    # --------------------------------------------------------

    with tab_directory:
        module_filter = st.selectbox(
            "Module Filter",
            ["All"] + MODULES,
        )

        if module_filter == "All":
            data = df(
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
                ORDER BY m.module, m.full_name
                """
            )

        else:
            data = df(
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
                (module_filter,),
            )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

        download_dataframe(
            data,
            "idfs_members.csv",
        )

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    with tab_register:
        with st.form("member_form"):
            col1, col2 = st.columns(2)

            member_no = col1.text_input(
                "Member Number",
                placeholder="EQB-M-001",
            )

            full_name = col2.text_input(
                "Full Name",
            )

            phone = col1.text_input(
                "Phone",
            )

            sex = col2.selectbox(
                "Sex",
                [
                    "Not specified",
                    "Female",
                    "Male",
                ],
            )

            module = col1.selectbox(
                "Module",
                MODULES,
            )

            module_branches = branches(module)

            branch_options = [
                f"{b['code']} | {b['name']}"
                for b in module_branches
            ]

            branch_choice = col2.selectbox(
                "Branch",
                branch_options
                if branch_options
                else ["No branch available"],
            )

            contribution = col1.number_input(
                "Regular Contribution per Round/Period (ETB)",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

            join_date = col2.date_input(
                "Join Date",
                value=date.today(),
            )

            trust_score = col1.number_input(
                "Initial Trust Score",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
            )

            status = col2.selectbox(
                "Membership Status",
                ["Active", "Inactive", "Suspended"],
            )

            address = col1.text_input(
                "Address",
            )

            notes = st.text_area(
                "Notes",
            )

            submitted = st.form_submit_button(
                "Register Member",
                type="primary",
            )

        if submitted:
            member_no = member_no.strip()
            full_name = full_name.strip()

            if not member_no or not full_name:
                st.error(
                    "Member number and full name are required."
                )
                return

            if not module_branches:
                st.error(
                    "Create a branch for this module first."
                )
                return

            branch_index = branch_options.index(
                branch_choice
            )

            branch_id = module_branches[
                branch_index
            ]["id"]

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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        member_no,
                        full_name,
                        phone.strip(),
                        sex,
                        str(join_date),
                        module,
                        branch_id,
                        contribution,
                        trust_score,
                        status,
                        address.strip(),
                        notes.strip(),
                        now(),
                    ),
                )

                audit(
                    "Registered member",
                    module,
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

    with tab_profile:
        all_members = members()

        if not all_members:
            st.info(
                "No members have been registered yet."
            )
            return

        options = [
            f"{m['member_no']} | "
            f"{m['full_name']} | "
            f"{m['module']}"
            for m in all_members
        ]

        selected = st.selectbox(
            "Select Member",
            options,
        )

        member = all_members[
            options.index(selected)
        ]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Member",
            member["member_no"],
        )

        col2.metric(
            "Module",
            member["module"],
        )

        col3.metric(
            "Regular Contribution",
            money(member["regular_contribution"]),
        )

        col4.metric(
            "Trust Score",
            f"{float(member['trust_score']):.2f}",
        )

        profile = pd.DataFrame(
            [
                {
                    "Field": "Full Name",
                    "Value": member["full_name"],
                },
                {
                    "Field": "Phone",
                    "Value": member["phone"],
                },
                {
                    "Field": "Sex",
                    "Value": member["sex"],
                },
                {
                    "Field": "Branch",
                    "Value": member["branch_name"],
                },
                {
                    "Field": "Join Date",
                    "Value": member["join_date"],
                },
                {
                    "Field": "Status",
                    "Value": member["status"],
                },
                {
                    "Field": "Address",
                    "Value": member["address"],
                },
                {
                    "Field": "Notes",
                    "Value": member["notes"],
                },
            ]
        )

        st.dataframe(
            profile,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# MODULE 5: IDFS EQUB
# ============================================================

def equb():
    header(
        "IDFS Equb",
        "Community savings, fixed contributions, rounds and rotating payout",
    )

    tabs = st.tabs(
        [
            "Overview",
            "Round Management",
            "Contribution Management",
            "Probability Engine",
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

    savings = sql(
        """
        SELECT COALESCE(SUM(amount), 0) AS n
        FROM contributions
        WHERE module='Equb'
          AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    rounds_count = sql(
        """
        SELECT COUNT(*) AS n
        FROM equb_rounds
        """,
        fetch=True,
    )[0]["n"]

    open_rounds = sql(
        """
        SELECT COUNT(*) AS n
        FROM equb_rounds
        WHERE status='Open'
        """,
        fetch=True,
    )[0]["n"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Active Members",
        active_members,
    )

    col2.metric(
        "Paid Contributions",
        money(savings),
    )

    col3.metric(
        "Rounds",
        rounds_count,
    )

    col4.metric(
        "Open Rounds",
        open_rounds,
    )

    st.info(
        """
        Equb savings model: each member has a regular
        contribution amount. Contributions are recorded by
        date, round and payment reference. The probability
        engine is a mathematical demonstration and can be
        replaced by a governance-approved fixed rotation.
        """
    )

    data = df(
        """
        SELECT
            r.round_no AS Round_No,
            b.code AS Branch,
            r.contribution_amount AS Contribution,
            r.expected_members AS Members,
            r.total_pool AS Total_Pool,
            r.start_date AS Start_Date,
            r.draw_date AS Draw_Date,
            r.status AS Status,
            COALESCE(m.full_name, '') AS Winner
        FROM equb_rounds r
        LEFT JOIN branches b
            ON r.branch_id=b.id
        LEFT JOIN members m
            ON r.winner_member_id=m.id
        ORDER BY r.id DESC
        """
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# EQUb ROUND MANAGEMENT
# ============================================================

def equb_rounds():
    section_title(
        "Round Management",
        "Create a fixed-contribution Equb round.",
    )

    equb_branches = branches("Equb")

    if not equb_branches:
        st.warning(
            "Create an Equb branch first."
        )
        return

    branch_options = [
        f"{b['code']} | {b['name']}"
        for b in equb_branches
    ]

    with st.form("equb_round_form"):
        col1, col2 = st.columns(2)

        branch_choice = col1.selectbox(
            "Equb Branch",
            branch_options,
        )

        round_no = col2.number_input(
            "Round Number",
            min_value=1,
            max_value=100000,
            value=1,
            step=1,
        )

        amount = col1.number_input(
            "Fixed Round Contribution (ETB)",
            min_value=1.0,
            value=1000.0,
            step=100.0,
        )

        start_date = col2.date_input(
            "Start Date",
            value=date.today(),
        )

        draw_date = col1.date_input(
            "Payout / Draw Date",
            value=date.today(),
        )

        status = col2.selectbox(
            "Status",
            [
                "Open",
                "Completed",
                "Cancelled",
            ],
        )

        submitted = st.form_submit_button(
            "Create Equb Round",
            type="primary",
        )

    if submitted:
        branch = equb_branches[
            branch_options.index(branch_choice)
        ]

        member_count = sql(
            """
            SELECT COUNT(*) AS n
            FROM members
            WHERE module='Equb'
              AND branch_id=?
              AND status='Active'
            """,
            (branch["id"],),
            fetch=True,
        )[0]["n"]

        pool = member_count * amount

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    branch["id"],
                    int(round_no),
                    amount,
                    str(start_date),
                    str(draw_date),
                    member_count,
                    pool,
                    status,
                    now(),
                ),
            )

            audit(
                "Created Equb round",
                "Equb",
                f"Round {round_no}",
            )

            st.success(
                "Equb round created successfully."
            )

            st.rerun()

        except sqlite3.IntegrityError as exc:
            st.error(
                f"Could not create round: {exc}"
            )


# ============================================================
# EQUb POOL UPDATE
# ============================================================

def update_pool(round_id):
    total = sql(
        """
        SELECT COALESCE(SUM(amount), 0) AS n
        FROM contributions
        WHERE round_id=?
          AND status='Paid'
        """,
        (round_id,),
        fetch=True,
    )[0]["n"]

    sql(
        """
        UPDATE equb_rounds
        SET total_pool=?
        WHERE id=?
        """,
        (total, round_id),
    )


# ============================================================
# EQUb CONTRIBUTIONS
# ============================================================

def equb_contributions():
    section_title(
        "Contribution Management",
        "Record individual Equb contributions against rounds.",
    )

    equb_members = members("Equb")

    if not equb_members:
        st.info(
            "Register Equb members first."
        )
        return

    rounds = sql(
        """
        SELECT
            r.id,
            r.round_no,
            b.code
        FROM equb_rounds r
        JOIN branches b
            ON r.branch_id=b.id
        WHERE r.status <> 'Cancelled'
        ORDER BY r.id DESC
        """,
        fetch=True,
    )

    member_options = [
        f"{m['member_no']} | {m['full_name']}"
        for m in equb_members
    ]

    round_options = [
        f"{r['id']} | Round {r['round_no']} | {r['code']}"
        for r in rounds
    ]

    with st.form("equb_contribution_form"):
        member_choice = st.selectbox(
            "Member",
            member_options,
        )

        round_choice = st.selectbox(
            "Equb Round",
            round_options
            if round_options
            else ["No round available"],
        )

        amount = st.number_input(
            "Contribution Amount (ETB)",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

        contribution_date = st.date_input(
            "Contribution Date",
            value=date.today(),
        )

        status = st.selectbox(
            "Payment Status",
            [
                "Pending",
                "Paid",
                "Cancelled",
            ],
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

        reference = st.text_input(
            "Payment Reference",
        )

        notes = st.text_area(
            "Notes",
        )

        submitted = st.form_submit_button(
            "Record Contribution",
            type="primary",
        )

    if submitted:
        if amount <= 0:
            st.error(
                "Contribution amount must be greater than zero."
            )
            return

        member = equb_members[
            member_options.index(member_choice)
        ]

        round_id = None

        if rounds and round_choice != "No round available":
            round_id = int(
                round_choice.split("|")[0].strip()
            )

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                member["id"],
                "Equb",
                round_id,
                amount,
                str(contribution_date),
                status,
                reference.strip(),
                method,
                notes.strip(),
                now(),
            ),
        )

        # Keep member regular contribution synchronized
        # with the latest paid contribution.
        if status == "Paid":
            sql(
                """
                UPDATE members
                SET regular_contribution=?
                WHERE id=?
                """,
                (
                    amount,
                    member["id"],
                ),
            )

        if round_id:
            update_pool(round_id)

        audit(
            "Recorded Equb contribution",
            "Equb",
            f"{member['member_no']} {money(amount)}",
        )

        st.success(
            "Contribution recorded successfully."
        )

        st.rerun()

    data = df(
        """
        SELECT
            c.contribution_date AS Date,
            m.member_no AS Member_No,
            m.full_name AS Member,
            c.amount AS Amount,
            c.status AS Status,
            c.payment_method AS Payment_Method,
            c.reference AS Reference,
            c.notes AS Notes
        FROM contributions c
        JOIN members m
            ON c.member_id=m.id
        WHERE c.module='Equb'
        ORDER BY c.id DESC
        LIMIT 500
        """
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MODULE 6: CONTRIBUTION-WEIGHTED PROBABILITY ENGINE
# ============================================================

def probability_table():
    equb_members = members("Equb")

    rows = []

    for member in equb_members:
        historical_paid = sql(
            """
            SELECT COALESCE(SUM(amount), 0) AS n
            FROM contributions
            WHERE member_id=?
              AND module='Equb'
              AND status='Paid'
            """,
            (member["id"],),
            fetch=True,
        )[0]["n"]

        regular = float(
            member["regular_contribution"] or 0
        )

        trust = float(
            member["trust_score"] or 0
        )

        rows.append(
            {
                "Member_No": member["member_no"],
                "Member": member["full_name"],
                "Branch": member["branch_name"],
                "Regular_Contribution": regular,
                "Historical_Paid": float(
                    historical_paid or 0
                ),
                "Trust_Score": trust,
            }
        )

    data = pd.DataFrame(rows)

    if data.empty:
        return data

    total_contribution = data[
        "Regular_Contribution"
    ].sum()

    if total_contribution > 0:
        data["Contribution_Weight"] = (
            data["Regular_Contribution"]
            / total_contribution
        )
    else:
        data["Contribution_Weight"] = (
            1.0 / len(data)
        )

    data["Probability"] = data[
        "Contribution_Weight"
    ]

    data["Probability_Percent"] = (
        data["Probability"] * 100
    )

    return data


def equb_probability():
    section_title(
        "Contribution-Weighted Probability Engine",
        "Research and demonstration model based on regular contribution.",
    )

    data = probability_table()

    if data.empty:
        st.info(
            "Register Equb members first."
        )
        return

    total_regular = data[
        "Regular_Contribution"
    ].sum()

    if total_regular <= 0:
        st.warning(
            "All regular contributions are zero. "
            "Equal probabilities are therefore used."
        )

    display = data.copy()

    display["Regular_Contribution"] = (
        display["Regular_Contribution"].map(money)
    )

    display["Historical_Paid"] = (
        display["Historical_Paid"].map(money)
    )

    display["Contribution_Weight"] = (
        display["Contribution_Weight"].map(
            lambda x: f"{x:.4f}"
        )
    )

    display["Probability"] = (
        display["Probability"].map(
            lambda x: f"{x:.4f}"
        )
    )

    display["Probability_Percent"] = (
        display["Probability_Percent"].map(
            lambda x: f"{x:.2f}%"
        )
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Regular Contribution",
        money(total_regular),
    )

    with col2:
        run = st.button(
            "Run Weighted Demonstration",
            type="primary",
            use_container_width=True,
        )

    if run:
        equb_members = members("Equb")

        probabilities = data[
            "Probability"
        ].tolist()

        selected_index = random.choices(
            range(len(equb_members)),
            weights=probabilities,
            k=1,
        )[0]

        winner = equb_members[
            selected_index
        ]

        st.success(
            "Selected demonstration member: "
            f"{winner['full_name']} "
            f"({winner['member_no']})"
        )

        audit(
            "Executed weighted probability demonstration",
            "Equb",
            winner["member_no"],
        )

    st.markdown(
        """
        **Model note**

        For member \(i\), the demonstration weight is
        proportional to the positive regular contribution
        \(C_i\):

        \(w_i = C_i / \\sum_j C_j\)

        If all regular contributions are zero, equal
        probabilities are assigned.

        This is a research/demo probability engine and should
        not be interpreted as a mandatory Equb governance rule.
        """
    )


# ============================================================
# MODULE 7: IDFS IDDIR
# ============================================================

def iddir():
    header(
        "IDFS Iddir",
        "Community risk sharing for approved social and community needs",
    )

    tabs = st.tabs(
        [
            "Overview",
            "Community Events",
            "Property Management",
            "Transactions",
            "Member Support History",
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

    benefits = sql(
        """
        SELECT COALESCE(SUM(approved_amount), 0) AS n
        FROM iddir_events
        WHERE status IN ('Approved', 'Paid')
        """,
        fetch=True,
    )[0]["n"]

    property_value = sql(
        """
        SELECT COALESCE(SUM(current_value), 0) AS n
        FROM properties
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    pending = sql(
        """
        SELECT COUNT(*) AS n
        FROM iddir_events
        WHERE status='Pending'
        """,
        fetch=True,
    )[0]["n"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Active Members",
        active_members,
    )

    col2.metric(
        "Approved Support",
        money(benefits),
    )

    col3.metric(
        "Active Property Value",
        money(property_value),
    )

    col4.metric(
        "Pending Cases",
        pending,
    )

    st.info(
        """
        Iddir operating scope: the platform records
        community support cases for funeral, wedding,
        holiday, emergency, medical, family and other
        approved purposes. The same module maintains
        community property such as land, buildings,
        vehicles, equipment and furniture.
        """
    )


# ============================================================
# IDDIR EVENTS
# ============================================================

def iddir_events():
    section_title(
        "Community Event and Benefit Management",
        "Record requests, approvals and payments.",
    )

    iddir_members = members("Iddir")

    if not iddir_members:
        st.info(
            "Register Iddir members first."
        )
        return

    member_options = [
        f"{m['member_no']} | {m['full_name']}"
        for m in iddir_members
    ]

    with st.form("iddir_event_form"):
        member_choice = st.selectbox(
            "Member / Beneficiary",
            member_options,
        )

        event_type = st.selectbox(
            "Event Type",
            EVENT_TYPES,
        )

        event_date = st.date_input(
            "Event Date",
            value=date.today(),
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
            "Case / Payment Reference",
        )

        description = st.text_area(
            "Description",
        )

        submitted = st.form_submit_button(
            "Record Community Support Case",
            type="primary",
        )

    if submitted:
        member = iddir_members[
            member_options.index(member_choice)
        ]

        payment_date = (
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                member["branch_id"],
                event_type,
                member["id"],
                str(event_date),
                description.strip(),
                requested,
                approved,
                status,
                payment_date,
                reference.strip(),
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Iddir",
                    member["branch_id"],
                    member["id"],
                    "Community Benefit Payment",
                    approved,
                    reference.strip(),
                    str(event_date),
                    f"{event_type} support",
                    now(),
                ),
            )

        audit(
            "Recorded Iddir support case",
            "Iddir",
            f"{event_type} for {member['member_no']}",
        )

        st.success(
            "Support case recorded successfully."
        )

        st.rerun()

    data = df(
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
        data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MODULE 8: IDDIR PROPERTY MANAGEMENT
# ============================================================

def iddir_properties():
    section_title(
        "Iddir Property Management",
        "Community asset register and valuation.",
    )

    iddir_branches = branches("Iddir")

    if not iddir_branches:
        st.warning(
            "Create an Iddir branch first."
        )
        return

    branch_options = [
        f"{b['code']} | {b['name']}"
        for b in iddir_branches
    ]

    with st.form("property_form"):
        branch_choice = st.selectbox(
            "Iddir Branch",
            branch_options,
        )

        col1, col2 = st.columns(2)

        property_code = col1.text_input(
            "Property Code",
        )

        property_type = col2.selectbox(
            "Property Type",
            PROPERTY_TYPES,
        )

        description = col1.text_input(
            "Description",
        )

        location = col2.text_input(
            "Location",
        )

        acquisition_date = col1.date_input(
            "Acquisition Date",
            value=date.today(),
        )

        acquisition_cost = col2.number_input(
            "Acquisition Cost (ETB)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
        )

        current_value = col1.number_input(
            "Current Estimated Value (ETB)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
        )

        status = col2.selectbox(
            "Status",
            [
                "Active",
                "Under Maintenance",
                "Disposed",
                "Transferred",
            ],
        )

        custodian = col1.text_input(
            "Custodian",
        )

        notes = st.text_area(
            "Notes",
        )

        submitted = st.form_submit_button(
            "Register Property",
            type="primary",
        )

    if submitted:
        property_code = property_code.strip()

        if not property_code:
            st.error(
                "Property code is required."
            )
            return

        branch = iddir_branches[
            branch_options.index(branch_choice)
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    branch["id"],
                    property_code,
                    property_type,
                    description.strip(),
                    location.strip(),
                    str(acquisition_date),
                    acquisition_cost,
                    current_value,
                    status,
                    custodian.strip(),
                    notes.strip(),
                    now(),
                ),
            )

            audit(
                "Registered Iddir property",
                "Iddir",
                property_code,
            )

            st.success(
                "Property registered successfully."
            )

            st.rerun()

        except sqlite3.IntegrityError:
            st.error(
                "Property code already exists."
            )

    data = df(
        """
        SELECT
            p.property_code AS Property_Code,
            p.property_type AS Type,
            p.description AS Description,
            b.code AS Branch,
            p.location AS Location,
            p.acquisition_date AS Acquisition_Date,
            p.acquisition_cost AS Acquisition_Cost,
            p.current_value AS Current_Value,
            p.status AS Status,
            p.custodian AS Custodian,
            p.notes AS Notes
        FROM properties p
        LEFT JOIN branches b
            ON p.branch_id=b.id
        ORDER BY p.id DESC
        """
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# IDDIR TRANSACTIONS
# ============================================================

def iddir_transaction_view():
    section_title(
        "Iddir Transactions",
        "Community financial activity generated by Iddir.",
    )

    data = df(
        """
        SELECT
            transaction_date AS Date,
            transaction_type AS Transaction_Type,
            amount AS Amount,
            reference AS Reference,
            description AS Description
        FROM transactions
        WHERE module='Iddir'
        ORDER BY id DESC
        """
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# IDDIR MEMBER HISTORY
# ============================================================

def iddir_history():
    section_title(
        "Member Support History",
        "Historical support cases for an Iddir member.",
    )

    iddir_members = members("Iddir")

    if not iddir_members:
        st.info(
            "No Iddir members registered."
        )
        return

    options = [
        f"{m['member_no']} | {m['full_name']}"
        for m in iddir_members
    ]

    selected = st.selectbox(
        "Select Member",
        options,
    )

    member = iddir_members[
        options.index(selected)
    ]

    data = df(
        """
        SELECT
            event_date AS Event_Date,
            event_type AS Event_Type,
            requested_amount AS Requested,
            approved_amount AS Approved,
            status AS Status,
            reference AS Reference,
            description AS Description
        FROM iddir_events
        WHERE member_id=?
        ORDER BY id DESC
        """,
        (member["id"],),
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MODULE 9: TRANSACTIONS
# ============================================================

def transactions():
    header(
        "Transactions",
        "Centralized transaction register for Equb and Iddir",
    )

    tab_record, tab_register = st.tabs(
        [
            "Record Transaction",
            "Transaction Register",
        ]
    )

    with tab_record:
        all_branches = branches()
        all_members = members()

        if not all_branches:
            st.warning(
                "Create a branch before recording a transaction."
            )
            return

        branch_options = [
            f"{b['code']} | {b['name']}"
            for b in all_branches
        ]

        member_options = [
            "No member"
        ] + [
            f"{m['member_no']} | {m['full_name']}"
            for m in all_members
        ]

        with st.form("transaction_form"):
            module = st.selectbox(
                "Module",
                MODULES,
            )

            branch_choice = st.selectbox(
                "Branch",
                branch_options,
            )

            member_choice = st.selectbox(
                "Member",
                member_options,
            )

            transaction_type = st.selectbox(
                "Transaction Type",
                [
                    "Contribution",
                    "Savings Receipt",
                    "Payout",
                    "Community Benefit Payment",
                    "Asset Purchase",
                    "Asset Sale",
                    "Other",
                ],
            )

            amount = st.number_input(
                "Amount (ETB)",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

            transaction_date = st.date_input(
                "Transaction Date",
                value=date.today(),
            )

            reference = st.text_input(
                "Reference",
            )

            description = st.text_area(
                "Description",
            )

            submitted = st.form_submit_button(
                "Record Transaction",
                type="primary",
            )

        if submitted:
            branch = all_branches[
                branch_options.index(branch_choice)
            ]

            if member_choice == "No member":
                member_id = None
            else:
                member_index = (
                    member_options.index(member_choice)
                    - 1
                )
                member_id = all_members[
                    member_index
                ]["id"]

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    module,
                    branch["id"],
                    member_id,
                    transaction_type,
                    amount,
                    reference.strip(),
                    str(transaction_date),
                    description.strip(),
                    now(),
                ),
            )

            audit(
                "Recorded transaction",
                module,
                f"{transaction_type}: {money(amount)}",
            )

            st.success(
                "Transaction recorded successfully."
            )

            st.rerun()

    with tab_register:
        data = df(
            """
            SELECT
                t.transaction_date AS Date,
                t.module AS Module,
                b.code AS Branch,
                COALESCE(m.member_no, '') AS Member_No,
                t.transaction_type AS Type,
                t.amount AS Amount,
                t.reference AS Reference,
                t.description AS Description
            FROM transactions t
            LEFT JOIN branches b
                ON t.branch_id=b.id
            LEFT JOIN members m
                ON t.member_id=m.id
            ORDER BY t.id DESC
            LIMIT 1000
            """
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

        download_dataframe(
            data,
            "idfs_transactions.csv",
        )


# ============================================================
# MODULE 10: REPORTS
# ============================================================

def reports():
    header(
        "Reports and Analytics",
        "Management information and downloadable records",
    )

    report_type = st.selectbox(
        "Report",
        [
            "Executive Summary",
            "Branch Register",
            "Member Register",
            "Equb Contributions",
            "Equb Rounds",
            "Equb Probability",
            "Iddir Community Support",
            "Iddir Properties",
            "Transactions",
        ],
    )

    if report_type == "Executive Summary":
        query = """
            SELECT
                module AS Module,
                COUNT(*) AS Active_Members,
                ROUND(
                    AVG(regular_contribution), 2
                ) AS Average_Contribution,
                ROUND(
                    AVG(trust_score), 3
                ) AS Average_Trust
            FROM members
            WHERE status='Active'
            GROUP BY module
        """
        filename = "idfs_summary.csv"

    elif report_type == "Branch Register":
        query = """
            SELECT
                code AS Branch_Code,
                name AS Branch_Name,
                module AS Module,
                location AS Location,
                manager AS Manager,
                phone AS Phone,
                status AS Status
            FROM branches
            ORDER BY module, name
        """
        filename = "idfs_branches.csv"

    elif report_type == "Member Register":
        query = """
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
            ORDER BY m.module, m.full_name
        """
        filename = "idfs_members.csv"

    elif report_type == "Equb Contributions":
        query = """
            SELECT
                m.member_no AS Member_No,
                m.full_name AS Member,
                COUNT(c.id) AS Payments,
                COALESCE(
                    SUM(c.amount), 0
                ) AS Total_Paid
            FROM members m
            LEFT JOIN contributions c
                ON m.id=c.member_id
                AND c.module='Equb'
                AND c.status='Paid'
            WHERE m.module='Equb'
            GROUP BY m.id
            ORDER BY Total_Paid DESC
        """
        filename = "idfs_equb_contributions.csv"

    elif report_type == "Equb Rounds":
        query = """
            SELECT
                r.round_no AS Round_No,
                b.code AS Branch,
                r.contribution_amount
                    AS Contribution,
                r.expected_members AS Members,
                r.total_pool AS Total_Pool,
                r.start_date AS Start_Date,
                r.draw_date AS Draw_Date,
                r.status AS Status,
                COALESCE(
                    m.full_name, ''
                ) AS Winner
            FROM equb_rounds r
            JOIN branches b
                ON r.branch_id=b.id
            LEFT JOIN members m
                ON r.winner_member_id=m.id
            ORDER BY r.id DESC
        """
        filename = "idfs_equb_rounds.csv"

    elif report_type == "Equb Probability":
        data = probability_table()

        if data.empty:
            st.info(
                "No Equb probability data available."
            )
            return

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

        download_dataframe(
            data,
            "idfs_equb_probability.csv",
        )

        return

    elif report_type == "Iddir Community Support":
        query = """
            SELECT
                event_type AS Event_Type,
                COUNT(*) AS Cases,
                COALESCE(
                    SUM(requested_amount), 0
                ) AS Requested,
                COALESCE(
                    SUM(approved_amount), 0
                ) AS Approved
            FROM iddir_events
            GROUP BY event_type
            ORDER BY Approved DESC
        """
        filename = "idfs_iddir_support.csv"

    elif report_type == "Iddir Properties":
        query = """
            SELECT
                property_type AS Property_Type,
                COUNT(*) AS Assets,
                COALESCE(
                    SUM(acquisition_cost), 0
                ) AS Acquisition_Cost,
                COALESCE(
                    SUM(current_value), 0
                ) AS Current_Value
            FROM properties
            GROUP BY property_type
            ORDER BY Current_Value DESC
        """
        filename = "idfs_iddir_properties.csv"

    else:
        query = """
            SELECT
                module AS Module,
                transaction_type AS Transaction_Type,
                COUNT(*) AS Transactions,
                COALESCE(
                    SUM(amount), 0
                ) AS Total_Amount
            FROM transactions
            GROUP BY module, transaction_type
            ORDER BY module, Total_Amount DESC
        """
        filename = "idfs_transactions.csv"

    data = df(query)

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
    )

    download_dataframe(
        data,
        filename,
    )


# ============================================================
# MODULE 11: AUDIT TRAIL
# ============================================================

def audit_page():
    header(
        "Audit Trail",
        "Traceable record of important system activities",
    )

    data = df(
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
        data,
        use_container_width=True,
        hide_index=True,
    )

    download_dataframe(
        data,
        "idfs_audit.csv",
    )


# ============================================================
# MODULE 12: USER ADMINISTRATION
# ============================================================

def users_page():
    header(
        "User Administration",
        "Role-based demonstration accounts",
    )

    data = df(
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
        data,
        use_container_width=True,
        hide_index=True,
    )

    with st.form("user_form"):
        col1, col2 = st.columns(2)

        username = col1.text_input(
            "Username",
        )

        full_name = col2.text_input(
            "Full Name",
        )

        password = col1.text_input(
            "Password",
            type="password",
        )

        role = col2.selectbox(
            "Role",
            ROLES,
        )

        module = col1.selectbox(
            "Module",
            ["Portal"] + MODULES,
        )

        available_branches = (
            branches(module)
            if module in MODULES
            else []
        )

        branch_options = [
            "No branch"
        ] + [
            f"{b['code']} | {b['name']}"
            for b in available_branches
        ]

        branch_choice = col2.selectbox(
            "Branch",
            branch_options,
        )

        active = col1.selectbox(
            "Account Status",
            [
                "Active",
                "Inactive",
            ],
        )

        submitted = st.form_submit_button(
            "Create User",
            type="primary",
        )

    if submitted:
        username = username.strip()
        full_name = full_name.strip()

        if not username or not full_name:
            st.error(
                "Username and full name are required."
            )
            return

        if len(password) < 6:
            st.error(
                "Password must contain at least six characters."
            )
            return

        if branch_choice == "No branch":
            branch_id = None
        else:
            branch_index = (
                branch_options.index(branch_choice)
                - 1
            )
            branch_id = available_branches[
                branch_index
            ]["id"]

        active_value = (
            1 if active == "Active" else 0
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    pwd_hash(password),
                    full_name,
                    role,
                    module,
                    branch_id,
                    active_value,
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
# MODULE 1: EXECUTIVE DASHBOARD
# ============================================================

def dashboard():
    header(
        "IDFS Executive Dashboard",
        "Integrated Equb savings and Iddir community risk-sharing platform",
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
        SELECT COALESCE(SUM(amount), 0) AS n
        FROM contributions
        WHERE module='Equb'
          AND status='Paid'
        """,
        fetch=True,
    )[0]["n"]

    iddir_property = sql(
        """
        SELECT COALESCE(SUM(current_value), 0) AS n
        FROM properties
        WHERE status='Active'
        """,
        fetch=True,
    )[0]["n"]

    equb_members = sql(
        """
        SELECT COUNT(*) AS n
        FROM members
        WHERE module='Equb'
          AND status='Active'
        """,
        fetch=True,
    )[0]["n"]

    iddir_members = sql(
        """
        SELECT COUNT(*) AS n
        FROM members
        WHERE module='Iddir'
          AND status='Active'
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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Active Members",
        active_members,
    )

    col2.metric(
        "Active Branches",
        active_branches,
    )

    col3.metric(
        "Equb Savings",
        money(equb_savings),
    )

    col4.metric(
        "Iddir Property",
        money(iddir_property),
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Equb Members",
        equb_members,
    )

    col2.metric(
        "Iddir Members",
        iddir_members,
    )

    col3.metric(
        "Pending Iddir Cases",
        pending_cases,
    )

    open_rounds = sql(
        """
        SELECT COUNT(*) AS n
        FROM equb_rounds
        WHERE status='Open'
        """,
        fetch=True,
    )[0]["n"]

    col4.metric(
        "Open Equb Rounds",
        open_rounds,
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("IDFS Equb")

        st.write(
            """
            Community savings, regular contributions,
            Equb rounds, payment records and a
            contribution-weighted probability demonstration.
            """
        )

    with col2:
        st.subheader("IDFS Iddir")

        st.write(
            """
            Community risk sharing for funeral, wedding,
            holiday, emergency, medical, family and
            other approved support, together with
            community property management.
            """
        )

    st.divider()

    st.subheader(
        "Recent System Activity"
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

    st.dataframe(
        activity,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    # Initialize database safely on every Streamlit run.
    init_db()

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    if not st.session_state.get(
        "authenticated",
        False,
    ):
        login()
        return

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    st.sidebar.title(
        "IDFS Web Platform"
    )

    st.sidebar.caption(
        "Indigenous Digital Financial System"
    )

    st.sidebar.divider()

    st.sidebar.write(
        f"**User:** "
        f"{st.session_state.get('full_name', '')}"
    )

    st.sidebar.write(
        f"**Role:** "
        f"{st.session_state.get('role', '')}"
    )

    st.sidebar.write(
        f"**Module:** "
        f"{st.session_state.get('module', '')}"
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "Sign out",
        use_container_width=True,
    ):
        audit(
            "Logout",
            "Portal",
            st.session_state.get(
                "username",
                "",
            ),
        )

        st.session_state.clear()

        st.rerun()

    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------

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

    if (
        st.session_state.get("role")
        == "Administrator"
    ):
        navigation.append(
            "User Administration"
        )

    page = st.sidebar.radio(
        "Navigation",
        navigation,
    )

    # --------------------------------------------------------
    # Page routing
    # --------------------------------------------------------

    if page == "Dashboard":
        dashboard()

    elif page == "Branch Management":
        branch_page()

    elif page == "Member Management":
        member_page()

    elif page == "IDFS Equb":
        equb()

    elif page == "IDFS Iddir":
        iddir()

    elif page == "Transactions":
        transactions()

    elif page == "Reports and Analytics":
        reports()

    elif page == "Audit Trail":
        audit_page()

    elif page == "User Administration":
        users_page()


# ============================================================
# CORRECT PYTHON ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
