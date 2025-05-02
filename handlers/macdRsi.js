const { Bot, InlineKeyboard } = require("grammy");
const ccxt = require("ccxt");
const { setTimeout } = require("timers/promises");

// Конфигурация
const CONFIG = {
  CHAT_ID: "-1002496172374",
  MESSAGE_DELAY: 3500,
  ANALYSIS_INTERVAL: 10 * 60 * 1000, // 10 минут в миллисекундах
  MAX_PAIRS: 400,
  TIMEFRAMES: ["5m", "15m", "1h", "1d"],
  INDICATORS: {
    RSI: { period: 14, overbought: 70, oversold: 30 },
    MACD: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    EMA: { period: 20 },
    SMA: { period: 50 },
    BOLL: { period: 20, stdDev: 2 },
    ATR: { period: 14 }
  },
  TREND_THRESHOLDS: {
    STRONG_BULLISH: 60,
    BULLISH: 55
  },
  EXIT_STRATEGY: {
    RISK_REWARD_RATIO: 2,
    ATR_MULTIPLIER: 1.5,
    TRAILING_STOP_PERCENT: 0.5
  },
  BYBIT_LINK: "https://www.bybit.com/ru-RU/trade/spot/"
};

// Инициализация биржи
const exchange = new ccxt.bybit({ enableRateLimit: true });

// Функции индикаторов
const calculateSMA = (data, period) => {
  const sma = [];
  for (let i = period - 1; i < data.length; i++) {
    sma.push(data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period);
  }
  return sma;
};

const calculateEMA = (data, period) => {
  const ema = [];
  const k = 2 / (period + 1);
  ema[0] = data[0];
  for (let i = 1; i < data.length; i++) {
    ema[i] = data[i] * k + ema[i - 1] * (1 - k);
  }
  return ema;
};

const calculateRSI = (data, period) => {
  const gains = [], losses = [];
  for (let i = 1; i < data.length; i++) {
    const change = data[i] - data[i - 1];
    gains.push(change > 0 ? change : 0);
    losses.push(change < 0 ? -change : 0);
  }
  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
  const rsi = [100 - (100 / (1 + avgGain / Math.max(avgLoss, 0.000001)))];
  for (let i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    rsi.push(100 - (100 / (1 + avgGain / Math.max(avgLoss, 0.000001))));
  }
  return rsi;
};

const calculateMACD = (data, fastPeriod, slowPeriod, signalPeriod) => {
  const fastEMA = calculateEMA(data, fastPeriod);
  const slowEMA = calculateEMA(data, slowPeriod);
  const startIdx = slowEMA.length - fastEMA.length;
  const macdLine = fastEMA.map((val, i) => val - slowEMA[startIdx + i]);
  return {
    macd: macdLine.slice(-1)[0],
    signal: calculateEMA(macdLine, signalPeriod).slice(-1)[0],
    histogram: macdLine.slice(-1)[0] - calculateEMA(macdLine, signalPeriod).slice(-1)[0]
  };
};

const calculateBollingerBands = (data, period, stdDev) => {
  const sma = calculateSMA(data, period);
  const bands = [];
  for (let i = period - 1; i < data.length; i++) {
    const slice = data.slice(i - period + 1, i + 1);
    const mean = sma[i - period + 1];
    const std = Math.sqrt(slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period);
    bands.push({ upper: mean + stdDev * std, middle: mean, lower: mean - stdDev * std });
  }
  return bands.slice(-1)[0];
};

const calculateATR = (candles, period) => {
  const tr = [];
  for (let i = 1; i < candles.length; i++) {
    tr.push(Math.max(
      candles[i].high - candles[i].low,
      Math.abs(candles[i].high - candles[i-1].close),
      Math.abs(candles[i].low - candles[i-1].close)
    ));
  }
  let atr = [tr.slice(0, period).reduce((a, b) => a + b, 0) / period];
  for (let i = period; i < tr.length; i++) {
    atr.push((atr[atr.length-1] * (period-1) + tr[i]) / period);
  }
  return atr.slice(-1)[0];
};

// Работа с биржей
const getTopLiquidPairs = async (limit = 100) => {
  try {
    await exchange.loadMarkets();
    return Object.values(exchange.markets)
      .filter(m => m.spot && m.active && m.quote === "USDT")
      .sort((a, b) => (b.info.turnover24h || 0) - (a.info.turnover24h || 0))
      .slice(0, limit)
      .map(m => m.symbol);
  } catch (error) {
    return [];
  }
};

const fetchOHLCV = async (symbol, timeframe, limit = 100) => {
  try {
    const ohlcv = await exchange.fetchOHLCV(symbol, timeframe, undefined, limit);
    return ohlcv.map(c => ({
      timestamp: c[0], open: c[1], high: c[2], 
      low: c[3], close: c[4], volume: c[5]
    }));
  } catch (error) {
    return null;
  }
};

