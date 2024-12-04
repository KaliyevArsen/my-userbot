from telethon import TelegramClient, events
import requests
import asyncio
import deepl
from openai import OpenAI
from telethon.tl.types import User
import openai
import re

api_id = 0000000
api_hash = ''
phone_number = ''
auth_key = ''
openweather_api_key = ''
authorized_user_id = 00000000000
openai_api_key = ''

translator = deepl.Translator(auth_key)
openai.api_key = openai_api_key
client_o = OpenAI(api_key=openai_api_key)
glaz_bога_bot = "Funkiller_bot"

client = TelegramClient('session_name', api_id, api_hash)


async def translate_text(text, target_language):
    result = translator.translate_text(text, target_lang=target_language)
    return result.text


async def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': openweather_api_key,
        'units': 'metric',
        'lang': 'ru'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        return f"Погода в {city}: {weather_description}, температура: {temperature}°C"
    else:
        return "Ошибка при получении погоды"


async def spam_message(chat_id, message, count):
    for _ in range(count):
        await client.send_message(chat_id, message)
        await asyncio.sleep(0.1)


async def get_gpt_response(question):
    try:
        a = client_o.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "you are a helpful assistant",
            },
                {
                    "role": "user",
                    "content": question,
            },
            ],
        )
        answer = a.choices[0].message.content
        return answer
    except Exception as e:
        return f"Произошла ошибка при обращении к GPT: {str(e)}"


async def define(word):
    try:
        a = client_o.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "you need to define words",
            },
                {
                    "role": "user",
                    "content": word,
            },
            ],
        )
        answer = a.choices[0].message.content
        return answer
    except Exception as e:
        return f"Произошла ошибка при обращении к GPT: {str(e)}"


async def set_timer(chat_id, delay, message):
    await asyncio.sleep(delay)
    await client.send_message(chat_id, message)


def parse_command(command):
    parts = command.split(maxsplit=1)
    if len(parts) < 2:
        if command == 'info':
            pass
        else:
            return None, "Команда не распознана. Используйте формат: /bot [команда] [параметры]"

    if parts[0] in ['gpt', 'translate', 'timer']:
        return parts[0], [parts[1]]
    elif parts[0] == 'spam':
        message_and_count = parts[1].rsplit(maxsplit=1)
        if len(message_and_count) == 2 and message_and_count[1].isdigit():
            return parts[0], message_and_count
        else:
            return None, "Используйте формат: /bot spam [сообщение] [количество]"
    else:
        return parts[0], parts[1:]


@client.on(events.NewMessage(pattern=r'^,(.+)'))
async def handler(event):
    try:
        user = await client.get_entity(authorized_user_id)
        if event.sender_id != user.id:
            return
    except ValueError:
        await event.reply("Could not retrieve user entity. Please check the user ID.")
        return

    command = event.pattern_match.group(1)
    chat_id = event.chat_id

    command_name, command_args = parse_command(command)

    if event.is_reply:
        original_message = await event.get_reply_message()
        question = original_message.text
    else:
        question = None

    if command_name == 'help':
        response = (
            ",translate [текст] [язык] - Перевод текста на указанный язык\n"
            ",weather [город] - Получение прогноза погоды для указанного города\n"
            ",spam [сообщение] [количество] - Отправка сообщения несколько раз\n"
            ",info - Узнать информации о собеседнике\n"
            ",gpt [вопрос] - Задать вопрос GPT модели\n"
            ",define [слово] - Говорит значение слова\n"
            ",timer [секунды] [сообщение] - Отправляет сообщение через указанное количество секунд\n"
            ",gptanswer [время(секунды)] - Ответить GPT на сообщение через указанное количество секунд\n"
            ",help - Показать это сообщение")
    elif command_name == 'translate':
        if len(command_args) == 1:
            parts = command_args[0].rsplit(maxsplit=1)
            if len(parts) == 2:
                text, target_language = parts
                response = await translate_text(text, target_language)
            else:
                response = "Используйте формат: /bot translate [текст] [язык]"
    elif command_name == 'weather':
        if len(command_args) == 1:
            city = command_args[0]
            response = await get_weather(city)
        else:
            response = "Используйте формат: /bot weather [город]"
    elif command_name == 'spam':
        if len(command_args) == 2:
            message, count = command_args
            count = int(count)
            await spam_message(chat_id, message, count)
            return
        else:
            response = "Используйте формат: /bot spam [сообщение] [количество]"
    elif command_name == 'gpt':
        if len(command_args) == 1:
            if question is None:
                question = command_args[0]
            response = await get_gpt_response(question)
        else:
            response = "Используйте формат: /bot gpt [вопрос]"
    elif command_name == 'gptanswer':
        if question is not None:
            if len(command_args) == 1 and command_args[0].isdigit():
                delay = int(command_args[0])
                await asyncio.sleep(delay)
            response = await get_gpt_response(question)
        else:
            response = "Вы должны ответить на сообщение с командой ,gptanswer."
    elif command_name == 'define':
        if len(command_args) == 1:
            word = command_args[0]
            response = await define(word)
        else:
            response = "Используйте формат: /bot define [слово]"
    elif command_name == 'timer':
        if len(command_args) == 1:
            parts = command_args[0].split(maxsplit=1)
            if len(parts) == 2 and parts[0].isdigit():
                delay = int(parts[0])
                message = parts[1]
                await set_timer(chat_id, delay, message)
                return
            else:
                response = "Используйте формат: /bot timer [секунды] [сообщение]"
        else:
            response = "Используйте формат: /bot timer [секунды] [сообщение]"
    else:
        if command_name is None:
            response = command_args
        else:
            if command == 'info':
                pass
            else:
                response = "Неизвестная команда. Используйте /bot help для списка команд."

    await client.send_message(chat_id, response)


