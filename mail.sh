#!/usr/bin/env bash

labMembers=("trevor.sullivan@tufts.edu")

for email in "$@"; do
    echo "notifying $email..."
    fortune | mailx -r "wesley.clawson@tufts.edu" -s "Experiment complete!" $email
    echo "sent"
done