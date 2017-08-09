# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from mozillapulse.config import PulseConfiguration
from mozillapulse.consumers import GenericConsumer


class PulseConsumer(GenericConsumer):
    def __init__(self, exchange, **kwargs):
        super(PulseConsumer, self).__init__(
            PulseConfiguration(**kwargs), exchange, **kwargs)


class PulseListener(object):
    def __init__(self, user, password, exchange, topic, applabel):
        self.exchange = exchange
        self.topic = topic
        self.applabel = applabel
        self.auth = {
            'user': user,
            'password': password,
        }

    def drain(self, callback):
        # Connect to pulse
        pulse = PulseConsumer(
            exchange=self.exchange, applabel=self.applabel, durable=True,
            **self.auth)

        # Tell pulse that you want to listen for all messages ('#' is
        # everything) and give a function to call every time there is a
        # message
        pulse.configure(topic=[self.topic], callback=callback)

        # Manually do the work of pulse.listen() so as to be able to
        # cleanly get out of it if necessary.
        consumer = pulse._build_consumer(callback=callback)

        with consumer:
            pulse.connection.drain_events(timeout=60)

        pulse.disconnect()
