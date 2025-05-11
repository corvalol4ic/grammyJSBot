const { Bot, InlineKeyboard } = require("grammy");
const ccxt = require("ccxt");
const { setTimeout } = require("timers/promises");

// Конфигурация
const CONFIG = {
  CHAT_ID: "-1002496172374",
  MESSAGE_DELAY: 3500,
  ANALYSIS_INTERVAL: 1 * 60 * 1000, // 10 минут в миллисекундах
  // Пары для анализа (можно добавлять/удалять)
  TRADING_PAIRS: [
    "MNT/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "PEPE/USDT",
    "SUI/USDT",
    "VIRTUAL/USDT",
    "APEX/USDT",
    "TRUMP/USDT",
    "ONDO/USDT",
    "GOAT/USDT",
    "LINK/USDT",
    "TRX/USDT",
    "TON/USDT",
    "SHIB/USDT",
    "AAVE/USDT",
    "POPCAT/USDT",
    "KAS/USDT",
    "CRV/USDT",
    "OP/USDT",
    "APT/USDT",
    "PYTH/USDT",
    
    "LTC/USDT"
  ],
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
    BULLISH: 55,
    BEARISH: 40,
    STRONG_BEARISH: 30
  },
  PROFIT_PERCENT: {
    STRONG_BULLISH: 2,
    BULLISH: 1
  },
  EXIT_STRATEGY: {
    RISK_REWARD_RATIO: 2,
    ATR_MULTIPLIER: 1.5,
    TRAILING_STOP_PERCENT: 0.5
  },
  BYBIT_LINK: "https://www.bybit.com/ru-RU/trade/spot/",
  MEXC_LINK: "https://www.mexc.com/ru-RU/exchange/"
};

// Инициализация биржи
const exchange = new ccxt.bybit({ enableRateLimit: true });

// Хранилище состояний пар
const pairStates = new Map();

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
const fetchOHLCV = async (symbol, timeframe, limit = 100) => {
  try {
    const ohlcv = await exchange.fetchOHLCV(symbol, timeframe, undefined, limit);
    return ohlcv.map(c => ({
      timestamp: c[0], open: c[1], high: c[2], 
      low: c[3], close: c[4], volume: c[5]
    }));
  } catch (error) {
    console.error(`Error fetching OHLCV for ${symbol}:`, error);
    return null;
  }
};

// Анализ и формирование сообщений
const determineTrend = (analysis) => {
  let bullishCount = 0, bearishCount = 0, totalSignals = 0;
  
  for (const timeframe of CONFIG.TIMEFRAMES) {
    if (!analysis[timeframe]) continue;
    const { indicators, lastClose } = analysis[timeframe];
    
    // Bullish signals
    if (indicators.RSI < CONFIG.INDICATORS.RSI.oversold) bullishCount++;
    if (indicators.MACD.histogram > 0) bullishCount++;
    if (indicators.EMA > indicators.SMA) bullishCount++;
    if (lastClose < indicators.BOLL.lower) bullishCount++;
    
    // Bearish signals
    if (indicators.RSI > CONFIG.INDICATORS.RSI.overbought) bearishCount++;
    if (indicators.MACD.histogram < 0) bearishCount++;
    if (indicators.EMA < indicators.SMA) bearishCount++;
    if (lastClose > indicators.BOLL.upper) bearishCount++;
    
    totalSignals += 4;
  }
  
  const bullishPercentage = (bullishCount / totalSignals) * 100;
  const bearishPercentage = (bearishCount / totalSignals) * 100;
  
  if (bullishPercentage > CONFIG.TREND_THRESHOLDS.STRONG_BULLISH) {
    return { 
      trend: "🟢 Сильный восходящий тренд", 
      percentage: bullishPercentage,
      state: "STRONG_BULLISH",
      profitPercent: CONFIG.PROFIT_PERCENT.STRONG_BULLISH
    };
  }
  if (bullishPercentage > CONFIG.TREND_THRESHOLDS.BULLISH) {
    return { 
      trend: "🟢 Восходящий тренд", 
      percentage: bullishPercentage,
      state: "BULLISH",
      profitPercent: CONFIG.PROFIT_PERCENT.BULLISH
    };
  }
  if (bearishPercentage > CONFIG.TREND_THRESHOLDS.STRONG_BEARISH) {
    return { 
      trend: "🔴 Сильный нисходящий тренд", 
      percentage: bearishPercentage,
      state: "STRONG_BEARISH",
      profitPercent: 0
    };
  }
  if (bearishPercentage > CONFIG.TREND_THRESHOLDS.BEARISH) {
    return { 
      trend: "🔴 Нисходящий тренд", 
      percentage: bearishPercentage,
      state: "BEARISH",
      profitPercent: 0
    };
  }
  
  return { 
    trend: "⚪ Нейтральный тренд", 
    percentage: 50,
    state: "NEUTRAL",
    profitPercent: 0
  };
};

