import re
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import threading

# -------- GLOBALS --------
printed_paths = set()
print_lock = threading.Lock()

# -------- Normalize --------
def normalize_path(path):
    try:
        if path.startswith("http"):
            path = urlparse(path).path

        path = path.split("?")[0]

        if path.endswith("/") and path != "/":
            path = path[:-1]

        return path.strip()
    except:
        return None


# -------- Smart Filter (NO DATA LOSS) --------
def is_valid_path(p):
    if not p:
        return False

    # must start with /
    if not p.startswith("/"):
        return False

    # remove HTML / JS junk
    if any(x in p for x in ["<", ">", "{", "}", "(", ")", "\\", "$", "`"]):
        return False

    # remove encoded junk
    if "%" in p:
        return False

    # ignore JS comments / artifacts
    if p.startswith(("//", "/#", "/@", "/*")):
        return False

    # remove static files only
    if any(p.endswith(ext) for ext in [
        ".js", ".css", ".png", ".jpg", ".jpeg", ".gif",
        ".svg", ".woff", ".ttf", ".ico", ".map",
        ".mp4", ".mp3", ".pdf", ".webp"
    ]):
        return False

    # remove wildcard junk
    if "*" in p:
        return False

    # too short = junk
    if len(p) < 3:
        return False

    return True


# -------- Extract --------
def extract_paths(js):
    patterns = [
        r'https?://[^\s"\']+',
        r'["\'](/[^"\']+)["\']'
    ]

    results = set()

    for pattern in patterns:
        matches = re.findall(pattern, js)

        for m in matches:
            p = normalize_path(m)

            if is_valid_path(p):
                results.add(p)

    return results


# -------- Process URL --------
def process_url(url):
    global printed_paths
    found = set()

    try:
        with print_lock:
            print(f"[JS] {url}")

        res = requests.get(url, timeout=10)
        paths = extract_paths(res.text)

        for p in paths:
            if p not in printed_paths:
                with print_lock:
                    if any(k in p for k in ["admin", "api", "auth", "internal", "debug"]):
                        print(f"   🔥 {p}")
                    else:
                        print(f"   └─ {p}")

                printed_paths.add(p)

            found.add(p)

    except:
        with print_lock:
            print(f"[ERROR] {url}")

    return found


# -------- Process File --------
def process_file(file, threads):
    all_paths = set()

    with open(file, "r") as f:
        urls = f.read().splitlines()

    with ThreadPoolExecutor(max_workers=threads) as exe:
        futures = [exe.submit(process_url, u) for u in urls]

        for f in as_completed(futures):
            all_paths.update(f.result())

    return all_paths


# -------- Extract Directories --------
def extract_dirs(paths):
    dirs = set()
    for p in paths:
        parts = p.split("/")
        for i in range(1, len(parts)):
            d = "/" + "/".join(parts[1:i])
            if len(d) > 2:
                dirs.add(d)
    return dirs


# -------- Save --------
def save(name, data):
    with open(name, "w") as f:
        for x in sorted(data):
            f.write(x + "\n")


# -------- MAIN --------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🔥 JS Path Extractor (Clean Version)")

    parser.add_argument("-i", "--input", required=True, help="JS URLs file")
    parser.add_argument("-o", "--output", default="paths.txt")
    parser.add_argument("-d", "--dirs", action="store_true")
    parser.add_argument("-t", "--threads", type=int, default=10)

    args = parser.parse_args()

    print("[+] Starting JS Recon...\n")

    paths = process_file(args.input, args.threads)

    print(f"\n[+] Total Clean Paths: {len(paths)}")

    save(args.output, paths)

    if args.dirs:
        d = extract_dirs(paths)
        save("dirs.txt", d)
        print(f"[+] Total Directories: {len(d)}")

    print("\n[+] Done ✔")