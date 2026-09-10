
export default async (request) => {

    const STOCK_CODE = "3501";

    const NORWAY_URL =
        `https://norway.twsthr.info/StockHolders.aspx?STOCK=${STOCK_CODE}`;

    const GOODINFO_URL =
        `https://goodinfo.tw/tw/StockBasicInfo.asp?STOCK_ID=${STOCK_CODE}`;


    const headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
            "AppleWebKit/537.36 (KHTML, like Gecko) " +
            "Chrome/131.0.0.0 Safari/537.36",

        "Accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

        "Accept-Language":
            "zh-TW,zh;q=0.9,en;q=0.8",

        "Cache-Control":
            "no-cache"
    };


    async function testSource(name, url) {

        try {

            const response = await fetch(url, {
                method: "GET",
                headers: headers,
                redirect: "follow"
            });


            const text = await response.text();


            return {

                source: name,

                success: response.ok,

                status: response.status,

                content_type:
                    response.headers.get("content-type") || "",

                length: text.length,

                preview:
                    text
                        .replace(/<[^>]+>/g, " ")
                        .replace(/\s+/g, " ")
                        .trim()
                        .slice(0, 500)

            };


        } catch (error) {

            return {

                source: name,

                success: false,

                status: 0,

                error: error.message

            };

        }

    }


    const norway = await testSource(
        "Norway 股權分散",
        NORWAY_URL
    );


    const goodinfo = await testSource(
        "Goodinfo 財務資料",
        GOODINFO_URL
    );


    const result = {

        ok: true,

        updated_at:
            new Date().toISOString(),

        stock: {

            code: STOCK_CODE,

            name: "維熹"

        },

        norway: norway,

        goodinfo: goodinfo

    };


    return new Response(

        JSON.stringify(
            result,
            null,
            2
        ),

        {

            status: 200,

            headers: {

                "Content-Type":
                    "application/json; charset=UTF-8",

                "Access-Control-Allow-Origin":
                    "*",

                "Cache-Control":
                    "no-store"

            }

        }

    );

};
