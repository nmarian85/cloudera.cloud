import click
import sys
import json
import os
from utils import show_progress, get_env_info, poll_for_status, get_cdp_env_crn
from cdpv1sign import generate_headers
import requests_ops
import requests


def dump_assign_group_resource_role_json(cdp_env_crn, cdp_role, group_name, json_skel):
    assign_group_role_json = dict(json_skel)
    resource_role_crn = f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{cdp_role}"
    assign_group_role_json["groupName"] = group_name
    assign_group_role_json["resourceRoleCrn"] = resource_role_crn
    assign_group_role_json["resourceCrn"] = cdp_env_crn
    return assign_group_role_json


# def dump_assign_user_resource_role_json(cdp_env_crn, cdp_role, user, json_skel):
#     assign_group_role_json = dict(json_skel)
#     resource_role_crn = f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{cdp_role}"
#     assign_group_role_json["groupName"] = user
#     assign_group_role_json["resourceRoleCrn"] = resource_role_crn
#     assign_group_role_json["resourceCrn"] = cdp_env_crn
#     return assign_group_role_json


# def dump_unassign_group_resource_role_json(cred_info, json_skel):
#     assign_group_role_json = dict(json_skel)
#     assign_group_role_json["credentialName"] = cred_info["credential_name"]
#     return assign_group_role_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["assign-role-to-group"]), required=True)
@click.option(
    "--env",
    type=click.Choice(["lab", "test", "dev", "acc", "prod"]),
    help="ECB environment: lab, test, etc.",
    required=True,
)
@click.option(
    "--cdp-env-name",
    help="Please see {env}.json file where you defined the CDP env name",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        assign_group_role_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    env_url = f"{requests_ops.CDP_IAM_ENDPOINT}/iam"
    cdp_env_crn = get_cdp_env_crn(cdp_env_name)
    for group, roles in cdp_env_info["cdp_igam_groups"].items():
        for role in roles:
            if action == "assign-role-to-group":
                click.echo(f"==============Assigning role {role} to group {group}==============")
                cdp_assign_group_role_json = dump_assign_group_resource_role_json(
                    cdp_env_crn, role, group, assign_group_role_json_skel
                )
                action_url = f"{env_url}/assignGroupResourceRole"
            # elif action == "delete-cred":
            #     click.echo(f"==============Deleting credential {cred_name}==============")
            #     cdp_assign_group_role_json = dump_unassign_group_resource_role_json(
            #         cred_info, assign_group_role_json_skel
            #     )
            #     action_url = f"{env_url}/deleteCredential"

        click.echo("-------------------Generated JSON-----------------------------")
        print(json.dumps(cdp_assign_group_role_json, indent=4, sort_keys=True))
        click.echo("--------------------------------------------------------------")

        if not dryrun:
            response = requests_ops.send_http_request(
                srv_url=action_url,
                req_type="post",
                data=cdp_assign_group_role_json,
                headers=generate_headers("POST", action_url),
            )

            click.echo(f"Waiting for {action} on role {role}")
            if action == "assign-role-to-group":
                elem_present = True
            # elif action == "delete-cred":
            #     elem_present = False

            elem_search_info = {
                "root_index": "resourceAssignments",
                "expected_key_val": {
                    "resourceRoleCrn": "{requests_ops.DEFAULT_IAM_CRN}:altus:resourceRole:{role}"
                },
                "present": elem_present,
            }

            poll_for_status(
                poll_url=f"{env_url}/listGroupAssignedResourceRoles",
                data={"groupName": group},
                elem_search_info=elem_search_info,
            )
            click.echo(f"Action {action} on cdp group {group} assigning role {role} DONE")
            # dumping file so that Gitlab will back it up
            with open(f"{group}_{role}.json", "w", encoding="utf-8") as f:
                json.dump(cdp_assign_group_role_json, f, ensure_ascii=False, indent=4)
        click.echo(f"===========================================================")
        click.echo()


if __name__ == "__main__":
    main()
