import telebot
import requests
import time
from flask import Flask, request
from telebot import types
from collections import defaultdict
from datetime import datetime, timedelta

# Telegram Bot API 令牌
TOKEN = '7627219407:AAFWbLwnSL3f2ogItDjjGueT0InaWQUPWak'
bot = telebot.TeleBot(TOKEN)

# Flask 应用
app = Flask(__name__)

# 图片 API 字典
IMAGE_API_DICT = {
    "看JK": "http://api.yujn.cn/api/jk.php",
    "看jk": "http://api.yujn.cn/api/jk.php",
    "看美女": "http://api.yujn.cn/api/ksxjj.php",
    "看黑丝": "http://api.yujn.cn/api/heisi.php",
    "看白丝": "http://api.yujn.cn/api/baisi.php",
    "看诱惑": "http://api.yujn.cn/api/yht.php",
    "美女壁纸": "http://api.yujn.cn/api/meinv.php"
}

# 视频 API 字典
VIDEO_API_DICT = {
    "小姐姐视频": "http://api.yujn.cn/api/zzxjj.php?type=video",
    "刷抖音": "http://api.yujn.cn/api/ndym.php?type=video",
    "玉足视频": "http://api.yujn.cn/api/yuzu.php?type=video",
    "热舞视频": "http://api.yujn.cn/api/rewu.php?type=video",
    "黑丝视频": "http://api.yujn.cn/api/heisis.php?type=video",
    "白丝视频": "http://api.yujn.cn/api/baisis.php?type=video",
    "甜妹视频": "http://api.yujn.cn/api/tianmei.php?type=video",
    "Jk视频": "http://api.yujn.cn/api/jksp.php?type=video"
}

# 提示信息
HELP_MESSAGE = (
    "羊羊来发福利啦！\n"
    "直接输入以下关键词即可获取内容：\n"
    "【图片】看JK、看jk、看美女、看黑丝、看白丝、看诱惑、美女壁纸\n"
    "【视频】小姐姐视频、刷抖音、玉足视频、热舞视频、黑丝视频、白丝视频、甜妹视频、Jk视频\n"
    "注意：每分钟最多请求 5 次！"
)

# 使用频率限制存储（用户ID -> 时间戳列表）
usage_tracker = defaultdict(list)
RATE_LIMIT = 5  # 每分钟最多 5 次请求
TIME_WINDOW = 60  # 时间窗口为 60 秒

# 检查使用频率
def is_rate_limited(user_id):
    now = datetime.now()
    user_requests = usage_tracker[user_id]
    
    # 清理超过时间窗口的记录
    usage_tracker[user_id] = [t for t in user_requests if now - t < timedelta(seconds=TIME_WINDOW)]
    
    # 检查请求次数是否超过限制
    if len(usage_tracker[user_id]) >= RATE_LIMIT:
        return True
    
    # 添加当前请求时间
    usage_tracker[user_id].append(now)
    return False

# 获取媒体的函数
def get_media(api_url):
    try:
        url_with_param = f"{api_url}&t={int(time.time())}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cache-Control": "no-cache"
        }
        response = requests.get(url_with_param, headers=headers, allow_redirects=True, stream=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'image' in content_type:
                response.raw.decode_content = True
                return 'image', response.raw
            elif 'video' in content_type or response.url.endswith(('.mp4', '.mov', '.avi')):
                return 'video', response.url
            else:
                return None, None
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching media: {e}")
        return None, None

# 处理 Webhook 请求
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data(as_text=True)
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid request', 400

# 处理群组加入
@bot.chat_member_handler()
def handle_chat_member_update(chat_member):
    new_status = chat_member.new_chat_member.status
    old_status = chat_member.old_chat_member.status
    chat_id = chat_member.chat.id
    
    if chat_member.new_chat_member.user.id == bot.get_me().id:
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator']:
            bot.send_message(chat_id, HELP_MESSAGE)

# 处理文本消息
@bot.message_handler(content_types=['text'])
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.strip()

    # 检查频率限制
    if is_rate_limited(user_id):
        bot.reply_to(message, "冲太快啦，每分钟最多 5 次，请稍等再试！")
        return

    if text in ["羊羊图库", "图库列表"]:
        bot.send_message(chat_id, HELP_MESSAGE)
    elif text in IMAGE_API_DICT:
        api_url = IMAGE_API_DICT[text]
        media_type, result = get_media(api_url)
        
        if media_type == 'image' and result:
            bot.send_photo(chat_id, photo=result, caption=f"老色批别冲啦！")
        elif media_type is None:
            bot.reply_to(message, "抱歉，获取图片失败，请稍后再试！")
    elif text in VIDEO_API_DICT:
        api_url = VIDEO_API_DICT[text]
        media_type, result = get_media(api_url)
        
        if media_type == 'video' and result:
            bot.send_video(chat_id, video=result, caption=f"老色批别冲啦！")
        elif media_type is None:
            bot.reply_to(message, "抱歉，获取视频失败，请稍后再试！")

# Vercel 入口函数
def handler(request):
    return app(request.environ, request.start_response)

if __name__ == '__main__':
    # 设置 Webhook（仅需运行一次）
    webhook_url = "https://your-vercel-app.vercel.app/" + TOKEN  # 替换为你的 Vercel 域名
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    app.run(host='0.0.0.0', port=3000)