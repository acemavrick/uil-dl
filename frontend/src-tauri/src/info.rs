use crate::models::{Contest, RawInfo};
use std::collections::HashMap;

// level sort order for UI display
fn level_sort_order(level: &str) -> u8 {
    match level {
        "Study Packet" => 0,
        "Invitational A" => 1,
        "Invitational B" => 2,
        "District" => 3,
        "Region" => 4,
        "State" => 5,
        _ => 6,
    }
}

// prettify subject name from key format
fn prettify_subject(key: &str, subject_dict: &HashMap<String, String>) -> String {
    subject_dict.get(key).cloned().unwrap_or_else(|| {
        key.split('-')
            .map(|w| {
                let mut chars: Vec<char> = w.chars().collect();
                if let Some(c) = chars.first_mut() {
                    *c = c.to_ascii_uppercase();
                }
                chars.into_iter().collect::<String>()
            })
            .collect::<Vec<_>>()
            .join(" ")
    })
}

// prettify level name from key format
fn prettify_level(key: &str, title_abbrevs: &HashMap<String, String>) -> String {
    title_abbrevs.get(key).cloned().unwrap_or_else(|| {
        key.split('-')
            .map(|w| {
                let mut chars: Vec<char> = w.chars().collect();
                if let Some(c) = chars.first_mut() {
                    *c = c.to_ascii_uppercase();
                }
                chars.into_iter().collect::<String>()
            })
            .collect::<Vec<_>>()
            .join(" ")
    })
}

// parse raw info.json into Contest structs with assigned IDs
pub fn parse_info(raw: RawInfo) -> Vec<Contest> {
    // group entries by (subject, level, year) to combine pdf/zip/other links
    let mut grouped: HashMap<
        (String, String, u16),
        (Option<String>, Option<String>, Option<String>),
    > = HashMap::new();

    for (key, url) in &raw.linkdata {
        let parts: Vec<&str> = key.split('_').collect();
        if parts.len() < 3 {
            continue;
        }

        let subject_key = parts[0];
        let level_key = parts[1];

        // parse year, handling _data suffix
        let (year_str, is_data) = if parts.len() > 3 && parts[3] == "data" {
            (parts[2], true)
        } else {
            (parts[2], false)
        };

        let year: u16 = match year_str.parse() {
            Ok(y) => y,
            Err(_) => continue,
        };

        let subject = prettify_subject(subject_key, &raw.subject_dict);
        let level = prettify_level(level_key, &raw.title_abbrevs);
        let group_key = (subject, level, year);

        let entry = grouped.entry(group_key).or_insert((None, None, None));

        // determine link type by extension or _data suffix
        if is_data || url.ends_with(".zip") {
            entry.1 = Some(url.clone());
        } else if url.ends_with(".pdf") {
            entry.0 = Some(url.clone());
        } else {
            entry.2 = Some(url.clone());
        }
    }

    // convert to Contest structs with IDs
    let mut contests: Vec<Contest> = grouped
        .into_iter()
        .enumerate()
        .map(
            |(idx, ((subject, level, year), (pdf, zip, other)))| Contest {
                id: idx as u32,
                subject,
                level: level.clone(),
                year,
                level_sort: level_sort_order(&level),
                pdf_link: pdf,
                zip_link: zip,
                other_link: other,
            },
        )
        .collect();

    // sort for consistent ID assignment: subject asc, year desc, level_sort asc
    contests.sort_by(|a, b| {
        a.subject
            .cmp(&b.subject)
            .then(b.year.cmp(&a.year))
            .then(a.level_sort.cmp(&b.level_sort))
    });

    // reassign IDs after sort
    for (idx, contest) in contests.iter_mut().enumerate() {
        contest.id = idx as u32;
    }

    contests
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_level_sort() {
        assert!(level_sort_order("Study Packet") < level_sort_order("District"));
        assert!(level_sort_order("Region") < level_sort_order("State"));
    }
}
