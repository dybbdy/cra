"""
QS 世界大学排名爬虫。

实现目标：
1. 自动访问 QS 排名页面
2. 自动判断优先使用 requests 静态解析，必要时切换 Selenium
3. 抓取前 100 所大学
4. 下载 Logo 到 QSLogo 目录
5. 保存抓取结果到 Result/QSRank.txt
"""

from __future__ import annotations

import argparse
import logging
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


try:
    from selenium import webdriver
    from selenium.common.exceptions import SessionNotCreatedException, TimeoutException, WebDriverException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    webdriver = None
    TimeoutException = Exception
    WebDriverException = Exception
    SessionNotCreatedException = Exception
    ChromeOptions = None
    ChromeService = None
    EdgeOptions = None
    EdgeService = None
    By = None
    EC = None
    WebDriverWait = None


BASE_DIR = Path(__file__).resolve().parent
QS_LOGO_DIR = BASE_DIR / "QSLogo"
RESULT_DIR = BASE_DIR / "Result"
OUTPUT_TXT = RESULT_DIR / "QSRank.txt"

TARGET_URL_2026 = "https://www.topuniversities.com/world-university-rankings/2026"
FALLBACK_URL = "https://www.topuniversities.com/world-university-rankings"


class QSRankCrawler:
    """QS 排名抓取器。"""

    RANK_RE = re.compile(r"Rank\s*(=?\s*\d+)")
    SCORE_RE = re.compile(r"Overall Score:\s*([0-9.]+)")
    LOCATION_RE = re.compile(
        r"([^\n]+,\s*[^\n]+)(?=\s*(?:QS Stars|Citations per Faculty|Academic Reputation|Faculty Student Ratio|Employer Reputation))"
    )

    def __init__(self, browser: str = "edge") -> None:
        self.session = self._build_session()
        self.browser = (browser or "edge").lower()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        ]
        self.headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.topuniversities.com/",
        }

    @staticmethod
    def _build_session() -> requests.Session:
        """创建带自动重试的请求会话。"""
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def ensure_directories() -> None:
        """自动创建目录。"""
        QS_LOGO_DIR.mkdir(parents=True, exist_ok=True)
        RESULT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def random_sleep() -> None:
        """随机延时 1~3 秒，降低访问频率。"""
        delay = random.uniform(1, 3)
        logging.info("随机休眠 %.2f 秒", delay)
        time.sleep(delay)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """清理非法文件名字符。"""
        cleaned = re.sub(r"[\\\\/:*?\"<>|]", "_", name.strip())
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned[:150] if cleaned else "unknown"

    def fetch_html(self, url: str) -> str:
        """下载网页源码。"""
        logging.info("使用 requests 请求页面：%s", url)
        self.random_sleep()
        response = self.session.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _extract_location(raw_text: str) -> tuple[str, str]:
        """从“城市, 国家”文本中拆分城市与国家。"""
        if raw_text and "," in raw_text:
            city, country = [item.strip() for item in raw_text.rsplit(",", 1)]
            return city, country
        return "", ""

    def _parse_card_text(self, text: str) -> Dict[str, str]:
        """从卡片文本中解析排名、分数、城市、国家。"""
        rank_raw = ""
        score = ""
        location_raw = ""

        rank_match = self.RANK_RE.search(text)
        if rank_match:
            rank_raw = rank_match.group(1).replace(" ", "")

        score_match = self.SCORE_RE.search(text)
        if score_match:
            score = score_match.group(1)

        location_match = self.LOCATION_RE.search(text)
        if location_match:
            location_raw = location_match.group(1).strip()

        city, country = self._extract_location(location_raw)
        return {
            "排名": rank_raw,
            "分数": score,
            "城市": city,
            "国家": country,
        }

    def parse_static(self, html: str) -> List[Dict[str, str]]:
        """
        尝试使用静态 HTML 解析。

        说明：
        QS 页面存在动态加载与反爬，静态解析成功率不稳定，因此仅作为优先方案。
        """
        logging.info("开始尝试静态解析 QS 页面")
        soup = BeautifulSoup(html, "lxml")
        anchors = soup.select("a[href*='/universities/']")
        results: List[Dict[str, str]] = []
        seen_urls = set()

        for anchor in anchors:
            if not isinstance(anchor, Tag):
                continue

            name = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "")
            if not name or not href or href in seen_urls:
                continue

            if len(name) < 3:
                continue

            container = anchor
            for _ in range(8):
                parent = container.parent
                if not isinstance(parent, Tag):
                    break
                parent_text = parent.get_text(" ", strip=True)
                if "Rank" in parent_text and "Overall Score:" in parent_text:
                    container = parent
                    break
                container = parent

            container_text = container.get_text("\n", strip=True)
            parsed = self._parse_card_text(container_text)
            if not parsed["排名"]:
                continue

            logo_url = ""
            image = container.select_one("a[href*='/universities/'] img")
            if image and image.get("src"):
                logo_url = urljoin(TARGET_URL_2026, image["src"])

            item = {
                "学校名称": name,
                "排名": parsed["排名"],
                "分数": parsed["分数"],
                "城市": parsed["城市"],
                "国家": parsed["国家"],
                "Logo URL": logo_url,
            }
            results.append(item)
            seen_urls.add(href)

            if len(results) >= 100:
                break

        logging.info("静态解析得到 %s 条数据", len(results))
        return results

    def _create_driver(self) -> webdriver.Chrome:
        """根据配置创建 Selenium 浏览器驱动。"""
        if webdriver is None:
            raise RuntimeError("未安装 selenium，无法启动浏览器模式")

        browser = self.browser
        if browser not in {"edge", "chrome"}:
            raise RuntimeError(f"暂不支持的浏览器类型：{browser}")

        def build_options(safe_mode: bool) -> object:
            if browser == "edge":
                if EdgeOptions is None or EdgeService is None:
                    raise RuntimeError("当前环境不支持 Edge WebDriver")
                opts = EdgeOptions()
            else:
                if ChromeOptions is None or ChromeService is None:
                    raise RuntimeError("当前环境不支持 Chrome WebDriver")
                opts = ChromeOptions()

            opts.add_argument("--disable-gpu")
            opts.add_argument("--window-size=1600,1000")
            opts.add_argument("--no-first-run")
            opts.add_argument("--no-default-browser-check")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--remote-allow-origins=*")

            if not safe_mode:
                opts.add_argument("--disable-blink-features=AutomationControlled")
                opts.add_argument(f"--user-agent={random.choice(self.user_agents)}")
                try:
                    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
                    opts.add_experimental_option("useAutomationExtension", False)
                except Exception:
                    pass

            return opts

        def create_with_options(opts: object) -> webdriver.Chrome:
            logging.info("Selenium 当前使用浏览器：%s", browser)
            if browser == "edge":
                return webdriver.Edge(service=EdgeService(), options=opts)
            return webdriver.Chrome(service=ChromeService(), options=opts)

        try:
            options = build_options(safe_mode=False)
            driver = create_with_options(options)
        except (SessionNotCreatedException, WebDriverException) as exc:
            logging.warning("浏览器启动失败，尝试安全模式重试：%s", exc)
            options = build_options(safe_mode=True)
            driver = create_with_options(options)

        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            },
        )
        return driver

    @staticmethod
    def _normalize_detail_url(url: str) -> str:
        """规范化学校详情链接，用于去重。"""
        if not url:
            return ""
        return url.split("?")[0].rstrip("/")

    def _extract_cards_on_current_page(
        self,
        driver: webdriver.Chrome,
        seen_urls: set[str],
        remain_count: int,
    ) -> List[Dict[str, str]]:
        """提取当前分页中的学校卡片，优先使用 page_source 解析以避免 stale element。"""
        results: List[Dict[str, str]] = []
        row_html_list = driver.execute_script(
            """
            return Array.from(
                document.querySelectorAll('#ranking-data-load .new-ranking-cards')
            ).map((el) => el.outerHTML);
            """
        )

        for row_html in row_html_list:
            try:
                row = BeautifulSoup(row_html, "lxml")
                anchor_candidates = row.select("a[href*='/universities/']")
                name_el = None
                detail_url = ""

                for anchor in anchor_candidates:
                    anchor_text = anchor.get_text(" ", strip=True)
                    href = anchor.get("href", "")
                    if anchor_text and href:
                        name_el = anchor
                        detail_url = self._normalize_detail_url(href)
                        break

                if name_el is None or not detail_url:
                    continue

                if detail_url in seen_urls:
                    continue

                name = name_el.get_text(" ", strip=True)
                text = row.get_text("\n", strip=True)
                parsed = self._parse_card_text(text)
                if not name or not parsed["排名"]:
                    continue

                logo_url = ""
                logo_el = row.select_one("a[href*='/universities/'] img")
                if logo_el and logo_el.get("src"):
                    logo_url = logo_el.get("src", "")

                item = {
                    "学校名称": name,
                    "排名": parsed["排名"],
                    "分数": parsed["分数"],
                    "城市": parsed["城市"],
                    "国家": parsed["国家"],
                    "Logo URL": logo_url,
                }
                results.append(item)
                seen_urls.add(detail_url)
            except Exception as exc:
                logging.warning("解析当前页学校卡片失败：%s", exc)

            if len(results) >= remain_count:
                break

        return results

    def _go_to_next_page(self, driver: webdriver.Chrome, previous_range_text: str) -> bool:
        """点击分页下一页，并等待结果区间文本变化。"""
        next_buttons = driver.find_elements(By.CSS_SELECTOR, "#alt-style-pagination a.page-link.next")
        if not next_buttons:
            logging.info("未找到下一页按钮，分页抓取结束")
            return False

        next_button = next_buttons[0]
        next_classes = (next_button.get_attribute("class") or "").lower()
        if "disabled" in next_classes:
            logging.info("下一页按钮已禁用，分页抓取结束")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", next_button)

        WebDriverWait(driver, 20).until(
            lambda d: (
                (d.find_element(By.CSS_SELECTOR, "._perpagejstext").text.strip() != previous_range_text)
                and len(d.find_elements(By.CSS_SELECTOR, "#ranking-data-load .new-ranking-cards")) > 0
            )
        )
        time.sleep(2)
        return True

    def parse_by_selenium(self, url: str) -> List[Dict[str, str]]:
        """使用 Selenium 按分页抓取前 100 所大学。"""
        logging.info("切换为 Selenium 抓取：%s", url)
        driver = self._create_driver()
        results: List[Dict[str, str]] = []
        seen_urls: set[str] = set()

        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(
                lambda d: (
                    "安全验证" not in d.page_source
                    and "Please Wait" not in d.title
                    and len(d.find_elements(By.CSS_SELECTOR, "#ranking-data-load .new-ranking-cards")) > 0
                )
            )

            current_page = 1
            while len(results) < 100 and current_page <= 4:
                WebDriverWait(driver, 20).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "#ranking-data-load .new-ranking-cards")) > 0
                )
                current_range_text = driver.find_element(By.CSS_SELECTOR, "._perpagejstext").text.strip()
                remain_count = 100 - len(results)
                page_items = self._extract_cards_on_current_page(driver, seen_urls, remain_count)
                results.extend(page_items)
                logging.info(
                    "已抓取第 %s 页，当前范围：%s，累计 %s 条",
                    current_page,
                    current_range_text,
                    len(results),
                )

                if len(results) >= 100:
                    break

                moved = self._go_to_next_page(driver, current_range_text)
                if not moved:
                    break
                current_page += 1

        except TimeoutException as exc:
            raise RuntimeError("Selenium 等待页面结果超时，可能触发了安全验证") from exc
        finally:
            driver.quit()

        logging.info("Selenium 抓取到 %s 条数据", len(results))
        return results[:100]

    def collect_data(self) -> List[Dict[str, str]]:
        """自动判断抓取方式并采集前 100 所大学。"""
        candidate_urls = [TARGET_URL_2026, FALLBACK_URL]

        for current_url in candidate_urls:
            try:
                html = self.fetch_html(current_url)
            except Exception as exc:
                logging.warning("requests 访问页面失败：%s -> %s", current_url, exc)
                continue

            if "blank page" in html.lower() or "coming soon" in html.lower():
                logging.warning("页面疑似空白或不可用：%s", current_url)
                continue

            results = self.parse_static(html)
            if len(results) >= 100:
                return results[:100]

            logging.info("页面 %s 的静态结果不足 100 条，尝试 Selenium 补抓", current_url)
            try:
                results = self.parse_by_selenium(current_url)
                if results:
                    return results[:100]
            except Exception as exc:
                logging.warning("Selenium 抓取失败：%s -> %s", current_url, exc)

        logging.info("requests 直连均不可用，最后尝试使用 Selenium 访问主排名页")
        results = self.parse_by_selenium(FALLBACK_URL)
        return results[:100]

    def download_logo(self, school_name: str, logo_url: str) -> Optional[Path]:
        """下载大学 Logo 图片。"""
        if not logo_url:
            logging.warning("学校 %s 没有可下载的 Logo URL", school_name)
            return None

        safe_name = self.sanitize_filename(school_name) + ".png"
        output_path = QS_LOGO_DIR / safe_name
        try:
            self.random_sleep()
            response = self.session.get(logo_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            output_path.write_bytes(response.content)
            logging.info("已保存 Logo：%s", output_path)
            return output_path
        except Exception as exc:
            logging.error("下载 Logo 失败：%s -> %s", school_name, exc)
            return None

    def save_results(self, results: List[Dict[str, str]]) -> None:
        """保存排名结果到文本文件。"""
        lines = []
        for index, item in enumerate(results, start=1):
            lines.extend(
                [
                    f"第{index}条",
                    f"学校名称：{item['学校名称']}",
                    f"排名：{item['排名']}",
                    f"分数：{item['分数']}",
                    f"城市：{item['城市']}",
                    f"国家：{item['国家']}",
                    f"Logo URL：{item['Logo URL']}",
                    "-" * 60,
                ]
            )

        OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")
        logging.info("已保存结果文件：%s", OUTPUT_TXT)

    def run(self) -> None:
        """程序主入口。"""
        self.ensure_directories()
        results = self.collect_data()
        if not results:
            raise RuntimeError("未采集到任何 QS 排名数据")

        for item in results:
            self.download_logo(item["学校名称"], item["Logo URL"])

        self.save_results(results)
        logging.info("QS 排名抓取完成，共 %s 条", len(results))


def configure_logging() -> None:
    """配置日志输出格式。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    """脚本启动入口。"""
    configure_logging()
    parser = argparse.ArgumentParser(description="QS 世界大学排名爬虫")
    parser.add_argument(
        "--browser",
        choices=["edge", "chrome"],
        default="edge",
        help="Selenium 使用的浏览器，默认 edge",
    )
    args = parser.parse_args()
    crawler = QSRankCrawler(browser=args.browser)
    crawler.run()


if __name__ == "__main__":
    main()
