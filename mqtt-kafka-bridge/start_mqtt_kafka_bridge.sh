#!/bin/bash
python consumer_to_score_computation.py 1 &

python consumer_to_user_data.py 1 &

wait -n

exit $?