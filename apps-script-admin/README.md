# 華昕網站文章後台

這個 Apps Script 網頁應用程式讓管理者透過表單維護網站文章，資料仍保存在既有 Google Sheet 的 `articles` 工作表，圖片保存到「華昕網站文章圖片」Google Drive 資料夾。

## 正式網址

- 網站入口：`https://www.hua-sin.com/admin.html`
- Apps Script：`https://script.google.com/macros/s/AKfycbyOt4cSPCDgfBZ09D-f9PVBioWCGjuPkSF0Z1bP2yTphjJpLIysljqyy1moSbndXKNr/exec`
- Apps Script 專案：`https://script.google.com/d/1HPTHs1K8nbrYiT31-Af7vuV_Skqpa5OgzI6lSiYM9H6CaNokyJX5mtfZ/edit`

## 權限

部署設定為 `MYSELF` / `USER_DEPLOYING`，只有部署者本人能進入後台。第一次開啟時，Google 會要求授權讀寫試算表與 Drive；完成一次即可。

## 更新部署

修改完成後，以這個資料夾的 `.clasp.json` 與 `.claspignore` 同步。正式部署 ID：

`AKfycbyOt4cSPCDgfBZ09D-f9PVBioWCGjuPkSF0Z1bP2yTphjJpLIysljqyy1moSbndXKNr`

後續更新應重新部署到同一個 ID，讓既有後台網址保持不變。
