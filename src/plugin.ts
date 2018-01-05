// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import {
  JupyterLabPlugin, JupyterLab
} from '@jupyterlab/application';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  INotebookModel, NotebookPanel
} from '@jupyterlab/notebook';

import {
  Kernel, KernelMessage
} from '@jupyterlab/services';

import {
  IJupyterWidgetRegistry
 } from '@jupyter-widgets/base';

import { Token, JSONObject } from '@phosphor/coreutils';

import {
  IDisposable, DisposableDelegate
} from '@phosphor/disposable';

import {
  JUPYTER_EXTENSION_VERSION
} from './version';

import {
  processTunnelMessage
} from './messages';


const EXTENSION_ID = 'jupyter.extensions.widget-tunnel';


export declare const IWidgetTunnel: Token<IWidgetTunnel>;
export interface IWidgetTunnel {
}

/**
 * The example plugin.
 */
const examplePlugin: JupyterLabPlugin<IWidgetTunnel> = {
  id: EXTENSION_ID,
  activate: activateWidgetExtension,
  provides: IWidgetTunnel,
  autoStart: true
};

export default examplePlugin;

export
type IWidgetTunnelExtension = DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>;


export
class TunnelManager implements IDisposable {
  constructor(context: DocumentRegistry.IContext<INotebookModel>) {
    this._context = context;
    context.session.kernelChanged.connect((sender, kernel) => {
      this.newKernel(kernel);
    });

    if (context.session.kernel) {
      this.newKernel(context.session.kernel);
    }
  }

  /**
  * Register a new kernel
  * @param kernel The new kernel.
  */
  newKernel(kernel: Kernel.IKernelConnection | null) {
    if (this._commRegistration) {
      this._commRegistration.dispose();
    }
    if (!kernel) {
      return;
    }
    this._commRegistration = kernel.registerCommTarget('jupyter.widget-tunnel',
      (comm, msg) => {
        this.handle_comm_open(kernel, comm, msg);
      });
  }

  /**
   * Get whether the manager is disposed.
   *
   * #### Notes
   * This is a read-only property.
   */
  get isDisposed(): boolean {
    return this._context === null;
  }

  /**
   * Dispose the resources held by the manager.
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }

    if (this._commRegistration) {
      this._commRegistration.dispose();
    }
    this._context = null;
  }

  /**
   * Handler of tunnel open.
   *
   * @param kernel 
   * @param comm 
   * @param msg 
   */
  handle_comm_open(kernel: Kernel.IKernelConnection, comm: Kernel.IComm, msg: KernelMessage.ICommOpenMsg) {
    // Should deserialize bunch, and pass it along to proper channels
    let messages = processTunnelMessage(msg);
    for (let commMsg of messages) {
      // FIXME: Currently, we have to dig into private API...
      (kernel as any)._handleCommOpen(commMsg as KernelMessage.ICommOpenMsg);
    }
  }

  _commRegistration: IDisposable;

  private _context: DocumentRegistry.IContext<DocumentRegistry.IModel> | null;
}


export
class WidgetTunnelExtension implements IWidgetTunnelExtension {
  /**
   * Create a new extension object.
   */
  createNew(nb: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    let commManager = new TunnelManager(context);
    return new DisposableDelegate(() => {
      commManager.dispose();
    });
  }
}

/**
 * Activate the widget extension.
 */
function activateWidgetExtension(app: JupyterLab): IWidgetTunnel {
  let extension = new WidgetTunnelExtension();
  app.docRegistry.addWidgetExtension('Notebook', extension);
  return {};
}
