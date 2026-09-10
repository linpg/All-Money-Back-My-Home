import json
import re
import ssl
import time
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# =========================================================
# 基本設定
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
# Request Headers
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


# =========================================================
# SSL
# =========================================================

SSL_CONTEXT = ssl.create_default_context()


# =========================================================
# 下載網頁
# =========================================================

def fetch_html(url):

    request = Request(
        url,
        headers=HEADERS,
        method="GET"
    )

    try:

        with urlopen(
            request,
            timeout=30,
            context=SSL_CONTEXT
        ) as response:

            data = response.read()

            status = response.status

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            final_url = response.geturl()


        # 嘗試不同編碼
        html = None
        used_encoding = None

        for encoding in (
            "utf-8",
            "cp950",
            "big5",
            "big5hkscs"
        ):

            try:

                html = data.decode(encoding)

                used_encoding = encoding

                break

            except UnicodeDecodeError:

                pass


        if html is None:

            html = data.decode(
                "utf-8",
                errors="ignore"
            )

            used_encoding = "utf-8-ignore"


        return {
            "success": True,
            "status": status,
            "content_type": content_type,
            "final_url": final_url,
            "encoding": used_encoding,
            "html": html,
            "bytes": len(data)
        }


    except HTTPError as error:

        return {
            "success": False,
            "error_type": "HTTPError",
            "status": error.code,
            "error": str(error),
            "html": ""
        }


    except URLError as error:

        return {
            "success": False,
            "error_type": "URLError",
            "status": 0,
            "error": str(error),
            "html": ""
        }


    except Exception as error:

        return {
            "success": False,
            "error_type": type(error).__name__,
            "status": 0,
            "error": str(error),
            "html": ""
        }


# =========================================================
# 清理 HTML
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

    html = re.sub(
        r"\s+",
        " ",
        html
    )

    return html.strip()


# =========================================================
# 判斷是否真的取得股票資料
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
        "股利"
    ]


    keyword_count = 0

    for keyword in keywords:

        if keyword in text:

            keyword_count += 1


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
# 測試來源
# =========================================================

def test_source(source_name, url):

    print()
    print("=" * 70)
    print(source_name)
    print("=" * 70)

    print("URL:")
    print(url)


    result = {
        "source": source_name,
        "url": url,
        "success": False,
        "status": None,
        "content_type": "",
        "encoding": "",
        "html_length": 0,
        "text_length": 0,
        "found_code": False,
        "found_name": False,
        "looks_like_stock_page": False,
        "keyword_count": 0,
        "error": None
    }


    response = fetch_html(url)


    if not response["success"]:

        print()
        print("❌ 網頁取得失敗")

        print(
            "錯誤類型:",
            response.get("error_type")
        )

        print(
            "錯誤:",
            response.get("error")
        )


        result["error"] = response.get("error")

        result["error_type"] = response.get(
            "error_type"
        )

        result["status"] = response.get(
            "status"
        )

        return result


    html = response["html"]


    print()
    print("HTTP Status:")
    print(response["status"])

    print(
        "Content-Type:",
        response["content_type"]
    )

    print(
        "Encoding:",
        response["encoding"]
    )

    print(
        "HTML bytes:",
        response["bytes"]
    )

    print(
        "HTML length:",
        len(html)
    )


    detection = detect_stock_content(html)


    print()
    print(
        "找到股票代號:",
        "🟢 是"
        if detection["found_code"]
        else "🔴 否"
    )

    print(
        "找到股票名稱:",
        "🟢 是"
        if detection["found_name"]
        else "🔴 否"
    )

    print(
        "疑似股票頁面:",
        "🟢 是"
        if detection["looks_like_stock_page"]
        else "🔴 否"
    )

    print(
        "關鍵字數量:",
        detection["keyword_count"]
    )


    text = clean_text(html)


    print()
    print("文字長度:")
    print(len(text))


    print()
    print("前 500 字:")
    print(text[:500])


    result.update({

        "success": True,

        "status":
            response["status"],

        "content_type":
            response["content_type"],

        "encoding":
            response["encoding"],

        "html_length":
            len(html),

        "text_length":
            len(text),

        "found_code":
            detection["found_code"],

        "found_name":
            detection["found_name"],

        "looks_like_stock_page":
            detection["looks_like_stock_page"],

        "keyword_count":
            detection["keyword_count"]

    })


    return result


# =========================================================
# 主程式
# =========================================================

def main():

    print()
    print("=" * 70)
    print("台股資料抓取測試")
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


    # -----------------------------------------------------
    # Norway
    # -----------------------------------------------------

    norway = test_source(
        "Norway 股權分散資料",
        NORWAY_URL
    )


    # -----------------------------------------------------
    # 等待 2 秒
    # -----------------------------------------------------

    time.sleep(2)


    # -----------------------------------------------------
    # Goodinfo
    # -----------------------------------------------------

    goodinfo = test_source(
        "Goodinfo 財務資料",
        GOODINFO_URL
    )


    # -----------------------------------------------------
    # 最終結果
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 建立 data 資料夾
    # -----------------------------------------------------

    os.makedirs(
        "data",
        exist_ok=True
    )


    # -----------------------------------------------------
    # 寫入測試結果
    # -----------------------------------------------------

    output_file = "data/test_result.json"


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


    # -----------------------------------------------------
    # 最終判斷
    # -----------------------------------------------------

    norway_ok = (
        norway.get("success")
        and norway.get(
            "looks_like_stock_page"
        )
    )


    goodinfo_ok = (
        goodinfo.get("success")
        and goodinfo.get(
            "looks_like_stock_page"
        )
    )


    print()
    print("=" * 70)
    print("測試結果")
    print("=" * 70)


    print(
        "Norway:",
        "🟢 OK"
        if norway_ok
        else "🔴 FAIL"
    )


    print(
        "Goodinfo:",
        "🟢 OK"
        if goodinfo_ok
        else "🔴 FAIL"
    )


    print()
    print(
        "結果檔案:",
        output_file
    )


    print()
    print("=" * 70)
    print("test_stock.py 執行完成")
    print("=" * 70)


    # 這裡故意不 exit 1
    # 即使來源網站擋住，也要讓 test_result.json 被保存

    if not norway_ok or not goodinfo_ok:

        print()
        print(
            "⚠️ 至少一個資料來源沒有通過測試。"
        )

        print(
            "但是 test_result.json 已經建立。"
        )

        return


    print()
    print(
        "🟢 Norway + Goodinfo 測試通過"
    )


# =========================================================
# 執行
# =========================================================

if __name__ == "__main__":

    main()
