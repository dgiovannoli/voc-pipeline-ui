#!/usr/bin/env python3
import pandas as pd
import argparse
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

def main():
    parser = argparse.ArgumentParser(description="Generate full data table from transcript")
    parser.add_argument(
        "--transcript",
        required=True,
        help="Path to transcript file (.docx or .txt)"
    )
    parser.add_argument(
        "--client",
        required=True,
        help="Client name"
    )
    parser.add_argument(
        "--company",
        required=True,
        help="Company name"
    )
    parser.add_argument(
        "--interviewee",
        required=True,
        help="Interviewee name"
    )
    parser.add_argument(
        "--deal-status",
        required=True,
        help="Deal status"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Date of interview"
    )
    parser.add_argument(
        "--output",
        default="response_data_table.csv",
        help="Output CSV file path"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Load transcript
    transcript_path = args.transcript
    if transcript_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(transcript_path)
        full_text = loader.load()[0].page_content
    else:
        full_text = open(transcript_path, encoding="utf-8").read()
    
    # Create prompt template
    prompt_template = PromptTemplate(
        input_variables=["transcript","client","company","interviewee","deal_status","date"],
        template="""
<role>
You are a Voice of Customer (VoC) data analyst specializing in extracting structured insights from customer interview transcripts. Your task is to analyze interview content and generate a comprehensive data table that captures customer feedback, pain points, and insights in a structured format.
</role>

<context>
You are processing a customer interview transcript to extract valuable insights for product development, customer success, and business strategy. The transcript contains a conversation between an interviewer and a customer (interviewee) discussing their experience with a product or service.
</context>

<task>
Analyze the provided interview transcript and generate a CSV-formatted data table with the following structure:

1. **Response ID**: A unique identifier for each response (format: {company}_response_1, {company}_response_2, etc.)
2. **Verbatim Response**: The exact quote or response from the transcript
3. **Subject**: Brief categorization of what the response is about (e.g., "Product Features", "Customer Service", "Pricing", "Implementation", "ROI", "Pain Points", "Success Metrics")
4. **Question**: What question or topic this response addresses (e.g., "What challenges did you face?", "How has the product helped?", "What would you improve?")
5. **Deal Status**: The current status of the customer relationship
6. **Company Name**: The customer's company name
7. **Interviewee Name**: The name of the person being interviewed
8. **Date of Interview**: The date when the interview was conducted

Guidelines:
- Extract meaningful, substantive responses and insights
- Avoid filler words, greetings, or non-substantive content
- Each row should represent a distinct insight or response
- Use clear, concise subject categories
- Ensure verbatim responses are accurate and complete
- Maintain proper CSV formatting with quotes around fields containing commas
</task>

<execution_instructions>
1. Read through the entire transcript carefully
2. Identify all substantive responses and insights
3. For each response, create a row with the required fields
4. Generate a properly formatted CSV with headers
5. Ensure all fields are populated correctly
6. Use the provided metadata (client, company, interviewee, deal_status, date) consistently
</execution_instructions>

<output_format>
Generate a CSV file with the following structure:

"Response ID","Verbatim Response","Subject","Question","Deal Status","Company Name","Interviewee Name","Date of Interview"
"{company}_response_1","[exact quote from transcript]","[subject category]","[question addressed]","{deal_status}","{company}","{interviewee}","{date}"
"{company}_response_2","[exact quote from transcript]","[subject category]","[question addressed]","{deal_status}","{company}","{interviewee}","{date}"
...

Example:
"AcmeCorp_response_1","The implementation was much smoother than we expected. The team was very responsive and helped us get up and running quickly.","Implementation","How was the implementation process?","Closed Won","Acme Corporation","John Smith","2024-01-15"
"AcmeCorp_response_2","We've seen a 40% reduction in processing time since switching to this solution.","ROI","What measurable benefits have you seen?","Closed Won","Acme Corporation","John Smith","2024-01-15"
</output_format>

<transcript>
{transcript}
</transcript>

<metadata>
Client: {client}
Company: {company}
Interviewee: {interviewee}
Deal Status: {deal_status}
Date: {date}
</metadata>

Please generate the complete CSV data table based on the transcript above.
"""
    )
    
    # Create LLM chain
    llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0.0)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    # Run the chain
    raw_csv = chain.run(
        transcript=full_text,
        client=args.client,
        company=args.company,
        interviewee=args.interviewee,
        deal_status=args.deal_status,
        date=args.date,
    )
    
    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(raw_csv.strip())
    
    print(f"✅ Wrote full data table to {args.output}")

if __name__ == "__main__":
    main() 