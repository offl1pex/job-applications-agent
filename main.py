from dotenv import load_dotenv
load_dotenv()
from openai import AsyncOpenAI
import asyncio
import json
from applications import add_application, list_applications, update_status, get_stats, followups, edit_application, delete_application
from search import search_docs


class Agent:
    def __init__(self, history_path='chat.json', apps_path='applications.json'):
        self.history_path = history_path
        self.apps_path = apps_path
        self.messages = [{
            'role': 'system',
            'content': '''Ты Job Applications Agent — помощник по учёту откликов на вакансии.
Статусы только: applied, interview, offer, rejected, ghosted.

Какой инструмент вызывать:
- «добавь отклик / подался в...» → add_application
- «покажи отклики / список» → list_applications
- «статистика / сколько» → get_stats
- «что напомнить / follow-up / давно без ответа» → followups
- смена статуса → update_status (нужен id из списка)
- если id неизвестен — сначала list_applications
- изменить отклик → edit_application
- удалить отклик → delete_application

Отвечай кратко. Не выдумывай id и статусы.
Когда показываешь список откликов, перечисляй все поля из результата tool:
id, компания, должность, дата, статус, заметка, ссылка.
Не сокращай и не выкидывай пустые заметки — пиши «нет».

Если вопрос про факты из базы знаний (Python, агенты, вакансии, термины) — сначала search_docs.
Отвечай по результату search_docs. Если «Ничего не найдено» — так и скажи, не выдумывай.
Заявки и статусы откликов — через tools откликов, не через search_docs.'''
        }]

        self.client = AsyncOpenAI()
        self.tools = [{
            'type': 'function',
            'function': {
                'name':  'add_application',
                'description': 'Добавить новый отклик на вакансию. Вызывать, когда пользователь сообщает, что откликнулся в компанию.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'company': {
                            'type': 'string',
                            'description': 'Название компании'
                        },
                        'position': {
                            'type': 'string',
                            'description': 'Название должности / вакансии'
                        },
                        'url': {
                            'type': 'string',
                            'description': 'Ссылка на вакансию, если есть'
                        },
                        'notes': {
                            'type': 'string',
                            'description': 'Заметка по отклику, если есть'
                        },
                    },
                    'required': ['company', 'position']
                }
            }
        }, {
            'type': 'function',
            'function': {
                'name':  'list_applications',
                'description': 'Показать список откликов с id, компанией, должностью, датой и статусом. Вызывать, когда просят показать, вывести или перечислить отклики.В ответе пользователю нужно передать все поля из результата функции, включая заметки и ссылки.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'status': {
                            'type': 'string',
                            'description': 'Фильтр по статусу: applied, interview, offer, rejected, ghosted. Если не указан — показать все.'
                        }
                    },
                    'required': []
                }
            }
        }, {
            'type': 'function',
            'function': {
                'name':  'update_status',
                'description': 'Изменить статус отклика по id. Статусы только: applied, interview, offer, rejected, ghosted.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'id': {
                            'type': 'integer',
                            'description': 'id отклика из списка'
                        },
                        'status': {
                            'type': 'string',
                            'description': 'Новый статус: applied, interview, offer, rejected или ghosted'
                        },
                    },
                    'required': ['id', 'status']
                }
            }
        }, {
            'type': 'function',
            'function': {
                'name':  'get_stats',
                'description': 'Краткая статистика: сколько откликов в каждом статусе и всего. Вызывать, когда просят статистику, итог или «сколько откликов».',
                'parameters': {
                    'type': 'object',
                    'properties': {
                    },
                    'required': []
                }
            }
        }, {
            'type': 'function',
            'function': {
                'name':  'followups',
                'description': 'Показать отклики со статусом applied или interview, по которым давно нет движения. Вызывать, когда просят напомнить, follow-up или «где давно тишина».',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'days': {
                            'type': 'integer',
                            'description': 'Сколько дней без обновления считать «давно». По умолчанию 7, если пользователь не указал.'
                        }
                    },
                    'required': []
                }
            }
        }, {
            'type': 'function',
            'function': {
                'name': 'edit_application',
                'description': 'Изменить поля отклика по id: company, position, url, notes. Меняются только переданные поля.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'id': {
                            'type': 'integer',
                            'description': 'id отклика'
                        },
                        'company': {
                            'type': 'string',
                            'description': 'Название компании'
                        },
                        'position': {
                            'type': 'string',
                            'description': 'Должность в компании'
                        },
                        'url': {
                            'type': 'string',
                            'description': 'Ссылка на вакансию'
                        },
                        'notes': {
                            'type': 'string',
                            'description': 'Заметка по отклику'
                        }
                    },
                    'required': ['id']
                }
            }
        }, {
            'type': 'function',
            'function': {
                'name': 'delete_application',
                'description': 'Удалить отклик по id. Вызывать, когда пользователь просит удалить заявку.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'id': {
                            'type': 'integer',
                            'description': 'id отклика'
                        }
                    },
                    'required': ['id']
                }
            }
        }, {
    'type': 'function',
    'function': {
        'name': 'search_docs',
        'description': (
            'Поиск по базе документов (docs). '
            'Вызывать для вопросов о терминах, Python, AI-агентах, откликах как теме — '
            'когда нужна информация из текстовой базы, а не список заявок пользователя.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Ключевая фраза или вопрос для смыслового поиска по документам'
                }
            },
            'required': ['query']
        }
    }
}
        ]

    def trim_history(self):
        system = self.messages[0]
        other = self.messages[1:][-20:]
        n = -20
        while other and other[0].get('role') == 'tool':
            n-=1
            other = self.messages[1:][n:]
        self.messages = [system] + other

    def load_messages(self):
        try:
            with open(self.history_path, 'r', encoding='utf-8') as file:
                self.messages = [self.messages[0]] + json.load(file)[1:]
        except FileNotFoundError:
            with open(self.history_path, 'w', encoding='utf-8') as file:
                json.dump(self.messages, file, ensure_ascii=False, indent=4)

    def save(self):
        self.trim_history()
        with open(self.history_path, 'w', encoding='utf-8') as file:
            json.dump(self.messages, file, ensure_ascii=False, indent=4)

    def clear(self):
        with open(self.history_path, 'w', encoding='utf-8') as file:
            json.dump([self.messages[0]], file, ensure_ascii=False, indent=4)
        return 'Успешная очистка истории'

    async def ask_model(self):
        response = await self.client.chat.completions.create(
            model='gpt-4.1-mini',
            tools=self.tools,
            max_completion_tokens=800,
            messages=self.messages
        )

        return response.choices[0].message

    def run_tool(self, name, args):
        try:
            if name == 'add_application':
                result = add_application(args['company'], args['position'], args.get('url', ''), args.get('notes', ''), path=self.apps_path)
            elif name == 'list_applications':
                result = list_applications(args.get('status', ''), path=self.apps_path)
            elif name == 'update_status':
                result = update_status(args['id'], args['status'], path=self.apps_path)
            elif name == 'get_stats':
                result = get_stats(path=self.apps_path)
            elif name == 'followups':
                result = followups(args.get('days') or 7, path=self.apps_path)
            elif name == 'edit_application':
                result = edit_application(args['id'], args.get('company', ''), args.get('position', ''), args.get('url', ''), args.get('notes', ''), path=self.apps_path)
            elif name == 'delete_application':
                result = delete_application(args['id'], path=self.apps_path)
            elif name == 'search_docs':
                result = search_docs(args['query'])
            else:
                return 'Неизвестная инструкция'
            return result
        except KeyError:
            return 'Неверно переданы аргументы'

    async def handle_tool_calls(self, message):
        for call in message.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments)
                result = self.run_tool(name, args)
            except json.JSONDecodeError:
                result = 'Не удалось разобрать аргументы'
            self.messages.append({
                'role': 'tool',
                'tool_call_id': call.id,
                'content': result
            })
        return await self.ask_model()

    async def chat(self, user_message):
        self.messages.append({
            'role': 'user',
            'content': user_message
        })
        message = await self.ask_model()
        if message.tool_calls:
            self.messages.append(message.model_dump())
            message = await self.handle_tool_calls(message)
        self.messages.append({
            'role': 'assistant',
            'content': message.content
        })
        return message.content

    async def run(self):
        self.load_messages()
        user_message = input('Ваш ввод: ')
        while user_message != 'выход':
            if user_message == 'сброс':
                print(self.clear())
                self.messages = [self.messages[0]]
            else:
                print(await self.chat(user_message))
                self.save()
            user_message = input('Ваш ввод: ')


if __name__ == "__main__":
    agent = Agent()
    asyncio.run(agent.run())