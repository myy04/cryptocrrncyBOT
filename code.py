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
    
    print(full_names)

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

def find_pair(name, pairs):
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

    if name not in prices.keys():
        prices.update({name: (updated_price(url), seconds)})
    else:
        if abs(prices[name][1] - seconds) > 2 * 60 * 60:
            prices.update({name : (updated_price(url), seconds)})

    return prices[name][0]

def KZT_USD(url = "https://kase.kz/en/currency/"):
    page = requests.get(url)
    print(url, page.status_code)

    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('table', class_="dataTable sorting-table--false table table-striped js-spot-table").find('tbody').find_all('tr')
    
    lst = []
    for row in table:
        r = row.text.strip().split()
        lst.append(r)
    
    print(lst)

    return float(lst[7][6].replace(',', '.'))

def currency_format(x, KZT = 0, USD = 0):
    if (USD): 
        return "${:,.2f}".format(float(x))
    if (KZT):
        return "₸{:,.2f}".format(float(x))


def correct_name(name):
    name = name.upper()

    short_sim = most_simillar(name, short_names)
    full_sim = most_simillar(name, full_names)

    print("NAME CORRECTION:")
    print("SHORT SIMILAR: ", short_sim)
    print("LONG SIMILLAR: ", full_sim)

    if fuzz.ratio(name, short_sim) > fuzz.ratio(name, full_sim):
        return find_pair(short_sim, links.keys())[0]

    else:
        return full_sim

####BOT####

TOKEN = "6293619156:AAE5DA-wcyiMjnDl2lcppb56W1fNd_zNn6U"
bot = telebot.TeleBot(TOKEN)
get_data()

@bot.message_handler(commands=['start', 'add'])
def welcome(message):
    msg = bot.reply_to(message, 'Type your cryptocurrency name to track its value')
    if message.chat.id not in tracks.keys():
        tracks.update({message.chat.id : []})

    bot.register_next_step_handler(msg, add_link)

def add_link(message):
    name = message.text
    print("ADD: INPUT", name)

    name = correct_name(name)
    print("ADD: CORRECTED", name)

    if name == "ERROR":
        bot.reply_to(message, "No match")
        return

    user_id = message.chat.id
    
    if name not in tracks[user_id]:
        tracks[user_id].append(name)    

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
    bot.register_next_step_handler(msg, remove_track)

def remove_track(message):
    user_id = message.chat.id
    name = message.text
    name = correct_name(name)

    if user_id in tracks.keys():
        tracks[user_id].remove(name)
        bot.reply_to(message, f"{name} has been successfuly removed from your list")
    else:
        bot.reply_to(message, "There is no such cryptocurrency in your list")

bot.infinity_polling()