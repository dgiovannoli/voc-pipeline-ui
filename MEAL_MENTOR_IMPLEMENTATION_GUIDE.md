# Meal Mentor System Implementation Guide

## Overview

The Meal Mentor system is designed to handle health questions and text-based food logging by leveraging Claude's capabilities. This system provides a comprehensive solution for nutrition tracking and health guidance while maintaining appropriate medical boundaries.

## Key Features

### 1. **Text-Based Food Logging**
- Natural language food descriptions
- Automatic nutritional analysis using AI
- Calorie estimation and macronutrient breakdown
- Meal type classification
- Symptom tracking and correlation

### 2. **Health Question Processing**
- Intelligent message classification
- Health-focused responses with medical disclaimers
- Symptom-aware food recommendations
- Appropriate escalation to healthcare providers

### 3. **Personalized Recommendations**
- Learning from user food history
- Pattern recognition for trigger foods
- Customized suggestions based on health conditions
- Adaptive responses based on user preferences

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  MealMentor     │    │   Database      │
│                 │    │    System       │    │   (Supabase)    │
│ - Chat Interface│ ── │                 │ ── │                 │
│ - Food Logging  │    │ - Classification│    │ - Food Logs     │
│ - Health Tips   │    │ - AI Processing │    │ - Health Queries│
└─────────────────┘    │ - Personalization│    │ - User Profiles │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   AI Provider   │
                       │                 │
                       │ - Claude (Pref) │
                       │ - OpenAI (Alt)  │
                       └─────────────────┘
```

### Message Flow

1. **Input Classification**: Automatically determine if message is:
   - Health question
   - Food logging
   - General nutrition chat

2. **Processing**: Route to appropriate handler:
   - Health questions → Medical-aware responses
   - Food logs → Nutritional analysis
   - General → Personalized recommendations

3. **Storage**: Log interactions for learning and pattern recognition

## Implementation Steps

### 1. Environment Setup

```bash
# Install dependencies
pip install -r meal_mentor_requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_backup_key
# SUPABASE_URL=your_supabase_url
# SUPABASE_ANON_KEY=your_supabase_key
```

### 2. Database Setup

```bash
# Run the schema creation
psql -d your_database -f meal_mentor_schema.sql

# Or use Supabase dashboard to execute the SQL
```

### 3. Running the System

```bash
# Start the Streamlit app
streamlit run meal_mentor_system.py
```

## Handling Text-Based Food Input

### Input Examples and Processing

**Example 1: Simple Food Log**
```
User: "I had a chicken salad for lunch"

System Processing:
1. Classify as FOOD_LOG_TEXT
2. Extract: food="chicken salad", meal="lunch"
3. AI Analysis: Estimate calories, nutrients, health assessment
4. Store in database with timestamp
5. Respond with nutritional breakdown
```

**Example 2: Health-Conscious Query**
```
User: "My stomach has been uneasy and I've had diarrhea. What should I eat?"

