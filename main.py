import discord
from discord.ext import commands, tasks
import random
import os
from dotenv import load_dotenv
import json
import sys
import asyncio
from discord.ui import Button, View
from datetime import datetime
import logging
from datetime import datetime
from datetime import datetime, timedelta

##############################################
####DEV BY THEDELF, ATLANTIC DIGITAL CLOUD####
##############################################

#Настройки ежедневного бонуса
DAILY_BONUS = {
    "min": 550,      # Минимальная награда
    "max": 1550,     # Максимальная награда
    "streak_bonus": {  # Бонусы за серию дней
        3: 3000,
        7: 7000,
        30: 30000
    }
}

BUSINESS_TYPES = {
    1: {"name": "Кофейня", "income": [10000, 11500], "upgrade_cost": 15000, "emoji": "☕", "capacity": 15000},
    2: {"name": "Каршеринг", "income": [50000, 200000], "upgrade_cost": 500000, "emoji": "🍽️", "capacity": 500000},
    3: {"name": "Наркобарон", "income": [200000, 350000], "upgrade_cost": 2500000, "emoji": "🏭", "capacity": 2500000}
}

@tasks.loop(minutes=60)
async def business_income():
    for user_id, biz in user_businesses.items():
        biz_type = BUSINESS_TYPES[biz["type"]]

        # Накопление, но не превышая лимит
        income = random.randint(biz_type["income"][0], biz_type["income"][1])
        biz["balance"] = min(biz.get("balance", 0) + income, biz_type["capacity"])

    save_businesses()

# Настройка логов
LOG_FILE = "bot.log"
ERROR_FILE = "errors.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE),
              logging.StreamHandler()])

error_logger = logging.getLogger('error_logger')
error_logger.addHandler(logging.FileHandler(ERROR_FILE))

#для лс
intents = discord.Intents.default()
intents.messages = True  # Для кнопок
intents.message_content = True  # Для чтения сообщений

# Загружаем токен из .env файла
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Настройки бота
PREFIX = '!'  # Префикс команд

# Валюта казино (можно изменить)
CURRENCY = "💰"

# Начальный баланс для новых игроков
STARTING_BALANCE = 1000

# Балансы игроков (хранится в памяти, для постоянного хранения нужно добавить БД)
user_balances = {}

#для бд
BALANCES_FILE = "user_balances.json"  # Файл для хранения балансов

# Настройки уровней
LEVELS_FILE = "user_levels.json"
XP_PER_MESSAGE = 1
XP_PER_MINUTE_VOICE = 2
LEVEL_UP_XP = 100  # Опыт для повышения уровня

# Список статусов для ротации
STATUS_ROTATION = [
    discord.Activity(type=discord.ActivityType.playing, name="в казино"),
    discord.Activity(type=discord.ActivityType.listening, name="ставки"),
    discord.Activity(type=discord.ActivityType.playing, name="с кодом"),
    discord.Activity(type=discord.ActivityType.listening, name="ваши команды"),
    discord.Activity(type=discord.ActivityType.watching, name="за сервером"),
    discord.Game(name=f"{PREFIX}помощь"),
    discord.Streaming(name="Разработку", url="https://twitch.tv/discord")
]

# Ответы на вопросы
RESPONSES = [
    "Бесспорно!", "Предрешено.", "Никаких сомнений.", "Определённо да!",
    "Можешь быть уверен в этом.", "Мне кажется — «да».", "Вероятнее всего.",
    "Хорошие перспективы.", "Знаки говорят — «да».",
    "Пока не ясно, попробуй снова.", "Спроси позже.", "Лучше не рассказывать.",
    "Сейчас нельзя предсказать.", "Сконцентрируйся и спроси опять.",
    "Даже не думай!", "Мой ответ — «нет».", "По моим данным — «нет».",
    "Перспективы не очень хорошие.", "Весьма сомнительно.", "Бля хуй знает.",
    "Иди нахуй."
]

