# Client Chat Interface - Deployment Guide

## 🚀 Quick Deployment (Streamlit Cloud)

### **Step 1: Prepare Your Repository**

Your repository should now have these files:
```
voc-pipeline-ui/
├── app.py                    # Internal pipeline (existing)
├── app_client.py            # Client chat interface (NEW)
├── client_chat_interface.py # Client app logic (NEW)
├── client_requirements.txt  # Client dependencies (NEW)
├── .streamlit/config.toml   # Streamlit config (NEW)
├── deploy_client.sh         # Deployment script (NEW)
└── ... (other existing files)
```

### **Step 2: Push to GitHub**

```bash
# Run the deployment script
./deploy_client.sh

# Or manually:
git add .
git commit -m "Add client chat interface"
git push
```

### **Step 3: Deploy to Streamlit Cloud**

1. **Go to Streamlit Cloud**: https://share.streamlit.io/
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Configure your app**:
   - **Repository**: Select your `voc-pipeline-ui` repo
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app_client.py`
   - **App URL**: Choose a custom URL (optional)

### **Step 4: Set Environment Variables**

In Streamlit Cloud, add these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |

### **Step 5: Deploy**

Click **"Deploy!"** and wait for the build to complete.

---

## 🔧 Alternative Deployment Options

### **Option A: Docker Deployment**

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app_client.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Option B: VPS Deployment**

```bash
# Install dependencies
pip install -r client_requirements.txt

# Run the app
streamlit run app_client.py --server.port=8501 --server.address=0.0.0.0
```

---

## 🔐 Security Configuration

### **1. Supabase Row Level Security (RLS)**

Add these policies to your Supabase database:

```sql
-- Enable RLS on all tables
ALTER TABLE stage4_themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE stage3_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE stage1_data_responses ENABLE ROW LEVEL SECURITY;

-- Create policies for client-specific access
CREATE POLICY "Client can only access their own themes" ON stage4_themes
FOR ALL USING (client_id = current_setting('app.client_id')::text);

CREATE POLICY "Client can only access their own findings" ON stage3_findings
FOR ALL USING (client_id = current_setting('app.client_id')::text);

CREATE POLICY "Client can only access their own responses" ON stage1_data_responses
FOR ALL USING (client_id = current_setting('app.client_id')::text);
```

### **2. Environment Variables**

Create a `.env` file for local development:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

---

## 🧪 Testing Your Deployment

### **1. Test Locally First**

```bash
# Test the client app locally
streamlit run app_client.py --server.port=8502

# Test the internal app (different port)
streamlit run app.py --server.port=8501
```

### **2. Test Client ID Access**

Use these test client IDs:
- `demo_client` - For testing
- `test_client_1` - For another test dataset
- Your actual client IDs from the database

### **3. Test Common Questions**

Try these questions in the chat:
- "What are the main themes from our customer interviews?"
- "What do customers say about our product setup process?"
- "What are the most common pain points mentioned?"
- "Show me insights about customer satisfaction"

---

## 📊 Monitoring & Maintenance

### **1. Check Deployment Status**

- **Streamlit Cloud**: Check the deployment logs
- **GitHub**: Monitor commit history
- **Supabase**: Monitor database usage

### **2. Monitor Costs**

- **OpenAI**: Check usage in OpenAI dashboard
- **Supabase**: Monitor bandwidth and storage
- **Streamlit**: Check app performance

### **3. Update Dependencies**

```bash
# Update requirements
pip install --upgrade streamlit supabase openai pandas

# Update requirements.txt
pip freeze > client_requirements.txt
```

---

## 🚨 Troubleshooting

### **Common Issues:**

1. **"Module not found" errors**
   - Check that all files are in the repository
   - Verify `client_requirements.txt` includes all dependencies

2. **"Environment variable not set"**
   - Double-check environment variables in Streamlit Cloud
   - Ensure variable names match exactly

3. **"Database connection failed"**
   - Verify Supabase URL and key
   - Check RLS policies are set correctly

4. **"OpenAI API error"**
   - Verify API key is valid
   - Check OpenAI account has sufficient credits

### **Debug Commands:**

```bash
# Check if app runs locally
streamlit run app_client.py --server.port=8502

# Check environment variables
echo $SUPABASE_URL
echo $OPENAI_API_KEY

# Check git status
git status
git log --oneline -5
```

---

## 🎯 Next Steps After Deployment

1. **Test with real clients** - Get feedback on the interface
2. **Add authentication** - Implement proper client login
3. **Customize branding** - Add your company logo and colors
4. **Add analytics** - Track usage and popular questions
5. **Scale up** - Add more features based on client needs

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Streamlit Cloud deployment logs
3. Test locally to isolate the issue
4. Check Supabase dashboard for database issues 