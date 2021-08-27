from click import echo


def show_progress(msg):
    sep = "=" * 10
    echo("\n" + sep + "> " + msg.upper() + " <" + sep)
