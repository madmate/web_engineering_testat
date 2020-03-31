from bs4 import BeautifulSoup
import requests
import json


# url = 'https://www.izmir-kebap-friedrichshafen.de'

def get_menu(url):
    html_content = requests.get(url).text

    soup = BeautifulSoup(html_content, features="html.parser")

    category_id = 0
    product_id = 1
    menu = {}
    category_html = soup.find_all("div", attrs={"class": "menucat"})
    for category in category_html:
        product_id = 1
        products = {}
        category_name = category.find("h3", attrs={"class": "category"}).text
        category_item_html = category.find_all("a", attrs={"class": "addtobasket"})
        for item in category_item_html:
            price = item.find("span", attrs={"class": "price"}).text.replace(',', ".")
            item_name = item.find("b", attrs={"itemprop": "name"}).text

            products[product_id] = {
                "name": item_name,
                "price": price
            }
            product_id += 1
        menu[category_id] = {
            "category": category_name,
            "products": products
        }
        category_id += 1

    return json.dumps(menu, indent=4, separators=(',', ': '))
