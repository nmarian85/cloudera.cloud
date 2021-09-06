import click
import sys
import json
import os
from utils import (
    show_progress,
    get_env_info,
    poll_for_status,
    get_cdp_env_crn,
    get_user_attr,
)
from cdpv1sign import generate_headers
import requests_ops
import requests

env_url = f"{requests_ops.CDP_IAM_ENDPOINT}"


def dump_assign_user_resource_role_json(cdp_env_crn, cdp_role, user_name, json_skel):
    assign_user_role_json = dict(json_skel)
    resource_role_crn = f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{cdp_role}"
    assign_user_role_json["user"] = user_name
    assign_user_role_json["resourceRoleCrn"] = resource_role_crn
    assign_user_role_json["resourceCrn"] = cdp_env_crn
    return assign_user_role_json


def assign_role_to_user(role, user, cdp_env_name, json_skel, dryrun):
    click.echo(f"===Assigning role {role} to user {user} on env {cdp_env_name}===")
    action_url = f"{env_url}/assignuserResourceRole"
    cdp_env_crn = get_cdp_env_crn(cdp_env_name)

    cdp_assign_user_role_json = dump_assign_user_resource_role_json(
        cdp_env_crn, role, user, json_skel
    )
    click.echo("-------------------Generated JSON-----------------------------")
    print(json.dumps(cdp_assign_user_role_json, indent=4, sort_keys=True))
    click.echo("--------------------------------------------------------------")

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_assign_user_role_json,
            headers=generate_headers("POST", action_url),
        )

        elem_search_info = {
            "root_index": "resourceAssignments",
            "expected_key_val": {
                "resourceRoleCrn": f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{role}",
                "resourceCrn": cdp_env_crn,
            },
            "present": True,
        }

        click.echo(f"Waiting for assigning {role} for user {user}")

        poll_for_status(
            poll_url=f"{env_url}/listUserAssignedResourceRoles",
            data={"userName": user, "pageSize": 100},
            elem_search_info=elem_search_info,
        )

        click.echo(f"Assigning {role} on cdp user {user} on env {cdp_env_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{user}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_user_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


def unassign_role_from_user(role, user, cdp_env_name, json_skel, dryrun):
    click.echo(f"===Unassigning role {role} from user {user} on env {cdp_env_name}===")
    action_url = f"{env_url}/unassignuserResourceRole"
    cdp_env_crn = get_cdp_env_crn(cdp_env_name)

    cdp_assign_user_role_json = dump_assign_user_resource_role_json(
        cdp_env_crn, role, user, json_skel
    )
    click.echo("-------------------Generated JSON-----------------------------")
    print(json.dumps(cdp_assign_user_role_json, indent=4, sort_keys=True))
    click.echo("--------------------------------------------------------------")

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_assign_user_role_json,
            headers=generate_headers("POST", action_url),
        )

        elem_search_info = {
            "root_index": "resourceAssignments",
            "expected_key_val": {
                "resourceRoleCrn": f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{role}",
                "resourceCrn": cdp_env_crn,
            },
            "present": False,
        }

        click.echo(f"Waiting for unassigning {role} from user {user}")

        poll_for_status(
            poll_url=f"{env_url}/listUserAssignedResourceRoles",
            data={"userName": user, "pageSize": 100},
            elem_search_info=elem_search_info,
        )

        click.echo(f"Unassigning {role} from cdp user {user} on env {cdp_env_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{user}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_user_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option(
    "--action",
    type=click.Choice(["assign-roles-to-def-users", "unassign-role-from-def-users"]),
    required=True,
)
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
def main(dryrun, env, cdp_env_name, action, user, roles, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        assign_user_role_json_skel = json.load(json_file)

    with open(f"{env}_users.json") as json_file:
        users = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)

    for user, roles in users.items():
        user_id = get_user_attr(user_name, "userId")
        for role in roles:
            if action == "assign-roles-to-def-users":
                assign_role_to_user(role, user, cdp_env_name, json_skel, dryrun)
            elif action == "unassign-role-from-def-users":
                unassign_role_from_user(role, user, cdp_env_name, json_skel, dryrun)


if __name__ == "__main__":
    main()
