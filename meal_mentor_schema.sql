-- Meal Mentor Database Schema
-- This schema supports text-based food logging and health question tracking

-- Table for storing food log entries
CREATE TABLE IF NOT EXISTS food_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    food_description TEXT NOT NULL,
    ai_analysis TEXT,
    estimated_calories INTEGER,
    meal_type VARCHAR(50), -- breakfast, lunch, dinner, snack, other
    symptoms_noted TEXT,
    context TEXT,
    nutritional_data JSONB, -- Store detailed nutritional breakdown
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for storing health queries and responses
CREATE TABLE IF NOT EXISTS health_queries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    question TEXT NOT NULL,
    ai_response TEXT,
    symptoms TEXT[], -- Array of symptoms mentioned
    context TEXT,
    urgency_level VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    follow_up_needed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for user profiles and preferences
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    dietary_restrictions TEXT[], -- allergies, intolerances, preferences
    health_conditions TEXT[], -- conditions that affect diet
    goals TEXT[], -- weight loss, muscle gain, general health, etc.
    preferred_meal_times JSONB, -- structured meal timing preferences
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for tracking user patterns and insights
CREATE TABLE IF NOT EXISTS user_insights (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    insight_type VARCHAR(100) NOT NULL, -- food_pattern, symptom_trigger, nutrition_gap
    insight_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Table for storing chat conversation history
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    message_type VARCHAR(50), -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB, -- additional context like message classification
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Table for food database (optional - for better nutritional analysis)
CREATE TABLE IF NOT EXISTS food_database (
    id SERIAL PRIMARY KEY,
    food_name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    serving_size VARCHAR(100),
    calories_per_serving INTEGER,
    macronutrients JSONB, -- protein, carbs, fat, fiber
    micronutrients JSONB, -- vitamins, minerals
    allergens TEXT[],
    food_group VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_food_logs_user_id ON food_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_food_logs_timestamp ON food_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_health_queries_user_id ON health_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_health_queries_timestamp ON health_queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_insights_user_id ON user_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id);

-- Row Level Security (RLS) policies for user data protection
ALTER TABLE food_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Create policies (example - adjust based on your authentication system)
CREATE POLICY "Users can only access their own food logs" ON food_logs
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own health queries" ON health_queries
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own profile" ON user_profiles
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own insights" ON user_insights
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own chat history" ON chat_history
    FOR ALL USING (auth.uid()::text = user_id);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW recent_food_logs AS
SELECT 
    user_id,
    food_description,
    meal_type,
    estimated_calories,
    symptoms_noted,
    timestamp,
    ai_analysis
FROM food_logs 
WHERE timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

CREATE OR REPLACE VIEW user_nutrition_summary AS
SELECT 
    user_id,
    DATE(timestamp) as log_date,
    COUNT(*) as meals_logged,
    SUM(estimated_calories) as total_calories,
    ARRAY_AGG(DISTINCT meal_type) as meal_types,
    ARRAY_AGG(DISTINCT symptoms_noted) FILTER (WHERE symptoms_noted IS NOT NULL) as symptoms
FROM food_logs 
GROUP BY user_id, DATE(timestamp)
ORDER BY log_date DESC;

-- Sample data for testing (remove in production)
INSERT INTO user_profiles (user_id, display_name, dietary_restrictions, health_conditions, goals) VALUES
('user_001', 'Test User', ARRAY['lactose intolerant'], ARRAY['IBS'], ARRAY['digestive health'])
ON CONFLICT (user_id) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE food_logs IS 'Stores user food entries with AI analysis and nutritional information';
COMMENT ON TABLE health_queries IS 'Tracks health-related questions and AI responses for pattern analysis';
COMMENT ON TABLE user_profiles IS 'User preferences, restrictions, and health information for personalization';
COMMENT ON TABLE user_insights IS 'AI-generated insights about user patterns and recommendations';
COMMENT ON TABLE chat_history IS 'Complete conversation history for context and learning';
COMMENT ON TABLE food_database IS 'Optional structured food database for enhanced nutritional analysis';