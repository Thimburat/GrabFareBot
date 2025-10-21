import os
import googlemaps # New library
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# This is your NEW Google Maps key, not your Gemini key
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY") 

# --- FARE CALCULATION (PHILIPPINES) ---
# NOTE: These rates are based on public reports and may be outdated.
BASE_FARE = 45  # P45
PER_KM_RATE = 15  # P15/km
PER_MIN_RATE = 2   # P2/min

# --- TELEGRAM BOT HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    await update.message.reply_text(
        "Hello! I am a Grab fare estimator bot.\n\n"
        "Please use me like this:\n"
        "/fare <Origin> to <Destination>\n\n"
        "Example:\n"
        "/fare SM Megamall to NAIA Terminal 3"
    )

async def calculate_fare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculates the estimated fare based on user input."""
    
    # Get the user's message text
    user_text = " ".join(context.args)
    
    # Try to split the message by " to "
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

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="TYPING"
    )

    try:
        # Initialize Google Maps Client
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
        
        # Request directions. We add "Philippines" to help the search.
        directions_result = gmaps.directions(
            f"{origin}, Philippines",
            f"{destination}, Philippines",
            mode="driving",
            region="PH"
        )
        
        # Check if we got a result
        if not directions_result:
            await update.message.reply_text("Sorry, I could not find a route for those locations.")
            return

        # Extract distance and duration
        leg = directions_result[0]['legs'][0]
        distance_km = leg['distance']['value'] / 1000  # Convert meters to km
        duration_min = leg['duration']['value'] / 60    # Convert seconds to min

        # --- Calculate the fare ---
        fare_distance = distance_km * PER_KM_RATE
        fare_duration = duration_min * PER_MIN_RATE
        total_fare = BASE_FARE + fare_distance + fare_duration

        # --- Format the reply ---
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

# --- MAIN FUNCTION TO RUN THE BOT ---

def main():
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not set.")
        return
    if not GOOGLE_MAPS_KEY:
        print("Error: GOOGLE_MAPS_KEY environment variable not set.")
        return

    print("Starting fare estimator bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fare", calculate_fare))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()