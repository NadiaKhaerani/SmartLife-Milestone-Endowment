# ==================================================
# IMPORTS
# ==================================================

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="SmartLife Milestone Endowment",
    page_icon="Logo FutureShield.png",
    layout="wide"
)

# ==================================================
# PROFESSIONAL UI STYLING
# ==================================================

st.markdown("""
<style>

/* ==================================================
BACKGROUND
================================================== */

.stApp{
    background:
    linear-gradient(
        180deg,
        #dff4ff 0%,
        #edf8ff 45%,
        #ffffff 100%
    );
}

/* ==================================================
GLOBAL SPACING
================================================== */

.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
    padding-left:2rem;
    padding-right:2rem;
}

/* ==================================================
SIDEBAR
================================================== */

section[data-testid="stSidebar"]{

    background:
    linear-gradient(
        180deg,
        #87CEFA 0%,
        #dff3ff 100%
    );

    border-right:
    1px solid #d8edf9;
}

/* ==================================================
HERO CARD
================================================== */

.hero-card{

    background:
    rgba(255,255,255,0.88);

    border-radius:34px;

    padding:42px;

    border:
    1px solid rgba(
        255,255,255,0.95
    );

    backdrop-filter:
    blur(16px);

    box-shadow:
    0 18px 50px
    rgba(0,0,0,0.08);
}

/* ==================================================
TITLE
================================================== */

.hero-title{

    font-size:50px;
    font-weight:800;
    color:#0b4f7d;

    margin-bottom:10px;
}

/* ==================================================
SUBTITLE
================================================== */

.hero-sub{

    color:#6484a1;
    font-size:20px;
    line-height:1.7;
}

/* ==================================================
SECTION TITLE
================================================== */

.section-title{

    font-size:28px;
    font-weight:700;
    color:#0b4f7d;

    margin-top:20px;
    margin-bottom:10px;
}

/* ==================================================
METRIC CARD
================================================== */

.metric-card{

    background:
    rgba(255,255,255,0.92);

    border-radius:28px;

    padding:28px;

    text-align:center;

    border:
    1px solid #d9eefc;

    box-shadow:
    0 10px 30px
    rgba(79,145,199,0.15);
}

.metric-title{

    color:#6f8ea7;
    font-size:16px;
    font-weight:600;
}

.metric-value{

    color:#0b4f7d;
    font-size:34px;
    font-weight:800;
}

/* ==================================================
FOOTER
================================================== */

.footer{

    text-align:center;
    color:#8198ab;
    margin-top:60px;
    font-size:14px;
}

</style>
""",
unsafe_allow_html=True)

# ==================================================
# HERO SECTION (UPGRADED)
# ==================================================

st.markdown("""
<div class="hero-card">

<div class="hero-title">
SmartLife Milestone Endowment
</div>

<div class="hero-sub">
Advanced actuarial pricing engine with mortality modeling,
multiple decrement, milestone benefits, premium calculation,
and prospective reserve projection.
</div>

</div>
""", unsafe_allow_html=True)

st.write("")

# ==================================================
# LOAD MORTALITY TABLE
# ==================================================

try:

    df = pd.read_excel(
        "Mortality_Rate_Table.xlsx",
        engine="openpyxl"
    )

except Exception as e:

    st.error(
        f"""
        Failed to load
        Mortality_Rate_Table.xlsx

        Error:
        {e}
        """
    )

    st.stop()

# ==================================================
# CLEAN COLUMN NAMES
# ==================================================

df.columns = (
    df.columns
    .str.strip()
)

rename_dict = {}

if "Age" in df.columns:
    rename_dict["Age"] = "Age"

if "Male" in df.columns:
    rename_dict["Male"] = "Male"

if "Female" in df.columns:
    rename_dict["Female"] = "Female"

df = df.rename(
    columns=rename_dict
)

# ==================================================
# VALIDATION
# ==================================================

required_cols = [

    "Age",
    "Male",
    "Female"

]

missing_cols = [

    col for col
    in required_cols
    if col not in df.columns

]

