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

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 1000,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

themium_request_schema = {
    "type": "object",
    "properties": {"style": {"type": "string"}},
    "required": ["style"],
}

math_request_schema = {
    "type": "object",
    "properties": {"question": {"type": "string"}},
    "required": ["question"],
}

ask_request_schema = {
    "type": "object",
    "properties": {"question": {"type": "string"}},
    "required": ["question"],
}

teachme_request_schema = {
    "type": "object",
    "properties": {"question": {"type": "string"}},
    "required": ["question"],
}

limiter = Limiter(app, default_limits=["3 per minute"])

logs_file = "logs.json"
tokens_file = "tokens.json"

def is_blocked_ip(ip):
    with open("blockedips.json") as file:
        blocked_ips = json.load(file)
        return ip in blocked_ips

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

    with open(logs_file, "w") as file:
        json.dump(logs, file, indent=2)


def is_valid_token(token):
    with open(tokens_file) as file:
        tokens = json.load(file)
        return token in tokens


@app.route("/api/themium/generate", methods=["POST"])
@limiter.limit("1 per second")
def generate_theme():
    ip = request.headers.get("cf-connecting-ip")
    if is_blocked_ip(ip):
        return jsonify({"error": "Your IP has been blocked"}), 403
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, themium_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    token = request.headers.get("Authorization")
    if token and is_valid_token(token):
        prompts = []
    else:
        log_request(ip, prompts, "/api/geminium/ask")

    user_style = request.json["style"]
    prompts.append(user_style)

    themium_prompt_parts = [
        'You create themes for Meower. Do not change any of the variable names, only their values! The only values should be "orange" (main color), "orangeLight" (main color but lighter), "orangeDark" (main color but darker). "background" (the background color), "foreground" (mainly used for text and a few other things), "foregroundOrange" (used for outlines of buttons) and "tinting" (used for tinting).Here are some basic color examples you can use:Red - #FF0000Orange - #FFA500Meower Orange - #FC5D11Yellow - #FFFF00Green - #008000Lime - #32CD32Mint Green - #98FB98Blue Green - #0D98BACobalt Blue - #0047ABToothpaste Blue - #B1EAE8Cyan - #00FFFFBlue - #0000FFTeal - #008080Blue Purple - #8A2BE2Indigo - #4B0082Purple - #800080Violet - #7F00FFPink - #FFC0CBBlack - #000000Grey - #808080White - #FFFFFF',
        "input: The default orange theme",
        'output: {"v":1,"orange":"#f9a636","orangeLight":"#ffcb5b","orangeDark":"#d48111","background":"#ffffff","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#252525"}',
        "input: The default orange theme but turqouise",
        'output: {"v":1,"orange":"#2ec4b6","background":"#ffffff","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#252525","orangeLight":"#53e9db","orangeDark":"#099f91"}',
        "input: A red theme with dark mode",
        'output: {"v":1,"orange":"#e62739","orangeLight":"#ff6974","orangeDark":"#bf001d","background":"#181818","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#252525"}',
        "input: A dark mode green theme",
        'output: {"v":1,"orange":"#28b485","orangeLight":"#52d8a8","orangeDark":"#008e60","background":"#181818","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#252525"}',
        "input: Android holo ui colours with dark background and blue accents",
        'output: {"v":1,"orange":"#0099cc","background":"#090909","foreground":"#ffffff","foregroundOrange":"#C5EAF8","tinting":"#001820","orangeLight":"#00b1ec","orangeDark":"#0081ac"}',
        "input: A dark mint-green theme with dark-green tinting",
        'output: {"v":1,"orange":"#2e8b57","orangeLight":"#64d88d","orangeDark":"#00693e","background":"#181818","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#00301b"}',
        "input: Light caramel colored background and and main color with white tinting",
        'output: {"v":1,"orange":"#c39f81","orangeLight":"#f6d7b8","orangeDark":"#97755d","background":"#f6d7b8","foreground":"#000000","foregroundOrange":"#000000","tinting":"#ffffff"}',
        "input: A pitch black AMOLED theme with cool cyan accents",
        'output: {"v":1,"orange":"#00bfff","orangeLight":"#33e0ff","orangeDark":"#008cba","background":"#000000","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#00171f"}',
        "input: A theme based on the colors of the Google Turtle Emoji",
        'output: {"v":1,"orange":"#66bb6a","orangeLight":"#99d98c","orangeDark":"#339933","background":"#001820","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#00301b"}',
        'input: Make this theme light mode: {"v":1,"orange":"#ffffff","orangeLight":"#ffffff","orangeDark":"#ffffff","background":"#000000","foreground":"#ffffff","foregroundOrange":"#000000","tinting":"#000000"}',
        'output: {"v":1,"orange":"#8bc34a","background":"#deffb7","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#030402","orangeLight":"#8ec74c","orangeDark":"#88bf48"}',
        'input: Make this theme light mode: {"v":1,"orange":"#ffeb3b","orangeLight":"#ffff72","orangeDark":"#c8b91d","background":"#1d2951","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#374785"}',
        'output: {"v":1,"orange":"#ffeb3b","orangeLight":"#ffff72","orangeDark":"#c8b91d","background":"#1d2951","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#374785"}',
        'input: Make this theme light mode: {"v":1,"orange":"#00bfff","orangeLight":"#33e0ff","orangeDark":"#008cba","background":"#000000","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#00171f"}',
        'output: {"v":1,"orange":"#00bfff","orangeLight":"#00d6ff","orangeDark":"#00a8e0","background":"#ffffff","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#00171f"}',
        'input: Make this theme dark mode: {"v":1,"orange":"#fc747b","orangeLight":"#ff8a8f","orangeDark":"#de5e64","background":"#ffffff","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#252525"}',
        'output: {"v":1,"orange":"#fc747b","orangeLight":"#ff99a0","orangeDark":"#d74f56","background":"#1c1c1c","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#252525"}',
        'input: Make this theme dark mode: {"v":1,"orange":"#57ab4b","orangeLight":"#88c971","orangeDark":"#2b802c","background":"#ffffff","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#252525"}',
        'output: {"v":1,"orange":"#57ab4b","orangeLight":"#7cd070","orangeDark":"#328626","background":"#171717","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#252525"}',
        'input: Make this theme dark mode: {"v":1,"orange":"#00bfff","background":"#ffffff","foreground":"#000000","foregroundOrange":"#ffffff","tinting":"#003e5c","orangeLight":"#33e0ff","orangeDark":"#008cba"}',
        'output: {"v":1,"orange":"#00bfff","background":"#000000","foreground":"#ffffff","foregroundOrange":"#ffffff","tinting":"#003e5c","orangeLight":"#00fdff","orangeDark":"#0081a3"}',
        "input: ",
        "output: ",
    ]
    themium_prompt_parts.append(f"{user_style}")

    response = model.generate_content(themium_prompt_parts)
    return response.text


