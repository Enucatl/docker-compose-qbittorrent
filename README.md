# docker-compose-qbittorrent

## After changing options in the UI
```
sudo cp /var/lib/docker/100000.100000/volumes/qbittorrent_qbittorrent.etc/_data/qBittorrent_new.conf qbittorrent.conf
```

## Security baseline

This compose project uses the shared [docker-compose-security-baseline](https://github.com/Enucatl/docker-compose-security-baseline) for common container hardening defaults, including capabilities, no-new-privileges, memory/swap, and PID limits.
