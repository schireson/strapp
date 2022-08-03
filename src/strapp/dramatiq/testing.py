import contextlib

import dramatiq
from dramatiq.brokers.stub import StubBroker


@contextlib.contextmanager
def worker_context(
    broker: StubBroker, actor: dramatiq.Actor = None, worker_timeout=100, worker_threads=1,
):
    worker = dramatiq.Worker(broker, worker_timeout=worker_timeout, worker_threads=worker_threads)
    worker.start()

    yield worker

    if actor:
        broker.join(actor.queue_name, fail_fast=True)

    worker.join()
    worker.stop()
