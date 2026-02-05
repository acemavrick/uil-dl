// tracks which files are selected for bulk download
// Map<contest_id, Set<"pdf" | "zip">>
import { writable, derived } from 'svelte/store';

export const selectedItems = writable<Map<number, Set<string>>>(new Map());

export const selectionSummary = derived(selectedItems, ($sel) => {
    let pdf = 0, zip = 0;
    for (const types of $sel.values()) {
        if (types.has('pdf')) pdf++;
        if (types.has('zip')) zip++;
    }
    return { total: pdf + zip, pdf, zip };
});

// helpers
export function toggleFile(contestId: number, fileType: string) {
    selectedItems.update((map) => {
        const next = new Map(map);
        const types = new Set(next.get(contestId) || []);
        if (types.has(fileType)) {
            types.delete(fileType);
            if (types.size === 0) next.delete(contestId);
            else next.set(contestId, types);
        } else {
            types.add(fileType);
            next.set(contestId, types);
        }
        return next;
    });
}

export function toggleRow(contestId: number, availableTypes: string[]) {
    selectedItems.update((map) => {
        const next = new Map(map);
        const current = next.get(contestId);
        const allSelected = current && availableTypes.every(t => current.has(t));

        if (allSelected) {
            next.delete(contestId);
        } else {
            next.set(contestId, new Set(availableTypes));
        }
        return next;
    });
}

export function selectAllColumn(fileType: string, contestIds: number[]) {
    selectedItems.update((map) => {
        const next = new Map(map);
        // check if all are already selected
        const allSelected = contestIds.every(id => next.get(id)?.has(fileType));

        for (const id of contestIds) {
            const types = new Set(next.get(id) || []);
            if (allSelected) {
                types.delete(fileType);
                if (types.size === 0) next.delete(id);
                else next.set(id, types);
            } else {
                types.add(fileType);
                next.set(id, types);
            }
        }
        return next;
    });
}

export function selectAll(contests: { id: number; pdf_link: string | null; zip_link: string | null }[]) {
    selectedItems.update((map) => {
        const next = new Map(map);
        // if everything is selected, deselect all
        const allSelected = contests.every(c => {
            const types = next.get(c.id);
            if (!types) return !c.pdf_link && !c.zip_link;
            const pdfOk = !c.pdf_link || types.has('pdf');
            const zipOk = !c.zip_link || types.has('zip');
            return pdfOk && zipOk;
        });

        if (allSelected) {
            return new Map();
        }

        for (const c of contests) {
            const types = new Set<string>();
            if (c.pdf_link) types.add('pdf');
            if (c.zip_link) types.add('zip');
            if (types.size > 0) next.set(c.id, types);
        }
        return next;
    });
}

export function clearSelection() {
    selectedItems.set(new Map());
}
