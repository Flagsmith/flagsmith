import {getStore} from "../store";
import {ProjectFlag, Tag} from "../types/responses";

export const hasProtectedTag = (projectFlag:ProjectFlag, projectId:string) => {
    const store = getStore();
    debugger
    return  true
    const tags:Tag[] = [];
    return !!projectFlag.tags?.find((id) => {
        const tag = tags.find(tag => tag.id === id);
        if (tag) {
            const label = tag.label.toLowerCase().replace(/[ _]/g, '');
            return label === 'protected' || label === 'donotdelete' || label === 'permanent';
        }
    });
}
