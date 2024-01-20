# SUPER SCRAPER

This project has several scrapers getting price, stock, codes and some other information from supermarkets web pages.

Nowadays it supports some markets from Argentina, but the aim is to add as many sites as possible.

DISCLAIMER: Web pages are in continuous change, then some scrapers may fail eventually, please report when it happens so I can correct issues.
Some information from a supermarket may be not in another one, this limitation depends on what information is given from each site.

# Requirements:

- python 3 installed in your system

- [scrapy](https://scrapy.org/) library

      pip install scrapy
- Connection to internet ;)

# HOW TO:

  Super_scraper is built on the framework [scrapy](https://scrapy.org/)

    

1) Get a copy of the repository, both using git: 

        git clone https://github.com/PabloAliArgentina/super_scraper
    
    or just downloading the zip from this site and decompressing 


2) Go to the directory:

        cd super_scraper/

3) Execute scrapy command line to start some scraper and get results in the desired format if supported. eg:

        scrapy crawl carrefourspider -O carrefour.json
        scrapy crawl jumbospider -O jumbo.csv



### Project is pretty new, so suggestion, feedback and collaborations are very welcome