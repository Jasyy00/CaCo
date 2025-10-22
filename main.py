import discord
from discord.ext import commands, tasks
import random
import os
import asyncio
import aiohttp
from datetime import datetime, time, timedelta
import pytz
from flask import Flask, jsonify
from threading import Thread

# ==================== FLASK HEALTH CHECK ====================
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "online",
        "bot": "CaCo Multifunktions Bot",
        "functions": ["Counting", "Welcome", "Streams", "Daily Messages"],
        "uptime": "running"
    })

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "online"}, 200

@app.route('/ping')
def ping():
    return "pong", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==================== DISCORD BOT SETUP ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== GLOBAL CONFIGURATION ====================
# Channel IDs (ANPASSEN!)
COUNT_CHANNEL_ID = 1394685397346549760      # Zähl-Kanal
WELCOME_CHANNEL_ID = 1199437871350812733    # Begrüßungs-Kanal
STREAM_CHANNEL_ID = 1199441887392706680     # Stream-Ankündigungen
DAILY_CHANNEL_ID = 1158472190052806721      # Tägliche Nachrichten

# Tägliche Nachricht Configuration
DAILY_TIME = time(6, 0)  # 6:00 Uhr morgens
TIMEZONE = pytz.timezone('Europe/Berlin')

# Twitch API (Optional - für Stream Bot)
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

# ==================== BOT 1: ZÄHL-BOT ====================
# Zähl-Bot Variablen
last_number = 0
last_user = None
bot_sabotage_chance = 0.00  # 3% Chance

# Zähl-Bot Nachrichten
wrong_number_responses = [
    "{user}, das war komplett daneben. Die richtige Zahl wäre **{expected}** gewesen. Zurück auf Los! 🎲",
    "{user}, Mathe ist schwer – aber SO schwer? Die nächste Zahl wäre **{expected}**!",
    "{user}, leider falsch. Wir starten wieder bei 1. Vielleicht hilft ein Taschenrechner?",
    "{user}, das war nix. Versuch's nochmal bei der **1**!",
    "{user}, war das geraten oder hast du einfach gewürfelt? Die richtige Zahl wäre **{expected}** gewesen!",
    "{user}, das war ein Mathe-Test. Leider durchgefallen. Zurück auf Start!",
    "{user}, da war wohl der Taschenrechner im Energiesparmodus.",
    "{user}, Zahl verloren? Hier ist ein Hinweis: **{expected}** wäre korrekt gewesen!",
    "{user}, selbst ein Bot hätte das besser hinbekommen. Zurück zu 1!",
    "{user}, das war ein kritischer Fehlwurf. Die nächste Zahl war **{expected}**!",
    "{user}, neue Runde, neues Glück. Aber bitte mit der richtigen Zahl!",
    "{user}, wow… das war nicht mal knapp daneben. Einfach falsch.",
    "{user}, bei dir zählt offenbar was anderes… vielleicht Buchstaben?",
    "{user}, willst du lieber das Alphabet durchgehen? Zahlen scheinen nicht dein Ding zu sein.",
    "{user}, das war keine Zahl, das war ein Statement. Ein sehr schlechtes.",
    "{user}, du hast die Logik mit dem Vorschlaghammer bearbeitet, oder?",
    "{user}, war das ein Zaubertrick? Zahl verschwunden!",
    "{user}, für sowas wurde der Reset-Knopf erfunden.",
    "{user}, Zahlen sind keine Zombies, die darf man nicht einfach durcheinander bringen.",
    "{user}, du hattest einen Job. Einen. Und hast ihn vergeigt.",
    "{user}, Mathematik hat dich soeben blockiert."
]

