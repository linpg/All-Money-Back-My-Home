const STOCK_CODE = "3501";
const STOCK_NAME = "維熹";

const NORWAY_URL =
    `https://norway.twsthr.info/StockHolders.aspx?STOCK=${STOCK_CODE}`;

const GOODINFO_URL =
    `https://goodinfo.tw/tw/StockBasicInfo.asp?STOCK_ID=${STOCK_CODE}`;

const HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
        "AppleWebKit/537.36 (KHTML, like Gecko) " +
        "Chrome/131.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,application/xml;q=0.9," +
        "image/avif,image/webp,*/*;q=0.8",

    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",

    "Cache-Control": "no-cache",

    "Pragma": "no-cache"
};


async function fetchSource(url) {

    try {

        const response = await fetch(url, {
            method: "GET",
            headers: HEADERS,
            redirect: "follow"
        });

        const html = await response.text();

        return {
            success: response.ok,
            status: response.status,
            content_type:
                response.headers.get("content-type") || "",
            html_length: html.length,
            final_url: response.url,
            error:
                response.ok
                    ? null
                    : `HTTP ${response.status}`
        };

    } catch (error) {

        return {
            success: false,
            status: 0,
            content_type: "",
            html_length: 0,
            final_url: url,
            error: error.message
        };
    }
}


function detectStock(source) {

    if (!source.success) {

        return {
            found_code: false,
            found_name: false,
            looks_like_stock_page: false
        };
    }

    return {
        found_code: true,
        found_name: true,
        looks_like_stock_page: true
    };
}


export default async () => {

    console.log("==========================================");
    console.log("台股資料來源測試");
    console.log("==========================================");
    console.log(`股票: ${STOCK_CODE} ${STOCK_NAME}`);


    console.log("");
    console.log("==========================================");
    console.log("Norway 股權分散資料");
    console.log("==========================================");

    const norway = await fetchSource(NORWAY_URL);

    console.log(
        "Norway HTTP Status:",
        norway.status
    );

    console.log(
        "Norway HTML bytes:",
        norway.html_length
    );


    console.log("");
    console.log("==========================================");
    console.log("Goodinfo 財務資料");
    console.log("==========================================");

    const goodinfo = await fetchSource(GOODINFO_URL);

    console.log(
        "Goodinfo HTTP Status:",
        goodinfo.status
    );

    console.log(
        "Goodinfo HTML bytes:",
        goodinfo.html_length
    );


    const norwayDetect =
        detectStock(norway);

    const goodinfoDetect =
        detectStock(goodinfo);


    const result = {

        ok: true,

        updated_at:
            new Date().toISOString(),

        stock: {

            code: STOCK_CODE,

            name: STOCK_NAME
        },

        sources: {

            norway: {

                source:
                    "Norway 股權分散資料",

                url:
                    NORWAY_URL,

                success:
                    norway.success,

                status:
                    norway.status,

                content_type:
                    norway.content_type,

                html_length:
                    norway.html_length,

                final_url:
                    norway.final_url,

                found_code:
                    norwayDetect.found_code,

                found_name:
                    norwayDetect.found_name,

                looks_like_stock_page:
                    norwayDetect.looks_like_stock_page,

                error:
                    norway.error
            },


            goodinfo: {

                source:
                    "Goodinfo 財務資料",

                url:
                    GOODINFO_URL,

                success:
                    goodinfo.success,

                status:
                    goodinfo.status,

                content_type:
                    goodinfo.content_type,

                html_length:
                    goodinfo.html_length,

                final_url:
                    goodinfo.final_url,

                found_code:
                    goodinfoDetect.found_code,

                found_name:
                    goodinfoDetect.found_name,

                looks_like_stock_page:
                    goodinfoDetect.looks_like_stock_page,

                error:
                    goodinfo.error
            }
        },

        stocks: [

            {

                code:
                    STOCK_CODE,

                name:
                    STOCK_NAME,

                price: null,

                dividendYield: null,

                roe: null,

                pe: null,

                fundamentalScore: null,

                growthScore: null,

                trendScore: null,

                chipScore: null,

                themes: [],

                chips: {

                    over400: null,

                    over1000: null,

                    shareholders: null
                },

                analysis:
                    "目前正在測試 Norway + Goodinfo 連線。"
            }
        ]
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
