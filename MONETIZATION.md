# Slide Vault — 变现接入清单（Monetization Setup）

本仓库已把变现能力接入代码层。**2026-11-20 起，所有站点级 ID 统一由根目录 `site_config.json` 管理**，不再散落在 HTML 和生成器里。

| 能力 | 实现位置 | 状态 |
|---|---|---|
| Google AdSense（自动广告） | `tools/gen_pages.py` 详情页 `<head>` + `index.html` `<head>` + 根目录 `ads.txt` | ✅ 已填发布商 ID `ca-pub-6730005742175239` |
| SEO 长尾词 + FAQ 结构化数据 | `tools/gen_pages.py` | ✅ 已生效 |
| 联盟营销（Canva / Envato） | `site_config.json` → `tools/apply_config.py` → 首页与详情页 `.affiliate-box` | ⚠️ **待填真实联盟链接** |
| Cloudflare Web Analytics | `site_config.json` → `tools/apply_config.py` 注入 beacon | ⚠️ **待填 token**（未填则不加载脚本） |
| 邮件钩子「领免费模板合集」 | 详情页 + 首页 `.lead-magnet` → `/subscribe` | ✅ 已生效（发信能力见第 4 节） |

---

## 1. 填 ID（只改一个文件）

编辑根目录 `site_config.json`：

```json
{
  "affiliate": {
    "canva_url": "https://www.canva.com/affiliates/…你的专属链接",
    "envato_url": "https://1.envato.market/…你的 Impact 追踪 ID"
  },
  "analytics": {
    "cloudflare_web_analytics_token": "主站专属 token",
    "google_site_verification": "可选：GSC 的 HTML 标签验证值"
  }
}
```

然后：

```bash
python3 tools/apply_config.py           # 应用到全部 HTML
python3 tools/apply_config.py --check   # 校验：占位符 / 页脚 nofollow / 首页 JSON-LD
git add -A && git commit && git push     # GitHub Actions 会自动重跑这两个脚本
```

**未配置时不会留坏链**：联盟位会退回到 Canva / Envato 官方普通链接，并去掉 `rel="sponsored"`（因为此时不是付费链接）；没填 token 就不注入统计脚本。配置好后重跑一次，会自动切换回带 `rel="sponsored noopener"` 的追踪链接。

> 注意：Cloudflare Web Analytics 的 token 要为主站单独创建，**不要复用** `tools.slidevaulte.com` 子域（那是 DrainCalc 的），否则两个项目的数据会混在一起。

## 2. 工作原理

- `tools/gen_pages.py` 的 `affiliate_slots()`、`tools/gen_blog.py`、`tools/gen_tool_pages.py` 都从 `site_config.json` 读取；重新生成页面不会把 `YOUR_...` 占位符带回来。
- `.github/workflows/deploy.yml` 在每次部署前依次执行 `fix_home.py` → `apply_config.py` → `apply_config.py --check`。校验不通过会直接阻断部署。
- `tools/fix_home.py` 从 `assets/templates.js` 重建首页 ItemList JSON-LD（扁平数组、列出全部模板）和静态 A–Z 内链索引，幂等可重复运行。

## 3. AdSense 上线步骤

1. 在 AdSense 后台「网站」添加 `slidevaulte.com` 并通过审核（首次需等 Google 审批，通常几天）。
2. 开启 **Auto Ads（自动广告）**——代码里只放了全局脚本，无需创建广告单元 ID。
3. `ads.txt` 已填好 `pub-6730005742175239`（最后一段 `f08c47fec0942fa0` 是 Google 权威 ID，保持不变）。
4. 想更可控时，再在 AdSense 后台建「展示广告」单元，把全局脚本替换为带 `data-ad-slot` 的 `<ins>` 单元。

⚠️ **合规**：切勿自己或教唆他人点击广告；自动广告已含「广告」标识，无需额外手动标注。

✅ **隐私政策页已就绪**：`/privacy/index.html` 已如实披露 Google AdSense / DoubleClick Cookie 及退出方式，与站点广告实际行为一致——这是 AdSense 审核的硬性要求，请勿再写「无广告 / 无追踪 Cookie」等矛盾表述。

## 4. 联盟链接合规

- 配置好真实联盟链接后，`apply_config.py` 会自动写入 `rel="sponsored noopener"`——这是 Google 对付费/联盟链接的强制要求。
- Canva / Envato 的联盟计划均为免费加入，按成交拿佣金，站点本身零成本。

## 5. 邮件「领合集」钩子

- 表单复用 `functions/subscribe.js`（数据存 Cloudflare D1，**不经过任何第三方**）。
- 已加 `source` 字段区分来源：`bundle_home`（首页）、`bundle_detail`（详情页）。
- **发信能力待补**：邮箱进来后目前只入库，要把「合集」真正发给用户，需接 Brevo 免费层 / MailerLite 或定期从 D1 导出列表群发。

`subscribe.js` 已做防御性兼容：表没有 `source` 列时自动回退到原两列写入。要记录来源，跑一次：

```bash
wrangler d1 execute slidevault_subs --remote --command \
  "ALTER TABLE subscribers ADD COLUMN source TEXT DEFAULT 'newsletter';"
```

## 6. 部署

```bash
git add -A
git commit -m "chore: site config + SEO fixes"
git push origin main        # GitHub Actions 自动部署到 Cloudflare Pages（约 2-3 分钟）
```

或手动：`wrangler pages deploy . --project-name slidevault-lite --branch main`

## 7. 验证

- 部署后打开任意详情页查看源代码：应含 `adsbygoogle`、`.affiliate-box`（无 `YOUR_`）、`.lead-magnet`、`FAQPage`。
- 首页 `id="tpl-list"` 的 JSON-LD 应是**扁平数组**且列出全部模板。
- `python3 tools/apply_config.py --check` 输出 `OK`。
- Search Console 里对新增/修改页「请求编入索引」，观察收录数变化；`tools/indexnow.py` 可向 Bing / Yandex 批量提交 sitemap URL。

---

## 附：2026-11-20 修复记录

- 联盟占位符集中到 `site_config.json`；未配置时改用官方普通链接，消除全站坏链。
- 首页 `ItemList.itemListElement` 由嵌套数组（非法）改为扁平数组，并补全全部模板。
- 首页新增静态 A–Z 内链索引 + `<noscript>` 兜底，模板详情页不再只依赖 `app.js` 渲染。
- 全站页脚 `Drainage Calculators` 跨项目外链加 `rel="nofollow"`，三个生成器同步修改。
- 新增 `functions/_middleware.js` 做 `www → 非 www` 301（Pages `_redirects` 只能匹配路径，不能匹配 hostname）。若该规则线上未生效，需在 Cloudflare 后台加一条 zone 级 Redirect Rule。
- 线上 `robots.txt` 里 Cloudflare 注入的 AI 爬虫屏蔽段属于**平台层配置**，改仓库 `robots.txt` 无效，需到 Cloudflare 后台调整内容信号 / AI 爬虫设置。

*由 WorkBuddy 实现 · 2026-10-28 初版，2026-11-20 更新*