// Анализ и формирование сообщений
const determineTrend = (analysis) => {
  let bullishCount = 0, totalSignals = 0;
  for (const timeframe of CONFIG.TIMEFRAMES) {
    if (!analysis[timeframe]) continue;
    const { indicators, lastClose } = analysis[timeframe];
    if (indicators.RSI < CONFIG.INDICATORS.RSI.oversold) bullishCount++;
    if (indicators.MACD.histogram > 0) bullishCount++;
    if (indicators.EMA > indicators.SMA) bullishCount++;
    if (lastClose < indicators.BOLL.lower) bullishCount++;
    totalSignals += 4;
  }
  const bullishPercentage = (bullishCount / totalSignals) * 100;
  if (bullishPercentage > CONFIG.TREND_THRESHOLDS.STRONG_BULLISH) {
    return { trend: "🟢 Сильный восходящий тренд", percentage: bullishPercentage };
  }
  if (bullishPercentage > CONFIG.TREND_THRESHOLDS.BULLISH) {
    return { trend: "🟢 Восходящий тренд", percentage: bullishPercentage };
  }
  return null;
};

const calculateExitLevels = (candles, lastClose, atr) => {
  const entry = lastClose;
  const stopLoss = entry - atr * CONFIG.EXIT_STRATEGY.ATR_MULTIPLIER;
  return {
    entry,
    stopLoss,
    takeProfit: entry + (entry - stopLoss) * CONFIG.EXIT_STRATEGY.RISK_REWARD_RATIO,
    trailingStop: entry * (1 - CONFIG.EXIT_STRATEGY.TRAILING_STOP_PERCENT / 100),
    atrValue: atr
  };
};

const createKeyboard = (symbol) => 
  new InlineKeyboard().url("Перейти к паре", `${CONFIG.BYBIT_LINK}${symbol}`);

const createMessage = (symbol, trendResult, exitLevels) => {
  const stopLossPercent = (exitLevels.entry - exitLevels.stopLoss) / exitLevels.entry * 100;
  const takeProfitPercent = (exitLevels.takeProfit - exitLevels.entry) / exitLevels.entry * 100;
  return `📊 <b>${symbol}</b>\n` +
    `📈 <b>Тренд:</b> ${trendResult.trend} (${trendResult.percentage.toFixed(2)}%)\n` +
    `🎯 <b>Вход:</b> ${exitLevels.entry}\n` +
<<<<<<< HEAD
    `🏷 <b>Трейлинг:</b> ${exitLevels.trailingStop}\n`;
=======
   // `🛑 <b>Стоп:</b> ${exitLevels.stopLoss} (${stopLossPercent.toFixed(2)}%)\n` +
    //`💰 <b>Профит:</b> ${exitLevels.takeProfit} (${takeProfitPercent.toFixed(2)}%)\n` +
    `🏷 <b>Трейлинг:</b> ${exitLevels.trailingStop}\n` +
   // `📉 <b>ATR:</b> ${exitLevels.atrValue}`;
>>>>>>> ef49d4b22195addbdd8e2cfbabefa001ad8fe186
};

const analyzePair = async (symbol) => {
  const analysis = {};
  for (const timeframe of CONFIG.TIMEFRAMES) {
    const data = await fetchOHLCV(symbol, timeframe);
    if (!data || data.length < 50) continue;
    const closes = data.map(d => d.close);
    analysis[timeframe] = {
      lastClose: closes.slice(-1)[0],
      indicators: {
        RSI: calculateRSI(closes, CONFIG.INDICATORS.RSI.period).slice(-1)[0],
        MACD: calculateMACD(closes, CONFIG.INDICATORS.MACD.fastPeriod, CONFIG.INDICATORS.MACD.slowPeriod, CONFIG.INDICATORS.MACD.signalPeriod),
        EMA: calculateEMA(closes, CONFIG.INDICATORS.EMA.period).slice(-1)[0],
        SMA: calculateSMA(closes, CONFIG.INDICATORS.SMA.period).slice(-1)[0],
        BOLL: calculateBollingerBands(closes, CONFIG.INDICATORS.BOLL.period, CONFIG.INDICATORS.BOLL.stdDev),
        ATR: calculateATR(data, CONFIG.INDICATORS.ATR.period)
      }
    };
  }
  return analysis;
};

// Основная функция  анализа
const runAnalysis = async (bot) => {
  const pairs = await getTopLiquidPairs(CONFIG.MAX_PAIRS);
  for (const pair of pairs) {
    try {
      const analysis = await analyzePair(pair);
      const trendResult = determineTrend(analysis);
      if (!trendResult) continue;
      
      const timeframeData = analysis['1h'] || analysis[Object.keys(analysis)[0]];
      const candles = await fetchOHLCV(pair, '1h', 100);
      if (!candles) continue;
      
      const exitLevels = calculateExitLevels(candles, timeframeData.lastClose, timeframeData.indicators.ATR);
      
      await bot.api.sendMessage(
        CONFIG.CHAT_ID,
        createMessage(pair, trendResult, exitLevels),
        { parse_mode: "HTML", reply_markup: createKeyboard(pair) }
      );
      await setTimeout(CONFIG.MESSAGE_DELAY);
    } catch (error) {}
  }
};

// Экспорт бота с автозапуском
module.exports = (bot) => {
  // Запуск анализа сразу  при старте
  runAnalysis(bot);
  
  // Установка периодического запуска каждые 10 минут
  setInterval(() => runAnalysis(bot), CONFIG.ANALYSIS_INTERVAL);
  
  // Ручной запуск по команде
  bot.command('analyze', async (ctx) => {
    await runAnalysis(bot);
  });
};
