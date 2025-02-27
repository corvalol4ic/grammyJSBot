// const ccxt = require('ccxt');
// const { Bot } = require('grammy');
// const { RSI, MACD } = require('technicalindicators');
// const winston = require('winston');

// // Настройка логгера
// const logger = winston.createLogger({
//     level: 'info',
//     format: winston.format.combine(
//         winston.format.timestamp(),
//         winston.format.printf(({ timestamp, level, message }) => {
//             return `${timestamp} [${level.toUpperCase()}]: ${message}`;
//         })
//     ),
//     transports: [
//         new winston.transports.Console(),
//         new winston.transports.File({ filename: 'bot.log' }),
//     ],
// });

// // Инициализация бота Telegram
// const bot = new Bot('YOUR_TELEGRAM_BOT_TOKEN');

// // Инициализация Bybit API
// const exchange = new ccxt.bybit({
//     apiKey: 'YOUR_BYBIT_API_KEY',
//     secret: 'YOUR_BYBIT_API_SECRET',
// });

// // Функция для получения списка торгующихся фьючерсов
// async function getFuturesMarkets() {
//     try {
//         const markets = await exchange.fetchMarkets();
//         const futuresMarkets = markets.filter(market => market.future); // Фильтруем фьючерсы
//         logger.info(`Получено ${futuresMarkets.length} фьючерсов`);
//         return futuresMarkets.map(market => market.symbol); // Возвращаем только символы
//     } catch (error) {
//         logger.error(`Ошибка при получении списка фьючерсов: ${error.message}`);
//         return [];
//     }
// }

// // Функция для получения свечей с Bybit
// async function getCandles(symbol, timeframe, limit = 100) {
//     try {
//         const candles = await exchange.fetchOHLCV(symbol, timeframe, undefined, limit);
//         logger.info(`Успешно получены свечи для ${symbol} (${timeframe})`);
//         return candles;
//     } catch (error) {
//         logger.error(`Ошибка при получении свечей для ${symbol} (${timeframe}): ${error.message}`);
//         return null;
//     }
// }

// // Функция для расчета RSI
// function calculateRSI(closes, period = 14) {
//     try {
//         const rsi = RSI.calculate({ values: closes, period });
//         logger.info(`RSI рассчитан для ${closes.length} свечей`);
//         return rsi;
//     } catch (error) {
//         logger.error(`Ошибка при расчете RSI: ${error.message}`);
//         return null;
//     }
// }

// // Функция для расчета MACD
// function calculateMACD(closes, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
//     try {
//         const macd = MACD.calculate({
//             values: closes,
//             fastPeriod,
//             slowPeriod,
//             signalPeriod,
//             SimpleMAOscillator: false,
//             SimpleMASignal: false,
//         });
//         logger.info(`MACD рассчитан для ${closes.length} свечей`);
//         return macd;
//     } catch (error) {
//         logger.error(`Ошибка при расчете MACD: ${error.message}`);
//         return null;
//     }
// }

// // Функция для определения разворота тренда с использованием RSI и MACD
// function detectTrendReversal(candles) {
//     if (candles.length < 30) {
//         logger.warn('Недостаточно данных для анализа тренда');
//         return false;
//     }

//     const closes = candles.map(candle => candle[4]); // Цены закрытия

//     // Расчет RSI
//     const rsi = calculateRSI(closes);
//     if (!rsi || rsi.length === 0) return false;

//     const lastRsi = rsi[rsi.length - 1];

//     // Расчет MACD
//     const macd = calculateMACD(closes);
//     if (!macd || macd.length === 0) return false;

//     const lastMacd = macd[macd.length - 1];

//     // Логика для определения разворота
//     const isOverbought = lastRsi > 70; // RSI выше 70 — перекупленность
//     const isOversold = lastRsi < 30; // RSI ниже 30 — перепроданность
//     const isBearishMACD = lastMacd.MACD < lastMacd.signal; // MACD ниже сигнальной линии
//     const isBullishMACD = lastMacd.MACD > lastMacd.signal; // MACD выше сигнальной линии

//     // Возможный разворот вниз (медвежий)
//     if (isOverbought && isBearishMACD) {
//         logger.info(`Обнаружен медвежий разворот для ${candles.length} свечей`);
//         return 'bearish';
//     }

//     // Возможный разворот вверх (бычий)
//     if (isOversold && isBullishMACD) {
//         logger.info(`Обнаружен бычий разворот для ${candles.length} свечей`);
//         return 'bullish';
//     }

//     return false;
// }

// // Функция для мониторинга трендов
// async function monitorTrends(symbol, timeframe, chatId) {
//     try {
//         const candles = await getCandles(symbol, timeframe);
//         if (!candles) return;

//         const reversalSignal = detectTrendReversal(candles);
//         if (reversalSignal) {
//             const message = `Возможный разворот тренда на ${symbol} (${timeframe}): ${reversalSignal === 'bullish' ? '📈 Бычий' : '📉 Медвежий'}`;
//             await bot.api.sendMessage(chatId, message);
//             logger.info(`Сообщение отправлено в Telegram: ${message}`);
//         }
//     } catch (error) {
//         logger.error(`Ошибка в функции monitorTrends: ${error.message}`);
//     }
// }

// // Команда для запуска мониторинга
// bot.command('start', async (ctx) => {
//     const chatId = ctx.chat.id;
//     const timeframes = ['1m', '5m', '15m', '1h']; // Таймфреймы

//     try {
//         // Получаем список фьючерсов
//         const futuresMarkets = await getFuturesMarkets();
//         if (futuresMarkets.length === 0) {
//             await ctx.reply('Не удалось получить список фьючерсов.');
//             return;
//         }

//         await ctx.reply(`Начинаю мониторинг фьючерсов: ${futuresMarkets.join(', ')} на таймфреймах: ${timeframes.join(', ')}`);
//         logger.info(`Мониторинг запущен для фьючерсов: ${futuresMarkets.join(', ')} на таймфреймах: ${timeframes.join(', ')}`);

//         // Запуск мониторинга каждые 10 секунд
//         setInterval(async () => {
//             for (const symbol of futuresMarkets) {
//                 for (const timeframe of timeframes) {
//                     await monitorTrends(symbol, timeframe, chatId);
//                 }
//             }
//         }, 10000);
//     } catch (error) {
//         logger.error(`Ошибка при запуске мониторинга: ${error.message}`);
//         await ctx.reply('Произошла ошибка при запуске мониторинга.');
//     }
// });

// // Обработка ошибок бота
// bot.catch((err) => {
//     logger.error(`Ошибка в боте Telegram: ${err.message}`);
// });

// // Запуск бота
// bot.start()
//     .then(() => {
//         logger.info('Бот успешно запущен');
//     })
//     .catch((error) => {
//         logger.error(`Ошибка при запуске бота: ${error.message}`);
//     });