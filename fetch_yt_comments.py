import os
import requests
import json
import re
from datetime import datetime, timezone, timedelta

# ================= 配置区 =================
BASE_DIR = "docs"
API_KEY = os.environ.get('YOUTUBE_API_KEY')
tz_utc_8 = timezone(timedelta(hours=8))

# 版块排序与分类ID (YouTube API 标准分类)
CATEGORIES = [
    {"name": "📰 新闻前十 (News)", "id": "25"},
    {"name": "🔥 最热前十 (Trending)", "id": None},
    {"name": "🎵 音乐前十 (Music)", "id": "10"},
    {"name": "🎬 影视前十 (Movies)", "id": "1"},
    {"name": "💖 粉丝热推 (Entertainment)", "id": "24"}
]
# ==========================================

def clean_uppercase(text):
    """正则替换：将长度>=2的纯大写单词转换为小写，保留正常的首字母大写"""
    return re.sub(r'\b[A-Z]{2,}\b', lambda x: x.group().lower(), text)

def fetch_category_videos(category_id):
    """获取指定版块的前十热门视频"""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": "US",
        "maxResults": 10,
        "key": API_KEY
    }
    if category_id:
        params["videoCategoryId"] = category_id
        
    try:
        res = requests.get(url, params=params, timeout=15).json()
        return res.get('items', [])
    except Exception as e:
        print(f"❌ 视频列表获取失败: {e}")
        return []

def fetch_top_comments(video_id):
    """获取该视频的高赞前排评论，进行过滤并转换大写"""
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&order=relevance&maxResults=60&key={API_KEY}"
    comments = []
    try:
        res = requests.get(url, timeout=10).json()
        if 'items' in res:
            for item in res['items']:
                snippet = item['snippet']['topLevelComment']['snippet']
                raw_text = snippet['textDisplay']
                
                if len(raw_text.split()) > 6 and 'href=' not in raw_text:
                    cleaned_text = clean_uppercase(raw_text)
                    comments.append({
                        'author': snippet['authorDisplayName'],
                        'avatar': snippet['authorProfileImageUrl'],
                        'text': cleaned_text,
                        'likes': int(snippet.get('likeCount', 0)),
                        'published': snippet['publishedAt']
                    })
    except Exception:
        pass
        
    comments.sort(key=lambda x: x['likes'], reverse=True)
    return comments[:30]

