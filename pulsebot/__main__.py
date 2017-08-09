# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals, print_function

from pulse import PulseListener


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

    buildid = None
    successes = []
    failures = {}
    messages = []

    try:

        def report():
            global buildid, failures, successes, messages
            print('BuildID: {}'.format(buildid))
            print('Success: {}'.format(', '.join(successes)))
            print('Failures:')
            for locale, url in failures:
                print('{}: {}'.format(locale, url))
            print()

            buildid = "{} (repeat)".format(buildid)
            successes = []
            failures = {}
            for message in messages:
                message.ack()
            messages = []

        def callback(data, message):
            global buildid
            payload = data['payload']
            if 'l10n' in payload['logurl']:
                if buildid != payload['buildid']:
                    report()
                    buildid = payload['buildid']
                if payload['status'] == 0:
                    successes.append(payload['locale'])
                else:
                    failures[payload['locale']] = payload['logurl']
        pulse.pulse_listener(callback, timeout=report)
    except KeyboardInterrupt:
        pass
    exit(0)
