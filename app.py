import os

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db_connection, init_db
from code_runner import run_user_code_with_tests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pukki_cyber_arcade_super_secret_key_2026_!#')

def calculate_level(xp):
    """
    Level 1: 0 - 99 XP
    Level 2: 100 - 249 XP
    Level 3: 250 - 449 XP
    Level 4: 450 - 699 XP
    Level 5: 700 - 999 XP
    Level 6+: Every 350 XP
    """
    if xp < 100:
        return 1, xp, 100
    elif xp < 250:
        return 2, xp - 100, 150
    elif xp < 450:
        return 3, xp - 250, 200
    elif xp < 700:
        return 4, xp - 450, 250
    elif xp < 1000:
        return 5, xp - 700, 300
    else:
        lvl = 5 + (xp - 1000) // 350
        curr = (xp - 1000) % 350
        return lvl, curr, 350

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

def award_badges_check(user_id, conn):
    """
    Checks and awards achievement badges if thresholds are met.
    """
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return []

    newly_awarded = []
    
    # 1. First Blood: completed at least 1 quest
    completed_count = conn.execute(
        'SELECT COUNT(*) as count FROM user_progress WHERE user_id = ? AND completed = 1',
        (user_id,)
    ).fetchone()['count']

    if completed_count >= 1:
        badge = conn.execute('SELECT * FROM badges WHERE slug = "first_blood"').fetchone()
        if badge:
            existing = conn.execute(
                'SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?',
                (user_id, badge['id'])
            ).fetchone()
            if not existing:
                conn.execute(
                    'INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)',
                    (user_id, badge['id'])
                )
                newly_awarded.append(badge['name'])

    # 2. Category master badges
    category_slugs = {
        'beginner': 'rookie_slayer',
        'amateur': 'adventurer_elite',
        'advanced': 'sorcerer_archmage',
        'professional': 'grandmaster_legend'
    }

    for cat, badge_slug in category_slugs.items():
        total_in_cat = conn.execute(
            'SELECT COUNT(*) as count FROM quests WHERE category_slug = ?',
            (cat,)
        ).fetchone()['count']

        completed_in_cat = conn.execute('''
            SELECT COUNT(*) as count FROM user_progress up
            JOIN quests q ON up.quest_id = q.id
            WHERE up.user_id = ? AND up.completed = 1 AND q.category_slug = ?
        ''', (user_id, cat)).fetchone()['count']

        if total_in_cat > 0 and completed_in_cat >= total_in_cat:
            badge = conn.execute('SELECT * FROM badges WHERE slug = ?', (badge_slug,)).fetchone()
            if badge:
                existing = conn.execute(
                    'SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?',
                    (user_id, badge['id'])
                ).fetchone()
                if not existing:
                    conn.execute(
                        'INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)',
                        (user_id, badge['id'])
                    )
                    newly_awarded.append(badge['name'])

    # 3. 500+ XP Speedrunner Badge
    if user['xp'] >= 500:
        badge = conn.execute('SELECT * FROM badges WHERE slug = "speed_runner"').fetchone()
        if badge:
            existing = conn.execute(
                'SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?',
                (user_id, badge['id'])
            ).fetchone()
            if not existing:
                conn.execute(
                    'INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)',
                    (user_id, badge['id'])
                )
                newly_awarded.append(badge['name'])

    conn.commit()
    return newly_awarded