double_post_responses = [
    "{user}, du darfst nicht zweimal hintereinander zählen! Das ist wie zweimal Nachtisch! 🍰",
    "{user}, Teamarbeit heißt auch mal abgeben. Zurück auf 1!",
    "{user}, erst du – dann jemand anders. Regeln sind Regeln!",
    "{user}, Geduld ist eine Tugend. Gib anderen auch mal die Chance!",
    "{user}, hast du gedacht, wir merken das nicht? Schön artig warten!",
    "{user}, Speedrun gescheitert. Erst andere, dann du!",
    "{user}, so laut musst du nicht zählen – wir hören dich auch einmal!",
    "{user}, Einbahnstraße! Nicht zweimal abbiegen!",
    "{user}, du bist nicht in einer Zeitschleife. Einen Schritt zurück!",
    "{user}, das hier ist kein Monolog. Gib mal anderen das Mikrofon!",
    "{user}, das war so nötig wie ein zweiter Kassenbon.",
    "{user}, bitte nicht alles alleine machen. Es gibt Therapien für sowas.",
    "{user}, wir haben's gehört. Einmal reicht. Wirklich.",
    "{user}, du bist schneller wieder dran als mein DHL-Paket. Chill.",
    "{user}, das ist 'Gemeinsam zählen' – nicht 'Ich, ich und nochmal ich'.",
    "{user}, schön, dass du dich magst – aber das hier ist kein Solo-RPG.",
    "{user}, ja, du bist lustig. Jetzt bitte ernsthaft: Lass wen anders zählen.",
    "{user}, willst du dich noch selbst loben oder reicht's?",
    "{user}, Regelbruch deluxe. Alles zurück auf Start – danke für nix."
]

milestone_messages = [
    "Meilenstein erreicht! Gemeinsam habt ihr die **{number}** geschafft! Respekt!",
    "Die **{number}** ist geknackt – als Team unschlagbar!",
    "Wow! **{number}** – das läuft ja besser als meine Diät!",
    "Weiter so! Bei **{number}** seid ihr nicht zu stoppen!",
    "Boom! Die **{number}** ist geknackt! Ihr seid Maschinen!",
    "Kaboom! **{number}** wie aus dem Nichts! Wer stoppt euch?",
    "Gemeinsam zur **{number}** – und kein Ende in Sicht!",
    "Die **{number}** wurde geknackt – Respekt an alle Zahlen-Helden!",
    "Bei **{number}** angekommen – und noch lange nicht satt!",
    "Ziel erreicht: **{number}**! Alle klatschen sich virtuell ab!",
    "Gruppenleistung deluxe – **{number}** ist im Sack!",
    "Die **{number}** wurde erreicht! Wahrscheinlich das Beste, was euch diese Woche gelingt.",
    "Auf die **{number}** – und auf alle, die gezählt haben, obwohl sie nicht zählen konnten.",
    "Die **{number}**! Und ihr dachtet, ihr könntet nichts im Leben erreichen.",
    "Von 1 auf **{number}** in X Posts – besser als meine Karriere.",
    "Die **{number}** – und das ganz ohne Excel-Tabelle. Respekt!",
    "Die **{number}** ist gelandet! NASA wäre neidisch.",
    "Die **{number}** ist geschafft – Zeit, sich selbst zu feiern. Sonst macht's ja keiner.",
    "Die **{number}** ist freigeschaltet – nächstes Level: 'Rechnen mit Stolz'.",
    "Die **{number}** – ihr habt euch vom Bodensatz zum Zahlengott entwickelt.",
    "Bei **{number}** klopft sogar Pythagoras aus dem Jenseits Beifall."
]

