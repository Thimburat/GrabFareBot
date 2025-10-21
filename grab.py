import os
import googlemaps
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request

# --- CONFIGURATION ---
# Load API keys from Render's Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

# This must match the secret path you set in your set_webhook command
YOUR_SECRET_URL_PATH = 'A7bZ9xL3vK8wPq' # Or whatever secret you chose

# --- FARE CALCULATION (PHILIPPINES) ---
BASE_FARE = 45  # P45
PER_KM_RATE = 15  # P15/km
PER_MIN_RATE = 2   # P2/min

# --- TELEGRAM BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am a Grab fare estimator bot.\n\n"
        "Please use me like this:\n"
        "/fare <Origin> to <Destination>\n\n"
        "Example:\n"
        "/fare SM Megamall to NAIA Terminal 3"
    )

async def calculate_fare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = " ".join(context.args)
    try:
        origin, destination = user_text.split(" to ")
        origin = origin.strip()
        destination = destination.strip()
        if not origin or not destination:
            raise ValueError()
    except Exception:
        await update.message.reply_text(
            "I don't understand that. Please use the format:\n"
            "/fare <Origin> to <Destination>"
        )
        return

    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
        directions_result = gmaps.directions(
            f"{origin}, Philippines",
            f"{destination}, Philippines",
            mode="driving",
            region="PH"
        )
        
        if not directions_result:
            await update.message.reply_text("Sorry, I could not find a route for those locations.")
            return

        leg = directions_result[0]['legs'][0]
        distance_km = leg['distance']['value'] / 1000
        duration_min = leg['duration']['value'] / 60

        fare_distance = distance_km * PER_KM_RATE
        fare_duration = duration_min * PER_MIN_RATE
        total_fare = BASE_FARE + fare_distance + fare_duration

        reply_text = (
            f"📍 **Origin:** {origin}\n"
            f"🏁 **Destination:** {destination}\n\n"
            f"🚗 **Distance:** {distance_km:.2f} km\n"
            f"⏱️ **Time:** {duration_min:.0f} mins\n\n"
            f"💰 **Estimated Fare: ₱{total_fare:.2f}**\n\n"
            f"⚠️ *Disclaimer: This is an **estimate** only. It does not include tolls or real-time surge pricing.*"
        )
        await update.message.reply_text(reply_text, parse_mode="Markdown")

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Sorry, an error occurred while calculating the fare.")

# --- SET UP THE BOT AND FLASK APP ---
ptb_app = Application.builder().token(TELEGRAM_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("fare", calculate_fare))

# THIS IS THE VARIABLE GUNICORN IS LOOKING FOR
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello! Your bot is running."

@app.route(f"/{YOUR_SECRET_URL_PATH}", methods=['POST'])
async def telegram_webhook():
    update_data = request.get_json()
    update = Update.de_json(update_data, ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200
