from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import ollama
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageColor
import os
import time
import textwrap

app = Flask(__name__)

# -------------------------------
# Configuration
# -------------------------------
NEWS_CATEGORIES = [
    {"query": "technology", "icon": "fa-solid fa-bolt"},
    {"query": "business", "icon": "fa-solid fa-briefcase"},
    {"query": "stocks", "icon": "fa-solid fa-chart-line"},
    {"query": "entertainment", "icon": "fa-solid fa-film"}  # NEW CATEGORY
]

NEWS_PER_CATEGORY = 3
TOTAL_NEWS = 12

summary_cache = {}
image_cache = {}

CATEGORY_COLORS = [
    "#38bdf8", "#fbbf24", "#10b981", "#f472b6", "#a78bfa",
    "#fb7185", "#34d399", "#fcd34d", "#60a5fa", "#f87171"
]

# -------------------------------
# Ollama Warm-up
# -------------------------------
print("Warming up Ollama model...")
try:
    ollama.chat(
        model="llama3",
        messages=[{"role":"system","content":"Warm-up."},{"role":"user","content":"Hello"}]
    )
    print("Ollama model ready!")
except Exception as e:
    print("Warning: Ollama warm-up failed:", e)

# -------------------------------
# Fetch Google News
# -------------------------------
def get_google_news(query, count=4):
    if query.lower() == "stocks":
        query_str = "stock market OR company stocks"
    else:
        query_str = query
    url = f"https://news.google.com/rss/search?q={query_str}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "xml")
    items = soup.find_all("item")[:count]
    news = []
    for item in items:
        news.append({
            "title": item.title.text,
            "link": item.link.text,
            "category": query
        })
    return news

# -------------------------------
# Summarize with Ollama
# -------------------------------
def summarize_with_ollama(text):
    if text in summary_cache:
        return summary_cache[text]
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role":"system","content":"Summarize the following news headline in one short sentence."},
                {"role":"user","content": text}
            ],
        )
        summary = response["message"]["content"]
    except:
        summary = text[:100] + "..."
    summary_cache[text] = summary
    return summary

# -------------------------------
# Generate News Card Image
# -------------------------------
def generate_news_card(title, idx, category="general", base_color="#64748b"):
    key = (title, category)
    if key in image_cache:
        return image_cache[key]

    os.makedirs("static/images", exist_ok=True)
    width, height = 900, 500
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)

    # -------------------------------
    # Dynamic gradient based on category
    # -------------------------------
    top_color = base_color
    # Slightly darker for bottom
    bottom_color = tuple(max(0, int(int(base_color.strip('#')[i:i+2], 16)*0.8)) 
                         for i in (0, 2, 4))
    for y in range(height):
        r1, g1, b1 = ImageColor.getrgb(top_color)
        r2, g2, b2 = bottom_color
        r = int(r1 + (r2 - r1) * y / height)
        g = int(g1 + (g2 - g1) * y / height)
        b = int(b1 + (b2 - b1) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # -------------------------------
    # Fonts
    # -------------------------------
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 32)
        footer_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # -------------------------------
    # Title with shadow for readability
    # -------------------------------
    margin = 40
    offset = 40
    lines = textwrap.wrap(title, width=35)
    for line in lines:
        # Shadow
        draw.text((margin+2, offset+2), line, font=title_font, fill="#000000")
        # Main text
        draw.text((margin, offset), line, font=title_font, fill="white")
        bbox = title_font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        offset += line_height + 10

    # -------------------------------
    # Footer
    # -------------------------------
    draw.text((30, height-40), "Generated locally • No APIs", font=footer_font, fill="#cbd5e1")

    path = f"static/images/news_{idx}.png"
    img.save(path)
    image_cache[key] = path
    return path

# -------------------------------
# Text-to-Speech (per news)
# -------------------------------
def text_to_speech(text):
    os.makedirs("static/audio", exist_ok=True)  # Save audio in separate folder
    filename = f"static/audio/news_{int(time.time()*1000)}.mp3"
    tts = gTTS(text=text, lang="en")
    tts.save(filename)
    return filename

# -------------------------------
# Flask Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/top-news")
def top_news():
    all_news = []
    color_map = {}

    for idx, cat in enumerate(NEWS_CATEGORIES):
        color_map[cat["query"]] = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
        news_list = get_google_news(cat["query"], NEWS_PER_CATEGORY)
        for n in news_list:
            n["icon"] = cat.get("icon","fa-solid fa-newspaper")
        all_news.extend(news_list)

    all_news = all_news[:TOTAL_NEWS]

    results = []
    for idx, news in enumerate(all_news):
        summary = summarize_with_ollama(news["title"])
        image = generate_news_card(news["title"], idx, news.get("category","general"), base_color=color_map.get(news.get("category","general"), "#64748b"))
        audio = text_to_speech(summary)
        results.append({
            "title": news["title"],
            "summary": summary,
            "link": news["link"],
            "image": image,
            "category": news.get("category","general"),
            "icon": news.get("icon","fa-solid fa-newspaper"),
            "audio": audio,
            "color": color_map.get(news.get("category","general"), "#64748b")
        })

    return jsonify({"news": results})

if __name__ == "__main__":
    app.run(debug=True)
