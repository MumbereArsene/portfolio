const nav = document.querySelector("[data-nav]");
const toggle = document.querySelector("[data-nav-toggle]");
const scrim = document.querySelector("[data-nav-scrim]");
const closeBtn = document.querySelector("[data-nav-close]");

function isNavOpen() {
    return document.body.classList.contains("is-nav-open");
}

function setNavOpen(open) {
    if (!nav || !toggle) {
        return;
    }
    document.body.classList.toggle("is-nav-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (window.matchMedia("(max-width: 980px)").matches) {
        nav.setAttribute("aria-hidden", open ? "false" : "true");
    } else {
        nav.removeAttribute("aria-hidden");
    }
}

if (toggle && nav) {
    setNavOpen(false);
    toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        setNavOpen(!isNavOpen());
    });
    if (closeBtn) {
        closeBtn.addEventListener("click", () => setNavOpen(false));
    }
    if (scrim) {
        scrim.addEventListener("click", () => setNavOpen(false));
    }
    nav.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => setNavOpen(false));
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setNavOpen(false);
        }
    });
    window.addEventListener("resize", () => {
        if (!window.matchMedia("(max-width: 980px)").matches) {
            setNavOpen(false);
        }
    });
}

document.querySelectorAll(".toast").forEach((toast) => {
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    }, 4200);
});
