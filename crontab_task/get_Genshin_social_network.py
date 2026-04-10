import requests
from bs4 import BeautifulSoup
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
        logger.info("GenshinSocialNetwork 初始化完成")

    def get_social_network(self):
        logger.info("开始获取社交网络数据")
        self.step1()
        self.step2()
        logger.info("社交网络数据获取完成")

    def step1(self):
        logger.info("开始执行步骤1：获取角色列表")
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
            logger.debug(f"找到 {len(items)} 个角色项")
            for item in items:
                name_tag = item.find("div", class_="L")
                if name_tag:
                    name = name_tag.text.strip()
                    self.characters.append(name)
                    logger.debug(f"添加角色: {name}")
            logger.info(f"步骤1完成，共获取 {len(self.characters)} 个角色")
        except Exception as e:
            logger.error(f"步骤1执行失败: {e}")
            raise

    def step2(self):
        pass

if __name__ == "__main__":
    logger.info("原神拓扑爬取程序开始运行")
    m = GenshinSocialNetwork()
    m.get_social_network()
    logger.info("原神拓扑爬取程序运行结束")