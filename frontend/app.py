import streamlit as st

st.set_page_config(page_title="Hybrid Search", layout="wide")

# ---------------- HEADER ---------------- #
st.title("🔍 Hybrid Search System")
st.caption(
    "Production-style retrieval system combining BM25 (keyword) + Vector (semantic) search with hybrid ranking."
)

st.divider()

# ---------------- QUICK ACTIONS ---------------- #
st.subheader("🚀 Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔍 Run Search", use_container_width=True):
        st.switch_page("pages/1_Search.py")

with col2:
    if st.button("📊 KPI Dashboard", use_container_width=True):
        st.switch_page("pages/2_KPI.py")

with col3:
    if st.button("🧪 Evaluation", use_container_width=True):
        st.switch_page("pages/3_Evaluation.py")

with col4:
    if st.button("🐞 Debug Results", use_container_width=True):
        st.switch_page("pages/4_Debug.py")

st.divider()

# ---------------- HOW IT WORKS ---------------- #
st.subheader("🧠 How It Works")

st.markdown(
    """
**Query → BM25 (Keyword Match) + Vector (Semantic Similarity) → Hybrid Ranking → Results**

- **BM25** → exact keyword matching  
- **Vector Search** → semantic understanding using embeddings  
- **Hybrid** → weighted combination controlled by alpha (α)  
"""
)

st.divider()

# ---------------- ABOUT ---------------- #
st.subheader("👨‍💻 About the System")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Hardik Grover")
    st.caption("Software Engineer")
    st.markdown("#### 📬 Contact")
    st.markdown(
        """
- 📧 h.grov21@gmail.com  
- 📱 +91-8882055121
- 🔗 [LinkedIn](https://www.linkedin.com/in/hardik-g-bb10bb91/)  
"""
    )


with col2:
    st.markdown(
        """
This project is a **hybrid retrieval system** designed to combine the strengths of:

- **Lexical search (BM25)** for precise keyword matching  
- **Vector search** for semantic understanding  
- **Hybrid ranking** to balance both approaches  

It focuses on:
- Search relevance and ranking quality  
- Observability and debugging of retrieval systems  
- Real-world experimentation with hybrid search strategies  

**Tech Stack:**
- FastAPI (search backend)  
- Streamlit (interactive UI)
- SQLite (request logging)
"""
    )

st.info(
    "Goal: Build a production-style search system with clear visibility into ranking behavior and performance."
)

st.divider()

# ---------------- FOOTER ---------------- #
st.caption("Use the sidebar or Quick Actions to navigate across Search, KPI, Evaluation, and Debug tools.")