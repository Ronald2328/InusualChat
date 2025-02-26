// Escucha cuando se instala la extensión
chrome.runtime.onInstalled.addListener(() => {
    // Inicializa la configuración
    chrome.storage.sync.set({
      enabled: true,
      allowedDomains: ["*"] // Puedes cambiar a dominios específicos, por ejemplo: ["example.com", "anotherdomain.org"]
    });
  });
  
  // Escucha los mensajes desde content.js o popup.js
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "checkIfEnabled") {
      const url = new URL(sender.tab.url);
      const domain = url.hostname;
      
      chrome.storage.sync.get(["enabled", "allowedDomains"], (data) => {
        if (data.enabled && (data.allowedDomains.includes("*") || data.allowedDomains.includes(domain))) {
          sendResponse({enabled: true});
        } else {
          sendResponse({enabled: false});
        }
      });
      return true; // Indica que la respuesta será asincrónica
    }
  });