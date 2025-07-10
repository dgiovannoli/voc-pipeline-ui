import pandas as pd
import logging
from supabase_database import create_supabase_database

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def analyze_current_themes():
    """Analyze current themes in the database"""
    try:
        supabase_db = create_supabase_database()
        
        # Get all scorecard themes
        response = supabase_db.supabase.table('scorecard_themes').select('*').execute()
        
        if not response.data:
            logger.warning("No themes found in database")
            return None
        
        df = pd.DataFrame(response.data)
        logger.info(f"Found {len(df)} themes in database")
        
        # Show summary statistics
        logger.info(f"Criteria represented: {df['scorecard_criterion'].nunique()}")
        logger.info(f"Sentiment distribution: {df['sentiment_direction'].value_counts().to_dict()}")
        logger.info(f"Quality score range: {df['overall_quality_score'].min():.2f} - {df['overall_quality_score'].max():.2f}")
        logger.info(f"Companies range: {df['companies_represented'].min()} - {df['companies_represented'].max()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error analyzing themes: {e}")
        return None

def generate_summary_report(df_original, df_final, selected_criteria):
    """Generate summary report of filtering results"""
    original_count = len(df_original)
    filtered_count = len(df_final)
    reduction_percent = ((original_count - filtered_count) / original_count) * 100
    
    # Calculate quality improvement
    original_quality = df_original['overall_quality_score'].mean()
    final_quality = df_final['overall_quality_score'].mean()
    quality_improvement = final_quality - original_quality
    
    return {
        'original_count': original_count,
        'filtered_count': filtered_count,
        'reduction_percent': reduction_percent,
        'quality_improvement': quality_improvement,
        'selected_criteria': selected_criteria
    }

def save_filtered_themes(df):
    """Save filtered themes to database"""
    try:
        supabase_db = create_supabase_database()
        
        # Clear existing themes
        supabase_db.supabase.table('scorecard_themes').delete().neq('id', 0).execute()
        
        # Insert filtered themes
        themes_data = df.to_dict('records')
        response = supabase_db.supabase.table('scorecard_themes').insert(themes_data).execute()
        
        if response.data:
            logger.info(f"Successfully saved {len(response.data)} themes to database")
            return True
        else:
            logger.error("No themes were saved")
            return False
            
    except Exception as e:
        logger.error(f"Error saving themes: {e}")
        return False



def step2_criteria_selection(df):
    """Step 2: Criteria Selection (keep all criteria with at least one high-quality, high-impact theme)"""
    logger.info("\n🎯 STEP 2: Criteria Selection (no arbitrary limit)")
    logger.info("=" * 40)
    
    # Just report which criteria remain
    remaining_criteria = df['scorecard_criterion'].unique().tolist()
    logger.info(f"Remaining criteria: {remaining_criteria}")
    logger.info(f"Themes after criteria selection: {len(df)}")
    
    return df, remaining_criteria

def step3_deduplication(df):
    """Step 3: Deduplication - remove similar themes"""
    logger.info("\n🔄 STEP 3: Deduplication")
    logger.info("=" * 40)
    
    initial_count = len(df)
    
    # Group by criterion and sentiment to find duplicates
    duplicates_removed = []
    unique_themes = []
    
    for criterion in df['scorecard_criterion'].unique():
        criterion_data = df[df['scorecard_criterion'] == criterion]
        
        for sentiment in criterion_data['sentiment_direction'].unique():
            sentiment_data = criterion_data[criterion_data['sentiment_direction'] == sentiment]
            
            if len(sentiment_data) > 1:
                # Multiple themes for same criterion + sentiment - keep the best one
                best_theme = sentiment_data.loc[sentiment_data['overall_quality_score'].idxmax()]
                unique_themes.append(best_theme)
                
                # Log removed duplicates
                for _, theme in sentiment_data.iterrows():
                    if theme.name != best_theme.name:
                        duplicates_removed.append(theme)
                        logger.info(f"Removed duplicate: {theme['theme_title']} (Quality: {theme['overall_quality_score']:.2f})")
                        logger.info(f"  Kept: {best_theme['theme_title']} (Quality: {best_theme['overall_quality_score']:.2f})")
            else:
                # Only one theme for this criterion + sentiment
                unique_themes.append(sentiment_data.iloc[0])
    
    df_deduplicated = pd.DataFrame(unique_themes)
    
    logger.info(f"Themes before deduplication: {initial_count}")
    logger.info(f"Themes after deduplication: {len(df_deduplicated)}")
    logger.info(f"Removed: {len(duplicates_removed)} duplicate themes")
    
    return df_deduplicated

def step1_quality_filtering(df):
    """Step 1: Company Count Filtering (minimum 3 companies)"""
    logger.info("\n🔍 STEP 1: Company Count Filtering")
    logger.info("=" * 40)
    
    initial_count = len(df)
    
    # Filter by minimum 3 companies
    min_companies = 3
    df_filtered = df[df['companies_represented'] >= min_companies].copy()
    
    logger.info(f"Minimum companies threshold: ≥ {min_companies}")
    logger.info(f"Themes before filtering: {initial_count}")
    logger.info(f"Themes after filtering: {len(df_filtered)}")
    logger.info(f"Removed: {initial_count - len(df_filtered)} themes")
    
    # Show removed themes
    removed_themes = df[df['companies_represented'] < min_companies]
    if not removed_themes.empty:
        logger.info("\nRemoved themes (insufficient companies):")
        for _, theme in removed_themes.iterrows():
            logger.info(f"  - {theme['theme_title']} (Companies: {theme['companies_represented']})")
    
    return df_filtered