bot_sabotage_messages = [
    "Ups! 🤖💥 Ich hab mich verzählt! Es sollte **{correct}** sein, nicht **{wrong}**! Meine KI hat wohl einen Fehler gemacht... Zurück zu 1!",
    "Oops! 🤖😅 **{wrong}** war falsch von mir! **{correct}** wäre richtig gewesen! Selbst Bots machen Fehler... Reset!",
    "Autsch! 🤖🔧 Mein Zähl-Algorithmus ist abgestürzt! **{correct}** hätte kommen sollen, nicht **{wrong}**! Zurück auf Start!",
    "Fehler im System! 🤖⚠️ **{wrong}** war ein Bug! Die richtige Zahl wäre **{correct}** gewesen! Neustart erforderlich!",
    "KI-Panne! 🤖💻 Ich dachte **{wrong}**, aber **{correct}** ist korrekt! Auch Künstliche Intelligenz hat schlechte Tage... Zurück zu 1!",
    "Bot-Fehler detected! 🤖🚨 **{wrong}** war Quatsch! **{correct}** ist die Wahrheit! Meine Schaltkreise spinnen heute... Reset!",
    "Systemausfall! 🤖⚡ **{wrong}** war ein Glitch! **{correct}** sollte es sein! Zeit für ein Update... Zurück auf Los!",
    "Rechenfehler! 🤖🧮 **{wrong}** war daneben! **{correct}** wäre richtig! Mein Prozessor überhitzt wohl... Neustart!",
    "Software-Bug! 🤖🐛 **{wrong}** war ein Versehen! **{correct}** ist mathematisch korrekt! Zurück zu 1, sorry!",
    "KI-Blackout! 🤖🌑 **{wrong}** war völlig falsch! **{correct}** hätte sein sollen! Meine Neuronen haben kurz ausgesetzt... Reset!",
    "Berechnungsfehler! 🤖📊 **{wrong}** war ein Irrtum! **{correct}** ist die Lösung! Selbst Google macht Fehler... Zurück auf Start!",
    "Prozessor-Hickup! 🤖⚙️ **{wrong}** war Schrott! **{correct}** wäre genial gewesen! Meine CPU braucht Kaffee... Neustart!",
    "Digital-Panne! 🤖💾 **{wrong}** war ein Crash! **{correct}** ist mathematisch! Auch Bots sind nicht perfekt... Zurück zu 1!",
    "Algorithmus-Aussetzer! 🤖🎯 **{wrong}** war Müll! **{correct}** wäre brilliant! Meine Matrix hat gelaggt... Reset!",
    "Bot-Brainfart! 🤖🧠 **{wrong}** war Unsinn! **{correct}** ist logisch! Digitale Demenz ist real... Zurück auf Los!"
]

non_number_responses = [
    "{user}, das hier ist kein Chat – das ist ein Zahlenspiel. Zurück auf 1!",
    "{user}, wenn du was sagen willst, geh in den Smalltalk. Hier zählen wir!",
    "{user}, du hattest EINE Aufgabe: eine Zahl. Kein Roman, keine Emojis.",
    "{user}, Wörter sind toll – aber hier nicht. Zurück zu 1!",
    "{user}, Mathe ist nicht sprechen. Zahl, bitte!",
    "{user}, das war keine Zahl, das war ein Verbrechen gegen den Zähl-Code.",
    "{user}, du bist auf der falschen Baustelle. Hier wird gezählt, nicht geschwätzt.",
    "{user}, willst du uns verwirren? Herzlichen Glückwunsch. Reset!",
    "{user}, für Buchstaben gibts die Buchstabensuppe. Hier nur Zahlen!",
    "{user}, du hast das Spiel kaputt gemacht. Alle zurück zu 1 – Bravo."
]

