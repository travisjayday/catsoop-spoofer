setTimeout(function() {
	browser.storage.local.get("user", function(result) {
		console.log(result)
		result = result.user;
		if (result != undefined && result != "")
			document.getElementById("user").innerHTML = result;
	});
	browser.storage.local.get("pass", function(result) {
		console.log(result)
		result = result.pass;
		if (result != undefined && result != "")
			document.getElementById("pass").innerHTML = result;
	});
}, 1000);

