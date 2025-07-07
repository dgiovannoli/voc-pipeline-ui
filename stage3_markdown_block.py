# Replacement block for Stage 3 markdown and subheaders in app.py

print('''
st.subheader("🎯 Enhanced Confidence Scoring")
st.markdown(
""" 
**Confidence Calculation**:
- **Base Score**: Number of criteria met (2-8 points)
- **Stakeholder Multipliers**: Executive (1.5x), Budget Holder (1.5x), Champion (1.3x)
- **Decision Impact Multipliers**: Deal Tipping Point (2.0x), Differentiator (1.5x), Blocker (1.5x)
- **Evidence Strength Multipliers**: Strong Positive/Negative (1.3x), Perspective Shifting (1.3x)

**Confidence Thresholds**:
- **Priority Finding**: ≥ 4.0/10.0
- **Standard Finding**: ≥ 3.0/10.0
- **Minimum Confidence**: ≥ 2.0/10.0
"""
)

st.subheader("🔍 Enhanced Pattern Recognition")
st.markdown(
""" 
**Pattern Thresholds**:
- Minimum 3 quotes to form a pattern
- Minimum 2 companies for cross-company validation
- Minimum 2 criteria met for valid findings
- Enhanced confidence scoring with stakeholder weighting

**Quote Selection Logic**:
- Automated selection of optimal quotes (max 3 per finding)
- Priority scoring based on deal impact, stakeholder perspective, and sentiment
- Deal tipping point identification (deal breaker, critical, essential)
- Executive and budget holder perspective weighting
"""
)

st.subheader("📈 Executive Insights & Output")
st.markdown(
""" 
**Enhanced Output Format**:
- **Enhanced Confidence Scores**: 0-10 scale with detailed breakdown
- **Criteria Met Analysis**: 0-8 criteria evaluation
- **Priority Classification**: Priority vs Standard findings
- **Stakeholder Impact**: Executive, budget holder, and champion perspectives
- **Decision Impact**: Deal tipping points, differentiators, and blockers
- **Selected Evidence**: Automatically chosen optimal quotes
- **Cross-company Validation**: Multi-company pattern recognition
"""
)
''') 