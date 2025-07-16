# Metadata Upload Process

## Current Company Mapping
The following companies have been assigned identifiers for Stage 4 testing:

- Company A
- Company B
- Company C
- Company D
- Company E
- Company F
- Company G
- Company H
- Company I
- Company J
- Company K
- Company L
- Company M
- Company N
- Company O
- Company P


## Future Metadata Upload Process

To upload metadata for new interviews:

1. **Prepare Metadata CSV** with columns:
   - interviewee_name
   - company_name
   - interview_date
   - deal_status
   - other_relevant_fields

2. **Upload Process**:
   ```python
   from metadata_uploader import MetadataUploader
   
   uploader = MetadataUploader()
   uploader.upload_metadata('path/to/metadata.csv', client_id='Rev')
   ```

3. **Validation**:
   - Ensure all required fields are present
   - Validate company names against existing mapping
   - Check for duplicate interviewee names

## Notes
- Company identifiers are automatically assigned (Company A, Company B, etc.)
- Cross-company validation requires minimum 2 companies per theme
- Strategic alerts can be single-company for urgent issues