#Для бонуса
def save_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Добавьте это в раздел с другими функциями загрузки/сохранения
def load_levels():
    try:
        if os.path.exists(LEVELS_FILE):
            with open(LEVELS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки уровней: {e}")
    return {}


def save_levels():
    try:
        with open(LEVELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_levels, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения уровней: {e}")


# Инициализация базы уровней
user_levels = load_levels()

#БД ДЛЯ ГЕЕВ
MARRIAGE_FILE = "marriages.json"

# Для сохранения бд бизнесов
def load_businesses():
    try:
        with open('businesses.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_businesses():
    with open('businesses.json', 'w') as f:
        json.dump(user_businesses, f, indent=4)

# Инициализация при запуске
user_businesses = load_businesses()

# Проверка прав администратора
def is_admin(ctx):
    # Проверка прав администратора сервера
    if ctx.author.guild_permissions.administrator:
        return True

    # Проверка ID пользователя
    with open('config.json', 'r') as f:
        config = json.load(f)
        return str(ctx.author.id) in config.get('admin_ids', [])

def load_marriages():
    try:
        with open(MARRIAGE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_marriages():
    with open(MARRIAGE_FILE, 'w') as f:
        json.dump(marriages, f, indent=4)


marriages = load_marriages()


#бд
def load_balances():
    """Загружает балансы из файла"""
    try:
        if os.path.exists(BALANCES_FILE):
            with open(BALANCES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки базы: {e}")
    return {}


def save_balances():
    """Сохраняет балансы в файл"""
    try:
        with open(BALANCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_balances, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")


user_levels = load_levels()
# Инициализация базы
user_balances = load_balances(
)  # ← Эта строка ЗАМЕНЯЕТ ваш старый пустой словарь `user_balances = {}`

# Инициализация бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX,
                   intents=intents,
                   activity=discord.Game(name="Загрузка..."),
                   status=discord.Status.online)

# Удаляем встроенную команду help
bot.remove_command('help')


# Событие при запуске бота
@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно подключился!')
    print(f'ID: {bot.user.id}')
    print(f'Серверов: {len(bot.guilds)}')
    print('------')
    status_task.start()


#Система уровней
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)

    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "voice_minutes": 0}

    old_level = user_levels[user_id]["level"]
    user_levels[user_id]["xp"] += XP_PER_MESSAGE

    # Проверка повышения уровня
    if user_levels[user_id]["xp"] >= (user_levels[user_id]["level"] *
                                      LEVEL_UP_XP):
        user_levels[user_id]["level"] += 1
        try:
            embed = discord.Embed(
                title=f"🎉 Новый уровень!",
                description=
                f"Поздравляем! Вы достигли уровня {user_levels[user_id]['level']}!",
                color=discord.Color.green())
            embed.add_field(name="Сервер",
                            value=message.guild.name,
                            inline=False)
            embed.add_field(
                name="Текущий опыт",
                value=
                f"{user_levels[user_id]['xp']}/{user_levels[user_id]['level'] * LEVEL_UP_XP}",
                inline=True)
            await message.author.send(embed=embed)
        except discord.Forbidden:
            pass  # Если пользователь запретил ЛС

        await message.channel.send(
            f"🎉 {message.author.mention} достиг уровня {user_levels[user_id]['level']}!",
            delete_after=10)

    save_levels()
    await bot.process_commands(message)


# Трекинг голосовой активности
@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    user_id = str(member.id)

    # Инициализация профиля
    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "voice_minutes": 0}

    # Начало разговора
    if before.channel is None and after.channel is not None:
        user_levels[user_id]["voice_start"] = datetime.now().timestamp()

    # Конец разговора
    elif before.channel is not None and after.channel is None:
        if "voice_start" in user_levels[user_id]:
            minutes = int((datetime.now().timestamp() -
                           user_levels[user_id]["voice_start"]) / 60)
            user_levels[user_id]["voice_minutes"] += minutes
            user_levels[user_id]["xp"] += minutes * XP_PER_MINUTE_VOICE
            del user_levels[user_id]["voice_start"]
            save_levels()


# Задача для смены статуса
@tasks.loop(minutes=5)
async def status_task():
    await bot.change_presence(activity=random.choice(STATUS_ROTATION))


# Кастомная команда помощи
@bot.command(name='помощь', help='Показывает список команд')
async def custom_help(ctx):
    embed = discord.Embed(title="📜 Список команд",
                          description=f"Префикс команд: `{PREFIX}`",
                          color=discord.Color.blurple())

    commands_list = [
        ("помощь", "Показать это сообщение"),
        ("вопрос <вопрос>", "Задать вопрос боту"),
        ("инфо", "Информация о боте"),
        ("баланс", "Показать ваш баланс"),
        ("кости <ставка>", "Игра в кости против бота"),
        ("казино <ставка> <цвет/число>",
         "Игра в рулетку (красное/черное/число)"),
        ("перевод @игрок сумма", "Перевести деньги другому игроку"),
        ("жениться @User", "Предложение для брака"),
        ("семейныйбюджет положить сумма", "Пополнить семейный бюджет"),
        ("брак @User", "Проверяет брак у участника"),
        ("уровень [@игрок]", "Показать уровень"),
        ("бонус", "Выдает ежедневный бонус"),
        ("данет", "Бот отвечает на вопрос ответом да или нет"),
        ("работы", "Показать все способы заработка"),
        ("бизнес", "Информация о вашем бизнесе"),
        ("купитьбизнес", "Купить начальный бизнес (15000💰)"),
        ("улучшитьбизнес", "Улучшить бизнес до следующего уровня"),
        ("забратьденьги [сумма|all]", "Снять деньги с бизнеса"),
        ("назватьбизнес [имя]", "Переименовать бизнес"),
        ("секс @User", "Позволяет занятся любовью с другим пользователем"),
        ("статус <текст>", "Изменить статус бота (ADMIN)"),
        ("сетбаланс @игрок сумма", "Установить баланс игрока (ADMIN)"),
        ("сетуровень @игрок уровень", "Установить уровень (ADMIN)"),
        ("выдатьопыт @игрок количество", "Выдать опыт (ADMIN)"),
        ("рестарт", "Перезагрузить бота (ADMIN)"),
    ]

    for cmd, desc in commands_list:
        embed.add_field(name=f"`{PREFIX}{cmd}`", value=desc, inline=False)

    await ctx.send(embed=embed)

# Команда Инфо
@bot.command(name='инфо')
async def bot_info(ctx):
    embed = discord.Embed(title="🤖 Информация о боте",
                          color=discord.Color.gold())
    embed.add_field(name="Разработчик", value="TheDelf", inline=True)
    embed.add_field(name="Версия", value="1.1", inline=True)
    embed.add_field(name="Библиотека",
                    value=f"discord.py {discord.__version__}",
                    inline=True)
    embed.add_field(name="Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="Пинг",
                    value=f"{round(bot.latency * 1000)}мс",
                    inline=True)
    embed.set_footer(text=f"ID: {bot.user.id}")

    await ctx.send(embed=embed)


@bot.command(name='вопрос')
async def ask_question(ctx, *, question):
    if not question.endswith('?'):
        await ctx.send("Добавьте '?' в конце вопроса.")
        return

    response = random.choice(RESPONSES)
    embed = discord.Embed(
        title="🤔 Я думаю",
        description=f"**Вопрос:** {question}\n**Ответ:** {response}",
        color=discord.Color.dark_purple())
    await ctx.send(embed=embed)


@bot.command(name='статус')
@commands.has_permissions(administrator=True)
async def set_custom_status(ctx, *, text):
    await bot.change_presence(activity=discord.Game(name=text))
    embed = discord.Embed(description=f"✅ Статус изменен на: `{text}`",
                          color=discord.Color.green())
    await ctx.send(embed=embed)


# Команда казино
@bot.command(name='казино', aliases=['casino', 'рулетка'])
async def casino(ctx, bet: int, *, choice: str):
    user_id = str(ctx.author.id)

    # Инициализация баланса
    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    # Проверки ставки
    if bet <= 0:
        await ctx.send("❌ Ставка должна быть положительной!")
        return
    if user_balances[user_id] < bet:
        await ctx.send(f"❌ Недостаточно средств! Ваш баланс: {user_balances[user_id]}{CURRENCY}")
        return

    # Генерация результата (0-36)
    result = random.randint(0, 36)
    is_red = result in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    sector = "🔵 Ноль" if result == 0 else "🔴 Красное" if is_red else "⚫ Черное"

    # Определяем сектор (1-12, 13-24, 25-36)
    sector_num = (result - 1) // 12 + 1 if result != 0 else 0

    # Проверка выигрыша
    win = 0
    response = ""

    # Ставка на число
    if choice.isdigit():
        if int(choice) == result:
            win = bet * 35
            response = f"🎉 Вы угадали число! Выигрыш: {win}{CURRENCY}"
        else:
            response = f"❌ Не угадали. Выпало: {result} ({sector})"

    # Ставка на цвет
    elif choice.lower() in ["красное", "красный", "red"]:
        if is_red and result != 0:
            win = bet * 2
            response = f"🎉 Красное! Выигрыш: {win}{CURRENCY}"
        else:
            response = f"❌ Не красное. Выпало: {result} ({sector})"

    elif choice.lower() in ["черное", "черный", "black"]:
        if not is_red and result != 0:
            win = bet * 2
            response = f"🎉 Черное! Выигрыш: {win}{CURRENCY}"
        else:
            response = f"❌ Не черное. Выпало: {result} ({sector})"

    # Ставка на сектор (1-й, 2-й, 3-й)
    elif choice.lower() in ["1 сектор", "первый сектор", "sector1"]:
        if 1 <= result <= 12:
            win = bet * 3
            response = f"🎉 1-й сектор (1-12)! Выигрыш: {win}{CURRENCY}"
        else:
            response = f"❌ Не 1-й сектор. Выпало: {result} ({sector})"

    elif choice.lower() in ["2 сектор", "второй сектор", "sector2"]:
        if 13 <= result <= 24:
            win = bet * 3
            response = f"🎉 2-й сектор (13-24)! Выигрыш: {win}{CURRENCY}"
        else:
            response = f"❌ Не 2-й сектор. Выпало: {result} ({sector})"

    elif choice.lower() in ["3 сектор", "третий сектор", "sector3"]:
        if 25 <= result <= 36:
            win = bet * 3
            response = f"🎉 3-й сектор (25-36)! Выигрыш: {win}{CURRENCY}"
        else:
            response = f"❌ Не 3-й сектор. Выпало: {result} ({sector})"

    else:
        await ctx.send("❌ Неправильная ставка! Варианты: число (0-36), цвет (красное/черное), сектор (1-й/2-й/3-й)")
        return

    # Обновление баланса
    user_balances[user_id] += win - bet if win > 0 else -bet
    save_balances()

    # Отправка результата
    embed = discord.Embed(
        title=f"🎰 Рулетка: {result} {sector}",
        description=response,
        color=0x2F3136
    )
    embed.add_field(name="Текущий баланс", value=f"{user_balances[user_id]}{CURRENCY}")
    await ctx.send(embed=embed)

# Команда баланса
@bot.command(name='баланс', help='Показывает ваш текущий баланс')
async def balance(ctx):
    user_id = str(ctx.author.id)
    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE
        save_balances()
    await ctx.send(f"Ваш баланс: {user_balances[user_id]}{CURRENCY}")


# Команда кости
@bot.command(name='кости', help='Игра в кости: !кости <ставка>')
async def dice(ctx, bet: int):
    user_id = str(ctx.author.id)

    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    if bet <= 0:
        await ctx.send("Ставка должна быть положительной!")
        return
    if user_balances[user_id] < bet:
        await ctx.send(
            f"Недостаточно средств! Ваш баланс: {user_balances[user_id]}{CURRENCY}"
        )
        return

    # Бросок костей
    player_roll = random.randint(1, 6) + random.randint(1, 6)
    bot_roll = random.randint(1, 6) + random.randint(1, 6)

    if player_roll > bot_roll:
        win = bet
        user_balances[user_id] += win
        await ctx.send(
            f"🎲 Вы: {player_roll} | Бот: {bot_roll}\n🎉 Вы выиграли {win}{CURRENCY}!"
        )
    elif player_roll < bot_roll:
        user_balances[user_id] -= bet
        await ctx.send(
            f"🎲 Вы: {player_roll} | Бот: {bot_roll}\n❌ Вы проиграли {bet}{CURRENCY}!"
        )
    else:
        await ctx.send(
            f"🎲 Вы: {player_roll} | Бот: {bot_roll}\n🤝 Ничья! Ставка возвращена."
        )
        save_balances()


#изменение баланса игроку через админа
@bot.command(name='сетбаланс')
async def set_balance(ctx, member: discord.Member, amount: int):
    if not is_admin(ctx):
        await ctx.send("❌ Недостаточно прав!")
        return

    user_balances[str(member.id)] = amount
    save_balances()

    await ctx.send(f"✅ Баланс {member.mention} установлен: {amount}{CURRENCY}")


#перевод денег с баланса на баланс
@bot.command(name='перевод',
             aliases=['transfer'],
             help='Перевести деньги другому игроку: !перевод @игрок сумма')
async def transfer_money(ctx, member: discord.Member, amount: int):
    try:
        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)

        # Проверки
        if amount <= 0:
            await ctx.send("❌ Сумма должна быть больше нуля!")
            return

        if sender_id == receiver_id:
            await ctx.send("❌ Нельзя переводить себе!")
            return

        # Инициализация балансов при необходимости
        if sender_id not in user_balances:
            user_balances[sender_id] = STARTING_BALANCE

        if receiver_id not in user_balances:
            user_balances[receiver_id] = STARTING_BALANCE

        if user_balances[sender_id] < amount:
            await ctx.send(
                f"❌ Недостаточно средств! Ваш баланс: {user_balances[sender_id]}{CURRENCY}"
            )
            return

        # Перевод денег
        user_balances[sender_id] -= amount
        user_balances[receiver_id] += amount
        save_balances()

        # Успешное сообщение
        embed = discord.Embed(
            title="✅ Перевод выполнен",
            description=f"{ctx.author.mention} → {member.mention}",
            color=discord.Color.green())
        embed.add_field(name="Сумма",
                        value=f"{amount}{CURRENCY}",
                        inline=False)
        embed.add_field(name="Ваш новый баланс",
                        value=f"{user_balances[sender_id]}{CURRENCY}",
                        inline=True)
        embed.add_field(name="Баланс получателя",
                        value=f"{user_balances[receiver_id]}{CURRENCY}",
                        inline=True)

        await ctx.send(embed=embed)

    except Exception as e:
        error_embed = discord.Embed(title="❌ Ошибка перевода",
                                    description=f"Произошла ошибка: {str(e)}",
                                    color=discord.Color.red())
        await ctx.send(embed=error_embed)
        print(f"Ошибка в переводе: {e}")


# команда перезапуска бота
@bot.command(name='рестарт',
             aliases=['restart'],
             help='Полная перезагрузка бота (ТОЛЬКО АДМИН)')
@commands.has_permissions(administrator=True)
async def restart_bot(ctx):
    try:
        # 1. Сохраняем данные и уведомляем о начале перезагрузки
        save_balances()
        embed = discord.Embed(
            title="🔄 Перезагрузка бота",
            description="Бот будет перезагружен через 3 секунды...",
            color=discord.Color.orange())
        await ctx.send(embed=embed)
        await asyncio.sleep(1)

        # 2. Отправляем сообщение в лог-канал (если нужно)
        log_channel = bot.get_channel(
            1400538179097985209)  # Замените на реальный ID
        if log_channel:
            await log_channel.send(
                f"🔧 Бот перезагружается по команде от {ctx.author.mention}")

        # 3. Фиксируем время перезагрузки
        with open("restart_time.txt", "w") as f:
            f.write(str(ctx.message.created_at))

        # 4. Запускаем перезагрузку с визуальным отсчетом
        for i in range(3, 0, -1):
            await ctx.send(f"⏳ Перезагрузка через {i}...")
            await asyncio.sleep(1)

        # 5. Перезапуск процесса
        python = sys.executable
        os.execl(python, python, *sys.argv)

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")


@bot.event
async def on_ready():
    # Проверяем факт перезагрузки
    if os.path.exists("restart_time.txt"):
        with open("restart_time.txt", "r") as f:
            restart_time = f.read()
        os.remove("restart_time.txt")

        # Отправляем сообщение о успешной перезагрузке
        channel = bot.get_channel(
            1400538179097985209)  # Замените на ID нужного канала
        if channel:
            embed = discord.Embed(
                title="✅ Бот успешно перезагружен",
                description=f"Последняя перезагрузка: {restart_time}",
                color=discord.Color.green())
            embed.set_footer(text=f"Версия {discord.__version__}")
            await channel.send(embed=embed)


#для работы с уровнем
@bot.command(name='уровень',
             aliases=['level', 'lvl'],
             help='Показывает ваш уровень')
async def show_level(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = str(target.id)

    if user_id not in user_levels:
        await ctx.send(f"{target.mention} еще не имеет уровня")
        return

    data = user_levels[user_id]
    embed = discord.Embed(title=f"📊 Уровень {target.display_name}",
                          color=discord.Color.blurple())
    embed.add_field(name="Уровень", value=data["level"], inline=True)
    embed.add_field(name="Опыт",
                    value=f"{data['xp']}/{data['level'] * LEVEL_UP_XP}",
                    inline=True)
    embed.add_field(name="Голосовой онлайн",
                    value=f"{data['voice_minutes']} мин.",
                    inline=True)
    embed.set_thumbnail(url=target.avatar.url)

    await ctx.send(embed=embed)

#установка уровня через админа
@bot.command(name='сетуровень', aliases=['setlevel'])
async def set_level(ctx, member: discord.Member, level: int):
    # Проверка прав
    if not is_admin(ctx):
        await ctx.send("❌ Только админы могут использовать эту команду!")
        return

    if level < 1:
        await ctx.send("❌ Уровень должен быть положительным!")
        return

    user_id = str(member.id)
    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "voice_minutes": 0}

    user_levels[user_id]["level"] = level
    user_levels[user_id]["xp"] = 0  # Сбрасываем опыт
    save_levels()

    embed = discord.Embed(
        title="✅ Уровень изменен",
        description=f"{member.mention} теперь {level} уровень",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

#добавить опыт участнику
@bot.command(name='выдатьопыт',
             aliases=['addxp'],
             help='Выдать опыт пользователю (ADMIN)')
@commands.check(is_admin)
async def give_xp(ctx, member: discord.Member, xp: int):
    user_id = str(member.id)

    # Проверки
    if xp <= 0:
        await ctx.send("❌ Количество опыта должно быть положительным!")
        return

    if member.bot:
        await ctx.send("❌ Нельзя выдавать опыт ботам!")
        return

    # Инициализация профиля
    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "voice_minutes": 0}

    old_level = user_levels[user_id]["level"]
    user_levels[user_id]["xp"] += xp

    # Проверка повышения уровня
    new_level = user_levels[user_id]["level"]
    while user_levels[user_id]["xp"] >= new_level * LEVEL_UP_XP:
        new_level += 1

    level_changed = new_level > old_level
    if level_changed:
        user_levels[user_id]["level"] = new_level

    save_levels()

    try:
        # Отправляем уведомление в ЛС пользователю
        dm_embed = discord.Embed(title="🎉 Вам выдали опыт!",
                                 color=discord.Color.gold())
        dm_embed.add_field(name="Сервер", value=ctx.guild.name, inline=False)
        dm_embed.add_field(name="Выдано опыта", value=str(xp), inline=True)
        dm_embed.add_field(
            name="Текущий опыт",
            value=f"{user_levels[user_id]['xp']}/{new_level * LEVEL_UP_XP}",
            inline=True)

        if level_changed:
            dm_embed.add_field(
                name="**Новый уровень!**",
                value=f"Поздравляем! Вы достигли уровня {new_level}!",
                inline=False)
            dm_embed.color = discord.Color.green()

        await member.send(embed=dm_embed)
    except discord.Forbidden:
        print(f"Не удалось отправить ЛС пользователю {member.name}")

    # Отчет в чат
    report_embed = discord.Embed(title="✅ Опыт успешно выдан",
                                 color=discord.Color.blurple())
    report_embed.add_field(name="Администратор",
                           value=ctx.author.mention,
                           inline=True)
    report_embed.add_field(name="Получатель",
                           value=member.mention,
                           inline=True)
    report_embed.add_field(name="Количество опыта",
                           value=str(xp),
                           inline=False)

    if level_changed:
        report_embed.add_field(name="Уровень повышен",
                               value=f"{old_level} → {new_level}",
                               inline=False)
        report_embed.color = discord.Color.green()

    await ctx.send(embed=report_embed)


@give_xp.error
async def give_xp_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(
            title="⛔ Ошибка",
            description="Только администраторы могут выдавать опыт!",
            color=discord.Color.red()))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=discord.Embed(
            title="❌ Неправильный синтаксис",
            description=f"Используйте: `{PREFIX}выдатьопыт @игрок количество`",
            color=discord.Color.orange()))
    else:
        await ctx.send(embed=discord.Embed(title="⚠️ Неизвестная ошибка",
                                           description=str(error),
                                           color=discord.Color.red()))


