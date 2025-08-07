# 🚀 Quick Start Guide

## **Immediate Usage Options**

### **Option 1: Command Line (Fastest)**
```bash
# Generate Excel workbook for Supio
python generate_excel_workbook.py --client Supio

# Generate with custom filename
python generate_excel_workbook.py --client Supio --output my_report.xlsx
```

### **Option 2: Streamlit UI (User-Friendly)**
```bash
# Start the web interface
streamlit run app.py --server.port 8501

# Then navigate to: http://localhost:8501
# Go to "📊 Excel Workbook Generation" tab
```

### **Option 3: Programmatic (For Developers)**
```python
from win_loss_report_generator import WinLossReportGenerator
from excel_win_loss_exporter import ExcelWinLossExporter

# Generate themes
generator = WinLossReportGenerator('Supio')
themes_data = generator.generate_analyst_report()

# Create Excel workbook
exporter = ExcelWinLossExporter()
output_path = exporter.export_analyst_workbook(themes_data)
print(f"Workbook created: {output_path}")
```

## **📋 What You Get**

### **Excel Workbook with:**
- **🔄 Cross-Section Themes Tab**: Identifies themes in multiple sections
- **📊 Section Validation Tabs**: Win Drivers, Loss Factors, Competitive, Implementation
- **📈 Analysis Tools**: Quote curation, theme validation, research alignment
- **📋 Executive Summary**: High-level insights and metrics

### **Key Features:**
- **No Duplicate Work**: Themes processed once in primary section
- **Cross-Reference System**: Clear indicators for multi-section themes
- **Processing Status**: Track completion of each theme
- **Quality Gates**: Ensures high-quality themes only

## **🎯 Analyst Workflow**

1. **Open Excel workbook**
2. **Start with "🔄 Cross-Section Themes" tab**
3. **Process themes in their primary sections**
4. **Mark processing status as you complete each theme**
5. **Use curated themes in your final report**

## **🔧 Prerequisites**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

## **📞 Need Help?**

- **Documentation**: See `PRODUCTION_README.md`
- **Troubleshooting**: Check logs for error details
- **Support**: Review the comprehensive documentation

---

**Ready to generate your first Excel workbook?**  
Start with: `python generate_excel_workbook.py --client Supio` 