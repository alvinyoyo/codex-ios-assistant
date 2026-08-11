# Lina：GitHub Actions → IPA → Sideloadly

這個流程從 Lina 官方公開原始碼的固定 commit 編譯 iPhone App，產出未簽章
`Lina-unsigned.ipa`。GitHub Actions 不會接觸 Apple ID；最後由 Windows 上的
Sideloadly 使用使用者自己的免費 Apple ID 簽章並安裝。

## 下載 IPA

1. 開啟 GitHub 儲存庫的 **Actions** 頁籤。
2. 選擇 **Build Lina IPA**。
3. 開啟最新且呈綠色勾勾的執行紀錄。
4. 在 **Artifacts** 下載 `Lina-unsigned-IPA`。
5. 解壓縮 ZIP，取得 `Lina-unsigned.ipa` 與 SHA-256 檔。

## 用 Sideloadly 安裝

1. 用 USB 連接 iPhone，保持解鎖並確認已信任這部電腦。
2. 開啟 Sideloadly，選擇 `Lina-unsigned.ipa`。
3. 輸入自己的 Apple ID；密碼與兩步驟驗證只能由使用者本人處理。
4. 不要移除 App Extensions；Lina 的 `LinaIntents.appex` 是捷徑動作所需元件。
5. 安裝後若 iPhone 要求信任，前往「設定 → 一般 → VPN 與裝置管理」完成信任。
6. 免費 Apple ID 的側載 App 通常約七天後需要重新簽章安裝。

## 安全與限制

- 原始碼固定在 `0dba26ca52cbfd2acf84e748b870c4e66752d8d0`，避免上游分支變動時靜默換碼。
- IPA 是未簽章產物；Sideloadly 必須同時簽署主 App 與 Intents extension。
- 工作流程不保存 Apple ID、密碼、兩步驟驗證碼、裝置 UDID 或簽章憑證。
- 如果 Sideloadly 顯示不支援 iCloud entitlement，可啟用其移除不支援 entitlement
  的選項，但不要刪除 App Extensions。
