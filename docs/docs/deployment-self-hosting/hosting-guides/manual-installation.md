---
title: "Manual Installation"
description: "How to manually install both the Front End and the API for a more configurable environment."
sidebar_position: 70
---

If you want a more configurable environment, you can manually install both the Front End and the API.

### Server Side API

The source code and installation instructions can be found at
[the GitHub project](https://github.com/Flagsmith/flagsmith/tree/main/api). The API is written in Python and is based on
Django and the Django Rest Framework. The Server side API relies on a Postgres SQL installation to store its data, and a
Redis installation as a cache.

### Front End Website

The source code and installation instructions can be found at
[the GitHub project](https://github.com/Flagsmith/flagsmith/tree/main/frontend). The Front End Website is written in
React/Javascript and requires NodeJS. 