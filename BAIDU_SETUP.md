# yiwks.com 百度统计 + 百度站长平台设置指南

## 一、百度统计

1. 访问 https://tongji.baidu.com
2. 用百度账号登录（如果没有需要手机号注册）
3. 点击"新增网站"
4. 填写网站域名：`yiwks.com`，网站名称："金钥匙开锁店"
5. 行业类目选择"居民服务"或"商务服务"
6. 提交后系统会生成一段统计代码，其中包含一串 32 位的 ID

示例代码：
```html
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?0123456789abcdef0123456789abcdef";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();
</script>
```

把 `hm.js?后面` 的 32 位字符串复制出来，这就是你的百度统计 ID。

## 二、百度搜索资源平台（站长平台）

1. 访问 https://ziyuan.baidu.com
2. 用同一个百度账号登录
3. 点击"用户中心" → "站点管理" → "添加网站"
4. 输入网站：`https://yiwks.com`
5. 选择验证方式：
   - **HTML 标签验证**：复制系统给的 `<meta name="baidu-site-verification" content="xxxx" />` 标签
   - 或者选择 **CNAME 验证**（推荐，更稳定）

## 三、一键插入到 yiwks.com

获取到百度统计 ID 和站长验证标签后，在本地执行：

```bash
cd ~/yiwks.com
export BAIDU_ID=0123456789abcdef0123456789abcdef
export BAIDU_VERIFY='<meta name="baidu-site-verification" content="xxxxxx" />'
python3 scripts/insert_baidu_analytics.py --stats-id "$BAIDU_ID" --verify-tag "$BAIDU_VERIFY"
```

然后提交部署：
```bash
git add .
git commit -m "seo: add Baidu Tongji and site verification"
git push origin main
```

Cloudflare Pages 会自动重新部署。

## 四、提交站点地图

百度站长平台验证通过后，进入"网站支持" → "sitemap"，提交：
```
https://yiwks.com/sitemap.xml
```

同时在百度统计中也可以设置自定义事件跟踪，如拨号、微信弹窗、在线预约按钮点击等。

## 五、常见问题

- **百度统计代码插入后没数据**：Cloudflare Pages 默认使用国外节点，部分国内爬虫/统计脚本可能被拦截。建议在 Cloudflare 开启"中国大陆优化"或配置国内 CDN。
- **验证失败**：HTML 标签验证需要等待 Cloudflare Pages 重新部署完成后才能验证。
