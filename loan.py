import streamlit as st
import pandas as pd
import plotly.express as px

# Page Setup
st.set_page_config(
    page_title="Loan & Credit Card Payment Simulator",
    page_icon="💳",
    layout="wide"
)

st.title("💳 Loan & Credit Card Repayment Simulator")
st.markdown("""
Explore how different repayment strategies (**On-time**, **Early**, or **Late**) affect total interest, payoff duration, and overall borrowing costs[cite: 1].
""")

# 1. USER INPUT SECTION (SIDEBAR)
st.sidebar.header("📊 Input Parameters")

# Example Scenarios from Assignment Briefing
scenario = st.sidebar.selectbox(
    "Select Example Scenario",
    [
        "Custom", 
        "🏠 Buying a house with a 20-year mortgage", 
        "🚗 Buying a car with a 5-year loan", 
        "💳 Paying off a credit card over time"
    ]
)

# Preset Default Value Mapping (in RM)
if scenario == "🏠 Buying a house with a 20-year mortgage":
    def_principal, def_rate, def_term, def_pmt = 300000.0, 4.20, 240, 0.0
elif scenario == "🚗 Buying a car with a 5-year loan":
    def_principal, def_rate, def_term, def_pmt = 60000.0, 3.50, 60, 0.0
elif scenario == "💳 Paying off a credit card over time":
    def_principal, def_rate, def_term, def_pmt = 5000.0, 18.00, 24, 0.0
else:
    def_principal, def_rate, def_term, def_pmt = 10000.0, 5.00, 36, 0.0

# Number Inputs using Streamlit
principal = st.sidebar.number_input(
    "Loan / Balance Amount (RM)", 
    min_value=100.0, 
    value=def_principal, 
    step=1000.0
)
annual_rate = st.sidebar.number_input(
    "Annual Interest Rate (%)", 
    min_value=0.0, 
    max_value=36.0, 
    value=def_rate, 
    step=0.1
)
term_months = int(st.sidebar.number_input(
    "Loan Term (Months)", 
    min_value=1, 
    max_value=420, 
    value=def_term, 
    step=12
))
user_monthly_payment = st.sidebar.number_input(
    "Monthly Payment (RM) [0 to auto-calculate standard payment]", 
    min_value=0.0, 
    value=def_pmt, 
    step=50.0
)

st.sidebar.markdown("---")
behavior = st.sidebar.radio(
    "Repayment Behavior Strategy",
    ["On-time", "Early (Pay Extra)", "Late (Underpay / Miss)"]
)

# Behavior Parameters
extra_payment = 0.0
underpayment = 0.0
late_fee = 0.0

if behavior == "Early (Pay Extra)":
    extra_payment = st.sidebar.number_input(
        "Extra Monthly Payment (RM)", 
        min_value=0.0, 
        value=100.0, 
        step=20.0
    )
elif behavior == "Late (Underpay / Miss)":
    underpayment = st.sidebar.number_input(
        "Monthly Underpaid Amount (RM)", 
        min_value=0.0, 
        value=50.0, 
        step=10.0
    )
    late_fee = st.sidebar.number_input(
        "Late Payment Fee (RM)", 
        min_value=0.0, 
        value=30.0, 
        step=5.0
    )

