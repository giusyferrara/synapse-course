-- Synapse Lesson Content Database
-- Professional Python course content

CREATE TABLE IF NOT EXISTS lesson_content (
    id SERIAL PRIMARY KEY,
    topic_id VARCHAR(100) UNIQUE NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    level VARCHAR(50) NOT NULL,
    
    -- Theory content
    introduction TEXT NOT NULL,
    explanation TEXT NOT NULL,
    key_points JSONB NOT NULL,
    misconceptions JSONB,
    applications JSONB,
    
    -- Metadata
    duration VARCHAR(50),
    difficulty INTEGER DEFAULT 1,
    prerequisites JSONB,
    learning_outcomes JSONB,
    
    -- Source attribution
    source_book VARCHAR(255),
    source_chapter VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lesson_examples (
    id SERIAL PRIMARY KEY,
    topic_id VARCHAR(100) REFERENCES lesson_content(topic_id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    explanation TEXT,
    expected_output TEXT,
    difficulty INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lesson_exercises (
    id SERIAL PRIMARY KEY,
    topic_id VARCHAR(100) REFERENCES lesson_content(topic_id),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    starter_code TEXT,
    solution_code TEXT,
    expected_output TEXT,
    hints JSONB,
    test_cases JSONB,
    order_index INTEGER DEFAULT 0
);

CREATE INDEX idx_topic_level ON lesson_content(level);
CREATE INDEX idx_topic_id ON lesson_content(topic_id);
