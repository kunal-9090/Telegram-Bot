import os
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
groq_api_key = os.getenv("GROQ_API_KEY")

def setup_llm_chain(topic="technology"):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Joking AI. Give me only ONE short, clever, and very funny joke on the given topic. "
                  "The joke should be direct and to the point. Do not include any explanation, thinking process, "
                  "or any text in <think> tags. Just provide the joke itself. Be witty and original."),
        ("user", f"Generate a joke on the topic: {topic}")
    ])

    llm = ChatGroq(
        model="Deepseek-R1-Distill-Llama-70b",
        groq_api_key=groq_api_key
    )

    return prompt | llm | StrOutputParser()

def clean_joke_response(response):

    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    
    cleaned = re.sub(r'^(Certainly!|Here\'s|Sure!|Alright,).*?\n', '', cleaned, flags=re.DOTALL)
    
    cleaned = cleaned.strip()
    
    return cleaned

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Mention me with a topic like '@MemeReaper_Bot python' to get a joke.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Mention me with a topic like '@MemeReaper_Bot python' to get a funny joke.")

async def generate_joke(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    try:
        await update.message.reply_text(f"Generating a joke about '{topic}'...")
        chain = setup_llm_chain(topic)
        joke_response = await chain.ainvoke({})  
        
        clean_joke = clean_joke_response(joke_response)
        
        await update.message.reply_text(clean_joke)
    except Exception as e:
        await update.message.reply_text("Oops! Something went wrong while generating the joke.")
        print(f"Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    bot_username = context.bot.username

    if f'@{bot_username}' in msg:
        match = re.search(rf'@{re.escape(bot_username)}\s+(.+)', msg)
        if match and match.group(1).strip():
            topic = match.group(1).strip()
            await generate_joke(update, context, topic)
        else:
            await update.message.reply_text("Please specify a topic after mentioning me.")

def main():
    token = os.getenv("TELEGRAM_API_KEY")
    if not token:
        raise RuntimeError("TELEGRAM_API_KEY not found in environment variables.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()