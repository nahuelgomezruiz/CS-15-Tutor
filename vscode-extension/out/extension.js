"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const chatViewProvider_1 = require("./chatViewProvider");
function activate(context) {
    console.log('CS15 Tutor extension is now active!');
    // Create and register the webview provider
    const provider = new chatViewProvider_1.ChatViewProvider(context.extensionUri);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('cs15-tutor.chatView', provider, {
        webviewOptions: {
            retainContextWhenHidden: true
        }
    }));
    // Register the command to open the chat
    context.subscriptions.push(vscode.commands.registerCommand('cs15-tutor.openChat', () => {
        vscode.commands.executeCommand('workbench.view.explorer');
    }));
}
exports.activate = activate;
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map