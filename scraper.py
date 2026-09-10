import json
import re
from datetime import datetime
from urllib.request import Request, urlopen

STOCK_CODE = "3501"
STOCK_NAME = "維熹"

NORWAY_URL = (
    f"https://norway.twsthr.info/StockHolders.aspx"
    f"?STOCK={STOCK_CODE}"
)

GOODINFO_URL = (
    f"https://goodinfo.tw/tw/StockBasicInfo.asp"
    f"?STOCK_ID={STOCK_CODE}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}


def fetch_html(url):
    """下載網頁 HTML。"""
    request = Request(url, headers=HEADERS)

    with urlopen(request, timeout=20) as response:
        data = response.read()

    # 優先使用 UTF-8，失敗再嘗試 Big5
    for encoding in ("utf-8", "big5", "cp950"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    return data.decode("utf-8", errors="ignore")


def clean_text(text):
    """清理 HTML 文字。"""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def test_source(name, url):
    print("=" * 60)
    print(name)
    print(url)
    print("=" * 60)

    try:
        html = fetch_html(url)

        print("✓ 網頁取得成功")
        print("HTML 長度:", len(html))

        text = clean_text(html)

        print("文字長度:", len(text))
        print("前 500 字:")
        print(text[:500])

        return {
            "success": True,
            "url": url,
            "html_length": len(html)
        }

    except Exception as error:
        print("✗ 取得失敗")
        print(type(error).__name__, str(error))

        return {
            "success": False,
            "url": url,
            "error": str(error)
        }


def main():

    print()
    print("==========================================")
    print("台股資料抓取測試")
    print("股票:", STOCK_CODE, STOCK_NAME)
    print("==========================================")
    print()

    norway = test_source(
        "Norway 股權分散資料",
        NORWAY_URL
    )

    goodinfo = test_source(
        "Goodinfo 財務資料",
        GOODINFO_URL
    )

    result = {
        "updated_at": datetime.now().isoformat(),
        "stock": {
            "code": STOCK_CODE,
            "name": STOCK_NAME
        },
        "sources": {
            "norway": norway,
            "goodinfo": goodinfo
        }
    }

    with open(
        "test_result.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("==========================================")
    print("測試完成")
    print("結果已寫入 test_result.json")
    print("==========================================")


if __name__ == "__main__":
    main()
