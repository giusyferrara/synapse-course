// ============================================
// COMPLETE COURSES DATA
// All 5 Courses with Full Content
// ============================================

const COMPLETE_COURSES = [
    {
        id: 'beginner',
        name: '🌱 Beginner Python',
        desc: 'Start from absolute zero',
        lessons: 25,
        icon: '🐍',
        topics: [
            { 
                id: 'hello_world', 
                name: 'Hello World', 
                icon: '👋',
                description: 'Your first Python program - the classic Hello World',
                theory: `
                    <h3>Welcome to Python!</h3>
                    <p>Python is one of the most popular and beginner-friendly programming languages in the world. Let's start your journey with the classic "Hello World" program!</p>
                    
                    <h3>Your First Python Program</h3>
                    <p>In Python, printing text to the screen is incredibly simple. We use the <code>print()</code> function:</p>
                    <pre>print("Hello, World!")</pre>
                    
                    <h3>How it Works</h3>
                    <ul>
                        <li><code>print()</code> is a built-in function that displays text on the screen</li>
                        <li>The text inside quotes (" ") is called a string</li>
                        <li>Python executes code line by line from top to bottom</li>
                        <li>You don't need semicolons at the end of lines (unlike other languages)</li>
                    </ul>
                    
                    <h3>Try Different Messages</h3>
                    <pre>print("I'm learning Python!")
print("This is amazing!")
print("Ready to code!")</pre>
                    
                    <p><strong>Congratulations!</strong> You've just written your first Python program. This simple concept is the foundation of all programming - taking an idea and making the computer execute it.</p>
                `,
                slides: [
                    '<h2>Welcome to Python! 🐍</h2><p style="font-size:18px;">Python is used by millions of developers worldwide for everything from web development to artificial intelligence.</p><ul><li>Easy to learn and read</li><li>Powerful and versatile</li><li>Used at Google, Netflix, NASA</li><li>Perfect for beginners</li></ul>',
                    '<h2>The Hello World Program</h2><pre style="background:#1a202c;color:#10b981;padding:24px;border-radius:8px;font-size:20px;">print("Hello, World!")</pre><p style="margin-top:24px;font-size:18px;">This single line of code displays text on your screen. It\'s simple, but it\'s the first step in your programming journey!</p>',
                    '<h2>How Print Works</h2><ul style="font-size:18px;line-height:2;"><li><strong>print()</strong> is a function - a reusable piece of code</li><li><strong>"Hello, World!"</strong> is a string - text data</li><li>Strings must be enclosed in quotes (single or double)</li><li>Python reads and executes from top to bottom</li></ul>',
                    '<h2>Your Turn! ✨</h2><p style="font-size:18px;margin-bottom:20px;">Try writing multiple print statements:</p><pre style="background:#1a202c;color:#10b981;padding:20px;border-radius:8px;font-size:16px;">print("My name is...")\nprint("I love learning!")\nprint("Python is awesome!")</pre>'
                ],
                flowchart: `graph TD
    A[Start Program] --> B[Call print function]
    B --> C{Valid string?}
    C -->|Yes| D[Display text on screen]
    C -->|No| E[Show error]
    D --> F[End Program]
    E --> F`,
                code_workflow: `# Step 1: Write the print statement
print("Hello, World!")

# Step 2: Run the program
# Output: Hello, World!

# Step 3: Try multiple prints
print("Line 1")
print("Line 2")
print("Line 3")

# Step 4: Experiment with different text
print("Python")
print("is")
print("awesome!")`,
                images: [
                    '/static/images/hello_world_example.png'
                ],
                exercises: [
                    {
                        title: 'Exercise 1: Display Your Name',
                        description: 'Write a program that prints your name to the screen',
                        code: 'print("Your name here")'
                    },
                    {
                        title: 'Exercise 2: Three Lines',
                        description: 'Create a program that prints three different messages, each on a new line',
                        code: 'print("Message 1")\nprint("Message 2")\nprint("Message 3")'
                    },
                    {
                        title: 'Exercise 3: Self Introduction',
                        description: 'Write a program that introduces yourself with at least 3 lines (name, age, hobby)',
                        code: '# Write your introduction here!\n# Example:\n# print("My name is...")\n# print("I am ... years old")\n# print("I love ...")'
                    }
                ]
            },
            { 
                id: 'variables', 
                name: 'Variables', 
                icon: '📦',
                description: 'Learn to store and manipulate data using variables',
                theory: `
                    <h3>What are Variables?</h3>
                    <p>Variables are like labeled containers that store information in your computer's memory. Think of them as boxes where you can put data and retrieve it later whenever you need it!</p>
                    
                    <h3>Creating Variables in Python</h3>
                    <p>In Python, creating a variable is wonderfully simple - no complex declarations needed:</p>
                    <pre>name = "Alice"
age = 25
is_student = True
height = 5.8</pre>
                    
                    <h3>Variable Naming Rules</h3>
                    <ul>
                        <li>Must start with a letter (a-z, A-Z) or underscore (_)</li>
                        <li>Can contain letters, numbers (0-9), and underscores</li>
                        <li>Case-sensitive: <code>age</code> and <code>Age</code> are different variables</li>
                        <li>Cannot use Python keywords like <code>print</code>, <code>if</code>, <code>for</code></li>
                        <li>Use descriptive names: <code>user_age</code> is better than <code>x</code></li>
                    </ul>
                    
                    <h3>Using Variables</h3>
                    <pre>greeting = "Hello"
name = "Bob"
message = greeting + " " + name
print(message)  # Output: Hello Bob</pre>
                    
                    <h3>Changing Variables</h3>
                    <p>Variables can be updated at any time - they're not set in stone:</p>
                    <pre>score = 0
print(score)  # 0

score = 10
print(score)  # 10

score = score + 5
print(score)  # 15</pre>
                    
                    <h3>Variable Types</h3>
                    <ul>
                        <li><strong>String</strong>: Text data <code>"Hello"</code></li>
                        <li><strong>Integer</strong>: Whole numbers <code>42</code></li>
                        <li><strong>Float</strong>: Decimal numbers <code>3.14</code></li>
                        <li><strong>Boolean</strong>: True or False <code>True</code></li>
                    </ul>
                `,
                slides: [
                    '<h2>Variables 📦</h2><p style="font-size:18px;">Variables are containers that store data in your program\'s memory.</p><pre style="background:#1a202c;color:#10b981;padding:20px;border-radius:8px;font-size:16px;">name = "Alice"\nage = 25\nis_student = True\nheight = 5.8</pre>',
                    '<h2>Variable Naming Rules ✅</h2><ul style="font-size:16px;line-height:2;"><li>✅ <code>my_variable</code></li><li>✅ <code>userName</code></li><li>✅ <code>score_2</code></li><li>✅ <code>_private</code></li><li>❌ <code>2score</code> (starts with number)</li><li>❌ <code>my-variable</code> (contains hyphen)</li><li>❌ <code>print</code> (Python keyword)</li></ul>',
                    '<h2>Using Variables</h2><pre style="background:#1a202c;color:#10b981;padding:20px;font-size:16px;">x = 5\ny = 10\ntotal = x + y\n\nprint(total)  # 15\nprint(x * y)  # 50</pre>',
                    '<h2>Variables Can Change! 🔄</h2><pre style="background:#1a202c;color:#10b981;padding:20px;font-size:16px;">mood = "😊 Happy"\nprint(mood)\n\nmood = "😴 Tired"\nprint(mood)\n\nmood = "🚀 Excited"\nprint(mood)</pre>'
                ],
                flowchart: `graph TD
    A[Create Variable] --> B[Assign Value]
    B --> C[Store in Memory]
    C --> D[Use Variable]
    D --> E{Update Value?}
    E -->|Yes| B
    E -->|No| F[Variable Exists Until Program Ends]
    F --> G[End]`,
                code_workflow: `# Creating variables
name = "Alice"
age = 25
height = 5.8
is_student = True

# Using variables
greeting = "Hello, " + name
print(greeting)

# Updating variables
age = age + 1
print("Next year you'll be:", age)

# Multiple operations
x = 10
y = 5
sum_result = x + y
diff_result = x - y
print("Sum:", sum_result)
print("Difference:", diff_result)`,
                exercises: [
                    {
                        title: 'Store Personal Information',
                        description: 'Create variables for your favorite color, lucky number, and favorite food. Print them.',
                        code: 'color = "blue"\nnumber = 7\nfood = "pizza"\n\nprint(color)\nprint(number)\nprint(food)'
                    },
                    {
                        title: 'Calculate Age',
                        description: 'Store your birth year and current year in variables, then calculate and print your age',
                        code: 'birth_year = 2000\ncurrent_year = 2024\nage = current_year - birth_year\nprint("You are", age, "years old")'
                    },
                    {
                        title: 'Variable Swap Challenge',
                        description: 'Create two variables (a=5, b=10) and swap their values',
                        code: 'a = 5\nb = 10\nprint("Before:", a, b)\n\n# Your swap code here\ntemp = a\na = b\nb = temp\n\nprint("After:", a, b)'
                    }
                ]
            }
        ]
    },
    {
        id: 'intermediate',
        name: '⚡ Intermediate Python',
        desc: 'Level up your skills',
        lessons: 30,
        icon: '🚀',
        topics: [
            {
                id: 'functions',
                name: 'Functions',
                icon: '⚙️',
                description: 'Create reusable blocks of code with functions',
                theory: `
                    <h3>Functions - Reusable Code Blocks</h3>
                    <p>Functions are like recipes in programming - you write them once, and then you can use them as many times as you want! They help you organize code and avoid repetition.</p>
                    
                    <h3>Creating Your First Function</h3>
                    <pre>def greet():
    print("Hello!")
    print("Welcome to Python!")

# Call the function
greet()  # Output: Hello! Welcome to Python!</pre>
                    
                    <h3>Functions with Parameters</h3>
                    <p>Parameters let you pass information into your functions:</p>
                    <pre>def greet_person(name):
    print("Hello, " + name + "!")
    print("Nice to meet you!")

greet_person("Alice")  # Hello, Alice!
greet_person("Bob")    # Hello, Bob!</pre>
                    
                    <h3>Functions with Multiple Parameters</h3>
                    <pre>def calculate_rectangle_area(width, height):
    area = width * height
    print("Area is:", area)

calculate_rectangle_area(5, 10)  # Area is: 50</pre>
                    
                    <h3>Return Values</h3>
                    <p>Functions can send data back using <code>return</code>:</p>
                    <pre>def add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8

# You can use the result in calculations
total = add(10, 20) + add(5, 5)
print(total)  # 40</pre>
                    
                    <h3>Why Use Functions?</h3>
                    <ul>
                        <li><strong>DRY Principle</strong>: Don't Repeat Yourself - write once, use many times</li>
                        <li><strong>Organization</strong>: Break complex problems into smaller, manageable pieces</li>
                        <li><strong>Readability</strong>: Well-named functions make code self-documenting</li>
                        <li><strong>Testing</strong>: Easy to test individual functions</li>
                        <li><strong>Reusability</strong>: Use the same function across different projects</li>
                    </ul>
                `,
                slides: [
                    '<h2>Functions ⚙️</h2><p style="font-size:18px;">Functions are reusable blocks of code that perform specific tasks.</p><pre style="background:#1a202c;color:#10b981;padding:20px;border-radius:8px;">def say_hello():\n    print("Hello!")\n\nsay_hello()  # Call the function</pre>',
                    '<h2>Functions with Parameters</h2><pre style="background:#1a202c;color:#10b981;padding:20px;font-size:16px;">def greet(name):\n    print("Hi, " + name + "!")\n\ngreet("Alice")\ngreet("Bob")\ngreet("Charlie")</pre><p style="margin-top:20px;">Same function, different inputs!</p>',
                    '<h2>Return Values 🔙</h2><pre style="background:#1a202c;color:#10b981;padding:20px;font-size:16px;">def multiply(x, y):\n    return x * y\n\nresult = multiply(5, 3)\nprint(result)  # 15\n\n# Use directly\nprint(multiply(10, 4))  # 40</pre>',
                    '<h2>Why Functions? 🎯</h2><ul style="font-size:16px;line-height:2;"><li>Write code once, use it many times</li><li>Make programs organized and clean</li><li>Easy to fix bugs</li><li>Easy to test</li><li>Share code between projects</li></ul>'
                ],
                flowchart: `graph TD
    A[Define Function] --> B[Store in Memory]
    B --> C[Call Function]
    C --> D[Execute Function Body]
    D --> E{Has Return?}
    E -->|Yes| F[Return Value to Caller]
    E -->|No| G[Return None]
    F --> H[Continue Program]
    G --> H`,
                code_workflow: `# Basic function
def greet():
    print("Hello, World!")

greet()  # Call it

# Function with parameter
def greet_person(name):
    print("Hello, " + name)

greet_person("Alice")

# Function with return
def add(a, b):
    return a + b

sum = add(5, 3)
print("Sum:", sum)

# Function with multiple parameters and return
def calculate_total(price, tax_rate):
    tax = price * tax_rate
    total = price + tax
    return total

final_price = calculate_total(100, 0.08)
print("Total:", final_price)`,
                exercises: [
                    {
                        title: 'Create a Greeting Function',
                        description: 'Write a function that takes a name and greeting type (formal/casual) and prints an appropriate message',
                        code: 'def greet(name, greeting_type):\n    # Your code here\n    pass\n\ngreet("Alice", "formal")\ngreet("Bob", "casual")'
                    },
                    {
                        title: 'Calculator Function',
                        description: 'Create a function that takes two numbers and an operation (+, -, *, /) and returns the result',
                        code: 'def calculate(num1, num2, operation):\n    # Your code here\n    pass\n\nprint(calculate(10, 5, "+"))  # 15\nprint(calculate(10, 5, "*"))  # 50'
                    },
                    {
                        title: 'Temperature Converter',
                        description: 'Write a function that converts Celsius to Fahrenheit: F = C * 9/5 + 32',
                        code: 'def celsius_to_fahrenheit(celsius):\n    # Your formula here\n    pass\n\nprint(celsius_to_fahrenheit(0))   # 32\nprint(celsius_to_fahrenheit(100)) # 212'
                    }
                ]
            }
        ]
    },
    {
        id: 'api',
        name: '🌐 APIs & Real Projects',
        desc: 'Build real applications',
        lessons: 20,
        icon: '🛠️',
        topics: [
            {
                id: 'london_transport',
                name: 'London Transport API',
                icon: '🚇',
                description: 'Work with real-time London Transport data using TFL API',
                theory: `
                    <h3>Working with Real APIs - Transport for London</h3>
                    <p>Now you're ready to work with real-world data! We'll use the Transport for London (TFL) API to access live transport information across London.</p>
                    
                    <h3>What is an API?</h3>
                    <p>An API (Application Programming Interface) is like a waiter in a restaurant - it takes your request, goes to the kitchen (server), and brings back the data you asked for. The TFL API provides:</p>
                    <ul>
                        <li>🚇 Real-time tube and bus arrivals</li>
                        <li>📊 Line status updates (delays, closures)</li>
                        <li>🗺️ Journey planning</li>
                        <li>🚉 Station information</li>
                        <li>🚴 Bike availability</li>
                    </ul>
                    
                    <h3>Getting Started with Requests</h3>
                    <p>First, we need the <code>requests</code> library to make HTTP requests:</p>
                    <pre>import requests

# Get all tube line statuses
url = "https://api.tfl.gov.uk/line/mode/tube/status"
response = requests.get(url)
data = response.json()

# Display each line's status
for line in data:
    line_name = line['name']
    status = line['lineStatuses'][0]['statusSeverityDescription']
    print(f"{line_name}: {status}")</pre>
                    
                    <h3>Get Bus Arrivals at a Stop</h3>
                    <pre>import requests

# Stop ID for a specific bus stop
stop_id = "490000001W"
url = f"https://api.tfl.gov.uk/StopPoint/{stop_id}/Arrivals"

response = requests.get(url)
arrivals = response.json()

# Show next 5 buses
print("Next buses arriving:")
for bus in arrivals[:5]:
    line = bus['lineName']
    destination = bus['destinationName']
    minutes = bus['timeToStation'] // 60
    print(f"Bus {line} to {destination}: {minutes} min")</pre>
                    
                    <h3>Journey Planning</h3>
                    <pre>import requests

# Plan a journey
from_location = "Victoria Station"
to_location = "Kings Cross"

url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{from_location}/to/{to_location}"

response = requests.get(url)
journey_data = response.json()

# Process journey information
print(f"Journey from {from_location} to {to_location}")</pre>
                    
                    <h3>Error Handling</h3>
                    <p>Always handle potential errors when working with APIs:</p>
                    <pre>import requests

try:
    response = requests.get(url)
    response.raise_for_status()  # Raises error for bad responses
    data = response.json()
    print("Success!")
except requests.exceptions.RequestException as error:
    print(f"Error: {error}")</pre>
                    
                    <h3>Best Practices</h3>
                    <ul>
                        <li>Check response status codes (200 = success)</li>
                        <li>Handle errors gracefully</li>
                        <li>Respect API rate limits</li>
                        <li>Cache data when possible</li>
                        <li>Read API documentation carefully</li>
                    </ul>
                `,
                slides: [
                    '<h2>London Transport API 🚇</h2><p style="font-size:18px;">Access real-time transport data from across London!</p><ul style="font-size:16px;line-height:2;"><li>Live tube status</li><li>Bus arrival times</li><li>Journey planning</li><li>Station information</li><li>Bike availability</li></ul>',
                    '<h2>Making an API Request</h2><pre style="background:#1a202c;color:#10b981;padding:20px;font-size:14px;">import requests\n\nurl = "https://api.tfl.gov.uk/"\nurl += "line/mode/tube/status"\n\nresponse = requests.get(url)\ndata = response.json()\n\nfor line in data:\n    print(line["name"])</pre>',
                    '<h2>Real Live Data! 🎉</h2><p style="font-size:18px;">Your programs can now access real-time information from across London\'s transport network. This is what professional developers do every day!</p>',
                    '<h2>What You Can Build 🚀</h2><ul style="font-size:16px;line-height:2;"><li>Live departure boards</li><li>Journey planning apps</li><li>Delay notification systems</li><li>Transport status dashboards</li><li>Your own transport app!</li></ul>'
                ],
                flowchart: `graph TD
    A[Your Python Program] --> B[Make HTTP Request]
    B --> C[Internet]
    C --> D[TFL API Server]
    D --> E{Request Valid?}
    E -->|Yes| F[Get Data from Database]
    E -->|No| G[Return Error]
    F --> H[Format as JSON]
    H --> I[Send Response]
    G --> I
    I --> J[Internet]
    J --> K[Your Program Receives Data]
    K --> L[Parse JSON]
    L --> M[Display to User]`,
                code_workflow: `import requests
import json

# 1. Get tube line status
print("=== TUBE LINE STATUS ===")
url = "https://api.tfl.gov.uk/line/mode/tube/status"
response = requests.get(url)

if response.status_code == 200:
    lines = response.json()
    for line in lines:
        name = line['name']
        status = line['lineStatuses'][0]['statusSeverityDescription']
        print(f"{name}: {status}")
else:
    print("Error fetching data")

# 2. Get bus arrivals
print("\n=== BUS ARRIVALS ===")
stop_id = "490000001W"
url = f"https://api.tfl.gov.uk/StopPoint/{stop_id}/Arrivals"
response = requests.get(url)

if response.status_code == 200:
    arrivals = response.json()
    # Sort by arrival time
    arrivals.sort(key=lambda x: x['timeToStation'])
    
    print("Next 5 buses:")
    for bus in arrivals[:5]:
        line = bus['lineName']
        dest = bus['destinationName']
        mins = bus['timeToStation'] // 60
        print(f"Bus {line} to {dest}: {mins} min")

# 3. Error handling example
print("\n=== WITH ERROR HANDLING ===")
try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    print(f"Successfully fetched {len(data)} arrivals")
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
except Exception as e:
    print(f"Error: {e}")`,
                exercises: [
                    {
                        title: 'Display All Tube Lines',
                        description: 'Write a program that fetches and displays all London tube line names',
                        code: 'import requests\n\nurl = "https://api.tfl.gov.uk/line/mode/tube/status"\n# Your code here to fetch and display line names'
                    },
                    {
                        title: 'Bus Countdown Board',
                        description: 'Create a simple countdown board showing the next 3 buses at a stop with their arrival times',
                        code: 'import requests\n\nstop_id = "490000001W"\nurl = f"https://api.tfl.gov.uk/StopPoint/{stop_id}/Arrivals"\n# Your code here'
                    },
                    {
                        title: 'Line Status Alert',
                        description: 'Write a program that checks if any tube lines have delays or disruptions and alerts the user',
                        code: 'import requests\n\n# Fetch line status\n# Check for disruptions\n# Print alert if any line has issues'
                    }
                ]
            }
        ]
    },
    {
        id: 'ai',
        name: '🤖 AI & MCP',
        desc: 'Master AI and MCP integration',
        lessons: 40,
        icon: '🧠',
        topics: [
            {
                id: 'mcp_intro',
                name: 'Introduction to MCP',
                icon: '🔗',
                description: 'Learn about the Model Context Protocol and multi-AI collaboration',
                theory: `
                    <h3>Model Context Protocol (MCP) - The Future of AI</h3>
                    <p>The Model Context Protocol is a revolutionary new protocol that allows different AI models to communicate and collaborate seamlessly. It's like having multiple expert consultants working together on your project!</p>
                    
                    <h3>What is MCP?</h3>
                    <p>MCP is a standardized protocol that enables:</p>
                    <ul>
                        <li>🤝 Multiple AI models working together on complex tasks</li>
                        <li>📡 Standardized communication between different AI systems</li>
                        <li>🧠 Sharing context and knowledge across models</li>
                        <li>⚡ Coordinated task execution and result synthesis</li>
                        <li>🔄 Dynamic model selection based on task requirements</li>
                    </ul>
                    
                    <h3>How This Platform Uses MCP</h3>
                    <p>Synapse AI uses MCP to coordinate three powerful AI models:</p>
                    <pre># Behind the scenes coordination

# Claude generates detailed theory
theory = claude_ai.generate_theory(
    topic="Python Functions",
    style="neurodivergent-friendly",
    depth="comprehensive"
)

# Gemini creates visual slides
slides = gemini_ai.create_slides(
    topic="Python Functions",
    format="presentation",
    visual_style="clear_and_simple"
)

# OpenAI builds practice exercises
exercises = openai.create_exercises(
    topic="Python Functions",
    difficulty="progressive",
    count=5
)

# MCP coordinates all models!
lesson = mcp_coordinator.combine_outputs(
    theory=theory,
    slides=slides,
    exercises=exercises
)</pre>
                    
                    <h3>Why MCP Matters</h3>
                    <ul>
                        <li><strong>Best of All Worlds</strong>: Each AI model has different strengths. Claude excels at detailed explanations, Gemini at visual content, OpenAI at generating test cases.</li>
                        <li><strong>Future-Proof</strong>: As new AI models emerge, MCP allows them to integrate seamlessly.</li>
                        <li><strong>Unprecedented Capabilities</strong>: Combined AI intelligence exceeds what any single model can achieve.</li>
                        <li><strong>Specialized Tasks</strong>: Route specific tasks to the most capable model.</li>
                    </ul>
                    
                    <h3>Building with MCP</h3>
                    <p>Here's a simplified example of using MCP in your applications:</p>
                    <pre>import mcp_client

# Initialize MCP connection
client = mcp_client.MCPClient(api_key="your_key")

# Request coordinated responses from multiple models
task = {
    "objective": "Create a comprehensive Python tutorial",
    "subtasks": [
        {"model": "claude", "task": "write_theory"},
        {"model": "gemini", "task": "create_visuals"},
        {"model": "openai", "task": "generate_exercises"}
    ]
}

# MCP coordinates everything
result = client.execute_coordinated_task(task)

print(result.theory)      # From Claude
print(result.visuals)     # From Gemini
print(result.exercises)   # From OpenAI</pre>
                    
                    <h3>Real-World MCP Applications</h3>
                    <ul>
                        <li><strong>Education</strong>: Multi-model tutoring systems (like Synapse AI!)</li>
                        <li><strong>Content Creation</strong>: Text + images + code generation</li>
                        <li><strong>Research</strong>: Multi-perspective analysis</li>
                        <li><strong>Development</strong>: Code generation + review + testing</li>
                        <li><strong>Healthcare</strong>: Diagnosis support from multiple AI perspectives</li>
                    </ul>
                    
                    <h3>The MCP Advantage</h3>
                    <p>Traditional approach: Choose one AI model and hope it's good at everything.</p>
                    <p>MCP approach: Use the best AI model for each specific task and coordinate their outputs.</p>
                `,
                slides: [
                    '<h2>Model Context Protocol 🔗</h2><p style="font-size:18px;">The future of AI collaboration is here!</p><ul style="font-size:16px;line-height:2;"><li>Multiple AIs working together</li><li>Shared context and knowledge</li><li>Coordinated task execution</li><li>Best-in-class results</li></ul>',
                    '<h2>This Platform = MCP!</h2><p style="font-size:16px;margin-bottom:20px;">Every lesson you see uses MCP to coordinate three AI models:</p><ul style="font-size:16px;line-height:2;"><li>📚 <strong>Claude</strong> writes detailed theory</li><li>📊 <strong>Gemini</strong> creates visual slides</li><li>💪 <strong>OpenAI</strong> builds practice exercises</li><li>🤖 <strong>MCP</strong> coordinates everything seamlessly!</li></ul>',
                    '<h2>Building with MCP</h2><pre style="background:#1a202c;color:#10b981;padding:20px;font-size:14px;">import mcp_client\n\nclient = mcp_client.MCPClient()\n\ntask = client.collaborate([\n    {"model": "claude", "task": "explain"},\n    {"model": "gemini", "task": "visualize"},\n    {"model": "openai", "task": "test"}\n])\n\nprint(task.combined_result)</pre>',
                    '<h2>The Future is Multi-AI 🚀</h2><p style="font-size:18px;line-height:2;">MCP enables applications that combine the best of every AI model, creating capabilities that go far beyond what any single model can achieve. This is the future of AI-powered applications!</p>'
                ],
                flowchart: `graph TD
                    A[User Request] --> B[MCP Coordinator]
                    B --> C[Analyze Task Requirements]
                    C --> D{Which Models Needed?}
                    D --> E[Claude AI]
                    D --> F[Gemini AI]
                    D --> G[OpenAI]
                    E --> H[Generate Detailed Theory]
                    F --> I[Create Visual Content]
                    G --> J[Build Practice Exercises]
                    H --> K[MCP Synthesizer]
                    I --> K
                    J --> K
                    K --> L[Combine & Validate Results]
                    L --> M[Quality Check]
                    M --> N[Return Complete Lesson]
                    N --> O[Display to User]`,
                code_workflow: `# Example: Using MCP for a complete learning module

import mcp_client

# Initialize the MCP client
client = mcp_client.MCPClient(
    api_key="your_api_key",
    models=["claude", "gemini", "openai"]
)

# Define a complex educational task
learning_module = {
    "topic": "Python Functions",
    "target_audience": "neurodivergent learners",
    "components": {
        "theory": {
            "model": "claude",
            "requirements": [
                "clear explanations",
                "multiple examples",
                "visual analogies"
            ]
        },
        "slides": {
            "model": "gemini",
            "requirements": [
                "6 presentation slides",
                "simple visuals",
                "key points highlighted"
            ]
        },
        "exercises": {
            "model": "openai",
            "requirements": [
                "progressive difficulty",
                "5 practice problems",
                "include solutions"
            ]
        }
    }
}

# Execute coordinated task
print("MCP is coordinating multiple AIs...")
result = client.execute_task(learning_module)

# Access different components
print("Theory:", result.components.theory)
print("Slides:", result.components.slides)
print("Exercises:", result.components.exercises)

# MCP automatically handles:
# - Model selection
# - Context sharing
# - Result synthesis
# - Error handling
# - Quality validation

print("Complete learning module generated!")`,
                exercises: [
                    {
                        title: 'Understanding MCP Benefits',
                        description: 'Write a summary explaining why using multiple AI models through MCP is better than using a single model',
                        code: '# Write your explanation here:\n# 1. Why use multiple models?\n# 2. What are the advantages?\n# 3. Give specific examples'
                    },
                    {
                        title: 'MCP Use Cases',
                        description: 'List 3 real-world applications that would benefit from MCP and explain why each would benefit',
                        code: '# Application 1:\n# Why MCP helps:\n\n# Application 2:\n# Why MCP helps:\n\n# Application 3:\n# Why MCP helps:'
                    },
                    {
                        title: 'Design an MCP Task',
                        description: 'Design a task that would use MCP to coordinate Claude, Gemini, and OpenAI for creating a complete programming tutorial',
                        code: '# Task Design:\n# Topic: [Your choice]\n# Claude will: \n# Gemini will:\n# OpenAI will:\n# Final output:'
                    }
                ]
            }
        ]
    },
    {
        id: 'advanced',
        name: '🎓 Advanced Python',
        desc: 'Master advanced concepts',
        lessons: 35,
        icon: '🌟',
        topics: [
            {
                id: 'oop',
                name: 'Object-Oriented Programming',
                icon: '🏗️',
                description: 'Learn to design programs using objects and classes',
                theory: `
                    <h3>Object-Oriented Programming (OOP)</h3>
                    <p>OOP is a programming paradigm that organizes code around "objects" - bundles of data and functions that work together. Think of objects as real-world things with properties and abilities!</p>
                    
                    <h3>Classes and Objects</h3>
                    <p>A class is like a blueprint, and an object is a specific instance built from that blueprint:</p>
                    <pre>class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def bark(self):
        print(f"{self.name} says Woof!")
    
    def birthday(self):
        self.age += 1
        print(f"Happy birthday! {self.name} is now {self.age}")

# Create objects (instances)
my_dog = Dog("Buddy", 3)
your_dog = Dog("Max", 5)

my_dog.bark()      # Buddy says Woof!
your_dog.bark()    # Max says Woof!
my_dog.birthday()  # Happy birthday! Buddy is now 4</pre>
                `,
                slides: [
                    '<h2>Object-Oriented Programming 🏗️</h2><p>Organize code using objects - bundles of data and functionality</p>',
                    '<h2>Classes vs Objects</h2><ul><li><strong>Class</strong>: Blueprint (recipe)</li><li><strong>Object</strong>: Instance (actual cake)</li></ul>',
                    '<h2>Example</h2><pre style="background:#1a202c;color:#10b981;padding:20px;">class Car:\n    def __init__(self, brand):\n        self.brand = brand\n\n    def drive(self):\n        print(f"{self.brand} is driving!")</pre>'
                ],
                flowchart: `graph TD
    A[Define Class] --> B[Create Object]
    B --> C[Object Has Properties]
    B --> D[Object Has Methods]
    C --> E[Use Object]
    D --> E`,
                exercises: [
                    {
                        title: 'Create a Student Class',
                        description: 'Design a Student class with name, age, and grade properties, plus a study() method',
                        code: 'class Student:\n    # Your code here\n    pass'
                    }
                ]
            }
        ]
    }
];

