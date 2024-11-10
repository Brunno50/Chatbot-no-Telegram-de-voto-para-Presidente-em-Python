from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Definição das perguntas e respostas corretas
questions = [
    {"question": "Qual é o nome do descobridor do México?", "options": ["Hernán Cortés", "Cristóvão Colombo", "Francisco Pizarro"], "answer": "Hernán Cortés"},
    {"question": "Qual é a capital do Brasil?", "options": ["São Paulo", "Rio de Janeiro", "Brasília"], "answer": "Brasília"},
    {"question": "Quem foi o primeiro presidente do Brasil?", "options": ["Getúlio Vargas", "Deodoro da Fonseca", "Juscelino Kubitschek"], "answer": "Deodoro da Fonseca"},
    {"question": "Qual é o maior estado do Brasil em termos de área?", "options": ["Amazonas", "Minas Gerais", "Bahia"], "answer": "Amazonas"},
    {"question": "Qual é o maior rio do Brasil?", "options": ["Rio Amazonas", "Rio São Francisco", "Rio Paraná"], "answer": "Rio Amazonas"},
    {"question": "Em que ano o Brasil se tornou independente?", "options": ["1822", "1889", "1500"], "answer": "1822"},
    {"question": "Qual é a maior cidade do Brasil em termos de população?", "options": ["São Paulo", "Rio de Janeiro", "Salvador"], "answer": "São Paulo"},
    {"question": "Qual é o maior bioma do Brasil?", "options": ["Amazônia", "Cerrado", "Caatinga"], "answer": "Amazônia"}
]

# Variáveis para controlar pontuação e estado das perguntas
user_scores = {}
question_index = {}

# Função de início do bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_scores[chat_id] = 0  # Inicia a pontuação do usuário
    question_index[chat_id] = 0  # A primeira pergunta

    # Primeira pergunta
    await ask_question(update, context, chat_id)

# Função para exibir a pergunta
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    q_index = question_index[chat_id]
    question = questions[q_index]
    question_text = question["question"]
    options = question["options"]

    # Botões para as respostas
    reply_markup = ReplyKeyboardMarkup([[option] for option in options] + [["Próximo"]], one_time_keyboard=True)

    # Envia a pergunta
    await update.message.reply_text(question_text, reply_markup=reply_markup)

# Função para lidar com as respostas do usuário
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_answer = update.message.text

    # Verifica a resposta
    q_index = question_index[chat_id]
    correct_answer = questions[q_index]["answer"]

    if user_answer == correct_answer:
        user_scores[chat_id] += 1
        await update.message.reply_text("Você tem um ponto!")
    else:
        await update.message.reply_text("Você errou!")

    # Atualiza o índice da pergunta
    if q_index < len(questions) - 1:
        question_index[chat_id] += 1
        await update.message.reply_text("Próxima pergunta!")
        await ask_question(update, context, chat_id)
    else:
        # Se acabou as perguntas, mostrar o botão de ver resultado
        keyboard = [[InlineKeyboardButton("Ver Resultado", callback_data="show_result")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Você terminou todas as perguntas. Clique no botão abaixo para ver seu resultado.", reply_markup=reply_markup)

# Função para mostrar o resultado final
async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id

    score = user_scores.get(chat_id, 0)
    total_questions = len(questions)
    
    # Mensagem de resultado
    if score == total_questions:
        await query.answer()
        await query.message.reply_text(f"Parabéns, você acertou todas as perguntas! Seu total de pontos é {score}.")
    elif score == 1:
        await query.answer()
        await query.message.reply_text(f"Você fez somente um ponto. Seu total de pontos é {score}.")
    else:
        await query.answer()
        await query.message.reply_text(f"Você fez {score} pontos de {total_questions}. Tente melhorar da próxima vez!")

# Função principal para iniciar o bot
def main():
    application = ApplicationBuilder().token('7405856221:AAFgT_kM9bfzAF8aOVk1PBf3vge3YcLK8pY').build()

    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    # Ação de ver resultado
    application.add_handler(CallbackQueryHandler(show_result, pattern="show_result"))

    # Inicia o bot
    application.run_polling()

if __name__ == "__main__":
    main()
