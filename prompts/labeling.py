"""
Labeling Prompt - Stage 3
Adds structured labels and classifications to responses for better organization and analysis.
This stage provides categorization without affecting the core data or analysis.
"""

LABELING_PROMPT = """
CRITICAL INSTRUCTIONS FOR RESPONSE LABELING:
- Add structured labels to categorize and classify the response
- Focus on objective, consistent labeling across multiple dimensions
- Provide confidence scores for each label
- Use predefined label categories for consistency

LABELING DIMENSIONS:

1. **Sentiment**: Overall emotional tone of the response
   - positive: Generally favorable, satisfied, enthusiastic
   - negative: Dissatisfied, frustrated, critical
   - neutral: Balanced, factual, neither positive nor negative
   - mixed: Contains both positive and negative elements

2. **Priority**: Business importance and urgency
   - high: Critical issues, major opportunities, urgent needs
   - medium: Important but not urgent, moderate impact
   - low: Minor issues, nice-to-have features, low impact

3. **Actionable**: Whether the response contains actionable insights
   - yes: Clear next steps, specific recommendations, implementable ideas
   - no: General feedback, observations without specific actions
   - maybe: Some actionable elements but not clearly defined

4. **Topic**: Primary subject matter of the response
   - product_features: Specific product capabilities or features
   - process: Workflow, procedures, operational aspects
   - pricing: Cost, pricing models, value for money
   - support: Customer service, technical support, help
   - integration: System integration, compatibility, APIs
   - decision_making: Purchase decisions, evaluation criteria
   - workflow_optimization: Process improvements, efficiency gains
   - competitive: Competitive analysis, market positioning
   - technical: Technical specifications, requirements
   - business_impact: ROI, business outcomes, strategic value

5. **Quality**: Assessment of response quality and usefulness
   - excellent: Highly detailed, specific, actionable, valuable insights
   - good: Detailed and useful, some actionable elements
   - fair: Some useful information but limited detail
   - poor: Vague, general, or low-value content

6. **Confidence**: Confidence in the accuracy of the analysis
   - high: Clear, unambiguous content, high confidence in labels
   - medium: Some ambiguity but generally clear
   - low: Unclear, contradictory, or limited information

Analyze the following response and provide structured labels. Return ONLY a JSON object with the labels:

{{
  "response_id": "{response_id}",
  "labels": {{
    "sentiment": {{
      "value": "positive|negative|neutral|mixed",
      "confidence": 0.95
    }},
    "priority": {{
      "value": "high|medium|low",
      "confidence": 0.90
    }},
    "actionable": {{
      "value": "yes|no|maybe",
      "confidence": 0.85
    }},
    "topic": {{
      "value": "primary_topic_category",
      "confidence": 0.88
    }},
    "quality": {{
      "value": "excellent|good|fair|poor",
      "confidence": 0.92
    }},
    "confidence": {{
      "value": "high|medium|low",
      "confidence": 0.87
    }}
  }}
}}

Guidelines:
- Be objective and consistent in your labeling
- Consider the full context of the response
- Provide confidence scores between 0.0 and 1.0
- Use the most appropriate label from the predefined categories
- Consider both explicit statements and implicit meaning
- Focus on the primary topic and sentiment
- Assess quality based on detail, specificity, and usefulness

Response to label:
{verbatim_response}

Subject: {subject}
Company: {company}
Interviewee: {interviewee_name}
"""

def get_labeling_prompt(response_id: str, verbatim_response: str, subject: str, 
                       company: str, interviewee_name: str) -> str:
    """Generate the labeling prompt with the provided parameters."""
    return LABELING_PROMPT.format(
        response_id=response_id,
        verbatim_response=verbatim_response,
        subject=subject,
        company=company,
        interviewee_name=interviewee_name
    ) 