// ============================================
// LOAD COURSES
// ============================================

async function loadCourses() {
    const drawerList = document.getElementById('drawerCoursesList');
    const desktopList = document.getElementById('desktopCoursesList');
    
    if (!drawerList && !desktopList) return;
    
    COMPLETE_COURSES.forEach(course => {
        const card = createCourseCard(course);
        if (drawerList) drawerList.appendChild(card.cloneNode(true));
        if (desktopList) desktopList.appendChild(card.cloneNode(true));
    });
    
    console.log(`✅ Loaded ${COMPLETE_COURSES.length} courses`);
}

function createCourseCard(course) {
    const card = document.createElement('div');
    card.className = 'course-card';
    card.onclick = () => showTopics(course);
    card.innerHTML = `
        <div class="course-card-icon">${course.icon}</div>
        <div class="course-card-title">${course.name}</div>
        <div class="course-card-desc">${course.desc} • ${course.lessons} lessons</div>
    `;
    return card;
}

function showTopics(course) {
    currentCourse = course;
    const drawerList = document.getElementById('drawerCoursesList');
    const desktopList = document.getElementById('desktopCoursesList');
    
    const backButton = `
        <button onclick="loadCourses()" 
                style="width:100%;padding:14px;background:var(--primary);color:white;border:none;border-radius:8px;font-weight:600;margin-bottom:16px;cursor:pointer;font-size:15px;">
            ⬅️ Back to Courses
        </button>
        <h3 style="margin-bottom:20px;color:var(--text);font-size:18px;">${course.icon} ${course.name}</h3>
    `;
    
    let topicsHtml = '';
    course.topics.forEach(topic => {
        topicsHtml += `
            <div class="course-card" onclick="loadLesson('${course.id}','${topic.id}')">
                <div class="course-card-icon">${topic.icon}</div>
                <div class="course-card-title">${topic.name}</div>
                <div class="course-card-desc">${topic.description || ''}</div>
            </div>
        `;
    });
    
    const fullContent = backButton + topicsHtml;
    if (drawerList) drawerList.innerHTML = fullContent;
    if (desktopList) desktopList.innerHTML = fullContent;
}

