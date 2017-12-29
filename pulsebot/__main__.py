# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals, print_function

from .pulse import PulseListener
import requests
from datetime import date
from collections import defaultdict


def process_messages(messages):
    builds = defaultdict(
        lambda: {
            'successes': defaultdict(dict),
            'failures': defaultdict(dict),
            'warnings': defaultdict(dict),
        }
    )
    for data in messages:
        payload = data['payload']
        logurl = payload['logurl']
        if 'l10n' in logurl:
            build = builds[payload['buildid']]
            locale = payload['locale']
            status = {0: 'success', 1: 'warnings'}.get(
                payload['status'], 'failures')
            build[status][locale][payload['platform']] = logurl
    return builds


def generate_report(builds):
    build_reports = []
    for buildid, data in builds.items():
        lines = []
        lines.append("<div>")
        lines.append('<p>BuildID: {}\n'.format(buildid))
        for status in ('failures', 'warnings', 'successes'):
            lines.append('<p>{}:\n'.format(status.title()))
            for locale, platforms in sorted(data[status].items()):
                results = []
                for platform, url in sorted(platforms.items()):
                    results.append(
                        '<a href="{url}">{platform}</a>'.format(
                            platform=platform, url=url))
                lines.append("{}({})".format(locale, ", ".join(results)))
        lines.append("</div>")

        build_reports.append("\n".join(lines))

    return build_reports


def send_report(reports):
    if reports:
        message = "\n\n<hr>\n\n".join(reports)
    else:
        message = "<div>No nightly builds to report.</div>"

    message += "\n\n-- "
    message += "\nSent by https://github.com/tomprince/thunderbird-pulse\n"

    requests.post(
        "https://api.mailgun.net/v3/{}/messages".format(
            environ.get("MAILGUN_DOMAIN")),
        auth=("api", environ.get("MAILGUN_APIKEY")),
        data={"from": environ.get("MAILGUN_LIST"),
              "to": [environ.get("MAILGUN_LIST")],
              "subject": "Nightly L10N Repack {}".format(
                  date.today().isoformat(),
              ),
              "html": message})


if __name__ == "__main__":
    from os import _exit as exit
    from os import environ
    pulse = PulseListener(
        user=environ.get("PULSE_USER"),
        password=environ.get("PULSE_PASSWORD"),
        exchange='exchange/build/normalized',
        topic='build.comm-central.#',
        applabel='tp-test',
    )

    builds = {}
    messages = []

    builds = process_messages(pulse.drain())
    reports = generate_report(builds)
    send_report(reports)
    pulse.ack()
    pulse.disconnect()

    exit(0)
