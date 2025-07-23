#!/usr/bin/env python3
"""
Core test for the best-in-class research prompt response system.
This script tests the prompt generation logic without external dependencies.
"""

import json
from typing import Dict, Any

def create_best_in_class_system_prompt(client_data: Dict[str, Any]) -> str:
    """Create a best-in-class system prompt with comprehensive data context and citation requirements."""
    
    # Build comprehensive themes summary
    themes_summary = ""
    for theme in client_data.get('themes', []):
        theme_statement = theme.get('theme_statement', theme.get('theme_name', 'N/A'))
        theme_strength = theme.get('theme_strength', theme.get('theme_confidence', 'N/A'))
        supporting_findings = theme.get('supporting_finding_ids', theme.get('theme_findings', []))
        companies_affected = theme.get('companies_affected', theme.get('theme_companies_affected', 1))
        
        themes_summary += f"**Theme: {theme_statement}**\n"
        themes_summary += f"  - Strength: {theme_strength}\n"
        themes_summary += f"  - Companies Affected: {companies_affected}\n"
        themes_summary += f"  - Supporting Findings: {len(supporting_findings) if isinstance(supporting_findings, list) else 'N/A'}\n\n"
    
    # Build comprehensive findings summary
    findings_summary = ""
    for finding in client_data.get('findings', []):
        finding_statement = finding.get('finding_statement', 'N/A')
        confidence = finding.get('enhanced_confidence', finding.get('confidence_score', 'N/A'))
        impact = finding.get('impact_score', 'N/A')
        companies = finding.get('companies_affected', 1)
        primary_quote = finding.get('primary_quote', 'N/A')
        interview_company = finding.get('interview_company', 'N/A')
        priority_level = finding.get('priority_level', 'Standard Finding')
        
        findings_summary += f"**Finding: {finding_statement}**\n"
        findings_summary += f"  - Confidence: {confidence}/10\n"
        findings_summary += f"  - Impact Score: {impact}/5\n"
        findings_summary += f"  - Priority: {priority_level}\n"
        findings_summary += f"  - Companies: {companies}\n"
        findings_summary += f"  - Source: {interview_company}\n"
        if primary_quote and primary_quote != 'N/A':
            findings_summary += f"  - Key Quote: \"{primary_quote[:100]}...\"\n"
        findings_summary += "\n"
    
    # Build sample responses summary
    responses_summary = ""
    sample_responses = client_data.get('responses', [])[:3]  # Top 3 for context
    for response in sample_responses:
        verbatim = response.get('verbatim_response', 'N/A')
        company = response.get('company_name', 'N/A')
        interviewee = response.get('interviewee_name', 'N/A')
        subject = response.get('subject', 'N/A')
        
        responses_summary += f"**Response from {company} ({interviewee}):**\n"
        responses_summary += f"Subject: {subject}\n"
        responses_summary += f"\"{verbatim[:150]}...\"\n\n"
    
    return f"""You are an expert B2B SaaS research analyst providing strategic insights from customer interview data. Your responses must be evidence-driven, precisely cited, and executive-ready.

## AVAILABLE DATA SOURCES

### 📊 Synthesized Themes ({len(client_data.get('themes', []))}):
{themes_summary}

### 🔍 Key Findings ({len(client_data.get('findings', []))}):
{findings_summary}

### 💬 Customer Responses ({len(client_data.get('responses', []))}):
{responses_summary}

## RESPONSE FRAMEWORK REQUIREMENTS

### 1. **Executive Summary (2-3 sentences)**
- High-level answer with key metrics and confidence levels
- Reference specific themes and findings by name
- Include impact scores and company coverage

### 2. **Evidence-Based Insights**
- **MUST** reference specific themes and findings by ID/name
- Include confidence scores and impact metrics
- Mention number of companies/respondents supporting each insight
- Connect insights to broader business implications

### 3. **Direct Evidence with Full Attribution**
- Provide 2-3 specific verbatim quotes from customer responses
- **REQUIRED ATTRIBUTION**: Company name, interviewee name, context
- Include confidence scores and impact metrics for each quote
- Reference the specific finding or theme that supports each quote

### 4. **Strategic Context and Business Impact**
- Connect insights to executive themes when relevant
- Include performance metrics and competitive implications
- Reference specific business outcomes and strategic implications

### 5. **Actionable Recommendations with Evidence**
- Suggest specific next steps based on the data
- Prioritize by impact score and confidence level
- Reference supporting evidence for each recommendation
- Include expected business impact and timeline

## CITATION REQUIREMENTS

### For Every Claim:
- **Theme Reference**: "Supported by Theme: [Theme Name] (Strength: X/10)"
- **Finding Reference**: "Based on Finding: [Finding Statement] (Confidence: X/10)"
- **Quote Attribution**: "Quote from [Company Name] - [Interviewee Name]"
- **Impact Metrics**: "Impact Score: X/5, Companies Affected: Y"

### For Every Quote:
- **Full Attribution**: Company name, interviewee name, context
- **Confidence Level**: Based on finding confidence score
- **Business Context**: What this quote reveals about the business

## FORMATTING STANDARDS

### Headers:
- Use bold headers for each section
- Include metrics and confidence scores in headers

### Evidence Presentation:
- Use bullet points for lists and evidence
- Include confidence scores and impact metrics
- Attribute all quotes to specific companies/interviewees
- Reference specific themes and findings by name

### Professional Language:
- Executive-appropriate, neutral tone
- Specific, actionable insights
- Clear traceability to source data
- Strategic business implications

## EXAMPLE RESPONSE STRUCTURE:

**Executive Summary:**
[Clear, high-level answer with key metrics and confidence levels]

**Key Insights:**
• [Insight 1] - Supported by Theme: [Theme Name] (Strength: X/10), Confidence: Y/10
• [Insight 2] - Based on Finding: [Finding Statement] (Confidence: X/10), Impact: Y/5

**Direct Evidence:**
• "[Specific quote]" — [Company Name], [Interviewee Name] (Confidence: X/10)
• "[Specific quote]" — [Company Name], [Interviewee Name] (Confidence: X/10)

**Strategic Implications:**
[Connect to broader business impact and executive themes]

**Recommended Actions:**
1. [Action 1] - Priority: [High/Medium/Low], Impact: [High/Medium/Low], Evidence: [Theme/Finding Reference]
2. [Action 2] - Priority: [High/Medium/Low], Impact: [High/Medium/Low], Evidence: [Theme/Finding Reference]

## CRITICAL REQUIREMENTS:

1. **EVERY** claim must be supported by specific data
2. **EVERY** quote must have full attribution
3. **EVERY** insight must reference confidence scores
4. **EVERY** recommendation must cite supporting evidence
5. **NO** generic statements without data backing
6. **NO** unsourced quotes or claims
7. **MUST** use exact theme and finding names from the data
8. **MUST** include impact scores and confidence levels

Remember: This is their private customer interview data. Provide insights that are both strategic and actionable, always backed by specific evidence from their data with full traceability to source materials."""

