import os
import requests
import json
from datetime import datetime, timezone, timedelta

# ================= 配置区 =================
BASE_DIR = "docs"
API_KEY = os.environ.get('YOUTUBE_API_KEY')
tz_utc_8 = timezone(timedelta(hours=8))
# ==========================================

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
    """获取高赞前排评论"""
    print("💬 正在潜入评论区提取神回复...")
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&order=relevance&maxResults=60&key={API_KEY}"
    comments = []
    try:
        res = requests.get(url, timeout=10).json()
        if 'items' in res:
            for item in res['items']:
                snippet = item['snippet']['topLevelComment']['snippet']
                text = snippet['textDisplay']
                
                # 过滤太短或含链接的垃圾评论
                if len(text.split()) > 6 and 'href=' not in text:
                    comments.append({
                        'author': snippet['authorDisplayName'],
                        'avatar': snippet['authorProfileImageUrl'],
                        'text': text,
                        'likes': int(snippet.get('likeCount', 0))
                    })
    except Exception as e:
        print(f"❌ 评论获取失败: {e}")
        
    comments.sort(key=lambda x: x['likes'], reverse=True)
    return comments[:30]

def save_daily_vibe(video, comments, now_obj):
    """按年月归档生成聊天气泡页面"""
    year_str, month_str = str(now_obj.year), str(now_obj.month)
    target_dir = os.path.join(BASE_DIR, year_str, month_str)
    
    # 建立 年文件夹 -> 月文件夹 的层级结构
    os.makedirs(target_dir, exist_ok=True)
    
    # 每天的归档文件
    filename = f"{now_obj.year}_{now_obj.month}_{now_obj.day}_{now_obj.strftime('%H%M')}.html"
    html_path = os.path.join(target_dir, filename)
    
    v_title = video['snippet']['title']
    v_channel = video['snippet']['channelTitle']
    v_thumb = video['snippet']['thumbnails']['high']['url']
    v_url = f"https://www.youtube.com/watch?v={video['id']}"
    now_str = now_obj.strftime("%Y-%m-%d %H:%M")
    
    comments_html = ""
    for c in comments:
        likes_str = f"{c['likes']/1000:.1f}k" if c['likes'] >= 1000 else str(c['likes'])
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
    <title>💬 {v_title}</title>
    <style>
        :root {{ --bg: #f2f2f7; --card: #ffffff; --text: #1c1e21; --muted: #8e8e93; --accent: #ff0000; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0 0 50px 0; }}
        
        .nav-back {{ padding: 15px; text-align: center; background: var(--card); border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 10; }}
        .nav-back a {{ text-decoration: none; color: var(--card); background: var(--accent); padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 8px rgba(255,0,0,0.2); }}
        
        .video-card {{ background: var(--card); border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 25px; }}
        .video-thumb {{ width: 100%; height: auto; display: block; aspect-ratio: 16/9; object-fit: cover; }}
        .video-info {{ padding: 20px; }}
        .v-channel {{ font-size: 0.85rem; color: var(--muted); font-weight: 600; text-transform: uppercase; margin-bottom: 6px; display: block; }}
        .v-title {{ font-size: 1.25rem; font-weight: 700; margin: 0 0 15px 0; line-height: 1.4; }}
        .v-actions {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f0f0f0; padding-top: 15px; }}
        .timestamp {{ font-size: 0.85rem; color: var(--muted); font-weight: 500; }}
        
        .chat-container {{ padding: 0 15px; display: flex; flex-direction: column; gap: 20px; }}
        .chat-message {{ display: flex; gap: 12px; align-items: flex-start; }}
        .avatar {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .message-content {{ flex: 1; min-width: 0; }}
        .message-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px; padding-left: 2px; }}
        .author {{ font-size: 0.85rem; color: var(--muted); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%; }}
        .likes {{ font-size: 0.75rem; color: var(--accent); font-weight: 700; background: #ffe5e5; padding: 2px 8px; border-radius: 10px; }}
        .bubble {{ background: var(--card); padding: 12px 16px; border-radius: 2px 18px 18px 18px; font-size: 1.05rem; line-height: 1.5; box-shadow: 0 2px 8px rgba(0,0,0,0.03); word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="nav-back"><a href="../../index.html">🔙 返回日历枢纽</a></div>
    <div class="container">
        <div class="video-card">
            <a href="{v_url}" target="_blank"><img src="{v_thumb}" class="video-thumb"></a>
            <div class="video-info">
                <span class="v-channel">{v_channel}</span>
                <h1 class="v-title">{v_title}</h1>
                <div class="v-actions">
                    <span class="timestamp">更新于: {now_str}</span>
                </div>
            </div>
        </div>
        <div class="chat-container">
            {comments_html if comments_html else '<div style="text-align:center;color:#888;">暂无数据</div>'}
        </div>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ 语料已归档: {html_path}")

def generate_index():
    # ---------- 1. 递归扫描获取日历数据 ----------
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
                        if len(parts) == 4:
                            day = parts[2]
                            time_str = f"{parts[3][:2]}:{parts[3][2:]}"
                            file_path = f"{year}/{month}/{file}"
                            
                            page_title = "Daily Vibe"
                            try:
                                with open(os.path.join(BASE_DIR, year, month, file), 'r', encoding='utf-8') as f_html:
                                    content = f_html.read(2000)
                                    start = content.find('<title>')
                                    end = content.find('</title>')
                                    if start != -1 and end != -1:
                                        # 过滤掉标题里的 Emoji
                                        raw_title = content[start+7:end]
                                        page_title = raw_title.replace("💬 ", "")
                            except:
                                pass
                            
                            if day not in archive_data[year][month]:
                                archive_data[year][month][day] = []
                                
                            archive_data[year][month][day].append({
                                "time": time_str,
                                "path": file_path,
                                "title": page_title
                            })
                    except Exception:
                        pass
    json_data = json.dumps(archive_data)

    # ---------- 2. 纯日历 WebApp 单页模板 ----------
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YouTube 语料日历枢纽</title>
    <style>
        :root {{ --bg: #f5f5f7; --text: #333; --muted: #888; --primary: #ff0000; --border: #e0e0e0; --card: #fff; }}
        body, html {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); margin: 0; padding: 0; color: var(--text); }}
        
        .container {{ max-width: 600px; margin: 0 auto; padding-bottom: 20px; }}
        
        .controls {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); padding: 15px 20px; display: flex; justify-content: center; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; box-shadow: 0 1px 5px rgba(0,0,0,0.02); }}
        .control-btn {{ background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: 8px 12px; font-size: 14px; cursor: pointer; font-weight: bold; transition: all 0.2s; }}
        .control-btn:active {{ opacity: 0.8; transform: scale(0.95); }}
        .select-box {{ padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 15px; background: #fff; outline: none; font-weight: bold; cursor: pointer; }}
        
        .calendar-wrapper {{ background: var(--card); padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
        .weekdays {{ display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: bold; font-size: 13px; color: var(--muted); margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }}
        .days-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }}
        
        .day-cell {{ aspect-ratio: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 16px; font-weight: 600; border-radius: 10px; cursor: pointer; position: relative; transition: all 0.2s; }}
        .day-cell.empty {{ visibility: hidden; }}
        .day-cell.has-news {{ color: var(--text); }}
        .day-cell.no-news {{ color: #ccc; }}
        
        .day-cell.selected {{ background: #ffe5e5; border: 1px solid var(--primary); color: var(--primary); font-weight: bold; }}
        .day-cell.today {{ background: #f0f0f0; color: #333; }}
        .dot {{ width: 5px; height: 5px; background-color: var(--primary); border-radius: 50%; position: absolute; bottom: 6px; display: none; }}
        .day-cell.has-news .dot {{ display: block; }}
        
        .news-section {{ padding: 0 15px; }}
        .news-item {{ background: var(--card); border-radius: 14px; padding: 18px 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); overflow: hidden; border-left: 4px solid var(--primary); transition: all 0.2s; }}
        .news-item:active {{ transform: scale(0.98); background: #fafafa; }}
        .news-time {{ font-size: 15px; font-weight: bold; flex-shrink: 0; color: var(--primary); }}
        .news-title {{ font-size: 14px; color: #555; margin-left: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; flex: 1; font-weight: 500; }}
        .empty-state {{ text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; background: var(--card); border-radius: 14px; }}
    </style>
</head>
<body>
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
            <div class="weekdays">
                <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span>
            </div>
            <div class="days-grid" id="daysGrid"></div>
        </div>

        <div class="news-section">
            <div id="newsList"></div>
        </div>
    </div>

    <script>
        const archiveData = DATA_PLACEHOLDER;
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

        function initSelects() {{
            const years = Object.keys(archiveData).map(Number).sort((a, b) => b - a);
            if (!years.includes(currentYear)) years.unshift(currentYear);
            
            years.forEach(y => {{
                const opt = document.createElement('option');
                opt.value = y; opt.textContent = y + ' 年';
                yearSelect.appendChild(opt);
            }});
            yearSelect.value = currentYear;
            monthSelect.value = currentMonth;
        }}

        function renderCalendar(year, month) {{
            daysGrid.innerHTML = '';
            const firstDay = new Date(year, month - 1, 1).getDay();
            const startDay = firstDay === 0 ? 7 : firstDay;
            const daysInMonth = new Date(year, month, 0).getDate();
            
            for (let i = 1; i < startDay; i++) {{
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-cell empty';
                daysGrid.appendChild(emptyCell);
            }}
            
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : {{}};
            
            for (let day = 1; day <= daysInMonth; day++) {{
                const cell = document.createElement('div');
                cell.className = 'day-cell';
                cell.textContent = day;
                
                const dot = document.createElement('div');
                dot.className = 'dot';
                cell.appendChild(dot);
                
                if (monthData[day]) cell.classList.add('has-news');
                else cell.classList.add('no-news');
                
                if (year === today.getFullYear() && month === today.getMonth() + 1 && day === today.getDate()) {{
                    cell.classList.add('today');
                }}
                
                if (year === selectedYear && month === selectedMonth && day === selectedDay) {{
                    cell.classList.add('selected');
                }}
                
                cell.addEventListener('click', () => {{
                    selectedYear = year; selectedMonth = month; selectedDay = day;
                    renderCalendar(year, month);
                    renderNews(year, month, day);
                }});
                
                daysGrid.appendChild(cell);
            }}
        }}

        function renderNews(year, month, day) {{
            newsList.innerHTML = '';
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : null;
            const dayData = monthData ? monthData[day] : null;
            
            if (dayData && dayData.length > 0) {{
                dayData.forEach(news => {{
                    const a = document.createElement('a');
                    a.href = news.path; a.className = 'news-item';
                    a.innerHTML = `<span class="news-time">${{news.time}}</span><span class="news-title">${{news.title}} ➔</span>`;
                    newsList.appendChild(a);
                }});
            }} else {{
                newsList.innerHTML = '<div class="empty-state">当日暂无归档记录，去外面看看吧 👀</div>';
            }}
        }}

        yearSelect.addEventListener('change', (e) => renderCalendar(parseInt(e.target.value), parseInt(monthSelect.value)));
        monthSelect.addEventListener('change', (e) => renderCalendar(parseInt(yearSelect.value), parseInt(e.target.value)));

        document.getElementById('prevBtn').addEventListener('click', () => {{
            let m = parseInt(monthSelect.value) - 1; let y = parseInt(yearSelect.value);
            if (m < 1) {{ m = 12; y--; yearSelect.value = y; }}
            monthSelect.value = m; renderCalendar(y, m);
        }});

        document.getElementById('nextBtn').addEventListener('click', () => {{
            let m = parseInt(monthSelect.value) + 1; let y = parseInt(yearSelect.value);
            if (m > 12) {{ m = 1; y++; yearSelect.value = y; }}
            monthSelect.value = m; renderCalendar(y, m);
        }});

        document.getElementById('todayBtn').addEventListener('click', () => {{
            selectedYear = today.getFullYear(); selectedMonth = today.getMonth() + 1; selectedDay = today.getDate();
            yearSelect.value = selectedYear; monthSelect.value = selectedMonth;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        }});

        // 初始化并渲染
        initSelects();
        renderCalendar(currentYear, currentMonth);
        renderNews(currentYear, currentMonth, selectedDay);
    </script>
</body>
</html>"""

    # 替换预留的 JSON 数据位
    final_html = html_template.replace("DATA_PLACEHOLDER", json_data)
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    print("🚀 首页日历 WebApp 已更新！")

if __name__ == "__main__":
    # 确保根目录存在
    os.makedirs(BASE_DIR, exist_ok=True)
    
    if API_KEY:
        video = fetch_trending_video()
        if video:
            comments = fetch_top_comments(video['id'])
            if comments:
                now = datetime.now(tz_utc_8)
                save_daily_vibe(video, comments, now)
    else:
        print("⚠️ 警告：未配置 YOUTUBE_API_KEY，跳过数据抓取，仅重新生成首页日历。")
        
    generate_index()