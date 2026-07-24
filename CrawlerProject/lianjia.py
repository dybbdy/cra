"""
北京链家二手房爬虫。

实现功能：
1. 自动翻页抓取 100 条以上房源
2. 抽取小区名、户型、面积、朝向、楼层、总价、单价
3. 尝试访问详情页抓取经纪人姓名、联系电话
4. 对姓名脱敏，对电话使用 AES-256-CBC 加密
5. 使用 HMAC-SHA256 对关键字段生成认证码
6. 使用 pandas + openpyxl 导出到 Excel
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from crypto_utils import encrypt_phone, generate_hmac, mask_name


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
RESULT_DIR = BASE_DIR / "Result"
OUTPUT_XLS = RESULT_DIR / "Lianjia.xls"
PUBLIC_OUTPUT_XLS = RESULT_DIR / "Lianjia_Public.xls"
LOGIN_OUTPUT_XLS = RESULT_DIR / "Lianjia_Login.xls"
BASE_URL = "https://bj.lianjia.com/ershoufang/"


@dataclass
class HouseRecord:
    """房源数据结构。"""

    小区名: str
    户型: str
    面积: str
    朝向: str
    楼层: str
    总价: str
    单价: str
    脱敏姓名: str
    电话密文: str
    HMAC: str


class LianjiaCrawler:
    """链家二手房爬虫。"""

    def __init__(
        self,
        target_count: int = 100,
        max_detail_pages: int = 100,
        enable_manual_verify: bool = True,
        browser: str = "edge",
    ) -> None:
        self.target_count = max(target_count, 100)
        self.max_detail_pages = max(0, max_detail_pages)
        self.enable_manual_verify = enable_manual_verify
        self.browser = (browser or "edge").lower()
        self.cookie_file = RESULT_DIR / f"lianjia_session_{self.browser}.json"

    @staticmethod
    def ensure_directories() -> None:
        """自动创建结果目录。"""
        RESULT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def random_sleep() -> None:
        """随机休眠 3~6 秒，降低被检测风险。"""
        delay = random.uniform(3, 6)
        logging.info("随机休眠 %.2f 秒", delay)
        time.sleep(delay)

    @staticmethod
    def parse_house_info(house_info_text: str) -> Dict[str, str]:
        """
        解析房源基础信息字符串。

        常见格式：
        2室1厅 | 89.3平米 | 南 北 | 精装 | 高楼层(共18层) | 板楼
        """
        parts = [item.strip() for item in house_info_text.split("|")]
        return {
            "户型": parts[0] if len(parts) > 0 else "",
            "面积": parts[1] if len(parts) > 1 else "",
            "朝向": parts[2] if len(parts) > 2 else "",
            "楼层": parts[4] if len(parts) > 4 else "",
        }

    @staticmethod
    def build_hmac_source(item: Dict[str, str]) -> str:
        """按课程要求拼接 HMAC 原文。"""
        fields = [
            item.get("小区名", ""),
            item.get("户型", ""),
            item.get("面积", ""),
            item.get("朝向", ""),
            item.get("楼层", ""),
            item.get("总价", ""),
            item.get("单价", ""),
            item.get("脱敏姓名", ""),
            item.get("电话密文", ""),
        ]
        return "|".join(fields)

    def _create_driver(self) -> webdriver.Chrome:
        """创建 Selenium 驱动，并复用本地浏览器资料目录。"""
        if webdriver is None:
            raise RuntimeError("未安装 selenium，无法执行浏览器抓取")

        browser = self.browser
        if browser not in {"edge", "chrome"}:
            raise RuntimeError(f"暂不支持的浏览器类型：{browser}")

        def build_options(safe_mode: bool) -> object:
            profile_dir = RESULT_DIR / f"{browser}_profile"
            profile_dir.mkdir(parents=True, exist_ok=True)

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
                opts.add_argument(f"--user-data-dir={profile_dir}")
                opts.add_argument("--profile-directory=Default")
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
    def _is_captcha_page(
        current_url: str = "",
        title: str = "",
        body_text: str = "",
        has_house_cards: bool = False,
    ) -> bool:
        """判断当前页面是否为验证码或安全验证页面。"""
        if has_house_cards:
            return False

        current_url = (current_url or "").lower()
        title = (title or "").lower()
        body_text = (body_text or "").lower()

        # URL 已跳到安全中心时，直接判定为验证码页面。
        if "hip.lianjia.com/captcha" in current_url:
            return True

        visible_keywords = [
            "人机验证",
            "安全验证",
            "点击按钮开始验证",
            "贝壳信息安全中心",
            "captcha",
            "geetest",
        ]
        visible_text = "\n".join([title, body_text])
        return any(keyword.lower() in visible_text for keyword in visible_keywords)

    def _wait_manual_verification(self, driver: webdriver.Chrome, current_url: str) -> bool:
        """
        等待用户手动完成验证码。

        设计思路：
        1. 浏览器使用持久化 profile，验证状态可在当前运行期持续复用
        2. 用户在浏览器中完成一次验证后，脚本继续用同一 driver 访问后续详情页
        """
        if not self.enable_manual_verify:
            logging.warning("当前已禁用人工验证码处理，跳过详情页人工介入")
            return False

        print("\n" + "=" * 72)
        print("检测到链家验证码页面。")
        print("请在已打开的浏览器窗口中手动完成验证。")
        print(f"当前页面：{current_url}")
        print("验证完成后，回到终端按一次回车，程序将继续复用当前浏览器会话抓取详情页。")
        print("=" * 72 + "\n")
        input("完成验证后请按回车继续：")
        time.sleep(2)

        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            body_text = ""

        has_house_cards = False
        try:
            has_house_cards = len(driver.find_elements(By.CSS_SELECTOR, ".sellListContent li")) > 0
        except Exception:
            has_house_cards = False

        if self._is_captcha_page(driver.current_url, driver.title, body_text, has_house_cards):
            logging.warning("回车后仍检测到验证码页面，当前会话暂不可用")
            return False

        logging.info("人工验证完成，继续复用当前浏览器会话抓取详情页")
        return True

    def _save_driver_cookies(self, driver: webdriver.Chrome) -> None:
        """将浏览器 Cookie 保存到本地文件，供下次运行复用。"""
        try:
            cookies = driver.get_cookies()
            self.cookie_file.write_text(
                json.dumps(cookies, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logging.info("已保存登录会话 Cookie：%s", self.cookie_file)
        except Exception as exc:
            logging.warning("保存登录会话 Cookie 失败：%s", exc)

    def _load_saved_cookies(self, driver: webdriver.Chrome) -> bool:
        """从本地文件加载已保存 Cookie，并刷新首页复用登录态。"""
        if not self.cookie_file.exists():
            logging.info("未找到历史登录会话 Cookie，本次需手动验证并登录")
            return False

        try:
            cookies = json.loads(self.cookie_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logging.warning("读取会话 Cookie 文件失败：%s", exc)
            return False

        loaded_count = 0
        for cookie in cookies:
            try:
                cookie_copy = dict(cookie)
                if "expiry" in cookie_copy:
                    cookie_copy["expiry"] = int(cookie_copy["expiry"])
                driver.add_cookie(cookie_copy)
                loaded_count += 1
            except Exception:
                continue

        if loaded_count == 0:
            logging.warning("历史 Cookie 文件存在，但没有成功注入任何 Cookie")
            return False

        driver.get(BASE_URL)
        time.sleep(2)
        logging.info("已加载历史登录会话 Cookie，共 %s 条", loaded_count)
        return True

    def _prepare_authenticated_session(self) -> webdriver.Chrome:
        """
        先打开首页，等待用户手动完成人机验证和登录，再开始抓取。

        若本地存在历史 Cookie，则先尝试自动恢复登录态；
        用户确认当前浏览器状态无误后再按回车继续。
        """
        driver = self._create_driver()
        driver.get(BASE_URL)
        time.sleep(2)
        self._load_saved_cookies(driver)

        print("\n" + "=" * 72)
        print("链家抓取将先使用浏览器首页建立会话。")
        print("请在已打开的浏览器窗口中完成人机验证和登录。")
        print("如果浏览器已经自动恢复为可访问状态，也可以直接回车继续。")
        print(f"当前首页：{BASE_URL}")
        print("=" * 72 + "\n")
        input("完成人机验证/登录后，请按回车开始抓取：")
        time.sleep(2)

        self._save_driver_cookies(driver)
        return driver

    def _load_page_with_reuse_session(self, driver: webdriver.Chrome, url: str) -> bool:
        """
        使用当前浏览器会话打开目标页面。

        若遇到验证码，则允许人工完成一次验证后继续使用同一会话。
        """
        logging.info("浏览器访问页面：%s", url)
        driver.get(url)
        time.sleep(random.uniform(1, 2))

        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            body_text = ""

        has_house_cards = False
        try:
            has_house_cards = len(driver.find_elements(By.CSS_SELECTOR, ".sellListContent li")) > 0
        except Exception:
            has_house_cards = False

        if self._is_captcha_page(driver.current_url, driver.title, body_text, has_house_cards):
            logging.warning("当前页面触发验证码：目标=%s，实际URL=%s，标题=%s", url, driver.current_url, driver.title)
            if not self._wait_manual_verification(driver, url):
                return False

        return True

    @staticmethod
    def _extract_by_selectors(driver: webdriver.Chrome, selectors: List[str]) -> str:
        """按多个 CSS 选择器顺序尝试提取文本。"""
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text:
                        return text
            except Exception:
                continue
        return ""

    def _extract_agent_info_from_driver(self, driver: webdriver.Chrome) -> tuple[str, str]:
        """从已打开的详情页中提取经纪人姓名与联系电话。"""
        page_source = driver.page_source
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            body_text = ""

        agent_name = self._extract_by_selectors(
            driver,
            [
                ".brokerInfoText .name",
                ".brokerCard .name",
                ".brokerName .name",
                ".ke-agent-sj-name",
                ".agent-name",
                ".brokerInfo .name",
            ],
        )
        if not agent_name:
            agent_name = self._extract_agent_name(body_text)

        phone = ""
        try:
            phone_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
            for link in phone_links:
                href = link.get_attribute("href") or ""
                phone = self._extract_phone(href)
                if phone:
                    break
        except Exception:
            phone = ""

        if not phone:
            phone = self._extract_by_selectors(
                driver,
                [
                    ".brokerInfoText .phone",
                    ".brokerCard .phone",
                    ".phone-text",
                    ".agent-phone",
                ],
            )
            phone = self._extract_phone(phone)

        if not phone:
            phone = self._extract_phone(body_text) or self._extract_phone(page_source)

        return agent_name, phone

    def _prepare_detail_session(self, driver: webdriver.Chrome, probe_url: str) -> bool:
        """
        预热详情页会话。

        首次先打开一个详情页，如果出现验证码，由用户手动验证一次；
        验证成功后，后续详情页尽量复用同一浏览器会话。
        """
        logging.info("开始预热详情页浏览器会话")
        ok = self._load_page_with_reuse_session(driver, probe_url)
        if ok:
            logging.info("详情页浏览器会话已准备完成")
        else:
            logging.warning("详情页浏览器会话准备失败，后续将以空详情字段继续导出")
        return ok

    def parse_list_by_selenium(self, driver: webdriver.Chrome, max_pages: int = 10) -> List[Dict[str, str]]:
        """使用 Selenium 自动翻页抓取链家列表页。"""
        logging.info("切换为 Selenium 抓取链家列表页")
        records: List[Dict[str, str]] = []

        try:
            for page in range(1, max_pages + 1):
                if len(records) >= self.target_count:
                    break

                page_url = BASE_URL if page == 1 else f"{BASE_URL}pg{page}/"
                ok = self._load_page_with_reuse_session(driver, page_url)
                if not ok:
                    raise RuntimeError("链家列表页验证码未能恢复，无法继续自动抓取")

                WebDriverWait(driver, 30).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, ".sellListContent li")) > 0
                )
                self.random_sleep()

                houses = driver.find_elements(By.CSS_SELECTOR, ".sellListContent li")
                for house in houses:
                    try:
                        title_link = house.find_element(By.CSS_SELECTOR, ".title a")
                        community_link = house.find_element(By.CSS_SELECTOR, ".positionInfo a")
                        house_info = house.find_element(By.CSS_SELECTOR, ".houseInfo")
                        total_price = house.find_element(By.CSS_SELECTOR, ".totalPrice span")
                        unit_price = house.find_element(By.CSS_SELECTOR, ".unitPrice span")

                        parsed_info = self.parse_house_info(house_info.text.strip())
                        item = {
                            "小区名": community_link.text.strip(),
                            "户型": parsed_info["户型"],
                            "面积": parsed_info["面积"],
                            "朝向": parsed_info["朝向"],
                            "楼层": parsed_info["楼层"],
                            "总价": total_price.text.strip() + "万",
                            "单价": unit_price.text.strip(),
                            "详情链接": title_link.get_attribute("href") or "",
                        }
                        records.append(item)
                    except Exception as exc:
                        logging.warning("解析链家列表房源失败：%s", exc)

                    if len(records) >= self.target_count:
                        break

                logging.info("已通过 Selenium 累计抓取 %s 条房源", len(records))

        except TimeoutException as exc:
            raise RuntimeError("Selenium 打开链家列表页超时") from exc

        return records[: self.target_count]

    @staticmethod
    def _extract_phone(text: str) -> str:
        """从文本中提取手机号。"""
        if not text:
            return ""
        match = re.search(r"(1[3-9]\d{9})", text)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_agent_name(text: str) -> str:
        """尽力从详情页文本中提取经纪人姓名。"""
        patterns = [
            r"经纪人[:：]\s*([\u4e00-\u9fa5]{2,4})",
            r"贝壳经纪人\s*([\u4e00-\u9fa5]{2,4})",
            r"联系人[:：]\s*([\u4e00-\u9fa5]{2,4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    def enrich_agent_info(
        self,
        base_items: List[Dict[str, str]],
        driver: webdriver.Chrome,
        max_details: int = 20,
    ) -> List[Dict[str, str]]:
        """
        尝试进入部分详情页抓取经纪人姓名与电话。

        说明：
        链家详情页容易触发验证码，因此此处采用受控抓取：
        1. 默认只访问前若干条详情页
        2. 如果验证码出现，则保留空字段并继续后续加密/导出流程
        """
        if not base_items:
            return base_items

        first_detail_url = next((item.get("详情链接", "") for item in base_items if item.get("详情链接")), "")
        if not first_detail_url:
            logging.warning("未找到任何详情页链接，跳过详情页抓取")
            return base_items

        session_ready = self._prepare_detail_session(driver, first_detail_url)
        if not session_ready:
            return base_items

        for index, item in enumerate(base_items):
            item["经纪人姓名"] = ""
            item["联系电话"] = ""

            if index >= max_details:
                continue

            detail_url = item.get("详情链接", "")
            if not detail_url:
                continue

            try:
                ok = self._load_page_with_reuse_session(driver, detail_url)
                if not ok:
                    logging.warning("当前详情页无法通过人工验证恢复，停止后续详情抓取")
                    break

                agent_name, phone = self._extract_agent_info_from_driver(driver)

                item["经纪人姓名"] = agent_name
                item["联系电话"] = phone
                logging.info(
                    "详情页抓取完成：索引=%s，经纪人=%s，电话是否获取=%s",
                    index + 1,
                    agent_name or "未获取",
                    "是" if phone else "否",
                )
            except Exception as exc:
                logging.warning("详情页抓取失败：%s", exc)

        return base_items

    def protect_and_convert(self, raw_items: List[Dict[str, str]]) -> List[HouseRecord]:
        """对房源数据执行脱敏、加密与 HMAC 保护。"""
        result: List[HouseRecord] = []
        for item in raw_items:
            masked_name = mask_name(item.get("经纪人姓名", ""))
            encrypted_phone = encrypt_phone(item.get("联系电话", "")) if item.get("联系电话") else ""

            prepared = {
                "小区名": item.get("小区名", ""),
                "户型": item.get("户型", ""),
                "面积": item.get("面积", ""),
                "朝向": item.get("朝向", ""),
                "楼层": item.get("楼层", ""),
                "总价": item.get("总价", ""),
                "单价": item.get("单价", ""),
                "脱敏姓名": masked_name,
                "电话密文": encrypted_phone,
            }
            hmac_value = generate_hmac(self.build_hmac_source(prepared))

            result.append(
                HouseRecord(
                    小区名=prepared["小区名"],
                    户型=prepared["户型"],
                    面积=prepared["面积"],
                    朝向=prepared["朝向"],
                    楼层=prepared["楼层"],
                    总价=prepared["总价"],
                    单价=prepared["单价"],
                    脱敏姓名=prepared["脱敏姓名"],
                    电话密文=prepared["电话密文"],
                    HMAC=hmac_value,
                )
            )
        return result

    def _write_excel_with_alias(self, df: pd.DataFrame, target_xls_path: Path) -> None:
        """写入 xlsx 内容，并同步生成课程要求的 xls 文件名。"""
        excel_path = target_xls_path.with_suffix(".xlsx")
        df.to_excel(excel_path, index=False, engine="openpyxl")
        target_xls_path.write_bytes(excel_path.read_bytes())
        logging.info("已保存 Excel 文件：%s", target_xls_path)

    def save_public_excel(self, raw_items: List[Dict[str, str]]) -> None:
        """导出未登录即可获取的公开字段。"""
        public_rows = [
            {
                "小区名": item.get("小区名", ""),
                "户型": item.get("户型", ""),
                "面积": item.get("面积", ""),
                "朝向": item.get("朝向", ""),
                "楼层": item.get("楼层", ""),
                "总价": item.get("总价", ""),
                "单价": item.get("单价", ""),
            }
            for item in raw_items
        ]
        df = pd.DataFrame(
            public_rows,
            columns=["小区名", "户型", "面积", "朝向", "楼层", "总价", "单价"],
        )
        self._write_excel_with_alias(df, PUBLIC_OUTPUT_XLS)

    def save_login_excel(self, records: List[HouseRecord]) -> None:
        """导出登录后增强字段结果。"""
        data = [record.__dict__ for record in records]
        df = pd.DataFrame(
            data,
            columns=["小区名", "户型", "面积", "朝向", "楼层", "总价", "单价", "脱敏姓名", "电话密文", "HMAC"],
        )
        self._write_excel_with_alias(df, LOGIN_OUTPUT_XLS)

    def save_to_excel(self, records: List[HouseRecord]) -> None:
        """保存课程要求的最终 Excel 结果。"""
        data = [record.__dict__ for record in records]
        df = pd.DataFrame(
            data,
            columns=["小区名", "户型", "面积", "朝向", "楼层", "总价", "单价", "脱敏姓名", "电话密文", "HMAC"],
        )
        self._write_excel_with_alias(df, OUTPUT_XLS)

    def run(self) -> None:
        """执行完整爬取流程。"""
        self.ensure_directories()
        driver = self._prepare_authenticated_session()
        try:
            raw_items = self.parse_list_by_selenium(driver, max_pages=10)
            if len(raw_items) < self.target_count:
                raise RuntimeError(f"房源抓取数量不足，当前仅获得 {len(raw_items)} 条")

            self.save_public_excel(raw_items)
            raw_items = self.enrich_agent_info(raw_items, driver, max_details=self.max_detail_pages)
            protected_items = self.protect_and_convert(raw_items)
            self.save_login_excel(protected_items)
            self.save_to_excel(protected_items)
            logging.info("链家房源抓取完成，共 %s 条", len(protected_items))
        finally:
            self._save_driver_cookies(driver)
            driver.quit()


def configure_logging() -> None:
    """配置日志格式。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    """脚本主入口。"""
    configure_logging()
    parser = argparse.ArgumentParser(description="北京链家二手房课程实验爬虫")
    parser.add_argument("--target-count", type=int, default=100, help="目标抓取房源数量，至少 100")
    parser.add_argument(
        "--max-detail-pages",
        type=int,
        default=100,
        help="最多抓取多少个详情页以提取经纪人信息，默认 100",
    )
    parser.add_argument(
        "--disable-manual-verify",
        action="store_true",
        help="禁用验证码出现后的人工验证与会话复用模式",
    )
    parser.add_argument(
        "--browser",
        choices=["edge", "chrome"],
        default="edge",
        help="Selenium 使用的浏览器，默认 edge",
    )
    args = parser.parse_args()

    crawler = LianjiaCrawler(
        target_count=args.target_count,
        max_detail_pages=args.max_detail_pages,
        enable_manual_verify=not args.disable_manual_verify,
        browser=args.browser,
    )
    crawler.run()


if __name__ == "__main__":
    main()
