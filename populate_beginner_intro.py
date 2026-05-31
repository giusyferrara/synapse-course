"""
Beginner Lesson: Introduction to Python
Based on: https://docs.python.org/3/tutorial/introduction.html
Official Python Documentation - The Python Tutorial
"""
from database.config import engine
from sqlalchemy import text
import json

def add_lesson(conn, topic_id, topic_name, level, introduction, explanation, 
               key_points, misconceptions, applications, duration, source_book, source_chapter):
    conn.execute(text("""
        INSERT INTO lesson_content 
        (topic_id, topic_name, level, introduction, explanation, 
         key_points, misconceptions, applications, duration, 
         source_book, source_chapter)
        VALUES 
        (:topic_id, :topic_name, :level, :introduction, :explanation,
         :key_points, :misconceptions, :applications, :duration,
         :source_book, :source_chapter)
        ON CONFLICT (topic_id) DO UPDATE SET
            introduction = EXCLUDED.introduction,
            explanation = EXCLUDED.explanation,
            key_points = EXCLUDED.key_points,
            misconceptions = EXCLUDED.misconceptions,
            applications = EXCLUDED.applications
    """), {
        "topic_id": topic_id,
        "topic_name": topic_name,
        "level": level,
        "introduction": introduction,
        "explanation": explanation,
        "key_points": json.dumps(key_points),
        "misconceptions": json.dumps(misconceptions),
        "applications": json.dumps(applications),
        "duration": duration,
        "source_book": source_book,
        "source_chapter": source_chapter
    })
    conn.commit()

def add_example(conn, topic_id, title, description, code, explanation, expected_output, order_index):
    conn.execute(text("""
        INSERT INTO lesson_examples 
        (topic_id, title, description, code, explanation, expected_output, order_index)
        VALUES 
        (:topic_id, :title, :description, :code, :explanation, :expected_output, :order_index)
    """), {
        "topic_id": topic_id,
        "title": title,
        "description": description,
        "code": code,
        "explanation": explanation,
        "expected_output": expected_output,
        "order_index": order_index
    })
    conn.commit()

def add_exercise(conn, topic_id, title, description, difficulty, starter_code, 
                 solution_code, expected_output, hints, order_index):
    conn.execute(text("""
        INSERT INTO lesson_exercises 
        (topic_id, title, description, difficulty, starter_code, 
         solution_code, expected_output, hints, order_index)
        VALUES 
        (:topic_id, :title, :description, :difficulty, :starter_code,
         :solution_code, :expected_output, :hints, :order_index)
    """), {
        "topic_id": topic_id,
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "starter_code": starter_code,
        "solution_code": solution_code,
        "expected_output": expected_output,
        "hints": json.dumps(hints),
        "order_index": order_index
    })
    conn.commit()

print("📚 Populating Beginner Lesson: Introduction to Python")
print("   Source: Official Python Tutorial (docs.python.org)")

