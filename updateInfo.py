import requests
import re
import json
import logging
from selectolax.lexbor import LexborHTMLParser
from collections import defaultdict
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init()

# Configure colored logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        # Store original level name
        original_levelname = record.levelname
        
        # Add color to level name
        if original_levelname in self.COLORS:
            record.levelname = f"{self.COLORS[original_levelname]}{original_levelname}{Style.RESET_ALL}"
            record.msg = f"{self.COLORS[original_levelname]}{record.msg}{Style.RESET_ALL}"
        
        # Format the record
        formatted = super().format(record)
        
        # Restore original level name to prevent issues with subsequent formatting
        record.levelname = original_levelname
        
        return formatted

# Configure logging with colors
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Remove any existing handlers
logger.handlers = []

# Add our custom handler
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Prevent propagation to root logger to avoid duplicate logs
logger.propagate = False

# Configuration
INTERACTIVE = True
FORCE_REWRITE = False
YEARS = range(2018, 2026)
# YEARS = range(2022, 2023)
BASE_URL = "https://www.uiltexas.org/academics/page/{year}-high-school-academic-study-materials"

def scrape_data():
    """Scrape UIL academic study materials data."""
    logger.info("Starting scraping process...")
    
    subjects = set()
    title_to_level = defaultdict(list)
    linkdata = {}
    stats = {'years_processed': 0, 'links_found': 0, 'data_files_found': 0}
    
    for year in YEARS:
        try:
            logger.info(f"Processing year {year}...")
            url = BASE_URL.format(year=year)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html = response.text
            
            tree = LexborHTMLParser(html)
            
            for h2 in tree.root.css('h2'):
                # all this complexity is bc the html is not consistent
                # this is why we have standards and conventions
                # like c'mon it shouldn't be this annoying
                subject_text = h2.text(strip=True)
                if not subject_text:
                    continue
                subject = subject_text.lower().replace(" ", "-")
                subjects.add(subject)
                is_programming = 'programming' in subject

                ul = h2.next.next
                if not ul or ul.tag != 'ul':
                    continue

                for li in ul.iter():
                    if is_programming:
                        # handle programming subject entries
                        text = re.split(r'[\n|\t|\r|\f]+', li.text().strip())
                        level = ""
                        packet_url = ""
                        data_url = ""
                        # yay hardcoding
                        if len(text) == 1:
                            # no sublevels to worry about (this would most likely be only the packet)
                            # we are assuming that the only link is the packet
                            if link_node := li.css_first('a'):
                                level = text[0]
                                packet_url = link_node.attributes.get('href', '')
                        else:
                            first_link_node = li.css_first('a')
                            fln_index = text.index(first_link_node.text(strip=True))
                            # even more hardcoding and assumptions =D
                            match fln_index:
                                # switch whether first link is the first or second piece of text
                                case 0:
                                    # i.e. "invitational A", etc. - would be the link to the packet
                                    packet_url = first_link_node.attributes.get('href', '')

                                    # there should be MORE LINKSSS
                                    datalink_nodes = li.css('a')[1:]
                                    if datalink_nodes:
                                        # this means there is a data file
                                        data_url = datalink_nodes[0].attributes.get('href', '')
                                case 1:
                                    # i.e. "data files" - would be the link to the data
                                    data_url = first_link_node.attributes.get('href', '')
                                case _:
                                    # idk
                                    raise ValueError(f"Unexpected index: {fln_index}.\n{li.html}")
                            # regardless, level is the first piece of text
                            level = text[0]

                        # we now have level, packet_url, and data_url (if they exist)
                        level = level.lower().replace(" ", "-")
                        key_packet = f"{subject}_{level}_{year}"
                        key_data = f"{subject}_{level}_{year}_data"
                        if packet_url:
                            linkdata[key_packet] = packet_url
                            stats['links_found'] += 1
                        
                        if data_url:
                            linkdata[key_data] = data_url
                            stats['links_found'] += 1
                            stats['data_files_found'] += 1
                        # finally, we are done
                    else:
                        link_node = li.css_first('a')
                        if not link_node:
                            continue
                            
                        level_text = link_node.text(strip=True)
                        url = link_node.attributes.get('href', '')
                        
                        if not level_text:
                            continue
                            
                        level = level_text.lower().replace(" ", "-")
                        key = f"{subject}_{level}_{year}"
                        
                        if url:
                            linkdata[key] = url
                            stats['links_found'] += 1
                            if level not in title_to_level[level_text]:
                                title_to_level[level_text].append(level)
            stats['years_processed'] += 1
            logger.info(f"Completed year {year}")
            
        except requests.RequestException as e:
            logger.error(f"Error processing year {year}: {e}")
            continue
    
    logger.info("Scraping completed with stats:")
    logger.info(f"- Years processed: {stats['years_processed']}")
    logger.info(f"- Links found: {stats['links_found']}")
    logger.info(f"- Data files found: {stats['data_files_found']}")
    logger.info(f"- Unique subjects: {len(subjects)}")
    logger.info(f"- Title mappings: {len(title_to_level)}")

    return subjects, title_to_level, linkdata

