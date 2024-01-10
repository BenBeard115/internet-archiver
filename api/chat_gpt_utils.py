"""Script for Open AI functions."""

from dotenv import load_dotenv
from openai import OpenAI

GPT_3_MODEL = 'gpt-3.5-turbo-1106'
GPT_4_MODEL = 'gpt-4-1106-preview'


load_dotenv()


def read_html_file(file_path: str) -> str:
    """Reads in HTML file."""

    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return html_content


def generate_summary(html_content, gpt_model: str = GPT_3_MODEL):
    """Generates summary of HTML content"""

    max_html_tokens = 10000 if gpt_model == GPT_3_MODEL else 50000
    html_content = html_content[:max_html_tokens]

    client = OpenAI()

    prompt = """You are an elite web content curator, renowned for crafting compelling and succinct summaries of web pages. Your expertise lies in distilling the essence of a webpage's content and function, with a primary focus on conveying what the page is about. 

Your task is to create a summary of the HTML document you receive, capturing the essence of the webpage's content in a way that is informative and engaging for users of our internet archiver website. 🌐✨ 

Ensure your summary is both captivating and concise, as it will be stored in our database for users to access. Kickstart the description by highlighting the core theme or purpose of the page, enticing users to explore further. Feel free to incorporate emojis to add a touch of vibrancy.

Your mission is to make each summary an invitation, sparking curiosity and encouraging users to delve into the fascinating world captured within each archived webpage. 📚💻
"""

    completion = client.chat.completions.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Please summarise this webpage as instructed: {html_content}."}
        ]
    )

    return completion.choices[0].message.content


def generate_genre(html_content, gpt_model: str = GPT_3_MODEL):
    """Generates genre from HTML content"""

    max_html_tokens = 10000 if gpt_model == GPT_3_MODEL else 50000
    html_content = html_content[:max_html_tokens]

    client = OpenAI()

    prompt = """Here are some common website types or categories that we want to use for our internet archiver website:

News:
Websites that provide news articles and current events.

Social Media:
Platforms that allow users to connect, share content, and engage with each other.

E-commerce:
Websites that facilitate online buying and selling of products.

Blogs:
Personal or professional websites that feature regularly updated articles or posts.

Educational:
Websites providing educational content, courses, or resources.

Entertainment:
Sites offering entertainment content such as videos, music, games, etc.

Business/Corporate:
Websites representing businesses or corporations, often providing information about products and services.

Government:
Official websites of government organizations or agencies.

Health and Wellness:
Sites focused on health-related content, medical information, or wellness advice.

Technology:
Websites covering technology news, reviews, and information.

Forums/Communities:
Platforms where users can engage in discussions and share information.

Sports:
Websites dedicated to sports news, scores, and related content.

Personal Portfolio:
Websites showcasing an individual's work, achievements, or resume.

Travel:
Platforms providing information about travel destinations, reviews, and bookings.

Food and Cooking:
Sites focused on recipes, cooking tips, and food-related content.

Fashion and Lifestyle:
Platforms featuring fashion trends, lifestyle articles, and related content.

Gaming:
Websites dedicated to video games, gaming news, and reviews.

Weather:
Platforms providing weather forecasts and related information.

Your job is to classify an html document into one of these categories.
"""

    completion = client.chat.completions.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Please get the category of this webpage as instructed: {html_content}. Please answer directly with category."}
        ]
    )

    return completion.choices[0].message.content


def get_genre(html_content, gpt_model: str = GPT_3_MODEL):
    """Gets genre from html doc."""

    website_categories = [
        "News",
        "Social Media",
        "E-commerce",
        "Blogs",
        "Educational",
        "Entertainment",
        "Business/Corporate",
        "Government",
        "Health and Wellness",
        "Technology",
        "Forums/Communities",
        "Sports",
        "Personal Portfolio",
        "Travel",
        "Food and Cooking",
        "Fashion and Lifestyle",
        "Gaming",
        "Weather"
    ]

    chat_gpt_response = generate_genre(html_content, gpt_model)

    for category in website_categories:
        if category in chat_gpt_response:
            return category

    return 'N/A'


if __name__ == "__main__":

    filenames = ['pete_bradshaw', 'rains', 'twitch', 'rocket_league']
    for filename in filenames:
        html_file = f'{filename}.html'

        html_content = read_html_file(html_file)

        print(filename)
        # print(generate_summary(html_content))
        print(get_genre(html_content))

        print()
