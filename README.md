# Generate Your Personal YouTube Report
<img src="https://i.imgur.com/ZWGHIhr.png" alt="avatar" width="571" height="656">
<img src="https://i.imgur.com/cN3aaV2.png" alt="avatar" width="571" height="278">

## Getting Started

### 1. Install Python 3+

If you don't already have Python 3+ installed on your computer, download it from https://www.python.org/downloads/. 

### 2. Get Your YouTube Data

Here you can find out how to download your Google data: https://support.google.com/accounts/answer/3024190?hl=en
Here you can download all of the data that Google has stored on you: https://takeout.google.com/
<img src="https://i.imgur.com/UT22gRr.png" alt="avatar" width="571" height="656">
<img src="https://i.imgur.com/nDXiP12.png" alt="avatar" width="571" height="656">

To use this script, you only need to select and download part of "YouTube", which Google will provide to you as a Zip file by default.

### 3. Clone This Repository

On [https://github.com/A3M4/Personal-YouTube-Report-Generator](https://github.com/Echoinsraht5/youtube_report), click the green "Clone or Download" button at the top right of the page. Then, click the "Download ZIP" button, and extract the ZIP somewhere on your computer.

NOTE: Make sure to set your [Google Account language ](https://support.google.com/accounts/answer/32047)to English before downloading

### 4. Extract the Takeout File

Extract the Takeout File(from step 2) and move it to the repository folder(from step 3). Now the files in Repository folder look like below.



<img src="https://i.ibb.co/R4D5yHn/Screenshot-2.png" alt="avatar" style="zoom: 200%;" />

### 5. Install Dependencies

Open [command prompt or Terminal window](https://tutorial.djangogirls.org/en/intro_to_command_line/#what-is-the-command-line) in this repository folder, type the following and press enter:

```
pip install -r requirements.txt
```

### 6. Run the Script

In the same command prompt or Terminal window, type the following and press enter:

```
python report.py
```

### 7. Results

The script will generate a file named **YouTube_Report.pdf**. This file will automatically open in your browser once the script completes. Besides, you can find all the images that make up this report in **Images** folder.

Here's the final outlook of entire directory
<img src="https://i.imgur.com/Pyz9hOt.png" alt="avatar"  style="zoom: 50%;">
<img src="https://i.imgur.com/8SSxi33.png" alt="avatar"  style="zoom: 50%;">


