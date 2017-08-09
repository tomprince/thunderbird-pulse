# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals, print_function

from .pulse import PulseListener
import requests
from datetime import date


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

    def callback(data, message):
        messages.append(message)
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

    build_reports = []
    for buildid, data in builds.items():
        lines = []
        lines.append('BuildID: {}\n'.format(buildid))
        lines.append('Success: {}\n'.format(', '.join(data['successes'])))
        lines.append('Failures:')
        for locale, url in data['failures']:
            lines.append('{}: {}\n'.format(locale, url))
        build_reports.append("\n".join(lines))

    if build_reports:
        message = "\n".join(build_reports)
    else:
        message = "No nightly builds to report."

    requests.post(
        "https://api.mailgun.net/v3/{}/messages".format(environ.get("MAILGUN_DOMAIN")),
        auth=("api", environ.get("MAILGUN_APIKEY")),
        data={"from": environ.get("MAILGUN_LIST"),
              "to": [environ.get("MAILGUN_LIST")],
              "subject": "Nightly L10N Repack {}".format(
                  date.today().isoformat(),
              ),
              "text": message})

    for message in messages:
        message.ack()
    pulse.drain(callback)

    exit(0)
