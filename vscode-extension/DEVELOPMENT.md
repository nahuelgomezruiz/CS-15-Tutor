# CS15 Tutor Extension - Development Guide

## Initial Setup (One-time)

1. **Install Prerequisites**
   - Node.js (v16 or higher)
   - VSCode
   - Git

2. **Install Dependencies**
   ```bash
   cd vscode-extension
   npm install
   ```

3. **Install Global Tools**
   ```bash
   npm install -g @vscode/vsce
   ```

## Daily Development Workflow

### 1. Start the API Server
```bash
# From the repository root
cd api-server
python index.py
```
Keep this running on port 5000.

### 2. Open the Extension Project
```bash
# In VSCode
code vscode-extension
```

### 3. Start Development Mode
1. Press `F5` to launch Extension Development Host
2. A new VSCode window opens with your extension loaded
3. Click the CS15 Tutor icon in the activity bar to test

### 4. Make Changes

**Key Files to Edit:**
- `src/chatViewProvider.ts` - Main chat interface and logic
- `src/extension.ts` - Extension activation and setup
- `package.json` - Extension metadata and configuration
- `icons/cs15-icon.svg` - Extension icon

**After Making Changes:**
1. Save your files
2. In the Extension Development Host window, press `Ctrl+R` (or `Cmd+R` on Mac) to reload
3. Test your changes

### 5. Debug Issues

**View Console Output:**
- In the Extension Development Host: `Ctrl+Shift+I` (or `Cmd+Option+I` on Mac)
- Check the Console tab for errors

**Debug Extension Code:**
- Set breakpoints in your TypeScript files
- Use the Debug Console in the main VSCode window

### 6. Test Thoroughly

Before packaging:
- [ ] Test sending messages
- [ ] Test Enter key vs Shift+Enter
- [ ] Test markdown rendering
- [ ] Test error handling (stop API server and try)
- [ ] Test textarea auto-resize
- [ ] Test with different VSCode themes

## Building for Distribution

### 1. Update Version
In `package.json`:
```json
"version": "1.0.1"  // Increment version
```

### 2. Compile TypeScript
```bash
npm run compile
```

### 3. Package Extension
```bash
vsce package --no-yarn
```

This creates `cs15-tutor-x.x.x.vsix`

### 4. Test the Package
1. Install the `.vsix` file in a fresh VSCode instance
2. Verify all features work

## Common Development Tasks

### Adding a New Feature
1. Plan the feature
2. Edit relevant TypeScript files
3. Test in Extension Development Host
4. Update README if needed

### Fixing Bugs
1. Reproduce the issue
2. Add console.log statements for debugging
3. Fix the code
4. Test the fix thoroughly

### Updating UI/Styling
- Edit CSS in `chatViewProvider.ts`
- Use VSCode theme variables for consistency
- Test with light and dark themes

### Updating Dependencies
```bash
npm update
npm audit fix
```

## File Structure
```
vscode-extension/
├── src/
│   ├── extension.ts          # Extension entry point
│   └── chatViewProvider.ts   # Chat UI and API communication
├── out/                      # Compiled JavaScript (git ignored)
├── icons/
│   └── cs15-icon.svg        # Extension icon
├── package.json             # Extension manifest
├── tsconfig.json            # TypeScript config
├── README.md                # User documentation
└── DEVELOPMENT.md           # This file
```

## Tips for Productive Development

1. **Use Watch Mode**
   ```bash
   npm run watch
   ```
   Auto-compiles TypeScript on save

2. **Keep Console Open**
   Always have Developer Tools open to catch errors early

3. **Test Edge Cases**
   - Empty messages
   - Very long messages
   - Rapid message sending
   - Network failures

4. **Version Control**
   ```bash
   git add .
   git commit -m "feat: add feature X"
   git push
   ```

5. **Document Changes**
   Update README for user-facing changes

## Troubleshooting Development Issues

**Extension not loading?**
- Check for TypeScript compilation errors
- Verify `package.json` syntax

**API communication failing?**
- Ensure Python server is running
- Check network requests in Developer Tools

**UI not updating?**
- Make sure to reload the Extension Development Host
- Clear any cached state if needed

---

Happy coding! Remember to test thoroughly before distributing updates to students. 