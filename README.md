# UIL-DL Standalone *(v1.0 Beta)*

This branch is the source code of the standalone/app version. For the dev version that operates out of a repository, go to the [dev branch](https://github.com/acemavrick/uil-dl/tree/main).

## Table of Contents

- [UIL-DL Standalone *(v1.0 Beta)*](#uil-dl-standalone-v10-beta)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Downloading Materials](#downloading-materials)
    - [File Types](#file-types)
    - [Filtering \& Sorting](#filtering--sorting)
    - [The Cache](#the-cache)
    - [Settings](#settings)
  - [Analytics](#analytics)
  - [Contact](#contact)
  - [Contributing](#contributing)

## Overview

UIL-DL (UIL Downloader) is a tool designed to simplify the process of downloading and managing UIL Academics contest materials.
It provides a clean, intuitive interface for filtering and accessing contest files, with features like caching to optimize bandwidth usage and download speed.

## Features

- **Search and Filter**: Easily find contests by subject, level, and year
- **Smart Caching**: Downloaded files are cached locally to avoid redundant downloads
- **Concurrent Downloads**: Efficiently manage multiple downloads
- **Responsive UI**: Clean and easy to use interface

## Installation

You can find the latest versions and instructions for macOS and Windows in the [releases](https://github.com/acemavrick/uil-dl/releases) section.

If you're the type of person who would build from source, you may want to check out the [dev](https://github.com/acemavrick/uil-dl/tree/main) version instead.

## Usage

### Downloading Materials

UIL-DL offers an easy and efficient way to download contest materials in batches.

1. Use the checkboxes to mark which files you want downloaded.
2. Click "Download Selected" to start downloading all the selected files.

Files will be saved to the directory specified in the left panel and
will be downloaded in the format `{Contest}_{Year}_{Level}_{filetype}`, with spaces being replaced by hyphens (e.g. `Calculator-Applications_2025_District_pdf.pdf`).
**Quitting the app before all files are downloaded will stop in-progress downloads.**

### File Types

There are three types of files that are available to download.

- PDF Packets: the packets of the contests, in PDF form. Often include the answer key.
- ZIP Data Files: Contain `zip` files of contest data. Mostly just for Computer Science Programming. May include answer keys.
- Other Files: This would be a link to files that are not downloadable by this tool, such as Box files.

All files are sourced directly from the official UIL [study materials](https://www.uiltexas.org/academics/resources/study-materials) page.
The app simply displays what's available on the official site, so any inconsistencies typically reflect the source website.

### Filtering & Sorting

Filter using the left panel options and sort by clicking column headers.
The levels are sorted by contest order (Study Packet* -> Invitational A -> Invitational B -> District -> Region -> State); everything else is sorted in alphabetical order.

>\*Study Packets are PDFs that typically include contests for the entire contest season in that year.

**Available Filters:**

- **Subject**: the subject/contest category (e.g. Accounting, Calculator Applications, Mathematics).
- **Level**: the contest level.
- **Year**: the year of the contest.
- **Status**: the file status of each contest file(s), as found in the cache.

### The Cache

The application maintains a smart caching system to track downloaded files and prevent redundant downloads.
The cache is designed to work seamlessly in the background and does not need attention in most cases.

- **Cache Location**: Downloaded files are stored in your specified downloads directory
- **Cache Manifest**: A `.cache_manifest.json` file maintains metadata about downloaded files including size and timestamps
- **Cache Operations**:
  - Refresh Cache: Scans your downloads directory to update the cache index with any manually added files
  - Reset Cache: Clears the cache index without deleting any physical files (useful if the cache becomes corrupted)

### Settings

On the top left, there is a panel displaying information and useful settings.

- Info Version: the version of the `info.json` file in use.
- Total Contests: the total number of contests (not files) tracked by this tool
- Downloads path: the path to the directory this tool is using to store and manage downloads.
- Refresh Info: fetches the latest version of the `info.json` file from this repository.
- Set Path: sets the downloads path (also edits the config file). Doing this will cancel any downloads in progress.

**What is `info.json`?**

The `info.json` is a file the tool uses to track what contests are available through UIL's website. The only way it can/will be updated for the *standalone* app will be through the "Refresh Info" button (and on startup). The actual file is located on the dev branch of this product and can only be updated manually.

If you find that the downloads offered by the tool do not match the website, please [contact me](#contact) promptly.

## Analytics

Basic, anonymous analytics data is collected by default to help improve the application and understand feature usage patterns. The analytics are limited to functional events (like downloads and searches) and never include personal information or file contents. All analytics events are processed in `app.py` and can be viewed in the code.

To disable analytics, go to the application support directory and delete the `ga4_csnt`. Do not delete the `ga4_cid` file; deleting that will cause analytics to be re-enabled.

## Contact

If you have questions, feedback, or need support:

- **GitHub Issues**: [Create an issue](https://github.com/acemavrick/uil-dl/issues) for bug reports or feature requests
- **Discord**: Join the [Discord server](https://discord.gg/a6DdBaebPk) for community support and updates
- **Direct Contact**: For personal inquiries, my contact information is available on my [GitHub profile](https://github.com/acemavrick).

When reporting issues, please include:

- Your operating system and version
- Application version
- Steps to reproduce the problem
- Any error messages or screenshots

## Contributing

Contributions are welcome! You can help by:

- **Reporting bugs** or requesting features through GitHub issues
- **Submitting pull requests** for fixes or enhancements
- **Improving documentation**

To contribute code:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a well-documented pull request
