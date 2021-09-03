import click
import sys
import json
import os
from utils import show_progress, get_env_info, poll_for_status
from cdpv1sign import generate_headers
import requests_ops
import requests


def dump_sync_all_users_json(json_skel, cdp_env_name=None):
    sync_json = dict(json_skel)
    if cdp_env_name:
        sync_json["environmentNames"] = [cdp_env_name]
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

    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"
    action_url = f"{env_url}/syncAllUsers"

    if cdp_env_name:
        click.echo(f"========Syncing all users on {cdp_env_name}====")
        cdp_env_info = get_env_info(env, cdp_env_name)
        cdp_sync_json = dump_sync_all_users_json(sync_json_skel, cdp_env_name)
    else:
        click.echo(f"========Syncing all users on all envs====")
        cdp_sync_json = dump_sync_all_users_json(sync_json_skel)

    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"
    click.echo("-------------------Generated JSON-----------------------------")
    print(json.dumps(cdp_sync_json, indent=4, sort_keys=True))
    click.echo("--------------------------------------------------------------")

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_sync_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for sync")

        poll_url = f"{env_url}/syncStatus"

        elem_search_info = {
            "root_index": "",
            "expected_key_val": {"operationId": response["operationId"], "status": "COMPLETED"},
            "present": True,
        }

        poll_for_status(poll_url=poll_url, elem_search_info=elem_search_info)

        click.echo(f"Action DONE")
        # dumping file so that Gitlab will back it up
        with open("sync_users.json", "w", encoding="utf-8") as f:
            json.dump(cdp_sync_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


if __name__ == "__main__":
    main()
