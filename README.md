# Documentation Downloader 📚

A powerful and user-friendly Python tool that downloads web documentation and converts it to clean Markdown format! Perfect for offline reading, documentation migration, or content analysis.

## ✨ Features

- 🔄 Multiple crawling methods:
  - Sitemap-based crawling (auto-detects common sitemap locations)
  - Recursive link-following for sites without sitemaps
  - Custom sitemap URL support
  - Support for sitemap indexes and nested sitemaps
- 📝 Converts HTML to clean Markdown format
- 🌳 Maintains documentation structure with proper directory hierarchy
- 🚀 Shows real-time progress with nice progress bars
- 🕊 Respects rate limiting and robots.txt rules
- 🎯 Smart error handling and detailed logging
- 💾 Organized output with clean filenames
- 🎨 User-friendly command-line interface with clear prompts
- 📊 Command-line arguments support for automation/scripting
- 💡 Set maximum pages to download and custom delay between requests

## 🛠 Installation

1. **Clone or download this repository**

2. **Create a virtual environment:**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration Parameters

### Request Delay
- **Purpose**: Controls the time interval between consecutive requests to avoid overloading the target server.
- **Default**: 1.0 second
- **Usage**: 
  - Command line: `--delay 2.5` (in seconds)
  - Interactive mode: Enter value when prompted
- **Recommendation**: Use higher values (2-3 seconds) for smaller servers, lower values (0.5-1 second) for robust sites.

### Page Limit
- **Purpose**: Sets the maximum number of pages to download, preventing unintended large-scale crawling.
- **Usage**:
  - Command line: `--max-pages 100`
  - Interactive mode: Enter value when prompted or leave empty for no limit
- **Note**: Setting this appropriately helps control execution time and output size.

### Robots.txt Compliance
- **Purpose**: Determines whether the crawler should respect robots.txt restrictions.
- **Default**: Enabled (respects robots.txt)
- **Usage**:
  - Command line: Use `--no-robots` to disable
  - Interactive mode: Answer 'n' when prompted

### Crawling Method
- **Purpose**: Determines how the tool discovers pages to download.
- **Options**:
  1. **Auto-detect sitemap** (`--method auto`): Fastest when sitemaps are available
  2. **Recursive crawling** (`--method recursive`): Most thorough but slower
  3. **Custom sitemap URL** (`--method sitemap --sitemap URL`): Best for known sitemap locations
- **Note**: Choose based on the structure of the documentation site and your specific needs.

### Output Directory
- **Purpose**: Specifies where the converted Markdown files will be saved.
- **Default**: 'markdown_docs'
- **Usage**:
  - Command line: `--output custom_folder_name`
  - Interactive mode: Enter value when prompted

## 🚀 Usage

### Interactive Mode

1. **Activate the virtual environment** (if not already activated):
   ```bash
   # On Windows
   .\venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

2. **Run the script:**
   ```bash
   python main.py
   ```

3. **Follow the interactive prompts:**
   - Enter the documentation base URL
   - Choose your preferred crawling method:
     1. Auto-detect sitemap.xml (tries common locations)
     2. Recursive crawling (follows links within the domain)
     3. Enter custom sitemap URL
   - Choose an output directory for the Markdown files
   - Set optional parameters like delay between requests

### Command-Line Arguments Mode (for automation)

You can also run the script with command-line arguments for automation:

```bash
python main.py --url https://docs.example.com --output docs_output --method recursive --delay 1.5 --max-pages 100 --no-robots
```

Available arguments:
- `--url`: Base URL of the documentation
- `--output`: Output directory name (default: markdown_docs)
- `--method`: Crawling method (auto/recursive/sitemap)
- `--sitemap`: Custom sitemap URL (required if method=sitemap)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--max-pages`: Maximum number of pages to download
- `--no-robots`: Ignore robots.txt restrictions

## 📝 Example

```bash
$ python main.py

╔═══════════════════════════════════════════╗
║     Documentation Downloader v1.0         ║
║         Convert Docs to Markdown          ║
╚═══════════════════════════════════════════╝

Welcome to Documentation Downloader!
This tool will help you convert web documentation to Markdown format.

Enter the base documentation URL: https://docs.example.com

Choose crawling method:
1. Auto-detect sitemap.xml
2. Recursive crawling (follows links)
3. Enter custom sitemap URL

Enter choice (1/2/3): 2

Enter output directory name [markdown_docs]: my_docs

Enter delay between requests in seconds [1.0]: 2

Maximum number of pages to download (leave empty for no limit): 50

Respect robots.txt restrictions? (y/n) [y]: y

Starting documentation download...
Downloading documentation: 100%|██████████| 42/42 [01:24<00:00]
Pages: 42, Pending: 13

Success! Documentation has been downloaded and converted.
You can find the Markdown files in the 'my_docs' directory.
```

## 📁 Output Structure

The downloaded documentation maintains its original structure:
```
my_docs/
├── index.md
├── getting-started/
│   ├── installation.md
│   └── configuration.md
├── guides/
│   ├── basic-usage.md
│   └── advanced-features.md
└── api/
    └── reference.md
```

Each Markdown file includes:
- Clean, readable content
- Original formatting preserved
- YAML frontmatter with:
  - Original title
  - Source URL
  - Download timestamp

Example Markdown file:
```markdown
---
title: Getting Started Guide
source_url: https://docs.example.com/getting-started
date_downloaded: 2024-03-14 11:20:15
---

# Getting Started

Rest of the converted content...
```

## 🔍 Logging

The script creates a `crawler.log` file with detailed information about the download process, helpful for debugging any issues.

## 🛠️ Advanced Features

### Robots.txt Support

The tool respects robots.txt rules by default, but you can disable this with the `--no-robots` flag or by answering "n" to the robots.txt prompt.

### Sitemap Parsing

The tool can handle both standard sitemaps and sitemap indexes (which contain links to multiple sitemaps).

### Error Handling

The tool provides detailed error handling and logging, with graceful fallbacks when issues occur.

## ⚠️ Important Notes

1. Choose the appropriate crawling method:
   - **Sitemap-based**: Faster and more efficient if available
   - **Recursive**: More thorough but slower, great for sites without sitemaps
2. Respect website terms of service and robots.txt
3. Use reasonable delays between requests (default: 1 second)
4. Some websites may block automated downloads
5. Large documentation sites may take significant time to download

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Python and lots of ❤️
- Uses excellent libraries:
  - beautifulsoup4 for HTML parsing
  - html2text for conversion
  - tqdm for progress bars
  - requests for HTTP requests
  - validators for URL validation
  - python-robots for robots.txt parsing
- Inspired by the need for offline documentation access
