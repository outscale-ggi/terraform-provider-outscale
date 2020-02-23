#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <target> <region> <accounts>" >&2
    exit 1
fi

target=$1
region=$2
accounts=$3

LOG_FILE='./remote_rw_exec.log'

error_exit()
{
    echo "ERROR: $1" 1>&2
    exit 1
}

check_error()
{
    if [ $1 -ne 0 ]; then
        error_exit "$2"
    fi
}

# scp src
echo "Copy sources on $target..." | tee $LOG_FILE
tar czf ../qa_tina.tgz --exclude ../qa_tina/venv_p3 ../qa_tina >> $LOG_FILE 2>&1 || error_exit "Local archive creation failed"
scp ../qa_tina.tgz $target:./ >> $LOG_FILE 2>&1 || error_exit "Archive scp failed"
rm ../qa_tina.tgz >> $LOG_FILE 2>&1 || error_exit "Local archive rm failed"
ssh $target 'if [ -e ./qa_tina ]; then rm -rf ./qa_tina; fi' >> $LOG_FILE 2>&1 || error_exit "Remote cleanup failed"
ssh $target tar xzf ./qa_tina.tgz >> $LOG_FILE 2>&1 || error_exit "Remote archive extraction failed"
ssh $target rm ./qa_tina.tgz >> $LOG_FILE 2>&1 || error_exit "remote archive rm failed"

# scp credential
echo "Copy credentials on $target..." | tee -a $LOG_FILE
if [ -e ~/.tmp_osc_credentials ]; then rm ~/.tmp_osc_credentials; fi >> $LOG_FILE 2>&1 || error_exit "Local tmp credential rm failed"
source ./venv_p3/bin/activate >> $LOG_FILE 2>&1 || error_exit "Local env init (source venv) failed"
export PYTHONPATH=$(make -s python-path) >> $LOG_FILE 2>&1 || error_exit "Local env init (PYTHONPATH) failed"
python ./qa_tools/qa_tools/gen_tmp_credential.py --region $region --accounts $accounts >> $LOG_FILE 2>&1 || error_exit "Local tmp credential creation failed"
scp ~/.tmp_osc_credentials $target:./.osc_credentials >> $LOG_FILE 2>&1 || error_exit "Tmp credential scp failed"

# ssh make env
echo "Remote environment creation..." | tee -a $LOG_FILE
ssh $target 'cd ./qa_tina; make clean; find . -name \*.pyc -delete; make env' >> $LOG_FILE 2>&1 || error_exit "Remote env init failed"

# ssh clean account
echo "Remote accounts cleanup..." | tee -a $LOG_FILE
ssh $target >> $LOG_FILE 2>&1 << EOF
set -e
cd ./qa_tina
source ./venv_p3/bin/activate
export PYTHONPATH=\$(make -s python-path)
python ./qa_tools/qa_tools/tools/account/cleanup_user.py -user $(echo $accounts | sed 's/,/=/g')  -zone-name "$region"a
EOF
check_error $? "Remote accounts cleanup failed"

# ssh test clean account
echo "Remote cleanup check before tests..." | tee -a $LOG_FILE
ssh $target >> $LOG_FILE 2>&1 << EOF
set -e
cd ./qa_tina
source ./venv_p3/bin/activate
export PYTHONPATH=\$(make -s python-path)
export OSC_AZS="$region"a
export OSC_USERS="$(echo $accounts | sed 's/,/ /g')"
pytest --disable-warnings -s -v ./qa_tools/qa_tools/tools/tests/test_clean_account.py
EOF
check_error $? "Remote cleanup check before tests failed"

# ssh exec tests
echo "Remote tests execution..." | tee -a $LOG_FILE
ssh $target >> $LOG_FILE 2>&1 << EOF
set -e
cd ./qa_tina
source ./venv_p3/bin/activate
export PYTHONPATH=\$(make -s python-path)
cat qa_tina/redwires.txt | xargs -t -i{} --process-slot-var=OSC_CPU -P $(echo $accounts | awk -F',' '{ print NF }') ./qa_tina/start_redwire.sh $accounts "$region"a {}
EOF
check_error $? "Remote tests execution failed"

nb_result=$(grep -c "^qa_tina.*::test_" $LOG_FILE)
nb_rw=$(grep -v "^#" qa_tina/redwires.txt | tr ',' '\n' | wc -l| sed 's/ //g')
echo "RESULTS: " | tee -a $LOG_FILE
grep "^qa_tina.*::test_" remote_rw_exec.log | tee -a $LOG_FILE
if [ $nb_result -ne $nb_rw ]; then
    echo "WARNING: missing results: $nb_result/$nb_rw" | tee -a $LOG_FILE
fi

# scp junit results
echo "Copy junit results..." | tee -a $LOG_FILE
if [ -e ./junit ]; then rm -rf ./junit; fi >> $LOG_FILE 2>&1 || error_exit "Local junit rm failed"
scp -r $target:./qa_tina/details ./junit >> $LOG_FILE 2>&1 || error_exit "Junit scp failed"

# ssh test clean account
echo "Remote cleanup check after tests..." | tee -a $LOG_FILE
ssh $target >> $LOG_FILE 2>&1 << EOF
set -e
cd ./qa_tina
source ./venv_p3/bin/activate
export PYTHONPATH=\$(make -s python-path)
export OSC_AZS="$region"a
export OSC_USERS="$(echo $accounts | sed 's/,/ /g')"
pytest --disable-warnings -s -v ./qa_tools/qa_tools/tools/tests/test_clean_account.py
EOF
check_error $? "Remote cleanup check after tests failed"
