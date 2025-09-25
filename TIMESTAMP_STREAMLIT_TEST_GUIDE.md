# 🎬 Timestamp Integration Test Guide

This guide shows you how to test the timestamp integration in Streamlit with your CSV data.

## 🚀 Quick Start

### Option 1: Streamlit Test App (Recommended)

1. **Run the test app:**
   ```bash
   source venv/bin/activate
   streamlit run test_timestamp_streamlit.py
   ```

2. **In the Streamlit interface:**
   - Set your Client ID in the sidebar
   - Upload your CSV file with 'Raw Transcript' column
   - Configure processing options (start with 2-3 interviews for testing)
   - Click "Process Transcripts"
   - View results with timestamps

### Option 2: Command Line Test

1. **Test with your CSV file:**
   ```bash
   source venv/bin/activate
   python test_csv_timestamps.py your_file.csv your_client_id 3 true
   ```

2. **Parameters:**
   - `your_file.csv` - Path to your CSV file
   - `your_client_id` - Your client identifier
   - `3` - Number of rows to process (for testing)
   - `true` - Save to database (or `false` for dry run)

## 📋 What You'll See

### Streamlit Interface Features:
- **CSV Upload**: Drag and drop your CSV file
- **Data Preview**: See your data before processing
- **Processing Options**: Configure max interviews, dry run, etc.
- **Real-time Progress**: Progress bar and status updates
- **Results Display**: Table showing all responses with timestamps
- **Sample Responses**: JSON preview of extracted data

### Expected Output:
```
✅ Successfully loaded CSV with X rows
✅ Database connected
📊 Interviews Processed: 3
📝 Total Responses: 15
🎬 Responses with Timestamps: 12
📈 Timestamp Coverage: 80.0%
```

## 🎯 What Gets Extracted

For each transcript, the system will:
1. **Parse timestamps** from various formats:
   - `Speaker 1 (01:00):` → `00:01:00`
   - `[00:01:00]` → `00:01:00`
   - `(02:00):` → `00:02:00`

2. **Extract Q&A pairs** with timing:
   - Question start time
   - Answer end time
   - Complete conversation flow

3. **Create database records** with:
   - `response_id`: Unique identifier
   - `verbatim_response`: The actual quote
   - `subject`: Topic category
   - `question`: The question that elicited the response
   - `start_timestamp`: When the response begins (HH:MM:SS)
   - `end_timestamp`: When the response ends (HH:MM:SS)
   - All other standard fields

## 🗄️ Database Integration

### Before Running:
Make sure your database has the timestamp columns:
```sql
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS start_timestamp VARCHAR(20);
ALTER TABLE stage1_data_responses ADD COLUMN IF NOT EXISTS end_timestamp VARCHAR(20);
```

### After Processing:
- All responses are saved to `stage1_data_responses` table
- Timestamps are in `HH:MM:SS` format
- You can query responses with timestamps:
  ```sql
  SELECT response_id, verbatim_response, start_timestamp, end_timestamp 
  FROM stage1_data_responses 
  WHERE start_timestamp IS NOT NULL;
  ```

## 🎬 Video Integration Ready

The extracted timestamps enable:
- **Precise video navigation** to specific quotes
- **Automatic video segment extraction**
- **Timeline-based quote organization**
- **Enhanced user experience** for quote review

## 🔧 Troubleshooting

### Common Issues:

1. **"CSV must contain 'Raw Transcript' column"**
   - Check your CSV has a column named exactly "Raw Transcript"
   - Case sensitive

2. **"Database connection failed"**
   - Check your Supabase credentials
   - Ensure database is accessible
   - Use dry run mode for testing

3. **"No responses extracted"**
   - Check transcript format has timestamps
   - Verify transcript content is not empty
   - Try with a different transcript

4. **"No timestamps found"**
   - Ensure transcript has timestamp patterns like:
     - `Speaker 1 (01:00):`
     - `[00:01:00]`
     - `(02:00):`

### Debug Mode:
Add this to see detailed processing:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Expected Results

Based on your `Puzzle.txt` transcript:
- **106 segments** with timestamps
- **17 Q&A pairs** identified
- **Multiple responses** per interview
- **80-90% timestamp coverage** typical

## 🎯 Next Steps

After successful testing:
1. **Integrate with main app**: Add timestamp UI to your main Streamlit app
2. **Scale up**: Process all your interviews
3. **Video integration**: Use timestamps for video navigation
4. **Analytics**: Analyze response timing patterns

## 💡 Tips

- Start with 2-3 interviews for testing
- Use dry run mode first to see results
- Check the sample responses to verify quality
- Look at timestamp coverage percentage
- Test with different transcript formats

Happy testing! 🎉
