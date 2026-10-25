"""app.py - StockSight Gemma 4 Interactive Financial Sentiment Dashboard
Addresses Issue #24 (Web GUI / Dashboard) and Issue #38 (Academic / Project Showcase).
Powered by Google's Gemma 4 open models (gemma-4-26b-a4b-it / gemma-4-31b-it) via GenAI SDK.
"""

import os
import streamlit as st
from gemma_sentiment import GemmaSentimentAnalyzer, SUPPORTED_GEMMA_MODELS, DEFAULT_GEMMA_MODEL

st.set_page_config(
    page_title="StockSight AI — Gemma 4 Sentiment & Market Reasoning",
    page_icon="📈",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1a73e8;
        margin-bottom: 12px;
    }
    .badge-positive { color: #0d8a43; font-weight: bold; }
    .badge-negative { color: #d93025; font-weight: bold; }
    .badge-neutral { color: #e37400; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("📈 StockSight AI: Gemma 4 Sentiment & Market Reasoning")
st.caption("Next-generation open-source financial sentiment analysis powered by Google Gemma 4 open weights.")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Model Settings")
    api_key_input = st.text_input(
        "Google GenAI API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Enter your Gemini/Gemma API key from Google AI Studio"
    )
    selected_model = st.selectbox(
        "Gemma 4 Architecture",
        options=SUPPORTED_GEMMA_MODELS,
        index=0
    )
    enable_thinking = st.checkbox(
        "Enable Thinking Process (Multi-step Reasoning)",
        value=True,
        help="Gemma 4 uses internal thinking reasoning for algorithmic and financial domain tasks."
    )

    st.markdown("---")
    st.markdown("### About StockSight")
    st.markdown(
        "StockSight previously used legacy rule-based lexicons (VADER/TextBlob). "
        "This upgraded version utilizes **Gemma 4** open models for deep financial catalyst evaluation."
    )

# Pre-defined sample headlines for fast testing
SAMPLE_HEADLINES = {
    "TSLA": "Tesla surges 12% after Q3 robotaxi deployment approval and crushing automotive gross margin estimates.",
    "AAPL": "Apple hit with $1.8B antitrust penalty in Europe as regulators mandate third-party app store fee reductions.",
    "NVDA": "Nvidia signs multi-year hyperscaler cloud contract for next-generation Blackwell Ultra architecture.",
    "AMZN": "Amazon Web Services reports operating income growth of 33% year-over-year fueled by enterprise AI compute demand.",
    "Custom": ""
}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Select Ticker & News")
    ticker = st.text_input("Stock Symbol", value="TSLA").upper().strip()
    
    preset = st.selectbox("Sample Headline Presets", options=list(SAMPLE_HEADLINES.keys()))
    default_text = SAMPLE_HEADLINES[preset] if preset != "Custom" else ""

    text_to_analyze = st.text_area(
        "News Headline or Market Commentary",
        value=default_text,
        height=140,
        placeholder="Paste a financial headline, tweet, or earnings report excerpt..."
    )

    analyze_btn = st.button("🚀 Analyze with Gemma 4", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Gemma 4 Financial Intelligence")

    if analyze_btn and text_to_analyze:
        with st.spinner("Gemma 4 is reasoning through market dynamics..."):
            analyzer = GemmaSentimentAnalyzer(
                api_key=api_key_input or None,
                model=selected_model,
                thinking=enable_thinking
            )
            result = analyzer.analyze(text_to_analyze, symbol=ticker)

        sentiment = result.get("sentiment", "neutral").upper()
        polarity = result.get("polarity", 0.0)
        subjectivity = result.get("subjectivity", 0.5)
        confidence = result.get("confidence", 0.8)
        reasoning = result.get("reasoning", "No explanation available.")
        catalysts = result.get("key_catalysts", [])

        # Metric Columns
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            color_class = "badge-positive" if sentiment == "POSITIVE" else ("badge-negative" if sentiment == "NEGATIVE" else "badge-neutral")
            st.metric("Sentiment", sentiment)
        with m2:
            st.metric("Polarity", f"{polarity:+.2f}", help="-1.0 (Bearish) to +1.0 (Bullish)")
        with m3:
            st.metric("Subjectivity", f"{subjectivity:.2f}", help="0.0 (Factual) to 1.0 (Opinion)")
        with m4:
            st.metric("Confidence", f"{confidence:.0%}")

        # Progress Bar for Polarity: map [-1, 1] to [0, 1]
        norm_polarity = (polarity + 1.0) / 2.0
        st.write("**Market Sentiment Spectrum**")
        st.progress(norm_polarity)

        # Reasoning
        st.markdown("### 🧠 Multi-Step Financial Rationale")
        st.info(reasoning)

        # Catalysts
        if catalysts:
            st.markdown("### 🎯 Key Market Catalysts")
            for cat in catalysts:
                st.markdown(f"- **{cat}**")

    elif not text_to_analyze and analyze_btn:
        st.warning("Please enter or select a headline to analyze.")
    else:
        st.info("Select a sample headline or enter text, then click **Analyze with Gemma 4**.")

st.markdown("---")
st.subheader("💬 Ask Gemma 4 About Any Stock")
user_question = st.text_input(
    f"Ask a question regarding {ticker}:",
    placeholder=f"e.g., What are the key upside and downside risks for {ticker} this quarter?"
)
if st.button("Submit Question") and user_question:
    with st.spinner("Consulting Gemma 4..."):
        analyzer = GemmaSentimentAnalyzer(
            api_key=api_key_input or None,
            model=selected_model,
            thinking=enable_thinking
        )
        answer = analyzer.ask(user_question, symbol=ticker)
    st.write(answer)
