export function init_overlay() {
    let overlay = document.querySelector("#click-for-overlay");
    if (overlay !== null) {
        overlay.onclick = function () { show_overlay(true); }
    }
    document.querySelector("#comic-page-overlay").onclick = function () { show_overlay(false); }
}

function show_overlay(show) {
    document.querySelector("#comic-page-overlay").hidden = !show;
}