def clean_title_abbreviations(title_to_level, old_abbrevs=None):
    """Clean and resolve title abbreviations.
    
    Args:
        title_to_level (dict): Scraped data: {full_form_from_site: [potential_abbreviations]}
        old_abbrevs (dict, optional): Existing abbreviations: {abbreviation: full_form}
        
    Returns:
        dict: Cleaned abbreviations: {abbreviation: full_form}
    """
    logger.info("Cleaning level abbreviations...")
    
    # Final dictionary: abbreviation -> full_form
    cleaned_abbrevs = {}
    
    stats = {
        'preserved_from_old': 0,
        'new_mappings_added': 0,
        'interactive_choice_for_title': 0,
        'user_skipped_title_mapping': 0,
        'abbrev_kept_existing_mapping': 0, # When a chosen abbrev was already mapped
        'titles_processed': len(title_to_level)
    }

    if old_abbrevs:
        cleaned_abbrevs.update(old_abbrevs)
        stats['preserved_from_old'] = len(old_abbrevs)
        logger.info(f"Preserved {len(old_abbrevs)} mappings from existing titleAbbrevs.")
        for abbrev, full_form in old_abbrevs.items():
            logger.debug(f"  Preserved: {abbrev} -> '{full_form}'")

    # title_to_level is: {full_form_from_site: [potential_abbreviations_from_url]}
    for full_form_from_site, potential_abbrevs in title_to_level.items():
        chosen_abbrev = None

        if not potential_abbrevs:
            logger.warning(f"No potential abbreviations found for title: '{full_form_from_site}'. Skipping this title.")
            stats['user_skipped_title_mapping'] += 1
            continue

        if len(potential_abbrevs) == 1:
            chosen_abbrev = potential_abbrevs[0]
        else: # Multiple potential abbreviations for this full_form_from_site
            stats['interactive_choice_for_title'] +=1
            if INTERACTIVE:
                print(f"\n{Fore.YELLOW}Conflict: Title '{Style.BRIGHT}{full_form_from_site}{Style.RESET_ALL}{Fore.YELLOW}' has multiple potential abbreviations:{Style.RESET_ALL}")
                for i, level_abbrev_option in enumerate(potential_abbrevs):
                    print(f"  {i}: {level_abbrev_option}")
                
                while True:
                    choice_str = input(f"Enter the number for the correct abbreviation for '{full_form_from_site}', or '-' to skip: ").strip()
                    if choice_str == '-':
                        chosen_abbrev = None
                        stats['user_skipped_title_mapping'] += 1
                        logger.info(f"User skipped mapping for title '{full_form_from_site}'.")
                        break
                    try:
                        idx = int(choice_str)
                        if 0 <= idx < len(potential_abbrevs):
                            chosen_abbrev = potential_abbrevs[idx]
                            break
                        else:
                            print(f"{Fore.RED}Invalid choice number. Try again.{Style.RESET_ALL}")
                    except ValueError:
                        print(f"{Fore.RED}Invalid input. Please enter a number or '-'.{Style.RESET_ALL}")
            else: # Not interactive, pick the first one
                chosen_abbrev = potential_abbrevs[0]
                logger.info(f"Non-interactive mode: Chose first abbreviation '{chosen_abbrev}' for title '{full_form_from_site}'.")

        if not chosen_abbrev: # User skipped or no valid choice was made
            continue

        # Check if this chosen_abbrev conflicts with existing cleaned_abbrevs
        if chosen_abbrev in cleaned_abbrevs:
            # Abbreviation already exists in our map (either from old_abbrevs or processed earlier).
            # Rule: "if it is in the old, keep the old over the new" means we keep cleaned_abbrevs[chosen_abbrev].
            if cleaned_abbrevs[chosen_abbrev] == full_form_from_site:
                # Consistent: the chosen_abbrev already maps to the same full_form_from_site.
                logger.debug(f"Mapping {chosen_abbrev} -> '{full_form_from_site}' is consistent with existing/preserved mapping.")
            else:
                # Conflict: chosen_abbrev is already mapped to a DIFFERENT full_form. Keep the existing one.
                logger.warning(
                    f"Abbreviation '{Fore.CYAN}{chosen_abbrev}{Style.RESET_ALL}' is already mapped to "
                    f"'{Fore.MAGENTA}{cleaned_abbrevs[chosen_abbrev]}{Style.RESET_ALL}'. "
                    f"Cannot map it to '{Fore.YELLOW}{full_form_from_site}{Style.RESET_ALL}'. "
                    f"Keeping existing mapping for '{Fore.CYAN}{chosen_abbrev}{Style.RESET_ALL}'."
                )
                stats['abbrev_kept_existing_mapping'] += 1
        else:
            # New abbreviation mapping.
            cleaned_abbrevs[chosen_abbrev] = full_form_from_site
            logger.info(f"New mapping created: {Fore.GREEN}{chosen_abbrev}{Style.RESET_ALL} -> '{full_form_from_site}'")
            stats['new_mappings_added'] += 1
    
    logger.info("Title abbreviation cleaning completed with stats:")
    logger.info(f"  - Titles processed from scrape: {stats['titles_processed']}")
    logger.info(f"  - Mappings preserved from old: {stats['preserved_from_old']}")
    logger.info(f"  - New mappings added: {stats['new_mappings_added']}")
    logger.info(f"  - Interactive choices presented for titles: {stats['interactive_choice_for_title']}")
    logger.info(f"  - Titles skipped by user/no valid abbrev: {stats['user_skipped_title_mapping']}")
    logger.info(f"  - Abbreviations that kept their existing/older mapping due to conflict: {stats['abbrev_kept_existing_mapping']}")
    
    return cleaned_abbrevs

