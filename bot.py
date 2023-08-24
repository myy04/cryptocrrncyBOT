import telebot
from telebot import types

from thefuzz import fuzz
from thefuzz import process

from datetime import datetime

from bs4 import BeautifulSoup
import requests

tracks = {} # {user_id : [cryptocurrencys' full names]}
links = {} # {(FULL NAME, SHORT NAME): URL}
prices = {} # {FULL NAME: (PRICE, LAST UPDATED TIME IN SECONDS)}
full_names = []
short_names = []

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def get_data():

    with open('full_names.txt') as f:
        content = f.readlines()
        for line in content:
            if str(line)[0] == '#':
                continue
            if is_ascii(str(line)) == 0:
                continue

            full_names.append(str(line).strip().upper())

    with open('short_names.txt') as f:
        content = f.readlines()
        for line in content:
            if str(line)[0] == '#':
                continue
            if is_ascii(str(line)) == 0:
                continue

            short_names.append(str(line).strip().upper())
        
    for i in range(len(full_names)):
        url = f"https://crypto.com/price/{full_names[i].replace(' ', '-').lower()}"
        links.update({(full_names[i], short_names[i]) : url})
    

def most_simillar(x, dataset):  
    max_score = float(0.00)
    ret = "-1"

    #print(dataset)

    for word in dataset:
        score = float(fuzz.ratio(x, word))
        if score > max_score:
            max_score = float(score)
            ret = word

    return ret 

def find_pair(name, pairs = links.keys()):
    for pair in pairs:
        if name == pair[0] or name == pair[1]:
            return pair
    
    print("Find Pair: Could not find a matching pair")
    return ("", "")

def updated_price(url):
    page = requests.get(url)
    print(url, page.status_code)
    soup = BeautifulSoup(page.text, 'html.parser')
    val = soup.find('h2').find('span').string.strip()
    return float(val.replace('$', '').replace('USD', '').replace(',', '', 1).replace(',', '.').strip())

def get_price(name):
    url = links[find_pair(name, links.keys())]

    current_time = datetime.now()
    seconds = int(current_time.hour) * 60 * 60 + int(current_time.minute) * 60 + int(current_time.second)

    update_freq = 180 #seconds

    if name not in prices.keys():
        prices.update({name: (updated_price(url), seconds)})
    else:
        if abs(prices[name][1] - seconds) > update_freq:
            prices.update({name : (updated_price(url), seconds)})

    return prices[name][0]

def currency_format(x, KZT = 0, USD = 0):
    if (USD): 
        return "${:,.2f}".format(float(x))
    if (KZT):
        return "₸{:,.2f}".format(float(x))


####BOT####

TOKEN = "6293619156:AAE5DA-wcyiMjnDl2lcppb56W1fNd_zNn6U"
bot = telebot.TeleBot(TOKEN)
get_data()

@bot.message_handler(commands=['start', 'add'])
def welcome(message):
    msg = bot.reply_to(message, 'Type your cryptocurrency name to track its value')
    if message.chat.id not in tracks.keys():
        tracks.update({message.chat.id : []})

    bot.register_next_step_handler(msg, add_to_list)

def add_to_list(message):
    name = message.text.upper()
    print("add_to_list input: ", name)

    name = most_simillar(name, list(full_names + short_names))
    name = find_pair(name)[0]

    print("add_to_list corrected input:", name)

    if name == "ERROR":
        print("add_to_list: error")
        bot.reply_to(message, "No match")
        return

    user_id = message.chat.id
    
    if name not in tracks[user_id]:
        tracks[user_id].append(name)    
        print(f"add_to_list: {user_id} has added {name} to their list")

    bot.reply_to(message, f"{name} has been added to your list")

@bot.message_handler(commands=['show'])
def show_prices(message):
    user_id = message.chat.id

    ans = ""

    for name in tracks[user_id]:
        pair = find_pair(name, links.keys())
        full_name = pair[0]
        short_name = pair[1]
        url = links[pair]

        price = get_price(full_name)

        ans = ans + '\n' + f"{full_name} ({short_name}): {currency_format(price, USD = 1)}" 

    bot.reply_to(message, ans)

@bot.message_handler(commands=['remove'])
def ask_to_type(message):
    msg = bot.reply_to(message, "Type the name of cryptocurrency that you want to remove from your list")
    bot.register_next_step_handler(msg, remove_from_list)

def remove_from_list(message):
    user_id = message.chat.id
    name = message.text.upper()

    name = most_simillar(name, list(full_names + short_names))
    name = find_pair(name)[0]

    if name in tracks[user_id]:
        tracks[user_id].remove(name)
        bot.reply_to(message, f"{name} has been removed from your list")
        print(f"remove_from_list: {user_id} has removed {name} from their list")
    else:
        bot.reply_to(message, f"{name} is not in your list")
        print(f"remove_from_list: {name} is not in {user_id} list")

bot.infinity_polling()