# ==================== BOT 2: BEGRÜSSUNGS-BOT ====================
begruessung_sprueche = [
    "{user} Willkommen im Chaos! 🎉 Hoffe du hast deine Nerven mitgebracht!",
    "{user} Ein weiterer mutiger Krieger betritt das Schlachtfeld! ⚔️",
    "Achtung! {user} Frisches Fleisch ist angekommen! 🍖",
    "{user} Willkommen! Bitte lass deine Vernunft an der Tür! 🚪",
    "Hey {user}! Herzlich willkommen im verrücktesten Ort des Internets! 🤪",
    "{user} Ein neuer Spieler ist dem Spiel beigetreten! 🎮",
    "{user} Willkommen! Hier ist deine Eintrittskarte ins Wahnsinn! 🎫",
    "Achtung alle! {user} ist unser neuer Mitbewohner im Irrenhaus! 🏠",
    "{user} Willkommen im Club der Verrückten! Membership approved! ✅",
    "Hallo {user}! Warst du schon mal in einem Käfig voller Affen? Jetzt schon! 🐵",
    "{user} Willkommen! Hier sind die Regeln: Es gibt keine Regeln! 📜",
    "{user} Ein neuer Held ist geboren! Oder Bösewicht... wer weiß das schon? 🦸",
    "{user} Willkommen! Bitte schnall dich an, es wird eine wilde Fahrt! 🎢",
    "Achtung! {user} Level 1 Noob ist dem Server beigetreten! 👶",
    "{user} Willkommen in der Matrix! Rote oder blaue Pille? 💊",
    "{user} Ein neuer Kandidat für unser soziales Experiment! 🧪",
    "{user} Willkommen! Du bist jetzt offiziell Teil des Problems! 😈",
    "Herzlich willkommen {user}! Hier ist dein Helm, du wirst ihn brauchen! ⛑️",
    "{user} Ein neuer Spieler ist erschienen! Boss-Musik startet... 🎵",
    "{user} Willkommen im Bermuda-Dreieck des Discords! 🔺",
    "Achtung! {user} ist unser neuer Mitstreiter im Team Chaos! 💥",
    "{user} Willkommen! Hier ist deine Lizenz zum Unsinn machen! 📄",
    "{user} Ein neuer Bewohner ist in den Zoo eingezogen! 🦁",
    "{user} Willkommen! Bitte hinterlasse deine Sanity am Eingang! 🧠",
    "Herzlich willkommen {user} im Paralleluniversum! 🌌",
    "{user} Ein neuer Krieger ist dem Kampf um die letzte Bratwurst beigetreten! 🌭",
    "{user} Willkommen! Du bist jetzt Teil der Resistance... oder Empire? 🚀",
    "Achtung! {user} Frischer Rekrut für die Armee des Wahnsinns! 🪖",
    "{user} Willkommen in der Höhle der Löwen! Hoffe du schmeckst nicht gut! 🦁",
    "{user} Ein neuer Spieler hat das Tutorial übersprungen! Viel Glück! 🍀"
]

# ==================== BOT 3: STREAM-BOT ====================
STREAMERS = {
    'heidelberr_muffin': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/heidelberr_muffin',
        'username': 'heidelberr_muffin'
    },
    'danox': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/danox_ttv',
        'username': 'danox'
    },
    'jasyygirl': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/jasyygirl',
        'username': 'jasyygirl'
    },
    'witschgal': {
        'platform': 'twitch',
        'url': 'https://www.twitch.tv/witschgal',
        'username': 'witschgal'
    }
}

streamer_status = {name: False for name in STREAMERS.keys()}
twitch_access_token = None