if len(missing_cols) > 0:

    st.error(
        f"""
        Missing mortality columns:

        {missing_cols}

        Required columns:
        Age / Male / Female
        """
    )

    st.stop()

# ==================================================
# GLOBAL ACTUARIAL ASSUMPTIONS
# ==================================================

TERMINAL_AGE = int(
    df["Age"].max()
)

EXPENSE_LOADING = 0.08
RISK_MARGIN = 0.05

# ==================================================
# QX LOOKUP FUNCTION
# ==================================================

def get_qx(
    age,
    gender
):

    age = int(age)

    if gender.lower() == "male":

        column = (
            "Male"
        )

    else:

        column = (
            "Female"
        )

    row = df.loc[
        df["Age"] == age,
        column
    ]

    if row.empty:

        return 0.999999

    qx = float(
        row.values[0]
    )

    qx = min(
        max(
            qx,
            0.000001
        ),
        0.999999
    )

    return qx

# ==================================================
# LAPSE RATE FUNCTION
# ==================================================

def get_lapse_rate(
    policy_year
):

    if policy_year <= 5:

        return lapse_1_5

    elif policy_year <= 10:

        return lapse_6_10

    else:

        return lapse_11_plus

# ==================================================
# SURVIVAL PROBABILITY
# MULTIPLE DECREMENT
# ==================================================

def survival_probability(
    age,
    gender,
    t
):

    survival = 1.0

    for k in range(int(t)):

        mortality = get_qx(
            age + k,
            gender
        )

        lapse = (
            get_lapse_rate(
                k + 1
            )
        )

        total_exit = min(

            mortality
            + lapse,

            0.999999
        )

        survival *= (
            1
            - total_exit
        )

    return survival

# ==================================================
# DECREMENT PROJECTION TABLE
# ==================================================

def decrement_projection(
    age,
    gender,
    term
):

    rows = []

    survival = 1.0

    for t in range(
        1,
        term + 1
    ):

        mortality = get_qx(
            age + t - 1,
            gender
        )

        lapse = (
            get_lapse_rate(t)
        )

        total_exit = min(

            mortality
            + lapse,

            0.999999
        )

        rows.append([

            t,
            mortality,
            lapse,
            total_exit,
            survival

        ])

        survival *= (
            1
            - total_exit
        )

    return pd.DataFrame(

        rows,

        columns=[

            "Policy Year",
            "Mortality (qx)",
            "Lapse Rate",
            "Total Exit",
            "Survival Probability"
        ]
    )
# ==================================================
# SIDEBAR
# POLICY INPUTS
# ==================================================

st.sidebar.title(
    "Policy Inputs"
)

# -----------------------------
# AGE
# -----------------------------

age = st.sidebar.selectbox(
    "Age",
    list(range(18, 101)),
    index=17
)

# -----------------------------
# GENDER
# -----------------------------

gender = st.sidebar.selectbox(
    "Gender",
    [
        "male",
        "female"
    ]
)

# -----------------------------
# INTEREST RATE
# -----------------------------

interest_input = (
    st.sidebar.number_input(
        "Interest Rate (%)",
        min_value=0.00,
        max_value=20.00,
        value=5.50,
        step=0.10
    )
)

interest = (
    interest_input / 100
)

# -----------------------------
# SUM ASSURED
# -----------------------------

benefit = st.sidebar.number_input(
    "Sum Assured",
    min_value=1000000,
    value=500000000,
    step=1000000
)

# -----------------------------
# POLICY TERM
# KEEP 4 OPTIONS
# -----------------------------

term = st.sidebar.selectbox(
    "Policy Term",
    [
        5,
        10,
        15,
        20
    ],
    index=3
)

# -----------------------------
# PAYMENT FREQUENCY
# -----------------------------

payment_frequency = (
    st.sidebar.selectbox(
        "Payment Frequency",
        [
            "Annual",
            "Semi-Annual",
            "Quarterly",
            "Monthly"
        ]
    )
)

# ==================================================
# MILESTONE SETTINGS
# ==================================================

st.sidebar.markdown("---")

st.sidebar.subheader(
    "Milestone Settings"
)

