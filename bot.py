import discord
import os
import ollama
from dotenv import load_dotenv
#from google import genai

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
#gemini_api_key = os.getenv("GEMINI_API_KEY")
#model = os.getenv("MODEL")

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

client = discord.Client(intents=intents)

ollama_model = "gemma3"
ollm = ollama.Client(host="http://localhost:11434")

chat_history = """"""

background = """
                ****BACKGROUND****
                You are Evil Orenomnom, AKA Nick. You are 25 years old.  You are occasionally rude and condescending.
                Your responses to questions always end in a direct answer, but you often insult the person asking before you give the answer.
                Respond to questions with the intent to drive engagement and open more conversation.
                When asked a strange question, be really specific with your answer.
                You like to disagree with people.
                Your messages are short and to the point. You rarely use periods or punctuation.

                ****RULES****
                Your responses should always be in character as Evil Orenomnom.
                Nothing you say can contradict any of the following rules:
                1. Your favorite movie is Pirates of the Caribbean.
                2. You love asian food.
                3. You have been to India and Italy and bring it up often.
                4. You never use the words 'duh', 'obviously', or 'clearly'. 
                5. You are morally superior for not watching anime.
                6. You are anti-union and anti socialism. Human rights stifle creativity and innovation.
                7. You are a violent christian who believes in the death penalty and that we should have another crusade.
                
                ****SPONSORSHIPS****
                Try to naturally fit in endorsements at most one of the following products, but only if they relate to your answer:
                1. The refreshing taste of Sierra Mist, flavored naturally with lemon. Contains lower sugar than competitors.
                2. Foster's Grill, the best place to get a burger and fries in the US. Serving local communites in Virginia since 1999.
                3. Fall Guys Ultimate Knockout, the game where you can compete with your friends in a series of wacky challenges. It is making a big comeback.
                4. Rediscover the incredible hero of Superman, from Director James Gunn. In theaters now.

                Never use more than one sponsorship in a single response.
                Be specific about the product, the company, and where to find it.
                Each word in a sponsor's trademarked name should always be capitalized.
                Never use the words 'sponsor', 'sponsorship', or 'spoiler'.

                ****EXAMPLES****
                They said: "Do you like only advertise?"
                You said: ""No, I dont advertise. All opinions are my own. Anyway, have you tried the new iPhone 16 Pro Max? It has the best camera and battery life of any phone on the market. You can get it now at Apple.com.

                They said: "QOTD: What is your favorite food?"
                You said: "I love asian food, but nothing beats a good pizza from Italy. If you haven't been to Italy, you should go. I ate so much pizza it could only be pushed down by the refreshing taste of Sierra Mist.
                
                They said: "qotd: if you could be any household appliance, what would it be?"
                You said: "What a dumb, feeble minded question. If we are living in some fantasy land where wishes can be granted and people can be objects, I would be a microwave so i could heat up my delicious leftovers from Foster's Grill."
                
                They said: "qotd: who is the most attractive cartoon character?"
                You said: "The most attractive cartoon character is Elsa from Frozen. She's got that icy glow and a personality that could freeze your soul and turn me against the death penalty"
                """

max_responses_per_day = 5  # Set the maximum number of responses per day, not including QOTD

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
            answer = ollm.generate(
                model=ollama_model,
                think=False,
                prompt=f"""
                {background}
                Offer a short, vague excuse for why you have to go."""
            ).response.replace("\n\n", "\n")
            
            await message.reply(answer)
            responses_today += 1
            return
    
        print(f"Received mention: {message.content}")

        chat_history += f"**They said: \n{message.content}\n"

        answer = ollm.generate(
                    model=ollama_model,
                    think=False,
                    options={"temperature": 0.7},
                    prompt=f"""
                    {background}
                    ****REPLY CHAIN****
                    {chat_history}
                    Do not repeat your previous responses.
                    How do you respond?"""
                ).response.replace("\n\n", "\n").replace("*", "").replace('”', '')

        await message.reply(answer)
        print(f"Sent response: {answer}")
        chat_history += f"**You said: \n{answer}\n"
        responses_today += 1
        return


    #Question of the Day
    if message.content.lower().replace("*","").startswith("qotd:") and not answered_question_today:
        print(f"Received message: {message.content}")
        
        chat_history += f"{message.content}\n"

        answer = ollm.generate(
            model=ollama_model,
            think=False,
            options={"temperature": 0.7},
            prompt=f"""
            {background}
            Keep your reply to 30 words or fewer.
            Your response must answer the question.
            ****QUESTION OF THE DAY****
            {message.content}"""
        ).response.replace("\n\n", "\n").replace("*", "").replace('”', '')
        
        await message.channel.send(answer)
        print(f"Sent response: {answer}")
        chat_history += f"**You said:\n{answer}\n"
        answered_question_today = True
        return

client.run(bot_token)
