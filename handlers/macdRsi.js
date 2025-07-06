const { Bot, InlineKeyboard } = require("grammy");
const ccxt = require("ccxt");
const { setTimeout } = require("timers/promises");

// Конфигурация
const CONFIG = {
  CHAT_ID: "-1002496172374",
  MESSAGE_DELAY: 3500,
  ANALYSIS_INTERVAL: 1 * 60 * 1000, // 1 минута в миллисекундах
  // Пары для анализа
  TRADING_PAIRS: [
    "PEPE/USDT", "XRP/USDT", "DOT/USDT", "LTC/USDT", "DOGE/USDT",
    "AXS/USDT", "DYDX/USDT", "AAVE/USDT", "LINK/USDT", "SUSHI/USDT",
    "UNI/USDT", "KAS/USDT", "ADA/USDT", "GRT/USDT", "SOL/USDT",
    "FIL/USDT", "OMG/USDT", "BAT/USDT", "ZRX/USDT", "CRV/USDT",
    "PERP/USDT", "WAVES/USDT", "LUNC/USDT", "SPELL/USDT", "SHIB/USDT",
    "ATOM/USDT", "ALGO/USDT", "SAND/USDT", "AVAX/USDT", "AVA/USDT",
    "QTUM/USDT", "GMX/USDT", "ACH/USDT", "SUN/USDT", "BTT/USDT",
    "TRX/USDT", "NFT/USDT", "POKT/USDT", "SON/USDT", "DOME/USDT",
    "NEAR/USDT", "SD/USDT", "APE/USDT", "RACA/USDT", "LUNA/USDT",
    "FLOKI/USDT", "BABYDOGE/USDT", "APT/USDT", "PEOPLE/USDT",
    "TWT/USDT", "ORT/USDT", "HOOK/USDT", "OAS/USDT", "MAGIC/USDT",
    "TON/USDT", "BONK/USDT", "FLR/USDT", "TIME/USDT", "RPL/USDT"
  ],
  TIMEFRAMES: ["15m", "1h", "4h"], // Оптимизированные таймфреймы
  INDICATORS: {
    STOCHASTIC: { period: 14, kPeriod: 3, dPeriod: 3, overbought: 80, oversold: 20 },
    MACD: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    ATR: { period: 14 }
  },
  TREND_THRESHOLDS: {
    STRONG_BULLISH: 75,
    BULLISH: 60,
    BEARISH: 40,
    STRONG_BEARISH: 25
  },
  PROFIT_PERCENT: {
    STRONG_BULLISH: 3,
    BULLISH: 2
  },
  EXIT_STRATEGY: {
    RISK_REWARD_RATIO: 2,
    ATR_MULTIPLIER: 1.5,
    TRAILING_STOP_PERCENT: 0.8
  },
  BYBIT_LINK: "https://www.bybit.com/ru-RU/trade/spot/",
  MEXC_LINK: "https://www.mexc.com/ru-RU/exchange/"
};

// Инициализация биржи
const exchange = new ccxt.bybit({ enableRateLimit: true });

// Хранилище состояний пар
const pairStates = new Map();

// Функции индикаторов
const calculateStochastic = (candles, period, kPeriod, dPeriod) => {
  const highs = candles.map(c => c.high);
  const lows = candles.map(c => c.low);
  const closes = candles.map(c => c.close);
  
  const stochK = [];
  for (let i = period - 1; i < closes.length; i++) {
    const highestHigh = Math.max(...highs.slice(i - period + 1, i + 1));
    const lowestLow = Math.min(...lows.slice(i - period + 1, i + 1));
    const currentClose = closes[i];
    const k = ((currentClose - lowestLow) / (highestHigh - lowestLow)) * 100;
    stochK.push(k);
  }
  
  const stochD = [];
  for (let i = kPeriod - 1; i < stochK.length; i++) {
    const d = stochK.slice(i - kPeriod + 1, i + 1).reduce((a, b) => a + b, 0) / kPeriod;
    stochD.push(d);
  }
  
  return {
    k: stochK.slice(-1)[0],
    d: stochD.slice(-1)[0]
  };
};

