import sys
from pathlib import Path
import logging
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import time

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config import setup_logging, crawler_settings, settings, get_business_database
from app.services.neo4j_service import Neo4jService

setup_logging("crawler")
logger = logging.getLogger("crawler")


class GenshinCrawler:

    def __init__(self):
        self.characters = []
        self.social_network = []
        self.cookies = crawler_settings.website_cookies["wiki_biligame_com"]["cookie_name"]
        self.headers = crawler_settings.headers
        self.time_sleep = crawler_settings.time_sleep
        self.max_retries = crawler_settings.max_retries

    def run(self):
        self._fetch_character_names_zh()
        self._fetch_character_names_en()
        self._fetch_social_network()
        self._save_results()

    def _fetch_character_names_zh(self):
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

    def _fetch_character_names_en(self):
        logger.info("开始执行步骤2：获取角色名称英文列表")
        count = 0
        for _ in range(len(self.characters)):
            self.characters[_]["name_en"] = self._fetch_name_en(self.characters[_]["name_zh"])
            count += 1
            time.sleep(self.time_sleep)
        logger.info(f"步骤2执行完成，共获取 {count} 个角色英文名称")
        s=",".join([character['name_en'] for character in self.characters])
        logger.info(f"【原神角色英文名称】：{s}")

    def _fetch_name_en(self, character_zh: str) -> str:
        path = quote(f"{character_zh}", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        try:
            times = 0
            while times < self.max_retries:
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                response.encoding = "utf-8"
                if response.status_code != 200:
                    logger.error(f"步骤2获取角色 {character_zh} 请求URL: {url}, 状态码: {response.status_code}, 重试次数: {times + 1}")
                    times += 1
                    time.sleep(self.time_sleep*30)
                else:
                    break
            else:
                raise Exception(f"步骤2获取角色 {character_zh} 请求URL: {url}失败，已达到最大重试次数: {self.max_retries}")
            soup = BeautifulSoup(response.text, "html.parser")
            character_en = soup.select_one('th:-soup-contains("全名/本名") + td span[lang="en"]').get_text(strip=True)[:-1]
            if "流浪者" in character_zh:
                character_en = character_en[:character_en.index("；")]
            return character_en
        except Exception as e:
            logger.error(f"步骤2获取角色 {character_zh} 的英文名称失败: {e}")
            raise

    def _fetch_social_network(self):
        logger.info("开始执行步骤3：获取角色社交网络数据")
        count = 0
        for character in self.characters:
            self._fetch_character_social_network(character["name_zh"])
            count += 1
            time.sleep(self.time_sleep)
        logger.info(f"步骤3执行完成，共获取 {count} 个角色社交网络数据")

    def _fetch_character_social_network(self, character_zh: str):
        character_en = [i for i in self.characters if i["name_zh"] == character_zh][0]["name_en"]
        logger.info(f"开始获取角色 {character_zh} 的社交网络数据")
        path = quote(f"{character_zh}语音", encoding="utf-8")
        url = f"https://wiki.biligame.com/ys/{path}"
        try:
            times = 0
            while times < self.max_retries:
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                response.encoding = "utf-8"
                if response.status_code != 200:
                    logger.error(f"步骤3获取角色 {character_zh} 请求URL: {url}, 状态码: {response.status_code}, 重试次数: {times + 1}")
                    times += 1
                    time.sleep(self.time_sleep*30)
                else:
                    break
            else:
                raise Exception(f"步骤3获取角色 {character_zh} 请求URL: {url}失败，已达到最大重试次数: {self.max_retries}")
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
                        if character_name["name_zh"] == character_zh:
                            continue
                        if character_name["name_zh"] not in title:
                            continue
                        title_zh = f"{character_zh}关于{character_name['name_zh']}"
                        title_en = f"{character_en} about {character_name['name_en']}"
                        self.social_network.append({
                            "name_zh": character_zh,
                            "title_zh": title_zh,
                            "content_zh": content_zh,
                            "name_en": character_en,
                            "title_en": title_en,
                            "content_en": content_en
                        })
            logger.info(f"步骤3获取角色 {character_zh} 的社交网络数据完成")
        except Exception as e:
            logger.error(f"步骤3获取角色 {character_zh} 的社交网络数据失败: {e}")
            raise

    def _save_results(self):
        logger.info("开始执行步骤4：将内存中的结果写入 Neo4j")
        nodes = [
            {"id": c["name_en"], "properties": {"name_zh": c["name_zh"], "name_en": c["name_en"]}}
            for c in self.characters
        ]
        edges = []
        for row in self.social_network:
            source_id = row["name_en"]
            target_id = row["title_en"].split(" about ", 1)[1].strip()
            edge_id = f"{source_id} to {target_id}"
            source_name_en = row["name_en"]
            target_name_en = row["title_en"].split(" about ", 1)[1].strip()
            source_name_zh = row["name_zh"]
            target_name_zh = row["title_zh"].split("关于", 1)[1].strip()
            title_en = row["title_en"]
            title_zh = row["title_zh"]
            edges.append({
                "id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "properties": {
                    "source_name_en": source_name_en,
                    "target_name_en": target_name_en,
                    "source_name_zh": source_name_zh,
                    "target_name_zh": target_name_zh,
                    "title_en": title_en,
                    "title_zh": title_zh,
                },
            })
        neo4j = Neo4jService(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=get_business_database("genshin"),
        )
        try:
            neo4j.connect()
            n_count = neo4j.add_nodes("Character", nodes)
            e_count = neo4j.add_edges("To", edges)
            logger.info(f"步骤4执行完成，写入 Neo4j 节点数: {n_count}，关系数: {e_count}")
        except Exception as e:
            logger.error(f"步骤4执行失败: {e}")
            raise
        finally:
            neo4j.close()


def run_crawler():
    logger.info("原神拓扑爬取程序开始运行")
    crawler = GenshinCrawler()
    crawler.run()
    logger.info("原神拓扑爬取程序运行结束")


if __name__ == "__main__":
    run_crawler()