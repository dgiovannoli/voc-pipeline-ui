"""
Modular Pipeline Processor
Allows independent execution of each pipeline stage for maximum flexibility.
"""

import os
import sys
import logging
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import prompts
try:
    from prompts import get_core_extraction_prompt, get_analysis_enrichment_prompt, get_labeling_prompt
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False

# Import database
try:
    from database import VOCDatabase
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Import LLM
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnableSequence
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

class ModularProcessor:
    """Modular processor for independent pipeline stages."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo-16k", max_tokens: int = 4096, temperature: float = 0.1):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        if not PROMPTS_AVAILABLE:
            raise ImportError("Prompts package not available")
        
        if not LLM_AVAILABLE:
            raise ImportError("LangChain not available")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Initialize database if available
        self.db = None
        if DB_AVAILABLE:
            try:
                self.db = VOCDatabase()
            except Exception as e:
                logger.warning(f"Database not available: {e}")
    
    def stage1_core_extraction(self, transcript_path: str, company: str, interviewee: str, 
                              deal_status: str, date_of_interview: str) -> List[Dict]:
        """
        Stage 1: Core extraction - extract verbatim responses and metadata only.
        
        Returns:
            List of dictionaries with core fields only
        """
        logger.info(f"Starting Stage 1: Core extraction from {transcript_path}")
        
        # Load transcript
        if transcript_path.lower().endswith(".docx"):
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(transcript_path)
            docs = loader.load()
            full_text = docs[0].page_content
        else:
            with open(transcript_path, encoding="utf-8") as f:
                full_text = f.read()
        
        if not full_text.strip():
            raise ValueError("Transcript is empty")
        
        # Create chunks (simplified chunking for now)
        chunks = self._create_chunks(full_text, target_tokens=7000, overlap_tokens=600)
        logger.info(f"Created {len(chunks)} chunks for processing")
        
        # Process each chunk
        all_responses = []
        for i, chunk in enumerate(chunks):
            try:
                response_id = f"{company}_{interviewee}_{i+1}"
                
                # Create prompt
                prompt_text = get_core_extraction_prompt(
                    response_id=response_id,
                    company=company,
                    interviewee_name=interviewee,
                    deal_status=deal_status,
                    date_of_interview=date_of_interview,
                    chunk_text=chunk
                )
                
                # Create chain
                prompt_template = PromptTemplate(
                    input_variables=["response_id", "company", "interviewee_name", "deal_status", "date_of_interview", "chunk_text"],
                    template=prompt_text
                )
                chain = prompt_template | self.llm
                
                # Get response
                result = chain.invoke({
                    "response_id": response_id,
                    "company": company,
                    "interviewee_name": interviewee,
                    "deal_status": deal_status,
                    "date_of_interview": date_of_interview,
                    "chunk_text": chunk
                })
                
                # Parse response
                if hasattr(result, 'content'):
                    response_text = result.content.strip()
                else:
                    response_text = str(result).strip()
                
                # Parse JSON
                try:
                    responses = json.loads(response_text)
                    if isinstance(responses, list):
                        all_responses.extend(responses)
                    else:
                        all_responses.append(responses)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from chunk {i}: {e}")
                    continue
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                continue
        
        logger.info(f"Stage 1 complete: extracted {len(all_responses)} responses")
        return all_responses
    
    def stage2_analysis_enrichment(self, core_responses: List[Dict]) -> List[Dict]:
        """
        Stage 2: Analysis enrichment - add AI-generated insights to core responses.
        
        Args:
            core_responses: List of dictionaries with core fields
            
        Returns:
            List of dictionaries with core fields + analysis fields
        """
        logger.info(f"Starting Stage 2: Analysis enrichment for {len(core_responses)} responses")
        
        enriched_responses = []
        
        for response in core_responses:
            try:
                # Create analysis prompt
                prompt_text = get_analysis_enrichment_prompt(
                    response_id=response['response_id'],
                    verbatim_response=response['verbatim_response'],
                    subject=response['subject'],
                    company=response['company'],
                    interviewee_name=response['interviewee_name']
                )
                
                # Create chain
                prompt_template = PromptTemplate(
                    input_variables=["response_id", "verbatim_response", "subject", "company", "interviewee_name"],
                    template=prompt_text
                )
                chain = prompt_template | self.llm
                
                # Get analysis
                result = chain.invoke({
                    "response_id": response['response_id'],
                    "verbatim_response": response['verbatim_response'],
                    "subject": response['subject'],
                    "company": response['company'],
                    "interviewee_name": response['interviewee_name']
                })
                
                # Parse response
                if hasattr(result, 'content'):
                    analysis_text = result.content.strip()
                else:
                    analysis_text = str(result).strip()
                
                # Parse JSON
                try:
                    analysis = json.loads(analysis_text)
                    
                    # Combine core response with analysis
                    enriched_response = {**response, **analysis}
                    enriched_responses.append(enriched_response)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse analysis JSON for {response['response_id']}: {e}")
                    # Keep original response without analysis
                    enriched_responses.append(response)
                
            except Exception as e:
                logger.error(f"Error enriching response {response['response_id']}: {e}")
                # Keep original response without analysis
                enriched_responses.append(response)
        
        logger.info(f"Stage 2 complete: enriched {len(enriched_responses)} responses")
        return enriched_responses
    
    def stage3_labeling(self, responses: List[Dict]) -> List[Dict]:
        """
        Stage 3: Labeling - add structured labels to responses.
        
        Args:
            responses: List of dictionaries with core fields (and optionally analysis fields)
            
        Returns:
            List of dictionaries with core fields + labels
        """
        logger.info(f"Starting Stage 3: Labeling for {len(responses)} responses")
        
        labeled_responses = []
        
        for response in responses:
            try:
                # Create labeling prompt
                prompt_text = get_labeling_prompt(
                    response_id=response['response_id'],
                    verbatim_response=response['verbatim_response'],
                    subject=response['subject'],
                    company=response['company'],
                    interviewee_name=response['interviewee_name']
                )
                
                # Create chain
                prompt_template = PromptTemplate(
                    input_variables=["response_id", "verbatim_response", "subject", "company", "interviewee_name"],
                    template=prompt_text
                )
                chain = prompt_template | self.llm
                
                # Get labels
                result = chain.invoke({
                    "response_id": response['response_id'],
                    "verbatim_response": response['verbatim_response'],
                    "subject": response['subject'],
                    "company": response['company'],
                    "interviewee_name": response['interviewee_name']
                })
                
                # Parse response
                if hasattr(result, 'content'):
                    labels_text = result.content.strip()
                else:
                    labels_text = str(result).strip()
                
                # Parse JSON
                try:
                    labels_data = json.loads(labels_text)
                    
                    # Combine response with labels
                    labeled_response = {**response, 'labels': labels_data.get('labels', {})}
                    labeled_responses.append(labeled_response)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse labels JSON for {response['response_id']}: {e}")
                    # Keep original response without labels
                    labeled_responses.append(response)
                
            except Exception as e:
                logger.error(f"Error labeling response {response['response_id']}: {e}")
                # Keep original response without labels
                labeled_responses.append(response)
        
        logger.info(f"Stage 3 complete: labeled {len(labeled_responses)} responses")
        return labeled_responses
    
    def save_to_database(self, responses: List[Dict]) -> int:
        """
        Save responses to database.
        
        Args:
            responses: List of response dictionaries
            
        Returns:
            Number of responses saved
        """
        if not self.db:
            logger.warning("Database not available")
            return 0
        
        saved_count = 0
        for response in responses:
            try:
                if self.db.save_response(response):
                    saved_count += 1
                else:
                    logger.warning(f"Failed to save response {response.get('response_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Error saving response {response.get('response_id', 'unknown')}: {e}")
        
        logger.info(f"Saved {saved_count} responses to database")
        return saved_count
    
    def _create_chunks(self, text: str, target_tokens: int = 7000, overlap_tokens: int = 600) -> List[str]:
        """Create text chunks for processing."""
        # Simple character-based chunking (can be improved with token-based chunking)
        chunk_size = target_tokens * 4  # Rough approximation
        overlap_size = overlap_tokens * 4
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > start + chunk_size * 0.8:  # Only break if we're not too far back
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk)
            start = end - overlap_size
        
        return chunks
    
    def run_full_pipeline(self, transcript_path: str, company: str, interviewee: str, 
                         deal_status: str, date_of_interview: str, 
                         save_to_db: bool = True) -> Dict[str, Any]:
        """
        Run the complete pipeline (all stages).
        
        Returns:
            Dictionary with results from each stage
        """
        logger.info("Starting full pipeline")
        
        # Stage 1: Core extraction
        core_responses = self.stage1_core_extraction(
            transcript_path, company, interviewee, deal_status, date_of_interview
        )
        
        # Stage 2: Analysis enrichment
        enriched_responses = self.stage2_analysis_enrichment(core_responses)
        
        # Stage 3: Labeling
        labeled_responses = self.stage3_labeling(enriched_responses)
        
        # Save to database if requested
        saved_count = 0
        if save_to_db:
            saved_count = self.save_to_database(labeled_responses)
        
        return {
            'stage1_core_count': len(core_responses),
            'stage2_enriched_count': len(enriched_responses),
            'stage3_labeled_count': len(labeled_responses),
            'database_saved_count': saved_count,
            'responses': labeled_responses
        } 