milestone_5_pct = (
    st.sidebar.slider(
        "Year 5 (%)",
        min_value=0.0,
        max_value=50.0,
        value=20.0,
        step=1.0
    )
)

milestone_10_pct = (
    st.sidebar.slider(
        "Year 10 (%)",
        min_value=0.0,
        max_value=50.0,
        value=15.0,
        step=1.0
    )
)

milestone_15_pct = (
    st.sidebar.slider(
        "Year 15 (%)",
        min_value=0.0,
        max_value=50.0,
        value=10.0,
        step=1.0
    )
)

maturity_pct = (
    st.sidebar.slider(
        "Maturity (%)",
        min_value=0.0,
        max_value=150.0,
        value=55.0,
        step=1.0
    )
)   

# -----------------------------
# CONVERT TO DECIMAL
# -----------------------------

milestone_5 = (
    milestone_5_pct / 100
)

milestone_10 = (
    milestone_10_pct / 100
)

milestone_15 = (
    milestone_15_pct / 100
)

maturity = (
    maturity_pct / 100
)

# ==================================================
# MULTIPLE DECREMENT
# ==================================================

st.sidebar.markdown("---")

st.sidebar.subheader(
    "Multiple Decrement"
)

lapse_1_5_pct = (
    st.sidebar.slider(
        "Lapse Year 1–5 (%)",
        min_value=0.00,
        max_value=10.00,
        value=1.00,
        step=0.05
    )
)

lapse_6_10_pct = (
    st.sidebar.slider(
        "Lapse Year 6–10 (%)",
        min_value=0.00,
        max_value=5.00,
        value=0.50,
        step=0.05
    )
)

lapse_11_plus_pct = (
    st.sidebar.slider(
        "Lapse Year 11+ (%)",
        min_value=0.00,
        max_value=3.00,
        value=0.25,
        step=0.05
    )
)

# -----------------------------
# CONVERT TO DECIMAL
# -----------------------------

lapse_1_5 = (
    lapse_1_5_pct / 100
)

lapse_6_10 = (
    lapse_6_10_pct / 100
)

lapse_11_plus = (
    lapse_11_plus_pct / 100
)
calculate = st.sidebar.button("Calculate")

# ==================================================
# MILESTONE BENEFIT SCHEDULE
# ==================================================

def get_milestone_schedule(
    term,
    benefit,
    milestone_5,
    milestone_10,
    milestone_15,
    maturity
):

    schedule = []

    if term >= 5:

        schedule.append({

            "Policy Year": 5,
            "Benefit Type": "Milestone",
            "Percentage": milestone_5,
            "Benefit Amount":
            benefit * milestone_5
        })

    if term >= 10:

        schedule.append({

            "Policy Year": 10,
            "Benefit Type": "Milestone",
            "Percentage": milestone_10,
            "Benefit Amount":
            benefit * milestone_10
        })

    if term >= 15:

        schedule.append({

            "Policy Year": 15,
            "Benefit Type": "Milestone",
            "Percentage": milestone_15,
            "Benefit Amount":
            benefit * milestone_15
        })

    schedule.append({

        "Policy Year": term,
        "Benefit Type": "Maturity",
        "Percentage": maturity,
        "Benefit Amount":
        benefit * maturity
    })

    return pd.DataFrame(
        schedule
    )


# ==================================================
# GROSS PREMIUM
# ==================================================

def gross_up_premium(
    net_premium
):

    gross = (

        net_premium

        * (
            1
            + RISK_MARGIN
        )

    ) / (

        1
        - EXPENSE_LOADING
    )

    return gross

# ==================================================
# REDUCED DEATH BENEFIT
# OPTION 3
# ==================================================

def remaining_death_benefit(
    benefit,
    policy_year
):

    paid_milestone = 0

    if policy_year > 5:
        paid_milestone += (
            benefit * milestone_5
        )

    if policy_year > 10:
        paid_milestone += (
            benefit * milestone_10
        )

    if policy_year > 15:
        paid_milestone += (
            benefit * milestone_15
        )

    death_benefit = (
        benefit
        - paid_milestone
    )

    return max(
        death_benefit,
        0
    )


