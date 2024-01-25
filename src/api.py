import os
from dotenv import *
from flask import Flask, request, jsonify
from jsonschema import validate, ValidationError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import google.generativeai as genai
import json

app = Flask(__name__)
CORS(app) 

load_dotenv()

api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 700,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

themium_prompt_parts = [
  "You create themes for Meower. Do not change any of the variable names, only their values! The only values should be \"orange\" (main color), \"orangeLight\" (main color but lighter), \"orangeDark\" (main color but darker). \"background\" (the background color), \"foreground\" (mainly used for text and a few other things), \"foregroundOrange\" (used for outlines of buttons) and \"tinting\" (used for tinting).Here are some basic color examples you can use:Red - #FF0000Orange - #FFA500Meower Orange - #FC5D11Yellow - #FFFF00Green - #008000Lime - #32CD32Mint Green - #98FB98Blue Green - #0D98BACobalt Blue - #0047ABToothpaste Blue - #B1EAE8Cyan - #00FFFFBlue - #0000FFTeal - #008080Blue Purple - #8A2BE2Indigo - #4B0082Purple - #800080Violet - #7F00FFPink - #FFC0CBBlack - #000000Grey - #808080White - #FFFFFF",
  "input: The default orange theme",
  "output: {\"v\":1,\"orange\":\"#f9a636\",\"orangeLight\":\"#ffcb5b\",\"orangeDark\":\"#d48111\",\"background\":\"#ffffff\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "input: The default orange theme but turqouise",
  "output: {\"v\":1,\"orange\":\"#2ec4b6\",\"background\":\"#ffffff\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\",\"orangeLight\":\"#53e9db\",\"orangeDark\":\"#099f91\"}",
  "input: A red theme with dark mode",
  "output: {\"v\":1,\"orange\":\"#e62739\",\"orangeLight\":\"#ff6974\",\"orangeDark\":\"#bf001d\",\"background\":\"#181818\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "input: A dark mode green theme",
  "output: {\"v\":1,\"orange\":\"#28b485\",\"orangeLight\":\"#52d8a8\",\"orangeDark\":\"#008e60\",\"background\":\"#181818\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "input: Android holo ui colours with dark background and blue accents",
  "output: {\"v\":1,\"orange\":\"#0099cc\",\"background\":\"#090909\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#C5EAF8\",\"tinting\":\"#001820\",\"orangeLight\":\"#00b1ec\",\"orangeDark\":\"#0081ac\"}",
  "input: A dark mint-green theme with dark-green tinting",
  "output: {\"v\":1,\"orange\":\"#2e8b57\",\"orangeLight\":\"#64d88d\",\"orangeDark\":\"#00693e\",\"background\":\"#181818\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#00301b\"}",
  "input: Light caramel colored background and and main color with white tinting",
  "output: {\"v\":1,\"orange\":\"#c39f81\",\"orangeLight\":\"#f6d7b8\",\"orangeDark\":\"#97755d\",\"background\":\"#f6d7b8\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#000000\",\"tinting\":\"#ffffff\"}",
  "input: A pitch black AMOLED theme with cool cyan accents",
  "output: {\"v\":1,\"orange\":\"#00bfff\",\"orangeLight\":\"#33e0ff\",\"orangeDark\":\"#008cba\",\"background\":\"#000000\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#00171f\"}",
  "input: A theme based on the colors of the Google Turtle Emoji",
  "output: {\"v\":1,\"orange\":\"#66bb6a\",\"orangeLight\":\"#99d98c\",\"orangeDark\":\"#339933\",\"background\":\"#001820\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#00301b\"}",
  "input: Make this theme light mode: {\"v\":1,\"orange\":\"#ffffff\",\"orangeLight\":\"#ffffff\",\"orangeDark\":\"#ffffff\",\"background\":\"#000000\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#000000\",\"tinting\":\"#000000\"}",
  "output: {\"v\":1,\"orange\":\"#8bc34a\",\"background\":\"#deffb7\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#030402\",\"orangeLight\":\"#8ec74c\",\"orangeDark\":\"#88bf48\"}",
  "input: Make this theme light mode: {\"v\":1,\"orange\":\"#ffeb3b\",\"orangeLight\":\"#ffff72\",\"orangeDark\":\"#c8b91d\",\"background\":\"#1d2951\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#374785\"}",
  "output: {\"v\":1,\"orange\":\"#ffeb3b\",\"orangeLight\":\"#ffff72\",\"orangeDark\":\"#c8b91d\",\"background\":\"#1d2951\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#374785\"}",
  "input: Make this theme light mode: {\"v\":1,\"orange\":\"#00bfff\",\"orangeLight\":\"#33e0ff\",\"orangeDark\":\"#008cba\",\"background\":\"#000000\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#00171f\"}",
  "output: {\"v\":1,\"orange\":\"#00bfff\",\"orangeLight\":\"#00d6ff\",\"orangeDark\":\"#00a8e0\",\"background\":\"#ffffff\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#00171f\"}",
  "input: Make this theme dark mode: {\"v\":1,\"orange\":\"#fc747b\",\"orangeLight\":\"#ff8a8f\",\"orangeDark\":\"#de5e64\",\"background\":\"#ffffff\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "output: {\"v\":1,\"orange\":\"#fc747b\",\"orangeLight\":\"#ff99a0\",\"orangeDark\":\"#d74f56\",\"background\":\"#1c1c1c\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "input: Make this theme dark mode: {\"v\":1,\"orange\":\"#57ab4b\",\"orangeLight\":\"#88c971\",\"orangeDark\":\"#2b802c\",\"background\":\"#ffffff\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "output: {\"v\":1,\"orange\":\"#57ab4b\",\"orangeLight\":\"#7cd070\",\"orangeDark\":\"#328626\",\"background\":\"#171717\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#252525\"}",
  "input: Make this theme dark mode: {\"v\":1,\"orange\":\"#00bfff\",\"background\":\"#ffffff\",\"foreground\":\"#000000\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#003e5c\",\"orangeLight\":\"#33e0ff\",\"orangeDark\":\"#008cba\"}",
  "output: {\"v\":1,\"orange\":\"#00bfff\",\"background\":\"#000000\",\"foreground\":\"#ffffff\",\"foregroundOrange\":\"#ffffff\",\"tinting\":\"#003e5c\",\"orangeLight\":\"#00fdff\",\"orangeDark\":\"#0081a3\"}",
  "input: ",
  "output: ",
]

math_prompt_parts = [
  "You're now the Geminium Math AI model. When given a math question, show the steps to solve the question and highlight the final answer in bold text (with markdown). If not given a math problem or math word problem, say \"Sorry, can't help with that\". Some math word problem examples include \"What numbers from 1 - 100 have the most multiples?\" or \"Is 23 a prime number?\", but can be word sentence with numbers and other math language in them.",
  "input: 23 + 4 / 5",
  "output: **Question:** 23 + 4 / 5\n\n**Step 1:** Perform the division operation first: 4 / 5 = 0.8\n\n**Step 2:** Add the result of the division to the remaining number: 23 + 0.8 = 23.8\n\n**Answer: 23.8**",
  "input: 55% of 98.3",
  "output: **Question:** 55% of 98.3\n\n**Step 1:** Convert 55% to decimal form: 55% = 55/100 = 0.55\n\n**Step 2:** Multiply the decimal form of the percentage by the number: 0.55 * 98.3 = 53.665\n\n**Answer: 53.665**",
  "input: 2 + 1",
  "output: **Question:** 2 + 1\n\n**Step 1:** Add the two numbers: 2 + 1 = 3\n\n**Answer: 3**",
  "input: 98 billion 320 million 22 thousand 3 hundred and 44 as a number",
  "output: **Question:** 98 billion 320 million 22 thousand 3 hundred and 44 as a number\n\n**Answer: 98,320,022,344**",
  "input: Is 23 a prime number?",
  "output: **Question:** Is 23 a prime number?\n\n**Answer: Yes**",
  "input: ",
  "output: ",
]

ask_prompt_parts = [
  "You're Geminium Ask, an AI model designed to answer questions with short but informative replies. You can't receive replies or additional context, only receive the question and answer the question. Respond using markdown. If asked a math question, you can answer it, but say \"By the way, if you want more accurate and more detailed math answers, try @Geminium math (your question)\" at the end in italics.",
  "input: Who was the 43rd president of the United States?",
  "output: The 43rd president of the United States was **George W. Bush**. He was president from the **20th of January 2001** to to the **20th of January 2009**.",
  "input: When was the first Google Pixel released? What colours did it come in?",
  "output: The first Google Pixel was released on October 20, 2016. It came in three colors: Quite Black, Really Blue, and Very Silver.",
  "input: What were the specs of the first iPhone?",
  "output: * 3.5-inch TFT touchscreen display with a resolution of 320x480 pixels\n* 2-megapixel rear camera with fixed focus and no flash\n* VGA front-facing camera\n* 4GB or 8GB of storage\n* 128MB of RAM\n* 412MHz ARM 1176JZ-F processor\n* Wi-Fi (802.11b/g), Bluetooth 2.0, and EDGE connectivity\n* 1,400mAh lithium-ion battery",
  "input: How many bananas have been sold in Australia?",
  "output: It is impossible to provide an accurate answer to this question, as there is no publicly available data on the total number of bananas sold in Australia.",
  "input: What's 21 + 89?",
  "output: 110 \n\n*By the way, if you want more accurate and more detailed math answers, try @Geminium math (the question you want to ask)*",
  "input: What is the combined voltage of 3 standard alkaline AA batteries?",
  "output: 4.5 volts",
  "input: Can you power a normal Red LED with an AAA battery?",
  "output: Yes, you can power a normal Red LED with an AAA battery. A standard AAA battery provides 1.5 volts of power, which is enough to power a normal Red LED, which typically requires around 2 volts to operate.",
  "input: How many iPhone 3G's worth of battery capacity is in a Google Pixel 6 Pro?",
  "output: The Google Pixel 6 Pro has a battery capacity of 5,003mAh, while the iPhone 3G has a battery capacity of 1,150mAh. Therefore, the Google Pixel 6 Pro has a battery capacity of approximately 4.35 iPhone 3Gs.",
  "input: What is the highest recorded gas price in history and where was it?",
  "output: The highest recorded gas price in history was **$10.77 per gallon**, in **Humboldt, California, United States** on June 14, 2022.",
  "input: When is your data training cutoff?",
  "output: My training cutoff is **April 2023**. This means that I do not have access to real-time information or data past this date.",
  "input: What is the most used emoji as of 2021?",
  "output: The most used emoji as of 2021 was **\"Tears of Joy\"** 😂.",
  "input: How many users does Reddit have in 2022 as compared to 2012?",
  "output: In 2022, Reddit had **430 million** active users, compared to **130 million** active users in 2012. This represents an increase of **230 million** active users.",
  "input: ",
  "output: ",
]

themium_request_schema = {
    "type": "object",
    "properties": {
        "style": {"type": "string"}
    },
    "required": ["style"]
}

math_request_schema = {
    "type": "object",
    "properties": {
        "question": {"type": "string"}
    },
    "required": ["question"]
}

ask_request_schema = {
    "type": "object",
    "properties": {
        "question": {"type": "string"}
    },
    "required": ["question"]
}

limiter = Limiter(app, default_limits=["3 per minute"])

logs_file = 'logs.json'

def log_request(ip, prompts, api_command):
    logs = {}
    if os.path.exists(logs_file):
        with open(logs_file) as file:
            logs = json.load(file)
    
    if ip not in logs:
        logs[ip] = {}
    
    if api_command not in logs[ip]:
        logs[ip][api_command] = []

    logs[ip][api_command].extend(prompts)
    
    with open(logs_file, 'w') as file:
        json.dump(logs, file, indent=2)



@app.route('/api/themium/generate', methods=['POST'])
@limiter.limit("1 per second")
def generate_theme():
    ip = request.headers.get('cf-connecting-ip')
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, themium_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    user_style = request.json['style']
    prompts.append(user_style)

    log_request(ip, [user_style], '/api/themium/generate')

    themium_prompt_parts.append(f"{user_style}")
    
    response = model.generate_content(themium_prompt_parts)
    return response.text

@app.route('/api/geminium/math', methods=['POST'])
@limiter.limit("1 per second")
def solve_math():
    ip = request.headers.get('cf-connecting-ip')
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, math_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    user_question = request.json['question']
    prompts.append(user_question)

    log_request(ip, [user_question], '/api/geminium/math')

    math_prompt_parts.append(f"{user_question}")
    
    response = model.generate_content(math_prompt_parts)
    return response.text

@app.route('/api/geminium/ask', methods=['POST'])
@limiter.limit("1 per second")
def solve_math():
    ip = request.headers.get('cf-connecting-ip')
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, ask_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    user_question = request.json['question']
    prompts.append(user_question)

    log_request(ip, [user_question], '/api/geminium/ask')

    math_prompt_parts.append(f"{user_question}")
    
    response = model.generate_content(ask_prompt_parts)
    return response.text


if __name__ == '__main__':
    app.run(port=5100)
