import streamlit as st
from fraud_detector import FraudDetector
from datetime import datetime, time
import pandas as pd

# Initialize fraud detector
if 'detector' not in st.session_state:
    st.session_state.detector = FraudDetector()

# Page config
st.set_page_config(
    page_title="BHARAT PRAGATI - UPI Fraud Prevention",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; background-color: #1f77b4; color: white; font-weight: bold; }
    h1 { color: #1f77b4; text-align: center; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .success { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    .warning { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    .danger { background-color: #f8d7da; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏦 BHARAT PRAGATI")
st.subtitle("AI-Driven UPI Fraud Prevention System | Team: QuantumMinds")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose Page", ["Fraud Detection", "Transaction History", "Statistics", "Settings", "About"])

# ======================== PAGE 1: FRAUD DETECTION ========================
if page == "Fraud Detection":
    st.header("🔍 Analyze UPI Transaction for Fraud Risk")
    st.write("Enter transaction details below to check fraud risk in real-time")
    
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input(
            "💰 Transaction Amount (₹)",
            min_value=0,
            max_value=500000,
            value=5000,
            step=500
        )
        
    with col2:
        transaction_time = st.time_input(
            "⏰ Transaction Time",
            value=datetime.now().time()
        )
        time_hour = transaction_time.hour
    
    col3, col4 = st.columns(2)
    
    with col3:
        is_new_recipient = st.checkbox("👤 Is this a NEW UPI recipient?", value=False)
    
    with col4:
        recipient_history = st.slider(
            "📱 How many times contacted this recipient before?",
            min_value=0,
            max_value=10,
            value=0
        )
    
    # Analyze button
    if st.button("🔍 ANALYZE TRANSACTION RISK", key="analyze"):
        with st.spinner("🤖 Analyzing transaction..."):
            # Get risk analysis
            result = st.session_state.detector.calculate_risk_score(
                amount=amount,
                time_hour=time_hour,
                is_new_recipient=is_new_recipient,
                recipient_history_count=recipient_history
            )
            
            # Save to database
            save_status = st.session_state.detector.save_transaction(
                amount=amount,
                transaction_time=str(transaction_time),
                is_new_recipient=is_new_recipient,
                recipient_history_count=recipient_history,
                analysis_result=result
            )
            
            st.markdown("---")
            
            # Risk Level Display
            if "HIGH" in result["risk_level"]:
                st.error(f"## {result['risk_level']}")
            elif "MEDIUM" in result["risk_level"]:
                st.warning(f"## {result['risk_level']}")
            else:
                st.success(f"## {result['risk_level']}")
            
            # Risk Score Bar
            st.metric("Risk Score", f"{result['risk_score']}%")
            
            # Progress bar visualization
            st.progress(min(result['risk_score'] / 100, 1.0))
            
            # Risk Factors
            st.subheader("📊 Risk Factors Detected:")
            if result['risk_factors']:
                for i, factor in enumerate(result['risk_factors'], 1):
                    st.write(f"**{i}.** {factor}")
            else:
                st.write("✅ No risk factors detected")
            
            # Recommendation
            st.subheader("✅ System Recommendation:")
            st.info(result["recommendation"])
            
            if save_status:
                st.success("✅ Transaction logged in SQLite database!")
            else:
                st.error("❌ Error saving transaction")

# ======================== PAGE 2: TRANSACTION HISTORY ========================
elif page == "Transaction History":
    st.header("📋 Transaction Analysis History")
    
    transactions = st.session_state.detector.get_all_transactions()
    
    if transactions:
        # Display as table
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Transaction History (CSV)",
            data=csv,
            file_name="bharat_pragati_transactions.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        st.subheader("🎯 Quick Filters:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_risk_only = st.checkbox("Show only HIGH RISK")
        with col2:
            medium_risk_only = st.checkbox("Show only MEDIUM RISK")
        with col3:
            low_risk_only = st.checkbox("Show only LOW RISK")
        
        if high_risk_only:
            filtered_df = df[df["Risk Level"].str.contains("HIGH")]
            st.dataframe(filtered_df, use_container_width=True)
        elif medium_risk_only:
            filtered_df = df[df["Risk Level"].str.contains("MEDIUM")]
            st.dataframe(filtered_df, use_container_width=True)
        elif low_risk_only:
            filtered_df = df[df["Risk Level"].str.contains("LOW")]
            st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("📭 No transactions analyzed yet. Go to 'Fraud Detection' tab to start!")

# ======================== PAGE 3: STATISTICS ========================
elif page == "Statistics":
    st.header("📊 Transaction Statistics & Analytics")
    
    stats = st.session_state.detector.get_stats()
    
    if stats['total'] > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total Transactions", stats['total'])
        with col2:
            st.metric("🔴 High Risk", stats['high_risk'])
        with col3:
            st.metric("🟡 Medium Risk", stats['medium_risk'])
        with col4:
            st.metric("🟢 Low Risk", stats['low_risk'])
        
        st.markdown("---")
        
        col5, col6 = st.columns(2)
        
        with col5:
            st.metric("📊 Average Risk Score", f"{stats['average_risk']}%")
        with col6:
            st.metric("💰 Total Amount Analyzed", f"₹{stats['total_amount']:,.0f}")
        
        st.markdown("---")
        
        # Pie chart
        st.subheader("Risk Distribution")
        risk_data = {
            '🔴 High Risk': stats['high_risk'],
            '🟡 Medium Risk': stats['medium_risk'],
            '🟢 Low Risk': stats['low_risk']
        }
        
        st.bar_chart({
            'High Risk': stats['high_risk'],
            'Medium Risk': stats['medium_risk'],
            'Low Risk': stats['low_risk']
        })
    else:
        st.info("📭 No data yet. Analyze transactions to see statistics!")

# ======================== PAGE 4: SETTINGS ========================
elif page == "Settings":
    st.header("⚙️ Settings & Database Management")
    
    st.subheader("🗄️ Database Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Database File:** `bharat_pragati.db`")
    with col2:
        st.write("**Database Type:** SQLite3")
    
    st.markdown("---")
    
    st.subheader("🧹 Clear Database")
    st.warning("⚠️ This will delete ALL transactions! Use only for testing.")
    
    if st.button("🗑️ DELETE ALL TRANSACTIONS", key="delete_all"):
        if st.session_state.detector.clear_database():
            st.success("✅ All transactions deleted successfully!")
            st.rerun()
        else:
            st.error("❌ Error deleting transactions")
    
    st.markdown("---")
    
    st.subheader("📝 Test Sample Data")
    if st.button("📥 Load Sample Transactions", key="load_samples"):
        sample_transactions = [
            {"amount": 2000, "time": "14:30", "new": False, "history": 5},
            {"amount": 200000, "time": "02:15", "new": True, "history": 0},
            {"amount": 75000, "time": "23:45", "new": True, "history": 2},
            {"amount": 5000, "time": "10:00", "new": False, "history": 10},
        ]
        
        for txn in sample_transactions:
            result = st.session_state.detector.calculate_risk_score(
                amount=txn["amount"],
                time_hour=int(txn["time"].split(":")[0]),
                is_new_recipient=txn["new"],
                recipient_history_count=txn["history"]
            )
            st.session_state.detector.save_transaction(
                amount=txn["amount"],
                transaction_time=txn["time"],
                is_new_recipient=txn["new"],
                recipient_history_count=txn["history"],
                analysis_result=result
            )
        
        st.success("✅ Sample transactions loaded!")
        st.rerun()

# ======================== PAGE 5: ABOUT ========================
elif page == "About":
    st.header("About BHARAT PRAGATI")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Problem Statement
        
        UPI fraud is increasing rapidly in India. Millions of transactions happen daily, but fraudsters are becoming smarter.
        
        **Real Problem:**
        - ₹2000+ crores lost annually to UPI fraud
        - Current systems are reactive (detect after fraud)
        - No real-time fraud prevention
        """)
    
    with col2:
        st.markdown("""
        ### 💡 Our Solution
        
        **BHARAT PRAGATI** - AI-powered real-time UPI fraud detection
        
        **Our System Analyzes:**
        - 💰 Transaction Amount
        - ⏰ Time of Day
        - 👤 Recipient History
        - 📱 Recipient Type (New vs. Known)
        """)
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
        ### 🚀 Key Features
        
        ✅ **Real-Time Risk Analysis**
        - Analyze transactions instantly
        
        ✅ **Multi-Factor Verification**
        - OTP + Biometric for high-risk
        
        ✅ **Transaction History**
        - Track all analyzed transactions
        
        ✅ **Risk Dashboard**
        - Visual risk indicators
        """)
    
    with col4:
        st.markdown("""
        ### 🏆 Impact
        
        - **Prevent Fraud:** Stop transactions before loss
        - **Save Lives:** Protect common people from scams
        - **Financial Security:** Make UPI safer for India
        - **Government Support:** Aligns with digital India
        
        ### 👥 Team
        **QuantumMinds**
        - Building solutions for India's digital security
        - Tejas Hackathon 2026
        """)
    
    st.markdown("---")
    
    st.subheader("📱 Tech Stack")
    col5, col6, col7 = st.columns(3)
    with col5:
        st.write("**Frontend:** Streamlit")
    with col6:
        st.write("**Backend:** Python")
    with col7:
        st.write("**Database:** SQLite")