import os
import requests
import json
from datetime import datetime, timezone, timedelta

# 从 GitHub Secrets 读取 API Key
API_KEY = os.environ.get('YOUTUBE_API_KEY')
OUTPUT_FILE = "index.html"
tz_utc_8 = timezone(timedelta(hours=8))

def fetch_trending_video():
    """获取全美当日排名第一的热门视频"""
    print("🎬 正在寻找今日全美最热视频...")
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=1&key={API_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        if 'items' in res and len(res['items']) > 0:
            return res['items'][0]
    except Exception as e:
        print(f"❌ 视频获取失败: {e}")
    return None

def fetch_top_comments(video_id):
    """获取该视频的高赞前排评论，并进行过滤"""
    print("💬 正在潜入评论区提取神回复...")
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&order=relevance&maxResults=60&key={API_KEY}"
    comments = []
    try:
        res = requests.get(url, timeout=10).json()
        if 'items' in res:
            for item in res['items']:
                snippet = item['snippet']['topLevelComment']['snippet']
                text = snippet['textDisplay']
                
                # 过滤条件：太短的不要（通常是纯表情或废话），带有 href 链接的不要（通常是广告）
                if len(text.split()) > 6 and 'href=' not in text:
                    comments.append({
                        'author': snippet['authorDisplayName'],
                        'avatar': snippet['authorProfileImageUrl'],
                        'text': text,
                        'likes': int(snippet.get('likeCount', 0)),
                        'published': snippet['publishedAt']
                    })
    except Exception as e:
        print(f"❌ 评论获取失败: {e}")
        
    # 按点赞数从高到低排序，只取前 30 条精华
    comments.sort(key=lambda x: x['likes'], reverse=True)
    return comments[:30]

def generate_html(video, comments):
    print("✨ 正在渲染聊天气泡排版...")
    
    if not video:
        print("未获取到视频数据，停止生成。")
        return
        
    v_title = video['snippet']['title']
    v_channel = video['snippet']['channelTitle']
    v_thumb = video['snippet']['thumbnails']['high']['url']
    v_url = f"https://www.youtube.com/watch?v={video['id']}"
    now_str = datetime.now(tz_utc_8).strftime("%Y-%m-%d %H:%M")
    
    # 构建聊天气泡 HTML
    comments_html = ""
    for c in comments:
        # 格式化点赞数 (例如 1500 -> 1.5k)
        likes = c['likes']
        if likes >= 1000:
            likes_str = f"{likes/1000:.1f}k"
        else:
            likes_str = str(likes)
            
        comments_html += f"""
        <div class="chat-message">
            <img src="{c['avatar']}" class="avatar" alt="avatar" loading="lazy">
            <div class="message-content">
                <div class="message-header">
                    <span class="author">{c['author']}</span>
                    <span class="likes">❤️ {likes_str}</span>
                </div>
                <div class="bubble">{c['text']}</div>
            </div>
        </div>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daily English Vibe</title>
    <style>
        :root {{ --bg: #f2f2f7; --card: #ffffff; --text: #1c1e21; --muted: #8e8e93; --accent: #007aff; --bubble: #e5e5ea; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; text-align: left; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0 0 50px 0; }}
        
        /* 顶部视频卡片 */
        .video-card {{ background: var(--card); border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 25px; }}
        .video-thumb {{ width: 100%; height: auto; display: block; aspect-ratio: 16/9; object-fit: cover; }}
        .video-info {{ padding: 20px; }}
        .v-channel {{ font-size: 0.85rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: block; }}
        .v-title {{ font-size: 1.25rem; font-weight: 700; margin: 0 0 15px 0; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .v-actions {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f0f0f0; padding-top: 15px; }}
        .timestamp {{ font-size: 0.85rem; color: var(--muted); font-weight: 500; }}
        .btn-play {{ background: #ff0000; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 700; transition: opacity 0.2s; }}
        .btn-play:active {{ opacity: 0.8; }}
        
        /* 聊天气泡布局 */
        .chat-container {{ padding: 0 15px; display: flex; flex-direction: column; gap: 20px; }}
        .chat-message {{ display: flex; gap: 12px; align-items: flex-start; }}
        .avatar {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: #ddd; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        
        .message-content {{ flex: 1; min-width: 0; }}
        .message-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px; padding-left: 2px; }}
        .author {{ font-size: 0.85rem; color: var(--muted); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%; }}
        .likes {{ font-size: 0.75rem; color: var(--accent); font-weight: 700; background: #e0f0ff; padding: 2px 8px; border-radius: 10px; }}
        
        .bubble {{ background: var(--card); padding: 12px 16px; border-radius: 2px 18px 18px 18px; font-size: 1.05rem; line-height: 1.5; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); word-wrap: break-word; }}
        
        .empty-state {{ text-align: center; color: var(--muted); padding: 40px 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="video-card">
            <a href="{v_url}" target="_blank">
                <img src="{v_thumb}" class="video-thumb" alt="Thumbnail">
            </a>
            <div class="video-info">
                <span class="v-channel">{v_channel}</span>
                <h1 class="v-title">{v_title}</h1>
                <div class="v-actions">
                    <span class="timestamp">更新于: {now_str}</span>
                    <a href="{v_url}" target="_blank" class="btn-play">▶ 原片</a>
                </div>
            </div>
        </div>
        
        <div class="chat-container">
            {comments_html if comments_html else '<div class="empty-state">今日暂无高价值长评论。</div>'}
        </div>
    </div>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"🎉 成功生成！已抓取 {len(comments)} 条爆梗评论。")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ 致命错误：未找到 YOUTUBE_API_KEY 环境变量！请在 GitHub Secrets 中配置。")
        exit(1)
        
    video = fetch_trending_video()
    if video:
        comments = fetch_top_comments(video['id'])
        generate_html(video, comments)
