import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from env_mgmt import get_cdp_env_crn
from cdp_role_map import assign_cdp_role_to_group, unassign_cdp_role_from_group
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
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        group_cdprole_json_skel = json.load(json_file)

    with open(f"conf/{env}/tenant/groups.json") as json_file:
        groups = json.load(json_file)

    for group, roles in groups.items():
        for role in roles["mgt_roles"]:
            if action == "assign":
                assign_cdp_role_to_group(
                    role, group, group_cdprole_json_skel, dryrun,
                )
            elif action == "unassign":
                unassign_cdp_role_from_group(
                    role, group, group_cdprole_json_skel, dryrun,
                )


if __name__ == "__main__":
    main()
