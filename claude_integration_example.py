#!/usr/bin/env python3
"""
Example script demonstrating Claude integration for the Meal Mentor system.
This shows how to handle text-based food logging and health questions.
"""

import os
from datetime import datetime
from typing import Dict, Any
import json

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Note: Anthropic library not installed. Install with: pip install anthropic")

def create_claude_client():
    """Initialize Claude client with API key."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    return anthropic.Anthropic(api_key=api_key)

def classify_user_message(message: str) -> str:
    """Simple keyword-based classification of user messages."""
    message_lower = message.lower()
    
    # Health-related keywords
    health_keywords = [
        "stomach", "nausea", "diarrhea", "constipation", "bloating", 
        "headache", "fatigue", "dizzy", "pain", "hurt", "sick", "ill",
        "should i eat", "what should i eat", "is it safe", "can i eat",
        "allergic", "allergy", "intolerant", "sensitivity", "reaction"
    ]
    
    # Food logging keywords
    food_keywords = [
        "ate", "eating", "had for", "consumed", "meal", "breakfast", 
        "lunch", "dinner", "snack", "food", "calories", "portion"
    ]
    
    if any(keyword in message_lower for keyword in health_keywords):
        return "HEALTH_QUESTION"
    elif any(keyword in message_lower for keyword in food_keywords):
        return "FOOD_LOG"
    else:
        return "GENERAL_CHAT"

def process_health_question(client, user_message: str) -> str:
    """Process health-related questions with medical disclaimers."""
    
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

Remember: Focus on nutrition and food choices, not medical diagnosis or treatment."""

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        return f"I'm having trouble processing your health question right now. Please consult a healthcare provider for medical concerns. Error: {str(e)}"

def process_food_log(client, user_message: str) -> Dict[str, Any]:
    """Process text-based food logging with nutritional analysis."""
    
    system_prompt = """You are a nutrition analysis assistant. Analyze food descriptions and provide detailed nutritional breakdowns.

TASK: Parse the food description and provide a structured analysis including:
1. Individual food items with estimated portions
2. Estimated calorie count per item and total
3. Macronutrient breakdown (carbs, protein, fat, fiber)
4. Key nutrients and vitamins present
5. Meal classification (breakfast, lunch, dinner, snack)
6. Health assessment (balanced, high sodium, high sugar, etc.)
7. Suggestions for improvement if applicable

RESPONSE FORMAT: 
Provide a conversational but detailed analysis that includes:
- Summary of foods consumed
- Nutritional breakdown
- Health assessment
- Any recommendations

Be encouraging and constructive in your feedback."""

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Please analyze this food intake: {user_message}"}]
        )
        
        analysis = response.content[0].text
        
        # Create a structured log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "food_description": user_message,
            "ai_analysis": analysis,
            "classification": "food_log"
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "log_entry": log_entry
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to analyze food intake at this time."
        }

def get_general_nutrition_advice(client, user_message: str) -> str:
    """Provide general nutrition guidance and recommendations."""
    
    system_prompt = """You are a friendly nutrition mentor providing general dietary guidance.

CAPABILITIES:
- General nutrition education
- Healthy eating tips
- Food choice recommendations
- Meal planning suggestions
- Nutritional goal support

RESPONSE STYLE:
- Be encouraging and supportive
- Provide practical, actionable advice
- Focus on sustainable healthy habits
- Ask follow-up questions to better help
- Avoid medical advice or diagnosis

Remember: You're a nutrition educator, not a medical professional."""

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        return f"I'm having trouble providing nutrition advice right now. Please try again later. Error: {str(e)}"

def demo_meal_mentor():
    """Demonstrate the meal mentor system with example interactions."""
    
    if not CLAUDE_AVAILABLE:
        print("Claude integration not available. Please install: pip install anthropic")
        return
    
    print("🥗 Meal Mentor Demo - Claude Integration")
    print("=" * 50)
    
    try:
        client = create_claude_client()
        print("✅ Claude client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Claude client: {e}")
        return
    
    # Example interactions
    test_cases = [
        {
            "message": "My stomach has been uneasy and I've had diarrhea. What should I eat?",
            "expected_type": "HEALTH_QUESTION"
        },
        {
            "message": "I had a chicken salad with mixed greens, tomatoes, and olive oil dressing for lunch",
            "expected_type": "FOOD_LOG"
        },
        {
            "message": "What are some good breakfast ideas for weight loss?",
            "expected_type": "GENERAL_CHAT"
        },
        {
            "message": "I ate pizza and feel bloated. Is this normal?",
            "expected_type": "HEALTH_QUESTION"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        message = test_case["message"]
        expected = test_case["expected_type"]
        
        print(f"User: {message}")
        
        # Classify message
        classification = classify_user_message(message)
        print(f"Classification: {classification} (expected: {expected})")
        
        # Process based on classification
        if classification == "HEALTH_QUESTION":
            response = process_health_question(client, message)
            print(f"Health Response: {response[:200]}...")
            
        elif classification == "FOOD_LOG":
            result = process_food_log(client, message)
            if result["success"]:
                print(f"Food Log Analysis: {result['analysis'][:200]}...")
                print(f"Log Entry Created: {result['log_entry']['timestamp']}")
            else:
                print(f"Food Log Error: {result['message']}")
                
        else:  # GENERAL_CHAT
            response = get_general_nutrition_advice(client, message)
            print(f"General Advice: {response[:200]}...")
        
        print("-" * 30)

def interactive_demo():
    """Interactive demo where users can type messages."""
    
    if not CLAUDE_AVAILABLE:
        print("Claude integration not available. Please install: pip install anthropic")
        return
    
    print("🥗 Interactive Meal Mentor Demo")
    print("Type 'quit' to exit, 'help' for examples")
    print("=" * 50)
    
    try:
        client = create_claude_client()
        print("✅ Connected to Claude")
    except Exception as e:
        print(f"❌ Failed to connect to Claude: {e}")
        return
    
    conversation_history = []
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            print("👋 Thanks for using Meal Mentor!")
            break
        elif user_input.lower() == 'help':
            print("\nExample messages:")
            print("- 'I had oatmeal with berries for breakfast'")
            print("- 'My stomach hurts after eating dairy'")
            print("- 'What are healthy snack options?'")
            continue
        elif not user_input:
            continue
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_input, "timestamp": datetime.now()})
        
        # Classify and process
        classification = classify_user_message(user_input)
        print(f"[{classification}]", end=" ")
        
        try:
            if classification == "HEALTH_QUESTION":
                response = process_health_question(client, user_input)
            elif classification == "FOOD_LOG":
                result = process_food_log(client, user_input)
                if result["success"]:
                    response = result["analysis"] + "\n\n✅ Food entry logged!"
                else:
                    response = result["message"]
            else:
                response = get_general_nutrition_advice(client, user_input)
            
            print(f"Mentor: {response}")
            conversation_history.append({"role": "assistant", "content": response, "timestamp": datetime.now()})
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Automated demo with test cases")
    print("2. Interactive chat demo")
    
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "1":
        demo_meal_mentor()
    elif choice == "2":
        interactive_demo()
    else:
        print("Invalid choice. Running automated demo...")
        demo_meal_mentor()