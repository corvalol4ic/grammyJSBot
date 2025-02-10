require('dotenv').config()
const {Bot, GrammyError,HttpError} = require('grammy')


const bot = new Bot(process.env.BOT_TOKEN)


//установка дефолтных команд бота
bot.api.setMyCommands([
    {
        command: 'start', description: 'начало работы бота'
    },
    {
        command: 'help', description: 'помощь'
    }
])


bot.command(['start', 'help'], async (ctx) =>{
    await ctx.reply('начало на JS')
})

// отправка ответа на сообщение
bot.command( 'wow', async (ctx) =>{
    
    await ctx.react('👍')
    await ctx.reply('начало на JS', {
        reply_parameters: {message_id: ctx.msg.message_id }
    })
})

bot.hears(/жесть/, async (ctx) =>{
    await ctx.reply('как есть')
})

bot.on(':photo', async (ctx) => {
    await ctx.reply('отличное фото')
})
// кастомные фильтры
bot.on('msg').filter((ctx) => {
   return ctx.from.id === 390731763
}, async (ctx) => {
    await ctx.reply('Привет хозяин')
    console.log(ctx.msg)
})


bot.catch((err) => {
    const ctx = err.ctx
    console.error(`ERROR while handling update ${ctx.update.update_id}:`);
    const e = err.error;

    if (e instanceof GrammyError){
        console.error('Error in request:', e.description);

    } else if (e instanceof HttpError){
        console.error('Could not contact Telegram:', e);
    } else{
        console.error('Unknown error:', e);
    }
})




bot.start()