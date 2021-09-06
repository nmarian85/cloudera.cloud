import click
import sys
import json
import os
from utils import show_progress, get_env_info, poll_for_status, get_user_attr
from cdpv1sign import generate_headers
import requests_ops
import requests


def dump_create_mapping_json(cdp_env_name, data_role_arn, user_crn, aws_role, json_skel):
    """[summary]

    Args:
        mapping_info ([type]): [description]
        json_skel ([type]): [description]

    Returns:
        [type]: [description]
    """
    mapping_json = dict(json_skel)
    mapping_json["environmentName"] = cdp_env_name
    mapping_json["dataAccessRole"] = data_role_arn
    mapping_json["mappings"] = {"accessorCrn": user_crn, "role": aws_role}

    # Whether to install an empty set of individual mappings, deleting any existing mappings.
    # The --set-empty-mappings option is required if --mappings is omitted or if its value is
    # an empty list,
    # and disallowed otherwise.
    mapping_json["setEmptyMappings"] = False
    return mapping_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
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
def main(dryrun, env, cdp_env_name, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        mapping_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    role_iam_arn = f'arn:aws:iam::{cdp_env_info["account_id"]}'
    data_role_arn = f'{role_iam_arn}:role/{cdp_env_info["data_role"]}'
    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"

    with open(f"{env}_users.json") as json_file:
        users = json.load(json_file)

    for user in users["cdp_env_name"].items():
        click.echo(f"========Setting idbroker mapping for user {user} on {cdp_env_name}====")
        user_crn = get_user_attr(user, "crn")
        aws_role = f"{role_iam_arn}:role/devo-discdata-s3-access-{user}-iam-role"

        cdp_mapping_json = dump_create_mapping_json(
            cdp_env_name, data_role_arn, user_crn, aws_role, mapping_json_skel
        )
        action_url = f"{env_url}/setIdBrokerMappings"

        click.echo("-------------------Generated JSON-----------------------------")
        print(json.dumps(cdp_mapping_json, indent=4, sort_keys=True))
        click.echo("--------------------------------------------------------------")

        if not dryrun:
            response = requests_ops.send_http_request(
                srv_url=action_url,
                req_type="post",
                data=cdp_mapping_json,
                headers=generate_headers("POST", action_url),
            )

            click.echo(f"Waiting for idbroker mapping on environment {cdp_env_name}")
            elem_search_info = {
                "root_index": "mappings",
                "expected_key_val": {"accessorCrn": user_crn, "role": aws_role},
                "present": True,
            }

            poll_url = f"{env_url}/getIdBrokerMappings"
            poll_for_status(
                poll_url=poll_url,
                elem_search_info=elem_search_info,
                data={"environmentName": cdp_env_name},
            )
            click.echo(f"idbroker mapping for user {user} on environment {cdp_env_name} DONE")
            # dumping file so that Gitlab will back it up
            with open(f"{user}_idbroker_mapping.json", "w", encoding="utf-8") as f:
                json.dump(cdp_mapping_json, f, ensure_ascii=False, indent=4)
        click.echo(f"===========================================================")
        click.echo()


# syncIdBrokerMappings

if __name__ == "__main__":
    main()
