import json

from langchain.prompts.chat import (
    AIMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models.gigachat import GigaChat

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, html
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters.command import Command

messages = []
secrets = {}
with open("secrets.json", "r") as f:
    secrets = json.load(f)

class StreamHandler(BaseCallbackHandler):
    def __init__(self, initial_text=""):
        pass

    def on_llm_new_token(self, token: str, **kwargs):
        print(f"{token} -", end="", flush=True)

giga = GigaChat(model="GigaChat-Pro", credentials=secrets["authorization_data"], streaming=True, callbacks=[StreamHandler()], verify_ssl_certs=False)

first_option = types.InlineKeyboardButton(text='1', callback_data='1')
second_option = types.InlineKeyboardButton(text='2', callback_data='2')
third_option = types.InlineKeyboardButton(text='3', callback_data='3')
fourth_option = types.InlineKeyboardButton(text='4', callback_data='4')
options_keyboard = types.InlineKeyboardMarkup(
	inline_keyboard=[
		[
			first_option,
			second_option,
			third_option,
			fourth_option
		]
	]
)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=secrets["token"])
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
	await message.answer(
	    text=''.join((
			f"Привет, <b>{message.from_user.full_name}</b>!\n",
			"Ты попал в текстовый квест!\n",
			"Для запуска квеста введи комманду - /quest"
		)),
	    parse_mode=ParseMode.HTML
	)
	

@dp.message(Command("quest"))
async def cmd_quest(message: types.Message):
	if len(message.text.split()) == 1:
		await message.reply(
			text=''.join((
				f"Неправильный формат!\n",
				"<blockquote>/quest тема</blockquote>\n"
			)),
			parse_mode=ParseMode.HTML
		)
		
	else:
		messages.clear()
		messages.append(HumanMessage(
			content=''.join((
				f'Создай текстовый квест на тему "{message.text[7:]}" с 4 вариантами ответов.\n',
				"Примечания: Не отвечай за меня; не повторяй в последующих действиях, действия, которые встречались раннее в диалоге; всегда должно быть 4 интересных варианта последующих действий.\n",
				"В формате:\n",
				"Описание действий, локации и т.п.\n"
				"[1] Первый вариант последующего действия ",
				"[2] Второй вариант последующего действия ",
				"[3] Третий вариант последующего действия ",
				"[4] Четвёртый вариант последующего действия\n",
			))
		))
		
		messages.append(giga(messages))
	
		await message.answer(messages[-1].content, reply_markup=options_keyboard)

@dp.callback_query()
async def callback_query_handler(callback_query: types.CallbackQuery):
	await bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id, 
        reply_markup=None
    )

	messages.append(HumanMessage(
		content=f"[{callback_query.data}]"
	))
	
	messages.append(giga(messages))

	await bot.send_message(chat_id=callback_query.from_user.id, text=messages[-1].content, reply_markup=options_keyboard)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
