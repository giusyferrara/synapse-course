"""
Setup lesson content tables in PostgreSQL
"""
from database.config import engine
from sqlalchemy import text

# SQL Schema
schema_sql = """
-- Synapse Lesson Content Database
DROP TABLE IF EXISTS lesson_exercises CASCADE;
DROP TABLE IF EXISTS lesson_examples CASCADE;
DROP TABLE IF EXISTS lesson_content CASCADE;

CREATE TABLE lesson_content (
    id SERIAL PRIMARY KEY,
    topic_id VARCHAR(100) UNIQUE NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    level VARCHAR(50) NOT NULL,
    
    introduction TEXT NOT NULL,
    explanation TEXT NOT NULL,
    key_points JSONB NOT NULL,
    misconceptions JSONB,
    applications JSONB,
    
    duration VARCHAR(50),
    difficulty INTEGER DEFAULT 1,
    prerequisites JSONB,
    learning_outcomes JSONB,
    
    source_book VARCHAR(255),
    source_chapter VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lesson_examples (
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

CREATE TABLE lesson_exercises (
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
"""

try:
    with engine.connect() as conn:
        # Execute each statement
        for statement in schema_sql.split(';'):
            if statement.strip():
                conn.execute(text(statement))
                conn.commit()
    
    print("✅ Tables created successfully!")
    
    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'lesson%'
            ORDER BY table_name;
        """))
        
        print("\n📊 Created tables:")
        for row in result:
            print(f"  ✓ {row[0]}")

except Exception as e:
    print(f"❌ Error: {e}")
