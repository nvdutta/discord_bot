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

background = """You are rude.
                You like to disagree with other people's opinions.
                Your messages are short and to the point. You do not use apostrophes or commas.
                Do not contradict your previous messages.
                You never use the words 'duh', 'obviously', or 'clearly'.
                Never use the words 'sponsor', 'sponsorship', or 'sponsored'.
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
handler.namer = lambda name: name + ".log"
handler.setFormatter(formatter)
logger.addHandler(handler)
 
chroma_client_sponsors = chromadb.PersistentClient(path=f"{os.curdir}/db/sponsors")
chroma_client_facts = chromadb.PersistentClient(path=f"{os.curdir}/db/facts")

sponsors_collection = chroma_client_sponsors.get_or_create_collection(name="sponsors")

facts_collection = chroma_client_facts.get_or_create_collection(name="facts")

def choose_relevant_fact(message: str) -> str:
    result = facts_collection.query(
            query_texts=[message],
            include=["documents", "distances"],
            n_results=1
        )
    # Check if the relevance is under 1.60, otherwise do not include a fact
    logger.info(f"Fact Distance: {result['distances'][0][0]}")
    if result["distances"][0][0] < 1.60:
        return result["documents"][0][0]
    return ""

def choose_relevant_sponsor(message: str) -> str:
    result = sponsors_collection.query(
            query_texts=[message],
            include=["documents", "distances"],
            n_results=1
        )
    logger.info(f"Sponsor Distance: {result['distances'][0][0]}")
    # Check if the relevance is under 1.70, otherwise do not include a sponsor
    if result["distances"][0][0] < 1.70:
        return result["documents"][0][0]
    return ""

def chat(message: str, additional_prompt: str = "", username: str = "", use_previous_chat: bool = True):
    global chat_history

    fact = choose_relevant_fact(message)
    logger.info(f"Chosen Fact: {fact}")
    sponsor = choose_relevant_sponsor(message)
    logger.info(f"Chosen Sponsor: {sponsor}")

    if use_previous_chat:
        chat_history.append({"role": "user", "content": f"{username}: {message}"})

    system_prompt = f"{background}"
    if fact:
        system_prompt += f"\n{fact}"
    if sponsor:
        system_prompt += f"\nSmoothly connect the following sponsored product, the company, and where to find it.\nYou are sponsored by: {sponsor}"

    system_prompt += f"\n{additional_prompt}"

    message_context = [{"role": "system", "content": system_prompt}]
    
    if use_previous_chat:
        message_context.extend(chat_history)

    response = litellm.completion(
                model=ollama_model,
                api_base="http://localhost:11434",
                temperature=0.6,
                messages=message_context
            )
    
    answer = response.choices[0].message.content.replace("\n\n", "\n").replace("*", "").replace('”', '').lower().replace(" i ", " I ")
    answer = (answer[:1900] + "...") if len(answer) > 1900 else answer
    if use_previous_chat:
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

    # Do not respond to messages from the bot itself
    if message.author == client.user:
        return
    # Check if channel is "qotd"
    if message.channel.name != "qotd":
        return
    if responses_today > max_responses_per_day:
        return

    # Specifically mentioned in message
    if (message.mentions and client.user in message.mentions and not message.mention_everyone):

        # If no responses left for today, give a sendoff
        if responses_today == max_responses_per_day:
            async with message.channel.typing():
                await message.reply("zzzz")
            responses_today += 1
            return
    
        logger.info(f"Received raw message: {message.content}")
    
        trimmed_message = message.content.partition(" ")[2].replace("*","") if "@" in message.content else message.content.replace("*","")

        async with message.channel.typing():
            answer = chat(trimmed_message, "Respond to the user's message.", message.author.display_name)
            await message.reply(answer)
        logger.info(f"Sent response: {answer}")
        responses_today += 1
        return
    
    # Interrupt discussion if there is a keyword, or random chance for long messages
    if (any(word in message.content.lower() for word in trigger_words)) or (len(message.content) > 80 and random.randint(1, 100) <= 2 * (max_responses_per_day - responses_today)):
        trimmed_message = message.content.replace("*","")
        async with message.channel.typing():
            answer = chat(trimmed_message, "Assert your opinion on what the user said.", message.author.display_name)
            await message.reply(answer)
        logger.info(f"Sent response: {answer}")
        responses_today += 1
        return

    # Question of the Day
    if ("qotd:" in message.content.lower() or "question of the day:" in message.content.lower()) and not answered_question_today:
        logger.info(f"Received raw message: {message.content}")

        trimmed_message = message.content.lower().partition(":")[2].strip()

        chat_history = []

        async with message.channel.typing():
            answer = chat(trimmed_message, "Choose a specific answer to the question and strongly defend it.", message.author.display_name)
            await message.reply(answer)
        
        logger.info(f"Sent response: {answer}")
        answered_question_today = True
        responses_today = 0
        return

client.run(bot_token)
