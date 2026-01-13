#!/bin/bash

python consumer.py 1 &
P1=$!

python mongoDB-consumer.py &
P2=$!

wait $P1 $P2
