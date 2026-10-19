import json
from datetime import datetime
from pathlib import Path


def load(path='applications.json'):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save(data, path='applications.json'):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_application(company, position, url='', notes='', path='applications.json'):
    appls = load(path)
    company = company.strip()
    position = position.strip()
    if company and position:
        application = {
            'id': len(appls) + 1,
            'company': company,
            'position': position,
            'status': 'applied',
            'url': url,
            'applied_at': datetime.now().strftime('%Y-%m-%d'),
            'notes': notes
        }
        appls.append(application)
        save(appls, path)
        return f'''Отклик #{application['id']} добавлен: {application['company']} - {application['position']}'''
    else:
        return 'Название компании или должности не должны быть пустыми!'


def edit_application(id, company='', position='', url='', notes='', path='applications.json'):
    appls = load(path)
    if appls:
        for appl in appls:
            if str(appl['id']) == str(id):
                if company:
                    appl['company'] = company
                if position:
                    appl['position'] = position
                if url:
                    appl['url'] = url
                if notes:
                    appl['notes'] = notes
                save(appls, path)
                return f'''Отклик #{id} теперь имеет вид: {appl['company']} | {appl['position']} | {appl['notes']} | {appl['status']} | {appl['applied_at']}'''
        return f'''Отклика #{id} нет в системе'''
    else:
        return 'На данный момент откликов на вакансии нет'


def delete_application(id, path='applications.json'):
    appls = load(path)
    if appls:
        for i in range(len(appls)):
            if str(appls[i]['id']) == str(id):
                del appls[i]
                save(appls, path)
                return f'''Удален отклик #{id}'''
        return f'''Отклика #{id} нет в системе'''
    else:
        return 'На данный момент откликов на вакансии нет'


def list_applications(status='', path='applications.json'):
    appls = load(path)
    statuses = ['applied', 'interview', 'offer', 'rejected', 'ghosted']
    if appls:
        if status:
            if status in statuses:
                application = [f'''#{appl['id']} | {appl['company']} | {appl['position']} | {appl['applied_at']} | {appl['status']}\nЗаметка: {appl['notes'] if appl['notes'] else 'нет'} \nУточняющая ссылка: {appl['url'] if appl['url'] else 'нет'}''' for appl in appls if appl['status'] == status]
                if not application:
                    return f'''Откликов на вакансии со статусом "{status}" отсутствуют'''
            else:
                return 'Неверно передан статус для фильтрации'
        else:
            application = [f'''#{appl['id']} | {appl['company']} | {appl['position']} | {appl['applied_at']} | {appl['status']}\nЗаметка: {appl['notes'] if appl['notes'] else 'нет'} \nУточняющая ссылка: {appl['url'] if appl['url'] else 'нет'}''' for appl in appls]
    else:
        return 'На данный момент откликов на вакансии нет'
    return '\n'.join(application)


def update_status(id, status, path='applications.json'):
    appls = load(path)
    statuses = ['applied', 'interview', 'offer', 'rejected', 'ghosted']
    if status in statuses:
        if appls:
            appl = [appl for appl in appls if str(appl['id']) == str(id)]
            if appl:
                appl[0]['status'] = status
                save(appls, path)
            else:
                return f'''Отклика на вакансию с id:{id} -  нет'''
        else:
            return 'На данный момент откликов на вакансии нет'
    else:
        return f'''Статус: "{status}" нет в предусмотренных для установки на отклики'''
    return f'''Отклик #{id} -> {status}'''


def get_stats(path='applications.json'):
    appls = load(path)
    if appls:
        applied = len([appl for appl in appls if appl['status'] == 'applied'])
        interview = len([appl for appl in appls if appl['status'] == 'interview'])
        offer = len([appl for appl in appls if appl['status'] == 'offer'])
        rejected = len([appl for appl in appls if appl['status'] == 'rejected'])
        ghosted = len([appl for appl in appls if appl['status'] == 'ghosted'])
    else:
        return 'На данный момент откликов на вакансии нет'
    return f'''applied: {applied}\ninterview: {interview}\noffer: {offer}\nrejected: {rejected}\nghosted: {ghosted}\nВсего: {len(appls)}'''


def followups(days=7, path='applications.json'):
    appls = load(path)
    if appls:
        try:
            appls_deadline = [f'''#{appl['id']} | {appl['company']} | {appl['position']} | {appl['applied_at']} | {appl['status']}''' for appl in appls if (appl['status'] == 'applied' or appl['status'] == 'interview') and (datetime.now() - datetime.strptime(appl['applied_at'], '%Y-%m-%d')).days >= days]
            if not appls_deadline:
                return 'Пока нечего напоминать'
            return '\n'.join(appls_deadline)
        except ValueError:
            return 'Упс... пришла битая или пустая дата'
    else:
        return 'На данный момент откликов на вакансии нет'