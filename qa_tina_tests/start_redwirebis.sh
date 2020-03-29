#!/bin/bash

# start all redwires: cat qa_tina/redwires.txt | xargs -t -i{} --process-slot-var=OSC_CPU -P <nb_cpu> ./qa_tina/start_redwire.sh <users_list> <az_name> {}

if [ "$#" -ne 3 ]; then
    echo "Usage: ./$(basename $0) <users_list> <az_name> <test_ids>"
    exit 1
fi

IFS=','
read -r -a USERS <<< "$1"
AZ=$2

export OSC_AZS=$AZ
export OSC_USERS=${USERS[$OSC_CPU]}

TEST_PATH=$(git grep "_$3_" | cut -d ':' -f1)

echo pytest --disable-warnings -s -v --junit-xml=./details/$3.xml -k "$3" ./$TEST_PATH 2> ./$3.err > ./$3.out

pytest --disable-warnings -s -v --junit-xml=./details/$3.xml -k "$3" ./$TEST_PATH 2> ./$3.err > ./$3.out

DIR=$(echo $TEST_PATH | rev | cut -d '/' -f2- | rev)

set -e
sed -i "s/name=\"pytest\"/name=\"$DIR\"/g" ./details/$3.xml

echo "======================================"
echo " ===> $3"
echo "======================================"
cat $3.err
cat $3.out
rm $3.err
rm $3.out
