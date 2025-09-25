#!/bin/bash

# Email settings
EMAIL_SUBJECT="UPS Alert"
EMAIL_RECIPIENT="dan@goepp.com"

# UPS event data
UPSEVENT=$1
UPSID=$2
UPSTEXT=$3

# Compose email message
MESSAGE="UPS Event: $UPSEVENT\nUPS ID: $UPSID\nMessage: $UPSTEXT"

# Send email using mail command
echo -e "$MESSAGE" | mail -s "$EMAIL_SUBJECT" "$EMAIL_RECIPIENT"