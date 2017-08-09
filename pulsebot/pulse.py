# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import socket
from kombu import Exchange
from mozillapulse.config import PulseConfiguration
from mozillapulse.consumers import GenericConsumer


class PulseConsumer(GenericConsumer):
    def __init__(self, exchange, **kwargs):
        super(PulseConsumer, self).__init__(
            PulseConfiguration(**kwargs), exchange, **kwargs)


class PulseListener(object):
    def __init__(self, user=None, password=None, exchange=None, topic='#',
                 applabel=None):
        self.exchange = exchange
        self.topic = topic

        if not applabel:
            # Let's generate a unique label for the script
            try:
                import uuid
                self.applabel = 'pulsebot-%s' % uuid.uuid4()
            except:
                from datetime import datetime
                self.applabel = 'pulsebot-%s' % datetime.now()
        else:
            self.applabel = applabel

        self.auth = {
            'user': user,
            'password': password,
        }

    def pulse_listener(self, callback, timeout):
        while True:
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
            exchange = Exchange(pulse.exchange, type='topic')
            queue = pulse._create_queue(exchange, pulse.topic[0])
            consumer = pulse.connection.Consumer(
                queue, auto_declare=False, callbacks=[pulse.callback])
            consumer.queues[0].queue_declare()
            # Bind to the first key.
            consumer.queues[0].queue_bind()

            with consumer:
                while True:
                    try:
                        pulse.connection.drain_events(timeout=60)
                    except socket.timeout:
                        pass
                        timeout()
                    except Exception:
                        # If we failed for some other reason than the timeout,
                        # cleanup and create a new connection.
                        break

            pulse.disconnect()
