module.exports = (bot) => {
    bot.on('msg').filter((ctx) => {
        return ctx.from.id === 390731763
     }, async (ctx) => {
         await ctx.reply('Привет хозяин')
        
     })
  };