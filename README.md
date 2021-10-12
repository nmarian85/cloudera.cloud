# CDP Management Tools

## Description

The purpose of this repo is to deliver the pipeline and the code required for managing CDP components (e.g. install and start an environment, install and delete CDE/CML clusters, etc.) via the CDP REST API. The code was written in such a manner that it can be run from any host, provided that the dependencies below (env variables and so on) are set up and access to the Cloudera Management Console is available, i.e. Internet access is required. 
There is as well a pipeline (described below) in order to provide a one-click provisioning method. 
It is important to mention that the code will wait after POST-ing the corresponding JSON and check if the action submitted was succesful or not. In case the expected status is not reached, the execution will time out.

## Repo structure
The repo contains the following folders:
- `conf`: the configurations required for provisioning a complete CDP environment (CDP environment, data lake, CDE, CML and CDW). The configurations are split per stage (e.g. lab, prod, etc.) and CDP environment name. Each CDP environment folder contains the json configuration files, split per CDP components. 
- `scripts`: the Python scripts required for interacting with the CDP REST API. Each CDP component has its own Python script. The CDP REST API requires specific headers, hence the `cdpv1sign.py` is required.
- `pipeline`: the Gitlab yml pipelines

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
  * **REQUESTS_CA_BUNDLE**:
    - /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt for RHEL/Amazon Linux
    - /etc/ssl/certs/ca-certificates.crt for Ubuntu/Alpine


* **Python dependencies**
    - click

## Steps for Provisioning a new environment without the use of the pipeline
TODO: Add section with documentation for each cluster type and talk about idempotency and scripts

- Create a new folder containing the CDP environment name in the `conf` folder following the convention `devo-<stage><env_number>`, e.g. `devo-lab02`.
- Create the json configuration files corresponding to the CDP components in the previously mentioned folder. Please fill all the required details belonging to that environment (VPC ID, security groups, subnets, role names, public key, account id, etc.). You can use the `devo-lab01` folder as an example.
- Export the CA bundle certificate location
`export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt`
- Create the credential for the environment
    ```bash
    cdp environments create-aws-credential --generate-cli-skeleton > cred_create.json && \
    python3 scripts/cred_mgmt.py --no-dryrun --action create-cred --env lab --cdp-env-name devo-lab02 --json-skel cred_create.json
    ```
- Create the CDP environment
    ```bash
     cdp environments create-aws-environment --generate-cli-skeleton > create_env.json && \
    python3 scripts/env_mgmt.py --no-dryrun --env lab --cdp-env-name devo-lab02 --action install-env --json-skel create_env.json
    ```
- Create ranger and idbroker mappings
    ```bash
    cdp environments set-id-broker-mappings --generate-cli-skeleton > create_idbroker_mapping.json && \
    python3 scripts/idbroker_map.py  --no-dryrun --env lab --cdp-env-name devo-lab02 --json-skel create_idbroker_mapping.json
    ```
- Create data lake
    ```bash
    cdp datalake delete-datalake --generate-cli-skeleton > create_dlake.json && \
    python3 scripts/cdl_mgmt.py --no-dryrun --action install-cdl --env lab --cdp-env-name devo-lab02 --json-skel create_dlake.json
    ```

- Sync idbroker mappings
    ```bash
    cdp environments sync-id-broker-mappings --generate-cli-skeleton > sync_idbroker_mapping.json && \
    python3 scripts/idbroker_sync.py --no-dryrun --env lab --cdp-env-name devo-lab02 --json-skel sync_idbroker_mapping.json
    ```

- Assign CDP users their CDP resource roles
    ```bash
    cdp iam assign-user-resource-role --generate-cli-skeleton > asg_user_res_role.json && \
    python3 scripts/group_cdprole_map.py --no-dryrun --env lab --cdp-env-name devo-lab02 --action assign-cdproles-to-groups --json-skel asg_user_res_role.json
    ```
- Sync CDP users to environment
    ```bash
    cdp environments sync-all-users --generate-cli-skeleton > sync_all_users.json && \
    python3 scripts/user_sync.py --no-dryrun --env lab --json-skel sync_all_users.json
    ```
- Install CDE
    ```bash
    cdp de enable-service --generate-cli-skeleton > create_cde.json && \
    python3 scripts/cde_mgmt.py --no-dryrun --action install-cde --env lab --cdp-env-name devo-lab02 --cde-cluster-name devo-lab02-cde01 --json-skel create_cde.json
    ```
- Install CDE VC
    ```bash
    cdp de create-vc --generate-cli-skeleton > create_vc_cde.json && \
    python3 scripts/vc_cde_mgmt.py --no-dryrun --action install-vc-cde --env lab --cdp-env-name devo-lab02 --cde-cluster-name devo-lab02-cde01 --vc-cde-cluster-name devo-lab02-cde01-vc01 --json-skel create_vc_cde.json

    ```

## Pipeline - work in progress for now

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