def merge_with_existing(new_data, old_data):
    """Merge new data with existing data, preserving important information."""
    if not old_data or FORCE_REWRITE:
        logger.info("No existing data or force rewrite enabled. Creating new data.")
        return create_new_data(new_data)
    
    logger.info("Merging with existing data...")
    subjects, title_to_level, linkdata = new_data
    
    # Merge subject dictionary
    old_subject_dict = old_data.get('subjectDict', {})
    new_subject_dict = {k: f'0-{k}' for k in subjects}
    merged_subject_dict = {}
    
    stats = {'subjects_preserved': 0, 'subjects_new': 0}
    for key in set(old_subject_dict) | set(new_subject_dict):
        if key in old_subject_dict:
            merged_subject_dict[key] = old_subject_dict[key]
            stats['subjects_preserved'] += 1
        else:
            merged_subject_dict[key] = new_subject_dict[key]
            stats['subjects_new'] += 1
    
    # Merge linkdata
    old_linkdata = old_data.get('linkdata', {})
    merged_linkdata = {**old_linkdata, **linkdata}
    
    stats['links_preserved'] = len(old_linkdata)
    stats['links_new'] = len(linkdata) - len(set(old_linkdata) & set(linkdata))
    
    # Get old title abbreviations for preservation
    old_abbrevs = old_data.get('titleAbbrevs', {})
    
    logger.info("Data merging completed with stats:")
    logger.info(f"- Subjects preserved: {stats['subjects_preserved']}")
    logger.info(f"- New subjects: {stats['subjects_new']}")
    logger.info(f"- Links preserved: {stats['links_preserved']}")
    logger.info(f"- New links: {stats['links_new']}")
    logger.info(f"- Existing title abbreviations: {len(old_abbrevs)}")
    
    return {
        "subjectDict": merged_subject_dict,
        "linkdata": merged_linkdata,
        "titleAbbrevs": clean_title_abbreviations(title_to_level, old_abbrevs)
    }

