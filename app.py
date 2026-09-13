import io
import streamlit as st
import pandas as pd
import numpy as np
from weasyprint import HTML

# ---------------------------------------------------------
# Page Configuration & Header
# ---------------------------------------------------------
st.set_page_config(
    page_title="PoultryPro Analytics | Farm Enterprise Suite",
    page_icon="🐓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🐓 PoultryPro Enterprise SaaS")
st.caption("Multi-Species Unit Economics, FCR Tracking & Profitability Engine")
st.markdown("---")

# ---------------------------------------------------------
# Sidebar Configuration Inputs
# ---------------------------------------------------------
st.sidebar.header("📋 Batch Setup Parameters")

species_type = st.sidebar.selectbox(
    "Select Poultry Species",
    ["Broiler (Meat)", "Layer (Egg Production)", "Noiler (Dual Purpose)", "Cockerel (Meat)", "Breeder (Hatching)"]
)

currency = st.sidebar.selectbox("Currency", ["₦ (NGN)", "$ (USD)", "£ (GBP)", "€ (EUR)"])
bird_count = st.sidebar.number_input("Initial Bird Stock (DOC Count)", min_value=10, max_value=100000, value=500, step=50)
doc_unit_price = st.sidebar.number_input(f"Unit Price per DOC/Bird ({currency})", min_value=0.0, value=650.0, step=10.0)
mortality_rate = st.sidebar.slider("Expected Mortality Rate (%)", min_value=0.0, max_value=25.0, value=5.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.header("🌾 Feed & Operational Costs")

if "Broiler" in species_type:
    default_feed_kg = 4.0
    default_sale_price = 4500.0
elif "Layer" in species_type:
    default_feed_kg = 42.0
    default_sale_price = 3800.0
elif "Noiler" in species_type:
    default_feed_kg = 7.5
    default_sale_price = 5500.0
elif "Cockerel" in species_type:
    default_feed_kg = 9.0
    default_sale_price = 5000.0
else:
    default_feed_kg = 38.0
    default_sale_price = 1200.0

feed_per_bird_kg = st.sidebar.number_input("Est. Feed Consumption per Bird (kg)", min_value=0.1, value=default_feed_kg, step=0.5)
feed_cost_per_bag = st.sidebar.number_input(f"Cost per 25kg Feed Bag ({currency})", min_value=0.0, value=18500.0, step=250.0)
drugs_vac_per_bird = st.sidebar.number_input(f"Medication & Vaccines per Bird ({currency})", min_value=0.0, value=250.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.header("🏠 Overhead & Shared Expenses")

heating_brooding = st.sidebar.number_input(f"Brooding Energy (Charcoal/Gas/Elec) ({currency})", min_value=0.0, value=25000.0, step=1000.0)
labor_wages = st.sidebar.number_input(f"Labor & Salaries for Batch ({currency})", min_value=0.0, value=60000.0, step=2500.0)
pen_rent_maint = st.sidebar.number_input(f"Pen Rent & Maintenance Allocated ({currency})", min_value=0.0, value=35000.0, step=1000.0)
utilities_other = st.sidebar.number_input(f"Water, Electricity & Misc ({currency})", min_value=0.0, value=15000.0, step=1000.0)

st.sidebar.markdown("---")
st.sidebar.header("💰 Revenue Projections")

if "Layer" in species_type:
    crates_per_bird = st.sidebar.number_input("Est. Crates of Eggs per Surviving Layer", min_value=1.0, value=14.0, step=0.5)
    price_per_crate = st.sidebar.number_input(f"Selling Price per Crate ({currency})", min_value=0.0, value=3600.0, step=100.0)
    spent_hen_price = st.sidebar.number_input(f"Spent Hen Selling Price ({currency})", min_value=0.0, value=3000.0, step=100.0)
else:
    unit_sale_price = st.sidebar.number_input(f"Selling Price per Bird ({currency})", min_value=0.0, value=default_sale_price, step=100.0)
    target_weight_kg = st.sidebar.number_input("Target Avg Weight per Bird at Harvest (kg)", min_value=0.5, value=2.6, step=0.1)

# ---------------------------------------------------------
# Analytical Calculations & Core Engine Logic
# ---------------------------------------------------------
surviving_birds = int(bird_count * (1 - (mortality_rate / 100)))
mortality_count = bird_count - surviving_birds

total_doc_cost = bird_count * doc_unit_price
total_feed_kg = bird_count * feed_per_bird_kg
total_feed_bags = total_feed_kg / 25.0
feed_cost_per_kg = feed_cost_per_bag / 25.0
total_feed_cost = total_feed_kg * feed_cost_per_kg
total_medication_cost = bird_count * drugs_vac_per_bird

total_overhead = heating_brooding + labor_wages + pen_rent_maint + utilities_other
total_batch_cost = total_doc_cost + total_feed_cost + total_medication_cost + total_overhead
cost_per_surviving_bird = total_batch_cost / surviving_birds if surviving_birds > 0 else 0

if "Layer" in species_type:
    egg_revenue = surviving_birds * crates_per_bird * price_per_crate
    spent_hen_revenue = surviving_birds * spent_hen_price
    gross_revenue = egg_revenue + spent_hen_revenue
    fcr = total_feed_kg / (surviving_birds * 2.0)
else:
    gross_revenue = surviving_birds * unit_sale_price
    total_biomass_kg = surviving_birds * target_weight_kg
    fcr = total_feed_kg / total_biomass_kg if total_biomass_kg > 0 else 0

net_profit = gross_revenue - total_batch_cost
net_margin_pct = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0
breakeven_price_per_bird = cost_per_surviving_bird

# Cost Breakdown Table Data
cost_data = {
    "Expense Category": ["Stocking (DOC)", "Feed", "Medication & Vaccines", "Overhead & Labor"],
    "Amount": [total_doc_cost, total_feed_cost, total_medication_cost, total_overhead],
    "Cost per Bird": [
        total_doc_cost / bird_count,
        total_feed_cost / bird_count,
        total_medication_cost / bird_count,
        total_overhead / bird_count
    ]
}
df_costs = pd.DataFrame(cost_data)
df_costs["Percentage of Total"] = (df_costs["Amount"] / total_batch_cost) * 100

# ---------------------------------------------------------
# PDF Generation Function
# ---------------------------------------------------------
def generate_pdf_report(species_type, bird_count, surviving_birds, mortality_rate, 
                        total_batch_cost, gross_revenue, net_profit, fcr, 
                        cost_per_surviving_bird, currency, df_costs):
    table_rows = ""
    for _, row in df_costs.iterrows():
        table_rows += f"""
        <tr>
            <td>{row['Expense Category']}</td>
            <td class="text-right">{currency} {row['Amount']:,.2f}</td>
            <td class="text-right">{currency} {row['Cost per Bird']:,.2f}</td>
            <td class="text-right">{row['Percentage of Total']:.1f}%</td>
        </tr>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 15mm 12mm; }}
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a202c; font-size: 10pt; }}
            .header {{ background-color: #1e3a8a; color: white; padding: 20px; border-radius: 6px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0 0 5px 0; font-size: 18pt; }}
            .header p {{ margin: 0; opacity: 0.85; font-size: 9.5pt; }}
            .kpi-table {{ width: 100%; border-collapse: separate; border-spacing: 8px; margin-bottom: 15px; }}
            .kpi-card {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; text-align: center; }}
            .kpi-value {{ font-size: 13pt; font-weight: bold; color: #1e3a8a; margin-top: 4px; }}
            .kpi-label {{ font-size: 8pt; color: #64748b; text-transform: uppercase; }}
            table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }}
            table.data-table th, table.data-table td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            table.data-table th {{ background-color: #f1f5f9; color: #334155; font-size: 9pt; font-weight: bold; }}
            .text-right {{ text-align: right; }}
            .summary-box {{ background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px 15px; margin-top: 20px; }}
            .summary-box h3 {{ margin: 0 0 5px 0; color: #15803d; font-size: 11pt; }}
            .summary-box p {{ margin: 0; color: #166534; font-size: 9.5pt; line-height: 1.4; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐓 PoultryPro Analytics Feasibility Report</h1>
            <p>Batch Unit Economics & Feasibility Audit | Enterprise SaaS Summary</p>
        </div>
        <table class="kpi-table">
            <tr>
                <td class="kpi-card" width="25%"><div class="kpi-label">Species Type</div><div class="kpi-value">{species_type}</div></td>
                <td class="kpi-card" width="25%"><div class="kpi-label">Surviving Flock</div><div class="kpi-value">{surviving_birds:,} Birds</div></td>
                <td class="kpi-card" width="25%"><div class="kpi-label">Total Investment</div><div class="kpi-value">{currency} {total_batch_cost:,.2f}</div></td>
                <td class="kpi-card" width="25%"><div class="kpi-label">Net Profit</div><div class="kpi-value">{currency} {net_profit:,.2f}</div></td>
            </tr>
        </table>
        <h3 style="color: #1e3a8a; border-bottom: 2px solid #e2e8f0;">Itemized Budget Distribution</h3>
        <table class="data-table">
            <thead>
                <tr><th>Expense Category</th><th class="text-right">Total Amount ({currency})</th><th class="text-right">Cost / Bird ({currency})</th><th class="text-right">Share of Budget</th></tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>
        <div class="summary-box">
            <h3>Key Batch Indicators</h3>
            <p>
                • <strong>Feed Conversion Ratio (FCR):</strong> {fcr:.2f}<br>
                • <strong>Production Cost per Bird:</strong> {currency} {cost_per_surviving_bird:,.2f}<br>
                • <strong>Break-Even Selling Price:</strong> {currency} {cost_per_surviving_bird:,.2f}<br>
                • <strong>Mortality Loss:</strong> {mortality_rate:.1f}% ({bird_count - surviving_birds} birds)
            </p>
        </div>
    </body>
    </html>
    """
    return HTML(string=html_template).write_pdf()

# ---------------------------------------------------------
# Dashboard Main Layout Presentation
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Surviving Flock", f"{surviving_birds:,} Birds", f"-{mortality_count} Dead ({mortality_rate}%)")
col2.metric("Total Batch Cost", f"{currency} {total_batch_cost:,.2f}")
col3.metric("Gross Revenue", f"{currency} {gross_revenue:,.2f}")
col4.metric("Net Profit", f"{currency} {net_profit:,.2f}", f"{net_margin_pct:.1f}% Margin")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Performance KPIs", "📑 Cost Breakdown & Exports", "📉 Sensitivity Analysis"])

with tab1:
    st.subheader("Key Performance & Efficiency Indicators")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.metric("Feed Conversion Ratio (FCR)", f"{fcr:.2f}", delta="Lower is better", delta_color="inverse")
        st.caption("Kg of feed consumed per kg of live weight gain.")
    with kpi_col2:
        st.metric("Production Cost / Surviving Bird", f"{currency} {cost_per_surviving_bird:,.2f}")
        st.caption("Includes DOC, feed, drugs, and allocated overhead.")
    with kpi_col3:
        st.metric("Break-Even Selling Price", f"{currency} {breakeven_price_per_bird:,.2f}")
        st.caption("Minimum unit selling price required to cover all costs.")

with tab2:
    st.subheader("Itemized Batch Cost Distribution")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.dataframe(df_costs.style.format({
            "Amount": f"{currency} {{:,.2f}}",
            "Cost per Bird": f"{currency} {{:,.2f}}",
            "Percentage of Total": "{:.1f}%"
        }), use_container_width=True)
    with c2:
        st.write("**Cost Structure Summary:**")
        st.write(f"- Total Feed Bags Required: **{total_feed_bags:.1f} bags**")
        st.write(f"- Feed Ratio to Total Cost: **{(total_feed_cost/total_batch_cost)*100:.1f}%**")
        st.write(f"- Overhead Ratio to Total Cost: **{(total_overhead/total_batch_cost)*100:.1f}%**")

    st.markdown("---")
    st.subheader("📥 Export Batch Reports & Financial Summaries")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        csv_bytes = df_costs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Cost Breakdown (CSV)",
            data=csv_bytes,
            file_name=f"poultry_cost_breakdown_{species_type.split()[0].lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_exp2:
        pdf_bytes = generate_pdf_report(
            species_type=species_type,
            bird_count=bird_count,
            surviving_birds=surviving_birds,
            mortality_rate=mortality_rate,
            total_batch_cost=total_batch_cost,
            gross_revenue=gross_revenue,
            net_profit=net_profit,
            fcr=fcr,
            cost_per_surviving_bird=cost_per_surviving_bird,
            currency=currency,
            df_costs=df_costs
        )
        st.download_button(
            label="📕 Download Executive Audit Report (PDF)",
            data=pdf_bytes,
            file_name=f"poultrypro_audit_{species_type.split()[0].lower()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

with tab3:
    st.subheader("Profit Sensitivity Matrix (Mortality vs. Feed Cost)")
    mortality_range = [3.0, 5.0, 8.0, 10.0, 15.0]
    feed_price_variations = [feed_cost_per_bag * factor for factor in [0.9, 0.95, 1.0, 1.05, 1.10]]
    
    matrix_data = []
    for f_price in feed_price_variations:
        row = []
        for m_rate in mortality_range:
            s_birds = bird_count * (1 - (m_rate / 100))
            t_f_cost = total_feed_kg * (f_price / 25.0)
            t_cost = total_doc_cost + t_f_cost + total_medication_cost + total_overhead
            if "Layer" in species_type:
                g_rev = s_birds * (crates_per_bird * price_per_crate + spent_hen_price)
            else:
                g_rev = s_birds * unit_sale_price
            row.append(g_rev - t_cost)
        matrix_data.append(row)
        
    df_matrix = pd.DataFrame(
        matrix_data,
        index=[f"Feed Bag @ {currency}{p:,.0f}" for p in feed_price_variations],
        columns=[f"Mortality {m}%" for m in mortality_range]
    )
    
    st.dataframe(df_matrix.style.format(f"{currency} {{:,.0f}}"), use_container_width=True)
    st.caption("Matrix displays estimated Net Profit across different feed price shocks and mortality levels.")