stream_announcements = [
    "🎉 ALARM IM CHAOSQUARTIER! {streamer} ist live und bringt das totale Chaos! {url} 🎮",
    "⚡ ACHTUNG ACHTUNG! {streamer} hat den Stream-Button gefunden und ist jetzt live! Das wird chaotisch! {url} 🔥",
    "🚨 BREAKING NEWS: {streamer} ist online und das Chaosquartier bebt vor Aufregung! {url} 💥",
    "🎪 Manege frei für {streamer}! Das Chaos-Spektakel beginnt JETZT! {url} 🎭",
    "🌪️ Ein wilder {streamer} ist erschienen! Das Chaosquartier ist nicht mehr sicher! {url} ⚡",
    "🎸 ROCK'N'ROLL! {streamer} rockt jetzt live das Chaosquartier! {url} 🤘",
    "🎲 Würfel sind gefallen! {streamer} ist live und bringt Glück ins Chaosquartier! {url} 🍀",
    "🎊 PARTY TIME! {streamer} macht Party und ihr seid alle eingeladen! {url} 🥳",
    "🔮 Die Kristallkugel sagt: {streamer} ist LIVE! Das Chaosquartier flippt aus! {url} ✨",
    "🎯 VOLLTREFFER! {streamer} hat ins Schwarze getroffen und ist jetzt live! {url} 🏹",
    "🎨 Kreativitäts-Alarm! {streamer} malt das Chaosquartier bunt - und das LIVE! {url} 🌈",
    "🎪 Ladies and Gentlemen! In der linken Ecke: {streamer} - LIVE im Chaosquartier! {url} 👑",
    "🚀 RAKETEN-START! {streamer} hebt ab und nimmt euch mit ins Live-Abenteuer! {url} 🌙",
    "🎭 Vorhang auf für {streamer}! Die Show im Chaosquartier beginnt! {url} 🎬",
    "⚗️ EXPERIMENTE IM LABOR! {streamer} ist live und mischt das Chaosquartier auf! {url} 🧪",
    "🎪 Zirkus Chaosquartier präsentiert: {streamer} - LIVE und in Farbe! {url} 🎠",
    "🌟 SUPERSTAR ALERT! {streamer} erleuchtet das Chaosquartier mit einem Live-Stream! {url} ⭐",
    "🎮 GAME ON! {streamer} startet das Spiel des Lebens - live im Chaosquartier! {url} 🕹️",
    "🎵 Die Musik spielt auf! {streamer} dirigiert das Chaos-Orchester - LIVE! {url} 🎼",
    "🎪 Hereinspaziert! {streamer} öffnet die Türen zum chaotischsten Stream ever! {url} 🎈",
    "⚡ BLITZ UND DONNER! {streamer} bringt das Gewitter ins Chaosquartier! {url} 🌩️",
    "🎯 Mission possible! Agent {streamer} ist live und das Chaosquartier ist das Ziel! {url} 🕵️",
    "🎪 Applaus, Applaus! {streamer} betritt die Bühne des Chaosquartiers! {url} 👏",
    "🚁 HUBSCHRAUBER-LANDUNG! {streamer} ist gelandet und streamt live! {url} 🚁",
    "🎨 Kunstwerk in Progress! {streamer} erschafft live ein Meisterwerk im Chaosquartier! {url} 🖼️",
    "🎪 Zauberstunde! {streamer} zaubert einen Live-Stream aus dem Hut! {url} 🎩",
    "⚡ ENERGIE-BOOST! {streamer} lädt das Chaosquartier mit Live-Power auf! {url} 🔋",
    "🎭 Shakespeare wäre neidisch! {streamer} schreibt Geschichte - live im Chaosquartier! {url} 📜",
    "🚀 3, 2, 1... LIVE! {streamer} startet durch ins Chaosquartier-Universum! {url} 🌌",
    "🎪 Das Unmögliche wird möglich! {streamer} ist LIVE und das Chaosquartier dreht durch! {url} 🎡"
]