const calculateExitLevels = (candles, lastClose, atr, profitPercent) => {
  const entry = lastClose;
  const stopLoss = entry - atr * CONFIG.EXIT_STRATEGY.ATR_MULTIPLIER;
  const takeProfit = entry * (1 + profitPercent / 100);
  return {
    entry,
    stopLoss,
    takeProfit,
    trailingStop: entry * (1 - CONFIG.EXIT_STRATEGY.TRAILING_STOP_PERCENT / 100),
    atrValue: atr,
    profitPercent
  };
};

const createKeyboard = (symbol) => {
  // Форматируем символ для Bybit (BTC/USDT) и для MEXC (BTC_USDT)
  const bybitSymbol = symbol;
  const mexcSymbol = symbol.replace('/', '_');
  
  return new InlineKeyboard()
    .url("Перейти к паре (Bybit)", `${CONFIG.BYBIT_LINK}${bybitSymbol}`).row()
    .url("Перейти к паре (MEXC)", `${CONFIG.MEXC_LINK}${mexcSymbol}`)
    
};

const createMessage = (symbol, trendResult, exitLevels) => {
  return `📊 <b>${symbol}</b>\n` +
    `📈 <b>Тренд:</b> ${trendResult.trend} (${trendResult.percentage.toFixed(2)}%)\n` +
    `🎯 <b>Вход:</b> ${exitLevels.entry.toFixed(9)}\n` +
    `💰 <b>Профит: ${exitLevels.profitPercent}%</b>\n` +
    //`🛑 <b>Стоп-лосс:</b> ${exitLevels.stopLoss.toFixed(6)}\n` +
    `🏷 <b>Трейлинг:</b> ${exitLevels.trailingStop.toFixed(6)}`;
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

// Проверка изменения состояния
const checkStateChange = (symbol, newState) => {
  const previousState = pairStates.get(symbol);
  
  // Если состояние не изменилось
  if (previousState === newState) return false;
  
  // Запоминаем новое состояние
  pairStates.set(symbol, newState);
  
  // Если предыдущего состояния не было (первый анализ)
  if (!previousState) return newState.includes("BULLISH");
  
  // Определяем важные переходы
  const importantTransitions = [
    ["BEARISH", "BULLISH"],
    ["BEARISH", "STRONG_BULLISH"],
    ["STRONG_BEARISH", "BULLISH"],
    ["STRONG_BEARISH", "STRONG_BULLISH"],
    ["NEUTRAL", "BULLISH"],
    ["NEUTRAL", "STRONG_BULLISH"]
  ];
  
  return importantTransitions.some(([prev, curr]) => 
    previousState.includes(prev) && newState.includes(curr)
  );
};

// Основная функция анализа
const runAnalysis = async (bot) => {
  try {
   // console.log("Starting analysis...");
  //  console.log(`Analyzing ${CONFIG.TRADING_PAIRS.length} pairs:`, CONFIG.TRADING_PAIRS);
    
    for (const pair of CONFIG.TRADING_PAIRS) {
      try {
        const analysis = await analyzePair(pair);
        const trendResult = determineTrend(analysis);
        
        if (!trendResult || trendResult.profitPercent === 0) {
          pairStates.set(pair, trendResult?.state || "NEUTRAL");
          continue;
        }
        
        const shouldNotify = checkStateChange(pair, trendResult.state);
        
        if (!shouldNotify) continue;
        
        const timeframeData = analysis['1h'] || analysis[Object.keys(analysis)[0]];
        const candles = await fetchOHLCV(pair, '1h', 100);
        if (!candles) continue;
        
        const exitLevels = calculateExitLevels(
          candles, 
          timeframeData.lastClose, 
          timeframeData.indicators.ATR,
          trendResult.profitPercent
        );
        
       // console.log(`Sending signal for ${pair}: ${trendResult.trend}`);
        await bot.api.sendMessage(
          CONFIG.CHAT_ID,
          createMessage(pair, trendResult, exitLevels),
          { parse_mode: "HTML", reply_markup: createKeyboard(pair) }
        );
        await setTimeout(CONFIG.MESSAGE_DELAY);
      } catch (error) {
       // console.error(`Error analyzing pair ${pair}:`, error);
      }
    }
    
   // console.log("Analysis completed");
  } catch (error) {
   // console.error("Error in runAnalysis:", error);
  }
};

// Команды для управления парами
const setupBotCommands = (bot) => {
  // Добавление пары для анализа
  bot.command('add_pair', async (ctx) => {
    const pair = ctx.message.text.split(' ')[1];
    if (!pair) return ctx.reply("Укажите пару, например: /add_pair BTC/USDT");
    
    if (CONFIG.TRADING_PAIRS.includes(pair)) {
      return ctx.reply(`Пара ${pair} уже в списке для анализа`);
    }
    
    CONFIG.TRADING_PAIRS.push(pair);
    ctx.reply(`Пара ${pair} добавлена в список для анализа. Всего пар: ${CONFIG.TRADING_PAIRS.length}`);
  });
  
  // Удаление пары из анализа
  bot.command('remove_pair', async (ctx) => {
    const pair = ctx.message.text.split(' ')[1];
    if (!pair) return ctx.reply("Укажите пару, например: /remove_pair BTC/USDT");
    
    const index = CONFIG.TRADING_PAIRS.indexOf(pair);
    if (index === -1) {
      return ctx.reply(`Пара ${pair} не найдена в списке для анализа`);
    }
    
    CONFIG.TRADING_PAIRS.splice(index, 1);
    ctx.reply(`Пара ${pair} удалена из списка для анализа. Всего пар: ${CONFIG.TRADING_PAIRS.length}`);
  });
  
  // Просмотр всех пар для анализа
  bot.command('list_pairs', async (ctx) => {
    ctx.reply(`Текущие пары для анализа (${CONFIG.TRADING_PAIRS.length}):\n${CONFIG.TRADING_PAIRS.join('\n')}`);
  });
  
  // Проверка состояния пары
  bot.command('check', async (ctx) => {
    const pair = ctx.message.text.split(' ')[1];
    if (!pair) return ctx.reply("Укажите пару, например: /check BTC/USDT");
    
    const state = pairStates.get(pair) || "не анализировалась";
    ctx.reply(`Текущее состояние пары ${pair}: ${state}`);
  });
  
  // Ручной запуск анализа
  bot.command('analyze', async (ctx) => {
    await ctx.reply("Запускаю анализ...");
    await runAnalysis(bot);
    await ctx.reply("Анализ  завершен");
  });
};

// Экспорт бота с автозапуском
module.exports = (bot) => {
  // Настройка команд бота
  setupBotCommands(bot);
  
  // Запуск анализа сразу при старте
  runAnalysis(bot).catch(console.error);
  
  // Установка периодического запуска
  setInterval(() => runAnalysis(bot), CONFIG.ANALYSIS_INTERVAL);
};
