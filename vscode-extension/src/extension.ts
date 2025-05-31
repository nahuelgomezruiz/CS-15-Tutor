import * as vscode from 'vscode';
import { ChatViewProvider } from './chatViewProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('CS15 Tutor extension is now active!');

    // Create and register the webview provider
    const provider = new ChatViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            'cs15-tutor.chatView',
            provider,
            {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            }
        )
    );

    // Register the command to open the chat
    context.subscriptions.push(
        vscode.commands.registerCommand('cs15-tutor.openChat', () => {
            vscode.commands.executeCommand('workbench.view.explorer');
        })
    );
}

export function deactivate() {} 