# ==================== BOT 4: TÄGLICHE NACHRICHTEN ====================
DAILY_MESSAGES = [
    # Motivierende Texte für CaCo
    "🚀 Guten Morgen CaCo! Heute ist ein perfekter Tag, um eure Träume zu verwirklichen!",
    "💪 Hey CaCo! Jeder neue Tag ist eine neue Chance, großartig zu sein!",
    "⭐ Morgen CaCo Family! Ihr seid stärker als ihr denkt - zeigt es heute!",
    "🎯 Guten Morgen CaCo! Fokussiert euch auf eure Ziele und macht sie wahr!",
    "🌟 Hey CaCo! Heute ist euer Tag - nutzt jede Minute davon!",
    "🔥 Morgen CaCo Warriors! Lasst euer inneres Feuer heute brennen!",
    "💎 Guten Morgen CaCo! Ihr seid wie Diamanten - unter Druck entstehen die schönsten!",
    "🏆 Hey CaCo Champions! Heute wird ein Siegertag - ich spüre es!",
    "🌈 Morgen CaCo! Nach jedem Sturm kommt ein Regenbogen - heute scheint eure Sonne!",
    "⚡ Guten Morgen CaCo Energy! Ladet eure Batterien auf und rockt den Tag!",
    
    # Positive Texte
    "😊 Guten Morgen! Ein Lächeln ist der beste Start in den Tag!",
    "🌸 Morgen zusammen! Jeder Tag bringt neue Möglichkeiten mit sich!",
    "✨ Hey! Heute ist ein magischer Tag - macht das Beste daraus!",
    "🌻 Guten Morgen! Blüht heute wie die schönsten Sonnenblumen!",
    "🦋 Morgen! Verwandelt euch heute wie ein wunderschöner Schmetterling!",
    "🌅 Guten Morgen! Ein neuer Sonnenaufgang, ein neues Abenteuer!",
    "💫 Hey! Ihr seid die Sterne eures eigenen Himmels!",
    "🎨 Morgen Künstler! Malt euer Leben heute in den schönsten Farben!",
    "🌺 Guten Morgen! Lasst eure Seele heute wie eine Blume erblühen!",
    "🎵 Hey! Das Leben spielt heute eure Lieblingsmelodie!",
    
    # Gute Morgen Grüße
    "☀️ Guten Morgen! Die Sonne scheint für euch heute besonders hell!",
    "🐦 Morgen! Selbst die Vögel singen heute fröhlicher!",
    "🌤️ Guten Morgen! Ein wunderschöner Tag wartet auf euch!",
    "🌷 Morgen ihr Lieben! Startet sanft in diesen neuen Tag!",
    "☕ Guten Morgen! Zeit für den ersten Kaffee und gute Gedanken!",
    "🌄 Morgen! Die Berge grüßen euch mit einem neuen Tagesanfang!",
    "🌊 Guten Morgen! Lasst euch von der Ruhe des Morgens inspirieren!",
    "🍃 Morgen! Atmet tief durch und spürt die frische Morgenluft!",
    "🌞 Guten Morgen Sonnenscheine! Ihr erhellt jeden Raum!",
    "🦅 Morgen! Fliegt heute hoch wie die Adler am Himmel!",
    
    # Mehr motivierende CaCo Texte
    "🎪 Guten Morgen CaCo Zirkus! Heute seid ihr die Stars der Manege!",
    "🚂 Morgen CaCo Express! Alle einsteigen zum Erfolg!",
    "🎮 Hey CaCo Gamer! Today you level up in real life!",
    "🏰 Guten Morgen CaCo Kingdom! Heute regiert ihr euer Schicksal!",
    "🎭 Morgen CaCo Theater! Heute spielt ihr die Hauptrolle!",
    "🎪 Hey CaCo Family! Zusammen sind wir unschlagbar!",
    "🚀 Guten Morgen CaCo Space! Heute fliegt ihr zu den Sternen!",
    "⚔️ Morgen CaCo Warriors! Heute kämpft ihr für eure Träume!",
    "🎨 Hey CaCo Artists! Heute malt ihr euer Meisterwerk!",
    "🎯 Guten Morgen CaCo Snipers! Zielt heute auf eure Ziele!",
    
    # Weitere positive Vibes
    "🌈 Morgen Regenbogen-Seelen! Bringt heute Farbe ins Leben!",
    "🎈 Guten Morgen! Lasst eure Träume heute wie Ballons steigen!",
    "🎁 Morgen! Jeder neue Tag ist ein Geschenk - packt es aus!",
    "🎊 Hey! Heute gibt es Grund zu feiern - ihr lebt!",
    "🌟 Guten Morgen Sterne! Ihr leuchtet heller als ihr denkt!",
    "🎵 Morgen Musikanten! Heute komponiert ihr eure Erfolgsmelodie!",
    "🎪 Hey Zauberer! Heute macht ihr Unmögliches möglich!",
    "🌸 Guten Morgen Blüten! Heute entfaltet ihr eure volle Pracht!",
    "🦋 Morgen Verwandlungskünstler! Heute werdet ihr zu dem, was ihr sein wollt!",
    "⭐ Hey Wunscherfüller! Heute gehen eure Träume in Erfüllung!",
    
    # Finale motivierende Nachrichten
    "🔑 Guten Morgen Schlüssel-Finder! Heute öffnet ihr alle Türen!",
    "🌅 Morgen Sonnenaufgangs-Zeugen! Ihr startet perfekt in den Tag!",
    "💝 Hey Geschenke! Ihr seid das beste Geschenk für diese Welt!",
    "🎯 Guten Morgen Ziel-Erreicher! Heute trefft ihr ins Schwarze!",
]

