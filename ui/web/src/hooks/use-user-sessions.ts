import { useQuery } from "@tanstack/react-query"
import { getUserSessionList } from "../api"

const useUserSessions = (userId: string) => {
    return useQuery({
        queryKey: ['user-sessions', userId],
        queryFn: () => getUserSessionList(),
        enabled: !!userId,
    })
}

export default useUserSessions