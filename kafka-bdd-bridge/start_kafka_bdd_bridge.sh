#!/bin/bash
python consumer_user_db_bridge.py 1 &

python consumer_score_db_bridge.py 1 &

wait -n

exit $?