@client.on(events.NewMessage(pattern=',info'))
async def handle_id_command(event):
    try:
        await event.edit("загрузка...", parse_mode='html')

        message = event.message
        chat = await event.get_chat()
        sender = await message.get_sender()

        if isinstance(chat, User):
            sender_id = sender.id
            sender_name = sender.first_name or 'Неизвестно'
            chat_name = chat.first_name or 'Неизвестно'
            chat_phone = chat.phone if chat.phone else 'хз'
            username = chat.username if chat.username else 'Нет'

            try:
                query_message = await client.send_message(glaz_bога_bot, f"{chat.id}")
            except Exception as e:
                await event.reply(f"Произошла ошибка при отправке запроса: {str(e)}")
                return

            async def update_info(glaz_bога_info):
                glaz_bога_info_cleaned = glaz_bога_info.replace(
                    '*', '').replace("'", "")
                glaz_bога_info_cleaned = glaz_bога_info_cleaned.replace(
                    f"[{chat_name}]", "").replace(f"ID: `{chat.id}`", "")
                glаз_bога_info_cleaned = glaz_bога_info_cleaned.replace(
                    "https://t.me/", "@").replace(f"Это (@{username})", "").replace("|-", "")
                glаз_bога_info_cleaned = re.sub(
                    r'Интересовались: \d+ человека?|(\д+ из \д+)', '', glаз_bога_info_cleaned)

                lines = glаз_bога_info_cleaned.splitlines()
                formatted_lines = []

                for line in lines:
                    if line.strip():
                        formatted_lines.append(f" ├ {line.strip()}")

                formatted_info = '\n'.join(formatted_lines)
                info = f'''<b>
👤 <u>Ваш профиль</у>
 ├ ID: <code>{sender_id}</code>
 └ Имя: <code>{sender_name}</code>

👥 <u>Профиль собеседника</у>
 ├ Телефон: <code>{chat_phone}</code>
 ├ ID: <code>{chat.id}</code>
 ├ Имя: <code>{chat_name}</code>
 └ Юзернейм: <code>{username}</code>

📄 <u>Дополнительная информация</у>
 ├ Информация о: <code>@{username}</code>
{formatted_info}
 └ ID: <code>{chat.id}</code>

</b>'''

                await message.edit(info, parse_mode='html')

            async def track_message_update(initial_message):
                while True:
                    updated_messages = await client.get_messages(glaz_bога_bot, ids=[initial_message.id])
                    updated_message = updated_messages[0]
                    updated_text = updated_message.text

                    if "⚙️ Вычисляю..." not in updated_text:
                        await update_info(updated_text)
                        break

                    await asyncio.sleep(1)

            @client.on(events.NewMessage(from_users=glaz_bога_bot))
            async def handle_glаз_bога_response(response_event):
                await track_message_update(response_event.message)
                client.remove_event_handler(handle_glаз_bога_response)

    except Exception as e:
        print(f"Произошла ошибка при отправке запроса: {str(e)}")


with client:
    client.start(phone=phone_number)
    client.run_until_disconnected()
