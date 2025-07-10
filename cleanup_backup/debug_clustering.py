#!/usr/bin/env python3

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage, fcluster
from sentence_transformers import SentenceTransformer
from supabase_database import create_supabase_database

def debug_clustering():
    """Debug the clustering issue"""
    
    # Get findings
    db = create_supabase_database()
    findings_df = db.get_stage3_findings('Rev')
    
    print(f"Found {len(findings_df)} findings")
    print(f"Columns: {findings_df.columns.tolist()}")
    
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
    
    # Test cluster analysis
    print("Testing cluster analysis...")
    findings_df = findings_df.copy()
    findings_df['cluster_id'] = labels
    
    clusters = []
    min_companies = 2
    min_findings = 1
    
    for cluster_id in sorted(set(labels)):
        print(f"Processing cluster {cluster_id}")
        cluster_findings = findings_df[findings_df['cluster_id'] == cluster_id]
        
        print(f"  Cluster {cluster_id}: {cluster_findings.shape[0]} findings")
        
        if cluster_findings.shape[0] < min_findings:
            print(f"  Skipping cluster {cluster_id} - insufficient findings")
            continue
        
        # Get unique companies
        print(f"  Checking companies for cluster {cluster_id}")
        if 'company' in cluster_findings.columns:
            companies = cluster_findings['company'].dropna().unique().tolist()
        else:
            companies = []
        print(f"  Companies: {companies}")
        
        if len(companies) < min_companies:
            print(f"  Skipping cluster {cluster_id} - insufficient companies")
            continue
        
        # Calculate metrics
        print(f"  Calculating metrics for cluster {cluster_id}")
        if 'confidence_score' in cluster_findings.columns and not cluster_findings['confidence_score'].isnull().all():
            avg_confidence = float(cluster_findings['confidence_score'].mean())
        else:
            avg_confidence = 0.0
            
        if 'impact_score' in cluster_findings.columns and not cluster_findings['impact_score'].isnull().all():
            avg_impact = float(cluster_findings['impact_score'].mean())
        else:
            avg_impact = 0.0
        
        print(f"  Metrics: confidence={avg_confidence}, impact={avg_impact}")
        
        # Create cluster analysis
        cluster_analysis = {
            'cluster_id': cluster_id,
            'companies': companies,
            'company_count': len(companies),
            'finding_count': int(cluster_findings.shape[0]),
            'avg_confidence': avg_confidence,
            'avg_impact_score': avg_impact,
            'supporting_quotes': cluster_findings['description'].dropna().tolist() if 'description' in cluster_findings.columns else []
        }
        
        clusters.append(cluster_analysis)
        print(f"  Added cluster {cluster_id} to analysis")
    
    print(f"✅ Analyzed {len(clusters)} valid clusters")

if __name__ == "__main__":
    debug_clustering() 