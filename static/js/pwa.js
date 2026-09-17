(() => {
    const button = document.querySelector("[data-pwa-install]");
    if (!button) {
        return;
    }

    const standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone;
    if (standalone) {
        button.hidden = true;
        return;
    }

    let deferredPrompt = null;

    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
    }

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredPrompt = event;
        button.hidden = false;
    });

    window.addEventListener("appinstalled", () => {
        deferredPrompt = null;
        button.hidden = true;
    });

    button.addEventListener("click", async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            await deferredPrompt.userChoice;
            deferredPrompt = null;
            return;
        }
        window.alert("Ouvre cette page dans Chrome ou Edge (ordinateur ou Android) pour installer l’app Atelier.");
    });
})();
