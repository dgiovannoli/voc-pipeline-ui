# Stage 3 Markdown Content - Temporarily moved from app.py

STAGE3_MARKDOWN_CONTENT = """
**How Scores and Findings Work**
| Relevance | Sentiment | Example Use                |
|-----------|-----------|---------------------------|
| 5         | Negative  | "Deal-breaker, must fix"  |
| 5         | Positive  | "Major strength"          |
| 3         | Neutral   | "Important, not polarizing" |
| 1         | Negative  | "Minor complaint"         |
| 0         | —         | Not mentioned             |

- **Relevance (0–5):** How important or salient the quote is for the criterion.
- **Sentiment:** Whether the feedback is positive, negative, neutral, or mixed.
- **Findings:**
    - **Strengths:** High relevance (≥ 3.5) + positive sentiment
    - **Risks/Areas for Improvement:** High relevance (≥ 3.5) + negative sentiment
    - **Monitor:** Moderate relevance, any sentiment
    - **Ignore:** Low relevance

**Note:**
The system now separates relevance and sentiment for clarity and better analytics.

**8 Core Evaluation Criteria**:
1. **Novelty**: The observation is new/unexpected, challenging assumptions
2. **Actionability**: Suggests clear steps, fixes, or actions to improve outcomes
3. **Specificity**: Precise, detailed, not generic - references particular features or processes
4. **Materiality**: Meaningful business impact affecting revenue, satisfaction, or positioning
5. **Recurrence**: Same observation across multiple interviews or sources
6. **Stakeholder Weight**: Comes from high-influence decision makers or critical personas
7. **Tension/Contrast**: Exposes tensions, tradeoffs, or significant contrasts
8. **Metric/Quantification**: Supported by tangible metrics, timeframes, or outcomes

**Enhanced Stage 3 Prompt Template**:
```
Generate an executive-ready finding using the Buried Wins Findings Criteria v4.0 framework.

CRITERION: {criterion} - {criterion_desc}
FINDING TYPE: {finding_type}
ENHANCED CONFIDENCE: {confidence_score:.1f}/10.0
CRITERIA MET: {criteria_met}/8 (Novelty, Actionability, Specificity, Materiality, Recurrence, Stakeholder Weight, Tension/Contrast, Metric/Quantification)

PATTERN SUMMARY:
{pattern_summary}

SELECTED EVIDENCE:
{selected_evidence}

REQUIREMENTS (Buried Wins v4.0):
- Write 2-3 sentences maximum
- Focus on actionable insights that could influence executive decision-making
- Use business language with specific impact
- Include material business implications
- Be clear, direct, and executive-ready
- Reference specific criteria met if relevant

OUTPUT: Just the finding text, no additional formatting.
```

**Enhanced Confidence Scoring**:
**Confidence Calculation**:
- **Base Score**: Number of criteria met (2-8 points)
- **Stakeholder Multipliers**: Executive (1.5x), Budget Holder (1.5x), Champion (1.3x)
- **Decision Impact Multipliers**: Deal Tipping Point (2.0x), Differentiator (1.5x), Blocker (1.5x)
- **Evidence Strength Multipliers**: Strong Positive/Negative (1.3x), Perspective Shifting (1.3x)

**Confidence Thresholds**:
- **Priority Finding**: ≥ 4.0/10.0
- **Standard Finding**: ≥ 3.0/10.0
- **Minimum Confidence**: ≥ 2.0/10.0

**Enhanced Pattern Recognition**:
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

**Executive Insights & Output**:
**Enhanced Output Format**:
- **Enhanced Confidence Scores**: 0-10 scale with detailed breakdown
- **Criteria Met Analysis**: 0-8 criteria evaluation
- **Priority Classification**: Priority vs Standard findings
- **Stakeholder Impact**: Executive, budget holder, and champion perspectives
- **Decision Impact**: Deal tipping points, differentiators, and blockers
- **Selected Evidence**: Automatically chosen optimal quotes
- **Cross-company Validation**: Multi-company pattern recognition
""" 