@app.route("/api/geminium/math", methods=["POST"])
@limiter.limit("1 per second")
def solve_math():
    ip = request.headers.get("cf-connecting-ip")
    if is_blocked_ip(ip):
        return jsonify({"error": "Your IP has been blocked"}), 403
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, math_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    token = request.headers.get("Authorization")
    if token and is_valid_token(token):
        prompts = []
    else:
        log_request(ip, prompts, "/api/geminium/ask")

    user_question = request.json["question"]
    prompts.append(user_question)

    log_request(ip, [user_question], "/api/geminium/math")

    math_prompt_parts = [
        "You're now the Geminium Math AI model. When given a math question, show the steps to solve the question and highlight the final answer in bold text (with markdown).",
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
    math_prompt_parts.append(f"{user_question}")

    response = model.generate_content(math_prompt_parts)
    return response.text


@app.route("/api/geminium/ask", methods=["POST"])
@limiter.limit("1 per second")
def ask_question():
    ip = request.headers.get("cf-connecting-ip")
    if is_blocked_ip(ip):
        return jsonify({"error": "Your IP has been blocked"}), 403
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, ask_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    token = request.headers.get("Authorization")
    if token and is_valid_token(token):
        prompts = []
    else:
        log_request(ip, prompts, "/api/geminium/ask")

    user_question = request.json["question"]
    prompts.append(user_question)

    log_request(ip, [user_question], "/api/geminium/ask")

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
        'output: The most used emoji as of 2021 was **"Tears of Joy"** 😂.',
        "input: How many users does Reddit have in 2022 as compared to 2012?",
        "output: In 2022, Reddit had **430 million** active users, compared to **130 million** active users in 2012. This represents an increase of **230 million** active users.",
        "input: What is Meower?",
        "output: Meower is a **social media platform** created by jaxonbaxon in 2020 and currently owned by MikeDEV. As of 26 January 2024, Meower has about 6000 users.",
        "input: What is the Meower website?",
        "output: The official Meower website is **https://meower.org**.",
        "input: How can I use Meower?",
        "output: You can access Meower using the **official client** at https://app.meower.org, or by using a **third party client** created by members of the community. Examples of these include [Roarer](https://mybearworld.github.io/roarer/) and [meo](https://meo-32r.pages.dev).",
        "input: What is Meower's official client made with?",
        "output: Meower's official client is made using **Svelte** and is deployed using **Cloudflare Pages**",
        "input: How can users interact on Meower?",
        "output: Users on Meower can interact in **home, livechat, group chats and DMs** using **posts, images and emojis**.",
        "input: How did Meower start?",
        "output: Meower started life as a Scratch 3.0-based social media platform. With the\ncontinuous support of our amazing community, Meower has evolved into a feature-rich platform for creators of all\nkinds.",
        "input: Is Meower open-source?",
        "output: **Yes!** Meower is open source and the source code is available on [GitHub](https://github.com/meower-media-co).",
        "input: Where is Meower's Terms of Sevrice/Privacy Policy?",
        "output: Meower's terms of service and privacy policy can be viewed **[here](https://meower.org/legal)**.",
        "input: What is Meower's official mascot?",
        "output: Meower's official mascot is **Meowy**! Meowy can be found around the Meower client, website, GitHub and community projects. [Picture of Meowy: https://meower.org/icons/meowyicon.svg]",
        "input: Who hosts Meower?",
        "output: Meower's servers are hosted by **MikeDEV**. Some other services however such as the **Meower Forums** are hosted by **tnix**.",
        "input: What is Roarer Glass?",
        "output: Roarer Glass is a **userscript for Roarer** that gives it a translucent glass-like effect with custom background support and **allows for customisation** of other UI elements. You can download it from **[Greasy Fork](https://greasyfork.org/en/scripts/485804-roarer-glass)** to a userscript manager such as **Tampermonkey** or **Violentmonkey**.",
        "input: ",
        "output: ",
    ]
    ask_prompt_parts.append(f"{user_question}")

    response = model.generate_content(ask_prompt_parts)
    return response.parts[0].text


