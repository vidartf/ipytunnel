"""Base class for a Comm"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import uuid

from ipykernel.kernelbase import Kernel

from ipykernel.jsonutil import json_clean
from traitlets import log



class Comm(object):
    """Class for communicating between a Frontend and a Kernel

    Different from the standard comm in the following ways:
     - Not trait based, so cheaper
     - Hook for capturing open message
    """

    def __init__(self, target_name='', data=None, metadata=None, buffers=None, **kwargs):
        self.primary = True  # Am I the primary or secondary Comm?
        self.target_name = target_name
        # requirejs module from which to load comm target
        self.target_module = kwargs.get('target_module', None)
        self.open_hook = None
        self._closed = True
        self._close_callback = None
        self._msg_callback = None
        try:
            self.kernel = kwargs['kernel']
        except KeyError:
            if Kernel.initialized():
                self.kernel = Kernel.instance()
            else:
                self.kernel = None
        try:
            self.comm_id = kwargs['comm_id']
        except KeyError:
            self.comm_id = uuid.uuid4().hex
        self.topic = kwargs.get('topic', ('comm-%s' % self.comm_id).encode('ascii'))
        self.log = log.get_logger()

        if self.kernel:
            if self.primary:
                # I am primary, open my peer.
                self.open(data=data, metadata=metadata, buffers=buffers)
            else:
                self._closed = False

    def _publish_msg(self, msg_type, data=None, metadata=None, buffers=None, **keys):
        """Helper for sending a comm message on IOPub"""
        data = {} if data is None else data
        metadata = {} if metadata is None else metadata
        content = json_clean(dict(data=data, comm_id=self.comm_id, **keys))
        self.kernel.session.send(
            self.kernel.iopub_socket,
            msg_type,
            content,
            metadata=json_clean(metadata),
            parent=self.kernel._parent_header,
            ident=self.topic,
            buffers=buffers,
        )

    def __del__(self):
        """trigger close on gc"""
        self.close()

    # publishing messages

    def open(self, data=None, metadata=None, buffers=None):
        """Open the frontend-side version of this comm"""
        comm_manager = getattr(self.kernel, 'comm_manager', None)
        if comm_manager is None:
            raise RuntimeError("Comms cannot be opened without a kernel "
                               "and a comm_manager attached to that kernel.")

        comm_manager.register_comm(self)
        try:
            f_msg = self.open_hook or self._publish_msg
            f_msg('comm_open',
                  data=data, metadata=metadata, buffers=buffers,
                  target_name=self.target_name, target_module=self.target_module,
                 )
            self._closed = False
        except:
            comm_manager.unregister_comm(self)
            raise

    def close(self, data=None, metadata=None, buffers=None):
        """Close the frontend-side version of this comm"""
        if self._closed:
            # only close once
            return
        self._closed = True
        # nothing to send if we have no kernel
        # can be None during interpreter cleanup
        if not self.kernel:
            return
        self._publish_msg(
            'comm_close', data=data, metadata=metadata, buffers=buffers,
        )
        self.kernel.comm_manager.unregister_comm(self)

    def send(self, data=None, metadata=None, buffers=None):
        """Send a message to the frontend-side version of this comm"""
        self._publish_msg(
            'comm_msg', data=data, metadata=metadata, buffers=buffers,
        )

    # registering callbacks

    def on_close(self, callback):
        """Register a callback for comm_close

        Will be called with the `data` of the close message.

        Call `on_close(None)` to disable an existing callback.
        """
        self._close_callback = callback

    def on_msg(self, callback):
        """Register a callback for comm_msg

        Will be called with the `data` of any comm_msg messages.

        Call `on_msg(None)` to disable an existing callback.
        """
        self._msg_callback = callback

    # handling of incoming messages

    def handle_close(self, msg):
        """Handle a comm_close message"""
        self.log.debug("handle_close[%s](%s)", self.comm_id, msg)
        if self._close_callback:
            self._close_callback(msg)

    def handle_msg(self, msg):
        """Handle a comm_msg message"""
        self.log.debug("handle_msg[%s](%s)", self.comm_id, msg)
        if self._msg_callback:
            shell = self.kernel.shell
            if shell:
                shell.events.trigger('pre_execute')
            self._msg_callback(msg)
            if shell:
                shell.events.trigger('post_execute')


__all__ = ['Comm']
