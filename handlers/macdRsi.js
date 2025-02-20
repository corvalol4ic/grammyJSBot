const ccxt = require('ccxt');
const { MACD, RSI } = require('technicalindicators');


const CHAt_ID = process.env.CHAt_ID

module.exports = (bot) => {
    bot.command('run', async (ctx) => {
// Настройки
//const symbol = 'BTC/USDT'; // Торговая пара
const symbols = ['BTC/USDT', 'APE/USDT', 'PEPE/USDT', 'XRP/USDT'];
//const timeframe = '5m';    // Таймфрейм (1 час)
const timeframes = ['1m', '5m', '1h', '1d']; // Разные таймфреймы
const limit = 100;         // Количество свечей для анализа

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

async function analyzeMarket() {
    // Перебор торговых пар
    for (const symbol of symbols) {
        for (const timeframe of timeframes) {
            try {
                // Получаем свечные данные
                const ohlcv = await exchange.fetchOHLCV(symbol, timeframe, undefined, limit);

                // Извлекаем цены закрытия
                const closes = ohlcv.map(candle => candle[4]);

                // Рассчитываем MACD
                const macd = MACD.calculate({
                    values: closes,
                    ...macdSettings,
                });

                // Рассчитываем RSI
                const rsi = RSI.calculate({
                    values: closes,
                    ...rsiSettings,
                });

                // Выводим результаты
                //await ctx.reply('Последние значения MACD:');
                //await ctx.reply(macd.slice(-5)); // Последние 5 значений MACD

                //await ctx.reply('Последние значения RSI:');
                //await ctx.reply(rsi.slice(-5)); // Последние 5 значений RSI

                // Пример анализа
                const lastMacd = macd[macd.length - 1];
                const lastRsi = rsi[rsi.length - 1];

                if (lastMacd.histogram > 0 && lastRsi > 50) {
                
                    // Отправка сообщения в группу
                    await bot.api.sendMessage(CHAt_ID, `Сигнал на покупку ${symbol}: MACD ${timeframe} гистограмма выше 0 и RSI выше 50`);
                } else if (lastMacd.histogram < 0 && lastRsi < 50) {
                    
                    await bot.api.sendMessage(CHAt_ID, `Сигнал на продажу ${symbol}: MACD  ${timeframe} гистограмма ниже 0 и RSI ниже 50`);
                } else {
                    
                    await bot.api.sendMessage(CHAt_ID, ` ${timeframe} нет четкого сигнала по  ${symbol}`);
                }
            } catch (error) {
                console.error('Ошибка:', error);
            }
}
}
}

// Запуск анализа
analyzeMarket();
})
}