import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
    const res = await fetch("/c.1.json");
    return { info: await res.json() };
};