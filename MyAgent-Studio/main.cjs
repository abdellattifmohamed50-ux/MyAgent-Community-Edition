"use strict";

const path = require("node:path");
const { app, BrowserWindow, ipcMain, session, shell } = require("electron");

function configuredWebUrl() {
  const candidate = process.env.MYAGENT_WEB_URL || "http://localhost:8080";
  const parsed = new URL(candidate);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error("MYAGENT_WEB_URL must use HTTP or HTTPS");
  }
  return parsed.toString();
}

const webUrl = configuredWebUrl();
const allowedOrigin = new URL(webUrl).origin;
let mainWindow = null;

async function loadWorkspace() {
  if (!mainWindow) return;
  try {
    await mainWindow.loadURL(webUrl);
  } catch (_) {
    await mainWindow.loadFile(path.join(__dirname, "offline.html"));
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 980,
    minHeight: 640,
    backgroundColor: "#0b0b10",
    title: "MyAgent Studio",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://")) shell.openExternal(url);
    return { action: "deny" };
  });
  mainWindow.webContents.on("will-navigate", (event, url) => {
    try {
      const target = new URL(url);
      const isOfflinePage = target.protocol === "file:" && target.pathname.endsWith("/offline.html");
      if (target.origin !== allowedOrigin && !isOfflinePage) event.preventDefault();
    } catch (_) {
      event.preventDefault();
    }
  });
  loadWorkspace();
}

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => {
    callback(false);
  });
  ipcMain.handle("workspace:retry", loadWorkspace);
  ipcMain.handle("workspace:url", () => webUrl);
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
