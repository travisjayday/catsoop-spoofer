# delete-backend.sh SID
docker stop firefoxSID$1
docker container rm firefoxSID$1
rm -rf /docker/appdata/firefoxSID$1
