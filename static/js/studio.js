const menu = document.querySelector("[data-menu]");
const toggle = document.querySelector("[data-menu-toggle]");
const scrim = document.querySelector("[data-menu-scrim]");
const closeBtn = document.querySelector("[data-menu-close]");

function isMenuOpen() {
    return document.body.classList.contains("is-menu-open");
}

function setMenuOpen(open) {
    if (!menu || !toggle) {
        return;
    }
    document.body.classList.toggle("is-menu-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    menu.setAttribute("aria-hidden", open ? "false" : "true");
}

if (menu && toggle) {
    toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        setMenuOpen(!isMenuOpen());
    });
    if (closeBtn) {
        closeBtn.addEventListener("click", () => setMenuOpen(false));
    }
    if (scrim) {
        scrim.addEventListener("click", () => setMenuOpen(false));
    }
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setMenuOpen(false);
        }
    });
}

document.querySelectorAll("[data-check-all]").forEach((master) => {
    master.addEventListener("change", () => {
        master.closest("form").querySelectorAll('input[name="ids"]').forEach((box) => {
            box.checked = master.checked;
        });
    });
});

document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (event) => {
        if (!window.confirm(el.getAttribute("data-confirm"))) {
            event.preventDefault();
        }
    });
});

document.querySelectorAll(".toast").forEach((toast) => {
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity .4s ease";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
});

const categoryField = document.querySelector("#id_category");
const tagRoot = document.querySelector("#id_tags");
if (categoryField && tagRoot) {
    const boxes = tagRoot.querySelectorAll("input[data-categories]");
    const applyTags = (resetHidden) => {
        boxes.forEach((box) => {
            const allowed = (box.getAttribute("data-categories") || "").split(/\s+/).filter(Boolean);
            const show = !categoryField.value || allowed.includes(categoryField.value);
            const row = box.closest("div");
            if (row) {
                row.hidden = !show;
            }
            if (!show && resetHidden) {
                box.checked = false;
            }
        });
    };
    categoryField.addEventListener("change", () => applyTags(true));
    applyTags(false);
}
