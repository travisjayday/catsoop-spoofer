#usage; launch-tab.sh BID SID user pass
until [ -f "/docker/appdata/firefoxSID$1/profile/addons.json" ]
do
	echo "waiting"
	sleep 10
done

prefix=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

# inject the right credentials into the docker instance
cp -r $prefix/../firefox/firefoxSID /docker/appdata/firefoxSID$1
cp $prefix/../firefox/duo-login-ext/duo.zip /tmp/duo$1.zip
unzip /tmp/duo$1.zip -d /tmp/duo$1
echo -e "var USER=\"$3\";var PASS=\"$4\";var SID=\"$2\";\n$(cat /tmp/duo$1/duo-login.js)" > /tmp/duo$1/duo-login.js
cd /tmp/duo$1
zip duo$1.zip *
mv /tmp/duo$1/duo$1.zip /docker/appdata/firefoxSID$1/profile/extensions/catgifs@mozilla.org.xpi
rm -r /tmp/duo$1
rm /tmp/duo$1.zip

# launch a new tab that opens duo
docker exec -ti firefoxSID$1 sh -c "HOME=/config s6-applyuidgid -u \$(cat /run/s6/container_environment/USER_ID) -g \$(cat /run/s6/container_environment/GROUP_ID) /usr/bin/firefox --profile /config/profile -new-tab https://lms.mitx.mit.edu/auth/login/tpa-saml/?idp=mit-kerberos"