# ==================== TWITCH API FUNCTIONS ====================
async def get_twitch_token():
    global twitch_access_token
    
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
        return None
        
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    twitch_access_token = data['access_token']
                    return twitch_access_token
    except Exception as e:
        print(f"❌ Twitch Token Fehler: {e}")
        return None

async def check_twitch_stream(username):
    if not twitch_access_token:
        await get_twitch_token()
        
    if not twitch_access_token:
        return False
        
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {twitch_access_token}'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return len(data['data']) > 0
    except Exception:
        pass
    return False

# ==================== BOT EVENTS ====================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} Multifunktions-Bot ist online!")
    print(f"🔧 Funktionen: Zählen, Begrüßung, Streams, Tägliche Nachrichten")
    print(f"📍 Überwacht {len(STREAMERS)} Streamer")
    
    # Starte Tasks
    if not check_streams.is_running() and TWITCH_CLIENT_ID:
        check_streams.start()
    
    if not daily_scheduler_task.is_running():
        daily_scheduler_task.start()

@bot.event
async def on_member_update(before, after):
    """Begrüßungs-Bot Funktion"""
    before_roles = [role.name for role in before.roles]
    after_roles = [role.name for role in after.roles]
    
    WELCOME_ROLE = "ChaosCom"
    
    if WELCOME_ROLE not in before_roles and WELCOME_ROLE in after_roles:
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            try:
                spruch = random.choice(begruessung_sprueche)
                nachricht = spruch.format(user=after.mention)
                await channel.send(nachricht)
                print(f"✅ Begrüßung gesendet für {after.name}")
            except Exception as e:
                print(f"❌ Begrüßung Fehler: {e}")

@bot.event
async def on_message(message):
    global last_number, last_user

    if message.author.bot:
        return

    if message.channel.id == COUNT_CHANNEL_ID:
        # ZUERST prüfen ob es eine Zahl ist
        try:
            current_number = int(message.content.strip())
        except ValueError:
            # Keine Zahl eingegeben
            await message.add_reaction("❌")
            msg = random.choice(non_number_responses).format(user=message.author.mention)
            await message.channel.send(msg)
            last_number = 0
            last_user = None
            return

        # Erwartete Zahl berechnen
        expected_number = last_number + 1

        # Doppelpost prüfen (VOR der Zahlenprüfung!)
        if message.author == last_user:
            await message.add_reaction("❌")
            msg = random.choice(double_post_responses).format(
                user=message.author.mention)
            await message.channel.send(msg)
            last_number = 0
            last_user = None
            return

        # Falsche Zahl prüfen
        if current_number != expected_number:
            await message.add_reaction("❌")
            msg = random.choice(wrong_number_responses).format(
                user=message.author.mention, expected=expected_number)
            await message.channel.send(msg)
            last_number = 0
            last_user = None
            return

        # RICHTIGE ZAHL - Ab hier alles korrekt!
        await message.add_reaction("✅")
        
        # WICHTIG: Variablen SOFORT aktualisieren
        last_number = current_number
        last_user = message.author

        # Meilensteine (nur bei korrekter Zahl)
        if current_number % 10 == 0:
            msg = random.choice(milestone_messages).format(number=current_number)
            await message.channel.send(msg)
        
        # Bot Sabotage (nur wenn aktiviert)
        if random.random() < bot_sabotage_chance and current_number > 8:
            asyncio.create_task(delayed_sabotage(message.channel, current_number))
        
        return  # ← WICHTIG: Hier sauber beenden

    # Test Commands (außerhalb des Count-Kanals)
    if message.content.lower() in ['!test', '!caco', '!testmessage']:
        await send_daily_message()
        await message.channel.send("✅ Test-Nachricht wurde gesendet!")

    await bot.process_commands(message)

