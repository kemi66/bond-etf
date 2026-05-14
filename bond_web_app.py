import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="債券 ETF 殖利率雷達", layout="wide")
st.title("📊 債券 ETF 即時殖利率與配息雷達")

# --- 新增功能：抓取即時美金兌台幣匯率 ---
try:
    twd_rate = yf.Ticker("TWD=X").history(period="1d")['Close'].iloc[-1]
    st.success(f"💵 目前即時匯率： **1 美元 (USD) = {twd_rate:.3f} 台幣 (TWD)**")
except:
    st.warning("⚠️ 目前無法取得即時匯率")
# ------------------------------------

st.markdown("🎯 **任務：** 自動抓取最新股價，以「最近一期配息」換算預估年化殖利率！")

bonds_data = [
    {"代號": "00687B", "名稱": "國泰20年美債", "配息頻率": "季配", "配息月份": "3, 6, 9, 12", "最近一期配息": 0.28},
    {"代號": "00679B", "名稱": "元大美債20年", "配息頻率": "季配", "配息月份": "2, 5, 8, 11", "最近一期配息": 0.28},
    {"代號": "00725B", "名稱": "國泰投資級公司債", "配息頻率": "季配", "配息月份": "1, 4, 7, 10", "最近一期配息": 0.49},
    {"代號": "00937B", "名稱": "群益ESG投等債20+", "配息頻率": "月配", "配息月份": "1~12", "最近一期配息": 0.072},
    {"代號": "00720B", "名稱": "元大投資級公司債", "配息頻率": "季配", "配息月份": "1, 4, 7, 10", "最近一期配息": 0.48},
    {"代號": "00751B", "名稱": "元大AAA至A公司債", "配息頻率": "季配", "配息月份": "3, 6, 9, 12", "最近一期配息": 0.41},
    {"代號": "00772B", "名稱": "中信高評級公司債", "配息頻率": "月配", "配息月份": "1~12", "最近一期配息": 0.14}
]

@st.cache_data(ttl=300)
def fetch_bond_data():
    df = pd.DataFrame(bonds_data)
    tickers = df["代號"].tolist()
    latest_prices = []
    
    for ticker in tickers:
        try:
            hist = yf.Ticker(f"{ticker}.TWO").history(period="5d")
            if hist.empty:
                hist = yf.Ticker(f"{ticker}.TW").history(period="5d")
                
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                latest_prices.append(round(price, 2))
            else:
                latest_prices.append(0.0)
        except:
            latest_prices.append(0.0)
            
    df["最新股價"] = latest_prices
    df["年化乘數"] = df["配息頻率"].map({"月配": 12, "季配": 4})
    df["預估年化配息"] = df["最近一期配息"] * df["年化乘數"]
    df["殖利率(%)"] = df.apply(
        lambda row: round((row["預估年化配息"] / row["最新股價"]) * 100, 2) if row["最新股價"] > 0 else 0.0, 
        axis=1
    )
    return df

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 更新最新股價與匯率", type="primary"):
        st.cache_data.clear()

with st.spinner("連線抓取最新報價與匯率中..."):
    df_display = fetch_bond_data()

st.sidebar.header("🔍 篩選與排序")
freq_filter = st.sidebar.multiselect("選擇配息頻率", options=["月配", "季配"], default=["月配", "季配"])
sort_by = st.sidebar.radio("排序方式", ["殖利率(%) 高至低", "最新股價 低至高"])

filtered_df = df_display[df_display["配息頻率"].isin(freq_filter)]
if "殖利率" in sort_by:
    filtered_df = filtered_df.sort_values(by="殖利率(%)", ascending=False)
else:
    filtered_df = filtered_df.sort_values(by="最新股價", ascending=True)

st.subheader("📋 債券 ETF 護眼監控表 (年化殖利率 = 最近一期配息 × 頻率 ÷ 最新股價)")
st.dataframe(
    filtered_df[["代號", "名稱", "最新股價", "最近一期配息", "殖利率(%)", "配息頻率", "配息月份"]],
    hide_index=True,
    use_container_width=True
)
