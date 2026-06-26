import os
import requests
import json
from datetime import datetime, timezone, timedelta

# ================= 配置区 =================
BASE_DIR = "docs"
API_KEY = os.environ.get('YOUTUBE_API_KEY')
tz_utc_8 = timezone(timedelta(hours=8))

# API 板块映射 (注意：YouTube API 的 chart 只有 mostPopular，分类通过 videoCategoryId 筛选)
# 新闻=25, 音乐=10, 最热=mostPopular(无分类), 粉丝热推(Gaming=20)
CATEGORIES = [
    {"name": "🔥 新闻前十", "id": "25", "chart": "mostPopular"},
    {"name": "🚀 最热前十", "id": None, "chart": "mostPopular"},
    {"name": "🎵 音乐前十", "id": "10", "chart": "mostPopular"},
    {"name": "🎮 粉丝热推", "id": "20", "chart": "mostPopular"}
]

def fetch_youtube_data():
    all_content = []
    print("🎬 正在从 YouTube 四大板块抓取数据...")
    
    for cat in CATEGORIES:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart={cat['chart']}&regionCode=US&maxResults=10&key={API_KEY}"
        if cat['id']:
            url += f"&videoCategoryId={cat['id']}"
            
        try:
            res = requests.get(url, timeout=10).json()
            if 'items' in res:
                all_content.append({"category": cat['name'], "items": res['items']})
        except Exception as e:
            print(f"❌ 获取 {cat['name']} 失败: {e}")
            
    return all_content

def save_daily_vibe(content_data, now_obj):
    year_str, month_str = str(now_obj.year), str(now_obj.month)
    target_dir = os.path.join(BASE_DIR, year_str, month_str)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"{now_obj.year}_{now_obj.month}_{now_obj.day}_YT.html"
    html_path = os.path.join(target_dir, filename)
    
    html_body = ""
    for cat in content_data:
        html_body += f"<h2 class='cat-title'>{cat['category']}</h2>"
        for item in cat['items']:
            title = item['snippet']['title']
            vid = item['id']
            html_body += f"""
            <a href="https://www.youtube.com/watch?v={vid}" target="_blank" class="news-item">
                <span class="news-title">{title}</span>
                <span class="news-arrow">▶</span>
            </a>
            """

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>YouTube 每日精选</title>
    <style>
        :root {{ --bg: #f5f5f7; --text: #1d1d1f; --primary: #ff0000; --card: #fff; }}
        body {{ font-family: -apple-system, sans-serif; background: var(--bg); padding: 20px; color: var(--text); }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .cat-title {{ font-size: 1.2rem; margin: 30px 0 15px 10px; color: var(--primary); }}
        .news-item {{ background: var(--card); border-radius: 12px; padding: 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 1px 4px rgba(0,0,0,0.05); }}
        .news-title {{ font-size: 14px; font-weight: 600; }}
        .news-arrow {{ color: var(--primary); font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 {now_obj.strftime('%Y-%m-%d')} 每日精选</h1>
        {html_body}
        <br><a href="../../index.html">🔙 返回首页</a>
    </div>
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 归档成功: {html_path}")

# (注：generate_index 逻辑保持你之前最稳健的“日历索引”版即可)