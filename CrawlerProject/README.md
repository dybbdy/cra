# CrawlerProject

本项目是按照课程实验要求编写的完整 Python3 爬虫实验项目，包含：

- `qs_rank.py`：QS 世界大学排名抓取
- `lianjia.py`：链家北京二手房抓取
- `crypto_utils.py`：AES 加密、AES 解密、HMAC 生成、姓名脱敏工具

项目代码采用函数化和面向对象结合的方式实现，并补充了中文注释、异常处理、请求失败自动重试、随机延时、自动建目录、日志输出等实验要求。

## 项目目录

```text
CrawlerProject
│
├── qs_rank.py
├── lianjia.py
├── crypto_utils.py
├── requirements.txt
├── README.md
│
├── Baidu/
├── QSLogo/
├── Result/
```

说明：

- `Baidu/`：预留给百度图片方案，本次按照建议实现 QS 方案
- `QSLogo/`：保存 QS 大学 Logo
- `Result/`：保存结果文件

## 环境安装

请先安装依赖：

```bash
pip install -r requirements.txt
```

## 运行方法

运行 QS 排名抓取：

```bash
python qs_rank.py
```

运行链家房产抓取：

```bash
python lianjia.py
```

增强版运行示例：

```bash
python lianjia.py --target-count 100 --max-detail-pages 30
```

链家推荐运行方式：

```bash
python lianjia.py --browser edge
```

### 可视化控制台运行方法

项目已新增一个独立的 Web 可视化前端，位于：

```text
dashboard/
```

安装前端依赖：

```bash
cd dashboard
npm install
```

启动前端与后端联调开发服务：

```bash
npm run dev
```

浏览器打开：

```text
http://localhost:5173/
```

说明：

- 前端使用 `React + TypeScript + Tailwind CSS`
- 后端使用 `Express + TypeScript`
- Web 控制台会通过本地后端调用 `qs_rank.py` 与 `lianjia.py`
- 可在页面中完成任务启动、日志查看、结果表格浏览与结果文件下载

## 功能说明

### 1. QS 排名抓取

目标站点：

```text
https://www.topuniversities.com/world-university-rankings/2026
```

实现内容：

- 自动访问 QS 页面
- 优先尝试 `requests + BeautifulSoup` 静态解析
- 若静态方式抓取结果不足，则自动切换 Selenium
- 抓取前 100 所大学
- 保存字段：
  - 学校名称
  - 排名
  - 分数
  - 城市
  - 国家
  - Logo URL
- 下载 Logo 到 `QSLogo/`
- 保存结果到 `Result/QSRank.txt`

### 2. 链家二手房抓取

目标站点：

```text
https://bj.lianjia.com/ershoufang/
```

实现内容：

- 程序自动翻页
- 抓取 100 条以上房源
- 抓取字段：
  - 小区名
  - 户型
  - 面积
  - 朝向
  - 楼层
  - 总价
  - 单价
- 尝试自动访问详情页抓取：
  - 经纪人姓名
  - 联系电话
- 支持“人工完成一次验证码后继续复用当前浏览器会话”的增强模式
- 支持“先打开首页，手动验证并登录，再开始自动抓取”的流程
- 支持保存并复用已登录 Cookie，会话文件保存在 `Result/`

说明：

- 链家详情页可能触发人机验证，因此代码已加入：
  - 随机请求头
  - 自动重试
  - 随机延时
  - Selenium 自动访问
  - 异常处理与日志记录
- 详情页增强版逻辑：
  - 启动浏览器并打开链家首页
  - 用户先在浏览器中手动完成人机验证和登录
  - 用户回到终端按回车后，程序开始自动抓取
  - 已登录 Cookie 会保存到 `Result/lianjia_session_edge.json` 或 `Result/lianjia_session_chrome.json`
  - 下次运行会优先尝试自动恢复登录态
- 若详情页被验证码拦截，程序会保留基础房源字段，并将经纪人字段置空后继续完成导出流程

链家脚本支持的可选参数：

```bash
python lianjia.py --target-count 120 --max-detail-pages 40
python lianjia.py --disable-manual-verify
```

参数说明：

- `--target-count`：目标抓取房源数，代码内部会保证不少于 100
- `--max-detail-pages`：最多尝试抓取多少个详情页来获取经纪人信息
- `--disable-manual-verify`：禁用“人工过验证码后复用会话”的增强模式

## 隐私保护说明

### 1. 姓名脱敏

由 `crypto_utils.py` 中的 `mask_name(name)` 实现。

规则：

- 保留第一个字符作为姓氏
- 其余字符全部替换为 `*`

示例：

```text
张三 -> 张*
欧阳娜娜 -> 欧***
```

### 2. AES 电话加密

由 `crypto_utils.py` 中的 `encrypt_phone(phone)` 实现。

加密方式：

- AES-256-CBC
- 随机 IV
- 最终输出 Base64 字符串

用于测试的解密函数：

```python
decrypt_phone(cipher_text_base64)
```

说明：

- 加密结果会把 `IV + 密文` 拼接后再做 Base64 编码
- 课程实验中为了便于直接运行，代码内置了演示密钥
- 实际生产环境应通过环境变量或密钥管理系统保存密钥

### 3. HMAC 完整性保护

由 `crypto_utils.py` 中的 `generate_hmac(data)` 实现。

算法：

- HMAC-SHA256

HMAC 原文字段拼接顺序为：

```text
小区名|户型|面积|朝向|楼层|总价|单价|脱敏姓名|电话密文
```

输出结果：

- 十六进制字符串

## 结果文件说明

### QS 结果

保存到：

```text
Result/QSRank.txt
```

内容包括：

- 学校名称
- 排名
- 分数
- 城市
- 国家
- Logo URL

### 链家结果

保存到：

```text
Result/Lianjia.xls
```

字段包括：

- 小区名
- 户型
- 面积
- 朝向
- 楼层
- 总价
- 单价
- 脱敏姓名
- 电话密文
- HMAC

补充说明：

- 程序内部使用 `pandas + openpyxl` 导出 Excel
- 由于 `openpyxl` 原生更适合写入 `.xlsx`，代码会先生成 `.xlsx` 内容，再同步输出为课程要求中的 `Lianjia.xls`
- 同时会额外导出两份结果：
  - `Result/Lianjia_Public.xls`：未登录即可获取的公开字段
  - `Result/Lianjia_Login.xls`：登录后增强字段结果

## 依赖说明

项目主要依赖：

- `requests`
- `beautifulsoup4`
- `lxml`
- `selenium`
- `pandas`
- `openpyxl`
- `pycryptodome`

## 注意事项

- 本项目仅用于课程实验与学习用途
- 目标网站可能随时调整页面结构或反爬策略
- 若 Selenium 无法启动，请先确认本机浏览器和对应驱动环境可用
- 若链家详情页出现验证码，属于目标网站的安全策略，代码已提供自动降级与异常处理逻辑
