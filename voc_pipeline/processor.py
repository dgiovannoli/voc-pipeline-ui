import os
import sys
import logging
import click
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_text_splitters import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import csv
from io import StringIO

# Set up logging
logging.basicConfig(filename="qc.log",
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def _process_transcript_impl(
    transcript_path: str,
    client: str,
    company: str,
    interviewee: str,
    deal_status: str,
    date_of_interview: str,
) -> None:
    """
    Load the transcript, run the full Response Data Table prompt,
    and emit raw CSV to stdout.
    """
    # Load environment variables
    load_dotenv()
    
    # Debug: Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        return
    
    # Load transcript
    if transcript_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(transcript_path)
        # 1) Load full transcript
        docs = loader.load()
        full_text = docs[0].page_content
    else:
        full_text = open(transcript_path, encoding="utf-8").read()
    
    if not full_text.strip():
        print("ERROR: Transcript is empty")
        return
    
    # Create single-row-per-chunk prompt template (reverted from response_coder.py)
    prompt_template = PromptTemplate(
        input_variables=["response_id","chunk_text","company","company_name","interviewee_name","deal_status","date_of_interview"],
        template="""You are an expert qualitative coding analyst specializing in win-loss interview data extraction.

Analyze the provided interview chunk and extract ONE meaningful insight. Return ONLY a valid JSON object with this structure:

{{
  "response_id": "{response_id}",
  "verbatim_response": "{chunk_text}",
  "subject": "brief_subject_description",
  "question": "what_question_this_answers",
  "deal_status": "{deal_status}",
  "company": "{company}",
  "interviewee_name": "{interviewee_name}",
  "date_of_interview": "{date_of_interview}",
  "findings": "key_finding_summary",
  "value_realization": "value_or_roi_metrics",
  "implementation_experience": "implementation_details",
  "risk_mitigation": "risk_mitigation_approaches",
  "competitive_advantage": "competitive_positioning",
  "customer_success": "customer_success_factors",
  "product_feedback": "product_feature_feedback",
  "service_quality": "service_quality_assessment",
  "decision_factors": "decision_influencing_factors",
  "pain_points": "challenges_or_pain_points",
  "success_metrics": "success_criteria_and_metrics",
  "future_plans": "future_plans_or_expansion"
}}

Guidelines:
- Extract ONE primary insight per chunk
- Subject categories: Product Features, Process, Pricing, Support, Integration, Decision Making
- Use "N/A" for fields that don't apply
- Ensure all fields are populated
- Return ONLY the JSON object, no other text

Interview chunk to analyze:
{chunk_text}"""
    )
    
    # Create LLM chain (RunnableSequence) - using OpenAI instead of ChatOpenAI for consistency
    llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), max_tokens=800, temperature=0.1)
    chain = prompt_template | llm
    
    # 2) Split into smaller chunks to avoid token limits (~2k tokens w/ 100 overlap)
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    chunks = splitter.split_text(full_text)
    
    # 3) Run the single-row-per-chunk processing
    chunk_results = []
    
    def process_chunk(chunk_index, chunk):
        try:
            # Generate response ID
            response_id = f"{company}_response_{chunk_index + 1}"
            
            # Prepare input for the chain
            chain_input = {
                "chunk_text": chunk,
                "response_id": response_id,
                "company": company,
                "company_name": company,
                "interviewee_name": interviewee,
                "deal_status": deal_status,
                "date_of_interview": date_of_interview
            }
            
            # Get response from LLM
            raw = ""
            # up to 3 attempts to get valid JSON
            for _ in range(3):
                raw = chain.invoke(chain_input).strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    # Validate required fields
                    required_fields = ["response_id", "verbatim_response", "subject", "question", 
                                     "deal_status", "company", "interviewee_name", "date_of_interview"]
                    for field in required_fields:
                        if field not in obj:
                            raise ValueError(f"Missing required field: {field}")
                    
                    # Convert to CSV row
                    csv_row = [
                        obj.get("response_id", ""),
                        obj.get("verbatim_response", ""),
                        obj.get("subject", ""),
                        obj.get("question", ""),
                        obj.get("deal_status", ""),
                        obj.get("company", ""),
                        obj.get("interviewee_name", ""),
                        obj.get("date_of_interview", ""),
                        obj.get("findings", ""),
                        obj.get("value_realization", ""),
                        obj.get("implementation_experience", ""),
                        obj.get("risk_mitigation", ""),
                        obj.get("competitive_advantage", ""),
                        obj.get("customer_success", ""),
                        obj.get("product_feedback", ""),
                        obj.get("service_quality", ""),
                        obj.get("decision_factors", ""),
                        obj.get("pain_points", ""),
                        obj.get("success_metrics", ""),
                        obj.get("future_plans", "")
                    ]
                    
                    return (chunk_index, csv_row)
                except Exception as e:
                    # malformed JSON, retry
                    continue
            
            # if we reach here, skip this chunk
            logging.warning(f"Chunk {chunk_index} dropped: no valid LLM output — text: {chunk[:60].replace(chr(10), ' ')}")
            return (chunk_index, None)
            
        except Exception as e:
            logging.warning(f"Chunk {chunk_index} dropped: {e} — text: {chunk[:100]!r}")
            return (chunk_index, None)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {executor.submit(process_chunk, i, chunk): (i, chunk) for i, chunk in enumerate(chunks)}
        for future in as_completed(future_to_chunk):
            try:
                chunk_index, result = future.result()
                if result is not None:  # Only add successful results
                    chunk_results.append((chunk_index, result))
            except Exception as e:
                print(f"Error processing chunk: {e}")
    
    # 4) Sort by chunk index and write CSV
    chunk_results.sort(key=lambda x: x[0])
    
    # Write CSV header
    header = ["Response ID", "Verbatim Response", "Subject", "Question", "Deal Status", 
              "Company Name", "Interviewee Name", "Date of Interview", "Findings", 
              "Value_Realization", "Implementation_Experience", "Risk_Mitigation", 
              "Competitive_Advantage", "Customer_Success", "Product_Feedback", 
              "Service_Quality", "Decision_Factors", "Pain_Points", "Success_Metrics", "Future_Plans"]
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    
    # Write data rows
    for chunk_index, row in chunk_results:
        writer.writerow(row)
    
    # Log summary
    logging.info(f"Processed {len(chunks)} chunks → created {len(chunk_results)} rows; dropped {len(chunks) - len(chunk_results)} chunks")
    
    # Output CSV to stdout
    print(output.getvalue())


