module.exports = (bot) => {
    bot.command('start', async (ctx) => {
      await ctx.reply('Добро пожаловать! Я ваш Telegram-бот.');
    });
  };