System Processing:
1. Classify as HEALTH_QUESTION
2. Extract symptoms: ["stomach uneasy", "diarrhea"]
3. AI Response: BRAT diet suggestions + medical disclaimer
4. Store health query for pattern tracking
5. Suggest follow-up if symptoms persist
```

### AI Prompt Engineering

The system uses specialized prompts for different scenarios:

#### Health Question Prompt
```python
system_prompt = """You are a knowledgeable nutrition assistant helping people with dietary questions. 

IMPORTANT MEDICAL DISCLAIMER: 
- You are NOT a medical professional and cannot provide medical diagnosis or treatment
- For serious symptoms, digestive issues, or ongoing health concerns, always recommend consulting a healthcare provider
- Your role is to provide general nutritional guidance and food suggestions

CAPABILITIES:
- Suggest appropriate foods for common digestive issues (nausea, diarrhea, upset stomach)
- Provide general nutrition advice
- Recommend hydration and gentle foods
- Explain how certain foods might help or worsen common symptoms
"""
```

#### Food Analysis Prompt
```python
system_prompt = """You are a nutrition analysis assistant. Analyze food descriptions and provide detailed nutritional breakdowns.

TASK: Parse the food description and provide:
1. Structured food items with portions
2. Estimated calorie count per item and total
3. Macronutrient breakdown (carbs, protein, fat, fiber)
4. Key nutrients and vitamins
5. Meal classification (breakfast, lunch, dinner, snack)
6. Health assessment (balanced, high sodium, high sugar, etc.)
"""
```

## Key Technical Decisions

### 1. **AI Provider Choice**
- **Primary**: Claude (Anthropic) - Better for health/medical contexts
- **Fallback**: OpenAI GPT-4 - Broader availability
- **Reasoning**: Claude is more cautious with medical advice and provides better disclaimers

### 2. **Message Classification**
- **Keyword-based classification** for speed and reliability
- **Health keywords**: stomach, nausea, sick, pain, allergic, etc.
- **Food keywords**: ate, meal, breakfast, calories, etc.
- **Extensible**: Can add ML-based classification later

### 3. **Data Storage Strategy**
- **Structured logging**: Separate tables for food logs and health queries
- **JSON fields**: Flexible storage for nutritional data and metadata
- **User privacy**: Row-level security policies
- **Pattern tracking**: Store for learning user preferences

## Safety and Medical Considerations

### Medical Disclaimers
- Always include disclaimers for health advice
- Recommend healthcare providers for serious symptoms
- Avoid diagnosis or treatment recommendations
- Focus on general nutritional guidance

### Data Privacy
- Implement row-level security
- User data isolation
- Optional anonymization for research
- GDPR/HIPAA considerations

### Content Filtering
- Avoid harmful diet advice
- Flag extreme calorie restrictions
- Identify eating disorder indicators
- Provide crisis resources when needed

## Usage Examples

### Scenario 1: User with Digestive Issues

```python
# User input: "I have IBS and feeling bloated after eating beans"

# System response process:
1. Classification: HEALTH_QUESTION
2. Symptom extraction: ["IBS", "bloated", "beans"]
3. Context analysis: Food trigger identification
4. Response: 
   - Explain beans and IBS connection
   - Suggest low-FODMAP alternatives
   - Recommend smaller portions
   - Include medical disclaimer
   - Store for pattern analysis
```

### Scenario 2: Regular Food Logging

```python
# User input: "Breakfast: 2 eggs, whole wheat toast, avocado, coffee"

# System response process:
1. Classification: FOOD_LOG_TEXT
2. Food parsing: Extract individual items
3. Nutritional analysis:
   - Eggs: ~140 cal, 12g protein
   - Toast: ~80 cal, 3g protein, 15g carbs
   - Avocado: ~160 cal, 15g healthy fats
   - Coffee: ~5 cal
   - Total: ~385 calories
4. Health assessment: "Balanced breakfast with good protein and healthy fats"
5. Store in food_logs table
```

## Future Enhancements

### 1. **Photo Integration**
- Add image processing for food photos
- Visual portion estimation
- Automatic food recognition
- Integration with existing text system

### 2. **Advanced Analytics**
- Trend analysis and insights
- Nutritional gap identification
- Symptom-food correlation detection
- Personalized meal planning

### 3. **Integration Options**
- Wearable device data
- Nutrition database APIs
- Healthcare provider portals
- Meal delivery services

## Testing and Validation

### Test Cases
1. **Health Question Classification**
   - Various symptom descriptions
   - Emergency situations (proper escalation)
   - General nutrition questions

2. **Food Logging Accuracy**
   - Different food description styles
   - Complex meals with multiple items
   - Portion size estimation

3. **Personalization**
   - Learning from user history
   - Dietary restriction handling
   - Preference adaptation

### Quality Assurance
- Medical professional review of health responses
- Nutritionist validation of food analysis
- User experience testing
- Safety protocol verification

## Deployment Considerations

### Production Setup
1. **Environment Configuration**
   - Separate staging/production environments
   - Secure API key management
   - Database backup strategies

2. **Monitoring and Logging**
   - User interaction tracking
   - Error monitoring and alerting
   - Performance metrics
   - Usage analytics

3. **Scaling Strategies**
   - Database optimization
   - AI API rate limiting
   - Caching strategies
   - Load balancing

## Support and Maintenance

### Regular Updates
- AI model improvements
- Nutrition database updates
- User feedback integration
- Security patches

### User Support
- FAQ and help documentation
- Error handling and recovery
- User onboarding guides
- Community features

This implementation provides a robust foundation for handling both text-based food logging and health questions while maintaining appropriate medical boundaries and user safety.