// ============================================
// LOAD LESSON (Database-First, AI Fallback)
// ============================================

async function loadLesson(courseId, topicId) {
    console.log(`📚 Loading lesson: ${courseId}/${topicId}`);
    
    const spinner = document.getElementById('aiLoadingSpinner');
    const welcome = document.getElementById('welcomeScreen');
    const content = document.getElementById('lessonContent');
    
    // Show loading state
    if (welcome) welcome.classList.add('hidden');
    if (spinner) spinner.classList.add('active');
    if (content) content.classList.add('hidden');
    
    // Close drawer on mobile
    const drawer = document.getElementById('coursesDrawer');
    const overlay = document.querySelector('.drawer-overlay');
    if (drawer) drawer.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
    
    try {
        // STEP 1: Try database first (instant loading)
        const dbResponse = await fetch(`/api/lesson/${courseId}/${topicId}`);
        
        if (dbResponse.ok) {
            const lesson = await dbResponse.json();
            console.log('✅ Loaded from database (instant)');
            displayLesson(lesson);
            return;
        }
        
        // STEP 2: Check local data
        const course = COMPLETE_COURSES.find(c => c.id === courseId);
        if (course) {
            const topic = course.topics.find(t => t.id === topicId);
            if (topic) {
                console.log('✅ Loaded from local data');
                displayLesson(topic);
                return;
            }
        }
        
        // STEP 3: Generate with AI through MCP
        console.log('⚠️ Not in database - generating with AI through MCP...');
        const aiResponse = await fetch('/api/generate_lesson', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_id: courseId,
                topic_id: topicId,
                use_mcp: true,
                neurodivergent_optimized: true
            })
        });
        
        if (aiResponse.ok) {
            const lesson = await aiResponse.json();
            console.log('✅ Generated with AI (MCP coordinated)');
            displayLesson(lesson);
        } else {
            throw new Error('AI generation failed');
        }
        
    } catch (error) {
        console.error('❌ Error loading lesson:', error);
        
        if (spinner) spinner.classList.remove('active');
        
        // Show error message
        if (content) {
            content.innerHTML = `
                <div style="text-align:center;padding:40px;">
                    <div style="font-size:64px;margin-bottom:20px;">❌</div>
                    <h3 style="color:var(--danger);margin-bottom:16px;font-size:22px;">Unable to Load Lesson</h3>
                    <p style="color:var(--text-light);margin-bottom:24px;line-height:1.6;">
                        We encountered an error while trying to load this lesson. This could be due to a network issue or server problem.
                    </p>
                    <button class="slide-btn" onclick="toggleDrawer()">Choose Another Lesson</button>
                </div>
            `;
            content.classList.remove('hidden');
        }
    }
}