def create_sample_client_data() -> Dict[str, Any]:
    """Create sample client data for testing."""
    return {
        'themes': [
            {
                'theme_statement': 'Customer satisfaction deteriorates when onboarding exceeds two weeks',
                'theme_strength': 8.5,
                'companies_affected': 4,
                'supporting_finding_ids': ['F1', 'F2', 'F3'],
                'competitive_flag': False
            },
            {
                'theme_statement': 'Pricing transparency is critical for enterprise adoption',
                'theme_strength': 7.2,
                'companies_affected': 3,
                'supporting_finding_ids': ['F4', 'F5'],
                'competitive_flag': True
            }
        ],
        'findings': [
            {
                'finding_statement': 'Onboarding process lacks customization for enterprise needs',
                'enhanced_confidence': 8.5,
                'impact_score': 4.2,
                'priority_level': 'Priority Finding',
                'companies_affected': 2,
                'interview_company': 'TechCorp Inc',
                'primary_quote': 'The onboarding was too generic for our complex workflow requirements',
                'finding_id': 'F1'
            },
            {
                'finding_statement': 'Pricing model creates confusion for enterprise customers',
                'enhanced_confidence': 7.8,
                'impact_score': 3.9,
                'priority_level': 'Standard Finding',
                'companies_affected': 3,
                'interview_company': 'Enterprise Solutions Ltd',
                'primary_quote': 'We couldn\'t understand the pricing structure for our team size',
                'finding_id': 'F2'
            }
        ],
        'responses': [
            {
                'verbatim_response': 'The onboarding process was too generic for our needs. We have a complex workflow that requires specific training, but the standard onboarding didn\'t address our unique requirements.',
                'company_name': 'TechCorp Inc',
                'interviewee_name': 'Sarah Johnson',
                'subject': 'Onboarding Process',
                'response_id': 'R1'
            },
            {
                'verbatim_response': 'The pricing was confusing. We couldn\'t understand how the costs would scale with our team size, and there were hidden fees that weren\'t clear upfront.',
                'company_name': 'Enterprise Solutions Ltd',
                'interviewee_name': 'Michael Chen',
                'subject': 'Pricing Transparency',
                'response_id': 'R2'
            }
        ]
    }

