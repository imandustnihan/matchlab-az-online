package main

import (
    "context"
    "embed"
    "fmt"
    "io"
    "io/fs"
    "log"
    "net"
    "net/http"
    "net/http/httputil"
    "net/url"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "time"
)

// Web UI is embedded into the EXE so it displays without waiting for Render.
//go:embed web
var bundled embed.FS

const backend = "https://matchlab-az-online.onrender.com"

var offlineFiles = map[string]bool{
    "/": true, "/index.html": true, "/app.js": true, "/styles.css": true,
    "/catalog.js": true, "/coach_tactics.js": true, "/featured_media.js": true,
    "/assets/icon.svg": true, "/_matchlab_simple.css": true,
    "/_matchlab_simple.js": true,
}

func router() http.Handler {
    u, _ := url.Parse(backend)
    proxy := httputil.NewSingleHostReverseProxy(u)
    proxy.Transport = &http.Transport{
        Proxy: http.ProxyFromEnvironment,
        DialContext: (&net.Dialer{Timeout: 6*time.Second, KeepAlive: 30*time.Second}).DialContext,
        ResponseHeaderTimeout: 30*time.Second,
        MaxIdleConns: 12,
    }
    proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
        log.Printf("Backend unavailable: %v", err)
        w.Header().Set("Cache-Control", "no-store")
        w.Header().Set("Content-Type", "application/json; charset=utf-8")
        w.WriteHeader(http.StatusBadGateway)
        _, _ = io.WriteString(w, "{\"ok\":false,\"backend\":false,\"error\":\"Server müvəqqəti əlçatan deyil\"}")
    }
    sub, err := fs.Sub(bundled, "web")
    if err != nil { panic(err) }
    static := http.FileServer(http.FS(sub))
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path == "/_matchlab_health" {
            w.Header().Set("Content-Type", "text/plain")
            _, _ = io.WriteString(w, "MATCHLABAZ-FAST/2")
            return
        }
        if (r.Method == "GET" || r.Method == "HEAD") && offlineFiles[r.URL.Path] {
            if r.URL.Path == "/" {
                r2 := r.Clone(r.Context())
                r2.URL.Path = "/index.html"
                w.Header().Set("Cache-Control", "no-store")
                static.ServeHTTP(w, r2)
                return
            }
            if strings.HasSuffix(r.URL.Path, ".html") {
                w.Header().Set("Cache-Control", "no-store")
            }
            static.ServeHTTP(w, r)
            return
        }
        if strings.HasPrefix(r.URL.Path, "/_matchlab_") {
            http.NotFound(w, r)
            return
        }
        // All live APIs and dynamic data remain server backed.
        proxy.ServeHTTP(w, r)
    })
}

func launch(address string) bool {
    profileRoot := os.Getenv("LOCALAPPDATA")
    if profileRoot == "" {
        profileRoot, _ = os.UserCacheDir()
    }
    if profileRoot == "" { profileRoot = os.TempDir() }
    profile := filepath.Join(profileRoot, "MATCHLAB_AZ", "BrowserProfile")
    _ = os.MkdirAll(profile, 0700)
    choices := []string{}
    for _, base := range []string{os.Getenv("PROGRAMFILES(X86)"), os.Getenv("PROGRAMFILES"), os.Getenv("LOCALAPPDATA")} {
        if base == "" { continue }
        choices = append(choices, filepath.Join(base,"Microsoft","Edge","Application","msedge.exe"))
        choices = append(choices, filepath.Join(base,"Google","Chrome","Application","chrome.exe"))
    }
    choices = append(choices,"msedge.exe","chrome.exe")
    for _, p := range choices {
        if _, err := exec.LookPath(p); err != nil { continue }
        cmd := exec.Command(p, "--app="+address, "--window-size=1220,860", "--user-data-dir="+profile, "--no-first-run")
        if err := cmd.Start(); err == nil {
            _ = cmd.Wait()
            return true
        }
    }
    cmd := exec.Command("rundll32.exe","url.dll,FileProtocolHandler",address)
    if err := cmd.Start(); err == nil {
        // Default browser may return immediately; keep the local server available.
        _ = cmd.Wait()
        select {}
    }
    return false
}

func main() {
    listener, err := net.Listen("tcp","127.0.0.1:0")
    if err != nil { log.Fatal(err) }
    server := &http.Server{Handler:router(),ReadHeaderTimeout:8*time.Second}
    go func() {
        if err := server.Serve(listener); err != nil && err != http.ErrServerClosed {
            log.Printf("Server error: %v",err)
        }
    }()
    address := "http://"+listener.Addr().String()
    if os.Getenv("MATCHLAB_TEST_HEADLESS") == "1" {
        fmt.Println(address)
        select {}
    }
    if !launch(address) { log.Print("Edge və Chrome tapılmadı") }
    ctx, cancel := context.WithTimeout(context.Background(),3*time.Second)
    defer cancel()
    _ = server.Shutdown(ctx)
}