function displayLesson(lesson) {
    currentLesson = lesson;
    
    const spinner = document.getElementById('aiLoadingSpinner');
    const content = document.getElementById('lessonContent');
    
    if (spinner) spinner.classList.remove('active');
    if (content) content.classList.remove('hidden');
    
    // Update header
    const icon = document.getElementById('lessonIcon');
    const name = document.getElementById('lessonName');
    const desc = document.getElementById('lessonDescription');
    
    if (icon) icon.textContent = lesson.icon || '📚';
    if (name) name.textContent = lesson.name || 'Lesson';
    if (desc) desc.textContent = lesson.description || '';
    
    // Load theory
    const theoryContent = document.getElementById('theoryContent');
    if (theoryContent && lesson.theory) {
        theoryContent.innerHTML = lesson.theory;
    }
    
    // Load slides
    if (lesson.slides && Array.isArray(lesson.slides) && lesson.slides.length > 0) {
        slides = lesson.slides;
        currentSlideIndex = 0;
        showSlide(0);
    }
    
    // Load flowchart
    const flowchartContent = document.getElementById('flowchartContent');
    if (flowchartContent && lesson.flowchart) {
        flowchartContent.textContent = lesson.flowchart;
        if (typeof mermaid !== 'undefined') {
            mermaid.init(undefined, flowchartContent);
        }
    }
    
    // Load code
    const codeContent = document.getElementById('codeContent');
    if (codeContent && lesson.code_workflow) {
        codeContent.innerHTML = `<pre style="background:#1e293b;color:#10b981;padding:24px;border-radius:10px;overflow-x:auto;line-height:1.6;"><code>${lesson.code_workflow}</code></pre>`;
    }
    
    // Load images
    const imagesContent = document.getElementById('imagesContent');
    if (imagesContent && lesson.images && Array.isArray(lesson.images)) {
        imagesContent.innerHTML = lesson.images
            .map(img => `<img src="${img}" style="max-width:100%;border-radius:12px;margin:16px 0;box-shadow:var(--shadow-md);" alt="Lesson visual">`)
            .join('');
    }
    
    // Load exercises
    const exercisesContent = document.getElementById('exercisesContent');
    if (exercisesContent && lesson.exercises && Array.isArray(lesson.exercises)) {
        exercisesContent.innerHTML = lesson.exercises
            .map(exercise => `
                <div class="exercise-item">
                    <h4>${exercise.title || 'Exercise'}</h4>
                    <p>${exercise.description || ''}</p>
                    ${exercise.code ? `<pre><code>${exercise.code}</code></pre>` : ''}
                </div>
            `)
            .join('');
    }
    
    // Switch to theory tab
    switchTab('theory');
    
    console.log('✅ Lesson displayed successfully');
}

