# CDP Management Tools

## Description

Project required for provisioning and managing CDP components via the cdpcli CDP automation tool. The purpose of this repo is to deliver the pipeline and the code required for managing CDP components (e.g. install and start an environment, install and delete CDE/CML clusters, etc.).
All commands are being run inside a Docker container based on the Docker image built here `https://gitlab.sofa.dev/ddp/docker-images/cdpcli-docker-image/`.

## Expected environment

* **Group level**
  * **DOCKER_REGISTRY** : The URI of the Artifactory repository where to store the container created
  * **ARTIFACTORY_USER** : the username to access our repository
  * **ARTIFACTORY_PASS** : the corresponding password
  * **DOCKER_AUTH_CONFIG** : a variable containing the following but also when automatically pulling images from a protected artifactory repository such as ours.

    ```json
    {"auths": { "artifactory.sofa.dev": { "auth": "$CI_DOCKER_AUTH" }}}
    ```  

    where **CI_DOCKER_AUTH** is a *base64* encoded and masked variable containing the artifactory credentials (in the form of *username:password*)

* **Project level**
  For interacting with CDP we are going to use a technical user's credentials (i.e. security key). For now these credentials are stored in Gitlab however they would need to be migrated to a safer store, e.g. AWS Secrets Manager. This user is an IGAM technical user and, after it is created, a SAML login to the CDP management console is required in order to populate it in the CDP UMS. Please be aware that IGAM SSO searches the `OU=Users and Groups,OU=ECB,DC=ecb01,DC=ecb,DC=de` branch, hence the technical user needs to be provisioned in that OU (other applications such as MoMo did the same for their monitoring users).
  Request type to be used in ITSP: Requests to create, modify, extend, delete non-Standard/-SA account in DEV AD environments.
  Technical user name: ap-devo-cdp

  * **CDP_ACCESS_KEY_ID** : The access key of the CDP technical user.
  * **CDP_PRIVATE_KEY** : The private key of the CDP technical user.
Find the CDP admin group in User Management and click on its Admins tab (https://console.cdp.cloudera.com/iam/index.html#/groups/ecbt1-igamfs-app-cdp-admin?tab=admins). Add the technical user.
User ap-devo-cdp has been assigned resource role IamGroupAdmin for ecbt1-igamfs-app-cdp-admin.
## How does the code work

The `{env}.json` file contains a description of all the components part of an environment. The code parses this file, extracts the information it needs regarding a specific component and then generates a CDP component (e.g. CML) compliant JSON. This file is then fed to the cdpcli command responsible for the action we want to achieve (e.g. deleting a cluster).

## Pipeline

To a certain extent, we are abusing the traditional concept of a pipeline, since the pipeline does not contain the traditional stages (build/test/deploy). We are building a "poor man's" dynamic pipeline based on the environment variable `ACTION`. The action can be one of the following:

* install (installs a CDP environment and its attached datalake)
* delete (deletes a CDP environment and its attached datalake)
* start (starts a CDP environment and its attached datalake)
* stop (stops environment and its attached datalake)
* install_cml (installs CML cluster)
* delete_cml (deletes a CML cluster)
* install_cde (installs a CDE cluster)
* delete_cde (deletes a CDE cluster)

Based on the value of this variable, a deployment pipeline will be generated on the fly containing the steps for that specific action. E.g. selecting `install_cml` will render a pipeline containing two stages: start the CDP environment and provision the CML cluster.
Most of the actions are manual in order to allow the user to confirm the action he wants to perform. 

## Running the code

* Decide the action you want to perform and change the value of the ACTION variable

* Set the ENV variable to specify which environment you are going to work on

* Set the CDP_ENV_NAME variable in order to specify which CDP environment should be used

* Check the `{env}.json` file to make sure that the component is defined. If not, please define it (e.g. a new CML cluster)

* If installing or deleting CDE/CML/CDW clusters please define them in the env variable list (e.g. `CML_CLUSTERS` when working with CML clusters)

* Commit the code and run the pipeline

# TODO: Add section with documentation for each cluster type and talk about idempotency and scripts


""" Dependencies
Python: pip3 install --upgrade --user click
Env variables: 
    - REQUESTS_CA_BUNDLE=
        - /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt for RHEL/Amazon Linux
        - /etc/ssl/certs/ca-certificates.crt for Ubuntu/Alpine
    - CDP_ACCESS_KEY_ID
    - CDP_PRIVATE_KEY
"""

# 1. Create credential for the environment
# 2. Create environment
# 3. Create ranger and idbroker mappings
# 4. Create data lake
# 5. Create CML/CDE/CDW
# 6. Add user CDP idbroker mappings
# 7. Sync idbroker mappings


## Complete env deployment

```bash
export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/cred_mgmt.py --no-dryrun --action create-cred --env lab --cdp-env-name devo-lab01 --json-skel cred_create.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/env_mgmt.py --no-dryrun --env lab --cdp-env-name devo-lab01 --action install-env --json-skel create_env.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/idbroker_map.py  --no-dryrun --env lab --cdp-env-name devo-lab01 --json-skel create_idbroker_mapping.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/cdl_mgmt.py --no-dryrun --action install-cdl --env lab --cdp-env-name devo-lab01 --json-skel create_dlake.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/idbroker_sync.py --no-dryrun --env lab --cdp-env-name devo-lab01 --json-skel sync_idbroker_mapping.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/group_cdprole_map.py --no-dryrun --env lab --cdp-env-name devo-lab01 --action assign-cdproles-to-groups --json-skel asg_user_res_role.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/user_sync.py --no-dryrun --env lab --json-skel sync_all_users.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 cde_mgmt.py --no-dryrun --action install-cde --env lab --cdp-env-name devo-lab01 --cde-cluster-name devo-lab01 --json-skel create_cde.json

export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt && git pull && python3 scripts/vc_cde_mgmt.py --no-dryrun --action install-vc-cde --env lab --cdp-env-name devo-lab01 --cde-cluster-name devo-lab01-cde01 --vc-cde-cluster-name devo-lab01-cde01-vc01 --json-skel create_vc_cde.json

```
