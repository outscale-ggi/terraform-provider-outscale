# Test Terraform provider for Outscale API

## Getting Started

### Python prerequisites

You will need Python 3.

You can create a Virtual Env and build, install the tests package following command lines below:
```bash
git clone the repository from the master branch in a $PATH
python3 -m venv build_deploy_venv
source build_deploy_venv/bin/activate
pip install pip==20.0.2
pip install wheel==0.34.2
python $PATH/provider-outscale/tests/setup.py bdist_wheel
pip install $PATH/provider-outscale/tests/dist/osc_qa_provider_oapi*-py3-none-any.whl
deactivate 
```

### Terraform prerequisites

You will need a Terraform v1.0.6 in your PATH.

## Usage

### Configuration

TODO: Template....

### Execute tests
execute tests in the venv created in the build/deploy of the tests package
```bash
source build_deploy_venv/bin/activate
mkdir tests_terraform_exec
cd tests_terraform_exec
export OSC_REGION=region
export OSC_USER=user
export TERRAFORM_PATH="/usr/bin/terraform_1.0.6"
export PLUGIN_VERSION=$VERSION
export INST_TYPE=$inst_type
export OMI_ID=$omi_id
export AK=$access_key
export SK=$secret_key
export ACCOUNT_ID=$account_id
pytest  -v  --pyargs qa_provider_oapi --junit-xml=xml_file -k ressource
```
* use '-s' for more detailed log in console
* use '-k' to execute a subset of tests



