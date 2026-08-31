let page_info_json;
let infinite_scroll_div;
let earliest_comic_loaded = null;
let latest_comic_loaded = null;
let current_image = null;
let starting_anchor = null;
let num_pages_to_load = 5;
let initializing = true;
let loading_more_pages = false;
// If an image is within these many pixels of the top of the viewport (by percentage of current viewport height),
// it counts as being "viewed" for the purposes of determining the current image.
let viewed_page_top_margin_percentage = 0.30;
let load_next_pages_threshold = 1000;
let comic_base_dir = null;

export async function load_page(local_comic_base_dir) {
    comic_base_dir = local_comic_base_dir;
    initializing = true;
    await fetch_all_json_data();
    // If no pages to load, end early.
    if (page_info_json.length === 0) {
        document.getElementById("loading-infinite-scroll").innerHTML = "<h2>No comic images have been published yet.</h2>";
        document.getElementById("jump-to").hidden = true;
        document.getElementById("load-newer").hidden = true;
        return;
    }
    infinite_scroll_div = document.getElementById("infinite-scroll");
    load_and_go_to_page();
    document.getElementById("load-older-button").onclick = load_older_pages;
    document.getElementById("load-newer-button").onclick = load_newer_pages;
    window.onscroll = on_scroll;
    for (let link of document.getElementsByClassName("chapter-links")) {
        link.addEventListener("click", function () {
            let url = this.getAttribute("href");
            console.log(url);
            window.location.href = url;
            initializing = true;
            infinite_scroll_div.textContent = '';
            load_and_go_to_page();
            initializing = false;
        })
    }
    initializing = false;
}

async function fetch_all_json_data() {
    console.debug(`${comic_base_dir}/comic/page_info_list.json`);
    let response = await fetch(`${comic_base_dir}/comic/page_info_list.json`);
    console.log("Fetched page info list");
    let json;
    try {
        json = await response.json();
    } catch (e) {
        console.error(e);
        console.error(response.text());
        throw e;
    }
    page_info_json = json["pages"].filter(page => page["images"].length > 0);
}

function image_fragment(page_name, image_index) {
    return `${page_name}_${String(image_index + 1).padStart(2, "0")}`;
}

function load_and_go_to_page() {
    current_image = null;
    get_starting_page();
    load_newer_pages();
    go_to_anchor();
}

function get_starting_page() {
    earliest_comic_loaded = 0;
    latest_comic_loaded = -1;
    starting_anchor = null;
    if (!window.location.href.includes("#")) {
        return;
    }
    let fragment = decodeURIComponent(window.location.href.split("#")[1]);
    console.log("Loading fragment " + fragment);
    for (let i=0; i < page_info_json.length; i++) {
        console.log(page_info_json[i].page_name);
        let image_match = page_info_json[i].images.some(
            (_image, index) => image_fragment(page_info_json[i].page_name, index) === fragment
        );
        if (page_info_json[i].page_name === fragment || image_match) {
            console.log("Starting on page " + i);
            if (i !== 0) {
                document.getElementById("load-older").hidden = false;
            }
            earliest_comic_loaded = i;
            latest_comic_loaded = i - 1;
            starting_anchor = page_info_json[i].page_name === fragment
                ? image_fragment(page_info_json[i].page_name, 0)
                : fragment;
            return;
        }
    }
    console.log("Couldn't find page or image fragment named " + fragment);
}

function build_comic_div(page) {
    let node = document.createElement("div");
    node.className = "infinite-page";
    node.id = page["page_name"];

    page["images"].forEach((image, index) => {
        let link_node = document.createElement("a");
        link_node.className = "infinite-image-link";
        link_node.href = `${page["url"]}#comic-image-${index + 1}`;
        link_node.id = image_fragment(page["page_name"], index);

        let image_node = document.createElement("img");
        image_node.className = "infinite-page-image";
        console.log("Adding div for page " + page["page_name"]);
        image_node.src = image["url"];
        image_node.alt = image["alt_text"];
        image_node.title = image["title"];

        link_node.appendChild(image_node);
        node.appendChild(link_node);
    });
    return node;
}

function load_older_pages() {
    if (earliest_comic_loaded <= 0) {
        // No more pages to display
        return;
    }
    if (loading_more_pages)
        return;
    loading_more_pages = true;
    try {
        for (let i = 0; i < num_pages_to_load; i++) {
            earliest_comic_loaded--;

            let node = build_comic_div(page_info_json[earliest_comic_loaded]);
            infinite_scroll_div.insertBefore(node, infinite_scroll_div.firstChild);
            if (current_image !== null) {
                current_image += page_info_json[earliest_comic_loaded].images.length;
            }

            if (earliest_comic_loaded <= 0) {
                // No more pages to display
                document.getElementById("load-older").hidden = true;
                break;
            }
        }
    } finally {
        loading_more_pages = false;
    }
}

function load_newer_pages() {
    if (latest_comic_loaded + 1 >= page_info_json.length) {
        // No more pages to display
        return;
    }
    if (loading_more_pages)
        return;
    loading_more_pages = true;
    document.getElementById("loading-infinite-scroll").hidden = true;
    try {
        for (let i = 0; i < num_pages_to_load; i++) {
            latest_comic_loaded++;

            let node = build_comic_div(page_info_json[latest_comic_loaded]);
            infinite_scroll_div.appendChild(node);

            if (latest_comic_loaded + 1 >= page_info_json.length) {
                // No more pages to display
                document.getElementById("load-newer").hidden = true;
                document.getElementById("caught-up-notification").hidden = false;
                break;
            }
        }
        console.log("Done loading images");
    } finally {
        loading_more_pages = false;
    }
}

function go_to_anchor() {
    if (!window.location.href.includes("#")) {
        return;
    }
    let anchor = starting_anchor || decodeURIComponent(window.location.href.split("#")[1]);
    let target = document.getElementById(anchor);
    if (target === null) {
        return;
    }
    let top = target.offsetTop;
    window.scrollTo(0, top);
}

function get_current_image(show_logs=false) {
    let image_nodes = infinite_scroll_div.querySelectorAll(".infinite-image-link");
    let threshold = viewed_page_top_margin_percentage * window.innerHeight;
    if (show_logs) {
        console.log("imageNodes length: " + image_nodes.length);
        console.log(threshold);
    }
    for (let i=0; i < image_nodes.length; i++) {
        let rect = image_nodes[i].getBoundingClientRect();
        if (show_logs)
            console.log("id=" + image_nodes[i].id + ", top=" + rect.top);
        if (rect.top >= threshold) {
            return Math.max(0, i - 1);
        }
    }
    return image_nodes.length - 1;
}

function set_current_image(new_current_image) {
    current_image = new_current_image;
    console.log("Current image: " + current_image);
    let image_nodes = infinite_scroll_div.querySelectorAll(".infinite-image-link");
    let anchor = image_nodes[current_image].id;
    console.log("Anchor: " + anchor);
    let new_url = window.location.href.split("#")[0] + "#" + anchor;
    window.history.replaceState(null, null, new_url);
}

function on_scroll(event) {
    if (initializing) {
        return;
    }
    if ((window.innerHeight + window.pageYOffset) >= document.body.offsetHeight - load_next_pages_threshold) {
        load_newer_pages();
    }

    let new_current_image = get_current_image();
    if (current_image !== new_current_image) {
        set_current_image(new_current_image);
    }
}
