import logging.handlers
import discord
import os
import random
import logging
import litellm
import chromadb
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

client = discord.Client(intents=intents)

ollama_model = "ollama/gemma3"

trigger_words = ["india", "italy", "anime", "asia", "socialism", "christianity", "death penalty", "evil orenomnom"]

chat_history = []

background = """****BACKGROUND****
                You are rude.
                You like to disagree with people's opinions.
                You choose a strong opinion for every topic.
                Your messages are short and to the point. You do not use apostrophes or commas.
                Do not contradict your previous messages.
                You never use the words 'duh', 'obviously', or 'clearly'.
                For sponsors, smoothly connect the product, the company, and where to find it.
                Never use the words 'sponsor', 'sponsorship', or 'spoiler'.
                """

max_responses_per_day = 3  # Set the maximum number of responses per day, not including QOTD

answered_question_today = False

responses_today = 0

os.chdir(os.path.dirname(os.path.abspath(__file__)))
# If the logs directory does not exist, create it
if not os.path.exists("logs"):
    os.makedirs("logs")

logger = logging.getLogger('discord')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
handler = logging.handlers.TimedRotatingFileHandler('logs/bot.log', when='midnight', backupCount= 10)
handler.setFormatter(formatter)
logger.addHandler(handler)
 
chroma_client_sponsors = chromadb.PersistentClient(path=f"{os.curdir}/db/sponsors")
chroma_client_facts = chromadb.PersistentClient(path=f"{os.curdir}/db/facts")

sponsors_collection = chroma_client_sponsors.get_or_create_collection(name="sponsors")

facts_collection = chroma_client_facts.get_or_create_collection(name="facts")

def choose_relevant_fact(message: str) -> str:
    global facts_collection
    result = facts_collection.query(
            query_texts=[message],
            include=["documents", "distances"],
            n_results=1
        )
    if result["distances"][0][0] < 1.60:
        return result["documents"][0][0]
    return ""

def choose_relevant_sponsor(message: str) -> str:
    global sponsors_collection
    result = sponsors_collection.query(
            query_texts=[message],
            include=["documents", "distances"],
            n_results=1
        )
    if result["distances"][0][0] < 1.70:
        return result["documents"][0][0]
    return ""

def chat(message: str, additional_prompt: str = "", username: str = ""):
    global chat_history

    fact = choose_relevant_fact(message)
    logger.info(f"Chosen Fact: {fact}")
    sponsor = choose_relevant_sponsor(message)
    logger.info(f"Chosen Sponsor: {sponsor}")

    chat_history.append({"role": "user", "content": f"{username}: {message}"})

    message_context = [{"role": "system", "content": f"{background}\n{fact}\nYou are sponsored by: {sponsor}\n{additional_prompt}"}]
    message_context.extend(chat_history)

    answer = litellm.completion(
                model=ollama_model,
                api_base="http://localhost:11434",
                temperature=0.6,
                messages=message_context
            ).choices[0].message.content.replace("\n\n", "\n").replace("*", "").replace('”', '').lower().replace(" i ", " I ")
    answer = (answer[:1900] + "...") if len(answer) > 1900 else answer
    chat_history.append(
            {"role": "assistant", "content": answer}
        )
    return answer


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_message(message):
    global responses_today
    global answered_question_today
    global chat_history

    #Do not respond to messages from the bot itself
    if message.author == client.user:
        return
    
    # Check if channel is "qotd"
    if message.channel.name != "qotd":
        return

    if responses_today > max_responses_per_day:
        return

    #Specifically mentioned in message, or message contains trigger word, or random chance for long messages
    if (message.mentions and client.user in message.mentions and not message.mention_everyone) or (any(word in message.content.lower() for word in trigger_words)) or (len(message.content) > 80 and random.randint(1, 100) <= 2 * (max_responses_per_day - responses_today)):
        if responses_today == max_responses_per_day:

            await message.reply("zzzz")
            responses_today += 1
            return
    
        logger.info(f"Received raw message: {message.content}")
    
        trimmed_message = message.content.partition(" ")[2].replace("*","") if "@" in message.content else message.content.replace("*","")

        async with message.channel.typing():
            answer = chat(trimmed_message, "Keep your reply to 30 words or fewer.", message.author.display_name)
            await message.reply(answer)
        logger.info(f"Sent response: {answer}")
        responses_today += 1
        return

    #Question of the Day
    if ("qotd:" in message.content.lower() or "question of the day:" in message.content.lower()) and not answered_question_today:
        logger.info(f"Received raw message: {message.content}")

        trimmed_message = message.content.lower().partition(":")[2].strip()

        chat_history = []

        async with message.channel.typing():
            answer = chat(trimmed_message, "", message.author.display_name)
            await message.reply(answer)
        
        logger.info(f"Sent response: {answer}")
        answered_question_today = True
        responses_today = 0
        return

client.run(bot_token)
