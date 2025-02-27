const ccxt = require('ccxt');
const { MACD, RSI } = require('technicalindicators');

const CHAt_ID = process.env.CHAt_ID

module.exports = (bot) => {
    bot.command('run', async (ctx) => {
        // Настройки
        //const symbol = 'BTC/USDT'; // Торговая пара
        //const symbols = ['BTC/USDT', 'APE/USDT', 'PEPE/USDT', 'XRP/USDT', 'SOL/USDT', 'TRX/USDT'];


        const symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'EOS/USDT', 'ETH/BTC', 'XRP/BTC',
            'DOT/USDT', 'XLM/USDT', 'LTC/USDT', 'DOGE/USDT', 'CHZ/USDT', 'AXS/USDT',
            'MANA/USDT', 'DYDX/USDT', 'MKR/USDT', 'COMP/USDT', 'AAVE/USDT', 'YFI/USDT', 'LINK/USDT',
            'SUSHI/USDT', 'UNI/USDT', 'KSM/USDT', 'ICP/USDT', 'ADA/USDT', 'ETC/USDT', 'XTZ/USDT', 'BCH/USDT', 'QNT/USDT',
            'USDC/USDT', 'GRT/USDT', 'SOL/USDT', 'FIL/USDT', 'OMG/USDT', 'BAT/USDT', 'ZRX/USDT', 'CRV/USDT', 'AGLD/USDT',
            'ANKR/USDT', 'PERP/USDT', 'WAVES/USDT', 'LUNC/USDT', 'SPELL/USDT', 'SHIB/USDT', 'ATOM/USDT', 'ALGO/USDT',
            'ENJ/USDT', 'SAND/USDT', 'AVAX/USDT', 'WOO/USDT', 'FTT/USDT', 'GODS/USDT', 'IMX/USDT', 'ENS/USDT', 'CAKE/USDT', 'STETH/USDT',
            'GALFT/USDT', 'SLP/USDT', 'C98/USDT', 'GENE/USDT', 'AVA/USDT', 'ONE/USDT', 'PTU/USDT', 'XYM/USDT', 'BOBA/USDT', 'JASMY/USDT',
            'GALA/USDT', 'TRVL/USDT', 'WEMIX/USDT', 'XEM/USDT', 'BICO/USDT', 'CEL/USDT', 'UMA/USDT', 'HOT/USDT', 'NEXO/USDT', 'BNT/USDT',
            'SNX/USDT', 'REN/USDT', '1INCH/USDT', 'TEL/USDT', 'SIS/USDT', 'LRC/USDT', 'LDO/USDT', 'REAL/USDT', 'ETH/USDC', 'BTC/USDC',
            '1SOL/USDT', 'PLT/USDT', 'IZI/USDT', 'QTUM/USDT', 'ZEN/USDT', 'THETA/USDT', 'MX/USDT', 'DGB/USDT', 'RVN/USDT', 'EGLD/USDT', 'RUNE/USDT',
            'XLM/USDC', 'SOL/USDC', 'XRP/USDC', 'ALGO/BTC', 'SOL/BTC', 'RAIN/USDT', 'XEC/USDT', 'ICX/USDT', 'XDC/USDT', 'HNT/USDT',
            'ZIL/USDT', 'HBAR/USDT', 'FLOW/USDT', 'KASTA/USDT', 'STX/USDT', 'SIDUS/USDT', 'VPAD/USDT', 'LOOKS/USDT', 'MBS/USDT', 'DAI/USDT',
            'ACA/USDT',
            'MV/USDT',
            'MIX/USDT',
            'LTC/USDC',
            'LTC/BTC',
            'DOT/BTC',
            'SAND/BTC', 'MANA/USDC',
            'SAND/USDC',
            'DOT/USDC',
            'LUNC/USDC',
            'RSS3/USDT',
            'TAP/USDT',
            'ERTHA/USDT',
            'GMX/USDT',
            'T/USDT',
            'ACH/USDT',
            'JST/USDT',
            'SUN/USDT',
            'BTT/USDT',
            'TRX/USDT',
            'NFT/USDT',
            'POKT/USDT',
            'SCRT/USDT',
            'PSTAKE/USDT',
            'SON/USDT',
            'DOME/USDT',
            'USTC/USDT',
            'BNB/USDT',
            'NEAR/USDT',
            'PAXG/USDT',
            'SD/USDT',
            'APE/USDT',
            'BTC3S/USDT',
            'BTC3L/USDT',
            'FIDA/USDT',
            'MINA/USDT',
            'SC/USDT',
            'CAPS/USDT',
            'STG/USDT',
            'GLMR/USDT',
            'MOVR/USDT',
            'ETH/DAI',
            'BTC/DAI',
            'WBTC/USDT',
            'XAVA/USDT',
            'GMT/USDT',
            'GST/USDT',
            'CELO/USDT',
            'SFUND/USDT',
            'LGX/USDT',
            'APEX/USDT',
            'CTC/USDT',
            'COT/USDT',
            'KMON/USDT',
            'FITFI/USDT',
            'ETH3S/USDT',
            'ETH3L/USDT',
            'FAME/USDT',
            'USDD/USDT',
            'OP/USDT',
            'LUNA/USDT',
            'THN/USDT',
            'VINU/USDT',
            'BEL/USDT',
            'FORT/USDT',
            'WLKN/USDT',
            'KON/USDT',
            'OBX/USDT',
            'SEOR/USDT',
            'DOGE/USDC',
            'EOS/USDC',
            'CUSD/USDT',
            'GSTS/USDT',
            'XETA/USDT',
            'FLOKI/USDT',
            'BABYDOGE/USDT',
            'STAT/USDT',
            'DICE/USDT',
            'WAXP/USDT',
            'AR/USDT',
            'KDA/USDT',
            'ROSE/USDT',
            'PSG/USDT',
            'JUV/USDT',
            'INTER/USDT',
            'AFC/USDT',
            'CITY/USDT',
            'SOLO/USDT',
            'WBTC/BTC',
            'AVAX/USDC',
            'ADA/USDC',
            'OP/USDC',
            'APEX/USDC',
            'TRX/USDC',
            'ICP/USDC',
            'LINK/USDC',
            'GMT/USDC',
            'CHZ/USDC',
            'SHIB/USDC',
            'LDO/USDC',
            'APE/USDC',
            'FIL/USDC',
            'CHRP/USDT',
            'WWY/USDT',
            'SWEAT/USDT',
            'DLC/USDT',
            'ETHW/USDT',
            'INJ/USDT',
            'MPLX/USDT',
            'AGLA/USDT',
            'ROND/USDT',
            'PUMLX/USDT',
            'APT/USDT',
            'APT/USDC',
            'USDT/EUR',
            'MCRT/USDT',
            'MASK/USDT',
            'ECOX/USDT',
            'HFT/USDC',
            'HFT/USDT',
            'KCAL/USDT',
            'PEOPLE/USDT',
            'TWT/USDT',
            'ORT/USDT',
            'HOOK/USDT',
            'OAS/USDT',
            'MAGIC/USDT',
            'MEE/USDT',
            'TON/USDT',
            'BONK/USDT',
            'FLR/USDT',
            'TIME/USDT',
            '3P/USDT',
            'RPL/USDT',
            'SSV/USDT',
            'FXS/USDT',
            'CORE/USDT',
            'RDNT/USDT',
            'BLUR/USDT',
            'LIS/USDT',
            'MDAO/USDT',
            'ACS/USDT',
            'HVH/USDT',
            'PIP/USDT',
            'PRIME/USDT',
            'EVER/USDT',
            'VRA/USDT',
            'ID/USDT',
            'ARB/USDC',
            'ARB/USDT',
            'XCAD/USDT',
            'MBX/USDT',
            'AXL/USDT',
            'CGPT/USDT',
            'AGI/USDT',
            'SUI/USDT',
            'SUI/USDC',
            'MVL/USDT',
            'PEPE/USDT',
            'LADYS/USDT',
            'LMWR/USDT',
            'BOB/USDT',
            'TOMI/USDT',
            'KARATE/USDT',
            'TURBOS/USDT',
            'FMB/USDT',
            'TENET/USDT',
            'VELO/USDT',
            'ELDA/USDT',
            'USDT/BRZ',
            'BTC/BRZ',
            'PENDLE/USDT',
            'EGO/USDT',
            'NYM/USDT',
            'MNT/USDT',
            'MNT/USDC',
            'MNT/BTC',
            'GSWIFT/USDT',
            'SALD/USDT',
            'ARKM/USDT',
            'NEON/USDT',
            'WLD/USDC',
            'WLD/USDT',
            'PLANET/USDT',
            'DSRUN/USDT',
            'SPARTA/USDT',
            'TAVA/USDT',
            'SEILOR/USDT',
            'SEI/USDT',
            'CYBER/USDT',
            'ORDI/USDT',
            'KAVA/USDT',
            'SAIL/USDT',
            'PYUSD/USDT',
            'SOL/EUR',
            'USDC/EUR',
            'ADA/EUR',
            'DOGE/EUR',
            'LTC/EUR',
            'XRP/EUR',
            'ETH/EUR',
            'BTC/EUR',
            'VEXT/USDT',
            'CTT/USDT',
            'KAS/USDT',
            'NESS/USDT',
            'FET/USDT',
            'LEVER/USDT',
            'ZTX/USDT',
            'JEFF/USDT',
            'PPT/USDT',
            'TUSD/USDT',
            'BEAM/USDT',
            'POL/USDT',
            'TIA/USDT',
            'TOKEN/USDT',
            'MEME/USDT',
            'SHRAP/USDT',
            'RPK/USDT',
            'FLIP/USDT',
            'VRTX/USDT',
            'ROOT/USDT',
            'PYTH/USDT',
            'MLK/USDT',
            'KUB/USDT',
            '5IRE/USDT',
            'KCS/USDT',
            'VANRY/USDT',
            'INSP/USDT',
            'JTO/USDT',
            'METH/USDT',
            'METH/ETH',
            'CBK/USDT',
            'ZIG/USDT',
            'VPR/USDT',
            'TRC/USDT',
            'SEI/USDC',
            'FMC/USDT',
            'MYRIA/USDT',
            'AKI/USDT',
            'MBOX/USDT',
            'IRL/USDT',
            'ARTY/USDT',
            'GRAPE/USDT',
            'COQ/USDT',
            'AIOZ/USDT',
            'GG/USDT',
            'VIC/USDT',
            'RATS/USDT',
            'SATS/USDT',
            'ZKF/USDT',
            'PORT3/USDT',
            'XAI/USDT',
            'ONDO/USDT',
            'FAR/USDT',
            'SQR/USDT',
            'DUEL/USDT',
            'APP/USDT',
            'SAROS/USDT',
            'USDY/USDT',
            'MANTA/USDT',
            'MYRO/USDT',
            'GTAI/USDT',
            'DMAIL/USDT',
            'AFG/USDT',
            'DYM/USDT',
            'ZETA/USDT',
            'JUP/USDT',
            'MXM/USDT',
            'DEFI/USDT',
            'FIRE/USDT',
            'MAVIA/USDT',
            'PURSE/USDT',
            'BCUT/USDT',
            'ALT/USDT',
            'HTX/USDT',
            'CSPR/USDT',
            'STRK/USDC',
            'STRK/USDT',
            'CPOOL/USDT',
            'QORPO/USDT',
            'BBL/USDT',
            'SQT/USDT',
            'PORTAL/USDT',
            'AEG/USDT',
            'SCA/USDT',
            'AEVO/USDT',
            'NIBI/USDT',
            'STAR/USDT',
            'NGL/USDT',
            'ZEND/USDT',
            'BOME/USDT',
            'VENOM/USDT',
            'ZKJ/USDT',
            'ETHFI/USDT',
            'WEETH/ETH',
            'AURY/USDT',
            'FLT/USDT',
            'NAKA/USDT',
            'GMRX/USDT',
            'APRS/USDT',
            'WEN/USDT',
            'BRAWL/USDT',
            'DEGEN/USDT',
            'MFER/USDT',
            'BONUS/USDT',
            'ENA/USDT',
            'USDE/USDT',
            'VELAR/USDT',
            'XAR/USDT',
            'W/USDT',
            'EVERY/USDT',
            'MOJO/USDT',
            'G3/USDT',
            'ESE/USDT',
            'TNSR/USDT',
            'BLOCK/USDT',
            'MASA/USDT',
            'FOXY/USDT',
            'PRCL/USDT',
            'MSTAR/USDT',
            'OMNI/USDT',
            'BRETT/USDT',
            'MEW/USDT',
            'MERL/USDT',
            'PBUX/USDT',
            'EXVG/USDT',
            'LL/USDT',
            'SAFE/USDT',
            'WIF/USDT',
            'LAI/USDT',
            'GUMMY/USDT',
            'SVL/USDT',
            'KMNO/USDT',
            'ZENT/USDT',
            'TAI/USDT',
            'MODE/USDT',
            'SPEC/USDT',
            'GALAXIS/USDT',
            'ZERO/USDT',
            'LFT/USDT',
            'BUBBLE/USDT',
            'PONKE/USDT',
            'BB/USDT',
            'CTA/USDT',
            'NOT/USDT',
            'NLK/USDT',
            'DRIFT/USDT',
            'SQD/USDT',
            'NUTS/USDT',
            'NYAN/USDT',
            'HLG/USDT',
            'USDE/USDC',
            'SOL/USDE',
            'ETH/USDE',
            'BTC/USDE',
            'MON/USDT',
            'ELIX/USDT',
            'APTR/USDT',
            'MOG/USDT',
            'TAIKO/USDT',
            'ULTI/USDT',
            'AURORA/USDT',
            'AARK/USDT',
            'IO/USDT',
            'ATH/USDT',
            'COOKIE/USDT',
            'PIRATE/USDT',
            'XZK/USDT',
            'ZK/USDC',
            'ZK/USDT',
            'POPCAT/USDT',
            'ZRO/USDC',
            'ZRO/USDT',
            'NRN/USDT',
            'ZEX/USDT',
            'BLAST/USDT',
            'TST/USDT',
            'BTC/BRL',
            'ETH/BRL',
            'SOL/BRL',
            'USDT/BRL',
            'USDC/BRL',
            'WELL/USDT',
            'PTC/USDT',
            'DOP1/USDT',
            'NEAR/EUR',
            'SHIB/EUR',
            'WIF/EUR',
            'PEPE/EUR',
            'AVAX/EUR',
            'ONDO/EUR',
            'STETH/EUR',
            'WLD/EUR',
            'ENA/EUR',
            'TON/EUR',
            'LINK/EUR',
            'MOCA/USDT',
            'PIXFI/USDT',
            'UXLINK/USDT',
            'A8/USDT',
            'CLOUD/USDT',
            'ZKL/USDT',
            'AVAIL/USDT',
            'L3/USDT',
            'RENDER/USDT',
            'G/USDT',
            'TON/USDC',
            'WIF/USDC',
            'PEPE/USDC',
            'DOGS/USDT',
            'NOT/USDC',
            'BNB/USDC',
            'BONK/USDC',
            'DOGS/USDC',
            'DOGS/EUR',
            'NEIRO/USDT',
            'USDT/PLN',
            'ETH/PLN',
            'BTC/PLN',
            'FLOKI/USDC',
            'BCH/USDC',
            'NEAR/USDC',
            'ORDER/USDT',
            'ETH/TRY',
            'BTC/TRY',
            'USDT/TRY',
            'MEW/USDC',
            'KAS/USDC',
            'ONDO/USDC',
            'JASMY/USDC',
            'ATOM/USDC',
            'FET/USDC',
            'UNI/USDC',
            'BRETT/USDC',
            'TIA/USDC',
            'INJ/USDC',
            'MAK/USDT',
            'SUNDOG/USDT',
            'CATI/USDT',
            'HMSTR/USDT',
            'CATI/USDC',
            'CATI/EUR',
            'SOCIAL/USDT',
            'EGP1/USDT',
            'HMSTR/USDC',
            'EIGEN/USDT',
            'CATS/USDT',
            'NAVX/USDT',
            'BBSOL/USDC',
            'BBSOL/USDT',
            'CARV/USDT',
            'ZAP/USDT',
            'DEEP/USDT',
            'PUFFER/USDT',
            'DBR/USDT',
            'PUFF/USDT',
            'SCR/USDT',
            'X/USDT',
            'COOK/USDT',
            'GRASS/USDT',
            'KRO/USDT',
            'SMILE/USDT',
            'KAIA/USDT',
            'SWELL/USDT',
            'BBQ/USDT',
            'SWELL/USDC',
            'NS/USDT',
            'GOAT/USDT',
            'CMETH/USDT',
            'MORPHO/USDT',
            'NEIROCTO/USDT',
            'STOP/USDT',
            'BAN/USDT',
            'OL/USDT',
            'VIRTUAL/USDT',
            'MAJOR/USDT',
            'MEMEFI/USDT',
            'PNUT/USDT',
            'SPX/USDT',
            'THRUST/USDT',
            'ZRC/USDT',
            'LUCE/USDT',
            'CHILLGUY/USDT',
            'SUPRA/USDT',
            'PAAL/USDT',
            'F/USDT',
            'HPOS10I/USDT',
            'BBSOL/SOL',
            'XION/USDT',
            'MOVE/USDT',
            'MOZ/USDT',
            'ME/USDT',
            'ZEREBRO/USDT',
            'SEND/USDT',
            'AERO/USDT',
            'STREAM/USDT',
            'VANA/USDT',
            'LUNAI/USDT',
            'PENGU/USDT',
            'MNRY/USDT',
            'FLUID/USDT',
            'CATBNB/USDT',
            'FUEL/USDT',
            'ODOS/USDT',
            'ALCH/USDT',
            'FLOCK/USDT',
            'SONIC/USDT',
            'SERAPH/USDT',
            'LAVA/USDT',
            'XTER/USDT',
            'AI16Z/USDT',
            'GAME/USDT',
            'AIXBT/USDT',
            'J/USDT',
            'S/USDT',
            'TOSHI/USDT',
            'GPS/USDT',
            'HAT/USDT',
            'SOLV/USDT',
            'OBT/USDT',
            'SOSO/USDT',
            'TRUMP/USDT',
            'TRUMP/USDC',
            'PLUME/USDT',
            'ANIME/USDT',
            'N3/USDT',
            'LAYER/USDT',
            'PINEYE/USDT',
            'BERA/USDT',
            'AVL/USDT',
            'B3/USDT',
            'DIAM/USDT',
            'G7/USDT',
            'IP/USDT',
            'OM/USDT']
        //const timeframe = '5m';    // Таймфрейм (1 час)
        //const timeframes = ['5m', '15m', '1h', '1d']; // Разные таймфреймы
        const limit = 100;         // Количество свечей для анализа
  // Создаем инлайн-клавиатуру
  const message_kb = new InlineKeyboard().url(
    `Перейти к ${symbol}`,
    `https://www.bybit.com/trade/spot/${symbol}`
  );
        // Параметры индикаторов
        const macdSettings = {
            fastPeriod: 12,
            slowPeriod: 26,
            signalPeriod: 9,
            SimpleMAOscillator: false,
            SimpleMASignal: false,
        };

        const rsiSettings = {
            period: 14,
        };

        // Инициализация Bybit
        const exchange = new ccxt.bybit();

        // Функция для создания задержки
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        async function analyzeMarket() {
            // Задержка между запросами (в миллисекундах)
            const delayBetweenRequests = 6000; // 1 секунда
            // Перебор торговых пар
            for (const symbol of symbols) {
                try {
                    // Получаем свечные данные
                    const ohlcv_5 = await exchange.fetchOHLCV(symbol, '5m', undefined, limit);

                    // Извлекаем цены закрытия
                    const closes_5 = ohlcv_5.map(candle => candle[4]);

                    // Рассчитываем MACD
                    const macd_5 = MACD.calculate({
                        values: closes_5,
                        ...macdSettings,
                    });

                    // Рассчитываем RSI
                    const rsi_5 = RSI.calculate({
                        values: closes_5,
                        ...rsiSettings,
                    });

                    // Получаем свечные данные
                    const ohlcv_15 = await exchange.fetchOHLCV(symbol, '15m', undefined, limit);

                    // Извлекаем цены закрытия
                    const closes_15 = ohlcv_15.map(candle => candle[4]);

                    // Рассчитываем MACD
                    const macd_15 = MACD.calculate({
                        values: closes_15,
                        ...macdSettings,
                    });

                    // Рассчитываем RSI
                    const rsi_15 = RSI.calculate({
                        values: closes_15,
                        ...rsiSettings,
                    });
                    // Получаем свечные данные
                    const ohlcv_1h = await exchange.fetchOHLCV(symbol, '1h', undefined, limit);

                    // Извлекаем цены закрытия
                    const closes_1h = ohlcv_1h.map(candle => candle[4]);

                    // Рассчитываем MACD
                    const macd_1h = MACD.calculate({
                        values: closes_1h,
                        ...macdSettings,
                    });

                    // Рассчитываем RSI
                    const rsi_1h = RSI.calculate({
                        values: closes_1h,
                        ...rsiSettings,
                    });
                    // Получаем свечные данные
                    const ohlcv_1d = await exchange.fetchOHLCV(symbol, '1d', undefined, limit);

                    // Извлекаем цены закрытия
                    const closes_1d = ohlcv_1d.map(candle => candle[4]);

                    // Рассчитываем MACD
                    const macd_1d = MACD.calculate({
                        values: closes_1d,
                        ...macdSettings,
                    });

                    // Рассчитываем RSI
                    const rsi_1d = RSI.calculate({
                        values: closes_1d,
                        ...rsiSettings,
                    });
                    // Пример анализа
                    const lastMacd_5 = macd_5[macd_5.length - 1];
                    const lastRsi_5 = rsi_5[rsi_5.length - 1];
                    const lastMacd_15 = macd_15[macd_15.length - 1];
                    const lastRsi_15 = rsi_15[rsi_15.length - 1];
                    const lastMacd_1h = macd_1h[macd_1h.length - 1];
                    const lastRsi_1h = rsi_1h[rsi_1h.length - 1];
                    const lastMacd_1d = macd_1d[macd_1d.length - 1];
                    const lastRsi_1d = rsi_1d[rsi_1d.length - 1];

 // Создаем инлайн-клавиатуру
  const message_kb = new InlineKeyboard().url(
    `Перейти к ${symbol}`,
    `https://www.bybit.com/trade/spot/${symbol}`
  );


                    if (lastMacd_5.histogram > 0 && lastMacd_15.histogram > 0 && lastMacd_1h.histogram > 0 && lastMacd_1d.histogram > 0 && lastRsi_1d < 40) {

                        // Отправка сообщения в группу
                         await bot.api.sendMessage(CHAt_ID, ` 
                            <b>${symbol}</b>\nНа основе анализа индикаторов MACD и RSI, найден оптимальный момент для входа в сделку с минимальной вероятностью убытков.\nТекущая ситуация:\n<b>MACD:</b> На графиках таймфрейма 1D, 1H, 15m, 5m наблюдается пересечение MACD линии и сигнальной линии вверх, что указывает на возможный восходящий тренд.\n<b>RSI:</b>Индекс относительной силы таймфрейма 1D находится в зоне ${lastRsi_1d}, что говорит о том, что актив может быть недооценен и есть потенциал для роста.\n<b>Рекомендация:</b>\nС учетом сигналов от MACD и RSI, сейчас может быть хороший момент для открытия <b>длинной позиции</b>. Однако не забудь учесть уровень стоп-лосса и тейк-профита, чтобы минимизировать риски.                        `,{  parse_mode: "HTML",reply_markup: message_kb});
                    } else if (lastMacd_5.histogram < 0 && lastMacd_15.histogram > 0 && lastMacd_1h.histogram > 0 && lastMacd_1d.histogram > 0 && lastRsi_1d < 40) {

                        await bot.api.sendMessage(CHAt_ID,`
                            <b>${symbol}</b>\nНа основе анализа индикаторов MACD и RSI, найден скорый разворот тренда.\nТекущая ситуация:\n<b>MACD:</b> На графиках таймфрейма 1D, 1H, 15m, наблюдается пересечение MACD линии и сигнальной линии вверх, таймфрейм 5m еще находится в нисходящей зоне.\n<b>RSI:</b>Индекс относительной силы таймфрейма 1D находится в зоне ${lastRsi_1d}, что говорит о том, что актив может быть недооценен и есть потенциал для роста.\n<b>Рекомендация:</b>\nС учетом сигналов от MACD и RSI, сейчас может быть хороший момент для открытия <b>короткой позиции</b>. Однако не забудь учесть уровень стоп-лосса и тейк-профита, чтобы минимизировать риски.
                           `,{
  parse_mode: "HTML",reply_markup: message_kb});
                    } //else {
                        //console.log(`${lastRsi_5} `)
                    //}
                } catch (error) {
                    console.error('Ошибка:', error);
                }
                // Добавляем задержку между запросами +
                await sleep(delayBetweenRequests);
            }
        }


        // Запуск анализа
        const intervalId = setInterval(async () => {

            analyzeMarket()
        }, 65 * 60 * 1000); // 5 минут в миллисекундах


    }
    )
}



