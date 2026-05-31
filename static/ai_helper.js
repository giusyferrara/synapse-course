/**
 * AI TUTOR HELPER - Uses knowledge base to generate intelligent responses
 * 
 * This file bridges the AI_KNOWLEDGE_BASE with actual user messages
 * to create context-aware, helpful responses.
 */

// Load the knowledge base
// In your HTML, make sure to include: <script src="/static/ai_knowledge_base.js"></script>

function getIntelligentResponse(userMessage, context = {}) {
  const msg = userMessage.toLowerCase().trim();
  const KB = typeof AI_KNOWLEDGE_BASE !== 'undefined' ? AI_KNOWLEDGE_BASE : {};
  
  // Get current context
  const currentTab = context.currentTab || document.querySelector('.tab-btn.active')?.textContent.toLowerCase() || '';
  const hasCode = context.hasCode || (document.getElementById('codeEditor')?.value.trim().length > 0);
  const hasOutput = context.hasOutput || (document.getElementById('outputConsole')?.textContent.trim().length > 20);
  const currentCourse = context.currentCourse || window.currentCourse || '';
  
  // ==========================================
  // SPECIFIC PLATFORM NAVIGATION QUESTIONS
  // ==========================================
  
  // Where is X?
  if (msg.includes('where is') || msg.includes('where do i') || msg.includes('how do i find')) {
    
    if (msg.includes('code editor') || msg.includes('where do i write')) {
      return "The code editor is in the **💻 Practice** tab! Click that tab at the top, and you'll see a big text box - that's where you type your Python code. Want to try writing something?";
    }
    
    if (msg.includes('run') && msg.includes('code')) {
      return "To run your code: Go to **💻 Practice** tab, write code in the big editor, then click the **Run Code** button below it. The output shows up in the black box underneath!";
    }
    
    if (msg.includes('example')) {
      return "Examples are in the **📊 Slides** tab at the top! Each example has buttons: **💻 Try This Example** loads it so you can play with it, or **▶️ Run & See Output** just shows what it does. Go check them out!";
    }
    
    if (msg.includes('exercise') || msg.includes('practice')) {
      return "Practice exercises are in the **💻 Practice** tab! Click that tab, scroll down past the code editor, and you'll see exercises to try. Each one has a **Start Exercise** button!";
    }
    
    if (msg.includes('output') || msg.includes('result')) {
      return "The output appears in the **Output Console** - that's the black box below the code editor in the **💻 Practice** tab. When you run code, results (or errors) show up there!";
    }
    
    if (msg.includes('dark mode') || msg.includes('theme')) {
      return "Click the **🦋 butterfly button** in the top right corner, then click the **🌙 moon icon** for dark mode! You can also change lots of other things in that menu.";
    }
    
    if (msg.includes('text size') || msg.includes('bigger') || msg.includes('font')) {
      return "Click the **🦋 butterfly** (top right), then use the **A+** button to make text bigger or **A-** to make it smaller! Keep clicking until it's perfect for you.";
    }
    
    if (msg.includes('course')) {
      return "All courses are listed in the **left sidebar**! You'll see Python Basics, Control Flow, Data Structures, Functions, and more. Just click any one to open it!";
    }
  }
  
  // ==========================================
  // HOW DO I / HOW TO
  // ==========================================
  
  if (msg.includes('how do i') || msg.includes('how to') || msg.includes('how can')) {
    
    if (msg.includes('start') || msg.includes('begin')) {
      if (currentTab.includes('theory')) {
        return "You're on the Theory tab - perfect place to start! Read through the concepts (don't memorize, just get the idea). When you're ready, click **📊 Slides** at the top to see actual working code. After that, you'll go to **💻 Practice** to write your own. Sound good?";
      } else {
        return "Here's how to start: Pick **Python Basics** from the left sidebar, look at **�� Slides** to see examples, click **💻 Try This Example** on one, then play with the code! Want me to walk you through it step by step?";
      }
    }
    
    if (msg.includes('change') || msg.includes('customize')) {
      return "To customize your experience, click the **🦋 butterfly button** in the top right! You can change:\n\n• Dark/light mode 🌙\n• Text size A+/A-\n• Dyslexia-friendly font 📖\n• Focus mode 🎯\n• Text-to-speech 🔊\n• And lots more!\n\nTry it out!";
    }
    
    if (msg.includes('run') || msg.includes('execute')) {
      return "To run code: Make sure you're in **💻 Practice** tab, write code in the editor, then click the big **Run Code** button! The output shows up below in the black console box. Try it!";
    }
    
    if (msg.includes('save') || msg.includes('download')) {
      return "Your code auto-saves as you type! To download it, you can copy it from the editor and paste it into a file on your computer. Want me to show you how to export code?";
    }
  }
  
  // ==========================================
  // LOST / DON'T KNOW WHAT TO DO
  // ==========================================
  
  if (msg.includes('lost') || msg.includes('where do i start') || msg.includes('what do i do') ||
      msg.includes('i don\'t know') || msg.includes('dont know') || msg.includes('no idea') ||
      msg.includes('confused where')) {
    
    // Context-aware based on current tab
    if (currentTab.includes('theory')) {
      return "You're on the **Theory** tab right now. This is where concepts are explained. Read it through, but don't stress about memorizing everything.\n\nWhen you're ready, click **📊 Slides** at the top to see actual working code examples. That's usually more fun! Want to jump there now?";
    }
    
    if (currentTab.includes('slide') || currentTab.includes('example')) {
      return "You're looking at **examples** right now! See those buttons under each example?\n\n• **💻 Try This Example** - loads the code so you can play with it\n• **▶️ Run & See Output** - just shows you what it does\n\nClick one and see what happens! Which one should we try?";
    }
    
    if (currentTab.includes('practice')) {
      if (!hasCode) {
        return "You're in the **Practice** area! That big empty box is where you write Python code. Want to try something super simple? Type this:\n\n```\nprint('Hello!')\n```\n\nThen click **Run Code** below it. Try it!";
      } else {
        return "I see you've written some code! Now click the **Run Code** button below the editor to make it work. The output will show up in the black box underneath. Go for it!";
      }
    }
    
    // General lost
    return "No worries! Let me orient you. There are 4 main areas:\n\n**📖 Theory** (top tab) - Learn concepts\n**📊 Slides** (top tab) - See working examples\n**💻 Practice** (top tab) - Write your own code\n**🦋 Butterfly** (top right) - Customize everything\n\nYou're currently looking at **" + (currentTab || "the main area") + "**. Want to try the Slides tab to see some examples?";
  }
  
  // ==========================================
  // STUCK / CONFUSED / TOO HARD
  // ==========================================
  
  if (msg.includes('stuck') || msg.includes('confused') || msg.includes('don\'t understand') ||
      msg.includes('dont understand') || msg.includes('too hard') || msg.includes('difficult')) {
    
    if (currentTab.includes('practice') && hasOutput) {
      return "Okay, I see you're in the Practice area and you've run some code. Is there an error showing in the output? Or is it working but you don't understand what it's doing? Tell me what's going on and I'll help!";
    }
    
    return "Hey, it's totally normal to feel stuck! Let's break this down.\n\nWhat specifically is tripping you up? Like:\n• A specific concept you don't get?\n• Code that's not working?\n• Not sure what to do next?\n\nJust tell me in your own words and we'll tackle it together!";
  }
  
  // ==========================================
  // ERRORS / DEBUGGING
  // ==========================================
  
  if (msg.includes('error') || msg.includes('not working') || msg.includes('wrong') || msg.includes('broken')) {
    
    if (msg.includes('syntax')) {
      return "SyntaxError! This means Python doesn't understand your code's grammar. Common causes:\n\n• Forgot quotes around text\n• Missing colon : after if/for/def\n• Mismatched ( ) or { }\n\nCan you share the line that has the error? I'll help you spot it!";
    }
    
    if (msg.includes('name')) {
      return "NameError means Python doesn't recognize that variable name. Quick checklist:\n\n• Is it spelled right? (case-sensitive!)\n• Did you create the variable before using it?\n• Did you accidentally put quotes around it?\n\nShow me the code?";
    }
    
    if (msg.includes('indent')) {
      return "IndentationError! Python is picky about spaces. Code inside if/for/def blocks needs to be indented (4 spaces or 1 tab).\n\nMake sure all lines that should be together have the same indent. Want to share the code so I can see?";
    }
    
    return "Okay, let's fix this! Here's what to do:\n\n1. Look at the **Output Console** (black box in Practice tab)\n2. Find the LAST line of the error - that's the key info\n3. Copy it and paste it here\n4. Also share your code if you can\n\nI'll help you figure it out!";
  }
  
  // ==========================================
  // WHAT'S NEXT / FINISHED
  // ==========================================
  
  if (msg.includes('what now') || msg.includes('what next') || msg.includes('finished') || 
      msg.includes('done') || msg.includes('completed') || msg.includes('what else')) {
    
    return "Nice work! You've got options:\n\n**Keep practicing:**\n• Scroll down in **Practice** tab for more exercises\n• Try another example from **Slides** tab\n\n**Level up:**\n• Pick a new course from the left sidebar\n• Ask me for a custom challenge\n\n**Build something:**\n• Try writing code from scratch without examples\n\nWhat sounds fun?";
  }
  
  // ==========================================
  // FEATURES & TOOLS
  // ==========================================
  
  if (msg.includes('feature') || msg.includes('tool') || msg.includes('what can')) {
    return "Cool! Here's what you can do:\n\n**Learn:**\n• Read Theory, see Slides, do Practice exercises\n• Get instant help from me (right here!)\n\n**Customize:**\n• Click 🦋 butterfly for dark mode, text size, focus mode, etc.\n• Click 💭 to report your mood\n\n**Code:**\n• Write & run Python in Practice tab\n• Try examples from Slides tab\n\nWhat do you want to try first?";
  }
  
  // ==========================================
  // ACCESSIBILITY QUESTIONS
  // ==========================================
  
  if (msg.includes('text to speech') || msg.includes('read aloud')) {
    return "Text-to-speech is awesome! Click the **🦋 butterfly**, then click the **🔊 speaker icon**. Now click anywhere on the page to hear it read! Click again to stop. Try it on the Theory tab!";
  }
  
  if (msg.includes('reading pointer') || msg.includes('line follow')) {
    return "The reading pointer is a colored line that follows your mouse! Click **🦋 butterfly** → **📍 pointer icon**. You can even customize the color and thickness. Super helpful for keeping your place!";
  }
  
  if (msg.includes('focus mode') || msg.includes('distraction')) {
    return "Focus Mode removes distractions! Click **🦋 butterfly** → **🎯 Focus Mode**. It dims everything except what you're working on. Perfect when you need to concentrate!";
  }
  
  if (msg.includes('voice') || msg.includes('speak my code')) {
    return "You can speak your code! Click **🦋 butterfly** → **🎤 microphone icon**. Then just speak and it types for you. Click the mic again when you're done. Give it a shot!";
  }
  
  // ==========================================
  // COURSE SELECTION
  // ==========================================
  
  if (msg.includes('which course') || msg.includes('what course') || msg.includes('best course')) {
    return "Depends on where you're at!\n\n**Brand new?** Start with **Python Basics** (left sidebar)\n\n**Comfortable with basics?** Try **Control Flow** or **Data Structures**\n\n**Want something practical?** Check out **London Transport API** - uses real data!\n\nWhere are you in your Python journey?";
  }
  
  // ==========================================
  // GREETINGS
  // ==========================================
  
  if (msg.match(/^(hi|hello|hey|sup|yo)$/)) {
    const greeting = getTimeGreeting();
    const name = getUserName();
    const nameStr = (name && name !== 'null') ? `, ${name}` : '';
    
    if (!currentCourse) {
      return `${greeting}${nameStr}! I'm your AI guide - I know every part of this platform and I'm here to help you!\n\nWant a quick tour of how everything works, or should we jump straight into coding?`;
    } else {
      return `${greeting}${nameStr}! You're working on ${currentCourse}. Need help with something, or just want to chat? I'm here!`;
    }
  }
  
  // ==========================================
  // GRATITUDE / POSITIVE
  // ==========================================
  
  if (msg.includes('thank') || msg.includes('thanks') || msg.includes('grazie')) {
    const replies = [
      "You're so welcome! It makes me happy to help. What shall we tackle next? \U0001F60A",
      "Anytime! That's what I'm here for. Ready to keep going, or need a break?",
      "You're welcome! You're doing really well, you know. What's next? \U0001F4AA",
      "Happy to help! Every question you ask makes you a better programmer. What else?",
      "No problem at all! I love seeing you learn. Want to try something else?"
    ];
    return replies[Math.floor(Math.random() * replies.length)];
  }
  
  if (msg.includes('cool') || msg.includes('nice') || msg.includes('awesome') || msg.includes('great')) {
    return "Right?! So what's next - want to try something new, or keep going with what you're doing?";
  }
  
  // ==========================================
  // EMOTIONAL SUPPORT
  // ==========================================
  
  if (msg.includes('overwhelm') || msg.includes('too much') || msg.includes('stressed')) {
    return "Hey, I totally get it. Let's slow down and just focus on one tiny thing. Forget everything else for now.\n\nWhat's ONE small thing you want to understand right now? Just that one thing. We'll tackle it together.";
  }
  
  if (msg.includes('frustrat') || msg.includes('annoying') || msg.includes('hate this')) {
    return "I hear you - this can be frustrating sometimes! That's completely normal.\n\nWant to:\n• Take a quick break?\n• Try something easier?\n• Have me walk you through this step by step?\n\nYour call - no judgment!";
  }
  
  if (msg.includes('tired') || msg.includes('exhausted')) {
    return "Sounds like you've been working hard! Maybe it's time for a little break? Your brain needs rest to learn well.\n\nGrab some water, stretch, and come back when you're ready. I'll be here!";
  }
  
  // ==========================================
  // DEFAULT - ASK FOR CLARIFICATION
  // ==========================================
  
  return "Hmm, I want to help but I'm not totally sure what you mean! Can you tell me a bit more?\n\nLike:\n• Are you stuck on something?\n• Looking for a feature?\n• Don't know where to go?\n• Have a question about Python?\n\nJust explain it in your own words and I'll help!";
}

// Helper function - get time-based greeting
function getTimeGreeting() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return 'Good morning';
  if (hour >= 12 && hour < 17) return 'Good afternoon';
  if (hour >= 17 && hour < 22) return 'Good evening';
  return 'Good night';
}

// Helper function - try to get user name
function getUserName() {
  return localStorage.getItem('userName') || sessionStorage.getItem('userName') || window.userName || null;
}
