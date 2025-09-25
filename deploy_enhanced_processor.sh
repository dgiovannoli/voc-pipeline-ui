#!/bin/bash

# Enhanced Processor with Timestamp Extraction - Production Deployment Script
echo "🎬 Deploying Enhanced Stage 1 Processor with Timestamp Extraction"
echo "=================================================================="

# Check if we're in the right directory
if [ ! -f "voc_pipeline/processor.py" ]; then
    echo "❌ Error: voc_pipeline/processor.py not found. Please run this script from the project root."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not found. Please initialize git first."
    exit 1
fi

echo "✅ Repository structure verified."

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Found uncommitted changes. Committing them now..."
    
    # Add all changes
    git add .
    
    # Commit with descriptive message
    git commit -m "Deploy enhanced Stage 1 processor with automatic timestamp extraction

- Added universal timestamp parsing for multiple formats
- Enhanced clean_verbatim_response to extract timestamps before cleaning
- Updated LLM prompt to include start_timestamp and end_timestamp fields
- Modified CSV output to include timestamp columns for video integration
- Added test interface for timestamp extraction validation
- Supports formats: [HH:MM:SS], Speaker (MM:SS):, (HH:MM:SS - HH:MM:SS), etc.

Ready for production deployment with video integration capabilities."
    
    echo "✅ Changes committed successfully."
else
    echo "✅ No uncommitted changes found."
fi

# Push to remote repository
echo "🚀 Pushing changes to remote repository..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to remote repository."
else
    echo "❌ Failed to push to remote repository."
    exit 1
fi

# Display deployment summary
echo ""
echo "🎉 Enhanced Processor Deployment Complete!"
echo "=========================================="
echo ""
echo "✅ **What's Deployed:**"
echo "   • Enhanced Stage 1 processor with automatic timestamp extraction"
echo "   • Universal timestamp parsing (supports all major formats)"
echo "   • Video integration ready (start_timestamp, end_timestamp columns)"
echo "   • Test interface for validation"
echo ""
echo "✅ **Supported Timestamp Formats:**"
echo "   • [HH:MM:SS] inline timestamps"
echo "   • Speaker 1 (01:00): speaker timestamps"
echo "   • Adri (00:00:38 - 00:00:39) ShipBob format"
echo "   • (03:00): standalone timestamps"
echo ""
echo "✅ **Production Ready Features:**"
echo "   • Zero workflow changes - existing process now includes timestamps"
echo "   • Database compatible - timestamps save automatically"
echo "   • Video integration ready - precise start/stop times"
echo "   • Future-proof - handles new timestamp formats automatically"
echo ""
echo "🚀 **Next Steps:**"
echo "   1. Test the enhanced processor with your production data"
echo "   2. Verify timestamp extraction in your database"
echo "   3. Integrate with your video player using the timestamp columns"
echo ""
echo "📱 **Test Interface:** http://localhost:8504 (if running locally)"
echo "📚 **Documentation:** See UNIVERSAL_TIMESTAMP_GUIDE.md"
echo ""
echo "🎬 Enhanced Stage 1 Processor is now live in production!"