#сообшения в лс через бота
@bot.command(name='лс', aliases=['dm'])
@commands.has_permissions(administrator=True)
async def send_dm(ctx, member: discord.Member, *, message: str):
    """Отправляет ЛС через бота с кнопкой ответа"""
    try:
        # Проверка запрещённого контента
        if any(bad_word in message.lower()
               for bad_word in ["http://", "https://", "discord.gg/"]):
            await ctx.send("❌ Ссылки запрещены!", delete_after=5)
            return

        # Создаём View с кнопкой
        class ResponseView(discord.ui.View):

            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Ответить",
                               style=discord.ButtonStyle.green,
                               emoji="✉️")
            async def callback(self, interaction: discord.Interaction,
                               button: discord.ui.Button):
                try:
                    # Просим пользователя ввести ответ
                    await interaction.response.send_message(
                        "Напишите ваш ответ (у вас 5 минут):", ephemeral=True)

                    # Ждём ответ в ЛС
                    def check(m):
                        return m.author == interaction.user and isinstance(
                            m.channel, discord.DMChannel)

                    answer = await bot.wait_for('message',
                                                check=check,
                                                timeout=300)

                    # Отправляем ответ админу
                    await ctx.author.send(
                        f"**📩 Ответ от {interaction.user.mention}:**\n"
                        f"{answer.content}")

                    await interaction.followup.send("✅ Ответ отправлен!",
                                                    ephemeral=True)

                except asyncio.TimeoutError:
                    await interaction.followup.send("⏳ Время вышло!",
                                                    ephemeral=True)
                except Exception as e:
                    print(f"Ошибка кнопки: {e}")

        # Отправляем сообщение с кнопкой
        embed = discord.Embed(title=f"🔔 Сообщение от {ctx.guild.name}",
                              description=message,
                              color=discord.Color.blue())
        await member.send(embed=embed, view=ResponseView())
        await ctx.send(f"✅ Сообщение отправлено {member.mention}",
                       delete_after=5)

    except discord.Forbidden:
        await ctx.send("❌ Бот не может писать этому пользователю!",
                       delete_after=5)
    except Exception as e:
        print(f"Ошибка команды !личка: {e}")


