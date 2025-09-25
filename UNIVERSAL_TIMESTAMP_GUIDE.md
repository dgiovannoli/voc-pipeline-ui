# 🎬 Universal Timestamp Processing Guide

## Future-Proof Your Interview Processing

This guide shows you how to make your timestamp processing work with **any interview format**, not just ShipBob.

## �� Quick Start

### Option 1: Universal Streamlit UI (Recommended)
```bash
source venv/bin/activate
streamlit run universal_timestamp_ui.py
```

### Option 2: Command Line Processing
```bash
source venv/bin/activate
python universal_timestamp_processor.py your_data.csv your_client_id 10 true
```

## 📋 Supported Formats

The universal processor automatically detects and handles:

| Format | Example | Description |
|--------|---------|-------------|
| **ShipBob** | `Speaker Name (00:00:38 - 00:00:39)` | Start and end timestamps |
| **Rev** | `Speaker 1 (01:00:00):` | Full timestamp format |
| **Original** | `Speaker 1 (01:00):` | Minutes:seconds format |
| **Generic** | `Name (HH:MM:SS):` | Any name with timestamp |
| **Inline** | `[00:01:00]` | Inline timestamps |

## 🔧 Integration with Your Existing App

### 1. Add to Your Main App

Add this to your `app.py`:

```python
from universal_timestamp_processor import UniversalTimestampParser, process_universal_transcript_with_timestamps

# In your processing function:
def process_any_interview(transcript, metadata):
    parser = UniversalTimestampParser()
    
    # Auto-detect format and process
    responses = process_universal_transcript_with_timestamps(
        transcript=transcript,
        company=metadata['company'],
        interviewee=metadata['interviewee'],
        deal_status=metadata['deal_status'],
        interview_date=metadata['date'],
        client_id=metadata['client_id'],
        interview_id=metadata['interview_id']
    )
    
    return responses
```

### 2. Update Your Database Save Function

Make sure your `supabase_database.py` includes timestamp fields:

```python
def save_core_response(self, response_data: Dict[str, Any]) -> bool:
    data = {
        # ... existing fields ...
        'start_timestamp': response_data.get('start_timestamp'),
        'end_timestamp': response_data.get('end_timestamp')
    }
```

## 🎯 Key Benefits

### ✅ **Automatic Format Detection**
- No need to specify format
- Works with any timestamp pattern
- Handles mixed formats in same file

### ✅ **Universal Column Mapping**
- Auto-detects transcript columns
- Maps metadata fields intelligently
- Works with any CSV structure

### ✅ **Future-Proof**
- Add new formats easily
- Extensible parser architecture
- Handles edge cases gracefully

### ✅ **Rich Metadata**
- Preserves all original data
- Adds timestamp information
- Maintains data lineage

## 📊 Usage Examples

### ShipBob Data
```bash
python universal_timestamp_processor.py "shipbob_data.csv" shipbob 10 true
```

### Rev Data
```bash
python universal_timestamp_processor.py "rev_data.csv" rev_client 5 true
```

### Any Other Format
```bash
python universal_timestamp_processor.py "any_data.csv" my_client 20 false
```

## 🔍 Format Detection

The system automatically detects formats by analyzing:

1. **Timestamp patterns** in the first 1000 characters
2. **Speaker identification** patterns
3. **Text structure** and formatting
4. **Common interview formats**

## 🛠️ Adding New Formats

To add support for a new format:

1. **Add regex pattern** to `UniversalTimestampParser.patterns`
2. **Create parser method** `_parse_new_format()`
3. **Add format detection** in `detect_format()`
4. **Test with sample data**

Example:
```python
# Add to patterns
'new_format': re.compile(r'^(\w+)\s*@(\d{2}:\d{2}:\d{2})\s*(.*)$', re.MULTILINE),

# Add detection
if self.patterns['new_format'].search(sample):
    return 'new_format'

# Add parser method
def _parse_new_format(self, transcript: str) -> List[TimestampSegment]:
    # Implementation here
    pass
```

## 📈 Performance

- **Fast processing**: Optimized regex patterns
- **Memory efficient**: Processes in chunks
- **Parallel ready**: Can be easily parallelized
- **Database optimized**: Batch operations

## 🎬 Video Integration Ready

All extracted timestamps are formatted for video integration:

- **Start/End times** for each quote
- **Speaker identification** for video overlays
- **Rich metadata** for video descriptions
- **Database storage** for video player integration

## 🚀 Next Steps

1. **Test with your data**: Upload a sample CSV
2. **Verify timestamps**: Check format detection
3. **Process full dataset**: Run production processing
4. **Integrate with app**: Add to your main interface
5. **Add new formats**: Extend as needed

## 💡 Pro Tips

- **Start small**: Test with 5-10 interviews first
- **Check format detection**: Use the detection tab in the UI
- **Verify timestamps**: Review sample responses
- **Monitor coverage**: Aim for 80%+ timestamp coverage
- **Backup data**: Always backup before processing

---

**Ready to process any interview format with timestamps!** 🎬
