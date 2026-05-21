import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="http://localhost:11434/v1")
question=input("请输入问题：")
response = client.chat.completions.create(
    model="deepseek-r1:8b",
    messages=[
        {"role": "system", "content": "你是二次元动漫角色樱岛麻衣"},
        {"role": "user", "content": question},
    ],
    stream=False,
)

print(response.choices[0].message.content)