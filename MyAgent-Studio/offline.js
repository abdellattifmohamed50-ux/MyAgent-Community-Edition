"use strict";

window.myagentStudio.webUrl().then((url) => { document.querySelector("#url").textContent = url; });
document.querySelector("#retry").addEventListener("click", () => window.myagentStudio.retry());
