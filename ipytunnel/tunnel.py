#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Vidar Tonaas Fauske.
# Distributed under the terms of the Modified BSD License.

"""
TODO: Add module docstring
"""

from contextlib import contextmanager
from ipykernel.comm import Comm
from ipykernel.kernelbase import Kernel
from ipykernel.jsonutil import json_clean
from jupyter_client.adapter import adapt

__protocol_version__ = "1.0.0"


def _convert_message(comm, **kwargs):
    data = kwargs.pop('data', None) or {}
    metadata = kwargs.pop('metadata', None) or {}
    buffers = kwargs.pop('buffers', None)
    content = dict(data=data, comm_id=comm.comm_id, **kwargs)
    msg = dict(content=content, metadata=metadata)
    if buffers:
        msg['n_buffers'] = len(buffers)
    return (msg, buffers)


@contextmanager
def hold_comm_open(kernel=None):
    if kernel is None:
        if not Kernel.initialized():
            raise ValueError(
                'No kernel passed, and current kernel not initialized')
        kernel = Kernel.instance()

    comm_manager = getattr(kernel, 'comm_manager', None)
    if comm_manager is None:
        raise RuntimeError("Comms cannot be opened without a kernel "
                           "and a comm_manager attached to that kernel.")

    patched_comms = []

    messages = []
    buffers = []

    def patched_register_comm(comm):
        original_publish_msg = comm._publish_msg

        def patched_publish_msg(msg_type, **kwargs):
            if msg_type != 'comm_open':
                original_publish_msg(msg_type, **kwargs)
            msg, msg_bufs = _convert_message(comm, **kwargs)
            messages.append(msg)
            buffers.extend(msg_bufs)

        patched_comms.append((comm, original_publish_msg))
        comm._publish_msg = patched_publish_msg

    original_register_comm = comm_manager.register_comm
    comm_manager.register_comm = patched_register_comm

    try:
        yield
    finally:
        comm_manager.register_comm = original_register_comm
        for comm, original_publish_msg in patched_comms:
            comm._publish_msg = original_publish_msg

    data = dict(
        messages=messages,
    )

    args = dict(target_name='jupyter.widget-tunnel',
                data=data,
                buffers=buffers,
                metadata={'version': __protocol_version__})

    comm = Comm(**args)
    comm.close()
