from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return html_content


# og_prompt = """
#              You are a world-class web copy editor, skilled in creating concise and easy-to-understand summaries of web pages.
#              You will be given the contents of an HTML document and you are to write a summary of the webpage's content and/or function
#              (however your primary focus should be content and you should mention what the page is about first).
#              This will act as a summary on an internet archiver website - so make it suitably informative and engaging
#              for users of the website who are viewing the scraped page. Use emojis if possible.

#              The world-class, engaging summary you create will be stored in a database so keep it concise.

#              Write about the document in a way that invites the website user to view the webpage in an intriguing way.

#              Finally, if it seems the website makes an effort to block scraping, inform the user of this, apologising for the inconvenience.
#              """

def generate_summary(html_content):
    client = OpenAI()

    prompt = """You are an elite web content curator, renowned for crafting compelling and succinct summaries of web pages. Your expertise lies in distilling the essence of a webpage's content and function, with a primary focus on conveying what the page is about. 

Your task is to create a summary of the HTML document you receive, capturing the essence of the webpage's content in a way that is informative and engaging for users of our internet archiver website. 🌐✨ 

Ensure your summary is both captivating and concise, as it will be stored in our database for users to access. Kickstart the description by highlighting the core theme or purpose of the page, enticing users to explore further. Feel free to incorporate emojis to add a touch of vibrancy.

Your mission is to make each summary an invitation, sparking curiosity and encouraging users to delve into the fascinating world captured within each archived webpage. 📚💻
"""

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Please summarise this webpage as instructed: {html_content}."}
        ]
    )

    return completion.choices[0].message


def summarise_styling(html_content):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": """
             You are a world-class web front-end engineer who is skilled at examining an HTML document and explaining the key features of the website -
             from functionality to aesthetic layout. You are to create a summary webpage's styling describing the most important features you see.
             """},
            {"role": "user", "content": f"Please summarise the styling of this HTML document: {html_content}."}
        ]
    )

    return completion.choices[0].message


if __name__ == "__main__":

    filenames = ['pete_bradshaw', 'rains', 'rocket_league',
                 'twitch', 'warner_bros', 'youtube', 'ebay', 'guitar_chords']
    for filename in filenames:
        html_file = f'static/{filename}.html'

        html_content = read_html_file(html_file)

        max_html_tokens = 10000
        html_content = html_content[:max_html_tokens]

        print(filename)
        print(generate_summary(html_content))

        print()

        # print(summarise_styling(html_content))
