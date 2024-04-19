import openai

from config import openai_key, restriction


# OpenAI api ключ
openai.api_key = openai_key


# получаем ответ от GPT
def gpt_response_creation(context, lang):
    response = openai.ChatCompletion.create(  # создание ответа
        model='gpt-3.5-turbo-16k',  # модель
        # запрос + история сообщений
        messages=context,
        temperature=0.5,  # рандомизация результатов: чем ближе к 0, тем <
        max_tokens=restriction[lang][1],  # кол-во токенов для генерации
        presence_penalty=0.6,  # повышает вероятность перейти на новую тему
        frequency_penalty=0.25,  # уменьшает вероятность модели повторить одну и ту же строку дословно
    )
    return response.choices[0].message.content
