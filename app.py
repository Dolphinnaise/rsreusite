import os
from flask import Flask, render_template_string, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Настройка приложения Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///afisha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Директория для загрузки файлов
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Роль: user или admin

class Afisha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    release_date = db.Column(db.String(20), nullable=False)
    poster = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(50), nullable=False)

# Создаем директорию для загрузки файлов, если она не существует
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Проверка разрешенных расширений для файлов
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Главная страница
@app.route('/')
def index():
    afishas = Afisha.query.all()
    return render_template_string("""
        <head><style>{{ styles }}</style></head>
        <header>Интернет-Афиша</header>
        <div class="container">
            {% if 'user' in session %}
                <p>Добро пожаловать, {{ session['user'] }}! <a href="{{ url_for('logout') }}" class="button">Выйти</a></p>
            {% else %}
                <p><a href="{{ url_for('login') }}" class="button">Войти</a> | <a href="{{ url_for('register') }}" class="button">Регистрация</a></p>
            {% endif %}
            <h2>Список афиш</h2>
            <a href="{{ url_for('add_afisha') }}" class="button">Добавить афишу</a>
            {% for afisha in afishas %}
                <div class="afisha-item">
                    <h3>{{ afisha.title }}</h3>
                    <p><strong>Жанр:</strong> {{ afisha.genre }}</p>
                    <p><strong>Описание:</strong> {{ afisha.description }}</p>
                    <p><strong>Дата выхода:</strong> {{ afisha.release_date }}</p>
                    <img src="{{ url_for('static', filename=afisha.poster) }}" width="100" alt="{{ afisha.title }}">
                    <p><a href="{{ url_for('edit_afisha', id=afisha.id) }}" class="button">Редактировать</a>
                    <a href="{{ url_for('delete_afisha', id=afisha.id) }}" class="button">Удалить</a></p>
                </div>
            {% endfor %}
        </div>
    """, styles=styles, afishas=afishas)

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация прошла успешно! Пожалуйста, войдите.')
        return redirect(url_for('login'))
    return render_template_string("""
        <head><style>{{ styles }}</style></head>
        <header>Регистрация</header>
        <div class="container">
            <form class="form" method="POST">
                <input type="text" name="username" placeholder="Имя пользователя" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Зарегистрироваться</button>
            </form>
            <p>Уже есть аккаунт? <a href="{{ url_for('login') }}" class="button">Войти</a></p>
        </div>
    """, styles=styles)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!')
    return render_template_string("""
        <head><style>{{ styles }}</style></head>
        <header>Вход</header>
        <div class="container">
            <form class="form" method="POST">
                <input type="text" name="username" placeholder="Имя пользователя" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
            <p>Нет аккаунта? <a href="{{ url_for('register') }}" class="button">Регистрация</a></p>
        </div>
    """, styles=styles)

# Страница выхода
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('index'))

# Страница добавления афиши
@app.route('/add_afisha', methods=['GET', 'POST'])
def add_afisha():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        release_date = request.form['release_date']
        genre = request.form['genre']
        
        # Обработка файла
        if 'poster' not in request.files:
            flash('Нет файла постера!')
            return redirect(request.url)
        file = request.files['poster']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            poster_url = f"/uploads/{filename}"
        else:
            flash('Неверный формат файла постера!')
            return redirect(request.url)
        
        # Добавление новой афиши в базу данных
        new_afisha = Afisha(title=title, description=description, release_date=release_date, poster=poster_url, genre=genre)
        db.session.add(new_afisha)
        db.session.commit()
        flash('Афиша успешно добавлена!')
        return redirect(url_for('index'))
    return render_template_string("""
        <head><style>{{ styles }}</style></head>
        <header>Добавление Афиши</header>
        <div class="container">
            <form class="form" method="POST" enctype="multipart/form-data">
                <input type="text" name="title" placeholder="Название" required>
                <textarea name="description" placeholder="Описание" required></textarea>
                <input type="text" name="release_date" placeholder="Дата выхода" required>
                <input type="text" name="genre" placeholder="Жанр" required>
                <input type="file" name="poster" accept="image/*" required>
                <button type="submit">Добавить</button>
            </form>
        </div>
    """, styles=styles)

# Страница редактирования афиши
@app.route('/edit_afisha/<int:id>', methods=['GET', 'POST'])
def edit_afisha(id):
    afisha = Afisha.query.get_or_404(id)
    if request.method == 'POST':
        afisha.title = request.form['title']
        afisha.description = request.form['description']
        afisha.release_date = request.form['release_date']
        afisha.genre = request.form['genre']
        
        # Обработка нового файла постера
        if 'poster' in request.files:
            file = request.files['poster']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                afisha.poster = f"/uploads/{filename}"
        
        db.session.commit()
        flash('Афиша успешно обновлена!')
        return redirect(url_for('index'))
    
    return render_template_string("""
        <head><style>{{ styles }}</style></head>
        <header>Редактирование Афиши</header>
        <div class="container">
            <form class="form" method="POST" enctype="multipart/form-data">
                <input type="text" name="title" placeholder="Название" value="{{ afisha.title }}" required>
                <textarea name="description" placeholder="Описание" required>{{ afisha.description }}</textarea>
                <input type="text" name="release_date" placeholder="Дата выхода" value="{{ afisha.release_date }}" required>
                <input type="text" name="genre" placeholder="Жанр" value="{{ afisha.genre }}" required>
                <p>Текущий постер:</p>
                <img src="{{ url_for('static', filename=afisha.poster) }}" width="100" alt="{{ afisha.title }}">
                <input type="file" name="poster" accept="image/*">
                <button type="submit">Обновить</button>
            </form>
        </div>
    """, styles=styles, afisha=afisha)

# Страница удаления афиши
@app.route('/delete_afisha/<int:id>')
def delete_afisha(id):
    afisha = Afisha.query.get_or_404(id)
    db.session.delete(afisha)
    db.session.commit()
    flash('Афиша успешно удалена!')
    return redirect(url_for('index'))

# Стили
styles = """
    body {
        font-family: Arial, sans-serif;
        background-color: #f0f0f5;
        color: grey;
    }
    header {
        text-align: center;
        background-color: #2a2a68;
        padding: 20px;
        font-size: 24px;
    }
    .container {
        width: 80%;
        margin: auto;
        padding: 20px;
    }
    .button {
        background-color: #6a4e9c;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
    }
    .button:hover {
        background-color: #8a6cbb;
    }
    .form input, .form textarea {
        width: 100%;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .form button {
        background-color: #6a4e9c;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
    }
    .form button:hover {
        background-color: #8a6cbb;
    }
    .afisha-item {
        background-color: #3f2b70;
        margin: 10px 0;
        padding: 20px;
        border-radius: 10px;
    }
    .afisha-item img {
        border-radius: 5px;
    }
"""

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
