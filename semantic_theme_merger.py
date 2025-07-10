#!/usr/bin/env python3
"""
Semantic Theme Merger with Enrichment
Merges semantically similar stage4_themes and creates richer, more comprehensive stage4_themes
"""

import pandas as pd
import logging
from typing import List, Dict, Tuple
from supabase_database import create_supabase_database
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def analyze_current_stage4_themes():
    """Analyze current stage4_themes in the database"""
    try:
        supabase_db = create_supabase_database()
        
        # Get all scorecard stage4_themes
        response = supabase_db.supabase.table('scorecard_stage4_themes').select('*').execute()
        
        if not response.data:
            logger.warning("No stage4_themes found in database")
            return None
        
        df = pd.DataFrame(response.data)
        logger.info(f"Found {len(df)} stage4_themes in database")
        
        return df
        
    except Exception as e:
        logger.error(f"Error analyzing stage4_themes: {e}")
        return None

def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing common words and punctuation"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    words = text.split()
    words = [word for word in words if word not in common_words and len(word) > 2]
    
    return ' '.join(words)

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using word overlap"""
    norm1 = set(normalize_text(text1).split())
    norm2 = set(normalize_text(text2).split())
    
    if not norm1 or not norm2:
        return 0.0
    
    intersection = norm1.intersection(norm2)
    union = norm1.union(norm2)
    
    return len(intersection) / len(union)

def find_similar_theme_groups(df: pd.DataFrame, similarity_threshold: float = 0.3) -> List[List[int]]:
    """Find groups of similar stage4_themes based on title similarity"""
    similar_groups = []
    processed = set()
    
    for i, row1 in df.iterrows():
        if i in processed:
            continue
            
        group = [i]
        processed.add(i)
        
        for j, row2 in df.iterrows():
            if j in processed:
                continue
                
            similarity = calculate_similarity(row1['theme_title'], row2['theme_title'])
            
            if similarity >= similarity_threshold:
                group.append(j)
                processed.add(j)
        
        if len(group) > 1:  # Only add groups with multiple stage4_themes
            similar_groups.append(group)
    
    return similar_groups

def merge_theme_group(df: pd.DataFrame, group_indices: List[int]) -> Dict:
    """Merge a group of similar stage4_themes into one enriched theme"""
    group_df = df.loc[group_indices]
    
    # Get the theme with highest quality score as the base
    base_theme = group_df.loc[group_df['overall_quality_score'].idxmax()]
    
    # Create enriched title
    titles = group_df['theme_title'].tolist()
    enriched_title = create_enriched_title(titles, base_theme['scorecard_criterion'])
    
    # Aggregate data
    all_companies = set()
    total_quotes = 0
    quality_scores = []
    impact_scores = []
    sentiments = set()
    
    for _, theme in group_df.iterrows():
        # Companies (union)
        if pd.notna(theme.get('companies_represented')):
            all_companies.add(theme['companies_represented'])
        
        # Quotes (sum)
        if pd.notna(theme.get('quotes_count')):
            total_quotes += theme['quotes_count']
        
        # Quality scores (for averaging)
        if pd.notna(theme.get('overall_quality_score')):
            quality_scores.append(theme['overall_quality_score'])
        
        # Impact scores (for averaging)
        if pd.notna(theme.get('impact_score')):
            impact_scores.append(theme['impact_score'])
        
        # Sentiments (for tracking)
        if pd.notna(theme.get('sentiment_direction')):
            sentiments.add(theme['sentiment_direction'])
    
    # Calculate aggregated values
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else base_theme.get('overall_quality_score', 0)
    avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else base_theme.get('impact_score', 0)
    
    # Determine sentiment
    if len(sentiments) > 1:
        final_sentiment = 'mixed'
    else:
        final_sentiment = list(sentiments)[0] if sentiments else base_theme.get('sentiment_direction', 'neutral')
    
    # Create description
    description = create_enriched_description(titles, sentiments, base_theme['scorecard_criterion'])
    
    # Create merged theme
    merged_theme = {
        'theme_title': enriched_title,
        'scorecard_criterion': base_theme['scorecard_criterion'],
        'sentiment_direction': final_sentiment,
        'companies_represented': len(all_companies),
        'quotes_count': total_quotes,
        'overall_quality_score': avg_quality,
        'impact_score': avg_impact,
        'description': description,
        'merged_from': titles,  # Track original stage4_themes
        'original_theme_ids': group_indices  # Track original IDs
    }
    
    return merged_theme

def create_enriched_title(titles: List[str], criterion: str) -> str:
    """Create an enriched title from multiple similar stage4_themes"""
    # Extract key concepts from titles
    concepts = set()
    for title in titles:
        # Extract key words (capitalized words, important terms)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', title)
        concepts.update(words)
    
    # Remove common words
    common_concepts = {'Rev', 'Legal', 'Services', 'The', 'A', 'An', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By', 'As', 'Is', 'Are', 'Was', 'Were', 'Be', 'Been', 'Being', 'Have', 'Has', 'Had', 'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should', 'May', 'Might', 'Can', 'This', 'That', 'These', 'Those', 'I', 'You', 'He', 'She', 'It', 'We', 'They', 'Me', 'Him', 'Her', 'Us', 'Them'}
    concepts = concepts - common_concepts
    
    # Create enriched title
    if concepts:
        key_concepts = list(concepts)[:3]  # Take top 3 concepts
        enriched_title = f"{' '.join(key_concepts)}: {criterion.title()} Excellence"
    else:
        enriched_title = f"{criterion.title()} Excellence and Performance"
    
    return enriched_title

def create_enriched_description(titles: List[str], sentiments: set, criterion: str) -> str:
    """Create an enriched description from multiple similar stage4_themes"""
    if len(sentiments) > 1:
        sentiment_desc = f"Mixed sentiment across {criterion} stage4_themes"
    else:
        sentiment_desc = f"Consistent {list(sentiments)[0]} sentiment"
    
    description = f"Combined insights from {len(titles)} related stage4_themes. {sentiment_desc}. "
    description += f"Key areas include: {', '.join(titles[:3])}"
    
    if len(titles) > 3:
        description += f" and {len(titles) - 3} additional related stage4_themes."
    
    return description

def save_merged_stage4_themes(merged_stage4_themes: List[Dict]):
    """Save merged stage4_themes to database"""
    try:
        supabase_db = create_supabase_database()
        
        # Clear existing stage4_themes
        supabase_db.supabase.table('scorecard_stage4_themes').delete().neq('id', 0).execute()
        
        # Prepare data for insertion (remove tracking fields)
        stage4_themes_data = []
        for theme in merged_stage4_themes:
            theme_data = {k: v for k, v in theme.items() if k not in ['merged_from', 'original_theme_ids']}
            stage4_themes_data.append(theme_data)
        
        # Insert merged stage4_themes
        response = supabase_db.supabase.table('scorecard_stage4_themes').insert(stage4_themes_data).execute()
        
        if response.data:
            logger.info(f"Successfully saved {len(response.data)} merged stage4_themes to database")
            return True
        else:
            logger.error("No stage4_themes were saved")
            return False
            
    except Exception as e:
        logger.error(f"Error saving stage4_themes: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting Semantic Theme Merging and Enrichment Process")
    logger.info("=" * 60)
    
    # Analyze current stage4_themes
    df_original = analyze_current_stage4_themes()
    if df_original is None:
        return
    
    logger.info(f"Original stage4_themes: {len(df_original)}")
    
    # Find similar theme groups
    similar_groups = find_similar_theme_groups(df_original, similarity_threshold=0.3)
    
    logger.info(f"Found {len(similar_groups)} groups of similar stage4_themes")
    
    # Merge each group
    merged_stage4_themes = []
    processed_indices = set()
    
    for group in similar_groups:
        merged_theme = merge_theme_group(df_original, group)
        merged_stage4_themes.append(merged_theme)
        processed_indices.update(group)
        logger.info(f"Merged group: {merged_theme['theme_title']}")
    
    # Add stage4_themes that weren't in any group (unique stage4_themes)
    for i, row in df_original.iterrows():
        if i not in processed_indices:
            # Convert to dict and add description
            theme_dict = row.to_dict()
            theme_dict['description'] = f"Standalone theme: {row['theme_title']}"
            theme_dict['merged_from'] = [row['theme_title']]
            theme_dict['original_theme_ids'] = [i]
            merged_stage4_themes.append(theme_dict)
            logger.info(f"Kept unique theme: {row['theme_title']}")
    
    # Show results
    logger.info(f"\n📊 MERGING RESULTS:")
    logger.info(f"Original stage4_themes: {len(df_original)}")
    logger.info(f"Merged stage4_themes: {len(merged_stage4_themes)}")
    logger.info(f"Reduction: {((len(df_original) - len(merged_stage4_themes)) / len(df_original) * 100):.1f}%")
    
    # Show final stage4_themes
    print(f"\n🎯 FINAL ENRICHED THEMES ({len(merged_stage4_themes)}):")
    print("=" * 60)
    
    try:
        from tabulate import tabulate
        display_data = []
        for theme in merged_stage4_themes:
            display_data.append([
                theme['theme_title'][:50] + "..." if len(theme['theme_title']) > 50 else theme['theme_title'],
                theme['scorecard_criterion'],
                theme['sentiment_direction'],
                theme['companies_represented'],
                f"{theme['overall_quality_score']:.2f}"
            ])
        
        print(tabulate(display_data, headers=['Theme', 'Criterion', 'Sentiment', 'Companies', 'Quality'], tablefmt='github'))
    except ImportError:
        for theme in merged_stage4_themes:
            print(f"• {theme['theme_title']}")
            print(f"  Criterion: {theme['scorecard_criterion']}")
            print(f"  Sentiment: {theme['sentiment_direction']}")
            print(f"  Companies: {theme['companies_represented']}")
            print(f"  Quality: {theme['overall_quality_score']:.2f}")
            print("")
    
    # Ask user if they want to save
    save_choice = input("\nDo you want to save these merged stage4_themes to the database? (y/n): ")
    if save_choice.lower() == 'y':
        success = save_merged_stage4_themes(merged_stage4_themes)
        if success:
            print("✅ Merged stage4_themes saved successfully!")
        else:
            print("❌ Failed to save merged stage4_themes")
    else:
        print("Merged stage4_themes not saved. Original stage4_themes remain in database.")

if __name__ == "__main__":
    main() 