@click.command()
@click.option('--input', '-i', required=True, help='Input CSV file to validate')
@click.option('--output', '-o', required=True, help='Output CSV file for validated data')
def validate(input, output):
    """Validate processed CSV data."""
    print(f"Validating {input}...")
    
    import pandas as pd
    
    try:
        # Read the input CSV
        df = pd.read_csv(input)
        print(f"Read {len(df)} rows from {input}")
        
        # Basic validation - keep rows that have meaningful content
        if len(df) > 0:
            # Filter out rows with empty verbatim responses
            df_valid = df[df['Verbatim Response'].str.strip() != '']
            print(f"After validation: {len(df_valid)} rows")
            
            # Save validated data
            df_valid.to_csv(output, index=False)
            print(f"Validation complete. Output saved to {output}")
        else:
            print("No data to validate")
            # Create empty file with headers
            df.to_csv(output, index=False)
            
    except Exception as e:
        print(f"Error during validation: {e}")
        # Create empty output file with headers
        pd.DataFrame(columns=[
            "Response ID","Verbatim Response","Subject","Question",
            "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
            "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
            "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
            "Pain_Points","Success_Metrics","Future_Plans"
        ]).to_csv(output, index=False)


@click.command()
@click.option('--input', '-i', required=True, help='Input CSV file to process')
@click.option('--output', '-o', required=True, help='Output CSV file for final table')
def build_table(input, output):
    """Build final data table from processed data."""
    print(f"Building table from {input} to {output}...")
    
    import pandas as pd
    
    try:
        # Read the input CSV
        df = pd.read_csv(input)
        print(f"Read {len(df)} rows from {input}")
        
        if len(df) > 0:
            # Reorder columns to match the expected schema
            expected_columns = [
                "Response ID","Verbatim Response","Subject","Question",
                "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
                "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
                "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
                "Pain_Points","Success_Metrics","Future_Plans"
            ]
            
            # Ensure all expected columns exist
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Reorder columns
            df_final = df[expected_columns]
            
            # Save final table
            df_final.to_csv(output, index=False)
            print(f"Table building complete. Output saved to {output}")
        else:
            print("No data to process")
            # Create empty file with headers
            df.to_csv(output, index=False)
            
    except Exception as e:
        print(f"Error during table building: {e}")
        # Create empty output file with headers
        pd.DataFrame(columns=[
            "Response ID","Verbatim Response","Subject","Question",
            "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
            "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
            "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
            "Pain_Points","Success_Metrics","Future_Plans"
        ]).to_csv(output, index=False)


@click.command("process_transcript")
@click.argument('transcript_path')
@click.argument('client')
@click.argument('company')
@click.argument('interviewee')
@click.argument('deal_status')
@click.argument('date_of_interview')
def process_transcript(transcript_path, client, company, interviewee, deal_status, date_of_interview):
    """Process a transcript and output CSV data."""
    _process_transcript_impl(transcript_path, client, company, interviewee, deal_status, date_of_interview)


if __name__ == "__main__":
    process_transcript() 