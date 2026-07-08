import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from statsmodels.tsa.holtwinters import ExponentialSmoothing

FORECAST_PATH = Path("data/data.xlsx")


@st.cache_data
def load_forecast_data():

    df = pd.read_excel(
        FORECAST_PATH,
        sheet_name="DAILY REPORT"
    )

    df["Order Date"] = pd.to_datetime(
        df["Order Date"]
    )

    df = df.sort_values(
        "Order Date"
    )

    return df


def show_forecast():

    df = load_forecast_data()

    # =====================================
    # SIDEBAR
    # =====================================

    st.sidebar.header("Filter")

    items = sorted(df["Description"].dropna().unique())

    item = st.sidebar.selectbox(
        "Pilih Item",
        items
    )

    # =====================================
    # FILTER DATA
    # =====================================

    data_item = df[df["Description"] == item].copy()

    if data_item.empty:
        st.error("Item tidak ditemukan.")
        return

    # =====================================
    # KPI
    # =====================================

    harga = data_item["Direct Unit Cost"].astype(float)

    harga_awal = harga.iloc[0]
    harga_terakhir = harga.iloc[-1]
    harga_rata = harga.mean()

    jumlah = len(harga)

    if harga_terakhir > harga_awal:
        trend = "📈 NAIK"
    elif harga_terakhir < harga_awal:
        trend = "📉 TURUN"
    else:
        trend = "➡️ STABIL"

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Harga Terakhir", f"Rp {harga_terakhir:,.0f}")
    c2.metric("Harga Rata-rata", f"Rp {harga_rata:,.0f}")
    c3.metric("Jumlah Transaksi", jumlah)
    c4.metric("Trend", trend)

    st.divider()

    # =====================================
    # FORECAST
    # =====================================

    st.subheader("🔮 Forecast")

    forecast = None

    if len(harga) >= 5:

        model = ExponentialSmoothing(
            harga,
            trend="add",
            seasonal=None
        )

        fit = model.fit()

        forecast = fit.forecast(2)

        f1, f2 = st.columns(2)

        f1.metric(
            "Forecast Periode 1",
            f"Rp {forecast.iloc[0]:,.0f}"
        )

        f2.metric(
            "Forecast Periode 2",
            f"Rp {forecast.iloc[1]:,.0f}"
        )

    else:

        st.warning("Data belum cukup untuk forecast.")

    st.divider()

    # =====================================
    # GRAFIK
    # =====================================

    st.subheader(f"📈 Trend Harga - {item}")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        data_item["Order Date"],
        harga,
        marker="o",
        linewidth=2,
        label="Harga Aktual"
    )

    if forecast is not None:

        tanggal_forecast = pd.date_range(
            start=data_item["Order Date"].max(),
            periods=3,
            freq="MS"
        )[1:]

        ax.plot(
            tanggal_forecast,
            forecast,
            linestyle="--",
            marker="o",
            linewidth=2,
            label="Forecast"
        )

    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Harga")
    ax.grid(True)
    ax.legend()

    plt.xticks(rotation=45)

    st.pyplot(fig)

    # =====================================
    # REKOMENDASI
    # =====================================

    if forecast is not None:

        st.subheader("💡 Rekomendasi")

        if forecast.iloc[1] > harga.iloc[-1]:

            st.warning(
                "Harga diperkirakan naik.\n\n"
                "Disarankan mempertimbangkan pembelian lebih awal."
            )

        else:

            st.success(
                "Harga diperkirakan stabil atau turun.\n\n"
                "Pembelian dapat dijadwalkan sesuai kebutuhan."
            )

    st.divider()

    # =====================================
    # DETAIL DATA
    # =====================================

    st.subheader("📋 Detail Transaksi")

    kolom = [
        "Order Date",
        "Buy-from Vendor Name",
        "Quantity",
        "Direct Unit Cost"
    ]

    st.dataframe(
        data_item[kolom],
        use_container_width=True
    )


if __name__ == "__main__":
    show_forecast()