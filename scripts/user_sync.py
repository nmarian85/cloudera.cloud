import click
import sys
import json
import os
from utils import show_progress, poll_for_status, dump_json_dict
from env_mgmt import get_env_info, get_all_cdp_envs
from cdpv1sign import generate_headers
import requests_ops
import requests


def dump_sync_all_users_json(json_skel, cdp_env_name=None):
    sync_json = dict(json_skel)
    if cdp_env_name:
        sync_json["environmentNames"] = [cdp_env_name]
    else:
        del sync_json["environmentNames"]
    return sync_json


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
    help="""Optional argument. When it is not specified the sync will happen for all envs. 
    Please see {env}.json file where you defined the CDP env name""",
    required=False,
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
        sync_json_skel = json.load(json_file)

    sync_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"
    action_url = f"{sync_url}/syncAllUsers"

    if cdp_env_name:
        click.echo(f"========Syncing all users on {cdp_env_name}====")
        cdp_sync_json = dump_sync_all_users_json(sync_json_skel, cdp_env_name)
        cdp_envs = [cdp_env_name]
    else:
        click.echo(f"========Syncing all users on all envs====")
        cdp_sync_json = dump_sync_all_users_json(sync_json_skel)
        cdp_envs = [env["environmentName"] for env in get_all_cdp_envs()]

    dump_json_dict(cdp_sync_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_sync_json,
            headers=generate_headers("POST", action_url),
        )

        for cdp_env in cdp_envs:
            click.echo(f"Waiting for sync on env {cdp_env}")

            poll_url = f"{sync_url}/getEnvironmentUserSyncState"

            elem_search_info = {
                "root_index": "",
                "expected_key_val": {"state": "COMPLETED"},
                "present": True,
            }

            poll_for_status(
                poll_url=poll_url,
                elem_search_info=elem_search_info,
                data={"environmentName": cdp_env},
            )

            click.echo(f"Action DONE")
        # dumping file so that Gitlab will back it up
        with open("sync_users.json", "w", encoding="utf-8") as f:
            json.dump(cdp_sync_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


if __name__ == "__main__":
    main()
