# yiwks.com 自动化运维脚本

## generate_blog_post.py

每日自动生成锁具科普文章并发布到 yiwks.com/blog/

### 依赖
- Python 3.9+
- requests (`pip install requests`)
- 系统已安装 git，并在 `~/yiwks.com` 目录下配置好 GitHub SSH 密钥
- Kimi API Key 设置到环境变量 `KIMI_API_KEY`

### 手动运行
```bash
cd ~/yiwks.com
export KIMI_API_KEY=sk-xxxx
python3 scripts/generate_blog_post.py
```

### 设置每日定时任务（macOS launchd / Linux cron）

#### macOS launchd
创建 `~/Library/LaunchAgents/com.yiwks.bloggen.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yiwks.bloggen</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/liu/yiwks.com/scripts/generate_blog_post.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>KIMI_API_KEY</key>
        <string>sk-xxxx</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/liu/yiwks.com</string>
    <key>StandardOutPath</key>
    <string>/Users/liu/yiwks.com/scripts/bloggen.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/liu/yiwks.com/scripts/bloggen.error.log</string>
</dict>
</plist>
```
然后执行：
```bash
launchctl load ~/Library/LaunchAgents/com.yiwks.bloggen.plist
```

#### Linux cron
```bash
0 9 * * * cd /Users/liu/yiwks.com && KIMI_API_KEY=sk-xxxx /usr/bin/python3 scripts/generate_blog_post.py >> scripts/bloggen.log 2>&1
```

### 注意事项
- 每次运行会消耗一定 Kimi API 费用，建议先手动测试几篇确认质量稳定后再开 cron
- 可以在 `TOPICS` 列表中增加更多科普主题，避免重复
- 如需保证每天不重复，可以在脚本中增加"已生成日期"记录
