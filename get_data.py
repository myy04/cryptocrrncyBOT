from bs4 import BeautifulSoup
import requests

for page_ind in range(1, 363):
    url = f"https://crypto.com/price?page={page_ind}"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('table', class_ = "chakra-table css-1qpk7f7").find('tbody', class_ = "css-0").find_all('tr')
    for i in table:
        j = i.find_all('div', class_ ="css-87yt5a")
        for k in j:
            print(k.find('span').text)

    print("###########")