with engine.connect() as conn:
    
    # LESSON: Introduction to Python
    add_lesson(
        conn,
        topic_id="intro",
        topic_name="Introduction to Python",
        level="beginner",
        
        introduction="""Python is a powerful, easy-to-learn programming language. The interpreter acts as a simple calculator where you can type expressions and see results immediately. Python uses indentation to group statements, making code naturally readable and clean.""",
        
        explanation="""Python is an interpreted language, which means you can run your programs immediately without compiling. When you start Python, you see the prompt (>>>) where you can type commands and get instant feedback.

The Python interpreter can be used interactively as a desk calculator. You can type mathematical expressions like 2 + 2 or 50 - 5*6 and see the results right away. This makes learning Python fun and immediate - you don't have to wait to compile and run a program.

Python uses indentation (spaces at the start of lines) to define code blocks. This is different from languages that use curly braces. The required indentation makes all Python code look similar and forces you to write readable code from the start.

The language includes powerful data types like strings for text, lists for collections of items, and dictionaries for key-value pairs. These built-in types are efficient and easy to use, letting you focus on solving problems rather than managing memory.""",
        
        key_points=[
            "Python interpreter provides immediate feedback - type and see results",
            "No compilation needed - write code and run it instantly",
            "Indentation defines code structure - forced readability",
            "Built-in powerful data types - strings, lists, dictionaries",
            "Interactive mode perfect for learning and experimenting"
        ],
        
        misconceptions=[
            "Python is only for beginners - False! Used by Google, NASA, and Netflix for critical systems",
            "You can't do serious math - Python has full support for complex numbers, decimals, and fractions",
            "Indentation is annoying - It actually makes code more readable and prevents common errors"
        ],
        
        applications=[
            "Scientific Computing - NumPy, SciPy for numerical computations",
            "Data Analysis - Pandas for working with datasets",
            "Web Development - Django and Flask frameworks",
            "Automation - Scripts to automate repetitive tasks",
            "Machine Learning - TensorFlow and PyTorch"
        ],
        
        duration="45 min",
        source_book="Official Python Tutorial",
        source_chapter="docs.python.org/3/tutorial/introduction.html"
    )
    
    print("  ✓ Lesson content added")
    
    # EXAMPLES
    add_example(
        conn,
        topic_id="intro",
        title="Using Python as a Calculator",
        description="The interpreter can act as a simple calculator. Type expressions and get results.",
        code="""2 + 2
50 - 5*6
(50 - 5*6) / 4
8 / 5  # division always returns a float""",
        explanation="Expression syntax is straightforward: +, -, *, / work as expected. Parentheses group operations. Division (/) always returns a floating-point number.",
        expected_output="4\n20\n5.0\n1.6",
        order_index=1
    )
    
    add_example(
        conn,
        topic_id="intro",
        title="Variables and Assignment",
        description="Use the equal sign (=) to assign values to variables.",
        code="""width = 20
height = 5 * 9
width * height""",
        explanation="Variables store values. The variable name goes on the left of =, the value on the right. You can use variables in calculations.",
        expected_output="900",
        order_index=2
    )
    
    add_example(
        conn,
        topic_id="intro",
        title="Working with Strings",
        description="Strings are enclosed in quotes and can be manipulated easily.",
        code="""'Hello, World!'
"Python is fun!"
'doesn\\'t'  # use \\' to escape quotes
print('First line.\\nSecond line.')""",
        explanation="Use single or double quotes for strings. Escape special characters with backslash. The print() function interprets escape sequences like \\n for newlines.",
        expected_output="'Hello, World!'\n'Python is fun!'\n\"doesn't\"\nFirst line.\nSecond line.",
        order_index=3
    )
    
    print("  ✓ 3 examples added")
    
    # EXERCISES
    add_exercise(
        conn,
        topic_id="intro",
        title="Simple Calculation",
        description="Calculate: 15 + 27. Type the expression and see the result.",
        difficulty="easy",
        starter_code="# Type your calculation\n",
        solution_code="15 + 27",
        expected_output="42",
        hints=[
            "Just type the numbers with the + operator",
            "Like this: 15 + 27",
            "Press Enter to see the answer"
        ],
        order_index=1
    )
    
    add_exercise(
        conn,
        topic_id="intro",
        title="Power Operation",
        description="Calculate 5 to the power of 2 using the ** operator.",
        difficulty="easy",
        starter_code="# Use the ** operator for powers\n",
        solution_code="5 ** 2",
        expected_output="25",
        hints=[
            "The ** operator calculates powers",
            "Format: base ** exponent",
            "Try: 5 ** 2"
        ],
        order_index=2
    )
    
    add_exercise(
        conn,
        topic_id="intro",
        title="Rectangle Area",
        description="Create variables width=20 and height=45, then calculate the area.",
        difficulty="easy",
        starter_code="# Create variables and calculate\nwidth = 20\nheight = 45\n",
        solution_code="width = 20\nheight = 45\nwidth * height",
        expected_output="900",
        hints=[
            "Multiply width by height",
            "Type: width * height",
            "Variables are already defined, just multiply them"
        ],
        order_index=3
    )
    
    add_exercise(
        conn,
        topic_id="intro",
        title="String Concatenation",
        description="Combine 'Hello, ' and 'Python!' using the + operator and print the result.",
        difficulty="medium",
        starter_code="# Combine strings\ngreeting = 'Hello, '\nlanguage = 'Python!'\n",
        solution_code="greeting = 'Hello, '\nlanguage = 'Python!'\nprint(greeting + language)",
        expected_output="Hello, Python!",
        hints=[
            "Use + to join strings",
            "greeting + language combines them",
            "Wrap in print() to display the result"
        ],
        order_index=4
    )
    
    add_exercise(
        conn,
        topic_id="intro",
        title="Multiple Line Output",
        description="Print 'Python' on one line and 'Programming' on the next using \\n.",
        difficulty="medium",
        starter_code="# Use \\n for newline\n",
        solution_code="print('Python\\nProgramming')",
        expected_output="Python\nProgramming",
        hints=[
            "\\n creates a new line in strings",
            "Put it between the two words",
            "Use print('Python\\nProgramming')"
        ],
        order_index=5
    )
    
    print("  ✓ 5 exercises added")

print("\n✅ Beginner lesson populated successfully!")
print("📊 Summary: 1 lesson, 3 examples, 5 exercises")
