import requests
import re
import json

INTERACTIVE = True
FORCE_REWRITE = False
YEARS = range(2018, 2026) # [2018, 2026)
mainURL = "https://www.uiltexas.org/academics/page/{year}-high-school-academic-study-materials"
linkPattern = re.compile(r'<a href="([^"]+)">(.*?)</a>')

## get new data
data = dict()
linkdata = dict()

# collect various patterns
subjects = set()
titleToLevel = dict()

print("Scraping... ", end = "")
for year in YEARS:
    page = requests.get(mainURL.format(year=year))
    html = page.text

    # get any and all links along with the text of the link
    catches = linkPattern.findall(html)

    while len(catches) > 0:
        url, title = [x.strip() for x in catches.pop(0)]

        # extract the subject from the link
        try:
            subject, _, level, yr = [x.strip() for x in url.split("/")[-1][:-4].split("_")]
        except:
            continue

        # clean year
        if len(yr) == 2:
            yr = "20"+yr
        
        # add to set of subjects
        subjects.add(subject)

        # process title
        if title in titleToLevel:
            # verify it matches. If not, add to title
            if not level in titleToLevel[title]:
                titleToLevel[title] += level
        else:
            titleToLevel[title] = [level]

        linkdata["_".join((subject, level, yr))] = url 
        
        # special handling for cs programming
        # check if the next url has a zip in it
        if "zip" in catches[0][0][-10:]:
            dataurl = catches.pop(0)[0]
            linkdata["_".join((subject, level, yr))+ "_data"] = dataurl
    print(".", end = "", flush=True)

print(" done.")

# init blank subjectDict
subjectDict = dict([(x, f'0-{x}') for x in subjects])

# clean titles
print("Cleaning level abbreviations.")
if not INTERACTIVE:
    print("Interactivity is turned off. In case of conflicts, the first occuring version will be chosen.")
cleanedTitleToLevel = {}
conflicts = 0
for key in titleToLevel:
    val = titleToLevel[key]
    if len(val) == 1:
        cleanedTitleToLevel[key] = val[0]
    else:
        conflicts += 1
        # interactive
        if INTERACTIVE:
            print("\n There has been a mismatch between levels and level abbreviations.")
            print(f"Full version: {title}")
            print("Conflicts:\n\t" + "\n\t".join(f"{i}:{t}" for i, t in enumerate(val)))
            while True:
                inpVal = input("Enter the correct version or '-' to skip: ").strip()
                if inpVal == '-':
                    # skip
                    break
                try:
                    cleanedTitleToLevel[key] = val[int(inpVal)]
                    break
                except:
                    continue
        else:
            cleanedTitleToLevel[key] = val[0]
print(f"Cleaned level abbreviations. {conflicts} conflicts found.")

# cross check with existing (if existing) data and update.
# if not existing, write new data

old = False
try:
    with open("info.json", "r") as f:
        oldData = json.loads(f.read())
    old = True
except FileNotFoundError:
    print("No existing info file found. Writing new.")
except json.decoder.JSONDecodeError as e:
    if INTERACTIVE:
        input("Error in decoding JSON. Press Enter to continue, Ctrl+c to quit.")
    else:
        raise e

if old and not FORCE_REWRITE:
    ### cross-check, update, and merge data

    ## merge subject dictionary.
    oldSubjectDict = oldData.get('subjectDict', {})
    combinedKeys = subjectDict.keys() | oldSubjectDict.keys()

    newSubjectDict = dict()
    for key in combinedKeys:
        valN = None
        # always throw away current values if possible (placeholders)
        if key in oldSubjectDict:
            valN = oldSubjectDict[key]
        else:
            valN = subjectDict[key]
        
        newSubjectDict[key] = valN
    
    # reassign
    subjectDict = newSubjectDict

    ## merge linkdata
    # inverse, merge, then inverse again
    ilinkO = {v:k for k, v in oldData.get('linkdata', {}).items()}
    ilinkC = {v:k for k, v in linkdata.items()}

    combinedKeys = ilinkO.keys() | ilinkC.keys()

    Nlinkdata = dict()
    for key in combinedKeys:
        valN = None
        # bias towards old data, always
        # if user wanted a rewrite they would force new updates
        if key in ilinkO:
            valN = ilinkO[key]
        elif key in ilinkC:
            # new link
            valN = ilinkC[key]
        
        # inverse as we go
        Nlinkdata[valN] = key
    
    # reassign
    linkdata = Nlinkdata
    

# build data and write
data["subjectDict"] = subjectDict
data["linkdata"] = linkdata
data["titleAbbrevs"] = cleanedTitleToLevel

jsons = json.dumps(data, indent=4)
with open("info.json", "w") as f:
    f.write(jsons)
print("Successfully wrote to 'info.json'.")
print()
print("!!! Important: Please manually look through the JSON to fix any errors.")
input("Press Enter to continue with building the database, Ctrl+c to quit. ")
print()

# execute databasebuilding
with open('buildDB.py', 'r') as f:
    exec(f.read())