# NilRanbow Media-RSS Auto-Syndication Feed

Automated, high-resolution Media RSS 2.0 generator for [NilRanbow](https://nilranbow.blogspot.com).

## Why this exists
Google Blogger's native RSS feeds do not emit `<media:content>` or `<enclosure>` tags, preventing Pinterest and modern social auto-publishers from finding high-resolution post images.

This repository dynamically parses NilRanbow's Blogger JSON feed, extracts full-resolution 1280x720 Google CDN cover images, and formats standard `<enclosure>` and `<media:content>` nodes.

## Live Feed URL
`https://subrata0ghosh.github.io/nilranbow-rss/feed.xml`

## Automation
A GitHub Action runs every 6 hours to fetch new posts and update `feed.xml` autonomously.
