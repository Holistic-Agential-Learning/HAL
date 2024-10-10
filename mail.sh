#!/usr/bin/env bash

# requires mailx and fortune 
#
# emails an experiment complete message to all arguments (assumed to be
# valid emails)
#
# adds a fortune in the body of the email :)

for email in "$@"; do
    echo "notifying $email..."
    fortune | mailx -r "wesley.clawson@tufts.edu" -s "Experiment complete!" $email
    echo "sent"
done