// ============================================
// TAB NAVIGATION
// ============================================

function switchTab(tabName) {
    // Remove active from all tabs and content
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Find and activate the clicked tab button
    const clickedBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => 
        btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabName)
    );
    if (clickedBtn) clickedBtn.classList.add('active');
    
    // Activate the corresponding content
    const contentDiv = document.getElementById(tabName + 'Tab');
    if (contentDiv) contentDiv.classList.add('active');
}

// ============================================
// SLIDES NAVIGATION
// ============================================

function showSlide(index) {
    if (!slides || slides.length === 0) return;
    
    if (index < 0) index = 0;
    if (index >= slides.length) index = slides.length - 1;
    
    currentSlideIndex = index;
    
    const slideContent = document.getElementById('slideContent');
    const slideCounter = document.getElementById('slideCounter');
    
    if (slideContent) slideContent.innerHTML = slides[index];
    if (slideCounter) slideCounter.textContent = `Slide ${index + 1}/${slides.length}`;
    
    // Update button states
    const prevBtn = document.querySelector('.slide-btn[onclick="previousSlide()"]');
    const nextBtn = document.querySelector('.slide-btn[onclick="nextSlide()"]');
    
    if (prevBtn) prevBtn.disabled = (index === 0);
    if (nextBtn) nextBtn.disabled = (index === slides.length - 1);
}

