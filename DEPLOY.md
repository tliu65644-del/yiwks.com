# 金钥匙开锁店 · yiwks.com 部署交付文档

## 一、站点信息

| 项目 | 内容 |
|------|------|
| 域名 | https://yiwks.com |
| 网站类型 | 静态HTML（Cloudflare Pages托管） |
| 建站日期 | 2026-07-12 |

## 二、GitHub 仓库

```
仓库地址: https://github.com/tliu65644-del/yiwks.com
本地路径: ~/yiwks.com
```

### 如何修改网站内容：

**修改文字/报价：**
1. 打开对应页面的 index.html 文件
2. 找到要改的文字直接修改
3. 保存后 git push，Cloudflare自动部署

**各页面文件位置：**
```
/Users/liu/yiwks.com/
├── index.html              # 首页
├── services/index.html     # 服务项目
├── cases/index.html        # 施工案例
├── booking/index.html      # 在线预约（嵌入腾讯表单）
├── price/index.html        # 参考价格
├── about/index.html        # 关于我们
├── contact/index.html      # 联系我们
├── privacy/index.html      # 隐私协议
├── sitemap.xml             # 站点地图
├── robots.txt              # 爬虫规则
└── images/
    ├── store/              # 门店照片+资质
    └── cases/              # 施工案例图
```

**修改价格：** 编辑 price/index.html 里的价格表格

**修改电话：** 全局搜索 15605799786 替换

**更换图片：** 替换 images/ 目录下的图片文件（保持同名）

## 三、Cloudflare 配置

```
登录: https://dash.cloudflare.com
域名: yiwks.com
Pages项目: yiwks-com
```

### 当前状态：
- ✅ DNS代理：仅DNS（灰色云朵）
- ✅ SSL/TLS：自动（Full模式）
- ✅ 自动部署：GitHub推送后自动构建

### 15天后操作（重要）：
将DNS代理从灰色改为橙色云朵，开启CDN加速+安全防护

## 四、百度收录

已通过 ping 接口通知百度收录 https://yiwks.com/sitemap.xml

如需在百度站长平台手动提交：
1. 打开 https://ziyuan.baidu.com/
2. 添加站点 yiwks.com
3. 验证站点（推荐CNAME验证）
4. 提交sitemap：https://yiwks.com/sitemap.xml

## 五、AI搜索引擎覆盖

已覆盖平台（yiwks.com替换旧域名地址）：
- 百度文心
- 豆包
- Kimi
- DeepSeek
- 通义千问
- 元宝

## 六、在线预约表单

当前状态：待创建
需要你去 https://docs.qq.com/form 创建预约表单
创建后把嵌入链接发给我，我更新到 booking/index.html

## 七、服务器备份

本网站为静态页面，源码存储在GitHub：
https://github.com/tliu65644-del/yiwks.com

任何情况下只要GitHub在，网站就不会丢。如需迁移，克隆仓库后部署到任何静态托管即可。
