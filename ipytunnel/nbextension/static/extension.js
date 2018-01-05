define([
    "base/js/namespace",
    "base/js/events",
    "notebook/js/outputarea",
    "./index"
], function(Jupyter, events, outputarea, tunnel) {
    "use strict";

    window['requirejs'].config({
        map: {
            '*': {
                'jupyter-widget-tunnel': 'nbextensions/jupyter-widget-tunnel/index',
            },
        }
    });

    function register() {
        /**
         * Create a widget manager for a kernel instance.
         */
        function newKernel(kernel) {
            if (kernel.comm_manager) {
                // Register with the comm manager.
                kernel.comm_manager.register_target('jupyter.widget-tunnel', function(comm, msg) {
                    handle_comm_open(kernel, comm, msg);
                });
            }
        };

        function handle_comm_open(kernel, comm, msg) {
            var messages = tunnel.processTunnelMessage(msg);
            for (var i = 0; i < messages.length; ++i) {
                kernel.comm_manager.comm_open(messages[i]);
            }
        };

        // When a kernel is created, create a comm manager.
        events.on('kernel_created.Kernel kernel_created.Session', function(event, data) {
            newKernel(data.kernel);
        });

        // If a kernel already exists, create a widget manager.
        if (Jupyter.notebook && Jupyter.notebook.kernel) {
            newKernel(Jupyter.notebook.kernel);
        }
    }

    // Export the required load_ipython_extention
    return {
        load_ipython_extension : function() {
            register();
        }
    };
});
