import requests
from bs4 import BeautifulSoup

class GenshinSocialNetwork:
    def __init__(self):
        self.characters = []
        self.social_network = {}

    def get_social_network(self):
        self.step1()

    def step1(self):
        url = "https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
        }
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("div.divsort.g")
        for item in items:
            name_tag = item.find("div", class_="L")
            if name_tag:
                name = name_tag.text.strip()
                self.characters.append(name)

if __name__ == "__main__":
    m = GenshinSocialNetwork()
    m.get_social_network()