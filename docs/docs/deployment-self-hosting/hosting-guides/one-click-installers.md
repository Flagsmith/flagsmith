---
title: "One-Click Installers"
description: "A dedicated page for the Deploy to options (DigitalOcean, Render, Railway) and guides for Fly.io and Caprover."
sidebar_position: 4
---

This guide provides instructions for deploying Flagsmith using one-click installers for various cloud platforms. These options offer a quick and straightforward way to get your Flagsmith instance up and running.

## Deploy to DigitalOcean

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/flagsmith/flagsmith/tree/main)

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/flagsmith/flagsmith/tree/main)

## Deploy on Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/36mGw8?referralCode=DGxv1S)

## Deploy to Fly.io

![Fly.io](/img/logos/fly.io.svg)

We're big fans of [Fly.io](https://fly.io)! You can deploy to Fly.io really easily:

```bash
git clone git@github.com:Flagsmith/flagsmith.git
cd flagsmith
flyctl postgres create --name flagsmith-flyio-db
flyctl apps create flagsmith-flyio
flyctl postgres attach --postgres-app flagsmith-flyio-db
flyctl deploy
```

Fly.io has a global application namespace, and so you may need to change the name of the application defined in [`fly.toml`](https://github.com/Flagsmith/flagsmith/blob/main/fly.toml) as well as the commands above.

## Deploy to Caprover

You can also deploy to a [Caprover Server](https://caprover.com/) with [One Click Apps](https://caprover.com/docs/one-click-apps.html). 