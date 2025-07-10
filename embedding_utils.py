#!/usr/bin/env python3

"""
Embedding Utilities for VOC Pipeline

This module provides comprehensive embedding generation and vector similarity
functions for all stages of the VOC pipeline.
"""

import os
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
import openai
from supabase_database import SupabaseDatabase
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manages embedding generation and vector operations for the VOC pipeline"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        
        self.db = SupabaseDatabase()
        self.model = "text-embedding-ada-002"
        self.dimension = 1536
        
    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for a given text"""
        if not text or not text.strip():
            return None
            
        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                input=text.strip(),
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def get_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Get embeddings for a batch of texts"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                client = openai.OpenAI(api_key=self.api_key)
                response = client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}")
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}: {e}")
                # Add None for failed embeddings
                embeddings.extend([None] * len(batch))
        
        return embeddings
    
    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_similar_items(self, query_embedding: List[float], 
                          item_embeddings: List[List[float]], 
                          threshold: float = 0.8) -> List[int]:
        """Find items similar to query embedding"""
        similar_indices = []
        
        for i, item_embedding in enumerate(item_embeddings):
            if item_embedding is None:
                continue
                
            similarity = self.calculate_cosine_similarity(query_embedding, item_embedding)
            if similarity >= threshold:
                similar_indices.append(i)
        
        return similar_indices
    
    def update_core_response_embeddings(self, client_id: str = 'default', 
                                       batch_size: int = 50) -> Dict:
        """Update embeddings for all core_responses for a client"""
        logger.info(f"🔄 Updating core response embeddings for client {client_id}")
        
        try:
            # Get all core responses without embeddings
            response = self.db.supabase.table('core_responses').select(
                'response_id,verbatim_response,embedding'
            ).eq('client_id', client_id).execute()
            
            if not response.data:
                logger.info("No core responses found")
                return {"status": "no_data", "updated": 0, "errors": 0}
            
            # Filter responses that need embeddings
            needs_embedding = []
            for row in response.data:
                if row.get('embedding') is None and row.get('verbatim_response'):
                    needs_embedding.append(row)
            
            if not needs_embedding:
                logger.info("All core responses already have embeddings")
                return {"status": "already_complete", "updated": 0, "errors": 0}
            
            logger.info(f"Found {len(needs_embedding)} responses needing embeddings")
            
            # Process in batches
            updated_count = 0
            error_count = 0
            
            for i in range(0, len(needs_embedding), batch_size):
                batch = needs_embedding[i:i + batch_size]
                
                # Generate embeddings
                texts = [row['verbatim_response'] for row in batch]
                embeddings = self.get_embeddings_batch(texts)
                
                # Update database
                for j, (row, embedding) in enumerate(zip(batch, embeddings)):
                    if embedding is not None:
                        try:
                            self.db.supabase.table('core_responses').update({
                                'embedding': embedding
                            }).eq('response_id', row['response_id']).execute()
                            updated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to update embedding for {row['response_id']}: {e}")
                            error_count += 1
                    else:
                        error_count += 1
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(needs_embedding) + batch_size - 1)//batch_size}")
            
            logger.info(f"✅ Core response embeddings complete: {updated_count} updated, {error_count} errors")
            return {
                "status": "success", 
                "updated": updated_count, 
                "errors": error_count,
                "total_processed": len(needs_embedding)
            }
            
        except Exception as e:
            logger.error(f"Failed to update core response embeddings: {e}")
            return {"status": "error", "message": str(e), "updated": 0, "errors": 0}
    
    def update_quote_analysis_embeddings(self, client_id: str = 'default', 
                                        batch_size: int = 50) -> Dict:
        """Update embeddings for quote_analysis relevance_explanation field"""
        logger.info(f"🔄 Updating quote analysis embeddings for client {client_id}")
        
        try:
            # Get all quote analysis without embeddings
            response = self.db.supabase.table('quote_analysis').select(
                'analysis_id,relevance_explanation,embedding'
            ).eq('client_id', client_id).execute()
            
            if not response.data:
                logger.info("No quote analysis found")
                return {"status": "no_data", "updated": 0, "errors": 0}
            
            # Filter records that need embeddings
            needs_embedding = []
            for row in response.data:
                if row.get('embedding') is None and row.get('relevance_explanation'):
                    needs_embedding.append(row)
            
            if not needs_embedding:
                logger.info("All quote analysis already have embeddings")
                return {"status": "already_complete", "updated": 0, "errors": 0}
            
            logger.info(f"Found {len(needs_embedding)} quote analyses needing embeddings")
            
            # Process in batches
            updated_count = 0
            error_count = 0
            
            for i in range(0, len(needs_embedding), batch_size):
                batch = needs_embedding[i:i + batch_size]
                
                # Generate embeddings
                texts = [row['relevance_explanation'] for row in batch]
                embeddings = self.get_embeddings_batch(texts)
                
                # Update database
                for j, (row, embedding) in enumerate(zip(batch, embeddings)):
                    if embedding is not None:
                        try:
                            self.db.supabase.table('quote_analysis').update({
                                'embedding': embedding
                            }).eq('analysis_id', row['analysis_id']).execute()
                            updated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to update embedding for analysis {row['analysis_id']}: {e}")
                            error_count += 1
                    else:
                        error_count += 1
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(needs_embedding) + batch_size - 1)//batch_size}")
            
            logger.info(f"✅ Quote analysis embeddings complete: {updated_count} updated, {error_count} errors")
            return {
                "status": "success", 
                "updated": updated_count, 
                "errors": error_count,
                "total_processed": len(needs_embedding)
            }
            
        except Exception as e:
            logger.error(f"Failed to update quote analysis embeddings: {e}")
            return {"status": "error", "message": str(e), "updated": 0, "errors": 0}
    
    def update_scorecard_theme_embeddings(self, client_id: str = 'default', 
                                         batch_size: int = 50) -> Dict:
        """Update embeddings for scorecard themes"""
        logger.info(f"🔄 Updating scorecard theme embeddings for client {client_id}")
        
        try:
            # Get all scorecard themes without embeddings
            response = self.db.supabase.table('scorecard_themes').select(
                'id,theme_title,client_performance_summary,embedding'
            ).eq('client_id', client_id).execute()
            
            if not response.data:
                logger.info("No scorecard themes found")
                return {"status": "no_data", "updated": 0, "errors": 0}
            
            # Filter themes that need embeddings
            needs_embedding = []
            for row in response.data:
                if row.get('embedding') is None:
                    # Combine title and summary for embedding
                    text = f"{row.get('theme_title', '')} {row.get('client_performance_summary', '')}"
                    if text.strip():
                        needs_embedding.append((row, text))
            
            if not needs_embedding:
                logger.info("All scorecard themes already have embeddings")
                return {"status": "already_complete", "updated": 0, "errors": 0}
            
            logger.info(f"Found {len(needs_embedding)} themes needing embeddings")
            
            # Process in batches
            updated_count = 0
            error_count = 0
            
            for i in range(0, len(needs_embedding), batch_size):
                batch = needs_embedding[i:i + batch_size]
                
                # Generate embeddings
                texts = [text for _, text in batch]
                embeddings = self.get_embeddings_batch(texts)
                
                # Update database
                for j, ((row, _), embedding) in enumerate(zip(batch, embeddings)):
                    if embedding is not None:
                        try:
                            self.db.supabase.table('scorecard_themes').update({
                                'embedding': embedding
                            }).eq('id', row['id']).execute()
                            updated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to update embedding for theme {row['id']}: {e}")
                            error_count += 1
                    else:
                        error_count += 1
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(needs_embedding) + batch_size - 1)//batch_size}")
            
            logger.info(f"✅ Scorecard theme embeddings complete: {updated_count} updated, {error_count} errors")
            return {
                "status": "success", 
                "updated": updated_count, 
                "errors": error_count,
                "total_processed": len(needs_embedding)
            }
            
        except Exception as e:
            logger.error(f"Failed to update scorecard theme embeddings: {e}")
            return {"status": "error", "message": str(e), "updated": 0, "errors": 0}
    
    def backfill_all_embeddings(self, client_id: str = 'default') -> Dict:
        """Backfill embeddings for all tables"""
        logger.info(f"🚀 Starting complete embedding backfill for client {client_id}")
        
        results = {
            "core_responses": self.update_core_response_embeddings(client_id),
            "quote_analysis": self.update_quote_analysis_embeddings(client_id),
            "scorecard_themes": self.update_scorecard_theme_embeddings(client_id)
        }
        
        total_updated = sum(r.get('updated', 0) for r in results.values())
        total_errors = sum(r.get('errors', 0) for r in results.values())
        
        logger.info(f"🎉 Complete embedding backfill finished:")
        logger.info(f"  Total updated: {total_updated}")
        logger.info(f"  Total errors: {total_errors}")
        
        return {
            "status": "complete",
            "results": results,
            "total_updated": total_updated,
            "total_errors": total_errors
        }

def run_embedding_backfill(client_id: str = 'default'):
    """Run complete embedding backfill for a client"""
    manager = EmbeddingManager()
    return manager.backfill_all_embeddings(client_id)

if __name__ == "__main__":
    import sys
    
    client_id = sys.argv[1] if len(sys.argv) > 1 else 'default'
    result = run_embedding_backfill(client_id)
    print(f"Backfill result: {result}") 