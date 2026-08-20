st.metric(
    "Risk Score",
    result["risk"]["final_score"]
)

st.write(
    "Risk Level:",
    result["risk"]["risk_level"]
)

st.write(
    "Decision:",
    result["decision"]
)

for reason in result["reasons"]:

    st.warning(reason)