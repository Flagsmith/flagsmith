import { FC, useMemo } from 'react';
import { useGetProjectsQuery } from 'common/services/useProject';

export type ProjectFilterType = {
  organisationId: string
  value?: string
  onChange: (value:string)=>void
  showAll? :boolean
}

const ProjectFilter: FC<ProjectFilterType> = ({organisationId, value, onChange, showAll}) => {
  const {data} = useGetProjectsQuery({organisationId})
  const foundValue = useMemo(()=>data?.find((project)=>`${project.id}` === value), [value,data])
  return (
    <Select
      value={foundValue? {label:foundValue.name, value:`${foundValue.id}`}: { value: "", label: showAll? "All Projects": "Select a Project" }}
      options={
        ((showAll? [{value:"",label:"All Projects"}]:[])).concat((data||[])?.map((v)=>({label: v.name, value:`${v.id}`})))
    }
      onChange={(value:{value:string, label:string})=>onChange(value?.value||"")}
    />
  );
};

export default ProjectFilter;
