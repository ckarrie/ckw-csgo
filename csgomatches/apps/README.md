# Wansspieltbig Apps

## WSB_Proxy

### Version naming scheme

`WSB_Proxy.<YEAR>.<MONTH>.<RELEASE NR>.bin`

### Generating binary

```bash
cd ~/workspace/venvs/wannspieltbig_v3/
source bin/activate
cd ~/workspace/src/github/ckw-csgo/
pyinstaller --onefile --windowed csgomatches/apps/WSB_Proxy.py
```

Generated Files are in `~/workspace/src/github/ckw-csgo/dist`

### Usage

```
usage: WSB_Proxy.2026-01-24.bin [-h] [--interval INTERVAL] --auth_user AUTH_USER --auth_pass AUTH_PASS
```

- `--interval 60`: Sleeping for `interval` seconds before next fetch, defaults to 60 seconds
- `--auth_user <username>`: Your Staff Wannspieltbig.de Username
- `--auth_pass <password>`: Your Staff Wannspieltbig.de Password

