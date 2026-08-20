import streamlit as st
import sqlite3, hashlib, secrets, hmac, random
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import numpy as np

# =========================================================
# IDDIR APP MANAGEMENT SYSTEM
# Standalone Streamlit prototype
# =========================================================

st.set_page_config(
    page_title="Iddir App Management System",
    page_icon="I",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = Path("iddir_demo.db")
ROLES = ["Administrator", "Branch Manager", "Finance Officer", "Member"]

st.markdown("""
<style>
.main-title{font-size:2rem;font-weight:700;color:#163A5F}
.sub-title{color:#64748B;margin-bottom:1rem}
.section-card{padding:1rem 1.2rem;border:1px solid #E2E8F0;border-radius:12px;
background:#F8FAFC;margin-bottom:1rem}
.module-label{color:#0B5CAD;font-weight:700;font-size:.82rem;text-transform:uppercase}
.manual-card{padding:1rem 1.2rem;border:1px solid #CBD5E1;border-radius:10px;
background:white;margin-bottom:1rem}
.metric-card{padding:.8rem;border:1px solid #E2E8F0;border-radius:10px}
</style>
""", unsafe_allow_html=True)


# =========================================================
# UTILITIES
# =========================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(x):
    try:
        return f"{float(x):,.2f} ETB"
    except Exception:
        return "0.00 ETB"


def sql(q, p=(), fetch=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(q, p)
    result = [dict(x) for x in cur.fetchall()] if fetch else None
    conn.commit()
    conn.close()
    return result


def df(q, p=()):
    return pd.DataFrame(sql(q, p, True))


def download(data, name):
    if not data.empty:
        st.download_button(
            "Download CSV",
            data.to_csv(index=False).encode("utf-8"),
            name,
            "text/csv",
            use_container_width=True
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


def audit(action, module="Portal", details=""):
    sql(
        """INSERT INTO audit_log
        (username,module,action,details,timestamp)
        VALUES(?,?,?,?,?)""",
        (
            st.session_state.get("username", "system"),
            module,
            action,
            details,
            now()
        )
    )


def header(title, subtitle=""):
    st.markdown(
        f'<div class="main-title">{title}</div>',
        unsafe_allow_html=True
    )
    if subtitle:
        st.markdown(
            f'<div class="sub-title">{subtitle}</div>',
            unsafe_allow_html=True
        )


# =========================================================
# DATABASE
# =========================================================

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        full_name TEXT,
        role TEXT,
        module TEXT,
        branch_id INTEGER,
        active INTEGER DEFAULT 1,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS branches(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        name TEXT,
        module TEXT DEFAULT 'Iddir',
        location TEXT,
        manager TEXT,
        phone TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_no TEXT UNIQUE,
        full_name TEXT,
        household_no TEXT,
        phone TEXT,
        sex TEXT,
        birth_date TEXT,
        join_date TEXT,
        module TEXT DEFAULT 'Iddir',
        branch_id INTEGER,
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
        group_code TEXT UNIQUE,
        group_name TEXT,
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
        UNIQUE(group_id,member_id)
    );

    CREATE TABLE IF NOT EXISTS contributions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        group_id INTEGER,
        module TEXT DEFAULT 'Iddir',
        amount REAL DEFAULT 0,
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
    """)

    conn.commit()
    conn.close()

    if not sql("SELECT id FROM users WHERE username='admin'", fetch=True):
        sql(
            """INSERT INTO users
            (username,password_hash,full_name,role,module,active,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (
                "admin",
                pwd_hash("admin123"),
                "Iddir Administrator",
                "Administrator",
                "Portal",
                1,
                now()
            )
        )

    demo_branches = [
        ("IDR-001", "Iddir Central Branch", "Aksum"),
        ("IDR-002", "Iddir North Branch", "Shire")
    ]

    for code, name, location in demo_branches:
        if not sql(
            "SELECT id FROM branches WHERE code=?",
            (code,),
            True
        ):
            sql(
                """INSERT INTO branches
                (code,name,module,location,manager,phone,status,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    code, name, "Iddir", location,
                    "Branch Manager", "", "Active", now()
                )
            )


def branches():
    return sql(
        "SELECT * FROM branches WHERE module='Iddir' ORDER BY name",
        fetch=True
    )


def members():
    return sql(
        """SELECT m.*,b.code branch_code,b.name branch_name
        FROM members m
        LEFT JOIN branches b ON m.branch_id=b.id
        WHERE m.module='Iddir'
        ORDER BY m.full_name""",
        fetch=True
    )


# =========================================================
# MATHEMATICAL / STATISTICAL MODELS
# =========================================================

def benefit_eligibility_score(member_id):
    """
    Prototype statistical score:
        E_i = w1 C_i + w2 P_i + w3 T_i + w4 M_i

    C_i = normalized contribution level
    P_i = payment consistency
    T_i = trust score
    M_i = membership duration proxy
    """
    ms = members()
    if not ms:
        return pd.DataFrame()

    rows = []

    for m in ms:
        h = df(
            """SELECT amount,contribution_date,status
            FROM contributions
            WHERE member_id=? AND module='Iddir'
            ORDER BY contribution_date""",
            (m["id"],)
        )

        planned = float(m["regular_contribution"] or 0)

        if h.empty:
            total_paid = 0
            consistency = 0
        else:
            total_paid = float(h["amount"].sum())
            paid_count = int((h["status"] == "Paid").sum())
            consistency = paid_count / len(h)

        join_date = pd.to_datetime(m["join_date"], errors="coerce")
        if pd.isna(join_date):
            membership_years = 0
        else:
            membership_years = max(
                0,
                (pd.Timestamp.today() - join_date).days / 365.25
            )

        rows.append({
            "Member_ID": m["id"],
            "Member_No": m["member_no"],
            "Member": m["full_name"],
            "Planned_Contribution": planned,
            "Total_Paid": total_paid,
            "Payment_Consistency": consistency,
            "Trust_Score": float(m["trust_score"] or 0),
            "Membership_Years": membership_years
        })

    x = pd.DataFrame(rows)

    def normalize(s):
        mx = float(s.max())
        return s / mx if mx > 0 else s * 0

    x["Contribution_Component"] = normalize(
        x["Total_Paid"]
    )
    x["Consistency_Component"] = x["Payment_Consistency"]
    x["Trust_Component"] = x["Trust_Score"]
    x["Membership_Component"] = normalize(
        x["Membership_Years"]
    )

    # Weights can be interpreted as a transparent prototype model.
    w1, w2, w3, w4 = 0.35, 0.30, 0.20, 0.15

    x["Eligibility_Score"] = (
        w1 * x["Contribution_Component"]
        + w2 * x["Consistency_Component"]
        + w3 * x["Trust_Component"]
        + w4 * x["Membership_Component"]
    )

    return x.sort_values(
        "Eligibility_Score",
        ascending=False
    ).reset_index(drop=True)


def fund_sustainability_model():
    """
    Simple Iddir fund sustainability model:

        R_t = C_t + O_t
        F_{t+1} = F_t + R_t - B_t - A_t

    where:
      F = fund balance
      C = contributions
      O = other income
      B = benefits
      A = administrative/operating expenditure
    """
    x = df("""
        SELECT
            contribution_date Date,
            SUM(amount) Contributions
        FROM contributions
        WHERE module='Iddir' AND status='Paid'
        GROUP BY contribution_date
        ORDER BY contribution_date
    """)

    if x.empty:
        return x

    benefits = df("""
        SELECT
            event_date Date,
            SUM(paid_amount) Benefits
        FROM benefits
        WHERE status IN ('Approved','Paid')
        GROUP BY event_date
        ORDER BY event_date
    """)

    x["Date"] = pd.to_datetime(x["Date"])
    if not benefits.empty:
        benefits["Date"] = pd.to_datetime(benefits["Date"])

    x = x.groupby("Date", as_index=False)["Contributions"].sum()

    if not benefits.empty:
        x = x.merge(benefits, on="Date", how="outer")
    else:
        x["Benefits"] = 0

    x = x.fillna(0).sort_values("Date")
    x["Net_Fund_Change"] = x["Contributions"] - x["Benefits"]
    x["Cumulative_Fund"] = x["Net_Fund_Change"].cumsum()

    return x


def property_depreciation(cost, salvage, life, years):
    if life <= 0:
        return cost
    annual = max((cost - salvage) / life, 0)
    book_value = max(cost - annual * years, salvage)
    return annual, book_value


# =========================================================
# LOGIN
# =========================================================

def login():
    header(
        "Iddir App Management System",
        "Digital indigenous community mutual-support and financial management prototype."
    )

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True
        )

    if submitted:
        result = sql(
            "SELECT * FROM users WHERE username=? AND active=1",
            (username.strip(),),
            True
        )

        if result and check_pwd(password, result[0]["password_hash"]):
            user = result[0]
            st.session_state.update(
                authenticated=True,
                username=user["username"],
                full_name=user["full_name"],
                role=user["role"],
                branch_id=user["branch_id"]
            )
            audit("Successful login")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Demonstration account: admin / admin123")


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():
    header(
        "Iddir Executive Dashboard",
        "Community membership, mutual-support funds, benefits, property and financial management."
    )

    active_members = sql(
        """SELECT COUNT(*) n FROM members
        WHERE module='Iddir' AND status='Active'""",
        fetch=True
    )[0]["n"]

    active_groups = sql(
        """SELECT COUNT(*) n FROM iddir_groups
        WHERE status='Active'""",
        fetch=True
    )[0]["n"]

    total_contributions = sql(
        """SELECT COALESCE(SUM(amount),0) n
        FROM contributions
        WHERE module='Iddir' AND status='Paid'""",
        fetch=True
    )[0]["n"]

    total_property = sql(
        """SELECT COALESCE(SUM(current_value * quantity),0) n
        FROM properties""",
        fetch=True
    )[0]["n"]

    a, b, c, d = st.columns(4)
    a.metric("Active Members", active_members)
    b.metric("Active Iddir Groups", active_groups)
    c.metric("Community Contributions", money(total_contributions))
    d.metric("Property Value", money(total_property))

    st.markdown("""
    <div class="section-card">
    <div class="module-label">Iddir App Management System</div>
    A digital management platform for community mutual-support organizations,
    combining member administration, regular contributions, benefit management,
    community events, property management, financial records, statistical
    monitoring and transparent audit controls.
    </div>
    """, unsafe_allow_html=True)

    a, b, c, d = st.columns(4)

    benefits = sql(
        """SELECT COALESCE(SUM(paid_amount),0) n
        FROM benefits WHERE status='Paid'""",
        fetch=True
    )[0]["n"]

    emergency = sql(
        """SELECT COALESCE(SUM(emergency_fund),0) n
        FROM iddir_groups WHERE status='Active'""",
        fetch=True
    )[0]["n"]

    a.metric("Benefits Paid", money(benefits))
    b.metric("Emergency Funds", money(emergency))
    c.metric(
        "Registered Properties",
        sql("SELECT COUNT(*) n FROM properties", fetch=True)[0]["n"]
    )
    d.metric(
        "Community Events",
        sql("SELECT COUNT(*) n FROM events", fetch=True)[0]["n"]
    )

    st.subheader("Recent Activities")

    x = df("""
        SELECT timestamp Timestamp,
               username User,
               module Module,
               action Action,
               details Details
        FROM audit_log
        ORDER BY id DESC
        LIMIT 15
    """)

    if not x.empty:
        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# BRANCH MANAGEMENT
# =========================================================

def branch_page():
    header(
        "Module 2: Branch Management",
        "Branch-based administrative structure for Iddir organizations."
    )

    t1, t2 = st.tabs(
        ["Branch Directory", "Register Branch"]
    )

    with t1:
        x = df("""
            SELECT code Branch_Code,
                   name Branch_Name,
                   module Module,
                   location Location,
                   manager Manager,
                   phone Phone,
                   status Status
            FROM branches
            WHERE module='Iddir'
            ORDER BY name
        """)

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True
        )

        download(x, "iddir_branches.csv")

    with t2:
        with st.form("branch_form"):
            a, b = st.columns(2)

            code = a.text_input("Branch Code")
            name = b.text_input("Branch Name")
            location = a.text_input("Location")
            manager = b.text_input("Manager")
            phone = a.text_input("Phone")
            status = b.selectbox(
                "Status",
                ["Active", "Inactive"]
            )

            submitted = st.form_submit_button(
                "Register Branch",
                type="primary",
                use_container_width=True
            )

        if submitted:
            try:
                sql(
                    """INSERT INTO branches
                    (code,name,module,location,manager,phone,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        code.strip(),
                        name.strip(),
                        "Iddir",
                        location,
                        manager,
                        phone,
                        status,
                        now()
                    )
                )

                audit(
                    "Created branch",
                    "Iddir",
                    code
                )

                st.success("Branch registered.")
                st.rerun()

            except sqlite3.IntegrityError:
                st.error("Branch code already exists.")


# =========================================================
# MEMBER MANAGEMENT
# =========================================================

def member_page():
    header(
        "Module 3: Member Management",
        "Registration, household information, contribution plans and membership records."
    )

    t1, t2, t3 = st.tabs(
        [
            "Member Directory",
            "Register Member",
            "Member Profile"
        ]
    )

    with t1:
        x = df("""
            SELECT
                m.member_no Member_No,
                m.full_name Full_Name,
                m.household_no Household_No,
                COALESCE(b.name,'') Branch,
                m.phone Phone,
                m.join_date Join_Date,
                m.regular_contribution Planned_Contribution,
                m.contribution_frequency Frequency,
                m.trust_score Trust_Score,
                m.status Status
            FROM members m
            LEFT JOIN branches b ON m.branch_id=b.id
            WHERE m.module='Iddir'
            ORDER BY m.full_name
        """)

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True
        )

        download(x, "iddir_members.csv")

    with t2:
        bl = branches()
        options = [
            f"{z['code']} | {z['name']}"
            for z in bl
        ]

        with st.form("member_form"):

            a, b, c = st.columns(3)

            member_no = a.text_input("Member Number")
            full_name = b.text_input("Full Name")
            household_no = c.text_input("Household Number")

            phone = a.text_input("Phone")
            sex = b.selectbox(
                "Sex",
                ["Not Specified", "Male", "Female"]
            )
            birth_date = c.date_input(
                "Birth Date",
                date(1990, 1, 1)
            )

            join_date = a.date_input(
                "Join Date",
                date.today()
            )

            branch = b.selectbox(
                "Branch",
                options or ["No branch"]
            )

            occupation = c.text_input("Occupation")

            contribution = a.number_input(
                "Regular Contribution (ETB)",
                0.0,
                step=50.0,
                value=100.0
            )

            frequency = b.selectbox(
                "Contribution Frequency",
                [
                    "Monthly",
                    "Quarterly",
                    "Weekly",
                    "Annual",
                    "Custom"
                ]
            )

            trust = c.number_input(
                "Initial Trust Score (%)",
                0.0,
                100.0,
                50.0,
                step=1.0
            )

            status = a.selectbox(
                "Status",
                ["Active", "Inactive", "Suspended"]
            )

            address = b.text_input("Address")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button(
                "Register Member",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if not member_no.strip() or not full_name.strip():
                st.error(
                    "Member number and full name are required."
                )

            else:

                branch_id = None

                if branch != "No branch":
                    branch_id = bl[
                        options.index(branch)
                    ]["id"]

                try:
                    sql(
                        """INSERT INTO members
                        (member_no,full_name,household_no,phone,sex,
                         birth_date,join_date,module,branch_id,
                         regular_contribution,contribution_frequency,
                         trust_score,status,address,occupation,notes,created_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            member_no,
                            full_name,
                            household_no,
                            phone,
                            sex,
                            str(birth_date),
                            str(join_date),
                            "Iddir",
                            branch_id,
                            contribution,
                            frequency,
                            trust / 100,
                            status,
                            address,
                            occupation,
                            notes,
                            now()
                        )
                    )

                    audit(
                        "Registered member",
                        "Iddir",
                        member_no
                    )

                    st.success(
                        "Member registered successfully."
                    )
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(
                        "Member number already exists."
                    )

    with t3:

        ms = members()

        if not ms:
            st.info(
                "No members registered yet."
            )
            return

        labels = [
            f"{z['member_no']} | {z['full_name']}"
            for z in ms
        ]

        selected = st.selectbox(
            "Select Member",
            labels
        )

        m = ms[labels.index(selected)]

        h = df(
            """SELECT contribution_date Date,
                      amount Amount,
                      status Status,
                      reference Reference,
                      payment_method Payment_Method
               FROM contributions
               WHERE member_id=? AND module='Iddir'
               ORDER BY id DESC""",
            (m["id"],)
        )

        a, b, c, d = st.columns(4)

        a.metric(
            "Planned Contribution",
            money(m["regular_contribution"])
        )

        b.metric(
            "Total Paid",
            money(h["Amount"].sum() if not h.empty else 0)
        )

        c.metric(
            "Trust Score",
            f"{m['trust_score']:.0%}"
        )

        d.metric(
            "Membership",
            m["status"]
        )

        st.dataframe(
            pd.DataFrame([{
                "Member Number": m["member_no"],
                "Full Name": m["full_name"],
                "Household": m["household_no"],
                "Branch": m["branch_name"] or "",
                "Phone": m["phone"] or "",
                "Frequency": m["contribution_frequency"],
                "Planned Contribution": m["regular_contribution"],
                "Trust Score": f"{m['trust_score']:.2%}",
                "Status": m["status"]
            }]),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Contribution History")

        if not h.empty:
            st.dataframe(
                h,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# IDDIR GROUP MANAGEMENT
# =========================================================

def group_page():
    header(
        "Module 4: Iddir Group Management",
        "Create and administer independent Iddir community groups."
    )

    t1, t2, t3 = st.tabs(
        [
            "Groups",
            "Register Group",
            "Group Membership"
        ]
    )

    with t1:

        x = df("""
            SELECT
                g.group_code Group_Code,
                g.group_name Group_Name,
                b.code Branch,
                g.contribution_amount Contribution,
                g.contribution_frequency Frequency,
                g.member_capacity Capacity,
                g.emergency_fund Emergency_Fund,
                g.property_value Property_Value,
                g.founding_date Founding_Date,
                g.status Status
            FROM iddir_groups g
            LEFT JOIN branches b ON g.branch_id=b.id
            ORDER BY g.group_name
        """)

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True
        )

        download(x, "iddir_groups.csv")

    with t2:

        bl = branches()
        options = [
            f"{z['code']} | {z['name']}"
            for z in bl
        ]

        with st.form("group_form"):

            a, b = st.columns(2)

            code = a.text_input("Group Code")
            name = b.text_input("Group Name")

            branch = a.selectbox(
                "Branch",
                options or ["No branch"]
            )

            amount = b.number_input(
                "Regular Contribution (ETB)",
                0.0,
                step=10.0,
                value=100.0
            )

            frequency = a.selectbox(
                "Contribution Frequency",
                ["Monthly", "Quarterly", "Weekly", "Annual"]
            )

            founding = b.date_input(
                "Founding Date",
                date.today()
            )

            capacity = a.number_input(
                "Member Capacity",
                0,
                step=1,
                value=100
            )

            emergency = b.number_input(
                "Initial Emergency Fund (ETB)",
                0.0,
                step=100.0
            )

            property_value = a.number_input(
                "Initial Property Value (ETB)",
                0.0,
                step=100.0
            )

            status = b.selectbox(
                "Status",
                ["Active", "Inactive"]
            )

            notes = st.text_area("Notes")

            submitted = st.form_submit_button(
                "Register Iddir Group",
                type="primary",
                use_container_width=True
            )

        if submitted:

            branch_id = None

            if branch != "No branch":
                branch_id = bl[
                    options.index(branch)
                ]["id"]

            try:
                sql(
                    """INSERT INTO iddir_groups
                    (branch_id,group_code,group_name,
                     contribution_amount,contribution_frequency,
                     founding_date,member_capacity,
                     emergency_fund,property_value,
                     status,notes,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        branch_id,
                        code,
                        name,
                        amount,
                        frequency,
                        str(founding),
                        capacity,
                        emergency,
                        property_value,
                        status,
                        notes,
                        now()
                    )
                )

                audit(
                    "Created Iddir group",
                    "Iddir",
                    code
                )

                st.success(
                    "Iddir group registered."
                )
                st.rerun()

            except sqlite3.IntegrityError:
                st.error(
                    "Group code already exists."
                )

    with t3:

        groups = sql(
            "SELECT * FROM iddir_groups WHERE status='Active' ORDER BY group_name",
            fetch=True
        )

        ms = members()

        if not groups or not ms:
            st.info(
                "Create a group and register members first."
            )
            return

        g_labels = [
            f"{g['group_code']} | {g['group_name']}"
            for g in groups
        ]

        m_labels = [
            f"{m['member_no']} | {m['full_name']}"
            for m in ms
        ]

        with st.form("group_member_form"):

            a, b = st.columns(2)

            group_label = a.selectbox(
                "Iddir Group",
                g_labels
            )

            member_label = b.selectbox(
                "Member",
                m_labels
            )

            role = a.selectbox(
                "Role",
                ["Member", "Chairperson", "Secretary",
                 "Treasurer", "Committee Member"]
            )

            joined = b.date_input(
                "Joined Date",
                date.today()
            )

            submitted = st.form_submit_button(
                "Add Member to Group",
                type="primary",
                use_container_width=True
            )

        if submitted:

            g = groups[g_labels.index(group_label)]
            m = ms[m_labels.index(member_label)]

            try:
                sql(
                    """INSERT INTO group_members
                    (group_id,member_id,role,joined_date,status)
                    VALUES(?,?,?,?,?)""",
                    (
                        g["id"],
                        m["id"],
                        role,
                        str(joined),
                        "Active"
                    )
                )

                audit(
                    "Added member to Iddir group",
                    "Iddir",
                    f"{m['member_no']} -> {g['group_code']}"
                )

                st.success(
                    "Member added to group."
                )
                st.rerun()

            except sqlite3.IntegrityError:
                st.error(
                    "This member is already in the selected group."
                )

        x = df("""
            SELECT
                g.group_code Group_Code,
                g.group_name Group_Name,
                m.member_no Member_No,
                m.full_name Member,
                gm.role Role,
                gm.joined_date Joined_Date,
                gm.status Status
            FROM group_members gm
            JOIN iddir_groups g ON gm.group_id=g.id
            JOIN members m ON gm.member_id=m.id
            ORDER BY g.group_name,m.full_name
        """)

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# CONTRIBUTION MANAGEMENT
# =========================================================

def contribution_page():
    header(
        "Module 5: Contributions",
        "Regular Iddir contributions and member payment records."
    )

    groups = sql(
        "SELECT * FROM iddir_groups WHERE status='Active' ORDER BY group_name",
        fetch=True
    )

    ms = members()

    if not groups or not ms:
        st.info(
            "Create an Iddir group and register members first."
        )
        return

    g_labels = [
        f"{g['group_code']} | {g['group_name']}"
        for g in groups
    ]

    m_labels = [
        f"{m['member_no']} | {m['full_name']}"
        for m in ms
    ]

    with st.form("contribution_form"):

        a, b = st.columns(2)

        group_label = a.selectbox(
            "Iddir Group",
            g_labels
        )

        member_label = b.selectbox(
            "Member",
            m_labels
        )

        group = groups[g_labels.index(group_label)]

        amount = a.number_input(
            "Contribution Amount (ETB)",
            0.0,
            step=10.0,
            value=float(group["contribution_amount"])
        )

        contribution_date = b.date_input(
            "Contribution Date",
            date.today()
        )

        payment_method = a.selectbox(
            "Payment Method",
            [
                "Cash",
                "Bank Transfer",
                "Mobile Money",
                "Other"
            ]
        )

        reference = b.text_input(
            "Reference"
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Record Contribution",
            type="primary",
            use_container_width=True
        )

    if submitted and amount > 0:

        member = ms[m_labels.index(member_label)]

        sql(
            """INSERT INTO contributions
            (member_id,group_id,module,amount,
             contribution_date,status,reference,
             payment_method,notes,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                member["id"],
                group["id"],
                "Iddir",
                amount,
                str(contribution_date),
                "Paid",
                reference,
                payment_method,
                notes,
                now()
            )
        )

        audit(
            "Recorded Iddir contribution",
            "Iddir",
            f"{member['member_no']} | {amount}"
        )

        st.success(
            "Contribution recorded."
        )
        st.rerun()

    x = df("""
        SELECT
            c.contribution_date Date,
            g.group_code Group_Code,
            m.member_no Member_No,
            m.full_name Member,
            c.amount Amount,
            c.status Status,
            c.reference Reference,
            c.payment_method Payment_Method
        FROM contributions c
        JOIN members m ON c.member_id=m.id
        LEFT JOIN iddir_groups g ON c.group_id=g.id
        WHERE c.module='Iddir'
        ORDER BY c.id DESC
    """)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    download(
        x,
        "iddir_contributions.csv"
    )


# =========================================================
# BENEFIT / MUTUAL SUPPORT MANAGEMENT
# =========================================================

def benefits_page():
    header(
        "Module 6: Benefits and Mutual Support",
        "Management of community support requests, approvals and payments."
    )

    groups = sql(
        "SELECT * FROM iddir_groups ORDER BY group_name",
        fetch=True
    )

    ms = members()

    if not groups or not ms:
        st.info(
            "Register groups and members first."
        )
        return

    gl = [
        f"{g['group_code']} | {g['group_name']}"
        for g in groups
    ]

    ml = [
        f"{m['member_no']} | {m['full_name']}"
        for m in ms
    ]

    with st.form("benefit_form"):

        a, b = st.columns(2)

        group_label = a.selectbox(
            "Iddir Group",
            gl
        )

        member_label = b.selectbox(
            "Beneficiary Member",
            ml
        )

        benefit_type = a.selectbox(
            "Benefit / Support Type",
            [
                "Bereavement Support",
                "Funeral Support",
                "Emergency Medical Support",
                "Emergency Household Support",
                "Natural Disaster Support",
                "Other Community Support"
            ]
        )

        event_date = b.date_input(
            "Event Date",
            date.today()
        )

        approved = a.number_input(
            "Approved Amount (ETB)",
            0.0,
            step=100.0
        )

        paid = b.number_input(
            "Paid Amount (ETB)",
            0.0,
            step=100.0
        )

        status = a.selectbox(
            "Status",
            [
                "Requested",
                "Reviewed",
                "Approved",
                "Paid",
                "Rejected"
            ]
        )

        reference = b.text_input(
            "Reference"
        )

        description = st.text_area(
            "Description"
        )

        submitted = st.form_submit_button(
            "Save Benefit Record",
            type="primary",
            use_container_width=True
        )

    if submitted:

        g = groups[gl.index(group_label)]
        m = ms[ml.index(member_label)]

        sql(
            """INSERT INTO benefits
            (group_id,member_id,benefit_type,
             event_date,approved_amount,paid_amount,
             status,reference,description,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                g["id"],
                m["id"],
                benefit_type,
                str(event_date),
                approved,
                paid,
                status,
                reference,
                description,
                now()
            )
        )

        audit(
            "Recorded Iddir benefit",
            "Iddir",
            f"{m['member_no']} | {benefit_type} | {paid}"
        )

        st.success(
            "Benefit record saved."
        )
        st.rerun()

    x = df("""
        SELECT
            b.event_date Event_Date,
            g.group_code Group_Code,
            m.member_no Member_No,
            m.full_name Beneficiary,
            b.benefit_type Benefit_Type,
            b.approved_amount Approved,
            b.paid_amount Paid,
            b.status Status,
            b.reference Reference
        FROM benefits b
        JOIN members m ON b.member_id=m.id
        LEFT JOIN iddir_groups g ON b.group_id=g.id
        ORDER BY b.id DESC
    """)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    download(
        x,
        "iddir_benefits.csv"
    )


# =========================================================
# COMMUNITY EVENTS
# =========================================================

def events_page():
    header(
        "Module 7: Community Events",
        "Planning, costing and recording Iddir community events."
    )

    groups = sql(
        "SELECT * FROM iddir_groups ORDER BY group_name",
        fetch=True
    )

    if not groups:
        st.info("Create an Iddir group first.")
        return

    gl = [
        f"{g['group_code']} | {g['group_name']}"
        for g in groups
    ]

    with st.form("event_form"):

        a, b = st.columns(2)

        group_label = a.selectbox(
            "Iddir Group",
            gl
        )

        event_type = b.selectbox(
            "Event Type",
            [
                "Community Meeting",
                "Funeral",
                "Memorial",
                "Social Gathering",
                "Emergency Response",
                "Other"
            ]
        )

        event_date = a.date_input(
            "Event Date",
            date.today()
        )

        household_count = b.number_input(
            "Households / Participants",
            0,
            step=1
        )

        estimated_cost = a.number_input(
            "Estimated Cost (ETB)",
            0.0,
            step=100.0
        )

        actual_cost = b.number_input(
            "Actual Cost (ETB)",
            0.0,
            step=100.0
        )

        status = a.selectbox(
            "Status",
            [
                "Planned",
                "Active",
                "Completed",
                "Cancelled"
            ]
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
            use_container_width=True
        )

    if submitted:

        group = groups[gl.index(group_label)]

        sql(
            """INSERT INTO events
            (group_id,event_type,event_date,
             household_count,estimated_cost,
             actual_cost,status,location,notes,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
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
                now()
            )
        )

        audit(
            "Recorded community event",
            "Iddir",
            event_type
        )

        st.success(
            "Event saved."
        )
        st.rerun()

    x = df("""
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
        LEFT JOIN iddir_groups g ON e.group_id=g.id
        ORDER BY e.id DESC
    """)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    download(
        x,
        "iddir_events.csv"
    )


# =========================================================
# PROPERTY MANAGEMENT
# =========================================================

def property_page():
    header(
        "Module 8: Property Management",
        "Registration, valuation, condition monitoring and financial management of community property."
    )

    groups = sql(
        "SELECT * FROM iddir_groups ORDER BY group_name",
        fetch=True
    )

    t1, t2 = st.tabs(
        [
            "Property Register",
            "Register Property"
        ]
    )

    with t1:

        x = df("""
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
            LEFT JOIN iddir_groups g ON p.group_id=g.id
            ORDER BY p.property_name
        """)

        st.dataframe(
            x,
            use_container_width=True,
            hide_index=True
        )

        download(
            x,
            "iddir_property_register.csv"
        )

        st.subheader(
            "Property Valuation Summary"
        )

        if not x.empty:

            total_cost = x["Acquisition_Cost"].sum()
            total_value = x["Current_Value"].sum()

            a, b, c = st.columns(3)

            a.metric(
                "Acquisition Cost",
                money(total_cost)
            )

            b.metric(
                "Current Value",
                money(total_value)
            )

            c.metric(
                "Change in Value",
                money(total_value - total_cost)
            )

    with t2:

        if not groups:
            st.info(
                "Create an Iddir group first."
            )
            return

        gl = [
            f"{g['group_code']} | {g['group_name']}"
            for g in groups
        ]

        with st.form("property_form"):

            a, b = st.columns(2)

            group_label = a.selectbox(
                "Iddir Group",
                gl
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
                    "Other"
                ]
            )

            property_name = a.text_input(
                "Property Name"
            )

            description = b.text_area(
                "Description"
            )

            acquisition_date = a.date_input(
                "Acquisition Date",
                date.today()
            )

            acquisition_cost = b.number_input(
                "Acquisition Cost (ETB)",
                0.0,
                step=100.0
            )

            current_value = a.number_input(
                "Current Value (ETB)",
                0.0,
                step=100.0
            )

            quantity = b.number_input(
                "Quantity",
                0.01,
                step=1.0,
                value=1.0
            )

            condition = a.selectbox(
                "Condition",
                [
                    "Excellent",
                    "Good",
                    "Fair",
                    "Needs Repair",
                    "Unusable"
                ]
            )

            ownership = b.selectbox(
                "Ownership",
                [
                    "Community",
                    "Group",
                    "Joint",
                    "Other"
                ]
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
                use_container_width=True
            )

        if submitted:

            group = groups[
                gl.index(group_label)
            ]

            sql(
                """INSERT INTO properties
                (group_id,property_type,property_name,
                 description,acquisition_date,
                 acquisition_cost,current_value,quantity,
                 condition_status,ownership_status,
                 location,responsible_person,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
                    now()
                )
            )

            audit(
                "Registered community property",
                "Iddir",
                property_name
            )

            st.success(
                "Property registered."
            )
            st.rerun()


# =========================================================
# PROPERTY ANALYTICS
# =========================================================

def property_analytics():
    header(
        "Module 9: Property Analytics",
        "Mathematical and statistical monitoring of community assets."
    )

    x = df("""
        SELECT
            property_type Type,
            SUM(quantity) Quantity,
            SUM(acquisition_cost * quantity) Acquisition_Cost,
            SUM(current_value * quantity) Current_Value
        FROM properties
        GROUP BY property_type
        ORDER BY Current_Value DESC
    """)

    if x.empty:
        st.info(
            "No properties have been registered."
        )
        return

    x["Value_Change"] = (
        x["Current_Value"] - x["Acquisition_Cost"]
    )

    x["Value_Change_Percent"] = np.where(
        x["Acquisition_Cost"] > 0,
        x["Value_Change"] / x["Acquisition_Cost"] * 100,
        0
    )

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Straight-Line Depreciation Demonstration"
    )

    props = sql(
        "SELECT * FROM properties ORDER BY property_name",
        fetch=True
    )

    if props:

        labels = [
            f"{p['id']} | {p['property_name']}"
            for p in props
        ]

        selected = st.selectbox(
            "Select Property",
            labels
        )

        p = props[labels.index(selected)]

        a, b = st.columns(2)

        salvage = a.number_input(
            "Estimated Salvage Value (ETB)",
            0.0,
            value=min(
                float(p["current_value"]),
                float(p["acquisition_cost"])
            ),
            step=100.0
        )

        life = b.number_input(
            "Useful Life (Years)",
            1,
            100,
            10,
            step=1
        )

        years = a.number_input(
            "Years Elapsed",
            0.0,
            float(life),
            1.0,
            step=1.0
        )

        annual, book = property_depreciation(
            float(p["acquisition_cost"]),
            salvage,
            life,
            years
        )

        b.metric(
            "Annual Depreciation",
            money(annual)
        )

        a.metric(
            "Estimated Book Value",
            money(book)
        )

    st.markdown("""
    <div class="section-card">
    <b>Prototype asset model.</b><br>
    Straight-line depreciation treats annual depreciation as the
    depreciable amount divided by useful life. The model is intended
    for prototype management and should be adapted to the applicable
    accounting policy before operational financial reporting.
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# FUND SUSTAINABILITY
# =========================================================

def fund_page():
    header(
        "Module 10: Fund Sustainability",
        "Statistical monitoring of contributions, benefits and cumulative community funds."
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
        hide_index=True
    )

    a, b, c = st.columns(3)

    a.metric(
        "Total Contributions",
        money(x["Contributions"].sum())
    )

    b.metric(
        "Total Benefits",
        money(x["Benefits"].sum())
    )

    c.metric(
        "Net Fund Change",
        money(x["Net_Fund_Change"].sum())
    )

    st.line_chart(
        x.set_index("Date")[
            ["Cumulative_Fund"]
        ]
    )

    st.markdown("""
    <div class="section-card">
    <b>Fund-balance model:</b>
    F(t+1) = F(t) + C(t) + O(t) − B(t) − A(t),
    where F is the fund balance, C is member contribution,
    O is other income, B is benefit expenditure and A is
    administrative expenditure. The present prototype records
    contributions and benefits; additional income and expenditure
    streams can be incorporated in future versions.
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# STATISTICAL ELIGIBILITY MODEL
# =========================================================

def statistical_model_page():
    header(
        "Module 11: Statistical Models",
        "Transparent mathematical/statistical models for Iddir management."
    )

    st.markdown("""
    <div class="section-card">
    The models below are prototype analytical tools rather than
    automatic legal or humanitarian decisions. Their purpose is to
    demonstrate how Iddir administrative records can be transformed
    into measurable indicators for planning, monitoring and research.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(
        [
            "Benefit Eligibility Score",
            "Fund Sustainability",
            "Contribution Risk"
        ]
    )

    with tab1:

        st.markdown("""
        ### Weighted member-support score

        A prototype eligibility index can be defined as

        **Eᵢ = w₁Cᵢ + w₂Pᵢ + w₃Tᵢ + w₄Mᵢ**

        where contribution level, payment consistency, trust and
        membership duration are normalized to comparable scales.
        """)

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
                "Eligibility_Score"
            ]:
                display[col] = display[col].map(
                    lambda z: f"{z:.2%}"
                )

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

            download(
                display,
                "iddir_eligibility_scores.csv"
            )

    with tab2:

        st.markdown("""
        ### Community fund sustainability

        The operational balance can be represented by

        **Fₜ₊₁ = Fₜ + Cₜ + Oₜ − Bₜ − Aₜ**

        This permits monthly or event-based monitoring of whether
        accumulated contributions are keeping pace with community
        support obligations.
        """)

        x = fund_sustainability_model()

        if not x.empty:
            st.dataframe(
                x,
                use_container_width=True,
                hide_index=True
            )
            st.line_chart(
                x.set_index("Date")[
                    ["Contributions", "Benefits", "Cumulative_Fund"]
                ]
            )
        else:
            st.info(
                "Insufficient records for the demonstration."
            )

    with tab3:

        st.markdown("""
        ### Contribution-risk indicator

        A simple operational risk indicator may be expressed as

        **Rᵢ = 1 − Pᵢ**

        where Pᵢ is the observed payment-consistency rate.

        Higher Rᵢ indicates a greater need for administrative follow-up,
        not a conclusion about the member's character or eligibility.
        """)

        ms = members()

        if ms:

            rows = []

            for m in ms:

                h = df(
                    """SELECT status
                    FROM contributions
                    WHERE member_id=? AND module='Iddir'""",
                    (m["id"],)
                )

                if h.empty:
                    consistency = 0
                else:
                    consistency = (
                        (h["status"] == "Paid").mean()
                    )

                rows.append({
                    "Member_No": m["member_no"],
                    "Member": m["full_name"],
                    "Payment_Consistency": consistency,
                    "Contribution_Risk": 1 - consistency
                })

            x = pd.DataFrame(rows)

            x["Payment_Consistency"] = x[
                "Payment_Consistency"
            ].map(lambda z: f"{z:.2%}")

            x["Contribution_Risk"] = x[
                "Contribution_Risk"
            ].map(lambda z: f"{z:.2%}")

            st.dataframe(
                x,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# TRANSACTIONS
# =========================================================

def transactions():
    header(
        "Module 12: Financial Transactions",
        "Iddir financial transaction recording and reconciliation."
    )

    bl = branches()
    groups = sql(
        "SELECT * FROM iddir_groups ORDER BY group_name",
        fetch=True
    )

    branch_options = [
        f"{z['code']} | {z['name']}"
        for z in bl
    ]

    group_options = [
        f"{z['group_code']} | {z['group_name']}"
        for z in groups
    ]

    with st.form("transaction_form"):

        a, b = st.columns(2)

        branch_label = a.selectbox(
            "Branch",
            branch_options or ["No branch"]
        )

        group_label = b.selectbox(
            "Iddir Group",
            group_options or ["No group"]
        )

        transaction_type = a.selectbox(
            "Transaction Type",
            [
                "Contribution",
                "Benefit Payment",
                "Property Purchase",
                "Property Sale",
                "Donation",
                "Administrative Expense",
                "Adjustment",
                "Other"
            ]
        )

        amount = b.number_input(
            "Amount (ETB)",
            0.0,
            step=100.0
        )

        reference = a.text_input(
            "Reference"
        )

        transaction_date = b.date_input(
            "Transaction Date",
            date.today()
        )

        description = st.text_area(
            "Description"
        )

        submitted = st.form_submit_button(
            "Record Transaction",
            type="primary",
            use_container_width=True
        )

    if submitted:

        branch_id = None
        group_id = None

        if branch_label != "No branch":
            branch_id = bl[
                branch_options.index(branch_label)
            ]["id"]

        if group_label != "No group":
            group_id = groups[
                group_options.index(group_label)
            ]["id"]

        sql(
            """INSERT INTO transactions
            (module,branch_id,group_id,
             transaction_type,amount,reference,
             transaction_date,description,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                "Iddir",
                branch_id,
                group_id,
                transaction_type,
                amount,
                reference,
                str(transaction_date),
                description,
                now()
            )
        )

        audit(
            "Recorded financial transaction",
            "Iddir",
            f"{transaction_type}: {amount}"
        )

        st.success(
            "Transaction recorded."
        )
        st.rerun()

    x = df("""
        SELECT
            t.transaction_date Date,
            b.code Branch,
            g.group_code Group_Code,
            t.transaction_type Type,
            t.amount Amount,
            t.reference Reference,
            t.description Description
        FROM transactions t
        LEFT JOIN branches b ON t.branch_id=b.id
        LEFT JOIN iddir_groups g ON t.group_id=g.id
        WHERE t.module='Iddir'
        ORDER BY t.id DESC
    """)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    download(
        x,
        "iddir_transactions.csv"
    )


# =========================================================
# REPORTS
# =========================================================

def reports():
    header(
        "Module 13: Reports and Analytics",
        "Management information for Iddir operations."
    )

    report = st.selectbox(
        "Report",
        [
            "Module Summary",
            "Members",
            "Iddir Groups",
            "Contributions",
            "Benefits",
            "Community Events",
            "Properties",
            "Transactions",
            "Statistical Eligibility"
        ]
    )

    queries = {

        "Module Summary": """
            SELECT
                'Iddir' Module,
                COUNT(*) Members,
                ROUND(AVG(regular_contribution),2)
                    Average_Planned_Contribution,
                ROUND(AVG(trust_score),3)
                    Average_Trust
            FROM members
            WHERE module='Iddir'
            AND status='Active'
        """,

        "Members": """
            SELECT
                m.member_no Member_No,
                m.full_name Full_Name,
                m.household_no Household_No,
                b.code Branch,
                m.regular_contribution Planned_Contribution,
                m.contribution_frequency Frequency,
                m.trust_score Trust_Score,
                m.status Status
            FROM members m
            LEFT JOIN branches b ON m.branch_id=b.id
            WHERE m.module='Iddir'
            ORDER BY m.full_name
        """,

        "Iddir Groups": """
            SELECT
                group_code Group_Code,
                group_name Group_Name,
                contribution_amount Contribution,
                contribution_frequency Frequency,
                member_capacity Capacity,
                emergency_fund Emergency_Fund,
                property_value Property_Value,
                status Status
            FROM iddir_groups
            ORDER BY group_name
        """,

        "Contributions": """
            SELECT
                c.contribution_date Date,
                g.group_code Group_Code,
                m.member_no Member_No,
                m.full_name Member,
                c.amount Amount,
                c.status Status,
                c.reference Reference
            FROM contributions c
            JOIN members m ON c.member_id=m.id
            LEFT JOIN iddir_groups g ON c.group_id=g.id
            WHERE c.module='Iddir'
            ORDER BY c.id DESC
        """,

        "Benefits": """
            SELECT
                b.event_date Event_Date,
                g.group_code Group_Code,
                m.member_no Member_No,
                m.full_name Beneficiary,
                b.benefit_type Benefit_Type,
                b.approved_amount Approved,
                b.paid_amount Paid,
                b.status Status
            FROM benefits b
            JOIN members m ON b.member_id=m.id
            LEFT JOIN iddir_groups g ON b.group_id=g.id
            ORDER BY b.id DESC
        """,

        "Community Events": """
            SELECT
                e.event_date Date,
                g.group_code Group_Code,
                e.event_type Event_Type,
                e.household_count Participants,
                e.estimated_cost Estimated_Cost,
                e.actual_cost Actual_Cost,
                e.status Status
            FROM events e
            LEFT JOIN iddir_groups g ON e.group_id=g.id
            ORDER BY e.id DESC
        """,

        "Properties": """
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
            LEFT JOIN iddir_groups g ON p.group_id=g.id
            ORDER BY p.property_name
        """,

        "Transactions": """
            SELECT
                transaction_date Date,
                transaction_type Type,
                amount Amount,
                reference Reference,
                description Description
            FROM transactions
            WHERE module='Iddir'
            ORDER BY id DESC
        """
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
        hide_index=True
    )

    download(
        x,
        "iddir_report.csv"
    )


# =========================================================
# MANUALS
# =========================================================

def manuals():
    header(
        "Module 14: Manuals",
        "Operational guidance for the Iddir management prototype."
    )

    manuals_data = [

        (
            "Iddir Operating Manual",
            "Register branches, groups and members; establish contribution "
            "rules; record payments; manage support requests; administer "
            "community events; maintain property records; and reconcile "
            "financial transactions."
        ),

        (
            "Community Support Management",
            "Support requests should be documented with the event, beneficiary, "
            "approval status, approved amount, paid amount and reference. "
            "The software provides administrative traceability rather than "
            "replacing the community's governing rules."
        ),

        (
            "Property Management",
            "Community property can be registered with acquisition cost, "
            "current value, quantity, condition, ownership and responsible "
            "person. The property module also supports prototype valuation "
            "and depreciation analysis."
        ),

        (
            "Statistical Management",
            "The system demonstrates weighted contribution consistency, trust "
            "and membership indicators as measurable variables. These models "
            "are intended for research, planning and monitoring and should "
            "be validated before operational decision-making."
        ),

        (
            "Audit and Financial Controls",
            "Important activities should be recorded in the audit trail. "
            "Transaction references and reconciliation procedures should "
            "be maintained to support accountability."
        )
    ]

    for title, text in manuals_data:

        st.markdown(
            f"""
            <div class="manual-card">
                <h2>{title}</h2>
                <p>{text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# AUDIT
# =========================================================

def audit_page():
    header(
        "Module 15: Audit Trail",
        "Traceable record of important Iddir system activities."
    )

    x = df("""
        SELECT
            timestamp Timestamp,
            username Username,
            module Module,
            action Action,
            details Details
        FROM audit_log
        ORDER BY id DESC
        LIMIT 2000
    """)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    download(
        x,
        "iddir_audit.csv"
    )


# =========================================================
# USER ADMINISTRATION
# =========================================================

def users_page():
    header(
        "Module 16: User Administration",
        "Role-based access management for the Iddir prototype."
    )

    x = df("""
        SELECT
            username Username,
            full_name Full_Name,
            role Role,
            module Module,
            active Active,
            created_at Created_At
        FROM users
        ORDER BY username
    """)

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True
    )

    bl = branches()
    options = [
        f"{z['code']} | {z['name']}"
        for z in bl
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
            type="password"
        )

        role = b.selectbox(
            "Role",
            ROLES
        )

        module = a.selectbox(
            "Module",
            ["Portal", "Iddir"]
        )

        branch = b.selectbox(
            "Branch",
            ["No branch"] + options
        )

        submitted = st.form_submit_button(
            "Create User",
            type="primary",
            use_container_width=True
        )

    if submitted:

        branch_id = None

        if branch != "No branch":
            branch_id = bl[
                options.index(branch)
            ]["id"]

        try:

            sql(
                """INSERT INTO users
                (username,password_hash,full_name,
                 role,module,branch_id,active,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    username,
                    pwd_hash(password),
                    full_name,
                    role,
                    module,
                    branch_id,
                    1,
                    now()
                )
            )

            audit(
                "Created user",
                "Portal",
                username
            )

            st.success(
                "User created."
            )
            st.rerun()

        except sqlite3.IntegrityError:
            st.error(
                "Username already exists."
            )


# =========================================================
# MAIN APPLICATION
# =========================================================

def main():

    init_db()

    if not st.session_state.get(
        "authenticated"
    ):
        login()
        return

    with st.sidebar:

        st.markdown("## Iddir")

        st.caption(
            "Iddir App Management System"
        )

        st.write(
            f"User: **{st.session_state.get('full_name','')}**"
        )

        st.write(
            f"Role: **{st.session_state.get('role','')}**"
        )

        if st.button(
            "Sign out",
            use_container_width=True
        ):

            audit(
                "Logout"
            )

            st.session_state.clear()
            st.rerun()

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
            "Audit Trail"
        ]

        if st.session_state.get(
            "role"
        ) == "Administrator":

            navigation.append(
                "User Administration"
            )

        page = st.radio(
            "Navigation",
            navigation
        )

    pages = {

        "Dashboard": dashboard,
        "Branch Management": branch_page,
        "Member Management": member_page,
        "Iddir Groups": group_page,
        "Contributions": contribution_page,
        "Benefits and Mutual Support": benefits_page,
        "Community Events": events_page,
        "Property Management": property_page,
        "Property Analytics": property_analytics,
        "Fund Sustainability": fund_page,
        "Statistical Models": statistical_model_page,
        "Financial Transactions": transactions,
        "Reports and Analytics": reports,
        "Manuals": manuals,
        "Audit Trail": audit_page,
        "User Administration": users_page
    }

    pages[page]()


if __name__ == "__main__":
    main()
