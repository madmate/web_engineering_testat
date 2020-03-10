from bs4 import BeautifulSoup
import requests
import json

url = 'https://www.izmir-kebap-friedrichshafen.de'

html_content = requests.get(url).text

soup = BeautifulSoup(html_content, features="html.parser")

menu = []
category_html = soup.find_all("div", attrs={"class": "menucat"})
for category in category_html:
    products = []
    category_name = category.find("h3", attrs={"class": "category"}).text
    category_item_html = category.find_all("a", attrs={"class": "addtobasket"})
    for item in category_item_html:
        price = item.find("span", attrs={"class": "price"}).text
        item_name = item.find("b", attrs={"itemprop": "name"}).text

        product = {
            "name": item_name,
            "price": price
        }
        products.append(product)
    filled_cat = {
        "category": category_name,
        "products": products
    }
    menu.append(filled_cat)

print(json.dumps(menu, indent=4, separators=(',', ': ')))

# print(soup.prettify())
