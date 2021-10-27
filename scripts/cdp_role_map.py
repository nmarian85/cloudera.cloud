import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops


iam_url = f"{requests_ops.CDP_IAM_ENDPOINT}"


def dump_group_cdp_role_map_role_json(cdp_role, group_name, json_skel):
    assign_group_role_json = dict(json_skel)
    assign_group_role_json["groupName"] = group_name
    assign_group_role_json["role"] = cdp_role
    return assign_group_role_json


def assign_cdp_role_to_group(role, group, json_skel, dryrun):
    click.echo(f"===Assigning role {role} to group {group}===")
    action_url = f"{iam_url}/assignGroupRole"
    role = f"crn:altus:iam:{requests_ops.DEFAULT_REGION}:altus:role:${role}"

    cdp_assign_group_role_json = dump_group_cdp_role_map_role_json(
        role, group, json_skel
    )

    dump_json_dict(cdp_assign_group_role_json)

    if not dryrun:
        requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_assign_group_role_json,
            headers=generate_headers("POST", action_url),
        )

        # elem_search_info = {
        #     "root_index": "resourceAssignments",
        #     "expected_key_val": {
        #         "role": f"{requests_ops.DEFAULT_IAM_CRN}:Role:{role}",
        #         "resourceCrn": cdp_env_crn,
        #     },
        #     "present": True,
        # }

        click.echo(f"Waiting for assigning {role} for group {group}")

        # poll_for_status(
        #     poll_url=f"{iam_url}/listGroupAssignedRoles",
        #     data={"groupName": group, "pageSize": 100},
        #     elem_search_info=elem_search_info,
        # )

        click.echo(f"Assigning {role} on cdp group {group} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{group}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_group_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()


def unassign_cdp_role_from_group(role, group, json_skel, dryrun):
    click.echo(f"===Unassigning role {role} from group {group}===")
    action_url = f"{iam_url}/unassignGroupRole"
    role = f"crn:altus:iam:{requests_ops.DEFAULT_REGION}:altus:role:${role}"

    cdp_assign_group_role_json = dump_group_cdp_role_map_role_json(
        role, group, json_skel
    )

    dump_json_dict(cdp_assign_group_role_json)

    if not dryrun:
        requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_assign_group_role_json,
            headers=generate_headers("POST", action_url),
        )

        # elem_search_info = {
        #     "root_index": "resourceAssignments",
        #     "expected_key_val": {
        #         "role": f"{requests_ops.DEFAULT_IAM_CRN}:Role:{role}",
        #         "resourceCrn": cdp_env_crn,
        #     },
        #     "present": False,
        # }

        click.echo(f"Waiting for unassigning {role} from group {group}")

        # poll_for_status(
        #     poll_url=f"{iam_url}/listGroupAssignedRoles",
        #     data={"groupName": group, "pageSize": 100},
        #     elem_search_info=elem_search_info,
        # )

        click.echo(f"Unassigning {role} from cdp group {group} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{group}_{role}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_assign_group_role_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()
