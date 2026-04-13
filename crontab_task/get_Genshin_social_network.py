import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import setup_logging

setup_logging()
logger = logging.getLogger('cron_task')

class GenshinSocialNetwork:
    def __init__(self):
        self.characters = []
        self.social_network = {}

    def get_social_network(self):
        self.step1()
        self.step2()
        self.step3()

    def step1(self):
        logger.info("开始执行步骤1：获取角色名称中文列表")
        url = "https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
        }
        try:
            response = requests.get(url, headers=headers)
            response.encoding = "utf-8"
            logger.debug(f"请求URL: {url}, 状态码: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("div.divsort.g")
            for item in items:
                name_tag = item.find("div", class_="L")
                if name_tag:
                    name = name_tag.text.strip()
                    if "旅行者" in name:
                        continue
                    self.characters.append({"name_zn":name})
            logger.info(f"步骤1执行完成，共获取 {len(self.characters)} 个角色中文名称")
        except Exception as e:
            logger.error(f"步骤1执行失败: {e}")
            raise
        s=",".join([character['name_zn'] for character in self.characters])
        logger.info(f"【原神角色中文名称】：{s}")

    def step2(self):
        logger.info("开始执行步骤2：获取角色名称英文列表")
        s=",".join([character['name_en'] for character in self.characters])
        logger.info(f"【原神角色英文名称】：{s}")

    def step3(self):
        logger.info("开始执行步骤3：获取角色社交网络数据")
        for character in self.characters:
            name_zn = character["name_zn"]
            logger.info(f"开始获取角色 {name_zn} 的社交网络数据")
            self.scrpayer_step3(name_zn)
            logger.info(f"获取角色 {name_zn} 的社交网络数据完成")
        logger.info(f"步骤3执行完成，共获取 {len(self.characters)} 个角色社交网络数据")

    def scrpayer_step3(self, character):
        path = quote(f"{character}语音", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
        }
        try:
            response = requests.get(url, headers=headers)
            response.encoding = "utf-8"
            logger.debug(f"请求URL: {url}, 状态码: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.error(f"获取角色 {character} 的社交网络数据失败: {e}")
            raise

if __name__ == "__main__":
    logger.info("原神拓扑爬取程序开始运行")
    m = GenshinSocialNetwork()
    m.get_social_network()
    logger.info("原神拓扑爬取程序运行结束")