# ==================================================
# EXPECTED BENEFIT ENGINE
# ==================================================

def expected_benefit_endowment(
    age,
    gender,
    benefit,
    term,
    interest
):

    v = (
        1 / (
            1 + interest
        )
    )

    epv = 0.0

    # -----------------------------
    # DEATH BENEFIT
    # -----------------------------

    for t in range(term):

        survival = (
            survival_probability(
                age,
                gender,
                t
            )
        )

        qx = get_qx(
            age + t,
            gender
        )

        death_probability = (
            survival * qx
        )

        death_benefit = (
            remaining_death_benefit(
                benefit,
                t + 1
            )
        )
        
        epv += (

            (v ** (t + 1))

            * death_probability

            * death_benefit
        )

    # -----------------------------
    # MILESTONE BENEFITS
    # -----------------------------

    milestone_dict = {

        5: milestone_5,
        10: milestone_10,
        15: milestone_15
    }

    for year, pct in (
        milestone_dict.items()
    ):

        if term >= year:

            survival = (
                survival_probability(
                    age,
                    gender,
                    year
                )
            )

            milestone_amount = (
                benefit * pct
            )

            epv += (

                (v ** year)

                * survival

                * milestone_amount
            )

    # -----------------------------
    # MATURITY BENEFIT
    # -----------------------------

    survival_term = (
        survival_probability(
            age,
            gender,
            term
        )
    )

    maturity_amount = (
        benefit
        * maturity
    )

    epv += (

        (v ** term)

        * survival_term

        * maturity_amount
    )

    return epv

# ==================================================
# PREMIUM ENGINE
# ==================================================

def premium_endowment(
    age,
    gender,
    benefit,
    term,
    interest
):

    v = (
        1 / (
            1 + interest
        )
    )

    epv_benefit = (
        expected_benefit_endowment(
            age,
            gender,
            benefit,
            term,
            interest
        )
    )

    epv_premium = 0.0

    for t in range(term):

        survival = (
            survival_probability(
                age,
                gender,
                t
            )
        )

        epv_premium += (

            (v ** t)

            * survival
        )

    net_premium = (

        epv_benefit
        / epv_premium
    )

    gross_premium = (
        gross_up_premium(
            net_premium
        )
    )

    return gross_premium

# ==================================================
# PROSPECTIVE RESERVE ENGINE
# ==================================================

def reserve_projection(
    age,
    gender,
    benefit,
    term,
    interest,
    annual_premium
):

    rows = []

    v = (
        1 / (1 + interest)
    )

    for duration in range(
        term + 1
    ):

        pv_future_benefit = 0.0
        pv_future_premium = 0.0

        remaining_term = (
            term - duration
        )

        # --------------------------------
        # FUTURE DEATH BENEFIT
        # --------------------------------

        for t in range(
            remaining_term
        ):

            survival = (
                survival_probability(
                    age + duration,
                    gender,
                    t
                )
            )

            qx = get_qx(
                age + duration + t,
                gender
            )

            death_probability = (
                survival * qx
            )

            death_benefit = (
                remaining_death_benefit(
                    benefit,
                    duration + t + 1
                )
            )

            pv_future_benefit += (

                (v ** (t + 1))
                * death_probability
                * death_benefit
            )

        # --------------------------------
        # FUTURE MILESTONE BENEFITS
        # --------------------------------

        milestone_dict = {

            5: milestone_5,
            10: milestone_10,
            15: milestone_15
        }

        for year, pct in (
            milestone_dict.items()
        ):

            if duration < year <= term:

                time_to_payment = (
                    year - duration
                )

                survival = (
                    survival_probability(
                        age + duration,
                        gender,
                        time_to_payment
                    )
                )

                pv_future_benefit += (

                    (v ** time_to_payment)
                    * survival
                    * benefit
                    * pct
                )

        # --------------------------------
        # MATURITY BENEFIT
        # --------------------------------

        if duration < term:

            time_to_maturity = (
                term - duration
            )

            survival = (
                survival_probability(
                    age + duration,
                    gender,
                    time_to_maturity
                )
            )

            pv_future_benefit += (

                (v ** time_to_maturity)
                * survival
                * benefit
                * maturity
            )

        # --------------------------------
        # FUTURE PREMIUMS
        # --------------------------------

        for t in range(
            remaining_term
        ):

            survival = (
                survival_probability(
                    age + duration,
                    gender,
                    t
                )
            )

            pv_future_premium += (

                (v ** t)
                * survival
                * annual_premium
            )

        reserve = (

            pv_future_benefit
            - pv_future_premium
        )


        rows.append([

            duration,
            pv_future_benefit,
            pv_future_premium,
            reserve

        ])

    return pd.DataFrame(

        rows,

        columns=[

            "Policy Duration",
            "PV Future Benefit",
            "PV Future Premium",
            "Reserve"
        ]
    )

