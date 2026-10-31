#!/usr/bin/env bash
# Menjalankan Webots + RViz2 sekaligus. Controller otomatis mempublish /scan, /odom,
# /oa/decision dan TF karena Webots dijalankan dengan environment ROS 2.
# Pemakaian: tools/rviz.sh            (ROS_DISTRO default: jazzy)
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISTRO="${ROS_DISTRO_NAME:-jazzy}"
# shellcheck disable=SC1090
source "/opt/ros/$DISTRO/setup.bash"
WEBOTS="${WEBOTS:-$(command -v webots || echo "$HOME/opt/webots/webots")}"
"$WEBOTS" --mode=realtime "$ROOT/worlds/obstacle_avoidance.wbt" &
WPID=$!
trap 'kill $WPID 2>/dev/null' EXIT
sleep 4
# RViz2 (Ogre/GLX) crash di Wayland native, paksa lewat XWayland
QT_QPA_PLATFORM=xcb rviz2 -d "$ROOT/rviz/obstacle_avoidance.rviz"
