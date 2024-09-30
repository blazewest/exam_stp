/** @odoo-module **/

import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

// Hàm kiểm tra undefined, null và object rỗng
function isUndefined(value) {
    return typeof value === 'undefined';
}

function isNull(value) {
    return value === null;
}

function isObject(value) {
    return value !== null && typeof value === 'object';
}

function isEmpty(value) {
    return Object.keys(value).length === 0;
}

registry
    .category("ir.actions.report handlers")
    .add("py3o_handler", async function (action, options, env) {
        if (action.report_type === "py3o") {
            let url = `/report/py3o/${action.report_name}`;
            const actionContext = action.context || {};

            if (
                isUndefined(action.data) ||
                isNull(action.data) ||
                (isObject(action.data) && isEmpty(action.data))
            ) {
                if (actionContext.active_ids) {
                    var activeIDsPath = "/" + actionContext.active_ids.join(",");
                    url += activeIDsPath;
                }
            } else {
                var serializedOptionsPath =
                    "?options=" + encodeURIComponent(JSON.stringify(action.data));
                serializedOptionsPath +=
                    "&context=" + encodeURIComponent(JSON.stringify(actionContext));
                url += serializedOptionsPath;
            }

            env.services.ui.block();
            try {
                await download({
                    url: "/report/download",
                    data: {
                        data: JSON.stringify([url, action.report_type]),
                        context: JSON.stringify(env.services.user.context),
                    },
                });
            } finally {
                env.services.ui.unblock();
            }

            const onClose = options.onClose;
            if (action.close_on_report_download) {
                return env.services.action.doAction(
                    { type: "ir.actions.act_window_close" },
                    { onClose }
                );
            } else if (onClose) {
                onClose();
            }
            return Promise.resolve(true);
        }
        return Promise.resolve(false);
    });
