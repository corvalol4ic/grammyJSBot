
const ccxt = require('ccxt');
const fs = require('fs');




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
                    //console.log(market.symbol);
                    
                // Добавляем новые значения в массив
                array = []
                 array = array.concat(market.symbol);    
                    console.log(array)
                    

                });
            } catch (error) {
                console.error('Ошибка при загрузке рынков:', error);
            }
           
        })(); 





    });
  };