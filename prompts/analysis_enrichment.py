"""
Analysis Enrichment Prompt - Stage 2
Generates detailed insights and analysis from core verbatim responses.
This stage adds value through AI-generated insights without affecting the source of truth.
"""

ANALYSIS_ENRICHMENT_PROMPT = """
CRITICAL INSTRUCTIONS FOR ANALYSIS ENRICHMENT:
- Analyze the provided verbatim response to generate comprehensive insights
- Focus on extracting actionable intelligence and strategic value
- Provide detailed analysis across multiple dimensions
- Maintain objectivity and evidence-based insights

ANALYSIS DIMENSIONS:
1. **Key Insight**: Most important takeaway or revelation
2. **Findings**: Key discoveries and observations
3. **Value Realization**: ROI, benefits, and value metrics
4. **Implementation Experience**: How the solution was implemented
5. **Risk Mitigation**: How risks were addressed or could be addressed
6. **Competitive Advantage**: What makes this solution or approach superior
7. **Customer Success**: Factors contributing to successful outcomes
8. **Product Feedback**: Specific feedback about product features or capabilities
9. **Service Quality**: Assessment of service delivery and support
10. **Decision Factors**: What influenced the decision-making process
11. **Pain Points**: Challenges, frustrations, or problems identified
12. **Success Metrics**: How success was measured or could be measured
13. **Future Plans**: What's planned next or recommendations for the future

ANALYSIS APPROACH:
- Extract specific, actionable insights from the verbatim response
- Identify quantitative metrics and qualitative observations
- Highlight unique perspectives and valuable information
- Connect insights to business value and strategic implications
- Provide context and interpretation of customer feedback

Analyze the following verbatim response and generate comprehensive insights. Return ONLY a JSON object with the analysis fields:

{{
  "response_id": "{response_id}",
  "key_insight": "most_important_takeaway_or_revelation",
  "findings": "key_discoveries_and_observations",
  "value_realization": "roi_benefits_and_value_metrics",
  "implementation_experience": "how_the_solution_was_implemented",
  "risk_mitigation": "how_risks_were_addressed_or_could_be_addressed",
  "competitive_advantage": "what_makes_this_solution_or_approach_superior",
  "customer_success": "factors_contributing_to_successful_outcomes",
  "product_feedback": "specific_feedback_about_product_features_or_capabilities",
  "service_quality": "assessment_of_service_delivery_and_support",
  "decision_factors": "what_influenced_the_decision_making_process",
  "pain_points": "challenges_frustrations_or_problems_identified",
  "success_metrics": "how_success_was_measured_or_could_be_measured",
  "future_plans": "whats_planned_next_or_recommendations_for_the_future"
}}

Guidelines:
- Be specific and actionable in your analysis
- Extract both explicit and implicit insights from the response
- Focus on business value and strategic implications
- Use "N/A" for fields that don't apply to this response
- Maintain objectivity and evidence-based analysis
- Provide detailed, comprehensive insights across all dimensions
- Connect insights to broader business context and implications

Verbatim response to analyze:
{verbatim_response}

Subject: {subject}
Company: {company}
Interviewee: {interviewee_name}
"""

def get_analysis_enrichment_prompt(response_id: str, verbatim_response: str, subject: str, 
                                 company: str, interviewee_name: str) -> str:
    """Generate the analysis enrichment prompt with the provided parameters."""
    return ANALYSIS_ENRICHMENT_PROMPT.format(
        response_id=response_id,
        verbatim_response=verbatim_response,
        subject=subject,
        company=company,
        interviewee_name=interviewee_name
    ) 