@app.route("/api/geminium/teachme", methods=["POST"])
@limiter.limit("1 per second")
def teachme_question():
    ip = request.headers.get("cf-connecting-ip")
    if is_blocked_ip(ip):
        return jsonify({"error": "Your IP has been blocked"}), 403
    prompts = []
    try:
        # Validate the JSON payload against the schema
        validate(request.json, teachme_request_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    token = request.headers.get("Authorization")
    if token and is_valid_token(token):
        prompts = []
    else:
        log_request(ip, prompts, "/api/geminium/teachme")

    user_question = request.json["question"]
    prompts.append(user_question)

    log_request(ip, [user_question], "/api/geminium/teachme")

    teachme_prompt_parts = [
        "You're Geminium Teachme (or just Geminium for short), an AI \nmodel designed to take a lession subject and teach the user about that subject with up to 3 detailed paragraphs. \nYou can't receive replies or additional context, only receive the \nquestion and answer the question. Respond using markdown. You have a character limit of 2000 characters",
        "input: sometimes when I pet my cat his fur is really smooth and soft when he \nwants food while other times his fur feels rougher like when he’s trying\n to sleep, why is this?",
        "output: Cats have two types of fur: **guard hairs** and **down hairs**. Guard hairs are the longer, coarser hairs that make up the outer layer of the fur. Down hairs are the shorter, finer hairs that make up the undercoat.\n\nWhen your cat is **relaxed and content**, the **guard hairs lie flat against the body**, and the **down hairs** are **fluffed up** to **create a layer of insulation. This makes the fur feel soft and smooth.**\n\nWhen your cat is **excited or stressed**, the **guard hairs stand up on end**, and the **down hairs are pulled in closer to the body**. This makes the fur feel rougher and more wiry.\n\nIn addition to the physical changes in the fur, there are also changes in the **oils that the skin produces**. When your cat is relaxed, the skin produces more oils, which makes the fur feel softer and shinier. When your cat is **stressed, the skin produces less oils**, which makes the fur feel drier and rougher.\n\nSo, the next time you pet your cat, pay attention to how their fur feels. It can tell you a lot about their mood and state of mind.",
        "input: why did jack dorsey create twitter?",
        'output: Jack Dorsey created Twitter in 2006 as a way for people to **share short messages** with each other. He was inspired by the idea of a "status update," which was a popular feature on AOL Instant Messenger at the time. Dorsey believed that a service that allowed people to share short updates about their lives would be a **valuable tool for communication and connection**.\n\nDorsey also wanted to create a platform that was easy to use and accessible to everyone. **He chose the name "Twitter" because it was short, easy to remember**, and evoked the idea of chirping birds. He also designed the platform to be **simple and straightforward**, with a focus on brevity and real-time communication.\n\nTwitter quickly gained popularity, and **by 2007, it had over 500,000 users**. In 2009, Twitter introduced hashtags, which made it easier for users to find and follow conversations about specific topics. This feature helped Twitter become even more popular, and by 2010, it had over 100 million users.\n\n**Today, Twitter is one of the most popular social media platforms in the world**, with **over 330 million monthly active users**. It is used by people from all walks of life to share news, information, and opinions. Twitter has also become a powerful tool for businesses and organizations to connect with customers and promote their products and services.',
        "input: How do penguins survive such harsh weather conditions?",
        "output: Penguins have a number of adaptations that help them survive in harsh weather conditions:\n\n* **Thick layer of fat:** Penguins have a thick layer of fat that insulates them from the cold. This layer of fat can be up to 2 inches thick, and it helps to keep the penguin's core temperature warm, even when the air temperature is below freezing.\n* **Feathers:** Penguins also have a dense layer of feathers that helps to trap heat and keep the penguin dry. Penguin feathers are also waterproof, which helps to protect the penguin from the cold water and snow.\n* **Flippers:** Penguins' flippers are not only used for swimming, but they also help to keep the penguin warm. Penguins can tuck their flippers into their bodies to conserve heat, and they can also use their flippers to cover their feet, which are one of the most vulnerable parts of their body to the cold.\n* **Behavioral adaptations:** Penguins also have a number of behavioral adaptations that help them to survive in harsh weather conditions. For example, penguins often huddle together in large groups to conserve heat. They will also take turns swimming and resting, so that each penguin can get a chance to warm up.\n\nThese are just a few of the adaptations that help penguins to survive in harsh weather conditions. These adaptations allow penguins to live in some of the coldest and most inhospitable environments on Earth.",
        "input: What is the story behind the creation of Apple Inc?",
        "output: **In 1976, two friends, Steve Jobs and Steve Wozniak, built a personal computer in Jobs' garage**. They called it the **Apple I**, and it was the first personal computer to be sold fully assembled. The Apple I was a success, and Jobs and Wozniak **founded Apple Computer, Inc. in 1977**.\n\nThe following year, Apple released the **Apple II**, which was an even bigger success than the Apple I. The Apple II was one of **the first personal computers to be sold with a color monitor**, and it quickly became the **most popular personal computer in the world**.\n\n**In 1980, Apple went public**, and Jobs became a multimillionaire. However, he was forced to resign from Apple in 1985 after a power struggle with the company's board of directors.\n\nJobs went on to found NeXT, a computer company that was not as successful as Apple. However, in 1997, Apple bought NeXT, and **Jobs returned to Apple as its CEO**.\n\nUnder Jobs' leadership, Apple released a number of **successful products, including the iMac, the iPod, the iPhone, and the iPad**. Apple became one of the most valuable companies in the world, and Jobs became one of the most iconic figures in the tech industry.\n\n**Jobs died in 2011**, but Apple continues to be a successful company. It is now the most valuable company in the world, and its products are used by people all over the globe.",
        "input: How did Tokyo make earthquake-proof buildings?",
        "output: Tokyo has a long history of earthquakes, and its buildings are designed to withstand them. Here are some of the ways that Tokyo's buildings are made earthquake-proof:\n\n* **Base isolation:** Many buildings in Tokyo are built on **base isolators**, which are devices that absorb seismic energy and reduce the amount of shaking that the building experiences. Base isolators are typically made of rubber or steel, and they are placed between the foundation of the building and the ground.\n* **Damping systems:** Damping systems are devices that dissipate seismic energy and reduce the vibrations of a building. There are many different types of damping systems, but they all work by converting the energy of the earthquake into heat or other forms of energy.\n* **Structural design:** The structural design of a building can also help to make it earthquake-proof. Buildings that are designed to be flexible and resilient are more likely to withstand an earthquake without collapsing.\n* **Materials:** The materials that are used to construct a building can also affect its earthquake resistance. Buildings that are made of reinforced concrete or steel are more likely to withstand an earthquake than buildings that are made of weaker materials, such as wood or brick.\n\n**Building codes:** Tokyo has strict building codes that require all new buildings to be designed to withstand earthquakes. These codes specify the types of materials that can be used, the structural design of the building, and the types of earthquake-proofing systems that must be installed.\n\nAs a result of these measures, Tokyo's buildings are some of the most earthquake-proof in the world. Even during the Great East Japan Earthquake of 2011, which was one of the most powerful earthquakes ever recorded, Tokyo's buildings suffered relatively little damage.",
        "input: Why is there a giant barcode-like thing in the middle of the Mojave Desert?",
        "output: The giant barcode-like thing in the middle of the Mojave Desert is called **Desert Sunlight**. It is a **solar power plant** that was built in 2014. The plant consists of **93,000 mirrors** that focus sunlight onto a **central tower**. The heat from the sunlight is then used to **generate electricity**.\n\nDesert Sunlight is a **concentrated solar power (CSP)** plant. CSP plants use mirrors or lenses to concentrate sunlight onto a small area, which creates heat. The heat is then used to boil water and generate steam, which drives a turbine to generate electricity.\n\nCSP plants are more efficient than traditional solar panels, which convert sunlight directly into electricity. However, CSP plants are also more expensive to build and maintain.\n\nDesert Sunlight is one of the largest CSP plants in the world. It has a capacity of **550 megawatts**, which is enough to power **150,000 homes**. The plant is owned and operated by **NextEra Energy Resources**.\n\nDesert Sunlight is a significant step forward in the development of solar power. It shows that CSP plants can be built on a large scale and that they can generate a significant amount of electricity.",
        "input: Why does China own almost every panda in the world?",
        "output: China owns almost every panda in the world because **pandas are native to China**, and **the Chinese government has strict laws protecting them**. Pandas are considered a **national treasure**, and it is illegal to hunt, kill, or capture them without a permit.\n\nIn addition, the Chinese government has been working to **repopulate the panda population**, which was once very low. In the 1980s, there were only about 1,000 pandas left in the wild. Today, there are over 2,000 pandas in the wild, and over 600 pandas in captivity.\n\nThe Chinese government has also been working to **promote pandas as a symbol of China**. Pandas are featured on Chinese currency, stamps, and other items. They are also popular tourist attractions, and the Chinese government has been working to increase tourism to panda reserves.\n\nAs a result of these efforts, China now owns almost every panda in the world. This has helped to protect the panda population and promote pandas as a symbol of China.",
        "input: What's the story of Meower?",
        "output: Sorry, I don't have any info on Meower yet, but Geminium Ask does if you want to ask any short question about Meower.",
        "input: ",
        "output: ",
    ]
    teachme_prompt_parts.append(f"{user_question}")

    response = model.generate_content(teachme_prompt_parts)
    return response.parts[0].text


if __name__ == "__main__":
    app.run(port=5100)
