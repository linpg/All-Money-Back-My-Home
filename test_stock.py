import json
import os
import re
import time
from datetime import datetime, timezone

import requests


# =========================================================
# 股票
# =========================================================

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


# =========================================================
# 不同瀏覽器 Header
# =========================================================

HEADER_SETS = [

    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,"
            "*/*;q=0.8"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    },

    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.6 Safari/605.1.15"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    },

    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    },

]


# =========================================================
# HTML 清理
# =========================================================

def clean_text(html):

    if not html:
        return ""

    html = re.sub(
        r"<script.*?</script>",
        " ",
        html,
        flags=re.I | re.S
    )

    html = re.sub(
        r"<style.*?</style>",
        " ",
        html,
        flags=re.I | re.S
    )

    html = re.sub(
        r"<[^>]+>",
        " ",
        html
    )

    html = html.replace("&nbsp;", " ")
    html = html.replace("&amp;", "&")
    html = html.replace("&gt;", ">")
    html = html.replace("&lt;", "<")
    html = html.replace("&#39;", "'")
    html = html.replace("&quot;", '"')

    html = re.sub(
        r"\s+",
        " ",
        html
    )

    return html.strip()


# =========================================================
# 判斷是不是股票頁面
# =========================================================

def detect_stock_content(html):

    if not html:
        return {
            "found_code": False,
            "found_name": False,
            "keyword_count": 0,
            "looks_like_stock_page": False,
            "text_length": 0
        }

    text = clean_text(html)

    found_code = STOCK_CODE in text
    found_name = STOCK_NAME in text

    keywords = [
        "股東",
        "持股",
        "財務",
        "營收",
        "EPS",
        "ROE",
        "殖利率",
        "本益比",
        "股利",
        "股權"
    ]

    keyword_count = sum(
        1 for keyword in keywords
        if keyword in text
    )

    looks_like_stock_page = (
        found_code
        or found_name
        or keyword_count >= 2
    )

    return {
        "found_code": found_code,
        "found_name": found_name,
        "keyword_count": keyword_count,
        "looks_like_stock_page": looks_like_stock_page,
        "text_length": len(text)
    }


# =========================================================
# 嘗試取得網站
# =========================================================

def fetch_source(source_name, url):

    print()
    print("=" * 70)
    print(source_name)
    print("=" * 70)

    print("URL:")
    print(url)

    attempts = []

    for index, headers in enumerate(HEADER_SETS, start=1):

        print()
        print(f"第 {index} 次連線")

        try:

            session = requests.Session()

            response = session.get(
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )

            print(
                "HTTP Status:",
                response.status_code
            )

            print(
                "Content-Type:",
                response.headers.get(
                    "content-type",
                    ""
                )
            )

            print(
                "HTML bytes:",
                len(response.content)
            )

            html = response.text

            detection = detect_stock_content(html)

            attempt = {
                "attempt": index,
                "status": response.status_code,
                "content_type":
                    response.headers.get(
                        "content-type",
                        ""
                    ),
                "html_length": len(html),
                "found_code":
                    detection["found_code"],
                "found_name":
                    detection["found_name"],
                "looks_like_stock_page":
                    detection["looks_like_stock_page"]
            }

            attempts.append(attempt)

            if response.ok:

                print("HTTP：🟢 成功")

                if detection["looks_like_stock_page"]:

                    print("股票頁面：🟢 找到")

                    text = clean_text(html)

                    print()
                    print("前 500 字：")
                    print(text[:500])

                    return {
                        "source": source_name,
                        "url": url,
                        "success": True,
                        "status": response.status_code,
                        "content_type":
                            response.headers.get(
                                "content-type",
                                ""
                            ),
                        "html_length": len(html),
                        "text_length": len(text),
                        "found_code":
                            detection["found_code"],
                        "found_name":
                            detection["found_name"],
                        "looks_like_stock_page":
                            detection["looks_like_stock_page"],
                        "attempts": attempts,
                        "error": None
                    }

                print("HTTP 成功，但不是預期股票頁面")

            else:

                print(
                    "HTTP：🔴",
                    response.status_code
                )

                if response.status_code == 403:

                    print(
                        "網站拒絕 GitHub Actions 請求"
                    )

        except requests.RequestException as error:

            print(
                "連線錯誤:",
                str(error)
            )

            attempts.append({
                "attempt": index,
                "status": 0,
                "error": str(error)
            })

        except Exception as error:

            print(
                "未知錯誤:",
                str(error)
            )

            attempts.append({
                "attempt": index,
                "status": 0,
                "error": str(error)
            })

        time.sleep(3)


    print()
    print("❌ 所有連線方式都沒有取得有效股票頁面")

    return {
        "source": source_name,
        "url": url,
        "success": False,
        "status":
            attempts[-1].get("status")
            if attempts
            else 0,
        "content_type": "",
        "html_length":
            attempts[-1].get("html_length", 0)
            if attempts
            else 0,
        "text_length": 0,
        "found_code": False,
        "found_name": False,
        "looks_like_stock_page": False,
        "attempts": attempts,
        "error": "所有連線方式均未取得有效股票頁面"
    }


# =========================================================
# 主程式
# =========================================================

def main():

    print()
    print("=" * 70)
    print("台股資料來源測試")
    print("=" * 70)

    print(
        "股票:",
        STOCK_CODE,
        STOCK_NAME
    )

    print(
        "時間:",
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    print("=" * 70)


    # =====================================================
    # Norway
    # =====================================================

    norway = fetch_source(
        "Norway 股權分散資料",
        NORWAY_URL
    )


    time.sleep(3)


    # =====================================================
    # Goodinfo
    # =====================================================

    goodinfo = fetch_source(
        "Goodinfo 財務資料",
        GOODINFO_URL
    )


    # =====================================================
    # 輸出 JSON
    # =====================================================

    result = {

        "ok": True,

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "stock": {

            "code":
                STOCK_CODE,

            "name":
                STOCK_NAME

        },

        "sources": {

            "norway":
                norway,

            "goodinfo":
                goodinfo

        }

    }


    os.makedirs(
        "data",
        exist_ok=True
    )


    output_file = (
        "data/test_result.json"
    )


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )


    # =====================================================
    # 最終結果
    # =====================================================

    print()
    print("=" * 70)
    print("最終測試結果")
    print("=" * 70)

    print(
        "Norway:",
        "🟢 OK"
        if norway["success"]
        else "🔴 FAIL"
    )

    print(
        "Goodinfo:",
        "🟢 OK"
        if goodinfo["success"]
        else "🔴 FAIL"
    )

    print()
    print(
        "結果檔案:",
        output_file
    )

    print()
    print("=" * 70)
    print("測試完成")
    print("=" * 70)

    # 不讓 GitHub Actions 因為 403 直接中止
    # 讓 test_result.json 一定可以保存


if __name__ == "__main__":
    main()