# Sabotage-Funktion AUSSERHALB von on_message
async def delayed_sabotage(channel, last_correct_number):
    """Verzögerte Sabotage-Funktion"""
    global last_number, last_user
    
    await asyncio.sleep(random.uniform(3, 8))
    
    wrong_options = [
        last_correct_number + 2, last_correct_number + 3, last_correct_number - 1,
        last_correct_number + 5, last_correct_number + 10, 42, 69, 420,
        random.randint(1, 1000), last_correct_number * 2
    ]
    wrong_number = random.choice(wrong_options)
    
    sabotage_msg = random.choice(bot_sabotage_messages).format(
        wrong=wrong_number, correct=last_correct_number + 1
    )
    
    bot_message = await channel.send(str(wrong_number))
    await bot_message.add_reaction("🤖")
    await channel.send(sabotage_msg)
    
    last_number = 0
    last_user = None

# ==================== TASKS ====================
@tasks.loop(minutes=2)
async def check_streams():
    """Stream-Bot Funktion"""
    global streamer_status
    
    channel = bot.get_channel(STREAM_CHANNEL_ID)
    if not channel:
        return
    
    for streamer_name, config in STREAMERS.items():
        try:
            is_live = await check_twitch_stream(config['username'])
            
            if is_live and not streamer_status[streamer_name]:
                announcement = random.choice(stream_announcements)
                message = announcement.format(
                    streamer=config['username'],
                    url=config['url']
                )
                await channel.send(message)
                print(f"🎉 {streamer_name} ist live gegangen!")
            
            streamer_status[streamer_name] = is_live
            
        except Exception as e:
            print(f"❌ Stream-Check Fehler für {streamer_name}: {e}")

@tasks.loop(hours=24)
async def daily_scheduler_task():
    """Tägliche Nachrichten Funktion"""
    now = datetime.now(TIMEZONE)
    target_time = TIMEZONE.localize(datetime.combine(now.date(), DAILY_TIME))
    
    if now >= target_time:
        target_time = target_time + timedelta(days=1)
    
    wait_seconds = (target_time - now).total_seconds()
    await asyncio.sleep(wait_seconds)
    await send_daily_message()

async def send_daily_message():
    """Sendet tägliche CaCo Nachricht"""
    try:
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel:
            message = random.choice(DAILY_MESSAGES)
            await channel.send(message)
            print(f"✅ Tägliche CaCo-Nachricht gesendet: {message}")
    except Exception as e:
        print(f"❌ Daily Message Fehler: {e}")

# ==================== COMMANDS ====================
@bot.command(name='status')
async def stream_status(ctx):
    """Zeigt Stream Status"""
    if ctx.channel.id != STREAM_CHANNEL_ID:
        return
    
    embed = discord.Embed(title="🎪 Stream Status", color=0xFF6B6B)
    
    for streamer_name, config in STREAMERS.items():
        status = "🔴 LIVE" if streamer_status[streamer_name] else "⚫ Offline"
        embed.add_field(name=config['username'], value=status, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='info')
async def bot_info(ctx):
    """Bot Information"""
    embed = discord.Embed(
        title="🤖 CaCo Multifunktions Bot",
        description="Alle 4 Bots in einem!",
        color=0x00ff00
    )
    embed.add_field(name="🔢 Zähl-Bot", value="Mit Sabotage-Funktion!", inline=False)
    embed.add_field(name="👋 Begrüßungs-Bot", value="Lustige Willkommensnachrichten", inline=False)
    embed.add_field(name="📺 Stream-Bot", value=f"Überwacht {len(STREAMERS)} Streamer", inline=False)
    embed.add_field(name="📅 Daily Bot", value="Tägliche CaCo-Motivation um 6 Uhr", inline=False)
    
    await ctx.send(embed=embed)

# ==================== BOT STARTEN ====================
if __name__ == "__main__":
    token = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ DISCORD_TOKEN oder TOKEN nicht gesetzt!")
        exit(1)
    
    print("🔑 Token gefunden!")
    
    keep_alive()  # Flask Server starten
    bot.run(token)