# Команда свадьбы
@bot.command(name='жениться', aliases=['marry'])
async def marry(ctx, partner: discord.Member):
    author_id = str(ctx.author.id)
    partner_id = str(partner.id)

    if author_id == partner_id:
        await ctx.send("❌ Нельзя жениться на себе!")
        return

    if partner.bot:
        await ctx.send("❌ Боты не могут вступать в брак!")
        return

    # Проверка существующих браков
    for marriage in marriages.values():
        if author_id in marriage["partners"] or partner_id in marriage[
                "partners"]:
            await ctx.send("⛔ Один из вас уже состоит в браке!")
            return

    # Создаем View для кнопок
    class MarriageView(discord.ui.View):

        def __init__(self):
            super().__init__(timeout=60.0)

        @discord.ui.button(label="Принять",
                           style=discord.ButtonStyle.success,
                           emoji="💍")
        async def accept(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
            if interaction.user.id != partner.id:
                await interaction.response.send_message(
                    "❌ Это предложение не для вас!", ephemeral=True)
                return

            marriage_id = f"{min(author_id, partner_id)}_{max(author_id, partner_id)}"
            marriages[marriage_id] = {
                "partners": [author_id, partner_id],
                "date": datetime.now().isoformat(),
                "wallet": 0
            }
            save_marriages()

            embed = discord.Embed(
                title="💍 Брак заключен!",
                description=f"{ctx.author.mention} ❤️ {partner.mention}",
                color=discord.Color.pink())
            embed.add_field(name="Дата свадьбы",
                            value=datetime.now().strftime("%d.%m.%Y %H:%M"))
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()

        @discord.ui.button(label="Отказаться",
                           style=discord.ButtonStyle.danger,
                           emoji="❌")
        async def decline(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
            if interaction.user.id != partner.id:
                await interaction.response.send_message(
                    "❌ Это предложение не для вас!", ephemeral=True)
                return
            await interaction.response.edit_message(
                content=f"{partner.mention} отказался от предложения 😢",
                view=None)
            self.stop()

    # Отправка предложения
    embed = discord.Embed(
        title="💌 Предложение брака",
        description=
        f"{partner.mention}, {ctx.author.mention} предлагает вам вступить в брак!",
        color=discord.Color.gold())
    await ctx.send(embed=embed, view=MarriageView())


# Команда развода
@bot.command(name='развод', aliases=['divorce'])
async def divorce(ctx):
    author_id = str(ctx.author.id)

    # Поиск брака
    marriage = None
    for m in marriages.values():
        if author_id in m["partners"]:
            marriage = m
            break

    if not marriage:
        await ctx.send("❌ Вы не в браке!")
        return

    # Получаем партнера
    partner_id = next(p for p in marriage["partners"] if p != author_id)
    partner = await bot.fetch_user(int(partner_id))

    # Дележ имущества
    wallet = marriage["wallet"]
    half = wallet // 2

    # Удаление брака
    marriage_id = f"{min(marriage['partners'])}_{max(marriage['partners'])}"
    del marriages[marriage_id]
    save_marriages(marriages)

    # Уведомление
    embed = discord.Embed(
        title="💔 Брак расторгнут",
        description=
        f"{ctx.author.mention} и {partner.mention} больше не вместе",
        color=discord.Color.dark_grey())
    if wallet > 0:
        embed.add_field(name="Раздел имущества",
                        value=f"Каждый получает по {half} 💰")
    await ctx.send(embed=embed)


# Поиск брака
@bot.command(name='брак', aliases=['marriage'])
async def marriage_info(ctx, user: discord.Member = None):
    target = user or ctx.author
    target_id = str(target.id)

    # Поиск брака
    marriage = None
    for m in marriages.values():
        if target_id in m["partners"]:
            marriage = m
            break

    if not marriage:
        await ctx.send(f"❌ {target.mention} не в браке!")
        return

    # Получаем данные
    partner_id = next(p for p in marriage["partners"] if p != target_id)
    partner = await bot.fetch_user(int(partner_id))
    date = datetime.fromisoformat(marriage["date"]).strftime("%d.%m.%Y")

    # Создаем Embed
    embed = discord.Embed(title=f"💍 Брачный союз", color=discord.Color.pink())
    embed.add_field(name="Партнеры",
                    value=f"{target.mention} ❤️ {partner.mention}",
                    inline=False)
    embed.add_field(name="Дата свадьбы", value=date, inline=True)
    embed.add_field(name="Общий бюджет",
                    value=f"{marriage['wallet']} 💰",
                    inline=True)

    await ctx.send(embed=embed)


# Семейный бюджет
@bot.command(name='семейныйбюджет', aliases=['familywallet'])
async def family_wallet(ctx, action: str = None, amount: int = None):
    author_id = str(ctx.author.id)

    # Поиск брака
    marriage = None
    for m in marriages.values():
        if author_id in m["partners"]:
            marriage = m
            break

    if not marriage:
        await ctx.send("❌ Вы не в браке!")
        return

    # Получаем партнера
    partner_id = next(p for p in marriage["partners"] if p != author_id)
    partner = await bot.fetch_user(int(partner_id))

    if not action:
        # Просмотр баланса
        await ctx.send(f"💰 Общий бюджет: {marriage['wallet']} монет")
        return

    if action == "положить":
        # Проверка баланса пользователя
        if user_balances.get(author_id, 0) < amount:
            await ctx.send("❌ Недостаточно средств!")
            return

        # Перевод
        user_balances[author_id] -= amount
        marriage["wallet"] += amount
        save_balances()
        save_marriages(marriages)

        await ctx.send(f"✅ {amount} монет добавлено в семейный бюджет!")

    elif action == "снять":
        if marriage["wallet"] < amount:
            await ctx.send("❌ Недостаточно средств в бюджете!")
            return

        marriage["wallet"] -= amount
        user_balances[author_id] += amount
        save_balances()
        save_marriages(marriages)

        await ctx.send(f"✅ {amount} монет переведено вам!")


@bot.event
async def on_ready():
    logging.info(f"Бот запущен как {bot.user.name} (ID: {bot.user.id})")
    print("------")
    business_income.start()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    logging.debug(f"Сообщение от {message.author}: {message.content[:20]}...")
    await bot.process_commands(message)

#команда для получения ежедневного бонуса
@bot.command(name='бонус', aliases=['daily'])
@commands.cooldown(1, 86400, commands.BucketType.user)  # 24 часа
async def daily_bonus(ctx):
    user_id = str(ctx.author.id)

    # Инициализация данных
    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    if user_id not in user_levels:
        user_levels[user_id] = {"level": 1, "xp": 0, "voice_minutes": 0, "last_daily": None, "streak": 0}

    # Проверка срока последнего бонуса
    now = datetime.now()
    last_claim = datetime.fromisoformat(user_levels[user_id].get("last_daily", "2000-01-01"))

    # Сброс серии, если пропущен день
    if (now - last_claim) > timedelta(days=1):
        user_levels[user_id]["streak"] = 0

    # Начисление бонуса
    bonus = random.randint(DAILY_BONUS["min"], DAILY_BONUS["max"])
    streak = user_levels[user_id]["streak"] + 1

    # Добавляем бонус за серию
    extra = 0
    for days, reward in DAILY_BONUS["streak_bonus"].items():
        if streak >= days and streak % days == 0:
            extra += reward

    total = bonus + extra
    user_balances[user_id] += total
    user_levels[user_id]["streak"] = streak
    user_levels[user_id]["last_daily"] = now.isoformat()

    # Сохраняем данные (используем существующие функции)
    save_balances()  # Использует BALANCES_FILE
    save_levels()    # Использует LEVELS_FILE

    # Отправляем Embed
    embed = discord.Embed(
        title="🎁 Ежедневный бонус",
        color=discord.Color.gold()
    )
    embed.add_field(name="Основная награда", value=f"{bonus} {CURRENCY}", inline=True)
    if extra > 0:
        embed.add_field(name="Бонус за серию", value=f"+{extra} {CURRENCY}", inline=True)
    embed.add_field(name="Текущая серия", value=f"{streak} дней", inline=False)
    embed.add_field(name="Общий баланс", value=f"{user_balances[user_id]} {CURRENCY}", inline=False)
    embed.set_footer(text="Возвращайся завтра!")

    await ctx.send(embed=embed)
@daily_bonus.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining = str(timedelta(seconds=int(error.retry_after)))
        embed = discord.Embed(
            title="⏳ Уже получал сегодня!",
            description=f"Следующий бонус через {remaining}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠️ Ошибка: {str(error)}")

# Работы
@bot.command(name='работа', aliases=['work'])
@commands.cooldown(1, 43200, commands.BucketType.user)  # 12 часов
async def work(ctx):
    user_id = str(ctx.author.id)
    jobs = [
        ("разработчиком", 800, 1500),
        ("строителем", 500, 1000),
        ("дизайнером", 600, 1200),
        ("водителем", 400, 800),
        ("продавцом", 300, 700)
    ]

    job = random.choice(jobs)
    earnings = random.randint(job[1], job[2])

    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    user_balances[user_id] += earnings
    save_balances()

    embed = discord.Embed(
        title="💼 Работа",
        description=f"Вы поработали {job[0]} и заработали {earnings}{CURRENCY}!",
        color=discord.Color.green()
    )
    embed.set_footer(text="Следующая работа через 12 часов")
    await ctx.send(embed=embed)

# Работа: Криптовалюта
@bot.command(name='крипта', aliases=['crypto'])
async def crypto(ctx, amount: int):
    user_id = str(ctx.author.id)

    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной!")
        return

    if user_balances[user_id] < amount:
        await ctx.send("❌ Недостаточно средств!")
        return

    # Шанс 60% на прибыль, 40% на убыток
    if random.random() < 0.6:
        profit = round(amount * random.uniform(0.1, 0.5))
        user_balances[user_id] += profit
        result = f"✅ Вы заработали {profit}{CURRENCY} на крипте!"
    else:
        loss = round(amount * random.uniform(0.1, 0.3))
        user_balances[user_id] -= loss
        result = f"❌ Вы потеряли {loss}{CURRENCY} на крипте..."

    save_balances()

    embed = discord.Embed(
        title="₿ Криптовалюта",
        description=result,
        color=discord.Color.orange()
    )
    embed.add_field(name="Текущий баланс", value=f"{user_balances[user_id]}{CURRENCY}")
    await ctx.send(embed=embed)

#Ограбление банка
@bot.command(name='ограбление', aliases=['rob'])
@commands.cooldown(1, 86400, commands.BucketType.user)  # 24 часа
async def rob_bank(ctx):
    user_id = str(ctx.author.id)

    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    # 45% успеха, 55% провала
    if random.random() < 0.45:
        loot = random.randint(1000, 5000)
        user_balances[user_id] += loot
        result = f"🎉 Вы успешно ограбили банк и получили {loot}{CURRENCY}!"
        color = discord.Color.green()
    else:
        fine = random.randint(500, 2000)
        user_balances[user_id] = max(0, user_balances[user_id] - fine)
        result = f"🚔 Вас поймали! Штраф: {fine}{CURRENCY}"
        color = discord.Color.red()

    save_balances()

    embed = discord.Embed(
        title="🏦 Ограбление банка",
        description=result,
        color=color
    )
    embed.set_footer(text="Попробуете снова через 24 часа")
    await ctx.send(embed=embed)

#Рыбалка
@bot.command(name='рыбалка', aliases=['fish'])
@commands.cooldown(1, 14400, commands.BucketType.user)  # 4 часа
async def fishing(ctx):
    user_id = str(ctx.author.id)
    fish_types = [
        ("карася", 50, 100),
        ("окуня", 100, 200),
        ("щуку", 200, 400),
        ("леща", 150, 300),
        ("сом", 300, 600),
        ("старую покрышку", 0, 0)
    ]

    fish = random.choice(fish_types)

    if fish[0] == "старую покрышку":
        earnings = 0
        result = "Вы поймали старую покрышку... Ничего не заработали"
    else:
        earnings = random.randint(fish[1], fish[2])
        result = f"Вы поймали {fish[0]} и заработали {earnings}{CURRENCY}!"

    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE

    user_balances[user_id] += earnings
    save_balances()

    embed = discord.Embed(
        title="🎣 Рыбалка",
        description=result,
        color=discord.Color.blue()
    )
    embed.set_footer(text="Следующая рыбалка через 4 часа")
    await ctx.send(embed=embed)

#Работы "(HELP)"
@bot.command(name='работы', aliases=['jobs'])
async def jobs_list(ctx):
    embed = discord.Embed(
        title="💼 Доступные способы заработка",
        description=f"Все способы получения {CURRENCY}",
        color=discord.Color.gold()
    )

    jobs_info = [
        {
            "name": "!работа",
            "description": "Классическая работа с гарантированным доходом",
            "income": "500-1500",
            "cooldown": "12 часов",
            "risk": "Нет риска"
        },
        {
            "name": "!крипта [сумма]",
            "description": "Рискованные инвестиции в криптовалюту",
            "income": "+10-50% или -10-30% от суммы",
            "cooldown": "Нет",
            "risk": "Высокий"
        },
        {
            "name": "!ограбление",
            "description": "Попытать удачу в ограблении банка",
            "income": "1000-5000 или штраф 500-2000",
            "cooldown": "24 часа",
            "risk": "Очень высокий"
        },
        {
            "name": "!рыбалка",
            "description": "Спокойная рыбалка с переменным успехом",
            "income": "0-600 (можно поймать покрышку)",
            "cooldown": "4 часа",
            "risk": "Низкий"
        },
        {
            "name": "!бонус",
            "description": "Ежедневная награда (чем дольше серия - тем больше бонус)",
            "income": "550-1550 + бонусы за серию",
            "cooldown": "24 часа",
            "risk": "Нет риска"
        }
    ]

    for job in jobs_info:
        embed.add_field(
            name=f"**{job['name']}**",
            value=(
                f"{job['description']}\n"
                f"💵 Доход: {job['income']}\n"
                f"⏳ Восстановление: {job['cooldown']}\n"
                f"⚠️ Риск: {job['risk']}"
            ),
            inline=False
        )

    embed.set_footer(text=f"Используйте {PREFIX}помощь для подробностей о командах")
    await ctx.send(embed=embed)

# Команда секас
@bot.command(name='секс', aliases=['kiss'])
async def kiss(ctx, member: discord.Member):
    kisses = [
        f"{ctx.author.mention} нежно ебет {member.mention} 💋",
        f"{ctx.author.mention} страстно ебет {member.mention} 😘",
        f"{ctx.author.mention} отправляет воздушный поцелуй в виде спермы {member.mention} 💨💋",
        f"{ctx.author.mention} целует {member.mention} в попку 😊"
    ]

    embed = discord.Embed(
        description=random.choice(kisses),
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)

# Да или нет
@bot.command(name='данет', aliases=['даилинет', 'yesno', 'yn'])
async def yesno(ctx, *, question: str = None):
    """Строго Да или Нет"""
    answer = random.choice(["✅ Да", "❌ Нет"])  # 50/50

    embed = discord.Embed(color=0x2F3136)  # Discord-серый

    if question:
        embed.add_field(name="Вопрос", value=question, inline=False)

    embed.add_field(name="Ответ", value=answer, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='добавитьадмина')
@commands.has_permissions(administrator=True)
async def add_admin(ctx, user: discord.User):
    with open('config.json', 'r+') as f:
        config = json.load(f)
        if str(user.id) not in config['admin_ids']:
            config['admin_ids'].append(str(user.id))
            f.seek(0)
            json.dump(config, f, indent=4)
            await ctx.send(f"✅ {user.mention} добавлен в список админов")
        else:
            await ctx.send("ℹ️ Этот пользователь уже имеет права")

# Система бизнесов
@bot.command(name='бизнес')
async def business_info(ctx):
    user_id = str(ctx.author.id)

    if user_id not in user_businesses:
        embed = discord.Embed(
            title="🛒 Система бизнесов",
            description=f"У вас пока нет бизнеса! Купите его командой `{PREFIX}купитьбизнес`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    biz = user_businesses[user_id]
    biz_type = BUSINESS_TYPES[biz["type"]]

    # Создаём прогресс-бар
    balance = biz.get("balance", 0)
    capacity = biz_type["capacity"]
    progress = min(balance / capacity * 100, 100)
    progress_bar = f"[{'█' * int(progress/10)}{'░' * (10 - int(progress/10))}] {progress:.1f}%"

    embed = discord.Embed(
        title=f"{biz_type['emoji']} {biz['name']}",
        description=f"**Тип:** {biz_type['name']} (Ур. {biz['level']})",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💰 Касса бизнеса",
        value=f"{balance}/{capacity}{CURRENCY}",
        inline=False
    )

    embed.add_field(
        name="📈 Прогресс",
        value=progress_bar,
        inline=False
    )

    embed.add_field(
        name="💵 Доходность",
        value=f"{biz_type['income'][0]}-{biz_type['income'][1]}{CURRENCY} в час",
        inline=True
    )

    if biz["type"] < 3:
        next_type = BUSINESS_TYPES[biz["type"] + 1]
        embed.add_field(
            name="⚡ Улучшение",
            value=f"До {next_type['name']} за {next_type['upgrade_cost']}{CURRENCY}",
            inline=True
        )

    embed.set_footer(text=f"Снять деньги: {PREFIX}забратьденьги [сумма|all]")

    await ctx.send(embed=embed)

@bot.command(name='купитьбизнес')
async def buy_business(ctx):
    user_id = str(ctx.author.id)
    cost = 3000

    if user_id in user_businesses:
        await ctx.send("❌ У вас уже есть бизнес!")
        return

    if user_balances.get(user_id, 0) < cost:
        await ctx.send(f"❌ Недостаточно средств! Нужно {cost}{CURRENCY}")
        return

    user_balances[user_id] -= cost
    user_businesses[user_id] = {
        "type": 1,
        "level": 1,
        "name": f"Кофейня {ctx.author.name}",
        "balance": 0,  # Добавляем баланс предприятия
        "last_income": datetime.now().isoformat()
    }

    save_balances()
    save_businesses()

    await ctx.send(f"✅ Вы купили кофейню! Проверьте: `{PREFIX}бизнес`")
    
@bot.command(name='улучшитьбизнес')
async def upgrade_business(ctx):
    """Улучшение бизнеса до следующего уровня"""
    user_id = str(ctx.author.id)

    if user_id not in user_businesses:
        await ctx.send("❌ У вас нет бизнеса!")
        return

    biz = user_businesses[user_id]
    if biz["type"] >= 3:
        await ctx.send("ℹ️ У вас максимальный уровень бизнеса!")
        return

    next_type = biz["type"] + 1
    cost = BUSINESS_TYPES[next_type]["upgrade_cost"]

    if user_balances.get(user_id, 0) < cost:
        await ctx.send(f"❌ Недостаточно средств! Нужно {cost}{CURRENCY}")
        return

    user_balances[user_id] -= cost
    biz["type"] = next_type
    biz["level"] += 1

    save_balances()
    save_businesses()

    await ctx.send(f"🎉 Вы улучшили бизнес до {BUSINESS_TYPES[next_type]['name']}!")

@bot.command(name='назватьбизнес')
async def rename_business(ctx, *, name: str):
    """Изменение названия бизнеса"""
    user_id = str(ctx.author.id)

    if user_id not in user_businesses:
        await ctx.send("❌ У вас нет бизнеса!")
        return

    if len(name) > 32:
        await ctx.send("❌ Название слишком длинное (макс. 32 символа)")
        return

    user_businesses[user_id]["name"] = name
    save_businesses()

    await ctx.send(f"✅ Бизнес переименован в «{name}»")

@tasks.loop(minutes=60)
async def business_income():
    """Автоматический доход каждый час"""
    for user_id, biz in user_businesses.items():
        biz_type = BUSINESS_TYPES[biz["type"]]
        income = random.randint(biz_type["income"][0], biz_type["income"][1])
        user_balances[user_id] = user_balances.get(user_id, 0) + income
    save_balances()

#снять деньги с бизнеса
@bot.command(name='забратьденьги', aliases=['снятьденьги', 'withdraw'])
async def withdraw_money(ctx, amount: str = "all"):
    user_id = str(ctx.author.id)

    if user_id not in user_businesses:
        await ctx.send("❌ У вас нет бизнеса!")
        return

    biz = user_businesses[user_id]
    biz_type = BUSINESS_TYPES[biz["type"]]

    max_amount = biz.get("balance", 0)

    # Обработка "all" или числа
    if amount.lower() == "all":
        amount = max_amount
    else:
        try:
            amount = int(amount)
            if amount <= 0:
                await ctx.send("❌ Сумма должна быть положительной!")
                return
        except ValueError:
            await ctx.send("❌ Укажите число или 'all'!")
            return

    if max_amount == 0:
        await ctx.send("ℹ️ На балансе бизнеса нет денег!")
        return

    if amount > max_amount:
        await ctx.send(f"❌ Недостаточно средств! Доступно: {max_amount}{CURRENCY}")
        return

    # Снятие денег
    biz["balance"] -= amount
    user_balances[user_id] = user_balances.get(user_id, 0) + amount

    save_businesses()
    save_balances()

    embed = discord.Embed(
        title=f"💰 Успешное снятие",
        description=f"Снято {amount}{CURRENCY} с бизнеса",
        color=discord.Color.green()
    )
    embed.add_field(name="Баланс бизнеса", value=f"{biz['balance']}/{biz_type['capacity']}{CURRENCY}", inline=True)
    embed.add_field(name="Ваш баланс", value=f"{user_balances[user_id]}{CURRENCY}", inline=True)

    await ctx.send(embed=embed)

# Обработка ошибок
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Команда не найдена. Используйте `{PREFIX}помощь`")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Не хватает аргумента. Используйте `{PREFIX}помощь`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Недостаточно прав!")
    else:
        await ctx.send("Произошла ошибка. Попробуйте снова.")


@bot.event
async def on_command_error(ctx, error):
    error_msg = f"Команда: {ctx.command}, Ошибка: {str(error)}"
    error_logger.error(error_msg, exc_info=True)

    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Команда не найдена", delete_after=5)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ Недостаточно прав!", delete_after=5)
    else:
        await ctx.send(f"⚠️ Ошибка: {str(error)}", delete_after=10)


# Запуск бота
if __name__ == "__main__":
    bot.run(TOKEN)


@bot.event
async def on_disconnect():
    """Автосохранение при отключении"""
    save_balances()


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    finally:
        save_balances()  # Сохранит данные даже при краше
