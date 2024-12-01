#!/bin/sh
#
# Copies the files from the remote server to my local server
#

set -x
rsync -avz -e ssh --exclude=.direnv --exclude=__pycache__ ws@ugv.local:~/OpenCV-Pi-AprilTags/ ./
