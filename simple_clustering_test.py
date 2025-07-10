#!/usr/bin/env python3

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage, fcluster
from sentence_transformers import SentenceTransformer
from supabase_database import create_supabase_database

def simple_clustering_test():
    """Simple clustering test to isolate the issue"""
    
    # Get findings
    db = create_supabase_database()
    findings_df = db.get_enhanced_findings('Rev')
    
    print(f"Found {len(findings_df)} findings")
    
    if findings_df.empty:
        print("No findings found!")
        return
    
    # Get finding descriptions
    findings_text = findings_df['description'].tolist()
    
    # Load embeddings model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(findings_text)
    
    # Compute similarity matrix
    print("Computing similarity matrix...")
    similarity_matrix = cosine_similarity(embeddings)
    
    # Convert to distance matrix
    distance_matrix = 1 - similarity_matrix
    
    # Perform clustering
    print("Performing clustering...")
    Z = linkage(distance_matrix, method='average')
    labels = fcluster(Z, t=0.3, criterion='distance')
    
    print(f"Clustering complete: {len(set(labels))} clusters")
    
    # Simple cluster analysis without complex checks
    print("Testing simple cluster analysis...")
    findings_df = findings_df.copy()
    findings_df['cluster_id'] = labels
    
    clusters = []
    
    for cluster_id in sorted(set(labels)):
        print(f"Processing cluster {cluster_id}")
        cluster_findings = findings_df[findings_df['cluster_id'] == cluster_id]
        
        print(f"  Cluster {cluster_id}: {cluster_findings.shape[0]} findings")
        
        # Simple cluster analysis
        cluster_analysis = {
            'cluster_id': cluster_id,
            'finding_count': int(cluster_findings.shape[0]),
            'supporting_quotes': cluster_findings['description'].tolist(),
            'companies': [],  # Skip company analysis for now
            'company_count': 0,
            'avg_confidence': 0.0,
            'avg_impact_score': 0.0,
            'competitive_flag': False
        }
        
        clusters.append(cluster_analysis)
        print(f"  Added cluster {cluster_id} to analysis")
    
    print(f"✅ Analyzed {len(clusters)} clusters")
    
    # Test theme generation
    print("Testing theme generation...")
    for cluster in clusters[:3]:  # Test first 3 clusters
        print(f"Cluster {cluster['cluster_id']}: {cluster['finding_count']} findings")
        print(f"  Sample quote: {cluster['supporting_quotes'][0][:100]}...")

if __name__ == "__main__":
    simple_clustering_test() 