from bs4 import BeautifulSoup
import requests
import json


def get_menu(url):
    """Parses HTML menu into JSON

    Parser for delivery services powered by lieferando.de.
    Only tested with https://www.izmir-kebap-friedrichshafen.de. Downloads the html and extracts all
    categories and their products. Put's them into python dictionary with unique ids for categories and products
    :param url: lieferando.de powered site like https://www.izmir-kebap-friedrichshafen.de
    :type url: str
    :return JSON Object of menu
    :rtype str of JSON Object
    """
    # requests html of url
    html_content = requests.get(url).text
    # library for parsing html
    soup = BeautifulSoup(html_content, features="html.parser")
    # unique category id
    category_id = 0
    # storage for categories and products
    menu = dict()
    
    category_html = soup.find_all("div", attrs={"class": "menucat"})
    # loops through all categories found in html
    for category in category_html:
        # unique product id in category
        product_id = 1
        products = dict()
        category_name = category.find("h3", attrs={"class": "category"}).text
        category_item_html = category.find_all("a", attrs={"class": "addtobasket"})
        # loops through all products in category found in html
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