@app.route('/')
def index():
    user = get_current_user()
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY order_idx ASC').fetchall()
    total_quests = conn.execute('SELECT COUNT(*) as count FROM quests').fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    conn.close()
    return render_template('index.html', user=user, categories=categories, total_quests=total_quests, total_users=total_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        avatar = request.form.get('avatar', 'cyber_fox')

        if not username or not email or not password:
            flash('All fields are required to join the squad!', 'error')
            return render_template('auth/register.html')

        conn = get_db_connection()
        existing = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()

        if existing:
            conn.close()
            flash('Username or email already claimed in the cyber registry.', 'error')
            return render_template('auth/register.html')

        hashed = generate_password_hash(password, method='pbkdf2:sha256')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, avatar, xp, level, streak, title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, hashed, avatar, 0, 1, 1, 'Script Rookie'))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        session['user_id'] = user_id
        session['username'] = username
        flash('Welcome to PyQuest! Your coding quest begins now.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username_or_email = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE username = ? OR email = ?
        ''', (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}! Let's hack some code.", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid handle or password. Access denied.', 'error')

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out safely. See you in the next run!', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash('Please login to view your command center.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    # User level stats
    lvl, curr_xp, next_lvl_xp = calculate_level(user['xp'])
    progress_pct = min(100, int((curr_xp / next_lvl_xp) * 100))

    # Categories with user completion stats
    categories = conn.execute('SELECT * FROM categories ORDER BY order_idx ASC').fetchall()
    cat_stats = []
    for cat in categories:
        total = conn.execute('SELECT COUNT(*) as count FROM quests WHERE category_slug = ?', (cat['slug'],)).fetchone()['count']
        completed = conn.execute('''
            SELECT COUNT(*) as count FROM user_progress up
            JOIN quests q ON up.quest_id = q.id
            WHERE up.user_id = ? AND up.completed = 1 AND q.category_slug = ?
        ''', (user['id'], cat['slug'])).fetchone()['count']
        pct = int((completed / total * 100)) if total > 0 else 0
        cat_stats.append({
            'cat': cat,
            'total': total,
            'completed': completed,
            'pct': pct
        })

    # Unlocked badges
    badges = conn.execute('''
        SELECT b.*, ub.earned_at FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
        ORDER BY ub.earned_at DESC
    ''', (user['id'],)).fetchall()

    # Next recommended quest (first uncompleted quest)
    next_quest = conn.execute('''
        SELECT q.*, c.title as cat_title, c.accent_color FROM quests q
        JOIN categories c ON q.category_slug = c.slug
        LEFT JOIN user_progress up ON q.id = up.quest_id AND up.user_id = ?
        WHERE up.completed IS NULL OR up.completed = 0
        ORDER BY c.order_idx ASC, q.order_idx ASC
        LIMIT 1
    ''', (user['id'],)).fetchone()

    conn.close()

    return render_template(
        'dashboard.html',
        user=user,
        level=lvl,
        curr_xp=curr_xp,
        next_lvl_xp=next_lvl_xp,
        progress_pct=progress_pct,
        cat_stats=cat_stats,
        badges=badges,
        next_quest=next_quest
    )

@app.route('/categories')
def categories_view():
    user = get_current_user()
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY order_idx ASC').fetchall()
    
    cat_data = []
    for c in categories:
        total = conn.execute('SELECT COUNT(*) as count FROM quests WHERE category_slug = ?', (c['slug'],)).fetchone()['count']
        completed = 0
        if user:
            completed = conn.execute('''
                SELECT COUNT(*) as count FROM user_progress up
                JOIN quests q ON up.quest_id = q.id
                WHERE up.user_id = ? AND up.completed = 1 AND q.category_slug = ?
            ''', (user['id'], c['slug'])).fetchone()['count']
        cat_data.append({
            'info': c,
            'total': total,
            'completed': completed,
            'pct': int((completed / total * 100)) if total > 0 else 0
        })
    conn.close()
    return render_template('categories.html', user=user, categories=cat_data)

@app.route('/category/<slug>')
def category_detail(slug):
    user = get_current_user()
    conn = get_db_connection()
    category = conn.execute('SELECT * FROM categories WHERE slug = ?', (slug,)).fetchone()
    if not category:
        conn.close()
        flash('Cyber tier category not found.', 'error')
        return redirect(url_for('categories_view'))

    quests = conn.execute('SELECT * FROM quests WHERE category_slug = ? ORDER BY order_idx ASC', (slug,)).fetchall()
    
    quest_list = []
    for q in quests:
        completed = False
        if user:
            prog = conn.execute('SELECT completed FROM user_progress WHERE user_id = ? AND quest_id = ?', (user['id'], q['id'])).fetchone()
            if prog and prog['completed']:
                completed = True
        quest_list.append({
            'quest': q,
            'completed': completed
        })

    conn.close()
    return render_template('category_detail.html', user=user, category=category, quests=quest_list)

@app.route('/learn/<int:quest_id>')
def learn_arena(quest_id):
    user = get_current_user()
    if not user:
        flash('Please login to access the intel network.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    quest = conn.execute('''
        SELECT q.*, c.title as cat_title, c.accent_color, c.slug as cat_slug 
        FROM quests q
        JOIN categories c ON q.category_slug = c.slug
        WHERE q.id = ?
    ''', (quest_id,)).fetchone()
    conn.close()

    if not quest:
        flash('Quest intel lost in hyperspace.', 'error')
        return redirect(url_for('categories_view'))

    return render_template('learn.html', user=user, quest=quest)

@app.route('/quest/<int:quest_id>')
def quest_arena(quest_id):
    user = get_current_user()
    if not user:
        flash('Please login to enter the Code Arena.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    quest = conn.execute('''
        SELECT q.*, c.title as cat_title, c.accent_color, c.slug as cat_slug 
        FROM quests q
        JOIN categories c ON q.category_slug = c.slug
        WHERE q.id = ?
    ''', (quest_id,)).fetchone()

    if not quest:
        conn.close()
        flash('Quest signal lost in hyperspace.', 'error')
        return redirect(url_for('categories_view'))

    # Check progress or saved draft
    progress = conn.execute('SELECT * FROM user_progress WHERE user_id = ? AND quest_id = ?', (user['id'], quest_id)).fetchone()
    saved_code = progress['submitted_code'] if (progress and progress['submitted_code']) else quest['starter_code']
    is_completed = bool(progress['completed']) if progress else False

    # Get adjacent quests for navigation
    prev_quest = conn.execute('''
        SELECT id FROM quests 
        WHERE category_slug = ? AND order_idx < ?
        ORDER BY order_idx DESC LIMIT 1
    ''', (quest['category_slug'], quest['order_idx'])).fetchone()

    next_quest = conn.execute('''
        SELECT id FROM quests 
        WHERE category_slug = ? AND order_idx > ?
        ORDER BY order_idx ASC LIMIT 1
    ''', (quest['category_slug'], quest['order_idx'])).fetchone()

    conn.close()

    return render_template(
        'quest.html',
        user=user,
        quest=quest,
        code=saved_code,
        is_completed=is_completed,
        prev_quest=prev_quest,
        next_quest=next_quest
    )

@app.route('/quiz')
def quiz_arena():
    user = get_current_user()
    conn = get_db_connection()
    quizzes = conn.execute('SELECT * FROM quizzes ORDER BY RANDOM() LIMIT 5').fetchall()
    conn.close()
    return render_template('quiz.html', user=user, quizzes=quizzes)

@app.route('/leaderboard')
def leaderboard():
    user = get_current_user()
    conn = get_db_connection()
    top_users = conn.execute('''
        SELECT u.id, u.username, u.avatar, u.xp, u.level, u.streak, u.title,
               COUNT(DISTINCT up.quest_id) as quests_done,
               COUNT(DISTINCT ub.badge_id) as badges_count
        FROM users u
        LEFT JOIN user_progress up ON u.id = up.user_id AND up.completed = 1
        LEFT JOIN user_badges ub ON u.id = ub.user_id
        GROUP BY u.id
        ORDER BY u.xp DESC, quests_done DESC
        LIMIT 25
    ''').fetchall()
    conn.close()
    return render_template('leaderboard.html', user=user, top_users=top_users)

@app.route('/profile')
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = get_db_connection()
    lvl, curr_xp, next_lvl_xp = calculate_level(user['xp'])
    badges = conn.execute('''
        SELECT b.*, ub.earned_at FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
        ORDER BY ub.earned_at DESC
    ''', (user['id'],)).fetchall()

    completed_quests = conn.execute('''
        SELECT q.title, q.difficulty, q.xp_reward, c.accent_color, up.completed_at
        FROM user_progress up
        JOIN quests q ON up.quest_id = q.id
        JOIN categories c ON q.category_slug = c.slug
        WHERE up.user_id = ? AND up.completed = 1
        ORDER BY up.completed_at DESC
    ''', (user['id'],)).fetchall()
    conn.close()

    return render_template(
        'profile.html',
        user=user,
        level=lvl,
        curr_xp=curr_xp,
        next_lvl_xp=next_lvl_xp,
        badges=badges,
        completed_quests=completed_quests
    )

@app.route('/api/run-code/<int:quest_id>', methods=['POST'])
def api_run_code(quest_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required. Please log in.'}), 401

    user_id = session['user_id']
    data = request.get_json() or {}
    user_code = data.get('code', '')

    if not user_code.strip():
        return jsonify({'success': False, 'message': 'Code snippet cannot be blank!'})

    conn = get_db_connection()
    quest = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
    if not quest:
        conn.close()
        return jsonify({'error': 'Quest not found'}), 404

    # Run user code against test harness in subprocess
    result = run_user_code_with_tests(user_code, quest['test_code'], timeout_seconds=4.0)

    xp_gained = 0
    new_level = None
    new_badges = []
    already_completed = False

    # Check if quest was already completed
    progress = conn.execute(
        'SELECT * FROM user_progress WHERE user_id = ? AND quest_id = ?',
        (user_id, quest_id)
    ).fetchone()

    if progress and progress['completed']:
        already_completed = True

    if result['success']:
        # Update progress
        conn.execute('''
            INSERT INTO user_progress (user_id, quest_id, completed, submitted_code, completed_at)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, quest_id) DO UPDATE SET
                completed = 1,
                submitted_code = excluded.submitted_code,
                completed_at = CURRENT_TIMESTAMP
        ''', (user_id, quest_id, user_code))

        if not already_completed:
            xp_gained = quest['xp_reward']
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            old_level, _, _ = calculate_level(user['xp'])
            new_xp = user['xp'] + xp_gained
            calc_lvl, _, _ = calculate_level(new_xp)

            conn.execute('UPDATE users SET xp = ?, level = ? WHERE id = ?', (new_xp, calc_lvl, user_id))
            conn.commit()

            if calc_lvl > old_level:
                new_level = calc_lvl

            # Check and award badges
            new_badges = award_badges_check(user_id, conn)
    else:
        # Save draft even if tests failed
        conn.execute('''
            INSERT INTO user_progress (user_id, quest_id, completed, submitted_code)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(user_id, quest_id) DO UPDATE SET
                submitted_code = excluded.submitted_code
        ''', (user_id, quest_id, user_code))
        conn.commit()

    conn.close()

    return jsonify({
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'message': result['message'],
        'xp_gained': xp_gained,
        'already_completed': already_completed,
        'new_level': new_level,
        'new_badges': new_badges
    })

@app.route('/api/submit-quiz', methods=['POST'])
def api_submit_quiz():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401

    data = request.get_json() or {}
    quiz_id = data.get('quiz_id')
    selected_option = data.get('selected_option', '').upper()

    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if not quiz:
        conn.close()
        return jsonify({'error': 'Question not found'}), 404

    is_correct = (selected_option == quiz['correct_option'])
    xp_gained = 0
    new_badges = []

    if is_correct:
        xp_gained = quiz['xp_reward']
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        new_xp = user['xp'] + xp_gained
        calc_lvl, _, _ = calculate_level(new_xp)
        conn.execute('UPDATE users SET xp = ?, level = ? WHERE id = ?', (new_xp, calc_lvl, user['id']))
        conn.commit()
        new_badges = award_badges_check(user['id'], conn)

    conn.close()

    return jsonify({
        'correct': is_correct,
        'correct_option': quiz['correct_option'],
        'explanation': quiz['explanation'],
        'xp_gained': xp_gained,
        'new_badges': new_badges
    })

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    print(f"🎮 PyQuest booting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
