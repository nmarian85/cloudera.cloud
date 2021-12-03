# CDP Management Tools

## Description

This repo contains the code required for installing the CDP components (e.g. CML, CDE, etc.) via the CDP REST API. The code can be run from any host, provided that the dependencies below (env variables and so on) are set up and access to the Cloudera Management Console is available, i.e. Internet access is required. 
The result of each REST API call is checked for success and, in case the expected status is not reached, the execution will time out.
## Repo structure

The repo contains the following folders:

- `conf`: the configurations required for provisioning a complete CDP environment (CDP environment, data lake, CDE, CML and CDW). The configurations are split per stage (e.g. lab, prod, etc.) and CDP environment name. Each CDP environment folder contains the json configuration files, split per CDP components. 

- `scripts`: the Python scripts required for interacting with the CDP REST API. Each CDP component has its own Python script. The CDP REST API requires specific headers, hence the `cdpv1sign.py` is required for signing the headers.
- `pipeline`: the Gitlab yml pipelines

## Expected environment

* **Group level**
  
    **These are required only if the pipeline is run. For running manually the code they are not needed.**
  * **DOCKER_REGISTRY** : The URI of the Artifactory repository where to store the container created
  * **ARTIFACTORY_USER** : the username to access our repository
  * **ARTIFACTORY_PASS** : the corresponding password
  * **DOCKER_AUTH_CONFIG** : a variable containing the following but also when automatically pulling images from a protected artifactory repository such as ours.

    ```json
    {"auths": { "artifactory.sofa.dev": { "auth": "$CI_DOCKER_AUTH" }}}
    ```  

    where **CI_DOCKER_AUTH** is a *base64* encoded and masked variable containing the artifactory credentials (in the form of *username:password*)

* **Project level**
  For interacting with CDP we are going to use a technical user's CDP credentials (i.e. access key and password). For now, these credentials are stored in Gitlab however they would need to be migrated to a safer store, e.g. AWS Secrets Manager. 
  
  This user is an IGAM technical user and, after it is created, a SAML login to the CDP management console is required in order to populate it in the CDP UMS. Please be aware that IGAM SSO searches the `OU=Users and Groups,OU=ECB,DC=ecb01,DC=ecb,DC=de` branch, hence the technical user needs to be provisioned in that OU (other applications such as MoMo did the same for their monitoring users).
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


