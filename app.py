from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
import click

app = Flask(__name__)

# Configure o URI do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://quizfacu_bpxn_user:fp3CgotGhuTTI1RbRCUatgCqPtVGhqh0@dpg-ct1u1au8ii6s73fj4v40-a.oregon-postgres.render.com/quizfacu_bpxn'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados
db = SQLAlchemy(app)

# Modelos
class Pergunta(db.Model):
    __tablename__ = 'pergunta'  # Definindo o nome da tabela explicitamente
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(200), nullable=False)
    explicacao = db.Column(db.String(200), nullable=False)

class Resposta(db.Model):
    __tablename__ = 'resposta'  # Definindo o nome da tabela explicitamente
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(100), nullable=False)
    correta = db.Column(db.Boolean, default=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('pergunta.id'), nullable=False)
    pergunta = db.relationship('Pergunta', backref=db.backref('respostas', lazy=True))

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para a página do quiz
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

# Rota para carregar as perguntas
@app.route('/quiz-data', methods=['GET'])
def get_quiz_data():
    perguntas = Pergunta.query.all()
    result = []
    for p in perguntas:
        respostas = Resposta.query.filter_by(pergunta_id=p.id).all()
        result.append({
            "texto": p.texto,
            "explicacao": p.explicacao,
            "respostas": [{"texto": r.texto, "correta": r.correta} for r in respostas]
        })
    return jsonify(result)

# Rota para salvar novas perguntas (via POST)
@app.route('/gerenciar', methods=['POST'])
def salvar_perguntas():
    data = request.json
    try:
        for item in data:
            pergunta = Pergunta(texto=item['texto'], explicacao=item['explicacao'])
            db.session.add(pergunta)
            db.session.flush()  # Assegura que o ID da pergunta seja gerado antes de salvar as respostas
            for resp in item['respostas']:
                resposta = Resposta(texto=resp['texto'], correta=resp['correta'], pergunta_id=pergunta.id)
                db.session.add(resposta)
        db.session.commit()
        return jsonify({"message": "Perguntas salvas com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()  # Reverte a transação em caso de erro
        return jsonify({"message": "Erro ao salvar as perguntas.", "error": str(e)}), 500

# Rota para remover todas as perguntas
@app.route('/remover-todas-perguntas', methods=['DELETE'])
def remover_todas_perguntas():
    try:
        Pergunta.query.delete()  # Remove todas as perguntas
        db.session.commit()  # Salva as alterações
        return jsonify({"message": "Todas as perguntas foram removidas com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()  # Reverte a transação em caso de erro
        return jsonify({"message": "Erro ao remover as perguntas.", "error": str(e)}), 500

# Inicializar o banco de dados ao rodar a aplicação
@app.cli.command('init-db')
@with_appcontext
def init_db():
    """Cria as tabelas no banco de dados."""
    try:
        db.create_all()  # Cria todas as tabelas
        print("Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar as tabelas: {str(e)}")

# Executando a aplicação
if __name__ == '__main__':
    app.run(debug=True)
