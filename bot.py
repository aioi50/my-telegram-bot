import telebot
import requests
import time
import os  # 这行代码不要动
import random

# Telegram Bot API 令牌
TOKEN = os.getenv('TOKEN')  # 从环境变量读取 Token
bot = telebot.TeleBot(TOKEN)

# 图片 API 字典
IMAGE_API_DICT = {
    "看JK": "http://api.yujn.cn/api/jk.php?type=image",
    "看jk": "http://api.yujn.cn/api/jk.php?type=image",
    "看美女": "http://api.yujn.cn/api/ksxjj.php?type=image",
    "看黑丝": "http://api.yujn.cn/api/heisi.php?type=image",
    "看白丝": "http://api.yujn.cn/api/baisi.php?type=image",
    "看诱惑": "http://api.yujn.cn/api/yht.php?type=image",
    "美女壁纸": "http://api.yujn.cn/api/meinv.php?type=image"
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
    "JK视频": "http://api.yujn.cn/api/jksp.php?type=video",
    "jk视频": "http://api.yujn.cn/api/jksp.php?type=video"
}

# 提示信息
HELP_MESSAGE = (
    "🐑 羊羊图库已就位！发送「羊羊图库」查看指令列表\n"
    "📌 发送对应关键词即可获取内容：\n"
    "【图片】看JK、看jk、看美女、看黑丝、看白丝、看诱惑、美女壁纸\n"
    "【视频】小姐姐视频、刷抖音、玉足视频、热舞视频、黑丝视频、白丝视频、甜妹视频、Jk视频"
)

# 获取媒体的函数（支持图片流和视频 URL）
def get_media(api_url):
    try:
        # 添加随机参数避免缓存（例如加入随机数）
        random_seed = random.randint(1000, 9999)
        url_with_param = f"{api_url}&t={int(time.time())}&r={random_seed}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://example.com/",  # 模拟真实来源
            "Cache-Control": "no-cache"
        }
        
        # 设置超时和重试
        response = requests.get(
            url_with_param,
            headers=headers,
            allow_redirects=True,
            stream=True,
            timeout=10  # 10秒超时
        )
        
        if response.status_code == 200:
            final_url = response.url
            content_type = response.headers.get('Content-Type', '').lower()
            
            # 调试日志
            print(f"[DEBUG] 最终 URL: {final_url}")
            print(f"[DEBUG] Content-Type: {content_type}")
            
            if 'image' in content_type:
                response.raw.decode_content = True
                return 'image', response.raw
            elif 'video' in content_type or final_url.endswith(('.mp4', '.mov', '.avi')):
                return 'video', final_url
            else:
                print("无法识别的媒体类型")
                return None, None
        else:
            print(f"API 响应异常: HTTP {response.status_code}")
            return None, None
    except Exception as e:
        print(f"请求失败: {e}")
        return None, None

# 处理机器人被添加到群组的事件
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
    text = message.text.strip()

    # 检查是否触发提示关键词
    if text in ["羊羊图库", "图库列表"]:
        bot.send_message(chat_id, HELP_MESSAGE)
    # 检查是否触发图片关键词
    elif text in IMAGE_API_DICT:
        max_retries = 3  # 最大重试次数
        retry_count = 0
        
        while retry_count < max_retries:        
            api_url = IMAGE_API_DICT[text]
            media_type, result = get_media(api_url)
        
            if media_type == 'image' and result:
                try:
                    # 尝试发送视频
                    bot.send_photo(chat_id, photo=result, caption=f"少冲点吧你！")
                    return  # 成功则退出函数
                except Exception as e:
                    print(f"发送失败，开始重试: {e}")
                    retry_count += 1
                    time.sleep(1)  # 等待1秒再重试
            else:
                break  # 获取内容失败则退出循环
                
            bot.reply_to(message, "🚧 内容发送失败，请稍后重试")
            
    # 检查是否触发视频关键词
    elif text in VIDEO_API_DICT:
        max_retries = 3  # 最大重试次数
        retry_count = 0

        while retry_count < max_retries:
            api_url = VIDEO_API_DICT[text]
            media_type, result = get_media(api_url)
        
            if media_type == 'video' and result:
                try:
                    # 尝试发送视频
                    bot.send_video(chat_id, video=result, caption=f"少冲点吧你！")
                    return  # 成功则退出函数
                except Exception as e:
                    print(f"发送失败，开始重试: {e}")
                    retry_count += 1
                    time.sleep(1)  # 等待1秒再重试
            else:
                break  # 获取内容失败则退出循环
                
        bot.reply_to(message, "🚧 内容发送失败，请稍后重试")

# 启动机器人
bot.polling(none_stop=True)