## Terraform prerequisites for installing CDP components
Before installing any CDP component we need to make sure that the underlying AWS infrastructure is provisioned in the ECB AWS account. For this, we are going to use the IaC repo (e.g. for lab https://gitlab-ccoe-hyhop.ecbcloud.xyz/cloud/aws/iac/product-teams/devo2/devo2-lab). 
Please make sure that the IaC code was ran before continuing. 
**Important mention: CDW requires a specific way of provisioning which could not be fully automated. You will find the instructions for it at the end of this README**

## Running the code
### Prerequisites
- SSH to the DEVO2 jumphost
- The jumphost should have already been configured for you via the https://gitlab.sofa.dev/ddp/devo/aws-ec2-setup, hence a Python environment is already available for you there.
- For now, the SoFa pipeline is not ready, hence the code will be run from the jumphost.

### Code
- The python scripts have a `--dryrun` option so that nothing gets executed but you will be able to see all the actions that will be done together with the JSON that would be posted to the CDP REST API endpoint. Please use the `--no-dryrun` flag when initiating a "real" execution.

- Export the CA bundle certificate location the environment name

    ```bash
    export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt
    export DEVO_ENV_NAME=devo-lab04
    ```
## Steps for configuring a new CDP tenant

- Assign the cdp roles to the admin groups

    ```bash
    cdp iam assign-group-role --generate-cli-skeleton > asg_group_role.json && \
    python3 scripts/group_cdp_role_map.py --no-dryrun --env lab --action assign --json-skel asg_group_role.json
    ```

## Installing a new CDP environment
- The steps below show how to install CDP components(environment, datalake, CDE, CML, etc.) from scratch. 
- Please follow the installation order below: CDP environment, CDP data lake, CDP experiences.
- Please see the section called "Running the code" for exporting the proper environment variables

- Create a new folder containing the CDP environment name in the `conf` folder following the convention `devo-<stage><env_number>`, e.g. `devo-lab04`.

- Create the json configuration files corresponding to the CDP components in the previously mentioned folder. Please fill all the required details belonging to that environment (VPC ID, security groups, subnets, role names, public key, account id, etc.). You can use the `devo-lab04` folder as an example.


### Create the credential for the environment

```bash
cdp environments create-aws-credential --generate-cli-skeleton > cred_create.json && \
python3 scripts/cred_mgmt.py --no-dryrun --action create --env lab --cdp-env-name ${DEVO_ENV_NAME} --json-skel cred_create.json
```

### Create the CDP environment
```bash
cdp environments create-aws-environment --generate-cli-skeleton > create_env.json && \
python3 scripts/env_mgmt.py --no-dryrun --env lab --cdp-env-name ${DEVO_ENV_NAME} --action install-env --json-skel create_env.json
```

### Create ranger and idbroker mappings

**Please be aware that when you add new roles and run the script below, the users have to login first in CDP so that their `accessorCrn` gets populated**
TODO: Populate users automatically
```bash
cdp environments set-id-broker-mappings --generate-cli-skeleton > create_idbroker_mapping.json && \
python3 scripts/idbroker_map.py  --no-dryrun --env lab --cdp-env-name ${DEVO_ENV_NAME} --json-skel create_idbroker_mapping.json
```

### Create data lake

```bash
cdp datalake create-aws-datalake --generate-cli-skeleton > create_dlake.json && \
python3 scripts/cdl_mgmt.py --no-dryrun --action install --env lab --cdp-env-name ${DEVO_ENV_NAME} --json-skel create_dlake.json
```

### Sync idbroker mappings

```bash
cdp environments sync-id-broker-mappings --generate-cli-skeleton > sync_idbroker_mapping.json && \
python3 scripts/idbroker_sync.py --no-dryrun --cdp-env-name ${DEVO_ENV_NAME} --json-skel sync_idbroker_mapping.json
```

### Assign CDP groups their CDP resource roles

```bash
cdp iam assign-group-resource-role --generate-cli-skeleton > asg_group_res_role.json && \
python3 scripts/group_cdp_res_role_map.py --no-dryrun --env lab --cdp-env-name ${DEVO_ENV_NAME} --action assign --json-skel asg_group_res_role.json
```
### Sync CDP users to environment

```bash
cdp environments sync-all-users --generate-cli-skeleton > sync_all_users.json && \
python3 scripts/user_sync.py --no-dryrun --json-skel sync_all_users.json
```

### Install CDE

```bash
cdp de enable-service --generate-cli-skeleton > create_cde.json && \
python3 scripts/cde_mgmt.py --no-dryrun --action install --env lab --cdp-env-name ${DEVO_ENV_NAME} --cde-cluster-name ${DEVO_ENV_NAME}-cde01 --json-skel create_cde.json
```
- Re-run the DEVO2 TF code for enabling https access to the EKS Control Plane. 
- Allow the jumphost role admin access to the EKS CP.

### Install CDE VC
```bash
cdp de create-vc --generate-cli-skeleton > create_vc_cde.json && \
python3 scripts/vc_cde_mgmt.py --no-dryrun --action install --env lab --cdp-env-name ${DEVO_ENV_NAME} --cde-cluster-name ${DEVO_ENV_NAME}-cde01 --vc-name ${DEVO_ENV_NAME}-cde01-vc01 --json-skel create_vc_cde.json
```

### Install CML

```bash
cdp ml create-workspace --generate-cli-skeleton > create_cml.json && \
python3 scripts/cml_mgmt.py --no-dryrun --action install --env lab --cdp-env-name ${DEVO_ENV_NAME} --cml-cluster-name ${DEVO_ENV_NAME}-cml01 --json-skel create_cml.json
```
- Re-run the DEVO2 TF code for enabling https access to the EKS Control Plane. 
- Allow the jumphost role admin access to the EKS CP.
  

## Enabling the CDW service
For enabling the CDW service we are going to use the following procedure. This is only needed when enabling the CDW service; for installing the virtual warehouses you will use the standard automation part of this repo.
This procedure is based on the one here: https://docs.cloudera.com/data-warehouse/cloud/aws-environments/topics/dw-aws-reduced-perms-mode-activating-environments.html

- Open the CDP MC (e.g. `https://t-igam.tadnet.eu/oamfed/idp/initiatesso?providerid=CDP` for TADNET), click on Data Warehouse, click on the lighting bolt for the specific environment where you want to provision CDW then:
- Choose only private subnets as Deployment Mode
- Choose all 3 BE networks in the Private Subents area
- Check use overlay nw
- Click Activate and then check to activate environment with reduced permissions mode.
- Click Activate
- Copy the CDW environment (e.g. `env-5frx9b`)
- **devo2-modules SoFa repo**
  - Create a new branch in the `devo2-modules` SoFa repo
    ```bash
    git checkout -b feature/cdw-env-m9zq6b develop
    ```
  - Paste the environment name in the environment's folder `main.tf` (e.g. `envs/lab/devo-lab04/main.tf`) in the locals section: 
  `cdw_env_name = "env-5frx9b"`
  - Merge your branch to the branch that is being used in the TF code in the IaC pipeline in the `main.tf` (usually `develop`). E.g.: `"git::https://oauth2:UtHHpqCf1-1QDzU2_DBd@gitlab.sofa.dev/ddp/devo/devo2-modules.git//devo-discdata-s3-access-v2?ref=develop"`

  - Please make sure that the modules listed below are commented/uncommented as per the example. **This is due to plenty of limitations (CDP CDW env name not known beforehand, TF not being able to cope with waiting for an EKS cluster to be provisioned, the ECB pipeline not allowing the AWS pipeline role to be impersonated)**
    ```bash
    module "cdp_cdw_infra" {
      source          = "../../../cdp-cdw-infra"
      this_account_id = var.this_account_id
      cdw_env_name    = local.cdw_env_name
      cdp_env_id      = local.cdp_env_id
      cdp_actor_crn   = local.cdp_actor_crn
      cdp_tenant_id   = local.cdp_tenant_id
      cdp_env_name    = local.cdp_env
      cdp_env_owner   = local.cdp_env_owner
      dlake_s3_bucket = local.cdp_internal_buckets["cdp_data_bucket"]
      cdw_policy_name = local.cdw_policy_name
      cdw_policy_json = local.cdw_policy_json
    }

    # module "eks_post_config" {
    #   source                  = "../../../eks-post-config"
    #   eks_cluster_name        = module.cdp_cdw_infra.cdw_eks_cluster_name
    #   node_instance_role_name = module.cdp_cdw_infra.cdw_instance_role_name
    #   jumpserver_role         = var.jumpserver_role
    #   crossaccount_role       = local.role_name["crossaccount"]
    #   this_account_id         = var.this_account_id
    # }

    # module "eks_cp_access" {
    #   source = "../../../eks-cp-access"
    # }
    ```

- **devo2 IaC repo** Run TF pipeline
- We are going to provision the cluster using the TF pipeline which uses a role that we cannot assume on the jumphost. For this reason we need to do the `kubectl apply` via TF, otherwise we will not be able to connect to the EKS cluster using the `jumpserver-role`.
- **devo2-modules SoFa repo**: Once the CDW cloud formation is deployed by the TF code please do the following:
  - Create a new branch in the `devo2-modules` SoFa repo
    ```bash
    git checkout -b feature/cdw-env-m9zq6b develop
    ```
  - Uncomment the following section in the environment directory (e.g. `envs/lab/devo-lab04/main.tf`) section
    ```bash
    module "eks_post_config" {
      source                  = "../../../eks-post-config"
      eks_cluster_name        = module.cdp_cdw_infra.cdw_eks_cluster_name
      node_instance_role_name = module.cdp_cdw_infra.cdw_instance_role_name
      jumpserver_role         = var.jumpserver_role
      crossaccount_role       = local.role_name["crossaccount"]
      this_account_id         = var.this_account_id
    }

    module "eks_cp_access" {
      source = "../../../eks-cp-access"
    }
    ```
  - Merge your branch to the branch that is being used in the TF code in the IaC pipeline in the `main.tf` (usually `develop`). E.g.: `"git::https://oauth2:UtHHpqCf1-1QDzU2_DBd@gitlab.sofa.dev/ddp/devo/devo2-modules.git//devo-discdata-s3-access-v2?ref=develop"`

-  **devo2 IaC repo** Run TF pipeline. Since no changes were performed in this repo then you need to do some dummy change (e.g. a comment) in one of the files of the repo in order to be able to issue a merge request.
- Once this is done, go back to the CDP MC Data Warehouse interface and then click on Copy Configurations, tick "Yes, Kubeconfig and AWS Auth configurations are applied" and then Continue. Wait until the service is enabled and the Database Catalog is provisioned.
- Login to the JH and then enable the Cloudwatch logging for EKS:

    ```bash
    ➜  aws eks update-cluster-config --name env-hk574w-dwx-stack-eks --logging '{"clusterLogging": [{"types": ["api","audit","authenticator","controllerManager","scheduler"],"enabled": true}]}'
    ```
- Follow the steps for provisioning the virtual warehouses in the Installing a CDP environment section.

## Install CDW Virtual Warehouse (Impala/Hive)
```bash
cdp dw create-vw --generate-cli-skeleton > create_vw.json && python3 scripts/vw_cdw_mgmt.py --no-dryrun --action install --env lab --cdp-env-name $DEVO_ENV_NAME --vw-name i03 --json-skel create_vw.json
```

## Allow the jumphost role admin access to the EKS CP for CDE or CML
  - SSH to the jumphost
  - Export the variables
  ```bash
  export DEVO_ENV_NAME=devo-lab04
  export EKS_CLUSTER_NAME=liftie-sx44dbft
  export EKS_CLUSTER_TYPE=cml
  export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  ```
  - Assume the crossaccount role
  ```bash
  cred=$(aws sts assume-role --role-arn arn:aws:iam::${ACCOUNT_ID}:role/${DEVO_ENV_NAME}-crossaccount-role  --role-session-name AWSCLI-Session | jq .Credentials)
  export AWS_ACCESS_KEY_ID=$(echo $cred|jq .AccessKeyId|tr -d '"')
  export AWS_SECRET_ACCESS_KEY=$(echo $cred|jq .SecretAccessKey|tr -d '"')
  export AWS_SESSION_TOKEN=$(echo $cred|jq .SessionToken|tr -d '"')
  ```
  - Retrieve the kubeconfig file and export the `KUBECONFIG` variable
  ```bash
  aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --kubeconfig ~/.kube/${DEVO_ENV_NAME}-${EKS_CLUSTER_TYPE}
  export KUBECONFIG=~/.kube/${DEVO_ENV_NAME}-${EKS_CLUSTER_TYPE}
  ```
  
  - Create the aws-auth configmap file
  ```bash
  cd cdp-mgmt
  kubectl get configmap aws-auth --namespace kube-system -o yaml | python3 scripts/dump_aws_auth.py > aws_auth_${DEVO_ENV_NAME}-${EKS_CLUSTER_TYPE}
  ```
  - Apply the configmap update
  ```bash
  kubectl apply -f aws_auth_${DEVO_ENV_NAME}-${EKS_CLUSTER_TYPE}
  ```

  - Test that it works by exiting and logging in again to the host and running the commands below.
  ```bash
  export DEVO_ENV_NAME=devo-lab04
  export EKS_CLUSTER_TYPE=cde
  export KUBECONFIG=~/.kube/${DEVO_ENV_NAME}-${EKS_CLUSTER_TYPE}
  kubectl get po -A | head -5
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