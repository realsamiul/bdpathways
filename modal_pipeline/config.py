# Two lists. This is the most important file you'll configure manually.  
  
SCRAPE_AND_SUMMARIZE = [  
    # Static policy pages — Ivy League  
    {"url": "++[https://admission.brown.edu/apply](https://admission.brown.edu/apply)++",  
     "institution": "Brown", "tier": 1, "subtype": "static_policy",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://www.admissionsbeat.com/](https://www.admissionsbeat.com/)++",  
     "institution": "Brown", "tier": 1, "subtype": "ao_blog",  
     "ao_name": "Logan Powell", "ao_title": "Dean of Admission",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://undergrad.admissions.columbia.edu/apply/first-year](https://undergrad.admissions.columbia.edu/apply/first-year)++",  
     "institution": "Columbia", "tier": 1, "subtype": "static_policy",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://admissions.cornell.edu/community/blog](https://admissions.cornell.edu/community/blog)++",  
     "institution": "Cornell", "tier": 1, "subtype": "ao_blog",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://caltechadmissions.blog/](https://caltechadmissions.blog/)++",  
     "institution": "Caltech", "tier": 1, "subtype": "ao_blog",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://sites.gatech.edu/admission-blog/](https://sites.gatech.edu/admission-blog/)++",  
     "institution": "Georgia Tech", "tier": 1, "subtype": "ao_blog",  
     "ao_name": "Rick Clark", "ao_title": "Director of Undergraduate Admission",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://mitadmissions.org/apply/](https://mitadmissions.org/apply/)++",  
     "institution": "MIT", "tier": 1, "subtype": "static_policy",  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://admission.princeton.edu/blogs/applying-college](https://admission.princeton.edu/blogs/applying-college)++",  
     "institution": "Princeton", "tier": 1, "subtype": "ao_blog",  
     "country": "us", "category": "admissions"},  
  
    # SAT Prep  
    {"url": "++[https://satsuite.collegeboard.org/sat/preparation](https://satsuite.collegeboard.org/sat/preparation)++",  
     "institution": "College Board", "tier": 1, "subtype": "static_policy",  
     "country": "us", "category": "sat_prep"},  
]  
  
LINK_ONLY = [  
    # Video/gated — no scraping, store metadata manually  
    {"url": "++[https://initialview.com/tuesdaytalks/](https://initialview.com/tuesdaytalks/)++",  
     "title": "InitialView Tuesday Talks",  
     "tier": 1, "subtype": "video_webinar",  
     "content_format": "video", "is_scrapeable": False,  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://admissions.yale.edu/podcast](https://admissions.yale.edu/podcast)++",  
     "title": "Yale Admissions Podcast",  
     "tier": 1, "subtype": "video_webinar",  
     "content_format": "podcast", "is_scrapeable": False,  
     "country": "us", "category": "admissions"},  
  
    {"url": "++[https://enrollify.org/masteringthenext/](https://enrollify.org/masteringthenext/)++",  
     "title": "NYU Mastering the Next Podcast",  
     "tier": 1, "subtype": "video_webinar",  
     "content_format": "podcast", "is_scrapeable": False,  
     "country": "us", "category": "admissions"},  
]  