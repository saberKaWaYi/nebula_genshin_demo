from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path

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
        self.social_network = []
        self.cookies = settings['crontab_task']['website_cookies']['wiki_biligame_com']["cookie_name"]
        self.headers = settings['crontab_task']['headers']
        self.time_sleep = settings['crontab_task']['time_sleep']
        self.max_retries = settings['crontab_task']['max_retries']

    def get_social_network(self):
        self.step1()
        self.step2()
        self.step3()
        self.step4()

    def step1(self):
        logger.info("开始执行步骤1：获取角色名称中文列表")
        url = "https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2"
        try:
            times = 0
            while times < self.max_retries:
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                response.encoding = "utf-8"
                if response.status_code != 200:
                    logger.error(f"步骤1请求URL: {url}, 状态码: {response.status_code}, 重试次数: {times + 1}")
                    times += 1
                    time.sleep(self.time_sleep*30)
                else:
                    break
            else:
                raise Exception(f"步骤1请求URL: {url}失败，已达到最大重试次数: {self.max_retries}")
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
        count = 0
        for _ in range(len(self.characters)):
            self.characters[_]["name_en"] = self.scrpayer_step2(self.characters[_]["name_zh"])
            count += 1
            time.sleep(self.time_sleep)
        logger.info(f"步骤2执行完成，共获取 {count} 个角色英文名称")
        s=",".join([character['name_en'] for character in self.characters])
        logger.info(f"【原神角色英文名称】：{s}")

    def scrpayer_step2(self, character):
        path = quote(f"{character}", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        try:
            times = 0
            while times < self.max_retries:
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                response.encoding = "utf-8"
                if response.status_code != 200:
                    logger.error(f"步骤2获取角色 {character} 请求URL: {url}, 状态码: {response.status_code}, 重试次数: {times + 1}")
                    times += 1
                    time.sleep(self.time_sleep*30)
                else:
                    break
            else:
                raise Exception(f"步骤2获取角色 {character} 请求URL: {url}失败，已达到最大重试次数: {self.max_retries}")
            soup = BeautifulSoup(response.text, "html.parser")
            name_en = soup.select_one('th:-soup-contains("全名/本名") + td span[lang="en"]').get_text(strip=True)[:-1]
            return name_en
        except Exception as e:
            logger.error(f"步骤2获取角色 {character} 的英文名称失败: {e}")
            raise

    def step3(self):
        logger.info("开始执行步骤3：获取角色社交网络数据")
        count = 0
        for character in self.characters:
            self.scrpayer_step3(character["name_zh"])
            count += 1
            time.sleep(self.time_sleep)
        logger.info(f"步骤3执行完成，共获取 {count} 个角色社交网络数据")

    def scrpayer_step3(self, character):
        character_name_en = [i for i in self.characters if i["name_zh"] == character][0]["name_en"]
        logger.info(f"开始获取角色 {character} 的社交网络数据")
        path = quote(f"{character}语音", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        try:
            times = 0
            while times < self.max_retries:
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                response.encoding = "utf-8"
                if response.status_code != 200:
                    logger.error(f"步骤3获取角色 {character} 请求URL: {url}, 状态码: {response.status_code}, 重试次数: {times + 1}")
                    times += 1
                    time.sleep(self.time_sleep*30)
                else:
                    break
            else:
                raise Exception(f"步骤3获取角色 {character} 请求URL: {url}失败，已达到最大重试次数: {self.max_retries}")
            soup = BeautifulSoup(response.text, "html.parser")
            item_divs = soup.find_all("div",style="margin:2px 0px;width:100%;display: table;overflow: hidden;padding:1px;")
            for item_div in item_divs:
                title = item_div.find("div", style="display: table-cell;width:180px;vertical-align: middle;background:#8F98A6;padding:5px 10px;color:#fff;font-weight:bold")
                if title:
                    title = title.text.strip()
                content_zh = item_div.find("div", class_="voice_text_chs vt_active")
                if content_zh:
                    content_zh = content_zh.text.strip()
                content_en = item_div.find("div", class_="voice_text_en")
                if content_en:
                    content_en = content_en.text.strip()
                if title and content_zh and content_en:
                    for character_name in self.characters:
                        if character_name["name_zh"] == character:
                            continue
                        if character_name["name_zh"] not in title:
                            continue
                        title_zh = f"{character}关于{character_name['name_zh']}"
                        title_en = f"{character_name_en} about {character_name['name_en']}"
                        self.social_network.append({
                            "name_zh": character,
                            "title_zh": title_zh,
                            "content_zh": content_zh,
                            "name_en": character_name_en,
                            "title_en": title_en,
                            "content_en": content_en
                        })
            logger.info(f"步骤3获取角色 {character} 的社交网络数据完成")
        except Exception as e:
            logger.error(f"步骤3获取角色 {character} 的社交网络数据失败: {e}")
            raise

    def step4(self):
        logger.info("开始执行步骤4：保存结果到 JSON 文件")
        output_path = Path(__file__).resolve().parent / 'social_network_demo.json'
        payload = {
            "characters": self.characters,
            "social_network": self.social_network
        }
        try:
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"步骤4执行完成，结果已保存到 {output_path}")
        except Exception as e:
            logger.error(f"步骤4执行失败: {e}")
            raise


if __name__ == "__main__":
    logger.info("原神拓扑爬取程序开始运行")
    m = GenshinSocialNetwork()
    m.get_social_network()
    logger.info("原神拓扑爬取程序运行结束")