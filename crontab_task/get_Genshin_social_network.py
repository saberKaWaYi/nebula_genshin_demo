from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import time

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import setup_logging
from settings import settings

setup_logging()
logger = logging.getLogger('cron_task')

class GenshinSocialNetwork:
    def __init__(self):
        self.characters = []
        self.social_network = {}
        self.cookies = settings['crontab_task']['website_cookies']['wiki_biligame_com']["cookie_name"]
        self.headers = settings['crontab_task']['headers']
        self.time_sleep = settings['crontab_task']['time_sleep']

    def get_social_network(self):
        self.step1()
        self.step2()
        self.step3()

    def step1(self):
        logger.info("开始执行步骤1：获取角色名称中文列表")
        url = "https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2"
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            response.encoding = "utf-8"
            if response.status_code != 200:
                logger.error(f"请求URL: {url}, 状态码: {response.status_code}")
                raise Exception(f"请求URL: {url}, 状态码: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("div.divsort.g")
            for item in items:
                name_tag = item.find("div", class_="L")
                if name_tag:
                    name = name_tag.text.strip()
                    if "旅行者" in name or "奇偶" in name:
                        continue
                    self.characters.append({"name_zh":name})
            logger.info(f"步骤1执行完成，共获取 {len(self.characters)} 个角色中文名称")
        except Exception as e:
            logger.error(f"步骤1执行失败: {e}")
            raise
        s=",".join([character['name_zh'] for character in self.characters])
        logger.info(f"【原神角色中文名称】：{s}")

    def step2(self):
        logger.info("开始执行步骤2：获取角色名称英文列表")
        for _ in range(len(self.characters)):
            time.sleep(self.time_sleep)
            self.characters[_]["name_en"] = self.scrpayer_step2(self.characters[_]["name_zh"])
        s=",".join([character['name_en'] for character in self.characters])
        logger.info(f"【原神角色英文名称】：{s}")

    def scrpayer_step2(self, character):
        path = quote(f"{character}", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            response.encoding = "utf-8"
            if response.status_code != 200:
                logger.error(f"请求URL: {url}, 状态码: {response.status_code}")
                raise Exception(f"请求URL: {url}, 状态码: {response.status_code}")
            logger.debug(f"请求URL: {url}, 状态码: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")
            name_en = soup.select_one('th:-soup-contains("全名/本名") + td span[lang="en"]').get_text(strip=True)[:-1]
            return name_en
        except Exception as e:
            logger.error(f"获取角色 {character} 的英文名称失败: {e}")
            raise

    def step3(self):
        logger.info("开始执行步骤3：获取角色社交网络数据")
        for character in self.characters:
            time.sleep(self.time_sleep)
            name_zh = character["name_zh"]
            logger.info(f"开始获取角色 {name_zh} 的社交网络数据")
            self.scrpayer_step3(name_zh)
            logger.info(f"获取角色 {name_zh} 的社交网络数据完成")
        logger.info(f"步骤3执行完成，共获取 {len(self.characters)} 个角色社交网络数据")

    def scrpayer_step3(self, character):
        path = quote(f"{character}语音", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            response.encoding = "utf-8"
            if response.status_code != 200:
                logger.error(f"请求URL: {url}, 状态码: {response.status_code}")
                raise Exception(f"请求URL: {url}, 状态码: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")
            item_divs = soup.find_all("div",style="margin:2px 0px;width:100%;display: table;overflow: hidden;padding:1px;")
            # print(len(item_divs))
            # for item_div in item_divs:
            #     title = item_div.find(
            #         "div",
            #         style="display: table-cell;width:180px;vertical-align: middle;background:#8F98A6;padding:5px 10px;color:#fff;font-weight:bold"
            #     ).get_text(strip=True)
            #     content = item_div.find(
            #         "div",
            #         class_="voice_text_chs vt_active"
            #     ).get_text(strip=True)
            #     print(title, content)
        except Exception as e:
            logger.error(f"获取角色 {character} 的社交网络数据失败: {e}")
            raise

if __name__ == "__main__":
    logger.info("原神拓扑爬取程序开始运行")
    m = GenshinSocialNetwork()
    m.get_social_network()
    logger.info("原神拓扑爬取程序运行结束")