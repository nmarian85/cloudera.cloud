import click
import sys
import json
import os
from utils import show_progress, poll_for_status, dump_json_dict
from env_mgmt import get_cdp_env_crn
from cdpv1sign import generate_headers
import requests_ops
import requests

iam_url = f"{requests_ops.CDP_IAM_ENDPOINT}"


def get_user_attr(user_name, attr, next_token=""):
    action_url = f"{iam_url}/listUsers"
    response = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        headers=generate_headers("POST", action_url),
        data={"startingToken": next_token},
    )
    for user_info in response["users"]:
        if user_info["workloadUsername"] == user_name:
            return user_info[attr]
    if "nextToken" in response:
        return get_user_attr(user_name, attr, response["nextToken"])


def dump_user_cdprole_map_json(cdp_env_crn, cdp_role, user_name, json_skel):
    assign_user_role_json = dict(json_skel)
    resource_role_crn = f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{cdp_role}"
    assign_user_role_json["user"] = user_name
    assign_user_role_json["resourceRoleCrn"] = resource_role_crn
    assign_user_role_json["resourceCrn"] = cdp_env_crn
    return assign_user_role_json


def dump_group_cdprole_map_role_json(cdp_env_crn, cdp_role, group_name, json_skel):
    assign_group_role_json = dict(json_skel)
    resource_role_crn = f"{requests_ops.DEFAULT_IAM_CRN}:resourceRole:{cdp_role}"
    assign_group_role_json["groupName"] = group_name
    assign_group_role_json["resourceRoleCrn"] = resource_role_crn
    assign_group_role_json["resourceCrn"] = cdp_env_crn
    return assign_group_role_json


def assign_cdprole_to_group(cdp_env_crn, role, group, cdp_env_name, json_skel, dryrun):
    click.echo(f"===Assigning role {role} to group {group} on env {cdp_env_name}===")
    action_url = f"{iam_url}/assignGroupResourceRole"

    cdp_assign_group_role_json = dump_group_cdprole_map_role_json(
        cdp_env_crn, role, group, json_skel
    )

    dump_json_dict(cdp_assign_group_role_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_assign_group_role_json,
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

        click.echo(f"Waiting for assigning {role} for group {group}")

        poll_for_status(
            poll_url=f"{iam_url}/listGroupAssignedResourceRoles",
            data={"groupName": group, "pageSize": 100},
            elem_search_info=elem_search_info,
        )

        click.echo(f"Assigning {role} on cdp group {group} on env {cdp_env_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{group}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_group_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


def unassign_role_from_group(cdp_env_crn, role, group, cdp_env_name, json_skel, dryrun):
    click.echo(f"===Unassigning role {role} from group {group} on env {cdp_env_name}===")
    action_url = f"{iam_url}/unassignGroupResourceRole"

    cdp_assign_group_role_json = dump_group_cdprole_map_role_json(
        cdp_env_crn, role, group, json_skel
    )

    dump_json_dict(cdp_assign_group_role_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_assign_group_role_json,
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

        click.echo(f"Waiting for unassigning {role} from group {group}")

        poll_for_status(
            poll_url=f"{iam_url}/listGroupAssignedResourceRoles",
            data={"groupName": group, "pageSize": 100},
            elem_search_info=elem_search_info,
        )

        click.echo(f"Unassigning {role} from cdp group {group} on env {cdp_env_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{group}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_group_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


def assign_role_to_user(role, user, cdp_env_crn, cdp_env_name, json_skel, dryrun):
    click.echo(f"===Assigning role {role} to user {user} on env {cdp_env_name}===")
    action_url = f"{iam_url}/assignuserResourceRole"

    cdp_assign_user_role_json = dump_user_cdprole_map_json(cdp_env_crn, role, user, json_skel)

    dump_json_dict(cdp_assign_user_role_json)

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
            poll_url=f"{iam_url}/listUserAssignedResourceRoles",
            data={"userName": user, "pageSize": 100},
            elem_search_info=elem_search_info,
        )

        click.echo(f"Assigning {role} on cdp user {user} on env {cdp_env_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{user}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_user_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


def unassign_role_from_user(cdp_env_crn, role, user, cdp_env_name, json_skel, dryrun):
    click.echo(f"===Unassigning role {role} from user {user} on env {cdp_env_name}===")
    action_url = f"{iam_url}/unassignuserResourceRole"

    cdp_assign_user_role_json = dump_user_cdprole_map_json(cdp_env_crn, role, user, json_skel)

    dump_json_dict(cdp_assign_user_role_json)

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
            poll_url=f"{iam_url}/listUserAssignedResourceRoles",
            data={"userName": user, "pageSize": 100},
            elem_search_info=elem_search_info,
        )

        click.echo(f"Unassigning {role} from cdp user {user} on env {cdp_env_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{user}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_user_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()
