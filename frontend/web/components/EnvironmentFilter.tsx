import { FC, useMemo } from 'react';
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment';

export type EnvironmentFilterType = {
  projectId: string
  value?: string
  onChange: (value:string)=>void
  showAll? :boolean
}

const EnvironmentFilter: FC<EnvironmentFilterType> = ({ projectId, value, onChange, showAll}) => {
  const {data} = useGetEnvironmentsQuery({ projectId})
  const foundValue = useMemo(()=>data?.results?.find((environment)=>`${environment.id}` === value), [value,data])
  return (
    <Select
      value={foundValue? {label:foundValue.name, value:`${foundValue.id}`}: { value: "", label: showAll? "All Environments": "Select a Environment" }}
      options={
        ((showAll? [{value:"",label:"All Environments"}]:[])).concat((data?.results||[])?.map((v)=>({label: v.name, value:`${v.id}`})))
    }
      onChange={(value:{value:string, label:string})=>onChange(value?.value||"")}
    />
  );
};

export default EnvironmentFilter;
