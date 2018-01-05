// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import {
  JSONObject
} from '@phosphor/coreutils';

import {
  KernelMessage
} from '@jupyterlab/services';


export
interface IBunchedMessage {
  n_buffers?: number;
  content: KernelMessage.ICommOpen;
  metadata: JSONObject;
}


export
interface ITunnelMessageData {
  messages: IBunchedMessage[]
}


/**
 * Extract the bunched comm open messages from a tunnel message
 * @param msg 
 */
export
function processTunnelMessage(msg:  KernelMessage.ICommOpenMsg): KernelMessage.ICommOpenMsg[] {
  let data = (msg.content.data as any as ITunnelMessageData);
  let buffers = msg.buffers || [];
  let i = 0;
  let messages = [];
  for (let packedMsg of data.messages) {
    let commMsg: KernelMessage.ICommOpenMsg = KernelMessage.createMessage(
      {
        msgType: 'comm_open',
        channel: 'iopub',
        session: '',
      }, packedMsg.content,
    packedMsg.metadata) as any;
    if (packedMsg.n_buffers) {
      commMsg.buffers = buffers.slice(i, i + packedMsg.n_buffers);
      i += packedMsg.n_buffers;
    }
    messages.push(commMsg);
  }
  return messages;
}