import os
import telebot
import pysrt
from flask import Flask
from threading import Thread

# သင့်ရဲ့ Bot Token ကို ထည့်ပါ
TOKEN = '8158171064:AAFfFmrXm_kcwDdIb43gKmqUfSrsLSPX9-U'
bot = telebot.TeleBot(TOKEN)
app = Flask('')

# 24/7 Run နိုင်ရန် Web Server အသေးလေး ဖန်တီးခြင်း
@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Document (SRT) ဖိုင်ပို့လာလျှင် အလုပ်လုပ်မည့်အပိုင်း
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        # ဖိုင်နာမည်စစ်ဆေးခြင်း
        file_name = message.document.file_name
        if not file_name.endswith('.srt'):
            bot.reply_to(message, "ကျေးဇူးပြု၍ .srt ဖိုင်ကိုသာ ပေးပို့ပါ။")
            return

        # အသုံးပြုသူ ပို့လိုက်သော Caption ကို ရယူခြင်း (ဥပမာ - Z1-1)
        # Caption မပါလာလျှင် ဖိုင်နာမည်ကို အသုံးပြုမည်
        user_caption = message.caption if message.caption else "Format ပြင်ဆင်ပြီး"

        # လုပ်ဆောင်နေကြောင်း အသိပေးစာပို့ခြင်း (Reply ထောက်၍)
        processing_msg = bot.reply_to(message, f"⏳ {user_caption} အတွက် Format အမှားများကို ပြင်ဆင်နေပါသည်...")

        # ဖိုင်ဒေါင်းလုဒ်ဆွဲခြင်း
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_name = "input_" + str(message.message_id) + ".srt"
        output_name = "fixed_" + file_name

        with open(input_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        # pysrt ကိုအသုံးပြု၍ Format ပြင်ဆင်ခြင်း (စာသားနှင့် အချိန်ကို မပြောင်းလဲပါ)
        subs = pysrt.open(input_name, encoding='utf-8')
        subs.save(output_name, encoding='utf-8')

        # ပြင်ဆင်ပြီးသော ဖိုင်ကို မူလ Message ကို Reply ထောက်၍ ပြန်ပို့ခြင်း
        with open(output_name, 'rb') as fixed_file:
            bot.send_document(
                chat_id=message.chat.id, 
                document=fixed_file, 
                caption=f"✅ {user_caption} အတွက် Format ပြင်ဆင်ပြီးပါပြီ။",
                reply_to_message_id=message.message_id # မူလပို့သော Message (Series No/Ep No) ကို Reply ထောက်ခြင်း
            )

        # အသိပေးစာ Message ကို ဖျက်ခြင်း (သပ်ရပ်စေရန်)
        bot.delete_message(message.chat.id, processing_msg.message_id)

        # အသုံးပြုပြီးသော ဖိုင်များကို ဖျက်ခြင်း
        if os.path.exists(input_name):
            os.remove(input_name)
        if os.path.exists(output_name):
            os.remove(output_name)

    except Exception as e:
        bot.reply_to(message, f"❌ အမှားအယွင်းဖြစ်ပေါ်နေပါသည်: ဖိုင် Format အလွန်အမင်းပျက်စီးနေနိုင်ပါသည်။\nError: {e}")
        # Error တက်လျှင်လည်း ကျန်နေခဲ့မည့် ဖိုင်များကို ရှင်းလင်းရန်
        if 'input_name' in locals() and os.path.exists(input_name):
            os.remove(input_name)
        if 'output_name' in locals() and os.path.exists(output_name):
            os.remove(output_name)

# Bot ကို စတင် Run ခြင်း
if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
