// Saves selected text whenever user selects something on a webpage
document.addEventListener("mouseup", () => {
  const selected = window.getSelection()?.toString()?.trim();
  if (selected && selected.length > 10) {
    chrome.storage.local.set({ selectedText: selected });
  }
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (msg.type === "GET_SELECTION") {
    reply({ text: window.getSelection()?.toString()?.trim() || "" });
  }
  return true;
});
