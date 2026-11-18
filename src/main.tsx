import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { registerSW } from "@/lib/sw-register";
import "./index.css";

registerSW();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
