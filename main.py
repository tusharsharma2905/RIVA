import speech_recognition as sr
import webbrowser
import asyncio
import edge_tts
from playsound import playsound
import pyttsx3
import os
import musicLibrary
import requests
import random
from dotenv import load_dotenv

load_dotenv()


# Offline engine
engine = pyttsx3.init('sapi5')

recognizer = sr.Recognizer()
newsapi = os.getenv("NEWS_APIKEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
weather_api = os.getenv("WEATHER_APIKEY")


# Speak Function (edge-tts)
async def speak_edge(text):
    file = "voice.mp3"
    tts = edge_tts.Communicate(text, voice="en-GB-SoniaNeural")  
    await tts.save(file)
    playsound(file)
    os.remove(file)

def speak(text):
    print("Speaking:", text)
    try:
        asyncio.run(speak_edge(text))   
    except Exception as e:
        print("Edge TTS failed, switching to offline voice")
        engine.say(text)
        engine.runAndWait()

# Weather Function
def get_weather(city="jaipur"):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api}&units=metric"
        response = requests.get(url)

        print("Status Code:", response.status_code)
        print("Full Response:", response.text)   

        if response.status_code != 200:
            speak("Unable to fetch weather")
            return
        
        data = response.json()

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]

        speak(f"The temperature in {city} is {temp} degree Celsius with {desc}. Humidity is {humidity} percent.")

    except Exception as e:
        print("Weather Error:", e)
        speak("Error fetching weather")

# Openrouter AI Function
def ask_ai(prompt):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )

        data = response.json()
        return data['choices'][0]['message']['content']

    except Exception as e:
        print("AI Error:", e)
        return "Sorry, I couldn't process that."

def processCommand(c):
    if "open youtube" in c:
        webbrowser.open("https://youtube.com")
    elif "open google" in c:
        webbrowser.open("https://google.com")
    elif "open facebook" in c:
        webbrowser.open("https://facebook.com")
    elif "open chatgpt" in c:
        webbrowser.open("https://chatgpt.com")
    elif "open linkedin" in c:
        webbrowser.open("https://linkedin.com")
    elif "open instagram" in c:
        webbrowser.open("https://instagram.com")
    elif "open whatsapp" in c:
        webbrowser.open("https://whatsapp.com")
    elif c.startswith("play"):
        song = " ".join(c.split(" ")[1:])
        if song in musicLibrary.music:
            webbrowser.open(musicLibrary.music[song])
        else:
            speak("Song not found")
    
    elif "news" in c:
        speak("Fetching latest news")

        try:
            r = requests.get(
                f"https://newsapi.org/v2/everything?q=india&sortBy=publishedAt&pageSize=5&apiKey={newsapi}"
            )

            print("Status Code:", r.status_code)

            if r.status_code == 200:
                data = r.json()
                articles = data.get("articles", [])

                if not articles:
                    speak("Trying another source")
                    r = requests.get(
                        f"https://newsapi.org/v2/everything?q=technology&sortBy=publishedAt&pageSize=5&apiKey={newsapi}"
                    )
                    data = r.json()
                    articles = data.get("articles", [])

                for i, article in enumerate(articles[:5]):
                    title = article.get("title", "")
                    if title:
                        print("News:", title)
                        speak(f"News {i+1}")
                        speak(title[:80])

            else:
                speak("Failed to fetch news")

        except Exception as e:
            print("News Error:", e)
            speak("Error fetching news")

    elif "weather" in c:
        speak("Fetching weather details")
        
        city = "jaipur"  # default
        
        # optional: detect city from command
        words = c.split()
        if "in" in words:
            city = words[words.index("in") + 1]

        get_weather(city)

    # openrouter AI (fallback)
    else:
        responses = ["Thinking...", "Let me think...", "Processing..."]
        speak(random.choice(responses))

        reply = ask_ai(c)
        print("AI:", reply)

        speak(reply[:200])  # limit long response


if __name__ == "__main__":
    speak("Initializing Riva")

    while True:
        print("recognizing.....")
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            word = recognizer.recognize_google(audio, language="en-IN").lower()
            print("Heard:", word)

            # Handle both "riva" and "rewa"
            if any(w in word for w in ["riva", "rewa"]):
                speak("Yes sir, how can I assist you?")

                with sr.Microphone() as source:
                    print("RIVA Active...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)

                    audio = recognizer.listen(source)
                    command = recognizer.recognize_google(audio, language="en-IN").lower()

                    print("Command:", command)
                    processCommand(command)

        except sr.UnknownValueError:
            print("Could not understand")
        except sr.RequestError:
            print("Internet issue")
        except Exception as e:
            print("Error:", e)