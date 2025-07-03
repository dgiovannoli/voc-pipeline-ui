import os
import sys
import logging
import click
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader
from langchain_openai import ChatOpenAI
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
    
    # Create prompt template
    prompt_template = PromptTemplate(
        input_variables=["transcript","client","company","interviewee","deal_status","date"],
        template="""
You are an expert qualitative-coding assistant. **Respond with _only_ a well-formed CSV table** (header + rows), no explanations, markdown, or extra text.

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
9. **Findings**: A one-sentence "Key Finding" summarizing the main insight from this response
10. **Value_Realization**: Specific value or ROI metrics mentioned
11. **Implementation_Experience**: Details about implementation process and experience
12. **Risk_Mitigation**: How risks were addressed or mitigated
13. **Competitive_Advantage**: Competitive positioning or advantages mentioned
14. **Customer_Success**: Customer success factors and outcomes
15. **Product_Feedback**: Specific product feature feedback
16. **Service_Quality**: Service and support quality assessment
17. **Decision_Factors**: Key factors that influenced the decision
18. **Pain_Points**: Challenges or pain points identified
19. **Success_Metrics**: Success criteria and measurement approaches
20. **Future_Plans**: Future plans or expansion intentions

Guidelines:
- Extract meaningful, substantive responses and insights
- Avoid filler words, greetings, or non-substantive content
- Each row should represent a distinct insight or response
- Use clear, concise subject categories
- Ensure verbatim responses are accurate and complete
- For each chunk, after the structured fields, generate a one-sentence "Key Finding" summarizing the main insight
- Populate all additional insight columns based on the content analysis
- Maintain proper CSV formatting with quotes around fields containing commas
</task>

<execution_instructions>
1. Read through the entire transcript carefully
2. Identify all substantive responses and insights
3. For each response, create a row with the required fields
4. Generate a properly formatted CSV with headers
5. Ensure all fields are populated correctly
6. Use the provided metadata (client, company, interviewee, deal_status, date) consistently
7. Analyze each response for the additional insight categories and populate accordingly
</execution_instructions>

<output_format>
Generate a CSV file with the following structure:

"Response ID","Verbatim Response","Subject","Question","Deal Status","Company Name","Interviewee Name","Date of Interview","Findings","Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage","Customer_Success","Product_Feedback","Service_Quality","Decision_Factors","Pain_Points","Success_Metrics","Future_Plans"
"{company}_response_1","[exact quote from transcript]","[subject category]","[question addressed]","{deal_status}","{company}","{interviewee}","{date}","[key finding summary]","[value metrics]","[implementation details]","[risk mitigation]","[competitive info]","[success factors]","[product feedback]","[service quality]","[decision factors]","[pain points]","[success metrics]","[future plans]"
"{company}_response_2","[exact quote from transcript]","[subject category]","[question addressed]","{deal_status}","{company}","{interviewee}","{date}","[key finding summary]","[value metrics]","[implementation details]","[risk mitigation]","[competitive info]","[success factors]","[product feedback]","[service quality]","[decision factors]","[pain points]","[success metrics]","[future plans]"
...

Example:
"AcmeCorp_response_1","The implementation was much smoother than we expected. The team was very responsive and helped us get up and running quickly.","Implementation","How was the implementation process?","Closed Won","Acme Corporation","John Smith","2024-01-15","Implementation process exceeded expectations with responsive team support","40% time savings","Smooth onboarding with responsive team","Minimal disruption to operations","Superior implementation support","Quick time-to-value","Excellent implementation experience","Outstanding support quality","Implementation ease was key","Initial complexity concerns","Time-to-value metrics","Planning expansion to other departments"
"AcmeCorp_response_2","We've seen a 40% reduction in processing time since switching to this solution.","ROI","What measurable benefits have you seen?","Closed Won","Acme Corporation","John Smith","2024-01-15","40% reduction in processing time demonstrates significant efficiency gains","40% processing time reduction","Efficient transition process","Data migration risks addressed","Performance advantage over competitors","Improved operational efficiency","High performance product","Reliable service delivery","ROI and efficiency gains","Processing bottlenecks eliminated","Processing time metrics","Scaling to additional workflows"
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
    
    # Create LLM chain (RunnableSequence)
    llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0.0, model="gpt-4o-mini")
    chain = prompt_template | llm
    
    # 2) Split into safe‐size chunks (~3k tokens w/ 200 overlap)
    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    
    # 3) Run the CSV‐generation chain on each chunk with parallel processing
    chunk_results = []
    
    def process_chunk(chunk_index, chunk):
        try:
            response = chain.invoke({
                "transcript": chunk,
                "client": client,
                "company": company,
                "interviewee": interviewee,
                "deal_status": deal_status,
                "date": date_of_interview,
            })
            raw_csv = response.content if hasattr(response, 'content') else str(response)
            if not raw_csv.strip():
                raise ValueError("empty response")
            
            # Verify column count after generation
            lines = raw_csv.strip().splitlines()
            reader = csv.reader(lines)
            validated_lines = []
            for i, row in enumerate(reader, start=1):
                if len(row) < 20:
                    raise ValueError(f"Bad row #{i}: expected at least 20 columns but got {len(row)} → {row}")
                # If more than 20 columns, truncate to first 20
                if len(row) > 20:
                    row = row[:20]
                validated_lines.append(row)
            
            # Reconstruct CSV with validated rows
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerows(validated_lines)
            raw_csv = output.getvalue()
            
            return (chunk_index, raw_csv)
        except Exception as e:
            logging.warning(f"Chunk {chunk_index} dropped: {e} — text: {chunk[:100]!r}")
            return (chunk_index, None)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {executor.submit(process_chunk, i, chunk): (i, chunk) for i, chunk in enumerate(chunks)}
        for future in as_completed(future_to_chunk):
            try:
                chunk_index, part = future.result()
                if part is not None:  # Only add successful results
                    chunk_results.append((chunk_index, part))
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue
    
    # 4) Parse CSV parts and create DataFrame
    # Define expected columns
    expected_columns = [
        "Response ID","Verbatim Response","Subject","Question",
        "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
        "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
        "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
        "Pain_Points","Success_Metrics","Future_Plans"
    ]
    
    # Sort results by chunk index to maintain order
    chunk_results.sort(key=lambda x: x[0])
    
    # Collect all rows for DataFrame
    all_rows = []
    
    # Process each chunk's CSV output
    for chunk_index, raw_csv in chunk_results:
        if not raw_csv.strip():
            continue
        
        rows = raw_csv.strip().splitlines()
        # Skip header line if present
        if rows and rows[0].startswith('"Response ID"'):
            rows = rows[1:]
        
        # Process each row in the chunk
        for row_num, line in enumerate(rows):
            if not line.strip():
                continue
            
            try:
                # Parse the CSV line
                reader = csv.reader([line])
                row_data = next(reader)
                
                # Validate we have enough columns
                if len(row_data) < len(expected_columns):
                    print(f"Warning: Row has {len(row_data)} columns, expected {len(expected_columns)}")
                    continue
                
                # Compute unique response ID: company_chunk_row
                unique_response_id = f"{company}_{chunk_index+1}_{row_num+1}"
                
                # Replace the response ID in the first column
                row_data[0] = unique_response_id
                
                # Add the row to our collection
                all_rows.append(row_data[:len(expected_columns)])
                
            except Exception as e:
                print(f"Error parsing row in chunk {chunk_index+1}, row {row_num+1}: {e}")
                continue
    
    # Emit raw CSV to stdout
    # Write header
    sys.stdout.write(','.join(f'"{col}"' for col in expected_columns) + '\n')
    
    # Write all rows
    for row_data in all_rows:
        sys.stdout.write(','.join(f'"{field}"' for field in row_data) + '\n')
    
    # Log summary statistics
    total_chunks = len(chunks)
    total_rows = len(all_rows)
    dropped = total_chunks - len(chunk_results)
    logging.info(f"Processed {total_chunks} chunks → created {total_rows} rows; dropped {dropped} chunks")


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