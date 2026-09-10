import json
import re
import ssl
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# =========================================================
# 基本設定
# =========================================================

STOCKS = [
    {
        "code": "3501",
        "name": "維熹",
    }
]

NORWAY_URL = (
    "https://norway.twsthr.info/StockHolders.aspx"
)

GOODINFO_URL = (
    "https://goodinfo.tw/tw/StockBasicInfo.asp"
)

OUTPUT_FILE = "data/stocks.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

# GitHub Actions / Linux 的 SSL 環境
SSL_CONTEXT = ssl.create_default_context()


# =========================================================
# 網頁下載
# =========================================================

def fetch_html(url, referer=None):
    """
    下載網頁 HTML。

    會依序嘗試 UTF-8 / Big5 / CP950。
    """

    headers = dict(HEADERS)

    if referer:
        headers["Referer"] = referer

    request = Request(
        url,
        headers=headers,
        method="GET"
    )

    try:
        with urlopen(
            request,
            timeout=30,
            context=SSL_CONTEXT
        ) as response:

            data = response.read()

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            print("HTTP:", response.status)
            print("Content-Type:", content_type)
            print("Bytes:", len(data))

    except HTTPError as error:

        print(
            f"HTTP ERROR {error.code}: {error.reason}"
        )

        return None

    except URLError as error:

        print(
            "URL ERROR:",
            error.reason
        )

        return None

    except Exception as error:

        print(
            "FETCH ERROR:",
            type(error).__name__,
            str(error)
        )

        return None

    # 嘗試不同編碼
    for encoding in (
        "utf-8",
        "big5",
        "cp950"
    ):

        try:
            return data.decode(
                encoding
            )

        except UnicodeDecodeError:
            continue

    return data.decode(
        "utf-8",
        errors="ignore"
    )


# =========================================================
# HTML 清理
# =========================================================

def clean_html_text(html):
    """
    把 HTML 轉成比較容易閱讀的純文字。
    """

    if not html:
        return ""

    # 移除 script
    html = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        html,
        flags=re.I | re.S
    )

    # 移除 style
    html = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        html,
        flags=re.I | re.S
    )

    # 換行標籤
    html = re.sub(
        r"<br\s*/?>",
        "\n",
        html,
        flags=re.I
    )

    html = re.sub(
        r"</tr\s*>",
        "\n",
        html,
        flags=re.I
    )

    html = re.sub(
        r"</td\s*>",
        "\t",
        html,
        flags=re.I
    )

    html = re.sub(
        r"</th\s*>",
        "\t",
        html,
        flags=re.I
    )

    # 移除其他 HTML 標籤
    text = re.sub(
        r"<[^>]+>",
        " ",
        html
    )

    # HTML entities
    text = (
        text
        .replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )

    # 清理空白
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n",
        text
    )

    return text.strip()


# =========================================================
# 數字工具
# =========================================================

