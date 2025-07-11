# Production Deployment Guide for VOC Pipeline

This guide covers the complete production deployment of the VOC Pipeline with Buried Wins v4.0 framework.

## 🚀 Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Supabase project created and configured
- [ ] Environment variables set up
- [ ] Database schema deployed
- [ ] API keys configured
- [ ] Client configurations established

### 2. Code Preparation
- [ ] All tests passing
- [ ] Code duplication cleaned up
- [ ] Configuration files updated
- [ ] Dependencies installed
- [ ] Logging configured

## 📋 Database Setup

### Step 1: Deploy Database Schema

1. **Access Supabase Dashboard**
   - Go to your Supabase project dashboard
   - Navigate to **SQL Editor** in the left sidebar

2. **Execute Schema Migration**
   ```sql
   -- Copy and paste the entire content of production_database_schema.sql
   -- This will create all necessary tables, indexes, and views
   ```

3. **Verify Schema Creation**
   ```sql
   -- Check that all tables were created
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN (
       'stage1_data_responses',
       'stage2_response_labeling', 
       'stage3_findings',
       'stage4_themes',
       'processing_metadata',
       'client_configurations'
   );
   ```

### Step 2: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI Configuration (for LLM findings generation)
OPENAI_API_KEY=your_openai_api_key

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
CLIENT_ID=default

# Processing Configuration
FINDINGS_THRESHOLD=5
CONFIDENCE_THRESHOLD=0.5
MAX_FINDINGS_PER_QUOTE=1
```

### Step 3: Test Database Connection

```bash
python -c "
from supabase_database import create_supabase_database
db = create_supabase_database()
print('✅ Database connection successful!')
"
```

## 🔧 Application Configuration

### 1. Update Configuration Files

**config/analysis_config.yaml**
```yaml
# Buried Wins v4.0 Configuration
buried_wins:
  min_threshold: 5
  confidence_threshold: 0.5
  max_findings_per_quote: 1
  
# LLM Configuration
llm:
  model: "gpt-4o-mini"
  max_tokens: 500
  temperature: 0.3
  
# Processing Configuration
processing:
  batch_size: 100
  max_workers: 4
  timeout_seconds: 300
```

### 2. Client Configuration

Set up client-specific configurations in the database:

```sql
-- Insert production client configurations
INSERT INTO client_configurations (client_id, client_name, client_description, client_settings)
VALUES 
('Rev', 'Rev.com', 'Rev.com VOC Analysis', '{"processing_enabled": true, "findings_threshold": 5, "confidence_threshold": 0.5}'),
('AltairLaw', 'Altair Law', 'Altair Law VOC Analysis', '{"processing_enabled": true, "findings_threshold": 5, "confidence_threshold": 0.5}'),
('default', 'Default Client', 'Default configuration', '{"processing_enabled": true, "findings_threshold": 5, "confidence_threshold": 0.5}')
ON CONFLICT (client_id) DO UPDATE SET 
client_settings = EXCLUDED.client_settings,
updated_at = NOW();
```

## 🚀 Deployment Steps

### Step 1: Code Deployment

1. **Deploy to Production Server**
   ```bash
   # Clone repository to production server
   git clone https://github.com/your-repo/voc-pipeline-ui.git
   cd voc-pipeline-ui
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Test Core Functionality**
   ```bash
   # Test database connection
   python test_database_connection.py
   
   # Test Stage 3 findings generation
   python -c "
   from stage3_findings_analyzer import run_stage3_analysis
   result = run_stage3_analysis('Rev')
   print(f'✅ Stage 3 analysis completed: {result}')
   "
   ```

### Step 2: Data Migration (if needed)

If you have existing data to migrate:

```bash
# Export existing data
python export_existing_data.py

# Import to new schema
python import_to_production.py
```

### Step 3: Production Testing

1. **Run Full Pipeline Test**
   ```bash
   # Test complete pipeline
   python test_production_pipeline.py
   ```

2. **Verify Findings Generation**
   ```bash
   # Generate findings for production client
   python stage3_findings_analyzer.py --client_id Rev
   
   # Check results
   ls -la findings_after_clustering.csv
   ```

## 📊 Monitoring and Maintenance

### 1. Database Monitoring

Set up monitoring queries:

```sql
-- Monitor findings generation
SELECT 
    client_id,
    COUNT(*) as total_findings,
    AVG(enhanced_confidence) as avg_confidence,
    MAX(created_at) as latest_finding
FROM stage3_findings 
GROUP BY client_id;

-- Monitor processing jobs
SELECT 
    stage,
    processing_status,
    COUNT(*) as job_count,
    AVG(processing_duration_seconds) as avg_duration
FROM processing_metadata 
GROUP BY stage, processing_status;
```

