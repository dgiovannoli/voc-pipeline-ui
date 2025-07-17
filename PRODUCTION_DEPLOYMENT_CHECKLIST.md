# Production Deployment Checklist

## ✅ Pre-Deployment Tests (All Passing)

### Environment & Infrastructure
- [x] Environment variables configured
- [x] OpenAI API connection working
- [x] Supabase database connection working
- [x] All database tables accessible
- [x] File permissions working
- [x] Network connectivity to external services

### Code & Dependencies
- [x] All module imports working
- [x] Stage 3 analyzer functionality
- [x] Stage 4 analyzer functionality
- [x] Enhanced classification system integrated

## 🚨 Common Production Issues & Solutions

### 1. Environment Variables
**Issue**: Missing or incorrect environment variables
**Solution**: 
- Ensure `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` are set
- Use the production test script: `python production_test.py`

### 2. OpenAI API Issues
**Issue**: API key invalid, rate limits, or network issues
**Solution**:
- Verify API key has sufficient credits
- Check rate limits (requests per minute)
- Ensure network connectivity to `api.openai.com`

### 3. Database Connection Issues
**Issue**: Supabase connection fails or tables missing
**Solution**:
- Verify Supabase URL and key are correct
- Ensure all required tables exist
- Check database permissions

### 4. Memory & Performance Issues
**Issue**: Out of memory or slow performance
**Solution**:
- Monitor memory usage during large operations
- Consider batching for large datasets
- Optimize LLM calls with smaller batches

### 5. File System Issues
**Issue**: Cannot read/write files
**Solution**:
- Ensure proper file permissions
- Check disk space
- Verify file paths are correct

## 🔧 Production Monitoring

### Key Metrics to Monitor
1. **LLM Integration Status** - Most critical
2. **Database Connection** - Core functionality
3. **Memory Usage** - Performance indicator
4. **API Response Times** - User experience
5. **Error Rates** - System health

### Automated Testing
Run the production test script regularly:
```bash
python production_test.py
```

## 🚀 Deployment Steps

### 1. Pre-Deployment
- [ ] Run `python production_test.py` locally
- [ ] Ensure all tests pass
- [ ] Check environment variables in production
- [ ] Verify database schema matches

### 2. Deployment
- [ ] Deploy code to production environment
- [ ] Set production environment variables
- [ ] Test basic functionality
- [ ] Monitor logs for errors

### 3. Post-Deployment
- [ ] Run production test script on production
- [ ] Test Stage 3 and Stage 4 functionality
- [ ] Verify data flows correctly
- [ ] Monitor performance metrics

## 🆘 Troubleshooting

### If LLM Integration Fails
1. Check OpenAI API key validity
2. Verify API key has credits
3. Test network connectivity
4. Check API rate limits

### If Database Connection Fails
1. Verify Supabase credentials
2. Check database is online
3. Test table permissions
4. Verify schema matches

### If Analyzers Fail
1. Check all required files exist
2. Verify prompt files are accessible
3. Test module imports
4. Check memory usage

## 📊 Success Indicators

✅ **All tests pass** in production test script
✅ **LLM Integration** shows green in dashboard
✅ **Database Connection** shows green in dashboard
✅ **Stage 3 and Stage 4** run without errors
✅ **Data flows** from Stage 1 → Stage 2 → Stage 3 → Stage 4

## 🔄 Continuous Monitoring

- Run production tests weekly
- Monitor dashboard status indicators
- Check error logs regularly
- Track performance metrics
- Update dependencies as needed 