def save_daily_vibe(daily_data, now_obj):
    """生成带有双重折叠、且内嵌原版聊天气泡UI的HTML"""
    year_str, month_str = str(now_obj.year), str(now_obj.month)
    target_dir = os.path.join(BASE_DIR, year_str, month_str)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"{now_obj.year}_{now_obj.month}_{now_obj.day}_{now_obj.strftime('%H%M')}.html"
    html_path = os.path.join(target_dir, filename)
    now_str = now_obj.strftime("%Y-%m-%d %H:%M")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daily English Vibe</title>
    <style>
        :root {{ --bg: #f2f2f7; --card: #ffffff; --text: #1c1e21; --muted: #8e8e93; --accent: #007aff; --bubble: #e5e5ea; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px 10px 50px 10px; }}
        
        .nav-back {{ padding: 15px; text-align: center; background: var(--card); border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .nav-back a {{ text-decoration: none; color: white; background: #ff0000; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }}
        /* --- 一级折叠：版块 --- */
        .category-details {{ margin-bottom: 15px; background: var(--bg); }}
        .category-summary {{ background: var(--card); padding: 16px 20px; border-radius: 16px; font-size: 1.2rem; font-weight: 800; cursor: pointer; list-style: none; box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; align-items: center; justify-content: space-between; color: #333; }}
        .category-summary::-webkit-details-marker {{ display: none; }}
        .category-details[open] > .category-summary {{ border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-bottom: 1px solid #eee; color: var(--accent); }}
        /* --- 二级折叠：视频列表 --- */
        .video-details {{ background: var(--card); margin-bottom: 2px; }}
        .video-details:last-child {{ border-bottom-left-radius: 16px; border-bottom-right-radius: 16px; margin-bottom: 0; }}
        .video-summary {{ padding: 15px 20px; font-size: 0.95rem; font-weight: 600; cursor: pointer; list-style: none; display: flex; gap: 12px; align-items: center; border-bottom: 1px solid #f9f9f9; }}
        .video-summary::-webkit-details-marker {{ display: none; }}
        .mini-thumb {{ width: 60px; height: 34px; border-radius: 4px; object-fit: cover; flex-shrink: 0; background: #eee; }}
        .mini-title {{ display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.3; color: #444; }}
        .video-details[open] > .video-summary {{ background: #f8f9fa; }}
        /* --- 展开后的原版 UI --- */
        .expanded-content {{ padding: 20px 0; background: var(--bg); border-bottom: 2px solid #ddd; }}
        
        .video-card {{ background: var(--card); border-radius: 24px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin: 0 15px 25px 15px; }}
        .video-thumb {{ width: 100%; height: auto; display: block; aspect-ratio: 16/9; object-fit: cover; }}
        .video-info {{ padding: 20px; }}
        .v-channel {{ font-size: 0.85rem; color: var(--muted); font-weight: 600; text-transform: uppercase; margin-bottom: 6px; display: block; }}
        .v-title {{ font-size: 1.15rem; font-weight: 700; margin: 0 0 15px 0; line-height: 1.4; }}
        .v-actions {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f0f0f0; padding-top: 15px; }}
        .timestamp {{ font-size: 0.85rem; color: var(--muted); font-weight: 500; }}
        .btn-play {{ background: #ff0000; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 700; }}
        
        .chat-container {{ padding: 0 15px; display: flex; flex-direction: column; gap: 20px; }}
        .chat-message {{ display: flex; gap: 12px; align-items: flex-start; }}
        .avatar {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: #ddd; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .message-content {{ flex: 1; min-width: 0; }}
        .message-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px; padding-left: 2px; }}
        .author {{ font-size: 0.85rem; color: var(--muted); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%; }}
        .likes {{ font-size: 0.75rem; color: var(--accent); font-weight: 700; background: #e0f0ff; padding: 2px 8px; border-radius: 10px; }}
        .bubble {{ background: var(--card); padding: 12px 16px; border-radius: 2px 18px 18px 18px; font-size: 1.05rem; line-height: 1.5; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); word-wrap: break-word; }}
        .empty-state {{ text-align: center; color: var(--muted); padding: 20px; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="nav-back"><a href="../../index.html">🔙 返回日历枢纽</a></div>
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 25px; color: #333;">📅 {now_obj.strftime("%Y-%m-%d")}</h2>
"""
    for cat in CATEGORIES:
        cat_name = cat["name"]
        videos = daily_data.get(cat_name, [])
        if not videos: continue
            
        html_content += f'\n        <details class="category-details">\n'
        if "新闻" in cat_name:
            html_content = html_content.replace('<details class="category-details">', '<details class="category-details" open>')
            
        html_content += f'            <summary class="category-summary"><span>{cat_name}</span> <span>⬇️</span></summary>\n'
        
        for v in videos:
            v_title, v_channel, v_thumb, v_url, comments = v['title'], v['channel'], v['thumb'], v['url'], v['comments']
            html_content += f'            <details class="video-details">\n'
            html_content += f'                <summary class="video-summary"><img src="{v_thumb}" class="mini-thumb" loading="lazy"><span class="mini-title">{v_title}</span></summary>\n'
            html_content += f'                <div class="expanded-content">\n'
            html_content += f"""                    <div class="video-card">
                        <a href="{v_url}" target="_blank"><img src="{v_thumb}" class="video-thumb" alt="Thumbnail" loading="lazy"></a>
                        <div class="video-info">
                            <span class="v-channel">{v_channel}</span>
                            <h2 class="v-title" style="font-size:1.1rem;">{v_title}</h2>
                            <div class="v-actions">
                                <span class="timestamp">更新于: {now_str}</span>
                                <a href="{v_url}" target="_blank" class="btn-play">▶ 原片</a>
                            </div>
                        </div>
                    </div>\n"""
                    
            html_content += f'                    <div class="chat-container">\n'
            if not comments:
                html_content += '                        <div class="empty-state">该视频暂无高价值长评论。</div>\n'
            else:
                for c in comments:
                    likes_str = f"{c['likes']/1000:.1f}k" if c['likes'] >= 1000 else str(c['likes'])
                    html_content += f"""                        <div class="chat-message">
                            <img src="{c['avatar']}" class="avatar" alt="avatar" loading="lazy">
                            <div class="message-content">
                                <div class="message-header">
                                    <span class="author">{c['author']}</span>
                                    <span class="likes">❤️ {likes_str}</span>
                                </div>
                                <div class="bubble">{c['text']}</div>
                            </div>
                        </div>\n"""
            html_content += f'                    </div>\n'
            html_content += f'                </div>\n'
            html_content += f'            </details>\n'
            
        html_content += f'        </details>\n'
    html_content += """    </div>\n</body>\n</html>"""
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 语料已归档: {html_path}")

def generate_index():
    """纯日历枢纽生成器 + 前端手动抓取控制台"""
    archive_data = {}
    if os.path.exists(BASE_DIR):
        years = [d for d in os.listdir(BASE_DIR) if d.isdigit()]
        for year in years:
            archive_data[year] = {}
            months = [d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()]
            for month in months:
                archive_data[year][month] = {}
                files = sorted([f for f in os.listdir(os.path.join(BASE_DIR, year, month)) if f.endswith('.html')], reverse=True)
                for file in files:
                    try:
                        parts = file.replace(".html", "").split('_')
                        if len(parts) >= 4:
                            day = parts[2]
                            time_str = f"{parts[3][:2]}:{parts[3][2:4]}"
                            file_path = f"{year}/{month}/{file}"
                            # 区分是自动生成的 Top50 还是手动抓取的 Custom
                            title = "📌 单集精读" if "custom" in file else "全美 Top 50 深度阅读"
                            
                            if day not in archive_data[year][month]:
                                archive_data[year][month][day] = []
                            
                            archive_data[year][month][day].append({
                                "time": time_str,
                                "path": file_path,
                                "title": title
                            })
                    except Exception:
                        pass
                        
    json_data = json.dumps(archive_data)
    
    # 使用 .replace() 注入数据，避免大段前端代码中的大括号冲突
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YouTube 语料日历枢纽</title>
    <style>
        :root { --bg: #f5f5f7; --text: #333; --muted: #888; --primary: #ff0000; --border: #e0e0e0; --card: #fff; }
        body, html { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); margin: 0; padding: 0; color: var(--text); }
        .container { max-width: 600px; margin: 0 auto; padding-bottom: 20px; }
        
        /* --- 新增：手动抓取输入栏 UI --- */
        .manual-fetch-bar { background: var(--card); padding: 12px 15px; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 20; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .fetch-input { flex: 1; padding: 10px 15px; border: 1px solid #ccc; border-radius: 20px; font-size: 14px; outline: none; background: #f9f9f9; transition: border 0.2s; }
        .fetch-input:focus { border-color: var(--primary); background: #fff; }
        .settings-btn { background: none; border: none; font-size: 20px; cursor: pointer; padding: 5px; }
        
        /* --- 设置面板模态框 --- */
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; justify-content: center; align-items: center; padding: 20px; }
        .modal-content { background: var(--card); border-radius: 16px; padding: 20px; width: 100%; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .modal-title { margin: 0 0 15px 0; font-size: 18px; font-weight: bold; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; box-sizing: border-box; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; }
        .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
        .btn { padding: 8px 16px; border-radius: 8px; border: none; font-size: 14px; font-weight: bold; cursor: pointer; }
        .btn-cancel { background: #eee; color: #333; }
        .btn-save { background: var(--primary); color: #fff; }
        
        /* 日历区与原本样式 */
        .controls { background: var(--bg); padding: 15px 20px; display: flex; justify-content: center; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); }
        .control-btn { background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: 8px 12px; font-size: 14px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
        .control-btn:active { opacity: 0.8; transform: scale(0.95); }
        .select-box { padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 15px; background: #fff; outline: none; font-weight: bold; cursor: pointer; }
        .calendar-wrapper { background: var(--card); padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .weekdays { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: bold; font-size: 13px; color: var(--muted); margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }
        .days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
        .day-cell { aspect-ratio: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 16px; font-weight: 600; border-radius: 10px; cursor: pointer; position: relative; transition: all 0.2s; }
        .day-cell.empty { visibility: hidden; }
        .day-cell.has-news { color: var(--text); }
        .day-cell.no-news { color: #ccc; }
        .day-cell.selected { background: #ffe5e5; border: 1px solid var(--primary); color: var(--primary); font-weight: bold; }
        .day-cell.today { background: #f0f0f0; color: #333; }
        .dot { width: 5px; height: 5px; background-color: var(--primary); border-radius: 50%; position: absolute; bottom: 6px; display: none; }
        .day-cell.has-news .dot { display: block; }
        .news-section { padding: 0 15px; }
        .news-item { background: var(--card); border-radius: 14px; padding: 18px 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); border-left: 4px solid var(--primary); transition: all 0.2s; }
        .news-item:active { transform: scale(0.98); background: #fafafa; }
        .news-time { font-size: 15px; font-weight: bold; flex-shrink: 0; color: var(--primary); }
        .news-title { font-size: 14px; color: #555; margin-left: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; flex: 1; font-weight: 500; }
        .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; background: var(--card); border-radius: 14px; }
        
        #loadingBar { height: 3px; background: var(--primary); width: 0%; transition: width 0.3s; position: absolute; top: 0; left: 0; z-index: 30; }
    </style>
</head>
<body>
    <div id="loadingBar"></div>
    <div class="manual-fetch-bar">
        <input type="text" id="ytUrlInput" class="fetch-input" placeholder="粘贴 YouTube 链接，回车生成..." autocomplete="off">
        <button class="settings-btn" onclick="openSettings()">⚙️</button>
    </div>

    <div class="modal-overlay" id="settingsModal">
        <div class="modal-content">
            <h3 class="modal-title">本地配置中心</h3>
            <p style="font-size:12px; color:#888; margin-top:-10px; margin-bottom:15px;">密钥仅保存在您的浏览器本地，不会上传到任何第三方服务器。</p>
            <div class="form-group">
                <label>YouTube API Key</label>
                <input type="password" id="cfgYtKey" placeholder="AIzaSy...">
            </div>
            <div class="form-group">
                <label>GitHub Personal Access Token</label>
                <input type="password" id="cfgGhToken" placeholder="ghp_...">
            </div>
            <div class="form-group">
                <label>GitHub 用户名</label>
                <input type="text" id="cfgGhOwner" value="moodHappy" placeholder="例如: moodHappy">
            </div>
            <div class="form-group">
                <label>GitHub 仓库名</label>
                <input type="text" id="cfgGhRepo" placeholder="例如: youtube-vibe">
            </div>
            <div class="modal-actions">
                <button class="btn btn-cancel" onclick="closeSettings()">取消</button>
                <button class="btn btn-save" onclick="saveSettings()">保存配置</button>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="controls">
            <button class="control-btn" id="prevBtn">&lt;</button>
            <select class="select-box" id="yearSelect"></select>
            <select class="select-box" id="monthSelect">
                <option value="1">01月</option><option value="2">02月</option><option value="3">03月</option>
                <option value="4">04月</option><option value="5">05月</option><option value="6">06月</option>
                <option value="7">07月</option><option value="8">08月</option><option value="9">09月</option>
                <option value="10">10月</option><option value="11">11月</option><option value="12">12月</option>
            </select>
            <button class="control-btn" id="nextBtn">&gt;</button>
            <button class="control-btn" id="todayBtn">今天</button>
        </div>
        <div class="calendar-wrapper">
            <div class="weekdays"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div>
            <div class="days-grid" id="daysGrid"></div>
        </div>
        <div class="news-section"><div id="newsList"></div></div>
    </div>

    <script>
        // ================= 1. 日历逻辑 =================
        const archiveData = REPLACEME_JSON_DATA;
        const today = new Date();
        let currentYear = today.getFullYear();
        let currentMonth = today.getMonth() + 1;
        let selectedDay = today.getDate();
        let selectedYear = currentYear;
        let selectedMonth = currentMonth;
        
        const yearSelect = document.getElementById('yearSelect');
        const monthSelect = document.getElementById('monthSelect');
        const daysGrid = document.getElementById('daysGrid');
        const newsList = document.getElementById('newsList');

        function initSelects() {
            const years = Object.keys(archiveData).map(Number).sort((a, b) => b - a);
            if (!years.includes(currentYear)) years.unshift(currentYear);
            years.forEach(y => { const opt = document.createElement('option'); opt.value = y; opt.textContent = y + ' 年'; yearSelect.appendChild(opt); });
            yearSelect.value = currentYear; monthSelect.value = currentMonth;
        }

        function renderCalendar(year, month) {
            daysGrid.innerHTML = '';
            const firstDay = new Date(year, month - 1, 1).getDay();
            const startDay = firstDay === 0 ? 7 : firstDay;
            const daysInMonth = new Date(year, month, 0).getDate();
            
            for (let i = 1; i < startDay; i++) { const emptyCell = document.createElement('div'); emptyCell.className = 'day-cell empty'; daysGrid.appendChild(emptyCell); }
            
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : {};
            
            for (let day = 1; day <= daysInMonth; day++) {
                const cell = document.createElement('div'); cell.className = 'day-cell'; cell.textContent = day;
                const dot = document.createElement('div'); dot.className = 'dot'; cell.appendChild(dot);
                
                if (monthData[day]) cell.classList.add('has-news'); else cell.classList.add('no-news');
                if (year === today.getFullYear() && month === today.getMonth() + 1 && day === today.getDate()) cell.classList.add('today');
                if (year === selectedYear && month === selectedMonth && day === selectedDay) cell.classList.add('selected');
                
                cell.addEventListener('click', () => { selectedYear = year; selectedMonth = month; selectedDay = day; renderCalendar(year, month); renderNews(year, month, day); });
                daysGrid.appendChild(cell);
            }
        }

        function renderNews(year, month, day) {
            newsList.innerHTML = '';
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : null;
            const dayData = monthData ? monthData[day] : null;
            
            if (dayData && dayData.length > 0) {
                dayData.forEach(news => {
                    const a = document.createElement('a'); a.href = news.path; a.className = 'news-item';
                    // 用颜色区分手动抓取
                    const titleStyle = news.title.includes("单集") ? 'color: var(--primary); font-weight: bold;' : '';
                    a.innerHTML = `<span class="news-time">${news.time}</span><span class="news-title" style="${titleStyle}">${news.title} ➔</span>`;
                    newsList.appendChild(a);
                });
            } else {
                newsList.innerHTML = '<div class="empty-state">当日暂无归档记录，去外面看看吧 👀</div>';
            }
        }

        yearSelect.addEventListener('change', (e) => renderCalendar(parseInt(e.target.value), parseInt(monthSelect.value)));
        monthSelect.addEventListener('change', (e) => renderCalendar(parseInt(yearSelect.value), parseInt(e.target.value)));
        document.getElementById('prevBtn').addEventListener('click', () => { let m = parseInt(monthSelect.value) - 1; let y = parseInt(yearSelect.value); if (m < 1) { m = 12; y--; yearSelect.value = y; } monthSelect.value = m; renderCalendar(y, m); });
        document.getElementById('nextBtn').addEventListener('click', () => { let m = parseInt(monthSelect.value) + 1; let y = parseInt(yearSelect.value); if (m > 12) { m = 1; y++; yearSelect.value = y; } monthSelect.value = m; renderCalendar(y, m); });
        document.getElementById('todayBtn').addEventListener('click', () => { selectedYear = today.getFullYear(); selectedMonth = today.getMonth() + 1; selectedDay = today.getDate(); yearSelect.value = selectedYear; monthSelect.value = selectedMonth; renderCalendar(selectedYear, selectedMonth); renderNews(selectedYear, selectedMonth, selectedDay); });

        initSelects(); renderCalendar(currentYear, currentMonth); renderNews(currentYear, currentMonth, selectedDay);

        // ================= 2. 纯前端抓取与提交逻辑 =================
        const ytUrlInput = document.getElementById('ytUrlInput');
        const modal = document.getElementById('settingsModal');
        const loadingBar = document.getElementById('loadingBar');

        function openSettings() {
            document.getElementById('cfgYtKey').value = localStorage.getItem('YT_API_KEY') || '';
            document.getElementById('cfgGhToken').value = localStorage.getItem('GH_TOKEN') || '';
            document.getElementById('cfgGhOwner').value = localStorage.getItem('GH_OWNER') || 'moodHappy';
            document.getElementById('cfgGhRepo').value = localStorage.getItem('GH_REPO') || '';
            modal.style.display = 'flex';
        }
        function closeSettings() { modal.style.display = 'none'; }
        function saveSettings() {
            localStorage.setItem('YT_API_KEY', document.getElementById('cfgYtKey').value.trim());
            localStorage.setItem('GH_TOKEN', document.getElementById('cfgGhToken').value.trim());
            localStorage.setItem('GH_OWNER', document.getElementById('cfgGhOwner').value.trim());
            localStorage.setItem('GH_REPO', document.getElementById('cfgGhRepo').value.trim());
            closeSettings();
            alert('配置已本地保存！');
        }

        // 解析任何 YouTube 链接提取 Video ID
        function extractVideoId(url) {
            const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/;
            const match = url.match(regExp);
            return (match && match[2].length === 11) ? match[2] : null;
        }

        ytUrlInput.addEventListener('keypress', async function (e) {
            if (e.key === 'Enter') {
                const url = ytUrlInput.value.trim();
                const videoId = extractVideoId(url);
                if (!videoId) return alert('❌ 无法识别的 YouTube 链接');
                
                const ytKey = localStorage.getItem('YT_API_KEY');
                const ghToken = localStorage.getItem('GH_TOKEN');
                const ghOwner = localStorage.getItem('GH_OWNER');
                const ghRepo = localStorage.getItem('GH_REPO');
                
                if (!ytKey || !ghToken || !ghOwner || !ghRepo) {
                    alert('请先点击齿轮⚙️配置 API Keys！');
                    openSettings();
                    return;
                }

                loadingBar.style.width = '10%';
                ytUrlInput.disabled = true;

                try {
                    // 1. 请求视频信息
                    loadingBar.style.width = '30%';
                    const vRes = await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id=${videoId}&key=${ytKey}`);
                    const vData = await vRes.json();
                    if (!vData.items || vData.items.length === 0) throw new Error("视频不存在或无权限");
                    const video = vData.items[0];

                    // 2. 请求评论区
                    loadingBar.style.width = '50%';
                    const cRes = await fetch(`https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId=${videoId}&order=relevance&maxResults=60&key=${ytKey}`);
                    const cData = await cRes.json();
                    let comments = [];
                    if (cData.items) {
                        for (let item of cData.items) {
                            const snippet = item.snippet.topLevelComment.snippet;
                            const text = snippet.textDisplay;
                            if (text.split(' ').length > 6 && !text.includes('href=')) {
                                comments.push({
                                    author: snippet.authorDisplayName,
                                    avatar: snippet.authorProfileImageUrl,
                                    text: text.replace(/\b[A-Z]{2,}\b/g, match => match.toLowerCase()), // 简单大写转小写
                                    likes: parseInt(snippet.likeCount || 0)
                                });
                            }
                        }
                    }
                    comments.sort((a, b) => b.likes - a.likes);
                    comments = comments.slice(0, 30);

                    // 3. 在浏览器中渲染【基础版】HTML模板
                    loadingBar.style.width = '70%';
                    const htmlOutput = generateBaseHTMLString(video, comments);

                    // 4. 推送到 GitHub
                    loadingBar.style.width = '90%';
                    const now = new Date();
                    const year = now.getFullYear();
                    const month = now.getMonth() + 1;
                    const day = now.getDate();
                    const hhmm = String(now.getHours()).padStart(2, '0') + String(now.getMinutes()).padStart(2, '0');
                    const filename = `${year}_${month}_${day}_${hhmm}_custom.html`;
                    
                    // 注意：GitHub API 路径，如果你的静态页面放在根目录 docs/ 下
                    const filePath = `docs/${year}/${month}/${filename}`;
                    
                    const ghRes = await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/${filePath}`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `token ${ghToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            message: `Add custom video: ${video.snippet.title}`,
                            content: btoa(unescape(encodeURIComponent(htmlOutput))) // 解决中文 Base64 编码问题
                        })
                    });

                    if (!ghRes.ok) throw new Error(await ghRes.text());

                    loadingBar.style.width = '100%';
                    alert('🎉 抓取并推送成功！刷新页面即可看到新添加的单集记录。');
                    ytUrlInput.value = '';
                    setTimeout(() => window.location.reload(), 1000);

                } catch (err) {
                    alert('❌ 操作失败: ' + err.message);
                    loadingBar.style.width = '0%';
                } finally {
                    ytUrlInput.disabled = false;
                }
            }
        });

        // 完全复刻的【基础版】排版生成器 (JS版本)
        function generateBaseHTMLString(video, comments) {
            const snippet = video.snippet;
            const v_title = snippet.title;
            const v_channel = snippet.channelTitle;
            const v_thumb = (snippet.thumbnails.maxres || snippet.thumbnails.high || snippet.thumbnails.default).url;
            const v_url = `https://www.youtube.com/watch?v=${video.id}`;
            const d = new Date();
            const now_str = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;

            let comments_html = "";
            for (let c of comments) {
                let likes_str = c.likes >= 1000 ? (c.likes / 1000).toFixed(1) + "k" : c.likes;
                comments_html += `
                <div class="chat-message">
                    <img src="${c.avatar}" class="avatar" alt="avatar" loading="lazy">
                    <div class="message-content">
                        <div class="message-header">
                            <span class="author">${c.author}</span>
                            <span class="likes">❤️ ${likes_str}</span>
                        </div>
                        <div class="bubble">${c.text}</div>
                    </div>
                </div>`;
            }

            return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>${v_title}</title>
    <style>
        :root { --bg: #f2f2f7; --card: #ffffff; --text: #1c1e21; --muted: #8e8e93; --accent: #007aff; --bubble: #e5e5ea; }
        body { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; text-align: left; -webkit-font-smoothing: antialiased; }
        .container { max-width: 600px; margin: 0 auto; padding: 0 0 50px 0; }
        .nav-back { padding: 15px; text-align: center; background: var(--card); position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .nav-back a { text-decoration: none; color: white; background: #ff0000; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
        .video-card { background: var(--card); border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 25px; }
        .video-thumb { width: 100%; height: auto; display: block; aspect-ratio: 16/9; object-fit: cover; }
        .video-info { padding: 20px; }
        .v-channel { font-size: 0.85rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: block; }
        .v-title { font-size: 1.25rem; font-weight: 700; margin: 0 0 15px 0; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .v-actions { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f0f0f0; padding-top: 15px; }
        .timestamp { font-size: 0.85rem; color: var(--muted); font-weight: 500; }
        .btn-play { background: #ff0000; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 700; }
        .chat-container { padding: 0 15px; display: flex; flex-direction: column; gap: 20px; }
        .chat-message { display: flex; gap: 12px; align-items: flex-start; }
        .avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: #ddd; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .message-content { flex: 1; min-width: 0; }
        .message-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px; padding-left: 2px; }
        .author { font-size: 0.85rem; color: var(--muted); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%; }
        .likes { font-size: 0.75rem; color: var(--accent); font-weight: 700; background: #e0f0ff; padding: 2px 8px; border-radius: 10px; }
        .bubble { background: var(--card); padding: 12px 16px; border-radius: 2px 18px 18px 18px; font-size: 1.05rem; line-height: 1.5; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); word-wrap: break-word; }
        .empty-state { text-align: center; color: var(--muted); padding: 40px 20px; }
    </style>
</head>
<body>
    <div class="nav-back"><a href="../../index.html">🔙 返回日历枢纽</a></div>
    <div class="container">
        <div class="video-card">
            <a href="${v_url}" target="_blank"><img src="${v_thumb}" class="video-thumb" alt="Thumbnail"></a>
            <div class="video-info">
                <span class="v-channel">${v_channel}</span>
                <h1 class="v-title">${v_title}</h1>
                <div class="v-actions">
                    <span class="timestamp">更新于: ${now_str}</span>
                    <a href="${v_url}" target="_blank" class="btn-play">▶ 原片</a>
                </div>
            </div>
        </div>
        <div class="chat-container">
            ${comments_html ? comments_html : '<div class="empty-state">暂无高价值长评论。</div>'}
        </div>
    </div>
</body>
</html>`;
        }
    </script>
</body>
</html>"""
    
    # 替换变量，避免使用 f-string 破坏 JS 代码中的花括号
    html_template = html_template.replace('REPLACEME_JSON_DATA', json_data)
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_template)
    print("🚀 首页日历 WebApp (含前端抓取模块) 已更新！")

def main():
    if not API_KEY:
        print("❌ 警告：未配置 YOUTUBE_API_KEY，跳过后端抓取。")
        generate_index()
        return
        
    print("🎬 开始抓取每日热门视频...")
    daily_data = {}
    
    for cat in CATEGORIES:
        cat_name = cat["name"]
        cat_id = cat["id"]
        print(f"  正在抓取版块: {cat_name}")
        
        videos_info = []
        videos = fetch_category_videos(cat_id)
        
        for v in videos:
            vid_id = v["id"]
            snippet = v["snippet"]
            
            thumbnails = snippet.get("thumbnails", {})
            v_thumb = thumbnails.get("maxres", thumbnails.get("high", thumbnails.get("default", {}))).get("url", "")
            
            comments = fetch_top_comments(vid_id)
            
            videos_info.append({
                "id": vid_id,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "thumb": v_thumb,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "comments": comments
            })
            
        daily_data[cat_name] = videos_info
        
    now = datetime.now(tz_utc_8)
    save_daily_vibe(daily_data, now)
    generate_index()

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    main()
