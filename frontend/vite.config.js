import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { defineConfig, loadEnv } from "vite";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    var proxyTarget = env.VITE_PROXY_TARGET || "http://127.0.0.1:8010";
    return {
        plugins: [vue()],
        resolve: {
            alias: {
                "@": fileURLToPath(new URL("./src", import.meta.url)),
            },
        },
        server: {
            host: "127.0.0.1",
            port: 5173,
            proxy: {
                "/api": {
                    target: proxyTarget,
                    changeOrigin: true,
                },
            },
        },
    };
});