if calculate:

    # ==================================================
    # PRODUCT CALCULATION
    # ==================================================

    annual_premium = premium_endowment(
        age,
        gender,
        benefit,
        term,
        interest
    )

    expected_benefit = expected_benefit_endowment(
        age,
        gender,
        benefit,
        term,
        interest
    )

    survival_to_term = survival_probability(
        age,
        gender,
        term
    )

    decrement_df = decrement_projection(
        age,
        gender,
        term
    )

    benefit_schedule = get_milestone_schedule(
        term,
        benefit,
        milestone_5,
        milestone_10,
        milestone_15,
        maturity
    )

    reserve_df = reserve_projection(
        age,
        gender,
        benefit,
        term,
        interest,
        annual_premium
    )

    # ==================================================
    # DEATH BENEFIT SCHEDULE
    # ==================================================

    death_rows = []

    for yr in range(1, term + 1):

        death_rows.append({
            "Policy Year": yr,
            "Death Benefit":
            remaining_death_benefit(
                benefit,
                yr
            )
        })

    death_df = pd.DataFrame(
        death_rows
    )

    # =========================
    # PAYMENT FREQUENCY
    # =========================

    if payment_frequency == "Monthly":
        premium = annual_premium / 12
    elif payment_frequency == "Quarterly":
        premium = annual_premium / 4
    elif payment_frequency == "Semi-Annual":
        premium = annual_premium / 2
    else:
        premium = annual_premium

else:
    st.info(" Click the **Calculate** button to view results")
    st.stop()


# ==================================================
# KPI SECTION
# ==================================================

