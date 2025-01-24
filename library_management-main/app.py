from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'library_secret'

# SQLite Configuration
DATABASE = 'library.db'

# Hardcoded admin credentials
ADMIN_USERNAME = 'veda'
ADMIN_PASSWORD = 'samhita'


def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize Database
def init_db():
    with connect_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                is_booked INTEGER DEFAULT 0,
                booked_by INTEGER DEFAULT NULL,
                FOREIGN KEY (booked_by) REFERENCES members (id)
            );
        ''')

        # Add a default user
        # db.execute("INSERT OR IGNORE INTO members (username, password) VALUES ('vaishnavi', '1234');")
        # Add some sample books
        # db.execute("INSERT OR IGNORE INTO books (id, title, author) VALUES (1, 'Book One', 'Author A');")
        # db.execute("INSERT OR IGNORE INTO books (id, title, author) VALUES (2, 'Book Two', 'Author B');")
        # db.execute("INSERT OR IGNORE INTO books (id, title, author) VALUES (3, 'Book Three', 'Author C');")
        # db.commit()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with connect_db() as db:
            member = db.execute('SELECT * FROM members WHERE username = ? AND password = ?', (username, password)).fetchone()
            if member:
                session['user_id'] = member['id']
                session['username'] = member['username']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Fetch available books
    with connect_db() as db:
        books = db.execute('SELECT * FROM books').fetchall()
    
    return render_template('dashboard.html', books=books, member_username=session['username'])

@app.route('/book/<int:book_id>')
def book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with connect_db() as db:
        db.execute('UPDATE books SET is_booked = 1, booked_by = ? WHERE id = ?', (session['user_id'], book_id))
        db.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    show = "bookedBooks"
    # Check if admin is logged in
    if 'admin_logged_in' not in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['admin_logged_in'] = True
                session['admin_username'] = username  # Store admin username in session
                return redirect(url_for('admin'))
            else:
                flash('Invalid admin credentials')
        return render_template('admin_login.html')

    if request.method == 'POST':
        # show booked books
        if 'book_id' in request.form:
            try:
                book_id = request.form['book_id']
                with connect_db() as db:
                    db.execute('UPDATE books SET is_booked = 0, booked_by = NULL WHERE id = ?', (book_id,))
                    db.commit()
                flash('Book unbooked successfully!')
            except sqlite3.Error as e:
                flash(f"Database error occured: {e}")

        #Handle Add/Delete Book
        if 'add_book' in request.form:
            try:
                title = request.form['title']
                author = request.form['author']
                with connect_db() as db:
                    db.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
                    db.commit()
                flash('Book added successfully!')
            except sqlite3.Error as e:
                flash(f"Database error occured: {e}")
            show = "bookManagement"
        elif 'delete_book' in request.form:
            try:
                book_id = request.form['book_id']
                with connect_db() as db:
                    db.execute('DELETE FROM books WHERE id = ?', (book_id,))
                    db.commit()
                flash('Book deleted successfully!')
            except sqlite3.Error as e:
                print(f"Database error occured: {e}")
            show = "bookManagement"

        # Handle Add/Delete Member
        if 'add_member' in request.form:
            try:
                username = request.form['member_username']
                password = request.form['member_password']
                with connect_db() as db:
                    db.execute('INSERT INTO members (username, password) VALUES (?, ?)', (username, password))
                    db.commit()
                flash('Member added successfully!')
            except sqlite3.Error as e:
                flash("UserName already exists")
            show = "memberManagement"
        elif 'delete_member' in request.form:
            try:
                member_id = request.form['member_id']
                with connect_db() as db:
                    db.execute('DELETE FROM members WHERE id = ?', (member_id,))
                    db.commit()
                flash('Member deleted successfully!')
            except sqlite3.Error as e:
                print(f"Database error occured: {e}")
            show = "memberManagement"

    # Get all books and members
    with connect_db() as db:
        booked_books = db.execute('SELECT * FROM books INNER JOIN members ON books.booked_by = members.id WHERE is_booked = 1').fetchall()
        books = db.execute('SELECT * FROM books').fetchall()
        members = db.execute('SELECT * FROM members').fetchall()
    
    return render_template('admin.html', show=show, booked_books=booked_books, books=books, members=members, admin_username=session.get('admin_username'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
