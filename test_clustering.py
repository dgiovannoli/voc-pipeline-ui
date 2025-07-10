#!/usr/bin/env python3
"""
Simple clustering test for findings
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
from supabase_database import create_supabase_database
from sentence_transformers import SentenceTransformer

def test_clustering():
    """Test clustering on findings"""
    
    # Get findings
    db = create_supabase_database()
    findings_df = db.get_enhanced_findings('Rev')
    
    if findings_df.empty:
        print("No findings found!")
        return
    
    print(f"Found {len(findings_df)} findings")
    
    # Get finding descriptions
    findings_text = findings_df['description'].tolist()
    
    # Load embeddings model (use the same one as your pipeline)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(findings_text)
    
    # Compute similarity matrix
    print("Computing similarity matrix...")
    similarity_matrix = cosine_similarity(embeddings)
    
    # Convert to distance matrix
    distance_matrix = 1 - similarity_matrix
    
    # Test different clustering thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    
    print("\n=== CLUSTERING RESULTS ===")
    for threshold in thresholds:
        # Perform agglomerative clustering
        Z = linkage(distance_matrix, method='average')
        labels = fcluster(Z, t=threshold, criterion='distance')
        
        # Count clusters
        n_clusters = len(set(labels))
        
        # Get cluster sizes
        cluster_sizes = [list(labels).count(i) for i in set(labels)]
        min_size = min(cluster_sizes) if cluster_sizes else 0
        max_size = max(cluster_sizes) if cluster_sizes else 0
        
        print(f"Threshold {threshold}: {n_clusters} clusters (size range: {min_size}-{max_size})")
        
        # Show sample clusters if we have any
        if n_clusters > 0 and n_clusters < 20:  # Don't show too many
            print(f"  Sample clusters:")
            for i in range(1, min(n_clusters + 1, 6)):  # Show first 5 clusters
                cluster_findings = findings_df[labels == i]
                if len(cluster_findings) > 0:
                    sample_text = cluster_findings.iloc[0]['description'][:100] + "..."
                    print(f"    Cluster {i} ({len(cluster_findings)} findings): {sample_text}")
            print()

if __name__ == "__main__":
    test_clustering() 