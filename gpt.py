import os
import openai
import json


def extract_json_from_text(text, prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant who extracts json data out of minimally structured text.",
            },
            {
                "role": "user",
                "content": f"{prompt}\n\nText:\n'''\n{text}\n'''",
            },
        ],
    )
    return json.loads(completion.choices[0].message.content)