def parse_number(value):
    """
    將文字轉成數字。

    例如：
    4.52 -> 4.52
    12.5% -> 12.5
    1,234 -> 1234
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # 括號負數
    negative = False

    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1]

    # 移除千分位
    value = value.replace(",", "")

    # 移除百分比
    value = value.replace("%", "")

    # 移除常見貨幣符號
    value = value.replace("NT$", "")
    value = value.replace("元", "")

    # 找第一個數字
    match = re.search(
        r"-?\d+(?:\.\d+)?",
        value
    )

    if not match:
        return None

    number = float(
        match.group()
    )

    if negative:
        number = -number

    return number


# =========================================================
# 從文字尋找數值
# =========================================================

def find_value_by_labels(text, labels):
    """
    嘗試從網頁文字中尋找：

    EPS 4.52
    ROE 10.8%
    殖利率 5.2%

    由於不同網站版面可能變化，
    這裡只做初步解析。
    """

    if not text:
        return None

    for label in labels:

        pattern = (
            re.escape(label)
            + r"\s*[:：]?\s*"
            r"([\-]?\d+(?:,\d{3})*(?:\.\d+)?)"
            r"\s*%?"
        )

        match = re.search(
            pattern,
            text,
            flags=re.I
        )

        if match:

            return parse_number(
                match.group(1)
            )

    return None


# =========================================================
# Goodinfo
# =========================================================

def fetch_goodinfo(stock):
    """
    取得 Goodinfo 基本頁。

    注意：
    這一版先把網頁抓回來並做初步欄位解析。

    如果 Goodinfo 改版或防爬，
    後面可以再針對實際 HTML 結構調整。
    """

    code = stock["code"]

    url = (
        GOODINFO_URL
        + "?STOCK_ID="
        + code
    )

    print()
    print("=" * 70)
    print("GOODINFO")
    print(stock["code"], stock["name"])
    print(url)
    print("=" * 70)

    html = fetch_html(url)

    if not html:

        return {
            "success": False,
            "url": url,
            "error": "無法取得 Goodinfo 網頁"
        }

    print(
        "Goodinfo HTML 長度:",
        len(html)
    )

    text = clean_html_text(html)

    print(
        "Goodinfo 文字長度:",
        len(text)
    )

    # -----------------------------------------------------
    # 初步尋找欄位
    # -----------------------------------------------------

    price = find_value_by_labels(
        text,
        [
            "成交價",
            "收盤價",
            "股價",
        ]
    )

    eps = find_value_by_labels(
        text,
        [
            "EPS",
            "每股盈餘",
        ]
    )

    roe = find_value_by_labels(
        text,
        [
            "ROE",
            "股東權益報酬率",
        ]
    )

    dividend = find_value_by_labels(
        text,
        [
            "殖利率",
            "現金殖利率",
        ]
    )

    pe = find_value_by_labels(
        text,
        [
            "本益比",
            "PE",
        ]
    )

    # -----------------------------------------------------
    # 判斷是不是被擋
    # -----------------------------------------------------

    blocked_keywords = [
        "Access Denied",
        "403 Forbidden",
        "Too Many Requests",
        "驗證碼",
        "機器人",
        "blocked"
    ]

    blocked = any(
        keyword.lower()
        in html.lower()
        for keyword in blocked_keywords
    )

    return {
        "success": True,
        "url": url,
        "html_length": len(html),
        "text_length": len(text),
        "blocked": blocked,
        "raw_preview": text[:1000],

        "price": price,
        "eps": eps,
        "roe": roe,
        "dividend": dividend,
        "pe": pe,
    }


# =========================================================
# Norway
# =========================================================

def fetch_norway(stock):
    """
    取得 Norway 股權分散頁。

    目前先取得完整 HTML，
    再從文字中尋找可能的股東資料。

    後續可以依 Norway 實際表格欄位
    精確解析大戶級距。
    """

    code = stock["code"]

    url = (
        NORWAY_URL
        + "?STOCK="
        + code
    )

    print()
    print("=" * 70)
    print("NORWAY")
    print(stock["code"], stock["name"])
    print(url)
    print("=" * 70)

    html = fetch_html(url)

    if not html:

        return {
            "success": False,
            "url": url,
            "error": "無法取得 Norway 網頁"
        }

    print(
        "Norway HTML 長度:",
        len(html)
    )

    text = clean_html_text(html)

    print(
        "Norway 文字長度:",
        len(text)
    )

    blocked_keywords = [
        "Access Denied",
        "403 Forbidden",
        "Too Many Requests",
        "驗證碼",
        "機器人",
        "blocked"
    ]

    blocked = any(
        keyword.lower()
        in html.lower()
        for keyword in blocked_keywords
    )

    # -----------------------------------------------------
    # 嘗試尋找股東人數
    # -----------------------------------------------------

    shareholders = find_value_by_labels(
        text,
        [
            "股東人數",
            "股東總人數",
            "總股東人數",
        ]
    )

    return {
        "success": True,
        "url": url,
        "html_length": len(html),
        "text_length": len(text),
        "blocked": blocked,

        "shareholders": shareholders,

        # 暫時保留前段文字，
        # 方便 GitHub Actions 測試解析結果
        "raw_preview": text[:2000],
    }


# =========================================================
# 分析評分
# =========================================================

def calculate_fundamental_score(goodinfo):

    score = 50

    roe = goodinfo.get("roe")
    eps = goodinfo.get("eps")
    dividend = goodinfo.get("dividend")

    if roe is not None:

        if roe >= 15:
            score += 20

        elif roe >= 10:
            score += 12

        elif roe >= 5:
            score += 5

        elif roe < 0:
            score -= 20

    if eps is not None:

        if eps > 5:
            score += 15

        elif eps > 2:
            score += 8

        elif eps < 0:
            score -= 15

    if dividend is not None:

        if dividend >= 6:
            score += 15

        elif dividend >= 4:
            score += 10

        elif dividend >= 2:
            score += 5

    return max(
        0,
        min(100, score)
    )


def calculate_chip_score(norway):

    if not norway.get("success"):
        return 50

    if norway.get("blocked"):
        return 50

    # 現階段 Norway 尚未精確解析所有級距，
    # 因此先使用中性分數。
    return 50


def calculate_growth_score(goodinfo):

    # 第一版不亂猜成長性。
    # 等營收 / EPS 年增資料接上後再計算。
    return 50


def calculate_trend_score(stock):

    # 第一版先保持中性。
    # 後面加入價格、成交量、均線後再計算。
    return 50


# =========================================================
# 建立股票資料
# =========================================================

def process_stock(stock):

    print()
    print()
    print("#" * 70)
    print(
        "開始分析:",
        stock["code"],
        stock["name"]
    )
    print("#" * 70)

    goodinfo = fetch_goodinfo(stock)

    # 避免連續請求太快
    time.sleep(2)

    norway = fetch_norway(stock)

    fundamental_score = (
        calculate_fundamental_score(
            goodinfo
        )
    )

    chip_score = (
        calculate_chip_score(
            norway
        )
    )

    growth_score = (
        calculate_growth_score(
            goodinfo
        )
    )

    trend_score = (
        calculate_trend_score(
            stock
        )
    )

    overall_score = round(
        fundamental_score * 0.30
        + chip_score * 0.20
        + growth_score * 0.25
        + trend_score * 0.25
    )

    return {
        "code": stock["code"],
        "name": stock["name"],

        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "goodinfo": goodinfo,

        "norway": norway,

        "analysis": {
            "fundamental_score":
                fundamental_score,

            "chip_score":
                chip_score,

            "growth_score":
                growth_score,

            "trend_score":
                trend_score,

            "overall_score":
                overall_score
        }
    }


# =========================================================
# 主程式
# =========================================================

def main():

    print()
    print("=" * 70)
    print("台股資料抓取系統")
    print("Norway + Goodinfo")
    print("=" * 70)
    print()

    results = {}

    for stock in STOCKS:

        result = process_stock(
            stock
        )

        results[
            stock["code"]
        ] = result

    # 確保 data 資料夾存在
    import os

    os.makedirs(
        "data",
        exist_ok=True
    )

    output = {
        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "source": {
            "norway":
                "https://norway.twsthr.info/",
            "goodinfo":
                "https://goodinfo.tw/tw/"
        },

        "stocks": results
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 70)
    print("完成")
    print(
        "資料已寫入:",
        OUTPUT_FILE
    )
    print("=" * 70)

    print()
    print(
        "股票數量:",
        len(results)
    )

    for code, result in results.items():

        print()
        print(
            code,
            result["name"]
        )

        print(
            "Goodinfo:",
            "成功"
            if result["goodinfo"].get("success")
            else "失敗"
        )

        print(
            "Norway:",
            "成功"
            if result["norway"].get("success")
            else "失敗"
        )

        print(
            "綜合分數:",
            result["analysis"]["overall_score"]
        )


if __name__ == "__main__":
    main()