### 2. Performance Monitoring

```sql
-- Check query performance
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename IN ('stage3_findings', 'stage1_data_responses')
ORDER BY tablename, attname;
```

### 3. Error Monitoring

```sql
-- Check for processing errors
SELECT 
    processing_id,
    stage,
    processing_status,
    error_messages,
    created_at
FROM processing_metadata 
WHERE processing_status = 'failed'
ORDER BY created_at DESC;
```

## 🔒 Security Considerations

### 1. API Key Management
- Store API keys in environment variables
- Use Supabase Row Level Security (RLS)
- Implement client-specific data access

### 2. Data Access Control
```sql
-- Enable RLS on all tables
ALTER TABLE stage1_data_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE stage2_response_labeling ENABLE ROW LEVEL SECURITY;
ALTER TABLE stage3_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE stage4_themes ENABLE ROW LEVEL SECURITY;

-- Create policies for client-based access
CREATE POLICY "Users can view own client data" ON stage3_findings
    FOR SELECT USING (auth.jwt() ->> 'client_id' = client_id);
```

### 3. Backup Strategy
- Enable Supabase automated backups
- Set up manual backup scripts
- Test restore procedures

## 📈 Scaling Considerations

### 1. Performance Optimization
- Monitor query performance
- Add indexes as needed
- Implement caching for frequently accessed data

### 2. Load Balancing
- Consider multiple application instances
- Implement queue system for large datasets
- Monitor resource usage

### 3. Data Retention
```sql
-- Implement data retention policies
-- Archive old findings after 12 months
CREATE OR REPLACE FUNCTION archive_old_findings()
RETURNS void AS $$
BEGIN
    INSERT INTO stage3_findings_archive 
    SELECT * FROM stage3_findings 
    WHERE created_at < NOW() - INTERVAL '12 months';
    
    DELETE FROM stage3_findings 
    WHERE created_at < NOW() - INTERVAL '12 months';
END;
$$ LANGUAGE plpgsql;
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check environment variables
   echo $SUPABASE_URL
   echo $SUPABASE_ANON_KEY
   
   # Test connection
   python test_database_connection.py
   ```

2. **LLM API Errors**
   ```bash
   # Check OpenAI API key
   echo $OPENAI_API_KEY
   
   # Test LLM connection
   python test_llm_connection.py
   ```

3. **Performance Issues**
   ```sql
   -- Check slow queries
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

### Emergency Procedures

1. **Rollback to Previous Version**
   ```bash
   git checkout previous-stable-tag
   python rollback_database.py
   ```

2. **Disable Processing**
   ```sql
   UPDATE client_configurations 
   SET client_settings = jsonb_set(client_settings, '{processing_enabled}', 'false')
   WHERE client_id = 'Rev';
   ```

## ✅ Post-Deployment Verification

### 1. Functionality Tests
- [ ] Database connection working
- [ ] Stage 3 findings generation working
- [ ] LLM integration functioning
- [ ] CSV export working
- [ ] Client data siloing working

### 2. Performance Tests
- [ ] Processing time acceptable
- [ ] Memory usage within limits
- [ ] Database queries optimized
- [ ] API response times good

### 3. Data Quality Checks
- [ ] Findings quality matches expectations
- [ ] No duplicate findings
- [ ] Evidence properly linked
- [ ] Metadata correctly populated

## 📞 Support and Maintenance

### 1. Regular Maintenance Tasks
- Monitor database performance
- Review and optimize queries
- Update dependencies
- Backup verification

### 2. Update Procedures
- Test updates in staging environment
- Deploy during low-traffic periods
- Monitor for issues post-update
- Rollback plan ready

### 3. Documentation Updates
- Keep deployment guide current
- Update troubleshooting procedures
- Maintain runbooks for common issues

---

## 🎯 Success Metrics

After deployment, monitor these key metrics:

1. **Processing Success Rate**: >95%
2. **Findings Quality Score**: >8.0/10
3. **Processing Time**: <5 minutes per 1000 quotes
4. **Database Response Time**: <100ms average
5. **Error Rate**: <1%

## 📞 Emergency Contacts

- Database Administrator: [Contact Info]
- Application Developer: [Contact Info]
- System Administrator: [Contact Info]

---

**Production Deployment Status**: ✅ Ready for Deployment

**Last Updated**: [Date]
**Version**: Buried Wins v4.0
**Deployed By**: [Your Name] 