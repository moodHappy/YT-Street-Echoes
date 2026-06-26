import os
import requests
import re
from datetime import datetime

# --- 配置区 ---
API_KEY = os.environ.get("YOUTUBE_API_KEY")
BASE_DIR = "docs"
REGION_CODE = "US"   # 默认抓取美区，语料质量更高
MAX_VIDEOS = 10      # 每个版块抓取前10个视频
MAX_COMMENTS = 5     # 每个视频抓取5条高赞评论，保持极简界面

# 版块排序与分类ID (YouTube API 标准分类)
# 新闻=25, 音乐=10, 影视=1, 娱乐(粉丝热推)=24, 最热=不传ID
CATEGORIES = [
    {"name": "📰 新闻前十", "id": "25"},
    {"name": "🔥 最热前十", "id": None}, 
    {"name": "🎵 音乐前十", "id": "10"},
    {"name": "🎬 影视前十", "id": "1"},
    {"name": "💖 粉丝热推", "id": "24"} 
]

def clean_uppercase(text):
    """
    正则替换：将长度>=2的纯大写单词转换为小写
    例如: "THIS IS GREAT" -> "this is great", 但 "I am" 保持不变
    """
    return re.sub(r'\b[A-Z]{2,}\b', lambda x: x.group().lower(), text)

def get_top_videos(category_id):
    """获取指定版块的最热视频"""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "chart": "mostPopular",
        "regionCode": REGION_CODE,
        "maxResults": MAX_VIDEOS,
        "key": API_KEY
    }
    if category_id:
        params["videoCategoryId"] = category_id
        
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
    
    return response.json().get("items", [])

def get_video_comments(video_id):
    """获取视频的热门评论"""
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": MAX_COMMENTS,
        "order": "relevance",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    
    # 处理评论区关闭或 API 限制的情况
    if response.status_code != 200:
        return ["(此视频已关闭评论区或无法获取)"]
        
    comments = []
    items = response.json().get("items", [])
    for item in items:
        raw_text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
        # 应用大写转小写规则，并去除换行符保持极简
        clean_text = clean_uppercase(raw_text).replace('\n', ' | ')
        comments.append(clean_text)
    
    return comments

def generate_daily_html(data_dict, today_str):
    """生成极简且支持双重折叠的 HTML"""
    
    # 极简 CSS 样式
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Vibe - {today_str}</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #222; line-height: 1.6; background: #fafafa; }}
        h1 {{ text-align: center; font-weight: 500; margin-bottom: 2rem; }}
        /* 一级折叠（版块） */
        .category-details {{ background: #fff; border-radius: 8px; margin-bottom: 1rem; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .category-summary {{ font-size: 1.2rem; font-weight: bold; cursor: pointer; outline: none; }}
        /* 二级折叠（视频） */
        .video-details {{ margin: 0.8rem 0 0.8rem 1rem; border-left: 3px solid #eee; padding-left: 1rem; }}
        .video-summary {{ font-size: 1rem; color: #0056b3; cursor: pointer; outline: none; margin-bottom: 0.5rem; }}
        /* 评论列表 */
        ul {{ margin: 0; padding-left: 1.2rem; color: #444; }}
        li {{ margin-bottom: 0.4rem; font-size: 0.95rem; }}
    </style>
</head>
<body>
    <h1>YouTube Daily Vibe - {today_str}</h1>
"""

    for category in CATEGORIES:
        cat_name = category["name"]
        videos = data_dict.get(cat_name, [])
        
        html_content += f'\n    <details class="category-details">\n'
        html_content += f'        <summary class="category-summary">{cat_name}</summary>\n'
        
        for vid in videos:
            title = vid["title"]
            video_url = f"https://youtu.be/{vid['id']}"
            html_content += f'        <details class="video-details">\n'
            # 视频标题作为第二层折叠的触发器
            html_content += f'            <summary class="video-summary">{title}</summary>\n'
            html_content += f'            <ul>\n'
            
            for comment in vid["comments"]:
                html_content += f'                <li>{comment}</li>\n'
            
            html_content += f'                <li><a href="{video_url}" target="_blank" style="font-size: 0.85rem; color: #888;">[Go to Video]</a></li>\n'
            html_content += f'            </ul>\n'
            html_content += f'        </details>\n'
            
        html_content += f'    </details>\n'

    html_content += "</body>\n</html>"
    return html_content

def update_hub_html(daily_dirs):
    """更新根目录的枢纽导航页"""
    daily_dirs.sort(reverse=True) # 日期倒序，最新的在最上面
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Archive Hub</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 600px; margin: 3rem auto; padding: 0 1rem; text-align: center; }
        ul { list-style: none; padding: 0; }
        li { margin: 1rem 0; }
        a { text-decoration: none; color: #1a73e8; font-size: 1.2rem; font-weight: bold; padding: 0.5rem 1rem; border: 1px solid #1a73e8; border-radius: 5px; display: inline-block; transition: 0.2s; }
        a:hover { background: #1a73e8; color: #fff; }
    </style>
</head>
<body>
    <h2>YouTube Comments Archive 🗂️</h2>
    <ul>
"""
    for d in daily_dirs:
        # d 类似 "2026/06/26"
        html_content += f'        <li><a href="{d}/index.html">{d}</a></li>\n'
        
    html_content += "    </ul>\n</body>\n</html>"
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    if not API_KEY:
        print("Error: YOUTUBE_API_KEY environment variable not set.")
        return

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    date_path = now.strftime("%Y/%m/%d")
    target_dir = os.path.join(BASE_DIR, date_path)
    
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"Start fetching data for {today_str}...")
    
    daily_data = {}
    
    # 按照设定的版块顺序抓取
    for category in CATEGORIES:
        cat_name = category["name"]
        cat_id = category["id"]
        print(f"Fetching {cat_name}...")
        
        videos_info = []
        videos = get_top_videos(cat_id)
        
        for v in videos:
            vid_id = v["id"]
            title = v["snippet"]["title"]
            comments = get_video_comments(vid_id)
            
            videos_info.append({
                "id": vid_id,
                "title": title,
                "comments": comments
            })
            
        daily_data[cat_name] = videos_info

    # 1. 生成今日的归档页面
    daily_html_path = os.path.join(target_dir, "index.html")
    with open(daily_html_path, "w", encoding="utf-8") as f:
        f.write(generate_daily_html(daily_data, today_str))
    print(f"Daily HTML generated at {daily_html_path}")

    # 2. 扫描 docs 目录，更新主导航页
    archive_paths = []
    for root, dirs, files in os.walk(BASE_DIR):
        if "index.html" in files and root != BASE_DIR:
            # 提取相对路径，例如 2026/06/26
            rel_path = os.path.relpath(root, BASE_DIR).replace("\\", "/")
            archive_paths.append(rel_path)
            
    update_hub_html(archive_paths)
    print("Hub HTML updated successfully.")

if __name__ == "__main__":
    main()
