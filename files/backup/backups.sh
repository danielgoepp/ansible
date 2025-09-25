#!/bin/zsh

STAMP=`date +"%Y-%m-%d_%H%M"`
BKUPDIR=/mnt/backups/
SRCDIR=/mnt/k3s-prod-data/

# disabled uptime kuma until I can improve it - no need to backup data, just config - some kind of custom sqlite export perhaps?

# for service in "esphome" "zigbee2mqtt" "uptime-kuma" "kopia"; do
for service in "esphome" "zigbee2mqtt" "kopia"; do
    echo "Processing backup for $service"
    case $service in
        "esphome")
            exclude=( --exclude='.esphome' )
            ;;
        "kopia")
            exclude=( --exclude={'logs','cache'} )
            ;;
        "zigbee2mqtt")
            exclude=( --exclude={'.git','.gitignore'} )
            ;;
        *)
            unset exclude
            ;;
    esac
    tar ${exclude[@]} -zcpf $BKUPDIR/$service/$service-$STAMP.tgz -C $SRCDIR $service
    echo "Purge backup for $service"
    find $BKUPDIR/$service -mtime +7 -delete
done

## backup opnsense
echo "Processing backup for opnsense"
source /usr/local/bin/.opnsense.env
curl -s -k -u $KEY:$SECRET https://$HOST/api/core/backup/download/this -o $BKUPDIR/opnsense/opnsense-$STAMP.xml
find $BKUPDIR/opnsense -mtime +7 -delete

## backup homeassistant
rsync -ah /mnt/k3s-prod-data/homeassistant/backups/ /mnt/backups/homeassistant/prod --delete

## backup unifi
echo "Processing backup for unifi"
rsync -ah root@ui-network:/var/lib/unifi/backup/autobackup/ /mnt/backups/unifi/ --delete

## backup victoriametrics
echo "Processing backup for victoriametrics"
vmbackup-prod -storageDataPath=/mnt/k3s-prod-data/vms-prod-lt -snapshot.createURL=https://vms-prod-lt.goepp.net/snapshot/create -dst=fs:///mnt/backups/victoriametrics/vms-prod-lt -loggerLevel=WARN

## purge jira backups
find $BKUPDIR/jira -mtime +7 -delete

## purge unifi backups
find $BKUPDIR/unifi -mtime +7 -delete

## backup torrent: plex, radarr, sonarr, prowlarr, transmission
# echo "Processing backup for torrent and plex"
# rsync -ah /mnt/k3s-prod-data/plex/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/ /mnt/backups/torrent/plex/Plug-in\ Support --delete
# rsync -ah /mnt/k3s-prod-data/radarr/Backups/ /mnt/backups/torrent/radarr --delete
# rsync -ah /mnt/k3s-prod-data/sonarr/Backups/ /mnt/backups/torrent/sonarr --delete
# rsync -ah /mnt/k3s-prod-data/prowlarr/Backups/ /mnt/backups/torrent/prowlarr --delete
## Disabled due to permissions issue - not really necessary anyway, transmission doesn't have much of a config
# rsync -ah --exclude '.*' /mnt/k3s-prod-data/transmission/ /mnt/backups/torrent/transmission --delete
# cp /mnt/k3s-prod-data/plex/Library/Application\ Support/Plex\ Media\ Server/Preferences.xml /mnt/backups/torrent/plex/
find /mnt/smb_media -type d | egrep -v "Plex Versions" > /mnt/backups/torrent/media_list.txt