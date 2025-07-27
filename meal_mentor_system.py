import streamlit as st
import pandas as pd
from supabase import create_client
import os
import json
from typing import List, Dict, Any, Optional
import openai
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY') 
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Initialize clients
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

# Choose AI provider (prefer Claude for health advice)
try:
    import anthropic
    if ANTHROPIC_API_KEY:
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        AI_PROVIDER = "claude"
    else:
        raise ImportError("No Anthropic API key")
except ImportError:
    if OPENAI_API_KEY:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        AI_PROVIDER = "openai"
    else:
        AI_PROVIDER = None

class MessageType(Enum):
    HEALTH_QUESTION = "health_question"
    FOOD_LOG_TEXT = "food_log_text"
    FOOD_LOG_PHOTO = "food_log_photo"
    GENERAL_CHAT = "general_chat"

@dataclass
class FoodLogEntry:
    user_id: str
    timestamp: datetime
    food_description: str
    estimated_calories: Optional[int] = None
    nutritional_analysis: Optional[Dict] = None
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    symptoms_noted: Optional[str] = None
    context: Optional[str] = None  # "feeling unwell", "post-workout", etc.

@dataclass 
class HealthQuery:
    user_id: str
    timestamp: datetime
    question: str
    symptoms: Optional[List[str]] = None
    context: Optional[str] = None
    urgency_level: str = "normal"  # low, normal, high, urgent

class MealMentorSystem:
    def __init__(self):
        self.supabase = supabase
        self.ai_provider = AI_PROVIDER
        
    def classify_message_type(self, message: str) -> MessageType:
        """Classify the type of user message to determine appropriate handling."""
        
        # Health question indicators
        health_keywords = [
            "stomach", "nausea", "diarrhea", "constipation", "bloating", 
            "headache", "fatigue", "dizzy", "pain", "hurt", "sick", "ill",
            "should i eat", "what should i eat", "is it safe", "can i eat",
            "allergic", "allergy", "intolerant", "sensitivity", "reaction"
        ]
        
        # Food logging indicators  
        food_keywords = [
            "ate", "eating", "had for", "consumed", "meal", "breakfast", 
            "lunch", "dinner", "snack", "food", "calories", "portion"
        ]
        
        message_lower = message.lower()
        
        # Check for health questions first (higher priority)
        if any(keyword in message_lower for keyword in health_keywords):
            return MessageType.HEALTH_QUESTION
            
        # Check for food logging
        if any(keyword in message_lower for keyword in food_keywords):
            return MessageType.FOOD_LOG_TEXT
            
        return MessageType.GENERAL_CHAT

    def process_health_question(self, query: HealthQuery) -> str:
        """Process health-related questions with appropriate medical disclaimers."""
        
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

RESPONSE STYLE:
- Be empathetic and supportive
- Always include medical disclaimer when appropriate
- Provide practical, actionable food suggestions
- Ask follow-up questions to better understand their needs
- Suggest when to seek medical attention

Current context: User is asking about food choices related to their health symptoms."""

        user_message = f"""User question: {query.question}

Additional context:
- Symptoms mentioned: {', '.join(query.symptoms) if query.symptoms else 'None specified'}
- Context: {query.context or 'Not provided'}
- Urgency level: {query.urgency_level}

Please provide helpful nutritional guidance while maintaining appropriate medical boundaries."""

        return self._get_ai_response(system_prompt, user_message)

    def process_food_log_text(self, food_description: str, user_id: str, context: str = None) -> Dict[str, Any]:
        """Process text-based food logging and extract nutritional information."""
        
        system_prompt = """You are a nutrition analysis assistant. Analyze food descriptions and provide detailed nutritional breakdowns.

TASK: Parse the food description and provide:
1. Structured food items with portions
2. Estimated calorie count per item and total
3. Macronutrient breakdown (carbs, protein, fat, fiber)
4. Key nutrients and vitamins
5. Meal classification (breakfast, lunch, dinner, snack)
6. Health assessment (balanced, high sodium, high sugar, etc.)

RESPONSE FORMAT: Provide a detailed but conversational analysis that could be logged in a food diary."""

        user_message = f"""Food description: {food_description}

Context: {context or 'Regular meal logging'}

Please analyze this food intake and provide nutritional insights."""

        # Get AI analysis
        analysis = self._get_ai_response(system_prompt, user_message)
        
        # Create food log entry
        food_entry = FoodLogEntry(
            user_id=user_id,
            timestamp=datetime.now(),
            food_description=food_description,
            context=context
        )
        
        # Store in database if available
        if self.supabase:
            self._store_food_log_entry(food_entry, analysis)
        
        return {
            "analysis": analysis,
            "food_entry": food_entry,
            "stored": self.supabase is not None
        }

    def get_personalized_recommendations(self, user_id: str, current_symptoms: List[str] = None) -> str:
        """Get personalized food recommendations based on user history and current state."""
        
        # Get user's food history if available
        food_history = self._get_user_food_history(user_id) if self.supabase else []
        
        system_prompt = """You are a personalized nutrition mentor. Based on the user's food history and current symptoms, provide tailored recommendations.

CAPABILITIES:
- Learn from user's eating patterns and preferences
- Suggest foods that align with their dietary habits
- Recommend foods that might help with current symptoms
- Identify potential trigger foods based on patterns
- Provide gentle, sustainable dietary adjustments

RESPONSE STYLE:
- Be supportive and encouraging
- Reference their past food choices when relevant
- Provide specific, actionable suggestions
- Explain the reasoning behind recommendations"""

        user_message = f"""User ID: {user_id}
Current symptoms: {', '.join(current_symptoms) if current_symptoms else 'None'}

