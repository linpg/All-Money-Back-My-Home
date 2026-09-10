
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
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}


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

        # 嘗試解碼
        html = None
        encoding_used = None

        for encoding in [
            "utf-8",
            "cp950",
            "big5",
            "big5hkscs"
        ]:

            try:

                html = data.decode(encoding)
                encoding_used = encoding
                break

            except UnicodeDecodeError:
                pass

        if html is None:

            html = data.decode(
                "utf-8",
                errors="ignore"
            )

            encoding_used = "utf-8-ignore"

        return {
            "success": True,
            "status": status,
            "content_type": content_type,
            "final_url": final_url,
            "encoding": encoding_used,
            "html": html,
            "bytes": len(data)
        }

    except HTTPError as error:

        return {
            "success": False,
            "status": error.code,
            "error_type": "HTTPError",
            "error": str(error),
            "html": ""
        }

    except URLError as error:

        return {
            "success": False,
            "status": 0,
            "error_type": "URLError",
            "error": str(error),
            "html": ""
        }

    except Exception as error:

        return {
            "success": False,
            "status": 0,
            "error_type": type(error).__name__,
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
# 判斷是否為股票頁面
# =========================================================

def detect_stock_content(html):

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
        "本益比"
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
        "text_length": len(text),
        "preview": text[:500]
    }


# =========================================================
# 測試資料來源
# =========================================================

def test_source(name, url):

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    print("URL:", url)

    response = fetch_html(url)

    result = {
        "source": name,
        "url": url,
        "success": False,
        "status": response.get("status"),
        "content_type": response.get("content_type", ""),
        "encoding": response.get("encoding", ""),
        "html_length": 0,
        "text_length": 0,
        "found_code": False,
        "found_name": False,
        "looks_like_stock_page": False,
        "keyword_count": 0,
        "preview": "",
        "error": None
    }

    if not response["success"]:

        print("❌ 網頁取得失敗")
        print("錯誤類型:", response.get("error_type"))
        print("錯誤:", response.get("error"))

        result["error"] = response.get("error")
        result["error_type"] = response.get("error_type")

        return result

    html = response["html"]

    detection = detect_stock_content(html)

    result.update({
        "success": True,
        "html_length": len(html),
        "text_length": detection["text_length"],
        "found_code": detection["found_code"],
        "found_name": detection["found_name"],
        "looks_like_stock_page":
            detection["looks_like_stock_page"],
        "keyword_count":
            detection["keyword_count"],
        "preview":
            detection["preview"]
    })

    print("HTTP Status:", response.get("status"))
    print("Encoding:", response.get("encoding"))
    print("HTML length:", len(html))
    print("文字長度:", detection["text_length"])

    print(
        "找到股票代號:",
        "🟢 是" if detection["found_code"] else "🔴 否"
    )

    print(
        "找到股票名稱:",
        "🟢 是" if detection["found_name"] else "🔴 否"
    )

    print(
        "疑似股票頁面:",
        "🟢 是"
        if detection["looks_like_stock_page"]
        else "🔴 否"
    )

    print()
    print("前 500 字:")
    print(detection["preview"])

    return result


# =========================================================
# 主程式
# =========================================================

def main():

    print("=" * 60)
    print("台股資料來源測試")
    print("=" * 60)

    print(
        "股票:",
        STOCK_CODE,
        STOCK_NAME
    )

    print(
        "時間:",
        datetime.now(timezone.utc).isoformat()
    )

    # -----------------------------------------------------
    # 最重要：
    # 先建立 data 資料夾
    # -----------------------------------------------------

    os.makedirs(
        "data",
        exist_ok=True
    )

    output_file = "data/test_result.json"

    # -----------------------------------------------------
    # 先建立一個初始結果
    # 即使程式中途出問題，也有檔案可以查看
    # -----------------------------------------------------

    initial_result = {
        "ok": False,
        "updated_at":
            datetime.now(timezone.utc).isoformat(),
        "stock": {
            "code": STOCK_CODE,
            "name": STOCK_NAME
        },
        "sources": {},
        "message": "測試開始"
    }

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            initial_result,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("✓ 已建立初始結果檔:")
    print(output_file)

    # -----------------------------------------------------
    # Norway
    # -----------------------------------------------------

    norway = test_source(
        "Norway 股權分散資料",
        NORWAY_URL
    )

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

    norway_ok = (
        norway.get("success")
        and norway.get("looks_like_stock_page")
    )

    goodinfo_ok = (
        goodinfo.get("success")
        and goodinfo.get("looks_like_stock_page")
    )

    result = {

        "ok": True,

        "updated_at":
            datetime.now(timezone.utc).isoformat(),

        "stock": {
            "code": STOCK_CODE,
            "name": STOCK_NAME
        },

        "sources": {

            "norway": norway,

            "goodinfo": goodinfo

        },

        "summary": {

            "norway_ok": norway_ok,

            "goodinfo_ok": goodinfo_ok,

            "all_sources_ok":
                norway_ok and goodinfo_ok

        }

    }

    # -----------------------------------------------------
    # 寫入結果
    # -----------------------------------------------------

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

    print()
    print("=" * 60)
    print("測試完成")
    print("=" * 60)

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
    print("✓ 結果檔案:")
    print(output_file)

    print()
    print("✓ 不論資料來源成功或失敗，test_result.json 都會存在。")


# =========================================================
# 執行
# =========================================================

if __name__ == "__main__":
    main()
