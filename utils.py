import json


def parse_url(link):
    if link.startswith("//"):
        domain = link.lstrip("//").rstrip('/').split("/")[0]
        protocol = "https://"
        path = link[link.index(domain) + len(domain):]

    elif link.startswith('/'):
        domain = ''
        protocol = ''
        path = link

    else:
        domain = link.lstrip("http").lstrip("s").lstrip("://").rstrip('/').split("/")[0]
        protocol = link[:link.index(domain)]
        path = link[link.index(domain) + len(domain):]

    return protocol, domain, path


def from_file_json_to_dict(path):
    dictionary = {}

    with open(path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        for key, value in data.items():
            dictionary[key] = value

    return dictionary
