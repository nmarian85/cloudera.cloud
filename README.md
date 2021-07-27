# CDP Management Tools

## Description

Project required for provisioning and managing CDP components via the CDPCLI. The purpose of this repo is to deliver the pipeline and the code required for managing CDP components (e.g. start an environment, provision/delete CDE, CML).
All commands are being run inside a Docker container based on the Docker image built here https://gitlab.sofa.dev/ddp/docker-images/cdpcli-docker-image/.

Technical user : TBD

## Expected environment

The building relies on the following variables being set

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
  For provisioning we are going to use a technical user's keys. In order to populate the user in CDP we need to perform a first login using SAML. Please be aware that IGAM SSO searches in OU=Users and Groups,OU=ECB,DC=ecb01,DC=ecb,DC=de, hence the technical user needs to be provisioned in that OU (other applications such as MoMo did the same for their monitoring users).
  Request type to be used in ITSP: Requests to create, modify, extend, delete non-Standard/-SA account in DEV AD environments.
  * **CDP_ACCESS_KEY_ID** : The access key of the CDP technical user.
  * **CDP_PRIVATE_KEY** : The private key of the CDP technical user.

## How does the code work

The `env.json` file contains a description of all the components part of an environment. The code parses this file, extracts the information it needs regarding a specific component and then generates a CDP component (e.g. CML) compliant JSON. This file is then fed to the cdpcli command responsible for the action we want to achieve (e.g. deleting a cluster).

## Pipeline

The pipeline is automatically generated based on the environment variable `ACTION`. To be more specific, if the variable is set as `provision`, the pipeline would contain only the jobs responsible for provisioning a cluster, while if it set to `delete`, then the pipeline will be composed only of jobs that delete clusters. 
It is important to mention that the only action which runs automatically as part of a push is the start environment one since we need to have a working environment before any action on a specific component is taken. The other jobs would need to be executed manually. 
TODO: Add pipeline schedule for destroying/creating clusters based on a predefined schedule.
### manage_env

Starts or stops the environment.

### provision

Provisions CML and CDE clusters.

### delete

Provisions CML and CDE clusters.

