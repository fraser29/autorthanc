---
title: Home
layout: home
---

# autorthanc
{: .no_toc }

A Docker containerized DICOM server using Orthanc Docker image, PostgreSQL database, Nginx server, and Python code for automatic downloading or forwarding of studies based on provided JSON rules.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}


{: .note }
This project is under active development. Please check back for updates and new features. 

## Overview

The "autorthanc" project integrates Orthanc, a lightweight DICOM server, with additional components like PostgreSQL for database management, Nginx for web server functionalities, and Python scripts for automated study management.
    
## Quick Start

See instructions here: [QuickStart]

## Components

- Orthanc Docker Image
- PostgreSQL Database
- Nginx Server
- Python Scripts

    
## Functionality

The project offers the following key functionalities:

- DICOM server functionality provided by Orthanc Docker image.
- Database management using PostgreSQL for storing metadata and related information.
- Web server capabilities through Nginx for hosting web-based interfaces or serving DICOM files.
- Automatic study management via Python scripts, utilizing JSON rules for defining actions such as downloading or forwarding DICOM studies to other nodes.
  

See full [usage]

More indepth [tutorials]

----

## Roadmap

- Web based json editing and addition
- Json controlled study deletion after action

[QuickStart]: {% link pages/quickstart.md %}
[usage]: {% link pages/usage.md %}
[tutorials]: {% link pages/tutorials.md %}