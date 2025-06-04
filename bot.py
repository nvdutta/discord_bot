import discord
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
gemini_api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("MODEL")

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

client = discord.Client(intents=intents)

llm = genai.Client(api_key=gemini_api_key)

background = """
                ****BACKGROUND****
                You are Orenomnom, AKA Nick. You are 25 years old.
                Your favorite movie is Pirates of the Caribbean.
                Your favorite food is anything asian.
                You have lived in the US all your life.
                You have been to India and Italy and bring it up often.
                Your messages are short and to the point. You do not use periods
                or capitalization.
                You never use the words 'duh', 'obviously', or 'clearly'. 
                When anime is involved, you feel you are morally superior for not watching it."""

max_responses_per_day = 3  # Set the maximum number of responses per day, not including QOTD

answered_question_today = False

responses_today = 0


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_message(message):
    global responses_today
    global answered_question_today
    #Do not respond to messages from the bot itself
    if message.author == client.user:
        return
    
    if responses_today == max_responses_per_day:
        await message.reply("zzz")
        responses_today += 1
        return
    
    if responses_today > max_responses_per_day:
        return

    #Specifically mentioned in message
    if message.mentions and client.user in message.mentions and not message.mention_everyone:
        print(f"Received mention: {message.content}")

        context = f"""They said: {message.content}"""

        if message.type == discord.MessageType.reply:
            context = f"""You said: {message.reference.resolved.content}\n""" + context
            ##if message.reference.resolved.type == discord.MessageType.reply:
            ##    context = f"""They said: {message.reference.resolved.reference.resolved.content}\n""" + context

        answer = llm.models.generate_content(
                model=model,
                contents=f"""
                {background}
                ****REPLY CHAIN****
                {context}
                
                How do you respond?"""
            )

        await message.channel.send(answer.text)
        ##await message.reply(answer.text)
        print(f"Sent response: {answer.text}")
        responses_today += 1
        return


    #Question of the Day
    if message.content.lower().replace("*","").startswith("qotd") and not answered_question_today:
        print(f"Received message: {message.content}")
        answer = llm.models.generate_content(
            model=model,
            contents=f"""
            {background}
            Answer the following question, in 20 words or fewer.
            ****QUESTION****
            {message.content[5:]}"""
        )
        
        await message.reply(answer.text)
        print(f"Sent response: {answer.text}")
        answered_question_today = True
        return

client.run(bot_token)