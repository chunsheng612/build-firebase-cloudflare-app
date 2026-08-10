# Firebase + Cloudflare 新手上線 Skill

這個 Codex Skill 會把一句產品想法、設計稿或既有前端，整理成可以上線的半成品產品：

- 保留原本的前端設計
- 視需要加入 Firebase 登入與班級資料
- 自動產生並檢查 Firestore／Storage Security Rules
- 將前端發布到 Cloudflare
- 優先使用免費、簡單、適合班級的做法
- 讓第一次使用 Codex 或 AI agent 的人，不必操作終端機

## 最簡單的安裝方式

把下面這句貼到 Codex：

> 請使用 $skill-installer，從 https://github.com/chunsheng612/build-firebase-cloudflare-app/tree/main/build-firebase-cloudflare-app 安裝這個 Skill。

安裝後重新開始一個 Codex 任務，Skill 會放在：

```text
~/.codex/skills/build-firebase-cloudflare-app
```

如果有自訂 `CODEX_HOME`，路徑會是：

```text
$CODEX_HOME/skills/build-firebase-cloudflare-app
```

## 開始使用

安裝後，用日常語句描述想做的東西即可。例如：

> 幫我做一個班級作品牆。學生用 Google 登入後可以交作品連結，老師可以精選或移除，完成後幫我發布。

或把現有設計／專案交給 Codex：

> 請保留這個設計，把它變成可以登入、儲存資料並上線的網站。

Codex 會先完成可逆的本機工作。需要連接 Firebase 或 Cloudflare 時，只會請你在官方登入頁完成登入；不會要求你把密碼、驗證碼、權杖或私鑰貼進聊天。

## 進階安裝

熟悉終端機的使用者也可以執行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo chunsheng612/build-firebase-cloudflare-app \
  --path build-firebase-cloudflare-app
```

## 安全原則

- 外來專案會先當作不可信內容檢查；建置與測試應在沒有雲端帳號憑證的隔離環境執行。
- Firebase／Cloudflare 登入只走官方瀏覽器頁面。
- Firestore 與 Storage 預設拒絕未授權存取，班級檔案預設只有本人與老師可以讀取。
- 不會默默建立付費資源、改 DNS、刪除部署或覆寫正式環境祕密。
- 初學者模式預設不啟用 Firebase Storage；作品可先用連結方式提交。

完整安全回報方式請見 [SECURITY.md](SECURITY.md)。

## 授權

[MIT License](LICENSE)
