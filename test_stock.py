import json
import os
import time
import requests
from datetime import datetime, timezone


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
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def test_source(name, url):

    print("=" * 70)
    print(name)
    print("=" * 70)
    print(url)

    result = {
        "source": name,
        "url": url,
        "success": False,
        "status": None,
        "content_type": "",
        "html_length": 0,
        "error": None,
    }

    try:

        session = requests.Session()

        session.headers.update(HEADERS)

        response = session.get(
            url,
            timeout=30,
            allow_redirects=True
        )

        text = response.text

        result["status"] = response.status_code
        result["content_type"] = response.headers.get(
            "Content-Type",
            ""
        )
        result["html_length"] = len(text)

        result["success"] = response.ok

        if response.ok:

            result["preview"] = (
                text
                .replace("\n", " ")
                .replace("\r", " ")
                [:500]
            )

            print("🟢 HTTP:", response.status_code)
            print("HTML:", len(text), "bytes")

        else:

            result["error"] = (
                f"HTTP {response.status_code}"
            )

            print(
                "🔴 HTTP:",
                response.status_code
            )

    except Exception as error:

        result["error"] = str(error)

        print("🔴 ERROR:", error)

    return result


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

    print()

    norway = test_source(
        "Norway 股權分散資料",
        NORWAY_URL
    )

    time.sleep(3)

    goodinfo = test_source(
        "Goodinfo 財務資料",
        GOODINFO_URL
    )

    result = {
        "ok": True,

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "stock": {
            "code": STOCK_CODE,
            "name": STOCK_NAME
        },

        "sources": {
            "norway": norway,
            "goodinfo": goodinfo
        }
    }

    os.makedirs(
        "data",
        exist_ok=True
    )

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

    print()
    print("=" * 70)
    print("測試完成")
    print("=" * 70)

    print(
        "結果檔案:",
        output_file
    )

    print(
        "Norway:",
        norway["status"]
    )

    print(
        "Goodinfo:",
        goodinfo["status"]
    )


if __name__ == "__main__":
    main()
