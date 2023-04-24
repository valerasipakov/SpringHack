import json
import aiohttp
import asyncio
import os
import time

from random import randint
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import unquote_plus

from utils import parse_url

tree = {}
forbidden_extensions = (".png", "jpg", ".zip", ".jpeg", ".mp4", ".pdf", ".gif")
num_requests = 0

unproc_links = set()
processed_links = set()


def collect_links_from_html(html, domain):
    links = []
    for link in BeautifulSoup(html, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            link = link["href"].rstrip("\"").rstrip("\'")
            _, link_domain, link_path = parse_url(link)
            if link_domain != '' and link_domain != domain:
                continue
            if link_path.endswith(forbidden_extensions):
                continue
            if '?' in link_path:
                link_path = link_path[:link_path.find('?')]
            if '#' in link_path:
                link_path = link_path[:link_path.find('#')]

            links.append(link_path)

    return links


async def get_links(session, url):
    global unproc_links, processed_links
    links = []

    await asyncio.sleep(randint(10, 30))
    async with session.get(url) as resp:
        print(url, resp.status)
        if resp.status != 200:
            print(f"Response code not 200, but {resp.status}")

            if 500 <= resp.status <= 599 or resp.status == 403:
                unproc_links.add(parse_url(url)[-1])

            return links

        _, domain, path = parse_url(url)
        html = await resp.content.read()
        links = collect_links_from_html(html, domain)

        save_html(domain, path, html)

    return links


def save_html(domain, path, html):
    path = path.rstrip("\"").rstrip("\'")
    os_path = os.path.join(domain, domain)
    if path == "/" and not os.path.exists(os_path):
        os.mkdir(os_path)
    else:
        for node in path.strip("/").split("/"):
            node = unquote_plus(node, encoding="utf-8")
            os_path = os.path.join(os_path, node.strip())
            # print(os_path)
            if not os.path.exists(os_path):
                os.mkdir(os_path)

        os_path = os.path.join(os_path, "index.html")
        with open(os_path, 'w', encoding="utf-8") as f:
            try:
                f.write(html.decode("utf-8"))
            except Exception:
                print(f"Unable to decode text: {path}")


async def parse(protocol, root_domain, root_path):
    global processed_links, unproc_links

    queue = []
    if os.path.exists(queue_file := os.path.join(root_domain, "queue.json")):
        with open(queue_file, 'r') as f:
            queue = json.load(f)

    queue = queue + [root_path] + list(unproc_links)
    async with aiohttp.ClientSession() as session:
        while len(queue) > 0:
            bs = 50  # batch size

            while len(queue) > 0:
                tasks = []
                for path in queue[:bs]:
                    if path.endswith(forbidden_extensions):
                        continue
                    tasks.append(asyncio.create_task(get_links(session, protocol + root_domain + path)))

                await asyncio.sleep(3)
                print('=' * 7, len(queue), '=' * 7)
                queue = queue[bs:]

                results = await asyncio.gather(*tasks[:bs])
                for links in results:
                    for link in links:
                        if link not in processed_links:
                            queue.append(link)
                            processed_links.add(link)

                with open(os.path.join(root_domain, "unproc.json"), 'w') as f:
                    json.dump(list(unproc_links), f)

                with open(os.path.join(root_domain, "proc.json"), 'w') as f:
                    json.dump(list(processed_links), f)

                with open(os.path.join(root_domain, "queue.json"), 'w') as f:
                    json.dump(queue, f)

        print("Out of while")


def collect_data(url):
    global unproc_links, processed_links

    protocol, root_domain, root_path = parse_url(url)
    if not os.path.exists(root_domain):
        os.mkdir(root_domain)

    if os.path.exists(proc_file := os.path.join(root_domain, "proc.json")):
        with open(proc_file, 'r') as f:
            processed_links = set(json.load(f))

    if os.path.exists(unproc_file := os.path.join(root_domain, "unproc.json")):
        with open(unproc_file, 'r') as f:
            unproc_links = set(json.load(f))

    _queue = []
    if os.path.exists(queue_file := os.path.join(root_domain, "queue.json")):
        with open(queue_file, 'r') as f:
            _queue = json.load(f)

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print(len(unproc_links), len(processed_links))

    counter = 0
    while (unproc_links or _queue or len(processed_links) == 0) and counter < 10:
        _queue = []
        asyncio.run(parse(protocol, root_domain, root_path))

        unproc_links -= processed_links
        print(f"Repeat. {len(unproc_links)} unprocessed links")

        counter += 1
        time.sleep(5)

    with open(os.path.join(root_domain, "unproc.json"), 'w') as f:
        json.dump(list(unproc_links), f)

    with open(os.path.join(root_domain, "proc.json"), 'w') as f:
        json.dump(list(processed_links), f)

    print("Finish")


if __name__ == "__main__":
    inp_url = ""
    # inp_url = "https://aeromotus.ru/"
    # inp_url = "https://www.dji.com/"
    while inp_url == "" or parse_url(inp_url)[-1].strip("/") != "":
        inp_url = input("Введите URL сайта, который необходимо скачать: ")

    collect_data(inp_url)
