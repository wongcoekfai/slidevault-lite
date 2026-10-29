# Slide Vault — 变现接入清单（Monetization Setup）

本仓库已把四项变现能力接入代码层，**全部为占位符，需你填真实 ID 后部署才生效**：

| 能力 | 实现位置 | 状态 |
|---|---|---|
| Google AdSense（自动广告） | `tools/gen_pages.py` 详情页 `<head>` + `index.html` `<head>` + 根目录 `ads.txt` | ✅ 已填发布商 ID `ca-pub-6730005742175239` |
| SEO 长尾词 + FAQ 结构化数据 | `tools/gen_pages.py`（`<meta name="keywords">` + `FAQPage` JSON-LD，已随 16 个详情页重生） | ✅ 已生效 |
| 联盟营销（Canva / Envato） | 详情页与首页的 `.affiliate-box`（链接带 `rel="sponsored"`） | 代码已就位，待填联盟参数 |
| 邮件钩子「领免费模板合集」 | 详情页 + 首页的 `.lead-magnet` 表单 → 复用 `/subscribe` 接口（`source` 标记） | ✅ 已生效（发信能力见下） |

---

## 1. 替换占位符（共 3 类）

全局搜索下面这些字符串，全部替换成你的真实值：

- **`ca-pub-6730005742175239`**（已填，`tools/gen_pages.py` 头部、 `index.html` 头部、 `ads.txt`）
  → 来自 AdSense 后台「账号信息」的发布商 ID，账户状态 Open，可直接投放。
- **`YOUR_CANVA_AFF_PARAMS`**（2 处：详情页、首页）
  → Canva 联盟链接参数。先注册 [Canva Affiliates](https://www.canva.com/affiliates/)，拿到带你 tracking 的专属链接。
- **`YOUR_ENVATO_AFF_ID`**（2 处：详情页、首页）
  → Envato 联盟链接。先注册 [Envato Affiliate](https://envato.com/affiliate/)（经 Impact），拿到专属跳转链接。

> 提示：改完用 `grep -rn "XXXXXXXXXXXXXXXX\|YOUR_" .` 确认无遗漏占位符。

## 2. AdSense 上线步骤

1. 在 AdSense 后台「网站」添加 `slidevaulte.com` 并通过审核（首次需等 Google 审批，通常几天）。
2. 开启 **Auto Ads（自动广告）**——代码里只放了全局脚本，无需创建广告单元 ID，Google 自动选位。
3. `ads.txt` 已填好 `pub-6730005742175239`（最后一段 `f08c47fec0942fa0` 是 Google 权威 ID，保持不变）。AdSense 要求根目录有有效 ads.txt，否则广告可能不展示。
4. 想更可控时，再在 AdSense 后台建「展示广告」单元，把代码里的全局脚本替换为带 `data-ad-slot` 的 `<ins>` 单元。

⚠️ **合规**：切勿自己或教唆他人点击广告；自动广告已含「广告」标识，无需额外手动标注。

✅ **隐私政策页已就绪**：`/privacy/index.html` 已如实披露 Google AdSense / DoubleClick Cookie 及退出方式（opt-out 链接），与站点广告实际行为一致——这是 AdSense 审核的硬性要求，请勿再写「无广告 / 无追踪 Cookie」等矛盾表述。页脚已链接到该页。

## 3. 联盟链接合规

- 所有联盟 `<a>` 已加 `rel="sponsored noopener"`——这是 Google 对付费/联盟链接的强制要求，避免排名惩罚。
- Canva / Envato 的联盟计划均为免费加入，按成交拿佣金，站点本身零成本。

## 4. 邮件「领合集」钩子

- 表单复用现有 `functions/subscribe.js`（数据存 Cloudflare D1，**不经过任何第三方**）。
- 已加 `source` 字段区分来源：`bundle_home`（首页）、`bundle_detail`（详情页），便于后续区分引流质量。
- **发信能力待补**（项目原 todo）：邮箱进来后目前只入库，要把「合集」真正发给用户，需接 **Brevo 免费层 / MailerLite** 或定期从 D1 导出列表群发。在此之前，钩子正常收集线索，只是还没自动投递。

### D1 表结构（可选但推荐）

`subscribe.js` 已做**防御性兼容**：表没有 `source` 列时自动回退到原两列写入，订阅永不中断。要真正记录来源，跑一次：

```bash
wrangler d1 execute slidevault_subs --remote --command \
  "ALTER TABLE subscribers ADD COLUMN source TEXT DEFAULT 'newsletter';"
```

## 5. 部署

```bash
git add -A
git commit -m "feat: adsense + affiliate + lead-magnet + long-tail SEO"
git push origin main        # GitHub Actions 自动部署到 Cloudflare Pages（约 2-3 分钟）
```

或手动：`wrangler pages deploy . --project-name slidevault-lite --branch main`

## 6. 验证

- 部署后打开任意详情页，查看源代码应含 `adsbygoogle`、`affiliate-box`、`lead-magnet`、`FAQPage`、`name="keywords"`。
- Search Console 里重新「请求编入索引」几个详情页，观察 FAQ 富摘要与长尾词出词。
- AdSense 后台看「网站」状态变「正常」、出现展示/点击数据即跑通。

---
*由 WorkBuddy 实现 · 2026-10-28 · 改动文件：tools/gen_pages.py、index.html、assets/style.css、functions/subscribe.js、ads.txt（新增）、MONETIZATION.md（新增）*
