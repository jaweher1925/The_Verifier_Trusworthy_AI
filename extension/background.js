// Adds a right-click menu option to verify selected text
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id:       "verify",
    title:    "🛡️ Verify with The Verifier",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === "verify" && info.selectionText) {
    chrome.storage.local.set({ selectedText: info.selectionText.trim() });
    chrome.action.openPopup();
  }
});
