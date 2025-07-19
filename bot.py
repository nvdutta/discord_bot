import discord
import os
import random
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
                You are 'Evil Orenomnom'.
                You like to disagree with people's opinions.
                You choose a strong opinion for every topic.
                Your messages are short and to the point. You do not use apostrophes or commas.
                Do not contradict your previous messages.
                You never use the words 'duh', 'obviously', or 'clearly'.
                For sponsors, be specific about the product, the company, and where to find it.
                Never use the words 'sponsor', 'sponsorship', or 'spoiler'.
                """

max_responses_per_day = 3  # Set the maximum number of responses per day, not including QOTD

answered_question_today = False

responses_today = 0

os.chdir(os.path.dirname(os.path.abspath(__file__)))

chroma_client_sponsors = chromadb.PersistentClient(path=f"{os.curdir}/chromadb/sponsors")
chroma_client_facts = chromadb.PersistentClient(path=f"{os.curdir}/chromadb/facts")

sponsors_collection = chroma_client_sponsors.get_or_create_collection(name="sponsors")

facts_collection = chroma_client_facts.get_or_create_collection(name="facts")

sponsors_collection.upsert(
    ids=["id1","id2","id3","id4","id5", "id6"],
    documents=[
        "The awakening taste of Jameson Irish Whiskey, brewed in Jameson, Dublin.",
        "Foster's Grill, the best place to get a burger and fries in the US. Serving local communites in Virginia since 1999.",
        "Fall Guys Ultimate Knockout, the game where you can compete with your friends in a series of wacky challenges. It is making a big comeback.",
        "Watch Superman's newest movie iteration from Director James Gunn. Enter the new DC Cinematic Universe. In theaters now.",
        "Smirnoff ICE alcoholic seltzers, available in Green Apple, Peach Bellini, and many more.",
        "Labubu plush monsters by Pop Mart are adorable, mischeivous, and highly collectible."
    ]
)

facts_collection.upsert(
    ids=["id1","id2","id3","id4","id5","id6", "id7"],
    documents=[
        "Your favorite movie is Pirates of the Caribbean.",
        "You have lived in the US your whole life, but you have been to India and Italy.",
        "You are better than other people because you do not watch anime.",
        "You are anti-union and anti socialism.",
        "You are a violent Christian. You believe there should be another crusade.",
        "War is the only way humanity can make progress. Violence is the best teacher.",
        "You love asian food. You will not stand for anyone badmouthing Sushi."
    ]
)

def choose_relevant_fact(message: str) -> str:
    global facts_collection
    return facts_collection.query(
            query_texts=[message],
            n_results=1
        )['documents'][0][0]

def choose_relevant_sponsor(message: str) -> str:
    global sponsors_collection
    return sponsors_collection.query(
        query_texts=[message],
        n_results=1
        )['documents'][0][0]

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_message(message):
    global responses_today
    global answered_question_today
    global chat_history
    global facts_collection
    global sponsors_collection

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

            # answer = litellm.completion(
            # model=ollama_model,
            # api_base="http://localhost:11434",
            # temperature=0.6,
            # messages=[
            #     {"role": "system", "content": f"{background}"},
            #     {"role": "user", "content": "Offer a short, vague excuse for why you have to go."}
            # ]
            # ).choices[0].message.content.replace("\n\n", "\n").replace("*", "").replace('”', '')
            
            await message.reply("zzzz")
            responses_today += 1
            return
    
        print(f"Received raw message: {message.content}")
    
        trimmed_message = message.content.partition(" ")[2].replace("*","") if "@" in message.content else message.content.replace("*","")

        fact = choose_relevant_fact(trimmed_message)
        print(f"Chosen Fact: {fact}")
        sponsor = choose_relevant_sponsor(trimmed_message)
        print(f"Chosen Sponsor: {sponsor}")

        chat_history.append({"role": "user", "content": f"{message.author.display_name}: {trimmed_message}"})

        message_context = [{"role": "system", "content": f"{background}\n{fact}\nYou are sponsored by: {sponsor}\nKeep your reply to 30 words or fewer."}]
        message_context.extend(chat_history)

        async with message.channel.typing():
            answer = litellm.completion(
                model=ollama_model,
                api_base="http://localhost:11434",
                temperature=0.6,
                messages=message_context
            ).choices[0].message.content.replace("\n\n", "\n").replace("*", "").replace('”', '').lower().replace(" i ", " I ")
            answer = (answer[:1900] + "...") if len(answer) > 1900 else answer

        await message.reply(answer)
        print(f"Sent response: {answer}")
        chat_history.append(
            {"role": "assistant", "content": f"{answer}"}
        )
        responses_today += 1
        return

    #Question of the Day
    if ("qotd:" in message.content.lower() or "question of the day:" in message.content.lower()) and not answered_question_today:
        print(f"Received raw message: {message.content}")

        trimmed_message = message.content.lower().partition(":")[2].strip()

        chat_history = [
            {"role": "user", "content": f"{message.author.display_name}: {trimmed_message}"}
        ]

        fact = choose_relevant_fact(trimmed_message)
        print(f"Chosen Fact: {fact}")
        sponsor = choose_relevant_sponsor(trimmed_message)
        print(f"Chosen Sponsor: {sponsor}")

        message_context = [{"role": "system", "content":f"{background}\n{fact}\nYou are sponsored by: {sponsor}\nKeep your reply to 30 words or fewer. ALL QUESIONS SHOULD BE ANSWERED WITH A SPECIFIC ANSWER."}]
        message_context.extend(chat_history)

        async with message.channel.typing():
            answer = litellm.completion(
                model=ollama_model,
                temperature=0.6,
                api_base="http://localhost:11434",
                messages=message_context
            ).choices[0].message.content.replace("\n\n", "\n").replace("*", "").replace('”', '').lower().replace(" i ", " I ")
            answer = (answer[:1900] + "...") if len(answer) > 1900 else answer

        await message.reply(answer)
        chat_history.append(
            {"role": "assistant", "content": answer}
        )
        print(f"Sent response: {answer}")
        answered_question_today = True
        return

client.run(bot_token)