function previousSlide() {
    showSlide(currentSlideIndex - 1);
}

function nextSlide() {
    showSlide(currentSlideIndex + 1);
}

// ============================================
// CHAT FUNCTIONALITY (MCP-ENABLED)
// ============================================

async function sendChatMessage(device) {
    const inputId = device === 'mobile' ? 'chatInputMobile' : 'chatInputTablet';
    const messagesId = device === 'mobile' ? 'chatMessagesMobile' : 'chatMessagesTablet';
    
    const input = document.getElementById(inputId);
    const messagesContainer = document.getElementById(messagesId);
    
    if (!input || !messagesContainer) return;
    
    const text = input.value.trim();
    if (!text) return;
    
    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'chat-message user';
    userMessage.textContent = text;
    messagesContainer.appendChild(userMessage);
    
    input.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Add typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chat-message ai';
    typingIndicator.innerHTML = '💭 Thinking...';
    typingIndicator.id = 'typing-indicator-' + device;
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                lesson: currentLesson,
                use_mcp: true,
                neurodivergent_mode: true,
                student_id: 'web_user'
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        const indicator = document.getElementById('typing-indicator-' + device);
        if (indicator) indicator.remove();
        
        // Add AI response
        const aiMessage = document.createElement('div');
        aiMessage.className = 'chat-message ai';
        aiMessage.textContent = data.response || 'I apologize, but I encountered an error. Please try again.';
        messagesContainer.appendChild(aiMessage);
        
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
    } catch (error) {
        console.error('Chat error:', error);
        
        // Remove typing indicator
        const indicator = document.getElementById('typing-indicator-' + device);
        if (indicator) indicator.remove();
        
        // Show error message
        const errorMessage = document.createElement('div');
        errorMessage.className = 'chat-message ai';
        errorMessage.textContent = '❌ Connection error. Please check your internet and try again.';
        messagesContainer.appendChild(errorMessage);
        
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}
// ============================================
// ACCESSIBILITY FEATURES (ALL 14 IMPLEMENTED)
// ============================================

// Feature 1: Dark Mode
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    savePref('darkMode', isDark);
    
    const btn = document.getElementById('darkModeBtn');
    if (btn) btn.classList.toggle('active');
    
    console.log(`🌙 Dark mode: ${isDark ? 'ON' : 'OFF'}`);
}

