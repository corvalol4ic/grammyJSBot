
const ccxt = require('ccxt');


module.exports = (bot) => {
    bot.command('spot', async (ctx) => {
      
    

        (async () => {
            // Создаем экземпляр биржи Bybit
            const exchange = new ccxt.bybit();
        
            try {
                // Загружаем рынки (торговые пары)
                const markets = await exchange.loadMarkets();
        
                // Фильтруем только спотовые рынки
                const spotMarkets = Object.values(markets).filter(market => market.spot);
        
                // Выводим список спотовых торговых пар
                spotMarkets.forEach(market => {
                    console.log(market.symbol);
                });
            } catch (error) {
                console.error('Ошибка при загрузке рынков:', error);
            }
        })(); 




    });
  };