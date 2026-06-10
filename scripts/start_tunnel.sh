#!/bin/bash
exec "$HOME/cloudflared" tunnel --url http://localhost:8080
