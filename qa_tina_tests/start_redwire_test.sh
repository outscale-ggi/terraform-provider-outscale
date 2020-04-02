#!/bin/bash

# start all redwires: cat qa_tina_tests/redwires.txt | xargs -t -i{} --process-slot-var=OSC_CPU -P <nb_cpu> ./qa_tina_tests/start_redwire.sh <users_list> <az_name> {}

if [ "$#" -ne 3 ]; then
    echo "Usage: ./$(basename $0) <users_list> <az_name> <test_ids>"
    exit 1
fi

IFS=','
read -r -a USERS <<< "$1"
AZ=$2
TEST_IDS_STR=$(echo $3 | sed 's/ /_/g')
TEST_IDS=$(echo $3 | sed 's/ /_ or _/g;s/^/_/g;s/$/_/g')

export OSC_AZS=$AZ
export OSC_USERS=${USERS[$OSC_CPU]}

pytest --disable-warnings -s -v --junit-xml=../details/$TEST_IDS_STR.xml -k "$TEST_IDS" ./qa_tina_tests/USER/ 2> ./$TEST_IDS_STR.err > ./$TEST_IDS_STR.out
sed -i "s:<testsuites>::g" ./details/$TEST_IDS_STR.xml
sed -i "s:</testsuites>::g" ./details/$TEST_IDS_STR.xml


echo "======================================"
echo " ===> $TEST_IDS_STR"
echo "======================================"
cat $TEST_IDS_STR.err
cat $TEST_IDS_STR.out
rm $TEST_IDS_STR.err
rm $TEST_IDS_STR.out
