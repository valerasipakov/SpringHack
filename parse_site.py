import os
import json
import time
import re

from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus, quote

from utils import parse_url, from_file_json_to_dict


def get_category(html_text):
    class_dict = from_file_json_to_dict(r'clasifier_words_from_site.json')
    max_classif_koef = 0

    result_category = "Общая категория"

    text = html_text  # получение текста с html
    text = re.sub("[\t\n\r\d,.:?!()₽]", " ", text) # очищение от лишних пробелов и знаков препинания
    text = re.sub(' +', " ", text)
    text = text.lower()

    percents = []
    for key, value in class_dict.items():
        count = 0
        for word in value:
            if re.search(f'{re.escape(word)}', text):
                count +=1
        # print("{:10s} {:4d} {:10s} {:4d}| {:5.2f}% |{:8s} - {:8s}".format(
        #     "count:",count,"total:",len(value),100*count/len(value),"category",key) )
        percents.append(100 * count / len(value))
        if max_classif_koef<count/len(value):
            result_category = key
            max_classif_koef = count/len(value)

    if len([p for p in percents if p >= 60]) >= 5:
        return "бпла коптерного типа"

    return result_category.lower()


def get_properties_from_page(path):
    url = f"https:/"
    for node in path.split("\\")[1:-1]:
        url += f"/{quote(node)}"

    path = unquote_plus(path, encoding="utf-8")

    with open("synonyms.json", 'r') as f:
        syns = json.load(f)

    with open(path, 'r', encoding="utf-8") as f:
        text = f.read()

    soup = BeautifulSoup(text, "html.parser")
    category = get_category(soup.text)
    if category.lower() == "Общая категория".lower():
        return {}

    properties = syns[category]["характеристики"]
    tags = soup.find_all()

    props = {}
    max_name_ratio = 0
    max_name = ""
    pictures = []
    for i, tag in enumerate(tags):
        for name in path.split("\\")[2:]:
            name = name.replace("-", " ").replace("_", " ")
            if tag.name == "img" and "src" in tag.attrs:
                if name in tag["src"] or name.replace(" ", "-") in tag["src"] or name.replace(" ", "_") in tag["src"]:
                    pictures.append(tag["src"])

            name = name.replace("-", " ").replace("_", " ")
            name_ratio = fuzz.partial_ratio(tag.text.strip().lower(), name)
            if tag.name in ["p", "h1"] and name_ratio > 90 and max_name_ratio < name_ratio:
                max_name_ratio = name_ratio
                max_name = tag.text.strip()

        if tag.findChild():
            continue

        max_ratio = 0
        max_key = ""
        for key, val in properties.items():
            key_syns = [key] + val
            cur_ratio = 0
            for k in key_syns:
                ratio = fuzz.ratio(tag.text.lower(), k.lower())
                if k != "" and ratio > 75:
                    cur_ratio = max(cur_ratio, ratio)

            if max_ratio < cur_ratio:
                max_ratio = cur_ratio
                max_key = key

        if max_ratio > 75:
            props[max_key] = props.get(max_key, (0, ""))
            if props[max_key][0] < max_ratio:
                props[max_key] = (max_ratio, tags[i + 1].text)

    result = {
        "название": max_name,
        "изображение": pictures,
        "категория": category,
        "ссылка": url,
        "характеристики": {},
    }
    for key, value in props.items():
        result["характеристики"][key] = value[1].replace("\n", " ").replace("\t", " ").replace("\xa0", " ")

    if result["характеристики"]:
        for key in properties:
            if key not in result["характеристики"]:
                result["характеристики"][key] = ""

        # print(*result.items(), sep="\n")
        # print(*result["характеристики"].items(), sep="\n")

        return result

    return {}


def get_properties(list_domain):
    result_list = []
    print(list_domain)
    for domain in list_domain:
        _, domain, _ = parse_url(domain)
        cur_path = os.path.join(domain, domain)

        i = 0
        for cur_dir, _, filename in os.walk(cur_path):
            i += 1
            if not filename:
                continue

            path = os.path.join(cur_dir, filename[0])
            print(f"{i}: {path}")
            properties = {}
            try:
                properties = get_properties_from_page(path)
            except:
                print("Неудалось спарсить")

            if properties:
                result_list.append(properties)

    result = {"content": result_list, "дата сбора": str(time.time())}
    return result


if __name__ == "__main__":
    # inp_domain = "www.dji.com"
    # inp_path = "/ru/mavic-3/specs"

    # inp_domain = ["idronex.ru"]
    # inp_domain = "idronex.ru"
    # inp_path = "/components%20for%20drones/battery-chargers/battery-charger-isdt-d2"

    inp_domain = []
    n = int(input("Количество сайтов: "))
    print("Ссылки на сайт (каждая в отдельной строке): ")
    for _ in range(n):
        inp_domain.append(input())

    if not os.path.exists("data"):
        os.mkdir("data")

    version = 0
    out_filename = os.path.join("data", "catalog")
    while os.path.exists(f"{out_filename}_v{version}.json"):
        version += 1

    with open("data\\version.json", 'w') as f:
        json.dump({"version": version}, f)

    data = get_properties(inp_domain)
    with open(f"{out_filename}_v{version}.json", 'w') as f:
        json.dump(data, f)

    print(f"Данные успешно собраны и сохранены в файл: {out_filename}_v{version}.json")

    # sys_path = os.path.join(inp_domain, inp_domain)
    # for directory in inp_path.split("/"):
    #     sys_path = os.path.join(sys_path, directory)
    #
    # sys_path = os.path.join(sys_path, "index.html")
    # print(sys_path)
    #
    # data = [get_properties_from_page(sys_path)]
    # print(data)
    # with open(out_filename, 'w') as f:
    #     json.dump(data, f)
    #
    # print(f"Данные успешно собраны и сохранены в файл: {out_filename}")
