import json
import os

from utils import from_file_json_to_dict


synonyms_filename = "synonyms.json"


def update_synonyms(filename):
    syns = {}
    if os.path.exists(synonyms_filename):
        with open(synonyms_filename, 'r') as f:
            syns = json.load(f)

    with open(filename, 'r', encoding="utf-8") as f:
        new_data = json.load(f)
        new_data = new_data["content"]


    if list(new_data[-1].keys())[0] == "размерности":
        syns["размерности"] = syns.get("размерности", {})
        for dim_key, dim_val in new_data[-1].items():
            dim_val = set(dim_val)
            dim_val.update(set(syns["размерности"].get(dim_key, {})))
            syns["размерности"][dim_key] = list(dim_val)

        new_data = new_data[:-1]

    for category in new_data:
        name = category["наименование"]
        syns[name] = syns.get(name, {})

        name_syns = set(category["синоним наименования"])
        name_syns.update(set(syns[name].get("синоним наименования", [])))
        syns[name]["синоним наименования"] = list(name_syns)

        syns[name]["характеристики"]= syns[name].get("характеристики", {})
        for param_key, param_val in category["характеристики"].items():
            values = set(param_val)
            values.update(set(syns[name]["характеристики"].get(param_key, [])))
            syns[name]["характеристики"][param_key] = list(values)

    with open(synonyms_filename, 'w') as f:
        try:
            json.dump(syns, f, ensure_ascii=False)
        except:
            json.dump(syns, f)


if __name__ == "__main__":
    inp_filename = input("Название файла с синонимами (должен леать в папке source/): ")
    # inp_filename = "ul.json"
    inp_filename = os.path.join("source", inp_filename)

    # print(inp_filename)
    if os.path.exists(inp_filename):
        update_synonyms(inp_filename)
        print("Данные успешно объединены")
    else:
        print("Такого файла не существует!")
