import { writable, derived } from 'svelte/store';
import Fuse from 'fuse.js';
import type { Contest } from '$lib/tauri';
import { searchQuery, searchMode, caseSensitive } from './search';

export const contests = writable<Contest[]>([]);
export const loading = writable({ contests: true, cache: true });

// filter state
export const selectedSubjects = writable<string[]>([]);
export const selectedLevels = writable<string[]>([]);
export const selectedYears = writable<string[]>([]);

// derived unique values for filter dropdowns
export const subjects = derived(contests, ($contests) =>
    [...new Set($contests.map(c => c.subject))].sort()
);

export const levels = derived(contests, ($contests) => {
    const levelOrder = ['Study Packet', 'Invitational A', 'Invitational B', 'District', 'Region', 'State'];
    const unique = [...new Set($contests.map(c => c.level))];
    return unique.sort((a, b) => levelOrder.indexOf(a) - levelOrder.indexOf(b));
});

export const years = derived(contests, ($contests) =>
    [...new Set($contests.map(c => c.year))].sort((a, b) => b - a).map(String)
);

// filtered by dropdowns first, then search
const dropdownFiltered = derived(
    [contests, selectedSubjects, selectedLevels, selectedYears],
    ([$contests, $selectedSubjects, $selectedLevels, $selectedYears]) => {
        if ($selectedSubjects.length === 0 && $selectedLevels.length === 0 && $selectedYears.length === 0) {
            return $contests;
        }
        return $contests.filter(c => {
            const subjectMatch = $selectedSubjects.length === 0 || $selectedSubjects.includes(c.subject);
            const levelMatch = $selectedLevels.length === 0 || $selectedLevels.includes(c.level);
            const yearMatch = $selectedYears.length === 0 || $selectedYears.includes(String(c.year));
            return subjectMatch && levelMatch && yearMatch;
        });
    }
);

// final filtered list: dropdown filters → search
export const filteredContests = derived(
    [dropdownFiltered, searchQuery, searchMode, caseSensitive],
    ([$filtered, $query, $mode, $caseSensitive]) => {
        const q = $query.trim();
        if (!q) return $filtered;

        if ($mode === 'fuzzy') {
            const fuse = new Fuse($filtered, {
                keys: ['subject', 'level', { name: 'year', weight: 0.5 }],
                threshold: 0.4,
                ignoreLocation: true,
                isCaseSensitive: $caseSensitive,
            });
            return fuse.search(q).map(r => r.item);
        }

        if ($mode === 'regex') {
            try {
                const flags = $caseSensitive ? '' : 'i';
                const re = new RegExp(q, flags);
                return $filtered.filter(c =>
                    re.test(c.subject) || re.test(c.level) || re.test(String(c.year))
                );
            } catch {
                // invalid regex, return all
                return $filtered;
            }
        }

        // exact substring match
        const normalize = (s: string) => $caseSensitive ? s : s.toLowerCase();
        const needle = normalize(q);
        return $filtered.filter(c =>
            normalize(c.subject).includes(needle) ||
            normalize(c.level).includes(needle) ||
            String(c.year).includes(needle)
        );
    }
);
