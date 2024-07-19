#!/usr/bin/env bash

labMembers=("tmsully2020@gmail.com" "nathan.wu.nhw5@yale.edu" "virajcz@ucla.edu" "wesley.clawson@tufts.edu")

for email in $labMembers; do
    fortune | mailx -s "Experiment complete!" $email
done