Food history summary: {self._summarize_food_history(food_history)}

Please provide personalized food recommendations for this user."""

        return self._get_ai_response(system_prompt, user_message)

    def _get_ai_response(self, system_prompt: str, user_message: str) -> str:
        """Get response from AI provider (Claude preferred for health advice)."""
        
        if self.ai_provider == "claude":
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}]
                )
                return response.content[0].text
            except Exception as e:
                st.error(f"Claude API error: {e}")
                return "I'm having trouble processing your request right now. Please try again later."
                
        elif self.ai_provider == "openai":
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=1024,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                st.error(f"OpenAI API error: {e}")
                return "I'm having trouble processing your request right now. Please try again later."
        else:
            return "AI service is not available. Please check your API configuration."

    def _store_food_log_entry(self, entry: FoodLogEntry, analysis: str):
        """Store food log entry in database."""
        try:
            data = {
                "user_id": entry.user_id,
                "timestamp": entry.timestamp.isoformat(),
                "food_description": entry.food_description,
                "ai_analysis": analysis,
                "meal_type": entry.meal_type,
                "symptoms_noted": entry.symptoms_noted,
                "context": entry.context,
                "estimated_calories": entry.estimated_calories
            }
            
            result = self.supabase.table('food_logs').insert(data).execute()
            return result.data
        except Exception as e:
            st.error(f"Error storing food log: {e}")
            return None

    def _get_user_food_history(self, user_id: str, days: int = 7) -> List[Dict]:
        """Retrieve user's recent food history."""
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=days)).isoformat()
            
            result = self.supabase.table('food_logs').select('*').eq(
                'user_id', user_id
            ).gte('timestamp', cutoff_date).order('timestamp', desc=True).execute()
            
            return result.data
        except Exception as e:
            st.error(f"Error retrieving food history: {e}")
            return []

    def _summarize_food_history(self, food_history: List[Dict]) -> str:
        """Create a summary of user's food history for context."""
        if not food_history:
            return "No recent food history available."
        
        summary = f"Recent food entries ({len(food_history)} items):\n"
        for entry in food_history[-5:]:  # Last 5 entries
            timestamp = entry.get('timestamp', 'Unknown time')
            food_desc = entry.get('food_description', 'No description')
            summary += f"- {timestamp}: {food_desc}\n"
        
        return summary

def create_meal_mentor_ui():
    """Create the Streamlit UI for the meal mentor system."""
    
    st.title("🥗 Meal Mentor - Your Personal Nutrition Assistant")
    
    # Initialize system
    if 'meal_mentor' not in st.session_state:
        st.session_state.meal_mentor = MealMentorSystem()
    
    # User identification
    st.sidebar.title("👤 User Settings")
    user_id = st.sidebar.text_input("User ID", value="user_001", help="Enter your unique user ID")
    
    # Chat interface
    st.subheader("💬 Chat with Your Meal Mentor")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.chat_message("user").write(message['content'])
        else:
            st.chat_message("assistant").write(message['content'])
    
    # Chat input
    if prompt := st.chat_input("Ask a health question or log your food..."):
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Process the message
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                message_type = st.session_state.meal_mentor.classify_message_type(prompt)
                
                if message_type == MessageType.HEALTH_QUESTION:
                    # Extract symptoms and context
                    query = HealthQuery(
                        user_id=user_id,
                        timestamp=datetime.now(),
                        question=prompt
                    )
                    response = st.session_state.meal_mentor.process_health_question(query)
                    
                elif message_type == MessageType.FOOD_LOG_TEXT:
                    # Process food logging
                    result = st.session_state.meal_mentor.process_food_log_text(
                        food_description=prompt,
                        user_id=user_id
                    )
                    response = result['analysis']
                    if result['stored']:
                        response += "\n\n✅ Food entry has been logged to your diary."
                    
                else:
                    # General nutrition conversation
                    response = st.session_state.meal_mentor.get_personalized_recommendations(
                        user_id=user_id
                    )
                
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Food logging section
    st.subheader("📝 Quick Food Log")
    
    col1, col2 = st.columns(2)
    
    with col1:
        food_description = st.text_area(
            "Describe what you ate:",
            placeholder="e.g., 'I had a chicken salad with mixed greens, tomatoes, and olive oil dressing for lunch'"
        )
        
        meal_type = st.selectbox(
            "Meal type:",
            ["Breakfast", "Lunch", "Dinner", "Snack", "Other"]
        )
    
    with col2:
        symptoms = st.text_area(
            "Any symptoms or how you're feeling? (optional)",
            placeholder="e.g., 'feeling nauseous', 'had stomach pain after eating'"
        )
        
        context = st.text_input(
            "Additional context (optional)",
            placeholder="e.g., 'post-workout meal', 'eating out'"
        )
    
    if st.button("Log Food Entry"):
        if food_description:
            with st.spinner("Analyzing your food..."):
                result = st.session_state.meal_mentor.process_food_log_text(
                    food_description=food_description,
                    user_id=user_id,
                    context=f"Meal: {meal_type}. Symptoms: {symptoms}. Context: {context}"
                )
                
                st.success("Food logged successfully!")
                st.write("**Nutritional Analysis:**")
                st.write(result['analysis'])
        else:
            st.warning("Please describe what you ate.")
    
    # Health tips section
    st.subheader("💡 Daily Health Tips")
    
    if st.button("Get Personalized Recommendations"):
        with st.spinner("Generating recommendations..."):
            recommendations = st.session_state.meal_mentor.get_personalized_recommendations(user_id)
            st.write(recommendations)

if __name__ == "__main__":
    create_meal_mentor_ui()