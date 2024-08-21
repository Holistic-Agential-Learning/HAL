#!/usr/bin/env bash

labMembers=("trevor.sullivan@tufts.edu" "wesley.clawson@tufts.edu")

for email in ${labMembers[@]}; do
    # echo $email
    fortune | mailx -r "wesley.clawson@tufts.edu" -s "Experiment complete!" $email
done