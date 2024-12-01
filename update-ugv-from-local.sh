#!/bin/sh
#
# Copies local files to the remote server
#

rsync -avz -e ssh --exclude=.direnv --exclude=__pycache__ ./ ws@ugv.local:~/OpenCV-Pi-AprilTags/
