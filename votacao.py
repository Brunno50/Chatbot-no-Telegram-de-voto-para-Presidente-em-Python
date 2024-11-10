import telebot
import sqlite3

# Insira o token do seu bot do Telegram
TOKEN = '7405856221:AAFgT_kM9bfzAF8aOVk1PBf3vge3YcLK8pY'
bot = telebot.TeleBot(TOKEN)

# Conexão com o banco de dados SQLite3
conn = sqlite3.connect('votacao.db', check_same_thread=False)
cursor = conn.cursor()

# Cria as tabelas para armazenar votos, o estado da votação e os candidatos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS votos (
        cpf TEXT PRIMARY KEY,
        nome TEXT,
        voto TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidatos (
        nome TEXT PRIMARY KEY
    )
''')

# Define o estado inicial da votação como aberta, caso não esteja configurado
cursor.execute('SELECT valor FROM configuracoes WHERE chave = "votacao_ativa"')
if cursor.fetchone() is None:
    cursor.execute('INSERT INTO configuracoes (chave, valor) VALUES ("votacao_ativa", "1")')
    conn.commit()

# Função para iniciar o bot e verificar o estado da votação
@bot.message_handler(commands=['start'])
def start(message):
    # Verifica se a votação está ativa
    cursor.execute('SELECT valor FROM configuracoes WHERE chave = "votacao_ativa"')
    votacao_ativa = cursor.fetchone()[0] == "1"

    if votacao_ativa:
        bot.send_message(message.chat.id, "Digite seu nome completo:")
        bot.register_next_step_handler(message, solicitar_nome)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add("Ver resultados")
        bot.send_message(message.chat.id, "A votação está encerrada. Clique em 'Ver resultados' para ver o resultado da eleição.", reply_markup=markup)
        bot.register_next_step_handler(message, mostrar_resultados)

# Função para solicitar o nome do usuário
def solicitar_nome(message):
    nome = message.text
    bot.send_message(message.chat.id, "Digite seu CPF (somente números):")
    bot.register_next_step_handler(message, solicitar_cpf, nome)

# Função para solicitar o CPF e iniciar a votação
def solicitar_cpf(message, nome):
    cpf = message.text
    if not cpf.isdigit() or len(cpf) != 11:
        bot.send_message(message.chat.id, "CPF inválido. Por favor, insira um CPF válido com 11 dígitos.")
        bot.register_next_step_handler(message, solicitar_cpf, nome)
        return

    cursor.execute('SELECT voto FROM votos WHERE cpf = ?', (cpf,))
    if cursor.fetchone():
        bot.send_message(message.chat.id, "Você já votou e não pode votar mais de uma vez.")
    else:
        # Recupera a lista de candidatos do banco de dados
        cursor.execute('SELECT nome FROM candidatos')
        candidatos = cursor.fetchall()

        if not candidatos:
            bot.send_message(message.chat.id, "Nenhum candidato disponível para votar.")
            return

        # Cria os botões com os candidatos
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for candidato in candidatos:
            markup.add(candidato[0])

        bot.send_message(message.chat.id, "Escolha seu candidato:", reply_markup=markup)
        bot.register_next_step_handler(message, escolher_presidente, cpf, nome)

# Função para escolher o presidente
def escolher_presidente(message, cpf, nome):
    voto = message.text
    cursor.execute('SELECT nome FROM candidatos WHERE nome = ?', (voto,))
    if cursor.fetchone() is None:
        bot.send_message(message.chat.id, "Opção inválida. Escolha um candidato válido.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Confirmar")
    bot.send_message(message.chat.id, f"Você escolheu {voto}. Clique em Confirmar para registrar seu voto.", reply_markup=markup)
    bot.register_next_step_handler(message, confirmar_voto, cpf, nome, voto)

# Função para confirmar o voto
def confirmar_voto(message, cpf, nome, voto):
    if message.text == "Confirmar":
        cursor.execute('INSERT INTO votos (cpf, nome, voto) VALUES (?, ?, ?)', (cpf, nome, voto))
        conn.commit()
        bot.send_message(message.chat.id, "Voto registrado com sucesso!")
    else:
        bot.send_message(message.chat.id, "Votação cancelada.")

# Função para inserir um novo presidente
@bot.message_handler(commands=['inserir_presidente'])
def inserir_presidente(message):
    bot.send_message(message.chat.id, "Digite a senha para adicionar um novo candidato:")
    bot.register_next_step_handler(message, verificar_senha_inserir)

def verificar_senha_inserir(message):
    senha = message.text
    if senha == "1234":
        bot.send_message(message.chat.id, "Digite o nome do novo candidato para adicionar à votação:")
        bot.register_next_step_handler(message, adicionar_candidato)
    else:
        bot.send_message(message.chat.id, "Senha incorreta. Não foi possível adicionar o candidato.")

def adicionar_candidato(message):
    nome_candidato = message.text
    try:
        cursor.execute('INSERT INTO candidatos (nome) VALUES (?)', (nome_candidato,))
        conn.commit()
        bot.send_message(message.chat.id, f"O candidato '{nome_candidato}' foi adicionado com sucesso!")
    except sqlite3.IntegrityError:
        bot.send_message(message.chat.id, f"O candidato '{nome_candidato}' já existe. Escolha outro nome.")

# Função para deletar um presidente
@bot.message_handler(commands=['deletar_presidente'])
def deletar_presidente(message):
    bot.send_message(message.chat.id, "Digite a senha para deletar um candidato:")
    bot.register_next_step_handler(message, verificar_senha_deletar)

def verificar_senha_deletar(message):
    senha = message.text
    if senha == "1234":
        bot.send_message(message.chat.id, "Digite o nome do candidato que deseja deletar:")
        bot.register_next_step_handler(message, excluir_candidato)
    else:
        bot.send_message(message.chat.id, "Senha incorreta. Não foi possível deletar o candidato.")

def excluir_candidato(message):
    nome_candidato = message.text
    cursor.execute('SELECT nome FROM candidatos WHERE nome = ?', (nome_candidato,))
    if cursor.fetchone() is None:
        bot.send_message(message.chat.id, f"O candidato '{nome_candidato}' não foi encontrado.")
    else:
        cursor.execute('DELETE FROM candidatos WHERE nome = ?', (nome_candidato,))
        conn.commit()
        bot.send_message(message.chat.id, f"O candidato '{nome_candidato}' foi deletado com sucesso.")

# Função para listar todos os candidatos
@bot.message_handler(commands=['lista_presidente'])
def lista_presidente(message):
    cursor.execute('SELECT nome FROM candidatos')
    candidatos = cursor.fetchall()

    if not candidatos:
        bot.send_message(message.chat.id, "Nenhum candidato foi adicionado ainda.")
    else:
        lista_candidatos = "\n".join([candidato[0] for candidato in candidatos])
        bot.send_message(message.chat.id, f"Lista de Candidatos:\n{lista_candidatos}")

# Função para encerrar a votação
@bot.message_handler(commands=['encerrar'])
def encerrar(message):
    bot.send_message(message.chat.id, "Digite a senha para encerrar a votação:")
    bot.register_next_step_handler(message, verificar_senha_encerrar)

def verificar_senha_encerrar(message):
    senha = message.text
    if senha == "1234":
        cursor.execute('UPDATE configuracoes SET valor = "0" WHERE chave = "votacao_ativa"')
        conn.commit()
        bot.send_message(message.chat.id, "A votação foi encerrada com sucesso!")
    else:
        bot.send_message(message.chat.id, "Senha incorreta. Não foi possível encerrar a votação.")

# Função para reabrir a votação
@bot.message_handler(commands=['reabrir'])
def reabrir(message):
    bot.send_message(message.chat.id, "Digite a senha para reabrir a votação:")
    bot.register_next_step_handler(message, verificar_senha_reabrir)

def verificar_senha_reabrir(message):
    senha = message.text
    if senha == "1234":
        cursor.execute('UPDATE configuracoes SET valor = "1" WHERE chave = "votacao_ativa"')
        conn.commit()
        bot.send_message(message.chat.id, "A votação foi reaberta com sucesso!")
    else:
        bot.send_message(message.chat.id, "Senha incorreta. Não foi possível reabrir a votação.")

# Função para zerar o banco de dados e reabrir a votação
@bot.message_handler(commands=['zerar_banco'])
def zerar_banco(message):
    bot.send_message(message.chat.id, "Digite a senha para zerar o banco de dados e reabrir a votação:")
    bot.register_next_step_handler(message, verificar_senha_zerar)

def verificar_senha_zerar(message):
    senha = message.text
    if senha == "1234":
        # Limpa todos os registros de votos e reabre a votação
        cursor.execute('DELETE FROM votos')  # Limpa todos os registros de votos
        cursor.execute('UPDATE configuracoes SET valor = "1" WHERE chave = "votacao_ativa"')  # Reabre a votação
        conn.commit()
        bot.send_message(message.chat.id, "Todos os dados de votos foram apagados e a votação foi reaberta com sucesso!")
    else:
        bot.send_message(message.chat.id, "Senha incorreta. Não foi possível zerar o banco de dados.")

# Função para mostrar os resultados da votação
def mostrar_resultados(message):
    cursor.execute('SELECT voto, COUNT(*) FROM votos GROUP BY voto')
    resultados = cursor.fetchall()
    total_votos = sum([voto[1] for voto in resultados])

    if total_votos == 0:
        bot.send_message(message.chat.id, "Nenhum voto foi registrado.")
        return

    mensagem_resultados = "Resultados da Eleição:\n"
    votos_dict = {voto[0]: voto[1] for voto in resultados}
    vencedor = max(votos_dict, key=votos_dict.get)

    for candidato, votos in votos_dict.items():
        porcentagem = (votos / total_votos) * 100
        mensagem_resultados += f"{candidato}: {votos} votos ({porcentagem:.2f}%)\n"

    mensagem_resultados += f"\nTotal de votos: {total_votos}\n"
    mensagem_resultados += f"Vencedor: {vencedor}\n"

    bot.send_message(message.chat.id, mensagem_resultados)

# Inicia o bot
bot.polling()