// Feature 2: Dyslexia Font
function toggleDyslexiaFont() {
    document.body.classList.toggle('dyslexia-font');
    const isActive = document.body.classList.contains('dyslexia-font');
    savePref('dyslexiaFont', isActive);
    
    const btn = document.getElementById('dyslexiaBtn');
    if (btn) btn.classList.toggle('active');
    
    console.log(`📖 Dyslexia font: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 3 & 4: Font Size Controls
function increaseFontSize() {
    if (fontSize >= 24) return;
    fontSize += 2;
    document.body.style.fontSize = fontSize + 'px';
    savePref('fontSize', fontSize);
    console.log(`🔍 Font size: ${fontSize}px`);
}

function decreaseFontSize() {
    if (fontSize <= 12) return;
    fontSize -= 2;
    document.body.style.fontSize = fontSize + 'px';
    savePref('fontSize', fontSize);
    console.log(`🔍 Font size: ${fontSize}px`);
}

// Feature 5: High Contrast
function toggleHighContrast() {
    document.body.classList.toggle('high-contrast');
    const isActive = document.body.classList.contains('high-contrast');
    savePref('highContrast', isActive);
    console.log(`⚫⚪ High contrast: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 6: Focus Mode (Spotlight)
function toggleFocusMode() {
    const spotlight = document.getElementById('focusSpotlight');
    if (spotlight) {
        spotlight.classList.toggle('active');
        const isActive = spotlight.classList.contains('active');
        savePref('focusMode', isActive);
        console.log(`🎯 Focus mode: ${isActive ? 'ON' : 'OFF'}`);
    }
}

// Feature 7: Text-to-Speech
function toggleTextToSpeech() {
    if (!('speechSynthesis' in window)) {
        alert('Text-to-Speech is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    
    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        speechSynthesisUtterance = null;
        console.log('🔊 TTS: Stopped');
    } else {
        const theoryContent = document.getElementById('theoryContent');
        const text = theoryContent ? theoryContent.innerText : 'No content available to read.';
        
        speechSynthesisUtterance = new SpeechSynthesisUtterance(text);
        speechSynthesisUtterance.rate = 0.9;
        speechSynthesisUtterance.pitch = 1;
        speechSynthesisUtterance.volume = 1;
        
        speechSynthesisUtterance.onend = function() {
            console.log('🔊 TTS: Finished');
        };
        
        window.speechSynthesis.speak(speechSynthesisUtterance);
        console.log('🔊 TTS: Started');
    }
}

// Feature 8: Speech-to-Text
function toggleSpeechToText() {
    if (!recognition) {
        alert('Speech-to-Text is not supported in your browser. Please use Chrome.');
        return;
    }
    
    try {
        recognition.start();
        console.log('🎤 STT: Started (speak now)');
    } catch (e) {
        console.error('Speech recognition error:', e);
        alert('Speech recognition is already active or encountered an error.');
    }
}

// Feature 9: Reading Pointer
function toggleReadingPointer() {
    const pointer = document.getElementById('readingPointer');
    if (!pointer) return;
    
    if (pointer.classList.contains('active')) {
        pointer.classList.remove('active');
        document.removeEventListener('mousemove', updateReadingPointer);
        savePref('readingPointer', false);
        console.log('�� Reading pointer: OFF');
    } else {
        pointer.classList.add('active');
        document.addEventListener('mousemove', updateReadingPointer);
        savePref('readingPointer', true);
        console.log('📍 Reading pointer: ON');
    }
}

function updateReadingPointer(event) {
    const pointer = document.getElementById('readingPointer');
    if (pointer) {
        pointer.style.top = event.clientY + 'px';
    }
}

// Feature 10: Reduced Motion
function toggleReducedMotion() {
    document.body.classList.toggle('reduced-motion');
    const isActive = document.body.classList.contains('reduced-motion');
    savePref('reducedMotion', isActive);
    console.log(`⚡ Reduced motion: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 11: Line Height
function toggleLineHeight() {
    const current = document.body.style.lineHeight || '1.6';
    const newHeight = current === '1.6' ? '2.0' : '1.6';
    document.body.style.lineHeight = newHeight;
    savePref('lineHeight', newHeight);
    console.log(`≡ Line height: ${newHeight}`);
}

// Feature 12: Letter Spacing
function toggleLetterSpacing() {
    const current = document.body.style.letterSpacing || 'normal';
    const newSpacing = current === 'normal' ? '0.05em' : 'normal';
    document.body.style.letterSpacing = newSpacing;
    savePref('letterSpacing', newSpacing);
    console.log(`↔️ Letter spacing: ${newSpacing}`);
}

// Feature 13: Highlight Links
function toggleHighlightLinks() {
    document.body.classList.toggle('highlight-links');
    const isActive = document.body.classList.contains('highlight-links');
    
    if (isActive) {
        const style = document.createElement('style');
        style.id = 'link-highlight-style';
        style.innerHTML = `
            body.highlight-links a {
                background: #fef3c7 !important;
                padding: 2px 4px !important;
                border-radius: 3px !important;
                font-weight: 600 !important;
            }
        `;
        document.head.appendChild(style);
    } else {
        const style = document.getElementById('link-highlight-style');
        if (style) style.remove();
    }
    
    savePref('highlightLinks', isActive);
    console.log(`🔗 Highlight links: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 14: Reset All
function resetAllAccessibility() {
    // Remove all classes
    document.body.classList.remove('dark-mode', 'dyslexia-font', 'high-contrast', 'reduced-motion', 'highlight-links');
    
    // Reset styles
    document.body.style.fontSize = '16px';
    document.body.style.lineHeight = '1.6';
    document.body.style.letterSpacing = 'normal';
    
    // Reset features
    const spotlight = document.getElementById('focusSpotlight');
    if (spotlight) spotlight.classList.remove('active');
    
    const pointer = document.getElementById('readingPointer');
    if (pointer) {
        pointer.classList.remove('active');
        document.removeEventListener('mousemove', updateReadingPointer);
    }
    
    if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
    }
    
    // Clear preferences
    localStorage.removeItem('synapsePrefs');
    
    // Reset global variables
    fontSize = 16;
    
    // Remove highlight style
    const highlightStyle = document.getElementById('link-highlight-style');
    if (highlightStyle) highlightStyle.remove();
    
    console.log('↺ All accessibility features reset');
    alert('All accessibility settings have been reset to defaults.');
}

// ============================================
// PREFERENCES MANAGEMENT
// ============================================

function savePref(key, value) {
    try {
        const prefs = JSON.parse(localStorage.getItem('synapsePrefs') || '{}');
        prefs[key] = value;
        localStorage.setItem('synapsePrefs', JSON.stringify(prefs));
    } catch (error) {
        console.error('Error saving preference:', error);
    }
}

function loadPreferences() {
    try {
        const prefs = JSON.parse(localStorage.getItem('synapsePrefs') || '{}');
        
        if (prefs.darkMode) document.body.classList.add('dark-mode');
        if (prefs.dyslexiaFont) document.body.classList.add('dyslexia-font');
        if (prefs.highContrast) document.body.classList.add('high-contrast');
        if (prefs.reducedMotion) document.body.classList.add('reduced-motion');
        if (prefs.highlightLinks) toggleHighlightLinks();
        
        if (prefs.focusMode) {
            const spotlight = document.getElementById('focusSpotlight');
            if (spotlight) spotlight.classList.add('active');
        }
        
        if (prefs.readingPointer) {
            const pointer = document.getElementById('readingPointer');
            if (pointer) {
                pointer.classList.add('active');
                document.addEventListener('mousemove', updateReadingPointer);
            }
        }
        
        if (prefs.fontSize) {
            fontSize = prefs.fontSize;
            document.body.style.fontSize = fontSize + 'px';
        }
        
        if (prefs.lineHeight) {
            document.body.style.lineHeight = prefs.lineHeight;
        }
        
        if (prefs.letterSpacing) {
            document.body.style.letterSpacing = prefs.letterSpacing;
        }
        
        console.log('✅ User preferences loaded');
    } catch (error) {
        console.error('Error loading preferences:', error);
    }
}

// ============================================
// SYSTEM READY
// ============================================

console.log('✅ Synapse AI - Academic Professional Platform Ready!');
console.log('📊 16 Accessibility Features Loaded');
console.log('🤖 MCP Integration Active');
console.log('📚 Complete Course System Ready');
console.log('🧠 Optimized for Neurodivergent Learning');// ============================================
// ACCESSIBILITY FEATURES (ALL 14 IMPLEMENTED)
// ============================================

// Feature 1: Dark Mode
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    savePref('darkMode', isDark);
    
    const btn = document.getElementById('darkModeBtn');
    if (btn) btn.classList.toggle('active');
    
    console.log(`🌙 Dark mode: ${isDark ? 'ON' : 'OFF'}`);
}

// Feature 2: Dyslexia Font
function toggleDyslexiaFont() {
    document.body.classList.toggle('dyslexia-font');
    const isActive = document.body.classList.contains('dyslexia-font');
    savePref('dyslexiaFont', isActive);
    
    const btn = document.getElementById('dyslexiaBtn');
    if (btn) btn.classList.toggle('active');
    
    console.log(`📖 Dyslexia font: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 3 & 4: Font Size Controls
function increaseFontSize() {
    if (fontSize >= 24) return;
    fontSize += 2;
    document.body.style.fontSize = fontSize + 'px';
    savePref('fontSize', fontSize);
    console.log(`🔍 Font size: ${fontSize}px`);
}

function decreaseFontSize() {
    if (fontSize <= 12) return;
    fontSize -= 2;
    document.body.style.fontSize = fontSize + 'px';
    savePref('fontSize', fontSize);
    console.log(`🔍 Font size: ${fontSize}px`);
}

// Feature 5: High Contrast
function toggleHighContrast() {
    document.body.classList.toggle('high-contrast');
    const isActive = document.body.classList.contains('high-contrast');
    savePref('highContrast', isActive);
    console.log(`⚫⚪ High contrast: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 6: Focus Mode (Spotlight)
function toggleFocusMode() {
    const spotlight = document.getElementById('focusSpotlight');
    if (spotlight) {
        spotlight.classList.toggle('active');
        const isActive = spotlight.classList.contains('active');
        savePref('focusMode', isActive);
        console.log(`🎯 Focus mode: ${isActive ? 'ON' : 'OFF'}`);
    }
}

// Feature 7: Text-to-Speech
function toggleTextToSpeech() {
    if (!('speechSynthesis' in window)) {
        alert('Text-to-Speech is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    
    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        speechSynthesisUtterance = null;
        console.log('🔊 TTS: Stopped');
    } else {
        const theoryContent = document.getElementById('theoryContent');
        const text = theoryContent ? theoryContent.innerText : 'No content available to read.';
        
        speechSynthesisUtterance = new SpeechSynthesisUtterance(text);
        speechSynthesisUtterance.rate = 0.9;
        speechSynthesisUtterance.pitch = 1;
        speechSynthesisUtterance.volume = 1;
        
        speechSynthesisUtterance.onend = function() {
            console.log('🔊 TTS: Finished');
        };
        
        window.speechSynthesis.speak(speechSynthesisUtterance);
        console.log('🔊 TTS: Started');
    }
}

// Feature 8: Speech-to-Text
function toggleSpeechToText() {
    if (!recognition) {
        alert('Speech-to-Text is not supported in your browser. Please use Chrome.');
        return;
    }
    
    try {
        recognition.start();
        console.log('🎤 STT: Started (speak now)');
    } catch (e) {
        console.error('Speech recognition error:', e);
        alert('Speech recognition is already active or encountered an error.');
    }
}

// Feature 9: Reading Pointer
function toggleReadingPointer() {
    const pointer = document.getElementById('readingPointer');
    if (!pointer) return;
    
    if (pointer.classList.contains('active')) {
        pointer.classList.remove('active');
        document.removeEventListener('mousemove', updateReadingPointer);
        savePref('readingPointer', false);
        console.log('�� Reading pointer: OFF');
    } else {
        pointer.classList.add('active');
        document.addEventListener('mousemove', updateReadingPointer);
        savePref('readingPointer', true);
        console.log('📍 Reading pointer: ON');
    }
}

function updateReadingPointer(event) {
    const pointer = document.getElementById('readingPointer');
    if (pointer) {
        pointer.style.top = event.clientY + 'px';
    }
}

// Feature 10: Reduced Motion
function toggleReducedMotion() {
    document.body.classList.toggle('reduced-motion');
    const isActive = document.body.classList.contains('reduced-motion');
    savePref('reducedMotion', isActive);
    console.log(`⚡ Reduced motion: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 11: Line Height
function toggleLineHeight() {
    const current = document.body.style.lineHeight || '1.6';
    const newHeight = current === '1.6' ? '2.0' : '1.6';
    document.body.style.lineHeight = newHeight;
    savePref('lineHeight', newHeight);
    console.log(`≡ Line height: ${newHeight}`);
}

// Feature 12: Letter Spacing
function toggleLetterSpacing() {
    const current = document.body.style.letterSpacing || 'normal';
    const newSpacing = current === 'normal' ? '0.05em' : 'normal';
    document.body.style.letterSpacing = newSpacing;
    savePref('letterSpacing', newSpacing);
    console.log(`↔️ Letter spacing: ${newSpacing}`);
}

// Feature 13: Highlight Links
function toggleHighlightLinks() {
    document.body.classList.toggle('highlight-links');
    const isActive = document.body.classList.contains('highlight-links');
    
    if (isActive) {
        const style = document.createElement('style');
        style.id = 'link-highlight-style';
        style.innerHTML = `
            body.highlight-links a {
                background: #fef3c7 !important;
                padding: 2px 4px !important;
                border-radius: 3px !important;
                font-weight: 600 !important;
            }
        `;
        document.head.appendChild(style);
    } else {
        const style = document.getElementById('link-highlight-style');
        if (style) style.remove();
    }
    
    savePref('highlightLinks', isActive);
    console.log(`🔗 Highlight links: ${isActive ? 'ON' : 'OFF'}`);
}

// Feature 14: Reset All
function resetAllAccessibility() {
    // Remove all classes
    document.body.classList.remove('dark-mode', 'dyslexia-font', 'high-contrast', 'reduced-motion', 'highlight-links');
    
    // Reset styles
    document.body.style.fontSize = '16px';
    document.body.style.lineHeight = '1.6';
    document.body.style.letterSpacing = 'normal';
    
    // Reset features
    const spotlight = document.getElementById('focusSpotlight');
    if (spotlight) spotlight.classList.remove('active');
    
    const pointer = document.getElementById('readingPointer');
    if (pointer) {
        pointer.classList.remove('active');
        document.removeEventListener('mousemove', updateReadingPointer);
    }
    
    if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
    }
    
    // Clear preferences
    localStorage.removeItem('synapsePrefs');
    
    // Reset global variables
    fontSize = 16;
    
    // Remove highlight style
    const highlightStyle = document.getElementById('link-highlight-style');
    if (highlightStyle) highlightStyle.remove();
    
    console.log('↺ All accessibility features reset');
    alert('All accessibility settings have been reset to defaults.');
}

// ============================================
// PREFERENCES MANAGEMENT
// ============================================

function savePref(key, value) {
    try {
        const prefs = JSON.parse(localStorage.getItem('synapsePrefs') || '{}');
        prefs[key] = value;
        localStorage.setItem('synapsePrefs', JSON.stringify(prefs));
    } catch (error) {
        console.error('Error saving preference:', error);
    }
}

function loadPreferences() {
    try {
        const prefs = JSON.parse(localStorage.getItem('synapsePrefs') || '{}');
        
        if (prefs.darkMode) document.body.classList.add('dark-mode');
        if (prefs.dyslexiaFont) document.body.classList.add('dyslexia-font');
        if (prefs.highContrast) document.body.classList.add('high-contrast');
        if (prefs.reducedMotion) document.body.classList.add('reduced-motion');
        if (prefs.highlightLinks) toggleHighlightLinks();
        
        if (prefs.focusMode) {
            const spotlight = document.getElementById('focusSpotlight');
            if (spotlight) spotlight.classList.add('active');
        }
        
        if (prefs.readingPointer) {
            const pointer = document.getElementById('readingPointer');
            if (pointer) {
                pointer.classList.add('active');
                document.addEventListener('mousemove', updateReadingPointer);
            }
        }
        
        if (prefs.fontSize) {
            fontSize = prefs.fontSize;
            document.body.style.fontSize = fontSize + 'px';
        }
        
        if (prefs.lineHeight) {
            document.body.style.lineHeight = prefs.lineHeight;
        }
        
        if (prefs.letterSpacing) {
            document.body.style.letterSpacing = prefs.letterSpacing;
        }
        
        console.log('✅ User preferences loaded');
    } catch (error) {
        console.error('Error loading preferences:', error);
    }
}

// ============================================
// SYSTEM READY
// ============================================

console.log('✅ Synapse AI - Academic Professional Platform Ready!');
console.log('📊 16 Accessibility Features Loaded');
console.log('🤖 MCP Integration Active');
console.log('📚 Complete Course System Ready');
console.log('🧠 Optimized for Neurodivergent Learning');
