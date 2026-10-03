import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'compuquest.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        streak INTEGER DEFAULT 1,
        last_active_date TEXT,
        avatar TEXT DEFAULT 'happy_bot',
        title TEXT DEFAULT 'Explorer',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        slug TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subtitle TEXT,
        badge_label TEXT,
        accent_color TEXT,
        icon TEXT,
        order_idx INTEGER,
        description TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_slug TEXT NOT NULL,
        title TEXT NOT NULL,
        learning_material TEXT,
        story_hook TEXT,
        xp_reward INTEGER DEFAULT 100,
        difficulty TEXT,
        order_idx INTEGER,
        quiz_question TEXT,
        quiz_options TEXT,
        quiz_answer INTEGER,
        FOREIGN KEY (category_slug) REFERENCES categories(slug)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quest_id INTEGER NOT NULL,
        completed INTEGER DEFAULT 0,
        completed_at TEXT,
        UNIQUE(user_id, quest_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (quest_id) REFERENCES quests(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        icon TEXT,
        category TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        badge_id INTEGER NOT NULL,
        earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, badge_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (badge_id) REFERENCES badges(id)
    )
    ''')
    
    conn.commit()
    seed_data(conn)
    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    
    if cursor.execute('SELECT COUNT(*) FROM quests').fetchone()[0] > 0:
        return

    cursor.execute('''
    INSERT OR IGNORE INTO users (username, email, password_hash, xp, level, streak, title, last_active_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('student1', 'student@school.edu', generate_password_hash('password', method='pbkdf2:sha256'), 150, 2, 3, 'Smart Kid', datetime.now().isoformat()))

    categories = [
        ('fundamentals', 'Computer Fundamentals', 'Grade 1-3', 'Basics', '#FF6B6B', '🖥️', 1, 'Learn what a computer is and its main parts!'),
        ('hardware_software', 'Software & Hardware', 'Grade 4-5', 'Tech', '#4ECDC4', '⚙️', 2, 'Discover what makes a computer work on the inside and outside!'),
        ('internet', 'Internet & Networking', 'Grade 6-7', 'Web', '#45B7D1', '🌐', 3, 'Explore the World Wide Web and stay safe online!'),
        ('digital_skills', 'Digital Skills & Logic', 'Grade 8-10', 'Logic', '#96CEB4', '🧠', 4, 'Learn about data, memory, and how computers think!')
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO categories (slug, title, subtitle, badge_label, accent_color, icon, order_idx, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', categories)

    badges = [
        ('first_step', 'First Step', 'Completed the first lesson', '🌟', 'fundamentals'),
        ('hardware_hero', 'Hardware Hero', 'Mastered Computer Parts', '🔧', 'hardware_software'),
        ('web_surfer', 'Web Surfer', 'Navigated the Internet', '🏄', 'internet'),
        ('data_master', 'Data Master', 'Understood Digital Logic', '📊', 'digital_skills'),
        ('super_learner', 'Super Learner', 'Earned 500 XP', '🚀', 'general')
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO badges (slug, name, description, icon, category)
    VALUES (?, ?, ?, ?, ?)
    ''', badges)

    quests = [
        # Fundamentals
        (
            'fundamentals', '1. What is a Computer?',
            """<h2>The Magic Machine</h2><p>A <strong>computer</strong> is a smart electronic machine that can take information, remember it, and do cool things with it! You can use it to play games, draw pictures, write stories, and watch videos.</p><p>It follows your instructions. When you click the mouse or press a key, the computer listens to you immediately!</p>""",
            'Let us start our adventure into the digital world!',
            100, 'Easy', 1,
            'Which of the following best describes a computer?',
            json.dumps(['A magic box that does things by itself', 'A smart machine that follows your instructions', 'A TV that only shows cartoons', 'A toy that needs no power']),
            1
        ),
        (
            'fundamentals', '2. The Monitor and Display',
            """<h2>The Window to the World</h2><p>The <strong>monitor</strong> looks like a TV screen. It shows you everything the computer is doing. Without it, you wouldn't be able to see your games or drawings!</p><p>Monitors come in many sizes, from tiny phone screens to giant desktop displays.</p>""",
            'See the magic happen on screen!',
            100, 'Easy', 2,
            'What is the main job of the monitor?',
            json.dumps(['To print paper', 'To play music', 'To show you pictures and text', 'To type letters']),
            2
        ),
        (
            'fundamentals', '3. The Keyboard',
            """<h2>Talking to the Computer</h2><p>The <strong>keyboard</strong> is full of buttons called keys. It has letters, numbers, and special symbols.</p><p>When you press a key, the computer knows exactly what you want to write. There are even special keys like "Space" and "Enter" to help you type.</p>""",
            'Type your way to victory!',
            100, 'Easy', 3,
            'Which key helps you make a gap between two words?',
            json.dumps(['Enter', 'Shift', 'Spacebar', 'Escape']),
            2
        ),
        (
            'fundamentals', '4. The Mouse',
            """<h2>Point and Click!</h2><p>The <strong>mouse</strong> helps you point at things on the screen. It moves a little arrow called the <strong>cursor</strong>.</p><p>You can "click" the left button to select something, and "double-click" it to open it!</p>""",
            'Grab your mouse and let us explore!',
            100, 'Easy', 4,
            'What do we call the little arrow on the screen controlled by the mouse?',
            json.dumps(['The Pointer or Cursor', 'The Clicker', 'The Arrow-bot', 'The Magic Wand']),
            0
        ),
        (
            'fundamentals', '5. The Brain: CPU',
            """<h2>The Computer's Brain</h2><p>The <strong>CPU</strong> stands for Central Processing Unit. It is the absolute brain of the computer!</p><p>It does all the math, thinking, and running of your programs. Without the CPU, the computer wouldn't know how to do anything at all.</p>""",
            'Meet the smartest part of the machine.',
            150, 'Easy', 5,
            'What does CPU stand for?',
            json.dumps(['Central Playing Unit', 'Central Processing Unit', 'Computer Power Unit', 'Cool Processing Unit']),
            1
        ),
        (
            'fundamentals', '6. Powering On and Off',
            """<h2>Wake up and Sleep</h2><p>To turn on a computer, you press the <strong>Power Button</strong>. But to turn it off, you shouldn't just press the button again!</p><p>You must tell the computer to "Shut Down" properly using the screen menu. This gives it time to close all its programs safely.</p>""",
            'Always be polite when waking up or putting your computer to sleep!',
            150, 'Medium', 6,
            'What is the proper way to turn off a computer?',
            json.dumps(['Pull the plug out of the wall', 'Hold the power button until it turns black', 'Use the Shut Down menu on the screen', 'Leave it on forever']),
            2
        ),

        # Hardware & Software
        (
            'hardware_software', '1. Hardware vs Software',
            """<h2>Touch it or Not?</h2><p><strong>Hardware</strong> is any part of the computer you can physically touch, like the mouse, keyboard, or the screen.</p><p><strong>Software</strong> is the programs and apps inside the computer. You cannot touch software. Games, paint programs, and web browsers are software!</p>""",
            'Hardware and Software working together as best friends!',
            150, 'Medium', 1,
            'Which of the following is an example of Software?',
            json.dumps(['Computer Mouse', 'A Video Game', 'The Monitor', 'The Keyboard']),
            1
        ),
        (
            'hardware_software', '2. The Operating System',
            """<h2>The Big Boss</h2><p>An <strong>Operating System (OS)</strong> is the most important software on a computer. It manages all the other programs!</p><p>Examples of Operating Systems include Windows, macOS, and Android on phones. It is the boss that tells the hardware what to do.</p>""",
            'Meet the manager of the computer!',
            150, 'Medium', 2,
            'Which of the following is an Operating System?',
            json.dumps(['Google Chrome', 'Microsoft Word', 'Windows', 'Minecraft']),
            2
        ),
        (
            'hardware_software', '3. Application Software',
            """<h2>Tools for Specific Jobs</h2><p><strong>Applications</strong> (or "apps") are software designed to help you do a specific task.</p><p>For example, a web browser helps you surf the internet, a word processor helps you type documents, and a game app lets you play!</p>""",
            'Apps make computers fun and useful!',
            150, 'Medium', 3,
            'If you want to type a story, what type of application would you use?',
            json.dumps(['A Word Processor', 'A Web Browser', 'A Music Player', 'A Calculator']),
            0
        ),
        (
            'hardware_software', '4. Storage Devices',
            """<h2>Where do files go?</h2><p>Computers need a place to save your pictures and games so they don’t disappear when you turn it off. We call this <strong>storage</strong>.</p><p>Examples include Hard Drives (HDD), Solid State Drives (SSD), and USB Flash Drives (pendrives). They act like digital backpacks!</p>""",
            'Keep your precious files safe forever!',
            150, 'Medium', 4,
            'What is a USB Flash Drive used for?',
            json.dumps(['To show pictures on the screen', 'To store and save files', 'To print documents', 'To play music loudly']),
            1
        ),
        (
            'hardware_software', '5. RAM: Short-term Memory',
            """<h2>Thinking Space</h2><p><strong>RAM</strong> (Random Access Memory) is the computer's short-term memory.</p><p>When you open a game, the computer loads it into RAM so it can run fast. But if you turn off the computer, everything in RAM is forgotten! That's why we must save our work to storage.</p>""",
            'RAM helps your computer think quickly!',
            150, 'Hard', 5,
            'What happens to the data in RAM when the computer is turned off?',
            json.dumps(['It gets saved forever', 'It gets uploaded to the internet', 'It is completely erased', 'It turns into a virus']),
            2
        ),
        (
            'hardware_software', '6. Input and Output',
            """<h2>In and Out</h2><p><strong>Input devices</strong> send information INTO the computer (like a Keyboard or Mouse).</p><p><strong>Output devices</strong> push information OUT of the computer (like a Monitor, Printer, or Speakers).</p>""",
            'Understand how information flows!',
            150, 'Medium', 6,
            'Which of the following is an Output device?',
            json.dumps(['Microphone', 'Keyboard', 'Printer', 'Mouse']),
            2
        ),

        # Internet & Networking
        (
            'internet', '1. What is the Internet?',
            """<h2>The World Wide Web</h2><p>The <strong>Internet</strong> is a giant network connecting millions of computers around the world. It allows them to talk to each other!</p><p>We use a <strong>Web Browser</strong> (like Chrome or Safari) to visit websites. Every website has an address called a <strong>URL</strong>.</p>""",
            'Surf the global digital waves!',
            200, 'Medium', 1,
            'What tool do we use to visit websites?',
            json.dumps(['A Web Browser', 'A Keyboard', 'A CPU', 'A Printer']),
            0
        ),
        (
            'internet', '2. Understanding URLs',
            """<h2>Web Addresses</h2><p>A <strong>URL</strong> is like a house address for a website. It tells the browser exactly where to go.</p><p>A URL usually starts with <strong>https://</strong> (which means it is secure) and ends with things like .com, .org, or .edu.</p>""",
            'Find your way around the web!',
            200, 'Medium', 2,
            'What does the "s" in https:// stand for?',
            json.dumps(['Super', 'Speedy', 'Secure', 'System']),
            2
        ),
        (
            'internet', '3. Search Engines',
            """<h2>The Internet Library</h2><p>A <strong>Search Engine</strong> (like Google or Bing) helps you find information on the internet.</p><p>You just type in keywords about what you want to know, and the search engine looks through millions of websites to find the best answers for you.</p>""",
            'Learn how to find anything instantly!',
            200, 'Medium', 3,
            'What is the purpose of a search engine?',
            json.dumps(['To play games', 'To find information on the internet', 'To clean your computer', 'To send text messages']),
            1
        ),
        (
            'internet', '4. Email Basics',
            """<h2>Digital Letters</h2><p><strong>Email</strong> (Electronic Mail) is a way to send messages from your computer to someone else's computer over the internet.</p><p>An email address looks like this: <em>name@website.com</em>. The "@" symbol separates the person's name from the email provider.</p>""",
            'Send a letter at the speed of light!',
            200, 'Medium', 4,
            'Which symbol is required in every email address?',
            json.dumps(['#', '$', '@', '&']),
            2
        ),
        (
            'internet', '5. Computer Networks',
            """<h2>Connecting Devices</h2><p>A <strong>Network</strong> is two or more computers connected together so they can share things.</p><p>A LAN (Local Area Network) connects computers in one building, like your school. A WAN (Wide Area Network) connects computers across cities or countries!</p>""",
            'Discover how computers talk to each other.',
            200, 'Hard', 5,
            'What type of network connects computers inside a single building?',
            json.dumps(['WAN', 'LAN', 'INTERNET', 'WIFI']),
            1
        ),
        (
            'internet', '6. Cyber Safety',
            """<h2>Protect Yourself!</h2><p>When using the internet, never share your real name, address, or passwords with strangers. Always be polite and respectful to others online, just like in real life.</p><p>If you see something that makes you uncomfortable, always tell a trusted adult or teacher!</p>""",
            'Be a responsible and safe digital citizen.',
            200, 'Medium', 6,
            'What should you do if a stranger asks for your password online?',
            json.dumps(['Give it to them', 'Ignore them and tell a trusted adult', 'Give a fake password', 'Share it with your friends instead']),
            1
        ),

        # Digital Skills
        (
            'digital_skills', '1. Bits and Bytes',
            """<h2>Computer Language</h2><p>Computers don’t understand English or Math the way we do. They only understand two things: ON and OFF. We represent this with <strong>1</strong> (ON) and <strong>0</strong> (OFF).</p><p>A single 1 or 0 is called a <strong>Bit</strong>. If you group 8 bits together, it makes a <strong>Byte</strong>. A Byte is enough to store one letter, like the letter "A"!</p>""",
            'Understand how computers think.',
            250, 'Hard', 1,
            'How many bits make up one Byte?',
            json.dumps(['4', '10', '8', '100']),
            2
        ),
        (
            'digital_skills', '2. Megabytes and Gigabytes',
            """<h2>Measuring Data</h2><p>Data is measured in Bytes. A <strong>Kilobyte (KB)</strong> is about 1,000 Bytes (a small text file).</p><p>A <strong>Megabyte (MB)</strong> is about 1,000 KB (a song or picture).</p><p>A <strong>Gigabyte (GB)</strong> is about 1,000 MB (a high-quality movie)!</p>""",
            'How heavy is a digital file?',
            250, 'Hard', 2,
            'Which unit of data is the largest?',
            json.dumps(['Byte', 'Kilobyte (KB)', 'Megabyte (MB)', 'Gigabyte (GB)']),
            3
        ),
        (
            'digital_skills', '3. File Types',
            """<h2>Identifying Files</h2><p>Files have <strong>extensions</strong> at the end of their name to tell the computer what type of file it is.</p><p>For example, <em>.jpg</em> or <em>.png</em> are pictures. <em>.mp3</em> is music. <em>.docx</em> or <em>.txt</em> are text documents!</p>""",
            'Learn to read file names like a pro.',
            250, 'Medium', 3,
            'What type of file is "vacation.jpg"?',
            json.dumps(['A text document', 'A music file', 'A picture/image file', 'A video game']),
            2
        ),
        (
            'digital_skills', '4. Folder Organization',
            """<h2>Keeping things tidy</h2><p>Just like you put papers into a real folder, you can put files into a digital <strong>Folder</strong> (also called a Directory).</p><p>Creating folders for your pictures, homework, and games helps you find things quickly instead of having a messy desktop!</p>""",
            'Become a master of digital organization.',
            250, 'Easy', 4,
            'What is the main purpose of creating digital folders?',
            json.dumps(['To make the computer run faster', 'To organize files so they are easy to find', 'To delete viruses', 'To make files smaller']),
            1
        ),
        (
            'digital_skills', '5. Algorithms',
            """<h2>Step by Step</h2><p>An <strong>Algorithm</strong> is a list of step-by-step instructions to solve a problem or complete a task. It’s just like a recipe for baking a cake!</p><p>Computers need very clear algorithms to do anything. If an instruction is missing, the computer might get confused or do the wrong thing.</p>""",
            'Write the perfect recipe for your computer!',
            250, 'Hard', 5,
            'What is an algorithm?',
            json.dumps(['A type of computer virus', 'A step-by-step list of instructions', 'A piece of hardware', 'The brain of the computer']),
            1
        ),
        (
            'digital_skills', '6. Bug Hunting',
            """<h2>Squashing Errors</h2><p>Sometimes, algorithms or computer programs have mistakes in them. We call these mistakes <strong>Bugs</strong>.</p><p>When a programmer looks through their instructions to find and fix the bug, it is called <strong>Debugging</strong>. It requires patience and logic!</p>""",
            'Grab your magnifying glass, it is time to debug!',
            250, 'Hard', 6,
            'What do we call a mistake or error in a computer program?',
            json.dumps(['A Glitch', 'A Virus', 'A Bug', 'A Hacker']),
            2
        )
    ]
    
    cursor.executemany('''
    INSERT INTO quests (category_slug, title, learning_material, story_hook, xp_reward, difficulty, order_idx, quiz_question, quiz_options, quiz_answer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', quests)
    
    conn.commit()
    print("Massive Database seeded successfully!")

if __name__ == '__main__':
    init_db()
