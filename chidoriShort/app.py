import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse

# --- Configuração ---

app = Flask(__name__)

# --- CONFIGURAÇÃO SIMPLES PARA SQLITE ---
# Garanta que esta linha esteja assim:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
# -----------------------------------------

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24) 

db = SQLAlchemy(app)
# --- Modelo do Banco de Dados ---

class Urls(db.Model):
    id_ = db.Column("id_", db.Integer, primary_key=True)
    long_url = db.Column("long_url", db.String())
    short_code = db.Column("short_code", db.String(6), unique=True)

    def __init__(self, long_url, short_code):
        self.long_url = long_url
        self.short_code = short_code

# --- Funções Auxiliares ---

def generate_short_code():
    """Gera um código alfanumérico aleatório de 6 caracteres."""
    characters = string.ascii_letters + string.digits
    while True:
        # Gera o código
        short_code = "".join(random.choice(characters) for _ in range(6))
        # Verifica se o código já existe no banco de dados
        if not Urls.query.filter_by(short_code=short_code).first():
            return short_code

def is_valid_url(url):
    """Verifica se a URL fornecida é válida."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# --- Rotas da Aplicação ---

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        long_url_received = request.form['long_url']

        # Adiciona 'http://' se o protocolo estiver faltando
        if not long_url_received.startswith(('http://', 'https://')):
            long_url_received = 'http://' + long_url_received

        if not is_valid_url(long_url_received):
            flash("Por favor, insira uma URL válida.", "error")
            return render_template('index.html')

        # Verifica se a URL já foi encurtada
        found_url = Urls.query.filter_by(long_url=long_url_received).first()

        if found_url:
            short_url = request.host_url + found_url.short_code
            return render_template('index.html', short_url=short_url)
        else:
            # Cria um novo link curto
            short_code = generate_short_code()
            new_url = Urls(long_url=long_url_received, short_code=short_code)
            db.session.add(new_url)
            db.session.commit()
            short_url = request.host_url + short_code
            return render_template('index.html', short_url=short_url)

    return render_template('index.html')

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redireciona o link curto para a URL original."""
    url_entry = Urls.query.filter_by(short_code=short_code).first_or_404()
    return redirect(url_entry.long_url)

# --- Inicialização ---

# Crie um contexto de aplicação para garantir que o banco de dados seja criado
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)