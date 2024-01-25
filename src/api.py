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

creator_prompt_parts = [
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

creator_request_schema = {
    "type": "object",
    "properties": {
        "style": {"type": "string"}
    },
    "required": ["style"]
}

limiter = Limiter(app, default_limits=["3 per minute"])

logs_file = 'logs.json'

def log_request(ip, prompts):
    logs = {}
    if os.path.exists(logs_file):
        with open(logs_file) as file:
            logs = json.load(file)
    
    if ip not in logs:
        logs[ip] = []
    
    logs[ip].extend(prompts)
    
    with open(logs_file, 'w') as file:
        json.dump(logs, file, indent=2)


@app.route('/generate-theme', methods=['POST'])
@limiter.limit("1 per second")
def generate_theme():
    ip = request.headers.get('cf-connecting-ip')
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, creator_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    user_style = request.json['style']
    prompts.append(user_style)

    log_request(ip, prompts)

    creator_prompt_parts.append(f"{user_style}")
    
    response = model.generate_content(creator_prompt_parts)
    return response.text


if __name__ == '__main__':
    app.run(port=5100)