const calculateMACD = (data, fastPeriod, slowPeriod, signalPeriod) => {
  const calculateEMA = (data, period) => {
    const ema = [];
    const k = 2 / (period + 1);
    ema[0] = data[0];
    for (let i = 1; i < data.length; i++) {
      ema[i] = data[i] * k + ema[i - 1] * (1 - k);
    }
    return ema;
  };

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

const calculateATR = (candles, period) => {
  const tr = [];
  for (let i = 1; i < candles.length; i++) {
    tr.push(Math.max(
      candles[i].high - candles[i].low,
      Math.abs(candles[i].high - candles[i-1].close),
      Math.abs(candles[i].low - candles[i-1].close)
    );
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
    const { indicators } = analysis[timeframe];
    
    // Сигналы стохастика
    if (indicators.STOCHASTIC.k < CONFIG.INDICATORS.STOCHASTIC.oversold && 
        indicators.STOCHASTIC.d < CONFIG.INDICATORS.STOCHASTIC.oversold &&
        indicators.STOCHASTIC.k > indicators.STOCHASTIC.d) {
      bullishCount += 2; // Более сильный вес для стохастика
    }
    
    // Сигналы MACD
    if (indicators.MACD.histogram > 0 && indicators.MACD.macd > indicators.MACD.signal) {
      bullishCount++;
    }
    
    // Медвежьи сигналы
    if (indicators.STOCHASTIC.k > CONFIG.INDICATORS.STOCHASTIC.overbought && 
        indicators.STOCHASTIC.d > CONFIG.INDICATORS.STOCHASTIC.overbought &&
        indicators.STOCHASTIC.k < indicators.STOCHASTIC.d) {
      bearishCount += 2;
    }
    
    if (indicators.MACD.histogram < 0 && indicators.MACD.macd < indicators.MACD.signal) {
      bearishCount++;
    }
    
    totalSignals += 3; // 2 от стохастика и 1 от MACD на каждом таймфрейме
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
  const bybitSymbol = symbol;
  const mexcSymbol = symbol.replace('/', '_');
  
  return new InlineKeyboard()
    .url("Bybit", `${CONFIG.BYBIT_LINK}${bybitSymbol}`).row()
    .url("MEXC", `${CONFIG.MEXC_LINK}${mexcSymbol}`);
};

const createMessage = (symbol, trendResult, exitLevels) => {
  return `📊 <b>${symbol}</b>\n` +
    `📈 <b>Тренд:</b> ${trendResult.trend} (${trendResult.percentage.toFixed(2)}%)\n` +
    `🎯 <b>Вход:</b> ${exitLevels.entry.toFixed(9)}\n` +
    `💰 <b>Профит: ${exitLevels.profitPercent}%</b>\n` +
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
        STOCHASTIC: calculateStochastic(
          data,
          CONFIG.INDICATORS.STOCHASTIC.period,
          CONFIG.INDICATORS.STOCHASTIC.kPeriod,
          CONFIG.INDICATORS.STOCHASTIC.dPeriod
        ),
        MACD: calculateMACD(
          closes,
          CONFIG.INDICATORS.MACD.fastPeriod,
          CONFIG.INDICATORS.MACD.slowPeriod,
          CONFIG.INDICATORS.MACD.signalPeriod
        ),
        ATR: calculateATR(data, CONFIG.INDICATORS.ATR.period)
      }
    };
  }
  return analysis;
};

// Проверка изменения состояния
const checkStateChange = (symbol, newState) => {
  const previousState = pairStates.get(symbol);
  
  if (previousState === newState) return false;
  
  pairStates.set(symbol, newState);
  
  if (!previousState) return newState.includes("BULLISH");
  
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
        
        await bot.api.sendMessage(
          CONFIG.CHAT_ID,
          createMessage(pair, trendResult, exitLevels),
          { parse_mode: "HTML", reply_markup: createKeyboard(pair) }
        );
        await setTimeout(CONFIG.MESSAGE_DELAY);
      } catch (error) {
        console.error(`Error analyzing pair ${pair}:`, error);
      }
    }
  } catch (error) {
    console.error("Error in runAnalysis:", error);
  }
};

// Команды для управления парами
const setupBotCommands = (bot) => {
  bot.command('add_pair', async (ctx) => {
    const pair = ctx.message.text.split(' ')[1];
    if (!pair) return ctx.reply("Укажите пару, например: /add_pair BTC/USDT");
    
    if (CONFIG.TRADING_PAIRS.includes(pair)) {
      return ctx.reply(`Пара ${pair} уже в списке для анализа`);
    }
    
    CONFIG.TRADING_PAIRS.push(pair);
    ctx.reply(`Пара ${pair} добавлена в список для анализа. Всего пар: ${CONFIG.TRADING_PAIRS.length}`);
  });
  
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
  
  bot.command('list_pairs', async (ctx) => {
    ctx.reply(`Текущие пары для анализа (${CONFIG.TRADING_PAIRS.length}):\n${CONFIG.TRADING_PAIRS.join('\n')}`);
  });
  
  bot.command('check', async (ctx) => {
    const pair = ctx.message.text.split(' ')[1];
    if (!pair) return ctx.reply("Укажите пару, например: /check BTC/USDT");
    
    const state = pairStates.get(pair) || "не анализировалась";
    ctx.reply(`Текущее состояние пары ${pair}: ${state}`);
  });
  
  bot.command('analyze', async (ctx) => {
    await ctx.reply("Запускаю анализ...");
    await runAnalysis(bot);
    await ctx.reply("Анализ завершен");
  });
};

// Экспорт бота с автозапуском
module.exports = (bot) => {
  setupBotCommands(bot);
  runAnalysis(bot).catch(console.error);
  setInterval(() => runAnalysis(bot), CONFIG.ANALYSIS_INTERVAL);
};
