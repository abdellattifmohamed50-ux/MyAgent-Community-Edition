# MyAgent Studio

Electron desktop shell for MyAgent Community Edition v3.0. Studio loads the web
experience with a restricted preload bridge and an offline fallback.

## Development

```bash
npm ci
npm start
```

## Build

```bash
npm run dist -- --linux dir
```

Electron and `electron-builder` are development/build dependencies. Do not commit
`node_modules` or `dist`.
