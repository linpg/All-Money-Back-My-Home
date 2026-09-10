export default async () => {

    const stock = {
        code: "3501",
        name: "維熹",

        // 先放測試資料
        // 等確認 Netlify 連線成功後，再接 Norway / Goodinfo
        price: null,
        dividendYield: null,
        roe: null,
        pe: null,

        fundamentalScore: null,
        growthScore: null,
        trendScore: null,
        chipScore: null,

        themes: ["測試"],

        chips: {
            over400: null,
            over1000: null,
            shareholders: null
        },

        analysis: "Netlify Function 已正常運作，等待接入即時資料。"
    };

    const result = {
        ok: true,

        updated_at: new Date().toISOString(),

        stocks: [stock]
    };

    return new Response(
        JSON.stringify(result, null, 2),
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
