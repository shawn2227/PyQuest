import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'pukki_arcade.db')

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
        avatar TEXT DEFAULT 'cyber_fox',
        title TEXT DEFAULT 'Script Novice',
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
        instructions TEXT,
        starter_code TEXT,
        test_code TEXT,
        solution_code TEXT,
        hint TEXT,
        xp_reward INTEGER DEFAULT 100,
        difficulty TEXT,
        order_idx INTEGER,
        FOREIGN KEY (category_slug) REFERENCES categories(slug)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_slug TEXT NOT NULL,
        question TEXT NOT NULL,
        code_snippet TEXT,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL,
        explanation TEXT,
        xp_reward INTEGER DEFAULT 25,
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
        submitted_code TEXT,
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
    
    # Guard to prevent duplicate seeding
    if cursor.execute('SELECT COUNT(*) FROM quests').fetchone()[0] > 0:
        return

    # Seed demo user
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, email, password_hash, xp, level, streak, title, last_active_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('cyber_coder', 'coder@pukki.dev', generate_password_hash('pukki123', method='pbkdf2:sha256'), 340, 2, 3, 'Code Adventurer', datetime.now().isoformat()))

    # Seed Categories
    categories = [
        ('beginner', 'Beginner', 'Script Rookie', 'Beginner', '#10b981', '🌱', 1, 'Learn the basics of Python'),
        ('amateur', 'Amateur', 'Code Adventurer', 'Amateur', '#06b6d4', '⚡', 2, 'Intermediate concepts and data structures'),
        ('advanced', 'Advanced', 'Logic Sorcerer', 'Advanced', '#8b5cf6', '🔮', 3, 'Advanced Python patterns and OOP'),
        ('professional', 'Professional', 'Cyber Grandmaster', 'Professional', '#f59e0b', '👑', 4, 'Master level algorithms and concepts')
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO categories (slug, title, subtitle, badge_label, accent_color, icon, order_idx, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', categories)

    # Seed Badges
    badges = [
        ('first_blood', 'First Blood', 'Completed the first quest', '🩸', 'beginner'),
        ('rookie_slayer', 'Rookie Slayer', 'Completed all beginner quests', '🗡️', 'beginner'),
        ('adventurer_elite', 'Adventurer Elite', 'Master of the amateur rank', '🛡️', 'amateur'),
        ('sorcerer_archmage', 'Archmage', 'Completed advanced sorcery', '🧙‍♂️', 'advanced'),
        ('grandmaster_legend', 'Legend', 'A true grandmaster', '🏆', 'professional'),
        ('speed_runner', 'Speed Runner', 'Completed a quest in record time', '⏱️', 'general')
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO badges (slug, name, description, icon, category)
    VALUES (?, ?, ?, ?, ?)
    ''', badges)

    # Quests
    quests = [
        (
            'beginner', 'Variables & Print',
            '<h2>The Magic Boxes</h2><p>Imagine your computer\'s memory is a giant warehouse of empty cardboard boxes. A <strong>variable</strong> is just a label you slap on one of these boxes so you can put something inside and find it later.</p><ul><li><code>score = 100</code> puts the number 100 in a box labeled "score"</li></ul><h4>Show Your Work</h4><p>The <code>print()</code> function is like a megaphone. It shouts whatever is inside the box so everyone (and you) can see it.</p>',
            'Initialize the distress signal!',
            'Create a variable called `signal` and set it to `"SOS"`, then print it.',
            '# Create the variable signal here\n',
            'assert "signal" in dir() or "signal" in locals(), "Variable \'signal\' not defined!"\nassert signal == "SOS", f"Expected signal to be \'SOS\', got \'{signal}\'"\nprint("TEST_PASSED: Signal broadcast successful!")',
            'signal = "SOS"\nprint(signal)',
            'Use standard assignment: signal = "SOS"',
            100, 'Easy', 1
        ),
        (
            'beginner', 'Math Operations',
            '<h2>Math, but Cooler</h2><p>Python acts like a massive calculator. You have the standard gear: <code>+</code> (add), <code>-</code> (subtract), <code>*</code> (multiply), <code>/</code> (divide). But you also get some power-ups!</p><ul><li><code>**</code> is for exponents (e.g., 2**3 = 8)</li><li><code>//</code> is integer division (e.g., 5//2 = 2)</li><li><code>%</code> is modulo, meaning remainder (e.g., 5%2 = 1)</li></ul>',
            'Calculate the mission loot!',
            'Write a function `calculate_loot(gold, multiplier, bonus)` that returns (gold * multiplier) + bonus.',
            'def calculate_loot(gold, multiplier, bonus):\n    # Return the total\n    pass',
            'assert calculate_loot(10, 2, 5) == 25, f"Expected 25, got {calculate_loot(10, 2, 5)}"\nassert calculate_loot(0, 10, 100) == 100, f"Expected 100, got {calculate_loot(0, 10, 100)}"\nassert calculate_loot(5, 5, 0) == 25, f"Expected 25, got {calculate_loot(5, 5, 0)}"\nprint("TEST_PASSED: Loot math is legit!")',
            'def calculate_loot(gold, multiplier, bonus):\n    return (gold * multiplier) + bonus',
            'Just return gold * multiplier + bonus',
            100, 'Easy', 2
        ),
        (
            'beginner', 'Booleans & Logic',
            '<h2>The Ultimate Yes/No</h2><p>In Python, things are either <code>True</code> or <code>False</code>. These are called Booleans. Think of it like a light switch.</p><p>You can combine them using logic operators: <strong>and</strong> (both must be True), <strong>or</strong> (at least one is True), <strong>not</strong> (flips it).</p><h4>Comparisons</h4><p>We use <code>==</code> for equal, <code>!=</code> for not equal, <code>></code>, <code><</code>, <code>>=</code>, <code><=</code>.</p>',
            'Guard the VIP lounge!',
            'Write a function `can_enter(level, has_vip)` that returns True if level >= 18 OR has_vip is True.',
            'def can_enter(level, has_vip):\n    pass',
            'assert can_enter(18, False) == True, "Level 18 should be allowed"\nassert can_enter(10, True) == True, "VIP should be allowed"\nassert can_enter(15, False) == False, "Level 15 without VIP should be rejected"\nassert can_enter(20, False) == True, "Level 20 should be allowed"\nprint("TEST_PASSED: Bouncer protocol works!")',
            'def can_enter(level, has_vip):\n    return level >= 18 or has_vip',
            'Use the OR operator',
            100, 'Easy', 3
        ),
        (
            'beginner', 'Strings',
            '<h2>String Theory</h2><p>Strings are just text wrapped in quotes. Python has amazing string powers!</p><ul><li>Concatenation: <code>"Cyber" + "Punk"</code></li><li>f-strings (magical!): <code>f"Hello {name}"</code> injects variables right in!</li><li>Methods: <code>.upper()</code>, <code>.lower()</code></li><li>Length: <code>len(my_string)</code> tells you how many characters there are.</li></ul>',
            'Format the gamer tags!',
            'Write a function `create_tag(name)` that returns `f"@{name.lower()}"` ONLY if len(name) > 0. If it is 0, return "@unknown".',
            'def create_tag(name):\n    pass',
            'assert create_tag("Ninja") == "@ninja", f"Expected \'@ninja\', got \'{create_tag(\'Ninja\')}\'"\nassert create_tag("") == "@unknown", f"Expected \'@unknown\' for empty name"\nassert create_tag("CYBER") == "@cyber", f"Expected \'@cyber\', got \'{create_tag(\'CYBER\')}\'"\nprint("TEST_PASSED: Tag system deployed!")',
            'def create_tag(name):\n    if len(name) > 0:\n        return f"@{name.lower()}"\n    return "@unknown"',
            'Check length first, then use an f-string',
            100, 'Easy', 4
        ),
        (
            'beginner', 'If/Elif/Else',
            '<h2>Crossroads</h2><p>Sometimes your code needs to make choices. Use <code>if</code> to check a condition. If it fails, Python tries <code>elif</code> (else if). If all else fails, it runs <code>else</code>.</p><pre><code>if ammo == 0:\n    reload()\nelif ammo < 10:\n    warn()\nelse:\n    shoot()</code></pre>',
            'Grade the arena performance!',
            'Write `get_rank(score)` returning "S" for >= 90, "A" for >= 75, "B" for >= 50, "C" otherwise.',
            'def get_rank(score):\n    pass',
            'assert get_rank(95) == "S", f"Expected \'S\' for 95, got \'{get_rank(95)}\'"\nassert get_rank(75) == "A", f"Expected \'A\' for 75, got \'{get_rank(75)}\'"\nassert get_rank(50) == "B", f"Expected \'B\' for 50, got \'{get_rank(50)}\'"\nassert get_rank(10) == "C", f"Expected \'C\' for 10, got \'{get_rank(10)}\'"\nprint("TEST_PASSED: Ranking system online!")',
            'def get_rank(score):\n    if score >= 90: return "S"\n    elif score >= 75: return "A"\n    elif score >= 50: return "B"\n    else: return "C"',
            'Chain if, elif, else in order of highest score first.',
            100, 'Medium', 5
        ),
        (
            'amateur', 'Lists',
            '<h2>Inventory Management</h2><p>A list is like a backpack. It holds items in order! You can put things in: <code>my_list.append("potion")</code>. You can get things out using their index (starting at 0): <code>my_list[0]</code>.</p><p>Slicing lets you grab a chunk: <code>my_list[1:3]</code>.</p>',
            'Organize the loot stash.',
            'Write `organize_stash(inventory, junk)` which returns a new list containing all items in inventory EXCEPT the junk item. It should also be sorted alphabetically.',
            'def organize_stash(inventory, junk):\n    pass',
            'result = organize_stash(["sword", "apple", "trash"], "trash")\nassert result == ["apple", "sword"], f"Expected [\'apple\', \'sword\'], got {result}"\nresult2 = organize_stash(["a", "b", "a"], "a")\nassert result2 == ["b"], f"Expected [\'b\'], got {result2}"\nprint("TEST_PASSED: Inventory organized!")',
            'def organize_stash(inventory, junk):\n    return sorted([x for x in inventory if x != junk])',
            'Remove the junk, then sort it.',
            150, 'Medium', 1
        ),
        (
            'amateur', 'Dictionaries',
            '<h2>Key-Value Stores</h2><p>Dictionaries are like phonebooks or player profiles. Instead of numeric indexes, you use keys (like "name") to find values.</p><pre><code>player = {"name": "Zer0", "hp": 100}\nprint(player["hp"]) # 100</code></pre><p>Add or update entries easily: <code>player["level"] = 2</code>.</p>',
            'Compile the player profile.',
            'Write `create_gamer_tag(username, kills, deaths)` returning a dict with keys: "tag" (username), "kdr" (kills/deaths OR 0 if deaths is 0), and "rank" ("Pro" if kdr > 1 else "Noob").',
            'def create_gamer_tag(username, kills, deaths):\n    pass',
            'r1 = create_gamer_tag("X", 10, 2)\nassert r1 == {"tag": "X", "kdr": 5.0, "rank": "Pro"}, f"Got {r1}"\nr2 = create_gamer_tag("Y", 0, 0)\nassert r2 == {"tag": "Y", "kdr": 0, "rank": "Noob"}, f"Got {r2}"\nprint("TEST_PASSED: Gamer profiles synced!")',
            'def create_gamer_tag(username, kills, deaths):\n    kdr = kills/deaths if deaths > 0 else 0\n    rank = "Pro" if kdr > 1 else "Noob"\n    return {"tag": username, "kdr": kdr, "rank": rank}',
            'Handle division by zero for kdr!',
            150, 'Medium', 2
        ),
        (
            'amateur', 'For Loops',
            '<h2>The Grind</h2><p>Need to do something to every item in a list? A <code>for</code> loop is your best friend.</p><pre><code>for item in inventory:\n    sell(item)</code></pre><p>Use <code>range(n)</code> to repeat exactly n times!</p>',
            'Scan for vowels in the transmission.',
            'Write `count_vowels(text)` that returns the number of vowels (a, e, i, o, u) in the string, case-insensitive.',
            'def count_vowels(text):\n    pass',
            'assert count_vowels("Hello") == 2, f"Expected 2, got {count_vowels(\'Hello\')}"\nassert count_vowels("CYBER") == 1, f"Expected 1, got {count_vowels(\'CYBER\')}"\nassert count_vowels("aeiou") == 5, f"Expected 5, got {count_vowels(\'aeiou\')}"\nprint("TEST_PASSED: Vowel scanner operational!")',
            'def count_vowels(text):\n    return sum(1 for c in text.lower() if c in "aeiou")',
            'Loop over the text, convert to lower, check if in "aeiou".',
            150, 'Medium', 3
        ),
        (
            'amateur', 'While Loops',
            "<h2>Loop Until Done</h2><p>A <code>while</code> loop keeps running as long as a condition is True. Use it when you don't know exactly how many times you need to loop.</p><h4>Warning!</h4><p>Don't forget to change the condition inside the loop, or it runs forever (Infinite Loop)!</p>",
            'Initiate the countdown sequence.',
            'Write `countdown(n)` returning a list of numbers from n down to 1. If n <= 0, return an empty list.',
            'def countdown(n):\n    pass',
            'assert countdown(3) == [3, 2, 1], f"Expected [3,2,1], got {countdown(3)}"\nassert countdown(0) == [], f"Expected [], got {countdown(0)}"\nassert countdown(1) == [1], f"Expected [1], got {countdown(1)}"\nprint("TEST_PASSED: Countdown sequence complete!")',
            'def countdown(n):\n    res = []\n    while n > 0:\n        res.append(n)\n        n -= 1\n    return res',
            'Append to a list and decrement n',
            150, 'Medium', 4
        ),
        (
            'amateur', 'String Methods',
            '<h2>Text Manipulation</h2><p>Strings have secret weapons! <code>split()</code> chops a string into a list of words. <code>join()</code> glues a list of strings together. <code>replace()</code> swaps substrings.</p>',
            'Decode the encrypted comms!',
            'Write `decode_cipher(text)` that reverses EACH WORD in the sentence but keeps word order. (e.g. "hello world" -> "olleh dlrow")',
            'def decode_cipher(text):\n    pass',
            'assert decode_cipher("hello world") == "olleh dlrow", f"Got \'{decode_cipher(\'hello world\')}\'"\nassert decode_cipher("cyber arcade") == "rebyc edacra", f"Got \'{decode_cipher(\'cyber arcade\')}\'"\nprint("TEST_PASSED: Cipher decoded!")',
            'def decode_cipher(text):\n    return " ".join([word[::-1] for word in text.split()])',
            'Split into words, reverse each word, join with spaces.',
            150, 'Medium', 5
        ),
        (
            'advanced', 'Functions Deep Dive',
            '<h2>The Factory</h2><p>Functions can take default arguments, keyword arguments, and even an arbitrary number of arguments using <code>*args</code>. This packs them into a tuple.</p><pre><code>def heal(*targets):</code></pre>',
            'Calculate the party stats.',
            'Write `power_stats(*values)` that returns a dict with keys "min", "max", "avg". If no values provided, return {"min":0, "max":0, "avg":0}.',
            'def power_stats(*values):\n    pass',
            'assert power_stats(10, 20, 30) == {"min": 10, "max": 30, "avg": 20.0}, f"Got {power_stats(10, 20, 30)}"\nassert power_stats() == {"min": 0, "max": 0, "avg": 0}, f"Got {power_stats()}"\nprint("TEST_PASSED: Power stats computed!")',
            'def power_stats(*values):\n    if not values: return {"min":0, "max":0, "avg":0}\n    return {"min": min(values), "max": max(values), "avg": sum(values)/len(values)}',
            'Use built-in min, max, sum',
            250, 'Hard', 1
        ),
        (
            'advanced', 'List Comprehensions',
            '<h2>One-Line Magic</h2><p>Why write 4 lines for a for-loop when you can do it in 1? List comprehensions let you map and filter in a beautiful syntax.</p><pre><code>[x*2 for x in nums if x > 0]</code></pre>',
            'Filter the sensor telemetry.',
            'Write `filter_telemetry(readings)` that returns a list of the squares of all strictly positive even numbers in `readings`.',
            'def filter_telemetry(readings):\n    pass',
            'assert filter_telemetry([1, 2, -2, 4]) == [4, 16], f"Got {filter_telemetry([1, 2, -2, 4])}"\nassert filter_telemetry([3, 5]) == [], f"Got {filter_telemetry([3, 5])}"\nassert filter_telemetry([6]) == [36], f"Got {filter_telemetry([6])}"\nprint("TEST_PASSED: Telemetry filtered!")',
            'def filter_telemetry(readings):\n    return [x**2 for x in readings if x > 0 and x % 2 == 0]',
            'if x > 0 and x % 2 == 0',
            250, 'Hard', 2
        ),
        (
            'advanced', 'Exception Handling',
            "<h2>Crash Protection</h2><p>Errors happen. A network drops, or a player inputs text instead of numbers. Use <code>try/except</code> to handle these gracefully so your game doesn't crash.</p>",
            'Write a safe division module.',
            'Write `safe_divide(a_str, b_str)`. Convert both to float and divide a/b. If ZeroDivisionError, return "Infinity". If ValueError (can\'t convert to float), return "Error".',
            'def safe_divide(a_str, b_str):\n    pass',
            'assert safe_divide("10", "2") == 5.0, f"Got {safe_divide(\'10\', \'2\')}"\nassert safe_divide("10", "0") == "Infinity", f"Got {safe_divide(\'10\', \'0\')}"\nassert safe_divide("ten", "2") == "Error", f"Got {safe_divide(\'ten\', \'2\')}"\nprint("TEST_PASSED: Exception shield active!")',
            'def safe_divide(a, b):\n    try:\n        return float(a) / float(b)\n    except ZeroDivisionError:\n        return "Infinity"\n    except ValueError:\n        return "Error"',
            'Use try... except ZeroDivisionError... except ValueError.',
            250, 'Hard', 3
        ),
        (
            'advanced', 'OOP Basics',
            '<h2>Blueprints</h2><p>Object-Oriented Programming (OOP) groups data and behavior together into a Class. <code>__init__</code> is the constructor where you set up the starting state. <code>self</code> refers to the specific instance of the object.</p>',
            'Build the CyberMech unit.',
            'Write class `CyberMech` with __init__(self, name, hp, attack_power). Methods: `take_damage(amount)` reduces hp. `is_alive()` returns True if hp > 0. `attack(other_mech)` calls take_damage on the other mech.',
            'class CyberMech:\n    pass',
            'm1 = CyberMech("A", 100, 20)\nm2 = CyberMech("B", 50, 10)\nm1.attack(m2)\nassert m2.hp == 30, f"Expected hp=30, got {m2.hp}"\nassert m2.is_alive() == True, "m2 should be alive"\nm1.attack(m2)\nm1.attack(m2)\nassert m2.is_alive() == False, "m2 should be dead after 3 attacks"\nprint("TEST_PASSED: CyberMech operational!")',
            'class CyberMech:\n    def __init__(self, name, hp, atk):\n        self.name = name\n        self.hp = hp\n        self.atk = atk\n    def take_damage(self, dmg):\n        self.hp -= dmg\n    def is_alive(self):\n        return self.hp > 0\n    def attack(self, other):\n        other.take_damage(self.atk)',
            'Define __init__ and all 3 methods correctly.',
            250, 'Hard', 4
        ),
        (
            'advanced', 'File-like Operations & Tuples',
            "<h2>Immutable Records</h2><p>Tuples are like lists, but you can't change them once they are created (immutable). They are great for packing fixed data. <code>enumerate()</code> is a super useful function that loops over an iterable and gives you both the index and the item as a tuple!</p>",
            'Index the digital inventory.',
            'Write `index_inventory(items)` that returns a list of tuples, where each tuple is `(index, item)`. E.g. ["sword"] -> [(0, "sword")]',
            'def index_inventory(items):\n    pass',
            'assert index_inventory(["a", "b"]) == [(0, "a"), (1, "b")], f"Got {index_inventory([\'a\', \'b\'])}"\nassert index_inventory([]) == [], f"Got {index_inventory([])}"\nprint("TEST_PASSED: Inventory indexed!")',
            'def index_inventory(items):\n    return list(enumerate(items))',
            'You can just use list(enumerate(items))',
            250, 'Hard', 5
        ),
        (
            'professional', 'Generators',
            "<h2>Lazy Evaluation</h2><p>A generator uses <code>yield</code> instead of <code>return</code>. It pauses execution and sends a value back, remembering its state. It's incredibly memory efficient because it doesn't build the whole sequence in memory at once.</p>",
            'Create an infinite energy stream (bounded by max).',
            'Write a generator `energy_stream(start, step, max)` that yields values starting at `start`, increasing by `step`, but STOPS strictly before `max`.',
            'def energy_stream(start, step, max):\n    pass',
            'import types\ngen = energy_stream(0, 2, 5)\nassert isinstance(gen, types.GeneratorType), "Must be a generator (use yield)!"\nassert list(energy_stream(0, 2, 5)) == [0, 2, 4], f"Got {list(energy_stream(0, 2, 5))}"\nassert list(energy_stream(10, 5, 10)) == [], f"Got {list(energy_stream(10, 5, 10))}"\nprint("TEST_PASSED: Generator pipeline online!")',
            'def energy_stream(start, step, maximum):\n    while start < maximum:\n        yield start\n        start += step',
            'Use a while loop and yield.',
            400, 'Expert', 1
        ),
        (
            'professional', 'Decorators',
            '<h2>The Wrapper Pattern</h2><p>Decorators take a function, add some functionality, and return it. They are widely used in frameworks (like @app.route in Flask). They use nested functions (closures).</p>',
            'Build an audit log decorator.',
            'Write a decorator `audit_log` that wraps a function. The wrapped function should return a tuple: `(original_result, original_function_name)`.',
            'def audit_log(func):\n    pass',
            '@audit_log\ndef add(a, b): return a + b\nresult = add(2, 3)\nassert result == (5, "add"), f"Expected (5, \'add\'), got {result}"\nprint("TEST_PASSED: Decorator telemetry hooked!")',
            'def audit_log(func):\n    def wrapper(*args, **kwargs):\n        return (func(*args, **kwargs), func.__name__)\n    return wrapper',
            'Define a wrapper that returns (func(*args, **kwargs), func.__name__).',
            400, 'Expert', 2
        ),
        (
            'professional', 'Lambda & Map/Filter',
            '<h2>Functional Programming</h2><p><code>lambda</code> lets you write tiny anonymous functions inline. Combine them with <code>map()</code> (apply to all) and <code>filter()</code> (keep if true) for functional pipelines.</p>',
            'Process the big data pipeline.',
            'Write `process_data(numbers)`. Use `filter` and a lambda to keep only even numbers, then use `map` and a lambda to square them. Return the result as a list.',
            'def process_data(numbers):\n    pass',
            'assert process_data([1, 2, 3, 4]) == [4, 16], f"Got {process_data([1, 2, 3, 4])}"\nassert process_data([1, 3, 5]) == [], f"Got {process_data([1, 3, 5])}"\nprint("TEST_PASSED: Lambda pipeline deployed!")',
            'def process_data(numbers):\n    return list(map(lambda x: x**2, filter(lambda x: x % 2 == 0, numbers)))',
            'list(map(..., filter(...)))',
            400, 'Expert', 3
        ),
        (
            'professional', 'Algorithms (Two Sum)',
            '<h2>Algorithmic Complexity</h2><p>Finding pairs in a list using nested loops is O(n^2). By using a Hash Map (Dictionary in Python), you can do it in O(n) time! Store the complement (target - current) as you iterate.</p>',
            'Find the matching encryption keys.',
            'Write `find_key_pair(addresses, target)` that returns a list of the two INDICES `[i, j]` whose values add up to target. You can assume there is exactly one solution.',
            'def find_key_pair(addresses, target):\n    pass',
            'assert find_key_pair([2, 7, 11, 15], 9) == [0, 1], f"Got {find_key_pair([2, 7, 11, 15], 9)}"\nassert find_key_pair([3, 2, 4], 6) == [1, 2], f"Got {find_key_pair([3, 2, 4], 6)}"\nprint("TEST_PASSED: Two-sum cracked in O(n)!")',
            'def find_key_pair(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i',
            'Keep a dictionary mapping value -> index.',
            400, 'Expert', 4
        ),
        (
            'professional', 'Recursion',
            '<h2>Inception</h2><p>Recursion is a function calling itself. You MUST have a base case (when to stop) and a recursive step (breaking the problem down).</p>',
            'Flatten the multi-dimensional array.',
            'Write `flatten(nested_list)` that recursively flattens a list of lists. E.g. [1, [2, [3, 4]]] -> [1, 2, 3, 4]. (Assume elements are either ints or lists).',
            'def flatten(nested_list):\n    pass',
            'assert flatten([1, [2, [3, 4]]]) == [1, 2, 3, 4], f"Got {flatten([1, [2, [3, 4]]])}"\nassert flatten([]) == [], f"Got {flatten([])}"\nassert flatten([[1], [2], [3]]) == [1, 2, 3], f"Got {flatten([[1], [2], [3]])}"\nprint("TEST_PASSED: Nested lists flattened!")',
            'def flatten(nested_list):\n    res = []\n    for item in nested_list:\n        if isinstance(item, list):\n            res.extend(flatten(item))\n        else:\n            res.append(item)\n    return res',
            'Check isinstance(item, list) and recursively extend.',
            400, 'Expert', 5
        ),
    ]

    quizzes = [
        # Beginner
        ('beginner', 'What does the print() function do?', 'print("Hello")', 'Saves to database', 'Displays on screen', 'Creates a file', 'Deletes a variable', 'Displays on screen', 'print() outputs text to the console.', 25),
        ('beginner', 'Which operator is used for exponentiation?', '2 ** 3', '^', '**', '*', '//', '**', '** is the exponent operator in Python.', 25),
        ('beginner', 'What is the output of 5 // 2?', 'print(5 // 2)', '2.5', '2', '3', '1', '2', '// performs integer division.', 25),
        ('beginner', 'Which boolean operator requires both sides to be True?', 'True _ True', 'or', 'not', 'and', 'xor', 'and', 'The "and" operator requires both operands to be True.', 25),
        ('beginner', 'How do you check string length?', 's = "abc"', 'size(s)', 'length(s)', 'len(s)', 's.len()', 'len(s)', 'len() is a built-in Python function.', 25),
        
        # Amateur
        ('amateur', 'How do you add an item to the end of a list?', 'lst = [1,2]', 'lst.add(3)', 'lst.insert(3)', 'lst.append(3)', 'lst.push(3)', 'lst.append(3)', 'append() adds to the end of a list.', 25),
        ('amateur', 'Which syntax creates a dictionary?', '', '[]', '{}', '()', '<>', '{}', 'Curly braces define dictionaries.', 25),
        ('amateur', 'What is the output of range(3)?', 'for i in range(3): print(i)', '1,2,3', '0,1,2', '0,1,2,3', '1,2', '0,1,2', 'range(n) starts at 0 and goes up to n-1.', 25),
        ('amateur', 'How do you split a string into a list?', 's = "a b c"', 's.cut()', 's.split()', 's.list()', 's.divide()', 's.split()', 'split() breaks a string by spaces by default.', 25),
        ('amateur', 'Which keyword is used to exit a loop early?', 'while True: ...', 'stop', 'exit', 'break', 'return', 'break', 'break terminates the nearest enclosing loop.', 25),
        
        # Advanced
        ('advanced', 'What does *args do in a function definition?', 'def f(*args):', 'Accepts a dictionary of arguments', 'Accepts an arbitrary number of positional arguments', 'Requires arguments to be pointers', 'Multiplies the arguments', 'Accepts an arbitrary number of positional arguments', '*args packs positional arguments into a tuple.', 25),
        ('advanced', 'Which comprehension syntax is valid?', '', '{x for x in list}', '(x for x in list)', '[x for x in list]', 'All of the above', 'All of the above', 'List, set, and generator comprehensions are all valid.', 25),
        ('advanced', 'What block always executes in try/except?', 'try: ...', 'catch', 'finally', 'else', 'then', 'finally', 'finally blocks run regardless of whether an exception occurred.', 25),
        ('advanced', 'What refers to the instance in a class method?', 'class A:', 'this', 'self', 'me', 'instance', 'self', 'self is conventionally used as the first parameter.', 25),
        ('advanced', 'Are tuples mutable?', 't = (1, 2)', 'Yes', 'No', 'Only if containing lists', 'Sometimes', 'No', 'Tuples are immutable data structures.', 25),
        
        # Professional
        ('professional', 'What keyword makes a function a generator?', 'def g():', 'generate', 'yield', 'emit', 'produce', 'yield', 'yield suspends execution and returns a value.', 25),
        ('professional', 'What does functools.wraps do?', '@wraps(f)', 'Speeds up execution', 'Hides the source code', 'Preserves metadata of the wrapped function', 'Prevents exceptions', 'Preserves metadata of the wrapped function', 'It keeps the name and docstring of the original function.', 25),
        ('professional', 'What does map() return in Python 3?', 'map(f, lst)', 'A list', 'An iterator', 'A tuple', 'A dictionary', 'An iterator', 'map() returns a map object which is an iterator.', 25),
        ('professional', 'What is the time complexity of dict lookups?', 'd["key"]', 'O(1) average', 'O(n) average', 'O(log n) average', 'O(n^2) average', 'O(1) average', 'Hash maps (dicts) have O(1) average case lookup time.', 25),
        ('professional', 'Which error occurs with infinite recursion?', 'def f(): f()', 'InfiniteLoopError', 'MemoryError', 'RecursionError', 'StackOverflow', 'RecursionError', 'Python raises RecursionError when max depth is reached.', 25)
    ]
    cursor.executemany('''
    INSERT INTO quizzes (category_slug, question, code_snippet, option_a, option_b, option_c, option_d, correct_option, explanation, xp_reward)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', quizzes)
    
    conn.commit()
    print("Database seeded successfully!")

if __name__ == '__main__':
    init_db()
