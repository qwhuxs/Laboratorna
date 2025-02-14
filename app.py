import json
import re
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  

# Файли для зберігання даних
ALBUMS_FILE = 'albums.json'
USERS_FILE = 'users.json'

# Клас для роботи з JSON даними
class JSONManager:
    @staticmethod
    def load_data(file_path, default_data):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return default_data

    @staticmethod
    def save_data(file_path, data):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

# Клас для роботи з альбомами
class AlbumManager:
    @staticmethod
    def load_albums():
        return JSONManager.load_data(ALBUMS_FILE, [])

    @staticmethod
    def save_albums(albums):
        JSONManager.save_data(ALBUMS_FILE, albums)

    @staticmethod
    def get_album_by_id(album_id):
        albums = AlbumManager.load_albums()
        return next((album for album in albums if album['id'] == album_id), None)

    @staticmethod
    def delete_album(album_id):
        albums = AlbumManager.load_albums()
        albums = [album for album in albums if album['id'] != album_id]
        AlbumManager.save_albums(albums)

    @staticmethod
    def add_album(title, description, release_date):
        albums = AlbumManager.load_albums()
        new_album = {
            'id': len(albums) + 1,
            'title': title,
            'description': description,
            'release_date': release_date
        }
        albums.append(new_album)
        AlbumManager.save_albums(albums)

# Клас для роботи з користувачами
class UserManager:
    @staticmethod
    def load_users():
        return JSONManager.load_data(USERS_FILE, {"admin": {"password": "admin123", "role": "admin"}})

    @staticmethod
    def save_users(users):
        JSONManager.save_data(USERS_FILE, users)

    @staticmethod
    def register_user(username, password):
        users = UserManager.load_users()
        if username in users:
            return False  
        users[username] = {"password": password, "role": "user"}
        UserManager.save_users(users)
        return True

    @staticmethod
    def authenticate_user(username, password):
        users = UserManager.load_users()
        return username in users and users[username]['password'] == password

# Валідація введених даних
def is_valid_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))  

def is_valid_password(password):
    return len(password) >= 6  

# Рендеримо головну сторінку
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not is_valid_username(username) or not is_valid_password(password):
            flash('Некоректні дані!')
            return redirect(url_for('register'))
        
        if UserManager.register_user(username, password):
            flash('Реєстрація успішна!')
            return redirect(url_for('login'))
        else:
            flash('Користувач вже існує!')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if UserManager.authenticate_user(username, password):
            session['username'] = username
            flash('Вхід успішний!')
            return redirect(url_for('index'))
        else:
            flash('Невірний логін або пароль!')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Ви вийшли з акаунту!')
    return redirect(url_for('index'))


@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
def edit_album(album_id):
    albums = AlbumManager.load_albums()
    album = next((a for a in albums if a['id'] == album_id), None)
    
    if album is None:
        flash('Альбом не знайдено!')
        return redirect(url_for('albums'))

    if request.method == 'POST':
        album['title'] = request.form['title']
        album['description'] = request.form['description']
        album['release_date'] = request.form['release_date']
        AlbumManager.save_albums(albums)  
        flash('Альбом оновлено!')
        return redirect(url_for('albums'))
    
    return render_template('edit_album.html', album=album)


@app.route('/add_album', methods=['GET', 'POST'])
def add_album():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        release_date = request.form['release_date']
        AlbumManager.add_album(title, description, release_date)
        flash('Альбом додано!')
        return redirect(url_for('albums'))
    return render_template('add_album.html')


@app.route('/delete_album/<int:album_id>', methods=['POST'])
def delete_album(album_id):
    AlbumManager.delete_album(album_id)
    flash('Альбом видалено!')
    return redirect(url_for('albums'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
