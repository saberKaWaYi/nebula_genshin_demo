from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
import logging

from config import crawler_settings, DATA_DIR, setup_logging

setup_logging()
logger = logging.getLogger("crawler")


class GenshinCrawler:
    """原神角色社交网络爬虫"""

    def __init__(self):
        self.characters = []
        self.social_network = []
        self.cookies = crawler_settings.website_cookies["wiki_biligame_com"]["cookie_name"]
        self.headers = crawler_settings.headers
        self.time_sleep = crawler_settings.time_sleep
        self.max_retries = crawler_settings.max_retries

    def run(self):
        """执行完整爬取流程"""
        self._fetch_character_names_zh()
        self._fetch_character_names_en()
        self._fetch_social_network()
        self._save_results()

    def _fetch_character_names_zh(self):
        """步骤1：获取角色中文名称列表"""
        logger.info("开始获取角色中文名称列表")
        url = "https://wiki.biligame.com/ys/角色"

        response = self._request_with_retry(url)
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("div.divsort.g")

        for item in items:
            name_tag = item.find("div", class_="L")
            if name_tag:
                name = name_tag.text.strip()
                if "旅行者" in name or "奇偶" in name:
                    continue
                self.characters.append({"name_zh": name})

        logger.info(f"获取完成，共 {len(self.characters)} 个角色")
        names = ",".join([c["name_zh"] for c in self.characters])
        logger.info(f"角色列表：{names}")

    def _fetch_character_names_en(self):
        """步骤2：获取角色英文名称列表"""
        logger.info("开始获取角色英文名称列表")
        for char in self.characters:
            char["name_en"] = self._fetch_name_en(char["name_zh"])
            time.sleep(self.time_sleep)
        logger.info(f"获取完成，共 {len(self.characters)} 个英文名称")

    def _fetch_name_en(self, character_zh: str) -> str:
        """获取单个角色的英文名称"""
        path = quote(character_zh, encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"

        response = self._request_with_retry(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name_en = soup.select_one('th:-soup-contains("全名/本名") + td span[lang="en"]').get_text(strip=True)[:-1]

        return name_en

    def _fetch_social_network(self):
        """步骤3：获取角色社交网络数据"""
        logger.info("开始获取角色社交网络数据")
        for char in self.characters:
            self._fetch_character_social_network(char["name_zh"])
            time.sleep(self.time_sleep)
        logger.info(f"获取完成，共 {len(self.social_network)} 条关系数据")

    def _fetch_character_social_network(self, character_zh: str):
        """获取单个角色的社交网络数据"""
        char_en = next(c["name_en"] for c in self.characters if c["name_zh"] == character_zh)
        logger.info(f"获取角色 {character_zh} 的社交网络")

        path = quote(f"{character_zh}语音", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"

        response = self._request_with_retry(url)
        soup = BeautifulSoup(response.text, "html.parser")
        item_divs = soup.find_all("div", style="margin:2px 0px;width:100%;display: table;overflow: hidden;padding:1px;")

        for item_div in item_divs:
            title = item_div.find("div", style="display: table-cell;width:180px;vertical-align: middle;background:#8F98A6;padding:5px 10px;color:#fff;font-weight:bold")
            content_zh = item_div.find("div", class_="voice_text_chs vt_active")
            content_en = item_div.find("div", class_="voice_text_en")

            if not (title and content_zh and content_en):
                continue

            title_text = title.text.strip()
            content_zh_text = content_zh.text.strip()
            content_en_text = content_en.text.strip()

            for other_char in self.characters:
                if other_char["name_zh"] == character_zh:
                    continue
                if other_char["name_zh"] not in title_text:
                    continue

                self.social_network.append({
                    "name_zh": character_zh,
                    "title_zh": f"{character_zh}关于{other_char['name_zh']}",
                    "content_zh": content_zh_text,
                    "name_en": char_en,
                    "title_en": f"{char_en} about {other_char['name_en']}",
                    "content_en": content_en_text,
                })

    def _save_results(self):
        """步骤4：保存结果到JSON文件"""
        logger.info("保存结果到JSON文件")
        output_path = DATA_DIR / "social_network.json"

        payload = {
            "characters": self.characters,
            "social_network": self.social_network,
        }

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        logger.info(f"保存完成：{output_path}")

    def _request_with_retry(self, url: str) -> requests.Response:
        """带重试的HTTP请求"""
        for attempt in range(self.max_retries):
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            response.encoding = "utf-8"

            if response.status_code == 200:
                return response

            logger.warning(f"请求失败 {url}, 状态码: {response.status_code}, 重试: {attempt + 1}")
            time.sleep(self.time_sleep * 30)

        raise Exception(f"请求失败 {url}, 已达最大重试次数")


def run_crawler():
    """运行爬虫的入口函数"""
    logger.info("原神爬虫开始运行")
    crawler = GenshinCrawler()
    crawler.run()
    logger.info("原神爬虫运行结束")


if __name__ == "__main__":
    run_crawler()