st.markdown("""
<div class="section-title">
SmartLife Dashboard
</div>
""",
unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

# ==================================================
# ACTUARIAL SUMMARY
# ==================================================

st.markdown("""
<div class="section-title">
Actuarial Summary
</div>
""",
unsafe_allow_html=True)

total_milestone_pct = (

    milestone_5
    + milestone_10
    + milestone_15
    + maturity
)

st.info(f"""

Policy Term: {term} years

Sum Assured:
Rp {benefit:,.0f}

Total Scheduled Benefit:
{total_milestone_pct:.0%}

Current Mortality (qx):
{get_qx(age, gender):.5f}

Expected Survival To Maturity:
{survival_to_term:.2%}

""")

# -----------------------------
# PREMIUM
# -----------------------------

with col1:

    st.markdown(f"""
    <div class="metric-card">

    <div class="metric-title">
    Premium ({payment_frequency})
    </div>

    <div class="metric-value">
    Rp {premium:,.0f}
    </div>

    </div>
    """,
    unsafe_allow_html=True)

# -----------------------------
# EXPECTED BENEFIT
# -----------------------------

with col2:

    st.markdown(f"""
    <div class="metric-card">

    <div class="metric-title">
    Expected Benefit
    </div>

    <div class="metric-value">
    Rp {expected_benefit:,.0f}
    </div>

    </div>
    """,
    unsafe_allow_html=True)

# -----------------------------
# SURVIVAL
# -----------------------------

with col3:

    st.markdown(f"""
    <div class="metric-card">

    <div class="metric-title">
    Survival To Maturity
    </div>

    <div class="metric-value">
    {survival_to_term:.2%}
    </div>

    </div>
    """,
    unsafe_allow_html=True)

# ==================================================
# MULTIPLE DECREMENT TABLE
# ==================================================

st.markdown("""
<div class="section-title">
Multiple Decrement Table
</div>
""",
unsafe_allow_html=True)

decrement_display = (
    decrement_df.copy()
)

for col in [

    "Mortality (qx)",
    "Lapse Rate",
    "Total Exit",
    "Survival Probability"

]:

    decrement_display[col] = (

        decrement_display[col]

        .apply(
            lambda x:
            f"{x:.5f}"
        )
    )

st.dataframe(
    decrement_display,
    use_container_width=True,
    height=350
)

# ==================================================
# BENEFIT SCHEDULE TABLE
# ==================================================

st.markdown("""
<div class="section-title">
Milestone Benefit Schedule
</div>
""",
unsafe_allow_html=True)

benefit_display = (
    benefit_schedule.copy()
)

benefit_display[
    "Percentage"
] = (

    benefit_display[
        "Percentage"
    ]

    .apply(
        lambda x:
        f"{x:.0%}"
    )
)

benefit_display[
    "Benefit Amount"
] = (

    benefit_display[
        "Benefit Amount"
    ]

    .apply(
        lambda x:
        f"Rp {x:,.0f}"
    )
)

st.dataframe(
    benefit_display,
    use_container_width=True,
    height=220
)

# ==================================================
# DEATH BENEFIT TABLE
# ==================================================

st.markdown("""
<div class="section-title">
Death Benefit Schedule
</div>
""",
unsafe_allow_html=True)

death_display = death_df.copy()

death_display["Death Benefit"] = (
    death_display["Death Benefit"]
    .apply(
        lambda x:
        f"Rp {x:,.0f}"
    )
)

st.dataframe(
    death_display,
    use_container_width=True,
    height=300
)

# ==================================================
# RESERVE TABLE
# ==================================================

st.markdown("""
<div class="section-title">
Reserve Projection
</div>
""",
unsafe_allow_html=True)

reserve_display = (
    reserve_df.copy()
)

for col in [

    "PV Future Benefit",
    "PV Future Premium",
    "Reserve"

]:

    reserve_display[col] = (

        reserve_display[col]

        .apply(
            lambda x:
            f"Rp {x:,.0f}"
        )
    )

st.dataframe(
    reserve_display,
    use_container_width=True,
    height=350
)

# ==================================================
# RESERVE GRAPH
# ==================================================

st.markdown("""
<div class="section-title">
Reserve Trend
</div>
""",
unsafe_allow_html=True)

fig, ax = plt.subplots(
    figsize=(10,5)
)

ax.plot(

    reserve_df[
        "Policy Duration"
    ],

    reserve_df[
        "Reserve"
    ],

    marker="o"
)

ax.set_xlabel(
    "Policy Duration"
)

ax.set_ylabel(
    "Reserve"
)

ax.set_title(
    "Prospective Reserve Projection"
)

ax.grid(True)

ax.yaxis.set_major_formatter(

    FuncFormatter(
        lambda x, p:
        f"Rp {x:,.0f}"
    )
)

plt.tight_layout()

st.pyplot(fig)

# ==================================================
# MORTALITY TABLE
# ==================================================

with st.expander(
    "Mortality Table"
):

    mortality_display = (
        df.copy()
    )

    mortality_display[
        "Age"
    ] = (
        mortality_display[
            "Age"
        ]
        .astype(int)
    )

    for col in [

        "Male",
        "Female"

    ]:

        mortality_display[
            col
        ] = (

            mortality_display[
                col
            ]

            .apply(
                lambda x:
                f"{x:.5f}"
            )
        )

    st.dataframe(
        mortality_display,
        use_container_width=True,
        height=450
    )

# ==================================================
# FOOTER
# ==================================================

st.markdown("""
<div class="footer">

SmartLife Milestone Endowment © 2026

Commercial Actuarial Pricing Dashboard

</div>
""",
unsafe_allow_html=True)