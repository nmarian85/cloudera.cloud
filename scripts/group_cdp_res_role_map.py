import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from env_mgmt import get_cdp_env_crn
from cdp_res_role_map import (
    assign_cdp_res_role_to_group,
    unassign_cdp_res_role_to_group,
)
import requests_ops


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option(
    "--action", type=click.Choice(["assign", "unassign"]), required=True,
)
@click.option(
    "--env",
    type=click.Choice(["lab", "tst", "dev", "acc", "prd"]),
    help="ECB environment: lab, tst, etc.",
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
        group_cdprole_json_skel = json.load(json_file)

    with open(f"conf/{env}/{cdp_env_name}/groups.json") as json_file:
        groups = json.load(json_file)

    cdp_env_crn = get_cdp_env_crn(cdp_env_name)

    for group, roles in groups.items():
        for role in roles["resource_roles"]:
            if action == "assign":
                assign_cdp_res_role_to_group(
                    cdp_env_crn,
                    role,
                    group,
                    cdp_env_name,
                    group_cdprole_json_skel,
                    dryrun,
                )
            elif action == "unassign":
                unassign_cdp_res_role_to_group(
                    cdp_env_crn,
                    role,
                    group,
                    cdp_env_name,
                    group_cdprole_json_skel,
                    dryrun,
                )


if __name__ == "__main__":
    main()
