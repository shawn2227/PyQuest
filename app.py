import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'compuquest_super_secret_key_2026_!#')

def calculate_level(xp):
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
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return []
    newly_awarded = []
    
    completed_count = conn.execute('SELECT COUNT(*) as count FROM user_progress WHERE user_id = ? AND completed = 1', (user_id,)).fetchone()['count']
    if completed_count >= 1:
        badge = conn.execute('SELECT * FROM badges WHERE slug = "first_step"').fetchone()
        if badge:
            if not conn.execute('SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?', (user_id, badge['id'])).fetchone():
                conn.execute('INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)', (user_id, badge['id']))
                newly_awarded.append(badge['name'])

    category_slugs = {
        'hardware_software': 'hardware_hero',
        'internet': 'web_surfer',
        'digital_skills': 'data_master'
    }

    for cat, badge_slug in category_slugs.items():
        total_in_cat = conn.execute('SELECT COUNT(*) as count FROM quests WHERE category_slug = ?', (cat,)).fetchone()['count']
        completed_in_cat = conn.execute('''
            SELECT COUNT(*) as count FROM user_progress up
            JOIN quests q ON up.quest_id = q.id
            WHERE up.user_id = ? AND up.completed = 1 AND q.category_slug = ?
        ''', (user_id, cat)).fetchone()['count']
        if total_in_cat > 0 and completed_in_cat >= total_in_cat:
            badge = conn.execute('SELECT * FROM badges WHERE slug = ?', (badge_slug,)).fetchone()
            if badge:
                if not conn.execute('SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?', (user_id, badge['id'])).fetchone():
                    conn.execute('INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)', (user_id, badge['id']))
                    newly_awarded.append(badge['name'])

    if user['xp'] >= 500:
        badge = conn.execute('SELECT * FROM badges WHERE slug = "super_learner"').fetchone()
        if badge:
            if not conn.execute('SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?', (user_id, badge['id'])).fetchone():
                conn.execute('INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)', (user_id, badge['id']))
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
        avatar = request.form.get('avatar', 'happy_bot')

        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('auth/register.html')

        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing:
            conn.close()
            flash('Username or email already in use.', 'error')
            return render_template('auth/register.html')

        hashed = generate_password_hash(password, method='pbkdf2:sha256')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, avatar, xp, level, streak, title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, hashed, avatar, 0, 1, 1, 'Explorer'))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        session['user_id'] = user_id
        session['username'] = username
        flash('Welcome to CompuQuest! Your adventure begins now.', 'success')
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
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}! Let's learn.", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully. See you next time!', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash('Please login to view your dashboard.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    lvl, curr_xp, next_lvl_xp = calculate_level(user['xp'])
    progress_pct = min(100, int((curr_xp / next_lvl_xp) * 100))

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
        cat_stats.append({'cat': cat, 'total': total, 'completed': completed, 'pct': pct})

    badges = conn.execute('''
        SELECT b.*, ub.earned_at FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
        ORDER BY ub.earned_at DESC
    ''', (user['id'],)).fetchall()

    next_quest = conn.execute('''
        SELECT q.*, c.title as cat_title, c.accent_color FROM quests q
        JOIN categories c ON q.category_slug = c.slug
        LEFT JOIN user_progress up ON q.id = up.quest_id AND up.user_id = ?
        WHERE up.completed IS NULL OR up.completed = 0
        ORDER BY c.order_idx ASC, q.order_idx ASC
        LIMIT 1
    ''', (user['id'],)).fetchone()
    conn.close()

    return render_template('dashboard.html', user=user, level=lvl, curr_xp=curr_xp, next_lvl_xp=next_lvl_xp, progress_pct=progress_pct, cat_stats=cat_stats, badges=badges, next_quest=next_quest)

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
        cat_data.append({'info': c, 'total': total, 'completed': completed, 'pct': int((completed / total * 100)) if total > 0 else 0})
    conn.close()
    return render_template('categories.html', user=user, categories=cat_data)

@app.route('/category/<slug>')
def category_detail(slug):
    user = get_current_user()
    conn = get_db_connection()
    category = conn.execute('SELECT * FROM categories WHERE slug = ?', (slug,)).fetchone()
    if not category:
        conn.close()
        flash('World not found.', 'error')
        return redirect(url_for('categories_view'))

    quests = conn.execute('SELECT * FROM quests WHERE category_slug = ? ORDER BY order_idx ASC', (slug,)).fetchall()
    quest_list = []
    for q in quests:
        completed = False
        if user:
            prog = conn.execute('SELECT completed FROM user_progress WHERE user_id = ? AND quest_id = ?', (user['id'], q['id'])).fetchone()
            if prog and prog['completed']:
                completed = True
        quest_list.append({'quest': q, 'completed': completed})
    conn.close()
    return render_template('category_detail.html', user=user, category=category, quests=quest_list)

@app.route('/learn/<int:quest_id>')
def learn_arena(quest_id):
    user = get_current_user()
    if not user:
        flash('Please login to access the lessons.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    quest_row = conn.execute('''
        SELECT q.*, c.title as cat_title, c.accent_color, c.slug as cat_slug 
        FROM quests q
        JOIN categories c ON q.category_slug = c.slug
        WHERE q.id = ?
    ''', (quest_id,)).fetchone()
    
    if not quest_row:
        conn.close()
        flash('Lesson not found.', 'error')
        return redirect(url_for('categories_view'))

    # Convert row to dict to parse JSON
    quest = dict(quest_row)
    quest['quiz_options_list'] = json.loads(quest['quiz_options']) if quest.get('quiz_options') else []
    
    # Check if already completed
    progress = conn.execute('SELECT completed FROM user_progress WHERE user_id = ? AND quest_id = ?', (user['id'], quest_id)).fetchone()
    is_completed = bool(progress['completed']) if progress else False

    # Get next quest
    next_quest = conn.execute('''
        SELECT id FROM quests 
        WHERE category_slug = ? AND order_idx > ?
        ORDER BY order_idx ASC LIMIT 1
    ''', (quest['category_slug'], quest['order_idx'])).fetchone()

    conn.close()
    return render_template('learn.html', user=user, quest=quest, is_completed=is_completed, next_quest=next_quest)

@app.route('/api/submit-lesson/<int:quest_id>', methods=['POST'])
def api_submit_lesson(quest_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401

    data = request.get_json() or {}
    selected_option = data.get('selected_option')
    
    conn = get_db_connection()
    quest = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
    if not quest:
        conn.close()
        return jsonify({'error': 'Lesson not found'}), 404

    is_correct = (str(selected_option) == str(quest['quiz_answer']))
    
    xp_gained = 0
    new_level = None
    new_badges = []
    already_completed = False

    progress = conn.execute('SELECT * FROM user_progress WHERE user_id = ? AND quest_id = ?', (session['user_id'], quest_id)).fetchone()
    if progress and progress['completed']:
        already_completed = True

    if is_correct:
        conn.execute('''
            INSERT INTO user_progress (user_id, quest_id, completed, completed_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, quest_id) DO UPDATE SET
                completed = 1,
                completed_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], quest_id))
        
        if not already_completed:
            xp_gained = quest['xp_reward']
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            old_level, _, _ = calculate_level(user['xp'])
            new_xp = user['xp'] + xp_gained
            calc_lvl, _, _ = calculate_level(new_xp)

            conn.execute('UPDATE users SET xp = ?, level = ? WHERE id = ?', (new_xp, calc_lvl, user['id']))
            conn.commit()

            if calc_lvl > old_level:
                new_level = calc_lvl

            new_badges = award_badges_check(user['id'], conn)
        else:
            conn.commit()
    
    conn.close()

    return jsonify({
        'correct': is_correct,
        'correct_answer': quest['quiz_answer'],
        'xp_gained': xp_gained,
        'already_completed': already_completed,
        'new_level': new_level,
        'new_badges': new_badges
    })


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

    return render_template('profile.html', user=user, level=lvl, curr_xp=curr_xp, next_lvl_xp=next_lvl_xp, badges=badges, completed_quests=completed_quests)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    print(f"🌟 CompuQuest booting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
