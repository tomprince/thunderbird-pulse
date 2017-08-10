# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals, print_function

from .pulse import PulseListener
import requests
from datetime import date


def process_messages(messages):
    builds = {}
    for data in messages:
        payload = data['payload']
        if 'l10n' in payload['logurl']:
            build = builds.setdefault(
                payload['buildid'],
                {'successes': [], 'failures': {}},
            )
            if payload['status'] == 0:
                build['successes'].append(payload['locale'])
            else:
                build['failures'][payload['locale']] = payload['logurl']
    return builds


def generate_report(builds):
    build_reports = []
    for buildid, data in builds.items():
        successes = ', '.join(sorted(data['successes']))
        lines = []
        lines.append('BuildID: {}\n'.format(buildid))
        lines.append('Success: {}\n'.format(successes))
        lines.append('Failures:')
        for locale, url in sorted(data['failures'].items()):
            lines.append('{}: {}\n'.format(locale, url))
        build_reports.append("\n".join(lines))

    return build_reports


def send_report(reports):
    if reports:
        message = "\n".join(reports)
    else:
        message = "No nightly builds to report."

    message += "\n\n-- \nSent by https://github.com/tomprince/thunderbird-pulse\n"

    requests.post(
        "https://api.mailgun.net/v3/{}/messages".format(environ.get("MAILGUN_DOMAIN")),
        auth=("api", environ.get("MAILGUN_APIKEY")),
        data={"from": environ.get("MAILGUN_LIST"),
              "to": [environ.get("MAILGUN_LIST")],
              "subject": "Nightly L10N Repack {}".format(
                  date.today().isoformat(),
              ),
              "text": message})


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
