import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from io import BytesIO
from forecast import show_forecast

# ==========================================
# CONFIG
# ==========================================

st.set_page_config(
    page_title="Procurement Analytics",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# CSS
# ==========================================

st.markdown("""
<style>

.main{
    background-color:#F5F7FA;
}

.stMetric{
    background:white;
    padding:15px;
    border-radius:15px;
}

div[data-testid="metric-container"]{
    background:white;
    border-radius:15px;
    padding:18px;
    box-shadow:0px 3px 8px rgba(0,0,0,.08);
    border-left:6px solid #00A86B;
}

h1,h2,h3{
    color:#0B6E4F;
}

.hero{
    background:linear-gradient(90deg,#0B6E4F,#00A86B);
    padding:30px;
    border-radius:18px;
    color:white;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# TITLE
# ==========================================

st.markdown("""
# 🏢 Procurement Analytics System

### Purchasing Performance Dashboard

---
""")

# ==========================================
# PATH
# ==========================================

DATA_PATH = Path("data/Dashboard Laporan.xlsx")
VENDOR_PATH = Path("data/Evaluasi Vendor Juni.xlsx")
COST_REDUCTION_PATH = Path("data/Cost Reduction.xlsx")
BUDGET_DETAIL_PATH = Path(
    "data/Budget Detail.xlsx"
)
SUPPORT_VENDOR_PATH = Path(
    "data/Support Vendor.xlsx"
)

VENDOR_ACTIVE_PATH = Path(
    "data/Vendor Aktif.xlsx"
)


MONTH_ORDER = [
    "Jan","Feb","Mar","Apr",
    "May","Jun","Jul","Aug",
    "Sep","Oct","Nov","Dec"
]

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("📂 Data")

uploaded = st.sidebar.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Budget",
        "Evaluasi Supplier",
        "Supplier",
        "Cost Reduction",
        "Forecast"
    ]
)

# ==========================================
# LOAD EXCEL
# ==========================================

@st.cache_data
def load_daily(upload_bytes):

    src = BytesIO(upload_bytes) if upload_bytes else DATA_PATH

    df = pd.read_excel(
        src,
        sheet_name="DAILY REPORT",
        header=4
    )

    df = df.loc[:,~df.columns.astype(str).str.contains("^Unnamed")]

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df["DATE"] = pd.to_datetime(
        df["DATE"],
        errors="coerce"
    )

    df = df.dropna(subset=["DATE"])

    df["QTY"] = (
        pd.to_numeric(
            df["QTY"],
            errors="coerce"
        )
        .fillna(0)
    )

    df["COST AMOUNT"] = (
        pd.to_numeric(
            df["COST AMOUNT"],
            errors="coerce"
        )
        .fillna(0)
    )

    df["MONTH_NO"] = df["DATE"].dt.month
    df["BULAN"] = df["DATE"].dt.strftime("%b")
    df["#YEAR"] = df["DATE"].dt.year

    return df

# ==========================================
# READ DATA
# ==========================================

upload_bytes = (
    uploaded.getvalue()
    if uploaded
    else None
)

try:

    df = load_daily(upload_bytes)

except Exception as e:

    st.error(e)

    st.stop()

# ==========================================
# FILTER
# ==========================================

tahun = sorted(df["#YEAR"].unique())

tahun_pilih = st.sidebar.selectbox(
    "Tahun",
    tahun
)

df = df[df["#YEAR"]==tahun_pilih]

bulan = st.sidebar.selectbox(
    "Bulan",
    ["Semua"]+MONTH_ORDER
)

if bulan!="Semua":

    df=df[df["BULAN"]==bulan]

# ==========================================
# DASHBOARD
# ==========================================

if menu == "Dashboard":

    # -------------------------------
    # HERO CARD
    # -------------------------------

    total_cost = df["COST AMOUNT"].sum()
    total_qty = df["QTY"].sum()
    total_supplier = df["SUPPLIER"].nunique()
    total_item = df["ITEM"].nunique()
    total_po = df["PO"].nunique()

    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg,#0B6E4F,#00A86B);
        padding:30px;
        border-radius:20px;
        color:white;
        margin-bottom:25px;
    ">
        <h4>💰 TOTAL PROCUREMENT COST</h4>
        <h1>Rp {total_cost:,.0f}</h1>
        <p>Procurement Analytics System</p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------
    # KPI
    # -------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📄 Total PO", f"{total_po:,}")
    c2.metric("🏭 Supplier", f"{total_supplier:,}")
    c3.metric("📦 Item", f"{total_item:,}")
    c4.metric("⚖ Quantity", f"{total_qty:,.2f}")

    st.divider()

    # -------------------------------
    # MONTHLY COST
    # -------------------------------

    monthly = (
        df.groupby(["MONTH_NO", "BULAN"], as_index=False)
        ["COST AMOUNT"]
        .sum()
        .sort_values("MONTH_NO")
    )

    fig = px.bar(
        monthly,
        x="BULAN",
        y="COST AMOUNT",
        text_auto=".2s",
        color="COST AMOUNT",
        color_continuous_scale="Greens"
    )

    fig.update_layout(
        title="💰 Cost Amount per Bulan",
        plot_bgcolor="white",
        paper_bgcolor="white",
        coloraxis_showscale=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # TOP SUPPLIER & TOP ITEM
    # -------------------------------

    col1, col2 = st.columns(2)

    with col1:

        supplier = (
            df.groupby("SUPPLIER", as_index=False)
            ["COST AMOUNT"]
            .sum()
            .sort_values("COST AMOUNT", ascending=False)
            .head(10)
        )

        fig1 = px.bar(
            supplier,
            x="COST AMOUNT",
            y="SUPPLIER",
            orientation="h",
            text_auto=".2s",
            color="COST AMOUNT",
            color_continuous_scale="Greens"
        )

        fig1.update_layout(
            title="🏭 Top 10 Supplier",
            coloraxis_showscale=False
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2:

        item = (
            df.groupby("ITEM", as_index=False)
            ["COST AMOUNT"]
            .sum()
            .sort_values("COST AMOUNT", ascending=False)
            .head(10)
        )

        fig2 = px.bar(
            item,
            x="COST AMOUNT",
            y="ITEM",
            orientation="h",
            text_auto=".2s",
            color="COST AMOUNT",
            color_continuous_scale="Greens"
        )

        fig2.update_layout(
            title="📦 Top 10 Item",
            coloraxis_showscale=False
        )

        st.plotly_chart(fig2, use_container_width=True)

    # -------------------------------
    # PROCUREMENT INSIGHT
    # -------------------------------

    bulan_max = monthly.loc[
        monthly["COST AMOUNT"].idxmax(),
        "BULAN"
    ]

    supplier_max = supplier.iloc[0]["SUPPLIER"]
    item_max = item.iloc[0]["ITEM"]

    st.success(f"""
### 🧠 Procurement Insight

📈 Bulan dengan Cost tertinggi : **{bulan_max}**

🏭 Supplier terbesar : **{supplier_max}**

📦 Item terbesar : **{item_max}**

💰 Total Cost : **Rp {total_cost:,.0f}**

📄 Total PO : **{total_po:,}**
""")

    st.divider()

    st.subheader("📋 Detail Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
        # ==========================================
# BUDGET
# ==========================================

elif menu == "Budget":

    st.title("💰 Budget Dashboard")

    try:

        src = BytesIO(upload_bytes) if upload_bytes else DATA_PATH

        budget = pd.read_excel(
            src,
            sheet_name="Budget",
            header=4
        )

        budget = budget.loc[
            :,
            ~budget.columns.astype(str).str.contains("^Unnamed")
        ]

        budget.columns = (
            budget.columns.astype(str)
            .str.strip()
        )

    except Exception as e:

        st.error(e)
        st.stop()

    # ==========================
    # KPI
    # ==========================

    total_budget = budget["BUDGET"].sum()
    total_actual = budget["ACTUAL"].sum()
    total_saving = budget["SAVING"].sum()

    c1, c2, c3 = st.columns(3)

    c1.metric("💰 Budget", f"Rp {total_budget:,.0f}")
    c2.metric("💸 Actual", f"Rp {total_actual:,.0f}")
    c3.metric("✅ Saving", f"Rp {total_saving:,.0f}")

    # ==========================
    # HERO
    # ==========================

    persen = (total_actual / total_budget) * 100

    st.markdown(f"""
    <div style="
        background:linear-gradient(90deg,#155724,#28A745);
        padding:25px;
        border-radius:18px;
        color:white;
    ">

    <h3>📊 Budget Absorption</h3>

    <h1>{persen:.1f}%</h1>

    </div>
    """, unsafe_allow_html=True)

    st.progress(min(persen / 100, 1.0))

    st.caption(f"Budget terserap {persen:.1f}%")
    
    fig = px.bar(

        budget,

        x="BUDGETING",

        y=[
            "BUDGET",
            "ACTUAL"
        ],

        barmode="group",

        title="Budget vs Actual"

    )

    st.plotly_chart(
        fig,
        use_container_width=True
)
    fig = px.bar(

        budget,

        x="BUDGETING",

        y="SAVING",

        color="SAVING",

        color_continuous_scale="Greens"

        )

    fig.update_layout(
        title="💰 Saving"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    budget_max = budget.loc[
        budget["ACTUAL"].idxmax(),
        "BUDGETING"
    ]

    st.success(f"""

### 🧠 Budget Insight

💰 Budget

Rp {total_budget:,.0f}

💸 Actual

Rp {total_actual:,.0f}

✅ Saving

Rp {total_saving:,.0f}

📈 Budget terbesar

{budget_max}

""")

    st.divider()

    st.subheader("📋 Detail Budget Bulanan")


    try:

        budget_detail = pd.read_excel(
            BUDGET_DETAIL_PATH,
            header=5
        )


        budget_detail = budget_detail.loc[
            :,
            ~budget_detail.columns.astype(str)
            .str.contains("^Unnamed")
        ]


        budget_detail.columns = (
            budget_detail.columns
            .astype(str)
            .str.strip()
        )


        # hapus baris kosong

        budget_detail = (
            budget_detail
            .dropna(subset=["BUDGETING"])
        )


        # format rupiah

        for col in [
            "BUDGET",
            "ACTUAL",
            "SAVING"
        ]:

            budget_detail[col] = (
                pd.to_numeric(
                    budget_detail[col],
                    errors="coerce"
                )
                .apply(
                    lambda x:
                    f"Rp {x:,.0f}"
                    if pd.notnull(x)
                    else "-"
                )
            )


        # format persen

        budget_detail[
            "% Budget tidak sesuai"
        ] = (
            pd.to_numeric(
                budget_detail[
                    "% Budget tidak sesuai"
                ],
                errors="coerce"
            )
            .apply(
                lambda x:
                f"{x:.2%}"
                if pd.notnull(x)
                else "-"
            )
        )


        st.dataframe(
            budget_detail,
            use_container_width=True,
            hide_index=True
        )


    except Exception as e:

        st.error(
            "Budget Detail gagal dibaca"
        )

        st.write(e) 

elif menu == "Forecast":

    show_forecast()

elif menu == "Evaluasi Supplier":

    st.title("🏭 Evaluasi Vendor")


    try:

        vendor = pd.read_excel(
            VENDOR_PATH,
            sheet_name="Rekapitulasi",
            header=3
        )


        vendor = vendor.loc[
            :,
            ~vendor.columns.astype(str).str.contains("^Unnamed")
        ]


        vendor.columns = (
            vendor.columns
            .astype(str)
            .str.strip()
        )


        vendor = vendor.dropna(
            subset=["Nama Vendor"]
        )

        # Tambahkan status visual



    except Exception as e:

        st.error("File Evaluasi Vendor belum terbaca")
        st.write(e)
        st.stop()



    # ==========================
    # KPI
    # ==========================

    total_vendor = vendor["Nama Vendor"].nunique()

    rata_score = vendor["Nilai Evaluasi"].mean()

    excellent = (
        vendor["Hasil"] == "Excellent"
    ).sum()

    poor = (
        vendor["Hasil"] == "Poor"
    ).sum()


    c1,c2,c3,c4 = st.columns(4)


    c1.metric(
        "🏭 Total Vendor",
        total_vendor
    )


    c2.metric(
        "⭐ Rata-rata Score",
        f"{rata_score:.2f}"
    )


    c3.metric(
        "🏆 Excellent",
        excellent
    )


    c4.metric(
        "⚠️ Poor",
        poor
    )



    st.divider()



    # ==========================
    # TABEL CANTIK
    # ==========================


    vendor_display = vendor.copy()

    vendor_display["Status"] = (
        vendor_display["Hasil"]
        .replace({
            "Excellent": "🟢 Excellent",
            "Good": "🟡 Good",
            "Poor": "🔴 Poor"
        })
    )

    st.dataframe(
        vendor_display,
        use_container_width=True,
        hide_index=True
    )

elif menu == "Supplier":

    st.title("🏭 Support Vendor")


    # ==================================
    # LOAD VENDOR AKTIF
    # ==================================

    try:

        vendor = pd.read_excel(
            VENDOR_ACTIVE_PATH,
            sheet_name="Sheet1",
            header=3
        )

        vendor = vendor.loc[
            :,
            ~vendor.columns.astype(str).str.contains("^Unnamed")
        ]

        vendor.columns = (
            vendor.columns
            .astype(str)
            .str.strip()
        )

        vendor = vendor.dropna(
            how="all"
        )

        vendor["Nama Item"] = (
            vendor["Nama Item"]
            .ffill()
        )

        vendor = vendor.dropna(
            subset=["Vendor"]
        )

        vendor["Nama Item"] = (
            vendor["Nama Item"]
            .astype(str)
            .str.strip()
        )

        vendor["Vendor"] = (
            vendor["Vendor"]
            .astype(str)
            .str.strip()
        )

    except Exception as e:

        st.error("Vendor Aktif gagal dibaca")
        st.write(e)

        try:
            st.write("Kolom terbaca:")
            st.write(vendor.columns.tolist())
        except:
            pass

        st.stop()


    # ==================================
    # LOAD SUPPORT VENDOR
    # ==================================

    try:

        support = pd.read_excel(
            SUPPORT_VENDOR_PATH,
            sheet_name="Rekap Sponsor",
            header=4
        )

        support = support.loc[
            :,
            ~support.columns.astype(str).str.contains("^Unnamed")
        ]

        support.columns = (
            support.columns
            .astype(str)
            .str.strip()
        )

        support = support.dropna(
            how="all"
        )

        support = support.dropna(
            subset=["Keterangan"]
        )

    except Exception as e:

        st.error("Support Vendor gagal dibaca")
        st.write(e)

        try:
            st.write("Kolom support terbaca:")
            st.write(support.columns.tolist())
        except:
            pass

        st.stop()


    # ==================================
    # CLEAN SUPPORT VENDOR
    # ==================================

    support["Nominal"] = pd.to_numeric(
        support["Nominal"],
        errors="coerce"
    ).fillna(0)

    support["Total Pembelian"] = pd.to_numeric(
        support["Total Pembelian"],
        errors="coerce"
    ).fillna(0)

    support["% Support"] = pd.to_numeric(
        support["% Support"],
        errors="coerce"
    ).fillna(0)


    # ==================================
    # KPI
    # ==================================

    total_vendor = vendor["Vendor"].nunique()

    total_item = vendor["Nama Item"].nunique()

    total_support = support["Nominal"].sum()

    total_pembelian = support["Total Pembelian"].sum()


    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "🏭 Vendor Aktif",
        total_vendor
    )

    c2.metric(
        "📦 Total Item",
        total_item
    )

    c3.metric(
        "🤝 Total Support",
        f"Rp {total_support:,.0f}"
    )

    c4.metric(
        "💰 Total Pembelian",
        f"Rp {total_pembelian:,.0f}"
    )


    st.divider()


    # ==================================
    # TABEL VENDOR AKTIF
    # ==================================

    st.subheader("📋 List Vendor Pareto Aktif")

    st.dataframe(
        vendor[
            [
                "Nama Item",
                "Vendor"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


    st.divider()


    # ==================================
    # TABEL SUPPORT VENDOR
    # ==================================

    st.subheader("🤝 Rekap Support Vendor")

    support_display = support.copy()

    support_display["Nominal"] = (
        support_display["Nominal"]
        .apply(
            lambda x: f"Rp {x:,.0f}"
        )
    )

    support_display["Total Pembelian"] = (
        support_display["Total Pembelian"]
        .apply(
            lambda x: f"Rp {x:,.0f}"
        )
    )

    support_display["% Support"] = (
        support_display["% Support"]
        .apply(
            lambda x: f"{x:.2%}"
        )
    )

    st.dataframe(
        support_display[
            [
                "Tanggal",
                "Keterangan",
                "Nominal",
                "Total Pembelian",
                "% Support"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )
elif menu == "Cost Reduction":

    st.title("💰 Cost Reduction")


    # ==========================
    # READ EXCEL
    # ==========================

    try:

        cr = pd.read_excel(
            COST_REDUCTION_PATH,
            sheet_name="Cost Reduction",
            header=3
        )


        cr = cr.loc[
            :,
            ~cr.columns.astype(str)
            .str.contains("^Unnamed")
        ]


        cr.columns = (
            cr.columns
            .astype(str)
            .str.strip()
        )


    except Exception as e:

        st.error(
            "File Cost Reduction tidak terbaca"
        )

        st.write(e)
        st.stop()



    # ==========================
    # CLEAN DATA
    # ==========================


    cr["Ket"] = (
        cr["Ket"]
        .astype(str)
        .str.strip()
    )


    # ubah PCR menjadi angka

    cr["PCR_VALUE"] = (
        cr["PCR"]
        .astype(str)
        .str.replace(
            "Rp",
            "",
            regex=False
        )
        .str.replace(
            ".",
            "",
            regex=False
        )
        .str.replace(
            ",",
            "",
            regex=False
        )
        .str.strip()
    )


    cr["PCR_VALUE"] = pd.to_numeric(
        cr["PCR_VALUE"],
        errors="coerce"
    )



    # ==========================
    # KPI
    # ==========================


    total_saving = (
        cr.loc[
            cr["Ket"]=="Saving",
            "PCR_VALUE"
        ]
        .sum()
    )


    total_saving_item = (
        cr[
            cr["Ket"]=="Saving"
        ]
        .shape[0]
    )


    total_increase = (
        cr[
            cr["Ket"]=="Cost Increase"
        ]
        .shape[0]
    )


    total_change = (
        cr[
            cr["Ket"]=="No Change"
        ]
        .shape[0]
    )



    c1,c2,c3 = st.columns(3)


    c1.metric(
        "💰 Total Saving",
        f"Rp {total_saving:,.0f}"
    )


    c2.metric(
        "🟢 Item Saving",
        total_saving_item
    )


    c3.metric(
        "🔴 Cost Increase",
        total_increase
    )



    st.divider()



    # ==========================
    # STATUS CHART
    # ==========================


    status = (
        cr["Ket"]
        .value_counts()
        .reset_index()
    )


    status.columns = [
        "Status",
        "Jumlah"
    ]


    fig = px.pie(
        status,
        names="Status",
        values="Jumlah",
        title="Status Cost Reduction"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )



    # ==========================
    # TABLE DISPLAY
    # ==========================


    st.subheader(
        "📋 Detail Cost Reduction"
    )


    cr_display = cr.copy()


    for col in ["Mei", "Juni"]:

            cr_display[col] = (
                pd.to_numeric(
                cr_display[col],
                errors="coerce"
            )
            .round(0)
            .apply(
                lambda x: f"Rp {x:,.0f}"
                if pd.notnull(x)
                else ""
            )
        )


    cr_display["PCR"] = (
            cr["PCR_VALUE"]
             .round(0)
             .apply(
                lambda x: f"Rp {x:,.0f}"
        )
    )


    cr_display["Ket"] = (
            cr_display["Ket"]
             .replace({
            "Saving":"🟢 Saving",
            "No Change":"🟡 No Change",
            "Cost Increase":"🔴 Cost Increase"
        })
    )


    st.dataframe(
            cr_display,
            use_container_width=True,
            hide_index=True
    )