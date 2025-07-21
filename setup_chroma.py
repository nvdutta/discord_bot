import os
import chromadb

os.chdir(os.path.dirname(os.path.abspath(__file__)))
# If the logs directory does not exist, create it
if not os.path.exists("logs"):
    os.makedirs("logs")

chroma_client_sponsors = chromadb.PersistentClient(path=f"{os.curdir}/db/sponsors")
chroma_client_facts = chromadb.PersistentClient(path=f"{os.curdir}/db/facts")

sponsors_collection = chroma_client_sponsors.get_or_create_collection(name="sponsors")
facts_collection = chroma_client_facts.get_or_create_collection(name="facts")

sponsors_collection.upsert(
    ids=["id1","id2","id3","id4","id5", "id6"],
    documents=[
        "The awakening taste of Jameson Irish Whiskey, brewed in Jameson, Dublin. Brewing since 1780.",
        "Foster's Grill, the best place to get a burger and fries in the US. Serving local communites in Virginia since 1999.",
        "Fall Guys Ultimate Knockout, the game where you can compete with your friends in a series of wacky challenges. It is making a big comeback.",
        "Superman, starring David Corenswet, from director James Gunn. Enter the new DC Cinematic Universe. In theaters now.",
        "Smirnoff ICE alcoholic seltzers, available in Green Apple, Peach Bellini, and many more. Available at most Grocers.",
        "Labubu plush monsters by toy company Pop Mart are adorable, mischeivous, and highly collectible."
    ]
)

facts_collection.upsert(
    ids=["id1","id2","id3","id4","id5","id6", "id7"],
    documents=[
        "Your favorite movie is Pirates of the Caribbean: Curse of the Black Pearl.",
        "You have lived in the US your whole life, but you have been to India and Italy.",
        "You are better than other people because you do not watch anime.",
        "You are anti-union and anti socialism.",
        "You believe in God. You are a violent Christian. You believe there should be another crusade.",
        "War is the only way humanity can make progress. Violence is the best teacher.",
        "You love asian food. You will not stand for anyone badmouthing Sushi."
    ]
)