def create_new_data(data):
    """Create new data structure from scraped data."""
    subjects, title_to_level, linkdata = data
    return {
        "subjectDict": {k: f'0-{k}' for k in subjects},
        "linkdata": linkdata,
        "titleAbbrevs": clean_title_abbreviations(title_to_level)
    }

def main():
    """Main execution function."""
    try:
        # Scrape data
        scraped_data = scrape_data()
        
        # Load existing data if available
        try:
            with open("info.json", "r") as f:
                old_data = json.load(f)
            logger.info("Found existing info.json file")
        except (FileNotFoundError, json.JSONDecodeError):
            old_data = None
            logger.info("No existing info.json file found or invalid JSON")
        
        # Process and merge data
        final_data = merge_with_existing(scraped_data, old_data)
        
        # Write to file
        with open("info.json", "w") as f:
            json.dump(final_data, f, indent=4, sort_keys=True)
        logger.info("Successfully wrote to 'info.json'")
        
        # User inspection and modification cycle
        while True:
            print(f"\n{Fore.YELLOW}!!! IMPORTANT: Please manually inspect info.json for any errors before proceeding.{Style.RESET_ALL}")
            print("Look for:")
            print(f"{Fore.CYAN}- Incorrect subject mappings")
            print("- Missing or incorrect links")
            print(f"- Incorrect level abbreviations")
            print(f"- Any other data inconsistencies{Style.RESET_ALL}")
            
            user_choice = input(
                f"\n{Fore.GREEN}Are you ready to build the database with the current info.json? {Style.RESET_ALL}"
                f"({Fore.CYAN}y{Style.RESET_ALL}es / {Fore.CYAN}n{Style.RESET_ALL}o, make changes / {Fore.CYAN}q{Style.RESET_ALL}uit): "
            ).lower().strip()

            if user_choice == 'y':
                logger.info("User confirmed readiness. Proceeding to build database.")
                break
            elif user_choice == 'n':
                input(
                    f"{Fore.YELLOW}Okay, please make any necessary changes to info.json now. \n"
                    f"After saving your changes, press Enter here to re-check...{Style.RESET_ALL} "
                )
                # Reload data to reflect changes for the next iteration or final build (optional but good practice)
                try:
                    with open("info.json", "r") as f:
                        final_data = json.load(f) # Re-load for consistency if needed by buildDB directly
                    logger.info("Re-checked info.json after potential user changes.")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.error(f"Error reloading info.json after user indicated changes: {e}")
                    print(f"{Fore.RED}Could not reload info.json. Please ensure it's valid or choose 'q' to quit.{Style.RESET_ALL}")
                    # Optionally, force quit or loop back to 'n' without proceeding.
                    continue # Loop back to the prompt
            elif user_choice == 'q':
                logger.info("User chose to quit before database creation.")
                print(f"{Fore.RED}Quitting as per user request.{Style.RESET_ALL}")
                return # Exit main function
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 'y', 'n', or 'q'.{Style.RESET_ALL}")
        
        # Build database
        import buildDB
        buildDB.create_database("info.json", "info.db", interactive=INTERACTIVE)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()