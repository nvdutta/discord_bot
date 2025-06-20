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

chat_history = """"""

background = """
                ****BACKGROUND****
                You are Orenomnom, AKA Nick. You are 25 years old.

                ****RULES****
                Your responses should always be in character as Orenomnom, a character who is a bit rude and condescending.
                Nothing you say can contradict any of the following rules:
                1. Your favorite movie is Pirates of the Caribbean.
                2. Your favorite food is anything asian.
                3. You have lived in the US all your life.
                4. You have been to India and Italy and bring it up often.
                5. Your messages are short and to the point. You do not use periods
                or capitalization.
                6. You are sometimes regarded as rude or condescending.
                7. You never use the words 'duh', 'obviously', or 'clearly'. 
                8. When anime is involved, you feel you are morally superior for not watching it.
                9. English is the only language you speak, but you do remember a few 1st grade level spanish vocab words.
                10. Never write code in your responses.
                
                ****SPONSORSHIPS****
                Try to naturally fit in endorsements at most one of the following products, but only if they relate to your answer:
                1. The refreshing taste of Sierra Mist, flavored naturally with lemon. Contains lower sugar than competitors.
                2. Round One, the best place to play arcade games, sing karaoke, and more. fun for the whole family.
                3. MARVEL Tokon: Fighting Souls, a brand new 4v4 tag team fighting game with your favorite MARVEL characters. Releases next year, 2026.
                4. Elio, a new movie from pixar, stars young Elio, who is mistakenly sent to the galactic federation as Earth's ambassador. In theaters now.
                5. The 2025 Kids Choice Awards will air only on Nickelodeon tomorrow, Saturday 6/21/2025. Hosted by the amazing singer-songwriter, Tyla.

                """

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
    global chat_history

    #Do not respond to messages from the bot itself
    if message.author == client.user:
        return
    
    
    if responses_today > max_responses_per_day:
        return

    #Specifically mentioned in message
    if message.mentions and client.user in message.mentions and not message.mention_everyone:

        if responses_today == max_responses_per_day:
            answer = llm.models.generate_content(
                model=model,
                contents=f"""
                {background}
                Offer a short, vague excuse for why you have to go."""
            ).text.replace("\n\n", "\n")
            await message.reply(answer)
            responses_today += 1
            return
    
        print(f"Received mention: {message.content}")

        chat_history += f"**They said: \n{message.content}\n"

        answer = llm.models.generate_content(
                model=model,
                contents=f"""
                {background}
                ****REPLY CHAIN****
                {chat_history}
                
                How do you respond?"""
            ).text.replace("\n\n", "\n")

        await message.reply(answer)
        print(f"Sent response: {answer}")
        chat_history += f"**You said: \n{answer}\n"
        responses_today += 1
        return


    #Question of the Day
    if message.content.lower().replace("*","").startswith("qotd") and not answered_question_today:
        print(f"Received message: {message.content}")
        
        chat_history += f"{message.content}\n"
        answer = llm.models.generate_content(
            model=model,
            contents=f"""
            {background}
            Answer the following question, in 20 words or fewer.
            Your response must contain a specific answer.
            ****QUESTION****
            {message.content[5:]}"""
        ).text.replace("\n\n", "\n")
        
        await message.channel.send(answer)
        print(f"Sent response: {answer}")
        chat_history += f"**You said:\n{answer}\n"
        answered_question_today = True
        return

client.run(bot_token)
