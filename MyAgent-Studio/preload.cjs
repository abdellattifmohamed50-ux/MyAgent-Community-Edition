"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("myagentStudio", {
  retry: () => ipcRenderer.invoke("workspace:retry"),
  webUrl: () => ipcRenderer.invoke("workspace:url"),
});
