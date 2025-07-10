import pandas as pd
import difflib
from typing import List, Dict, Any

def deduplicate_findings(findings: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Deduplicate findings using fuzzy string matching.
    """
    if not findings:
        return []
    
    # Extract finding statements
    statements = []
    for finding in findings:
        statement = finding.get('Finding_Statement', '').strip()
        statements.append(statement)
    
    # Group similar findings
    groups = []
    used_indices = set()
    
    for i, statement in enumerate(statements):
        if i in used_indices:
            continue
            
        # Start a new group
        group = [findings[i]]
        used_indices.add(i)
        
        # Find similar statements
        for j, other_statement in enumerate(statements):
            if j in used_indices or i == j:
                continue
                
            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, statement.lower(), other_statement.lower()).ratio()
            
            if similarity >= similarity_threshold:
                group.append(findings[j])
                used_indices.add(j)
        
        groups.append(group)
    
    # Merge groups into single findings
    deduplicated = []
    for group in groups:
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Merge multiple findings
            merged = group[0].copy()
            merged['Finding_Statement'] = f"MERGED: {group[0]['Finding_Statement']}"
            merged['Supporting_Response_IDs'] = ';'.join([f.get('Supporting_Response_IDs', '') for f in group])
            merged['Quote_Attributions'] = ';'.join([f.get('Quote_Attributions', '') for f in group])
            deduplicated.append(merged)
    
    return deduplicated

def main():
    # Load the Gold Standard CSV
    df = pd.read_csv('Context/Findings Data All.csv')
    
    print(f"Original Gold Standard findings: {len(df)}")
    
    # Convert to list of dicts
    findings = df.to_dict('records')
    
    # Test different similarity thresholds
    thresholds = [0.95, 0.90, 0.85, 0.80, 0.75]
    
    for threshold in thresholds:
        deduplicated = deduplicate_findings(findings, threshold)
        print(f"With {threshold} threshold: {len(deduplicated)} unique findings")
        
        # Show some examples of merged findings
        merged_count = len(findings) - len(deduplicated)
        if merged_count > 0:
            print(f"  - {merged_count} findings were merged")
            
            # Show first few merged findings
            merged_findings = [f for f in deduplicated if f['Finding_Statement'].startswith('MERGED')]
            for i, finding in enumerate(merged_findings[:3]):
                print(f"    Example {i+1}: {finding['Finding_Statement'][:100]}...")
    
    print(f"\nGold Standard Analysis:")
    print(f"  - Original: {len(df)} findings")
    print(f"  - Target: 57 findings")
    print(f"  - Our current approach: 119 findings (without deduplication)")
    
    # Test with 0.85 threshold (same as our pipeline)
    final_deduplicated = deduplicate_findings(findings, 0.85)
    print(f"  - Gold Standard with 0.85 deduplication: {len(final_deduplicated)} findings")
    
    if len(final_deduplicated) <= 57:
        print(f"  ✅ Gold Standard would meet target with deduplication!")
    else:
        print(f"  ❌ Gold Standard would still exceed target with deduplication")

if __name__ == "__main__":
    main() 