def step4_semantic_deduplication(df):
    """Step 4: Semantic Deduplication - merge similar themes and create enriched themes"""
    logger.info("\n🔗 STEP 4: Semantic Deduplication & Enrichment")
    logger.info("=" * 40)
    
    initial_count = len(df)
    
    # Import semantic merging functions
    try:
        from semantic_theme_merger import find_similar_theme_groups, merge_theme_group
    except ImportError:
        logger.warning("Semantic merger module not found. Skipping semantic deduplication.")
        return df
    
    # Find similar theme groups
    similar_groups = find_similar_theme_groups(df, similarity_threshold=0.3)
    
    if not similar_groups:
        logger.info("No similar theme groups found. All themes are unique.")
        return df
    
    logger.info(f"Found {len(similar_groups)} groups of similar themes")
    
    # Merge each group
    merged_themes = []
    processed_indices = set()
    
    for group in similar_groups:
        merged_theme = merge_theme_group(df, group)
        merged_themes.append(merged_theme)
        processed_indices.update(group)
        logger.info(f"Merged group: {merged_theme['theme_title']}")
    
    # Add themes that weren't in any group (unique themes)
    for i, row in df.iterrows():
        if i not in processed_indices:
            # Convert to dict and add description
            theme_dict = row.to_dict()
            theme_dict['description'] = f"Standalone theme: {row['theme_title']}"
            merged_themes.append(theme_dict)
            logger.info(f"Kept unique theme: {row['theme_title']}")
    
    df_merged = pd.DataFrame(merged_themes)
    
    logger.info(f"Themes before semantic deduplication: {initial_count}")
    logger.info(f"Themes after semantic deduplication: {len(df_merged)}")
    logger.info(f"Reduction: {((initial_count - len(df_merged)) / initial_count * 100):.1f}%")
    
    return df_merged

def main():
    """Main function"""
    logger.info("🚀 Starting High Quality Theme Filtering Process")
    logger.info("=" * 60)
    
    # Analyze current themes
    df_original = analyze_current_themes()
    if df_original is None:
        return
    
    # Step 1: Company Count Filtering
    df_company_filtered = step1_quality_filtering(df_original)
    
    if df_company_filtered.empty:
        logger.warning("No themes passed company count filtering.")
        return
    
    # Step 2: Criteria Selection (no arbitrary limit)
    df_criteria_filtered, remaining_criteria = step2_criteria_selection(df_company_filtered)
    
    if df_criteria_filtered.empty:
        logger.warning("No themes passed criteria selection.")
        return
    
    # Step 3: Deduplication
    df_final = step3_deduplication(df_criteria_filtered)
    
    if df_final.empty:
        logger.warning("No themes passed deduplication.")
        return
    
    # Step 4: Semantic Deduplication
    df_semantic_deduplicated = step4_semantic_deduplication(df_final)
    
    if df_semantic_deduplicated.empty:
        logger.warning("No themes passed semantic deduplication.")
        return
    
    # Generate summary report
    summary = generate_summary_report(df_original, df_semantic_deduplicated, remaining_criteria)
    
    # Show final themes in the console as a table
    try:
        from tabulate import tabulate
        print("\n🎯 FINAL THEMES (table):")
        print(tabulate(df_semantic_deduplicated[[
            'theme_title', 'scorecard_criterion', 'sentiment_direction', 'companies_represented', 'overall_quality_score'
        ]], headers=['Theme', 'Criterion', 'Sentiment', 'Companies', 'Quality'], tablefmt='github'))
    except ImportError:
        print("\n🎯 FINAL THEMES (table):")
        print(df_semantic_deduplicated[[
            'theme_title', 'scorecard_criterion', 'sentiment_direction', 'companies_represented', 'overall_quality_score'
        ]].to_string(index=False, header=['Theme', 'Criterion', 'Sentiment', 'Companies', 'Quality']))
    
    # Ask user if they want to save the filtered themes
    print(f"\n📊 FILTERING RESULTS:")
    print(f"Original themes: {summary['original_count']}")
    print(f"Filtered themes: {summary['filtered_count']}")
    print(f"Reduction: {summary['reduction_percent']:.1f}%")
    print(f"Quality improvement: {summary['quality_improvement']:.2f}")
    print(f"Selected criteria: {', '.join(summary['selected_criteria'])}")
    
    save_choice = input("\nDo you want to save these filtered themes to the database? (y/n): ")
    if save_choice.lower() == 'y':
        success = save_filtered_themes(df_semantic_deduplicated)
        if success:
            print("✅ Filtered themes saved successfully!")
        else:
            print("❌ Failed to save filtered themes")
    else:
        print("Filtered themes not saved. Original themes remain in database.")

if __name__ == "__main__":
    main() 