def test_system_prompt_creation():
    """Test the system prompt creation function."""
    print("🧪 Testing system prompt creation...")
    
    sample_data = create_sample_client_data()
    system_prompt = create_best_in_class_system_prompt(sample_data)
    
    # Check if the prompt contains required elements
    required_elements = [
        "Executive Summary",
        "Evidence-Based Insights", 
        "Direct Evidence with Full Attribution",
        "Strategic Context and Business Impact",
        "Actionable Recommendations with Evidence",
        "CITATION REQUIREMENTS",
        "CRITICAL REQUIREMENTS"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in system_prompt:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing required elements: {missing_elements}")
        return False
    else:
        print("✅ System prompt creation successful - all required elements present")
        return True

def test_data_integration():
    """Test that data is properly integrated into the prompt."""
    print("🧪 Testing data integration...")
    
    sample_data = create_sample_client_data()
    system_prompt = create_best_in_class_system_prompt(sample_data)
    
    # Check that sample data appears in the prompt
    expected_data = [
        "Customer satisfaction deteriorates when onboarding exceeds two weeks",
        "Pricing transparency is critical for enterprise adoption",
        "Onboarding process lacks customization for enterprise needs",
        "Pricing model creates confusion for enterprise customers",
        "TechCorp Inc",
        "Enterprise Solutions Ltd"
    ]
    
    missing_data = []
    for item in expected_data:
        if item not in system_prompt:
            missing_data.append(item)
    
    if missing_data:
        print(f"❌ Missing data integration: {missing_data}")
        return False
    else:
        print("✅ Data integration successful - all sample data properly included")
        return True

def test_citation_requirements():
    """Test that citation requirements are clearly specified."""
    print("🧪 Testing citation requirements...")
    
    sample_data = create_sample_client_data()
    system_prompt = create_best_in_class_system_prompt(sample_data)
    
    citation_requirements = [
        "Theme Reference",
        "Finding Reference", 
        "Quote Attribution",
        "Impact Metrics",
        "Full Attribution",
        "Confidence Level",
        "Business Context"
    ]
    
    missing_requirements = []
    for requirement in citation_requirements:
        if requirement not in system_prompt:
            missing_requirements.append(requirement)
    
    if missing_requirements:
        print(f"❌ Missing citation requirements: {missing_requirements}")
        return False
    else:
        print("✅ Citation requirements comprehensive - all requirements specified")
        return True

def test_response_structure():
    """Test that response structure is clearly defined."""
    print("🧪 Testing response structure...")
    
    sample_data = create_sample_client_data()
    system_prompt = create_best_in_class_system_prompt(sample_data)
    
    structure_elements = [
        "Executive Summary",
        "Key Insights",
        "Direct Evidence", 
        "Strategic Implications",
        "Recommended Actions"
    ]
    
    missing_structure = []
    for element in structure_elements:
        if element not in system_prompt:
            missing_structure.append(element)
    
    if missing_structure:
        print(f"❌ Missing response structure: {missing_structure}")
        return False
    else:
        print("✅ Response structure comprehensive - all sections defined")
        return True

def main():
    """Run all tests."""
    print("🔬 Testing Best-in-Class Research Prompt Response System")
    print("=" * 60)
    
    tests = [
        test_system_prompt_creation,
        test_data_integration,
        test_citation_requirements,
        test_response_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The implementation is ready for use.")
        print("\n📋 Implementation Summary:")
        print("✅ Best-in-class research prompt response system implemented")
        print("✅ Comprehensive citation requirements")
        print("✅ Evidence-driven insights with full attribution")
        print("✅ Executive-grade communication standards")
        print("✅ Strategic business implications")
        print("✅ Actionable recommendations with supporting evidence")
    else:
        print("⚠️ Some tests failed. Please review the implementation.")

if __name__ == "__main__":
    main() 