def simulate_schedule(p: float, rate: float, term: int, user_pmt: float, p_behavior: str, extra: float = 0.0, under: float = 0.0, fee: float = 0.0):
    monthly_rate = (rate / 100) / 12
    
    # Standard Amortization Formula
    if user_pmt <= 0:
        if monthly_rate > 0:
            scheduled_pmt = p * (monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
        else:
            scheduled_pmt = p / term
    else:
        scheduled_pmt = user_pmt

    balance = p
    total_interest = 0.0
    schedule = []
    month = 0
    max_months = max(term * 4, 360)  # Safety iteration limit

    while balance > 0.01 and month < max_months:
        month += 1
        interest_month = balance * monthly_rate
        
        # Calculate target payment based on repayment behavior
        if p_behavior == "Early (Pay Extra)":
            payment_target = scheduled_pmt + extra
        elif p_behavior == "Late (Underpay / Miss)":
            payment_target = max(0.0, scheduled_pmt - under) + fee
        else:
            payment_target = scheduled_pmt

        # Cap payment to final remaining balance + accrued interest
        actual_payment = min(payment_target, balance + interest_month)
        principal_paid = actual_payment - interest_month
        
        # Handle underpayment / negative amortization
        if principal_paid < 0:
            balance += abs(principal_paid)
        else:
            balance -= principal_paid
            
        total_interest += interest_month
        
        schedule.append({
            "Month": month,
            "Payment (RM)": round(actual_payment, 2),
            "Principal Paid (RM)": round(max(0.0, principal_paid), 2),
            "Interest Paid (RM)": round(interest_month, 2),
            "Remaining Balance (RM)": round(max(0.0, balance), 2)
        })

    return pd.DataFrame(schedule), scheduled_pmt, total_interest, month


# Calculation
df_selected, base_pmt, total_interest_sel, payoff_months_sel = simulate_schedule(
    principal, annual_rate, term_months, user_monthly_payment, behavior, extra_payment, underpayment, late_fee
)

# On-Time Benchmark Simulation for comparison
df_ontime, _, total_interest_ontime, payoff_months_ontime = simulate_schedule(
    principal, annual_rate, term_months, user_monthly_payment, "On-time"
)


# 2. NUMERICAL SUMMARIES
st.subheader("📌 Key Financial Metrics")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Scheduled Monthly Payment", f"RM {base_pmt:,.2f}")
col2.metric("Total Interest Paid", f"RM {total_interest_sel:,.2f}")
col3.metric("Total Amount Repaid", f"RM {(principal + total_interest_sel):,.2f}")
col4.metric("Payoff Duration", f"{payoff_months_sel} Months ({(payoff_months_sel/12):.1f} Yrs)")

# Savings or Cost Impact Highlight
interest_diff = total_interest_sel - total_interest_ontime
month_diff = payoff_months_ontime - payoff_months_sel

if interest_diff < -0.01:
    st.success(f"🎉 **Early Settlement Savings:** Paying extra saves you **RM {abs(interest_diff):,.2f}** in interest and pays off your debt **{month_diff} months** faster!")
elif interest_diff > 0.01:
    st.error(f"⚠️ **Late Payment Penalty:** Underpaying adds **RM {interest_diff:,.2f}** in extra interest/fees and extends your debt term by **{abs(month_diff)} months**.")

st.markdown("---")

# 3. LINKED VISUALIZATIONS DASHBOARD
st.subheader("📊 Linked Interactive Dashboard")

v_col1, v_col2 = st.columns(2)

with v_col1:
    st.markdown("### View 1: Loan Balance Drawdown")
    # Balance drawdown curve
    fig_balance = px.line(
        df_selected, 
        x="Month", 
        y="Remaining Balance (RM)", 
        title="Remaining Principal Balance Over Time",
        markers=True
    )
    fig_balance.update_traces(line_color="#1f77b4", line_width=2.5)
    st.plotly_chart(fig_balance, use_container_width=True)

with v_col2:
    st.markdown("### View 2: Repayment Strategy Comparison")
    # Strategy comparisons
    _, _, int_ontime, _ = simulate_schedule(principal, annual_rate, term_months, user_monthly_payment, "On-time")
    _, _, int_early, _ = simulate_schedule(principal, annual_rate, term_months, user_monthly_payment, "Early (Pay Extra)", extra=100.0)
    _, _, int_late, _ = simulate_schedule(principal, annual_rate, term_months, user_monthly_payment, "Late (Underpay / Miss)", under=50.0, fee=30.0)

    df_comp = pd.DataFrame({
        "Behavior Strategy": ["Early (+RM100)", "On-Time Standard", "Late (-RM50 + RM30 Fee)"],
        "Total Interest Paid (RM)": [int_early, int_ontime, int_late]
    })
    
    fig_comp = px.bar(
        df_comp, 
        x="Behavior Strategy", 
        y="Total Interest Paid (RM)", 
        color="Behavior Strategy",
        title="Total Interest Cost Across Strategies",
        text_auto=".2f"
    )
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# View 3: Principal vs Interest Breakdown
st.markdown("### View 3: Principal vs. Interest Breakdown (Profit/Loss View)")

p_col1, p_col2 = st.columns([1, 1])

with p_col1:
    cost_df = pd.DataFrame({
        "Component": ["Original Principal", "Total Interest Paid"],
        "Amount (RM)": [principal, total_interest_sel]
    })
    fig_pie = px.pie(
        cost_df, 
        names="Component", 
        values="Amount (RM)", 
        title=f"Total Amount Repaid Breakdown ({behavior})",
        color_discrete_sequence=["#2ca02c", "#d62728"],
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with p_col2:
    st.markdown("#### Complete Amortization Schedule Table")
    st.dataframe(df_selected, height=300, use_container_width=True)

st.markdown("---")

# 4. FINANCIAL INTERPRETATION & ANALYSIS
st.subheader("💡 Financial Interpretation & Insights")

interest_ratio = (total_interest_sel / principal) * 100 if principal > 0 else 0.0

if behavior == "Early (Pay Extra)":
    st.info(f"""
    **Interpretation of Your Current Strategy (Early Payment):**
    * **Interest Reduction:** By paying an additional **RM {extra_payment:,.2f}** each month, you accelerate the rate at which your principal balance decreases.
    * **Cost Efficiency:** Interest makes up **{interest_ratio:.1f}%** of your total repaid amount (RM {principal + total_interest_sel:,.2f}).
    * **Time Savings:** Paying extra directly reduces interest compounding, allowing you to settle the debt in **{payoff_months_sel} months** (saving **{payoff_months_ontime - payoff_months_sel} months** compared to standard on-time installments).
    """)
elif behavior == "Late (Underpay / Miss)":
    st.warning(f"""
    **Interpretation of Your Current Strategy (Late / Underpayment):**
    * **Compounding Interest Impact:** Underpaying by **RM {underpayment:,.2f}** per month leaves a larger remaining balance to accrue interest each cycle.
    * **Fee Accumulation:** Late payment charges (RM {late_fee:,.2f}/month) further increase your total borrowing cost.
    * **Long-Term Cost:** Interest and penalties account for **{interest_ratio:.1f}%** of your total repayment, extending your tenure to **{payoff_months_sel} months** (**{payoff_months_sel - payoff_months_ontime} additional months** compared to on-time payments).
    """)
else:
    if user_monthly_payment > 0:
        pmt_note = f"With a custom monthly payment of **RM {user_monthly_payment:,.2f}**, it will take **{payoff_months_sel} months** to fully clear your balance."
    else:
        pmt_note = f"Paying the scheduled amortized amount of **RM {base_pmt:,.2f}** every month ensures you meet your target payoff term of **{payoff_months_sel} months** without incurring late fees."

    st.info(f"""
    **Interpretation of Your Current Strategy (Standard On-Time):**
    * **Payoff Duration:** {pmt_note}
    * **Cost Breakdown:** You will pay **RM {total_interest_sel:,.2f}** in cumulative interest, which constitutes **{interest_ratio:.1f}%** relative to your original borrowed principal of RM {principal:,.2f}.
    """)
